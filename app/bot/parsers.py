"""D-03 — Parser de texto libre del bot.

Extrae de un mensaje suelto del usuario: placa vehicular, precio y documento (DNI).
Salida tipada con el schema `Extracted` (app/schemas/conversation.py). No toca la red.
"""

import re

from app.schemas.conversation import Extracted

# --- Placa ---------------------------------------------------------------
# Auto particular Perú: 3 letras + 3 dígitos (ABC-123 / ABC123).
_PLATE_CAR = re.compile(r"(?<![A-Z0-9])([A-Z]{3})-?(\d{3})(?![A-Z0-9])")
# Moto: 4 dígitos + 2 letras  (1234-AB)  o  2 letras + 4 dígitos (AB-1234).
_PLATE_MOTO_A = re.compile(r"(?<![A-Z0-9])(\d{4})-?([A-Z]{2})(?![A-Z0-9])")
_PLATE_MOTO_B = re.compile(r"(?<![A-Z0-9])([A-Z]{2})-?(\d{4})(?![A-Z0-9])")

# --- Precio --------------------------------------------------------------
# "32 mil", "3.5 mil"  → multiplica por 1000.
_PRICE_MIL = re.compile(r"(\d+(?:[.,]\d+)?)\s*mil\b")
# "S/ 32,000", "s/. 45,500.50"  → con prefijo de soles.
_PRICE_SOLES = re.compile(r"s/\.?\s*(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)")
# Número suelto 4-6 dígitos (o con separador de miles), sin pegarse a letras/guion
# (evita capturar el "1234" de una placa de moto o los 8 dígitos de un DNI).
_PRICE_PLAIN = re.compile(
    r"(?<![\w-])(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d{4,6}(?:\.\d+)?)(?![\w-])"
)

# --- Documento (DNI Perú = 8 dígitos) ------------------------------------
_DNI = re.compile(r"(?<!\d)(\d{8})(?!\d)")


def parse_plate(text: str) -> str | None:
    """Devuelve la placa normalizada (sin guion, mayúsculas) o None."""
    t = text.upper()
    for pattern in (_PLATE_CAR, _PLATE_MOTO_A, _PLATE_MOTO_B):
        m = pattern.search(t)
        if m:
            return m.group(1) + m.group(2)
    return None


def parse_price(text: str) -> float | None:
    """Devuelve el precio en soles (float) o None.

    Soporta "32 mil", "S/32,000", "32000 soles". El separador de miles es la
    coma (formato peruano); el punto es decimal.
    """
    t = text.lower()

    m = _PRICE_MIL.search(t)
    if m:
        return float(m.group(1).replace(",", ".")) * 1000

    m = _PRICE_SOLES.search(t)
    if m:
        return float(m.group(1).replace(",", ""))

    m = _PRICE_PLAIN.search(t)
    if m:
        return float(m.group(1).replace(",", ""))

    return None


def parse_document(text: str) -> str | None:
    """Devuelve el DNI (8 dígitos) o None. No confunde con precios ni teléfonos."""
    m = _DNI.search(text)
    return m.group(1) if m else None


def parse_free_text(text: str) -> Extracted:
    """Extrae placa, precio y documento de un mensaje libre en un solo `Extracted`."""
    return Extracted(
        plate=parse_plate(text),
        asking_price=parse_price(text),
        document_number=parse_document(text),
    )
