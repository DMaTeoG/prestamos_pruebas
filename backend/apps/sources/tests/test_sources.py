import pytest
from unittest.mock import patch, MagicMock
from apps.sources.services import MockSource, OpenDataSource, build_retry_session, _format_registration_date
from apps.sources.models import DataSourceSnapshot


# ==============================================================================
# Semana 1: Patrón AAA (Arrange, Act, Assert)
# Semana 2: Parametrización (@pytest.mark.parametrize)
# ==============================================================================


@pytest.mark.django_db
class TestDataSources:
    @pytest.mark.parametrize(
        "raw_date,expected_formatted",
        [
            ("20150331", "2015-03-31"),   # Formato numérico YYYYMMDD
            ("2020-05-15", "2020-05-15"), # Formato estándar ISO YYYY-MM-DD
            (None, "2020-01-01"),         # Valor por defecto ante fecha nula
        ],
    )
    def test_format_registration_date_parametrized_aaa(self, raw_date, expected_formatted):
        """Prueba parametrizada de formateo de fechas con patrón AAA."""
        # Arrange
        input_date = raw_date

        # Act
        formatted_date = _format_registration_date(input_date)

        # Assert
        assert formatted_date == expected_formatted

    def test_retry_session_configuration_aaa(self):
        """Verifica la configuración del adaptador HTTP de reintentos con AAA."""
        # Arrange & Act: Construcción de la sesión resiliente
        session = build_retry_session(retries=2, backoff_factor=0.3)
        adapter = session.get_adapter("https://www.datos.gov.co/")

        # Assert: Aserciones sobre las políticas de reintento
        assert adapter.max_retries.total == 2
        assert 503 in adapter.max_retries.status_forcelist
        session.close()

    def test_mock_source_returns_valid_dict_and_snapshot_aaa(self):
        """Verifica la fuente de respaldo MockSource con AAA."""
        # Arrange
        source = MockSource()
        nit_to_fetch = "900123456-7"

        # Act
        data = source.fetch_company_info(nit_to_fetch)

        # Assert
        assert data["nit"] == nit_to_fetch
        assert "EMPRESA SIMULADA" in data["legal_name"]
        assert data["origin"] == "MOCK"

        snapshot = DataSourceSnapshot.objects.filter(nit=nit_to_fetch).first()
        assert snapshot is not None
        assert snapshot.source_name == "MockSource"
        assert snapshot.status_code == 200

    def test_open_data_source_success_parsing_aaa(self):
        """Verifica el parsing exitoso de Open Data simulado con AAA."""
        # Arrange
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

        # Act
        with patch("requests.Session.get", return_value=mock_response):
            data = source.fetch_company_info("900170781-7")

        # Assert
        assert data["legal_name"] == "ESCANHER ABOGADOS SAS"
        assert data["ciiu"] == "6910"
        assert data["city"] == "Bogota"
        assert data["registration_date"] == "2007-09-04"
        assert data["origin"] == "PUBLIC"
        assert data["status"] == "ACTIVA"

        snapshot = DataSourceSnapshot.objects.filter(nit="900170781-7", source_name="datos.gov.co").first()
        assert snapshot is not None
        assert snapshot.status_code == 200

    def test_open_data_source_fallback_creates_snapshot_aaa(self):
        """Verifica resiliencia y fallback transparente ante indisponibilidad con AAA."""
        # Arrange
        source = OpenDataSource()
        nit_fallback = "800197268-4"

        # Act
        data = source.fetch_company_info(nit_fallback)

        # Assert
        assert data is not None
        assert data["nit"] == nit_fallback
        assert DataSourceSnapshot.objects.count() >= 1
