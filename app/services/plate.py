"""C-02 — Validación y normalización de placas peruanas.

Reglas del Registro de Propiedad Vehicular (Perú):
- Auto particular / comercial estándar: 3 letras + 3 dígitos (ej: ABC-123, ABC123).
- Trimotos / Mototaxis / Especiales: 1 letra + 1 dígito + 1 letra + 3 dígitos (ej: A1B-234, A1B234).
- Motos formato A: 4 dígitos + 2 letras (ej: 1234-AB, 1234AB).
- Motos formato B: 2 letras + 4 dígitos (ej: AB-1234, AB1234).

Toda placa válida se normaliza a mayúsculas y sin guiones (ej: ABC123, 1234AB).
"""

import re

# Formatos válidos de placa vehicular en Perú (con o sin guion opcional)
_PLATE_CAR = re.compile(r"^([A-Za-z]{3})-?(\d{3})$")
_PLATE_TRIMOTO = re.compile(r"^([A-Za-z]\d[A-Za-z])-?(\d{3})$")
_PLATE_MOTO_A = re.compile(r"^(\d{4})-?([A-Za-z]{2})$")
_PLATE_MOTO_B = re.compile(r"^([A-Za-z]{2})-?(\d{4})$")

_PATTERNS = (_PLATE_CAR, _PLATE_TRIMOTO, _PLATE_MOTO_A, _PLATE_MOTO_B)


def is_valid_plate(plate: str) -> bool:
    """Verifica si el string corresponde a un formato válido de placa peruana."""
    if not plate or not isinstance(plate, str):
        return False
    p = plate.strip()
    return any(pattern.match(p) is not None for pattern in _PATTERNS)


def normalize_plate(plate: str) -> str:
    """Normaliza una placa peruana a mayúsculas sin guiones.

    Raises:
        ValueError: Si la placa no tiene un formato válido (code: 'invalid_plate').
    """
    if not plate or not isinstance(plate, str):
        raise ValueError("invalid_plate")

    p = plate.strip()
    for pattern in _PATTERNS:
        match = pattern.match(p)
        if match:
            part1, part2 = match.groups()
            return f"{part1.upper()}{part2.upper()}"

    raise ValueError("invalid_plate")
