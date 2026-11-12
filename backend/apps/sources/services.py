import logging
from abc import ABC, abstractmethod

import requests
from django.conf import settings
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from apps.sources.models import DataSourceSnapshot

logger = logging.getLogger("apps.sources.services")


def build_retry_session(retries: int = 2, backoff_factor: float = 0.3) -> requests.Session:
    """Builds a requests Session with bounded retries for external open data queries (T2.3)."""
    session = requests.Session()
    retry_strategy = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


class CompanySource(ABC):
    @abstractmethod
    def fetch_company_info(self, nit_clean: str) -> dict | None:
        """Obtiene información registrada de la empresa por NIT."""
        pass


class MockSource(CompanySource):
    """
    Fuente simulada determinista para pruebas offline y fallback de datos abiertos.
    """

    def fetch_company_info(self, nit_clean: str) -> dict | None:
        raw_nit = nit_clean.split("-")[0]
        seed_num = int(raw_nit) if raw_nit.isdigit() else 900123456

        cities = ["Bogotá, D.C.", "Medellín", "Cali", "Barranquilla", "Bucaramanga"]
        ciius = ["4690", "6201", "4110", "1010", "7020"]
        sizes = ["MICRO", "PEQUENA", "MEDIANA", "GRANDE"]

        data = {
            "nit": nit_clean,
            "dv": nit_clean.split("-")[1] if "-" in nit_clean else "7",
            "legal_name": f"EMPRESA SIMULADA COLOMBIA {raw_nit[-4:]} S.A.S.",
            "ciiu": ciius[seed_num % len(ciius)],
            "registration_date": "2018-05-15",
            "status": "ACTIVA",
            "city": cities[seed_num % len(cities)],
            "size": sizes[seed_num % len(sizes)],
            "origin": "MOCK",
        }

        DataSourceSnapshot.objects.create(
            nit=nit_clean,
            source_name="MockSource",
            status_code=200,
            payload=data,
        )
        logger.info("MockSource snapshot recorded for nit=%s", nit_clean)
        return data


def _format_registration_date(raw_date: str | None) -> str:
    """Formats YYYYMMDD date string to YYYY-MM-DD, or defaults cleanly."""
    if not raw_date:
        return "2020-01-01"
    raw_str = str(raw_date).strip()
    if len(raw_str) == 8 and raw_str.isdigit():
        return f"{raw_str[:4]}-{raw_str[4:6]}-{raw_str[6:8]}"
    return raw_str[:10]


class OpenDataSource(CompanySource):
    """
    Adaptador oficial para datos.gov.co utilizando la SODA API (Socrata)
    con el dataset oficial de RUES / Camaras de Comercio (c82u-588k).
    Incluye timeout y reintentos limitados (T2.2, T2.3).
    """

    CARATULA_URL = "https://www.datos.gov.co/resource/c82u-588k.json"

    def fetch_company_info(self, nit_clean: str) -> dict | None:
        raw_nit = nit_clean.split("-")[0]
        app_token = getattr(settings, "OPEN_DATA_APP_TOKEN", None)
        headers = {}
        if app_token:
            headers["X-App-Token"] = app_token

        params = {
            "$where": f"nit='{raw_nit}' or numero_identificacion='{raw_nit}'",
            "$limit": 1,
        }
        timeout = getattr(settings, "OPEN_DATA_TIMEOUT_SECONDS", 4)
        max_retries = getattr(settings, "OPEN_DATA_MAX_RETRIES", 2)

        session = build_retry_session(retries=max_retries)
        try:
            response = session.get(
                self.CARATULA_URL,
                params=params,
                headers=headers,
                timeout=timeout,
            )
            status_code = response.status_code
            if status_code == 200:
                json_data = response.json()
                DataSourceSnapshot.objects.create(
                    nit=nit_clean,
                    source_name="datos.gov.co",
                    status_code=200,
                    payload={"results": json_data},
                )
                if json_data and isinstance(json_data, list) and len(json_data) > 0:
                    row = json_data[0]
                    logger.info("OpenDataSource match found on datos.gov.co for nit=%s", nit_clean)
                    dv = (
                        row.get("digito_verificacion")
                        or row.get("dv")
                        or (nit_clean.split("-")[1] if "-" in nit_clean else "0")
                    )
                    city = row.get("camara_comercio") or row.get("ciudad") or "Bogotá, D.C."
                    return {
                        "nit": f"{raw_nit}-{dv}" if "-" not in nit_clean else nit_clean,
                        "dv": str(dv),
                        "legal_name": row.get("razon_social")
                        or row.get("nombre_completo", f"EMPRESA NIT {raw_nit}"),
                        "ciiu": row.get("cod_ciiu_act_econ_pri") or row.get("ciiu", "4690"),
                        "registration_date": _format_registration_date(
                            row.get("fecha_matricula") or row.get("fecha_corte")
                        ),
                        "status": row.get("estado_matricula") or row.get("status", "ACTIVA"),
                        "city": city.title() if city.isupper() else city,
                        "size": "MEDIANA",
                        "origin": "PUBLIC",
                    }
            else:
                DataSourceSnapshot.objects.create(
                    nit=nit_clean,
                    source_name="datos.gov.co",
                    status_code=status_code,
                    payload={"error": f"HTTP {status_code}"},
                )
                logger.warning("OpenDataSource returned status=%s for nit=%s", status_code, nit_clean)
        except Exception as exc:
            logger.warning(
                "OpenDataSource request failed for nit=%s (%s): falling back to MockSource",
                nit_clean,
                exc.__class__.__name__,
            )
            DataSourceSnapshot.objects.create(
                nit=nit_clean,
                source_name="datos.gov.co",
                status_code=500,
                payload={"error": str(exc)},
            )
        finally:
            session.close()

        # Automatic transparent fallback to MockSource if Open Data has no record or fails
        mock = MockSource()
        return mock.fetch_company_info(nit_clean)
