import re
from django.core.exceptions import ValidationError


def calculate_verification_digit(nit_num: str) -> str:
    """
    Calcula el Dígito de Verificación (DV) de un NIT según el algoritmo módulo 11 de la DIAN.
    """
    if not nit_num or not nit_num.isdigit():
        raise ValueError("El NIT debe ser una cadena numérica.")

    weights = [71, 67, 59, 53, 47, 43, 41, 37, 29, 23, 19, 17, 13, 7, 3]
    nit_padded = nit_num.zfill(15)
    
    total = sum(int(nit_padded[i]) * weights[i] for i in range(15))
    remainder = total % 11

    if remainder in (0, 1):
        return str(remainder)
    return str(11 - remainder)


def validate_and_clean_nit(nit_raw: str) -> tuple[str, str]:
    """
    Limpia y valida un NIT colombiano. Retorna una tupla (nit_clean, dv_calculated).
    Acepta formatos: '900.123.456-7', '9001234567', '900123456-7', '900123456'.
    """
    if not nit_raw or not isinstance(nit_raw, str):
        raise ValidationError("El NIT proporcionado es inválido.")

    # Remove dots and spaces
    cleaned = re.sub(r"[\.\s]", "", nit_raw.strip())
    
    # Check if format has hyphens e.g. 900123456-7
    if "-" in cleaned:
        parts = cleaned.split("-")
        if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
            raise ValidationError("Formato de NIT inválido. Ejemplo válido: 900123456-7.")
        nit_num, provided_dv = parts[0], parts[1]
    else:
        if not cleaned.isdigit():
            raise ValidationError("El NIT solo debe contener dígitos numéricos.")
        if len(cleaned) == 10:
            nit_num, provided_dv = cleaned[:9], cleaned[9:]
        else:
            nit_num = cleaned
            provided_dv = None

    if len(nit_num) < 6 or len(nit_num) > 12:
        raise ValidationError("La longitud del NIT es inválida.")

    expected_dv = calculate_verification_digit(nit_num)

    if provided_dv is not None and provided_dv != expected_dv:
        raise ValidationError(
            f"El dígito de verificación {provided_dv} no corresponde al NIT {nit_num}. Esperado: {expected_dv}."
        )

    formatted_nit = f"{nit_num}-{expected_dv}"
    return formatted_nit, expected_dv
