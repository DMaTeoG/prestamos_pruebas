import pytest
from django.core.exceptions import ValidationError

from apps.companies.validators import calculate_verification_digit, validate_and_clean_nit

# ==============================================================================
# Semana 1: Patrón AAA (Arrange, Act, Assert)
# Semana 2: Valores Límite (BVA) & Parametrización (@pytest.mark.parametrize)
# ==============================================================================


@pytest.mark.parametrize(
    "nit_base,expected_dv",
    [
        ("800197268", "4"),  # Bancolombia
        ("890900943", "1"),  # EPM
        ("860003020", "1"),  # Grupo Éxito
        ("900123456", "7"),  # NIT generado estándar
        ("800037015", "7"),  # DV cálculo módulo 11
    ],
)
def test_calculate_verification_digit_parametrized(nit_base: str, expected_dv: str):
    """Prueba unitaria parametrizada bajo el patrón estricto AAA."""
    # Arrange: Preparación del escenario y datos de prueba
    input_nit = nit_base

    # Act: Ejecución de la unidad de código bajo prueba
    calculated_dv = calculate_verification_digit(input_nit)

    # Assert: Verificación rigurosa del resultado obtenido vs esperado
    assert calculated_dv == expected_dv


@pytest.mark.parametrize(
    "invalid_input",
    [
        "",  # Cadena vacía
        "ABCDEFGHI",  # Caracteres no numéricos
        "80019726A",  # Alfanumérico
        "123-456",  # Guión no permitido en función base
    ],
)
def test_calculate_verification_digit_invalid_raises_value_error(invalid_input: str):
    """Verificación de entradas inválidas usando pytest.raises bajo patrón AAA."""
    # Arrange: Entrada no válida
    raw_input = invalid_input

    # Act & Assert: Debe levantar ValueError para entradas no numéricas
    with pytest.raises(ValueError) as exc_info:
        calculate_verification_digit(raw_input)

    assert "debe ser una cadena numérica" in str(exc_info.value)


@pytest.mark.parametrize(
    "raw_nit,expected_formatted,expected_dv",
    [
        ("800.197.268-4", "800197268-4", "4"),  # Con puntos y guion
        ("8001972684", "800197268-4", "4"),      # 10 dígitos continuos (9 dígitos + DV)
        ("800197268", "800197268-4", "4"),       # 9 dígitos sin DV (autocálculo)
        (" 800.197.268 - 4 ", "800197268-4", "4"),  # Espacios en blanco
    ],
)
def test_validate_and_clean_nit_valid_formats(raw_nit: str, expected_formatted: str, expected_dv: str):
    """Validación DRY de múltiples formatos válidos de entrada."""
    # Arrange
    data = raw_nit

    # Act
    formatted_nit, calculated_dv = validate_and_clean_nit(data)

    # Assert
    assert formatted_nit == expected_formatted
    assert calculated_dv == expected_dv


# ------------------------------------------------------------------------------
# Análisis de Valores Límite (Boundary Value Analysis - BVA)
# Longitud del NIT: Mínimo 6 dígitos, Máximo 12 dígitos
# ------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "boundary_nit_digits",
    [
        "100000",        # Límite inferior exacto (6 dígitos)
        "1000000",       # Límite inferior + 1 (7 dígitos)
        "12345678901",   # Límite superior - 1 (11 dígitos)
        "123456789012",  # Límite superior exacto (12 dígitos)
    ],
)
def test_validate_and_clean_nit_bva_valid_boundaries(boundary_nit_digits: str):
    """BVA: Valida las fronteras válidas de longitud permitida [6, 12]."""
    # Arrange
    nit_input = boundary_nit_digits

    # Act
    formatted_nit, dv = validate_and_clean_nit(nit_input)

    # Assert
    assert formatted_nit.startswith(nit_input)
    assert dv is not None
    assert len(dv) == 1


@pytest.mark.parametrize(
    "invalid_boundary_nit",
    [
        "12345",          # Límite inferior - 1 (5 dígitos: Inválido)
        "1234",           # Por debajo del límite inferior (4 dígitos)
        "1234567890123",  # Límite superior + 1 (13 dígitos: Inválido)
    ],
)
def test_validate_and_clean_nit_bva_invalid_boundaries(invalid_boundary_nit: str):
    """BVA: Rechaza longitudes fuera de los límites de frontera con pytest.raises."""
    # Arrange
    out_of_bounds_nit = invalid_boundary_nit

    # Act & Assert
    with pytest.raises(ValidationError) as excinfo:
        validate_and_clean_nit(out_of_bounds_nit)

    assert "longitud del NIT es inválida" in str(excinfo.value)


@pytest.mark.parametrize(
    "corrupted_dv_nit,wrong_dv",
    [
        ("800197268-9", "9"),  # DV correcto es 4
        ("890900943-7", "7"),  # DV correcto es 1
        ("860003020-5", "5"),  # DV correcto es 1
    ],
)
def test_validate_and_clean_nit_invalid_dv_rejection(corrupted_dv_nit: str, wrong_dv: str):
    """Valida rechazo de Dígito de Verificación inconsistente con pytest.raises."""
    # Arrange
    nit_with_bad_dv = corrupted_dv_nit

    # Act & Assert
    with pytest.raises(ValidationError) as excinfo:
        validate_and_clean_nit(nit_with_bad_dv)

    assert f"El dígito de verificación {wrong_dv} no corresponde" in str(excinfo.value)
