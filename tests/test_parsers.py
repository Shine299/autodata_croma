"""D-03 — 15 casos del parser de texto libre (placa, precio, DNI)."""

import pytest

from app.bot.parsers import parse_free_text, parse_plate, parse_price, parse_document

# (texto, plate, asking_price, document_number)
CASES = [
    ("ABC-123 me lo dan a 32 mil", "ABC123", 32000, None),   # caso ancla del DoD
    ("abc123", "ABC123", None, None),
    ("La placa es XYZ-789", "XYZ789", None, None),
    ("S/32,000", None, 32000, None),
    ("cuesta 32000 soles", None, 32000, None),
    ("me piden S/. 45,500", None, 45500, None),
    ("32 mil", None, 32000, None),
    ("vale 3.5 mil", None, 3500, None),
    ("DNI 12345678", None, None, "12345678"),
    ("mi documento es 87654321", None, None, "87654321"),
    ("placa PQR-456, precio 28 mil, dni 11223344", "PQR456", 28000, "11223344"),
    ("el auto ABC456 esta a S/ 15,000 y su dni 99887766", "ABC456", 15000, "99887766"),
    ("placa 1234-AB", "1234AB", None, None),      # moto: no leer 1234 como precio
    ("mi numero es 987654321", None, None, None),  # telefono 9 digitos != DNI
    ("no hay nada util aca", None, None, None),
]


@pytest.mark.parametrize("text,plate,price,doc", CASES)
def test_parse_free_text(text, plate, price, doc):
    result = parse_free_text(text)
    assert result.plate == plate
    assert result.asking_price == price
    assert result.document_number == doc


def test_plate_normaliza_guion_y_mayusculas():
    assert parse_plate("abc-123") == "ABC123"


def test_precio_mil_y_soles():
    assert parse_price("32 mil") == 32000
    assert parse_price("S/32,000") == 32000


def test_dni_no_captura_precio():
    assert parse_document("cuesta 32000") is None
