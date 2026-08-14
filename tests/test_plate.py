"""Tests para C-02: Normalización y validación de placas vehiculares."""

import pytest

from app.services.plate import is_valid_plate, normalize_plate


# 10 casos estructurados para validar y normalizar placas
VALID_CASES = [
    ("ABC-123", "ABC123"),       # 1. Auto con guión
    ("abc123", "ABC123"),        # 2. Auto minúsculas sin guión
    ("D0H-741", "D0H741"),       # 3. Auto/camioneta con número al medio y guión
    ("A1B-234", "A1B234"),       # 4. Trimoto / mototaxi con guión
    ("a1b234", "A1B234"),        # 5. Trimoto sin guión minúsculas
    ("1234-AB", "1234AB"),       # 6. Moto formato A con guión (4 dígitos + 2 letras)
    ("5678cd", "5678CD"),        # 7. Moto formato A sin guión
    ("AB-1234", "AB1234"),       # 8. Moto formato B con guión (2 letras + 4 dígitos)
    ("xy9999", "XY9999"),        # 9. Moto formato B sin guión
    ("  Z9X-001  ", "Z9X001"),   # 10. Auto con espacios en blanco
]

INVALID_CASES = [
    "ABC-12",         # Incompleta
    "ABC-1234",       # Auto con exceso de dígitos
    "123-ABC",        # Formato invertido inválido
    "ABCD-123",       # Exceso de letras
    "INVALID",        # Texto arbitrario
    "",               # Vacío
    "   ",            # Espacios
    "AB@123",         # Símbolo no permitido
    "12-34-56",       # Formato numérico ajeno
    "12345-AB",       # Moto con 5 dígitos
]


@pytest.mark.parametrize("input_plate,expected", VALID_CASES)
def test_valid_plates_normalization(input_plate: str, expected: str):
    assert is_valid_plate(input_plate) is True
    assert normalize_plate(input_plate) == expected


@pytest.mark.parametrize("invalid_plate", INVALID_CASES)
def test_invalid_plates_rejection(invalid_plate: str):
    assert is_valid_plate(invalid_plate) is False
    with pytest.raises(ValueError, match="invalid_plate"):
        normalize_plate(invalid_plate)
