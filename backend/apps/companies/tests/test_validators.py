import pytest
from django.core.exceptions import ValidationError
from apps.companies.validators import calculate_verification_digit, validate_and_clean_nit


def test_calculate_verification_digit():
    # Known real Colombian NITs and their official DVs
    assert calculate_verification_digit("800197268") == "4"  # Bancolombia
    assert calculate_verification_digit("890900943") == "1"  # EPM
    assert calculate_verification_digit("860003020") == "1"  # Grupo Éxito


def test_validate_and_clean_nit_valid_formats():
    nit, dv = validate_and_clean_nit("800.197.268-4")
    assert nit == "800197268-4"
    assert dv == "4"

    nit, dv = validate_and_clean_nit("8001972684")
    assert nit == "800197268-4"
    assert dv == "4"

    nit, dv = validate_and_clean_nit("800197268")
    assert nit == "800197268-4"
    assert dv == "4"


def test_validate_and_clean_nit_invalid_dv():
    with pytest.raises(ValidationError) as excinfo:
        validate_and_clean_nit("800197268-9")  # Correct DV is 4
    assert "El dígito de verificación 9 no corresponde" in str(excinfo.value)


def test_validate_and_clean_nit_invalid_format():
    with pytest.raises(ValidationError):
        validate_and_clean_nit("INVALID_NIT_STRING")
