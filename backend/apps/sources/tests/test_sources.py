import pytest
from unittest.mock import patch, MagicMock
from apps.sources.services import MockSource, OpenDataSource, build_retry_session, _format_registration_date
from apps.sources.models import DataSourceSnapshot


@pytest.mark.django_db
class TestDataSources:
    def test_format_registration_date(self):
        assert _format_registration_date("20150331") == "2015-03-31"
        assert _format_registration_date("2020-05-15") == "2020-05-15"
        assert _format_registration_date(None) == "2020-01-01"

    def test_retry_session_configuration(self):
        session = build_retry_session(retries=2, backoff_factor=0.3)
        adapter = session.get_adapter("https://www.datos.gov.co/")
        assert adapter.max_retries.total == 2
        assert 503 in adapter.max_retries.status_forcelist
        session.close()

    def test_mock_source_returns_valid_dict_and_snapshot(self):
        source = MockSource()
        data = source.fetch_company_info("900123456-7")

        assert data["nit"] == "900123456-7"
        assert "EMPRESA SIMULADA" in data["legal_name"]
        assert data["origin"] == "MOCK"

        snapshot = DataSourceSnapshot.objects.filter(nit="900123456-7").first()
        assert snapshot is not None
        assert snapshot.source_name == "MockSource"
        assert snapshot.status_code == 200

    def test_open_data_source_success_parsing(self):
        source = OpenDataSource()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "numero_identificacion": "900170781",
                "digito_verificacion": "7",
                "razon_social": "ESCANHER ABOGADOS SAS",
                "cod_ciiu_act_econ_pri": "6910",
                "camara_comercio": "BOGOTA",
                "fecha_matricula": "20070904",
                "estado_matricula": "ACTIVA",
            }
        ]

        with patch("requests.Session.get", return_value=mock_response):
            data = source.fetch_company_info("900170781-7")

        assert data["legal_name"] == "ESCANHER ABOGADOS SAS"
        assert data["ciiu"] == "6910"
        assert data["city"] == "Bogota"
        assert data["registration_date"] == "2007-09-04"
        assert data["origin"] == "PUBLIC"
        assert data["status"] == "ACTIVA"

        snapshot = DataSourceSnapshot.objects.filter(nit="900170781-7", source_name="datos.gov.co").first()
        assert snapshot is not None
        assert snapshot.status_code == 200

    def test_open_data_source_fallback_creates_snapshot(self):
        source = OpenDataSource()
        # Even when open data API times out or is offline, it falls back to MockSource transparently
        data = source.fetch_company_info("800197268-4")

        assert data is not None
        assert data["nit"] == "800197268-4"
        assert DataSourceSnapshot.objects.count() >= 1
