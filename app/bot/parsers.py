"""D-03 — Parser de texto libre del bot.

Extrae de un mensaje suelto del usuario: placa vehicular, precio y documento (DNI).
Salida tipada con el schema `Extracted` (app/schemas/conversation.py). No toca la red.
"""

import re

from app.schemas.conversation import Extracted

# --- Placa ---------------------------------------------------------------
# El separador entre letras y dígitos puede ser guion, espacio o nada:
# "ABC-123", "ABC 123", "ABC123" → todos válidos.
# Auto particular Perú: 3 letras + 3 dígitos.
_PLATE_CAR = re.compile(r"(?<![A-Z0-9])([A-Z]{3})[-\s]?(\d{3})(?![A-Z0-9])")
# Moto: 4 dígitos + 2 letras  (1234-AB)  o  2 letras + 4 dígitos (AB-1234).
_PLATE_MOTO_A = re.compile(r"(?<![A-Z0-9])(\d{4})[-\s]?([A-Z]{2})(?![A-Z0-9])")
_PLATE_MOTO_B = re.compile(r"(?<![A-Z0-9])([A-Z]{2})[-\s]?(\d{4})(?![A-Z0-9])")

# --- Precio --------------------------------------------------------------
# "32 mil", "3.5 mil"  → multiplica por 1000.
_PRICE_MIL = re.compile(r"(\d+(?:[.,]\d+)?)\s*mil\b")
# "29k", "29 k"  → multiplica por 1000.
_PRICE_K = re.compile(r"(\d+(?:[.,]\d+)?)\s*k\b")
# "S/ 32,000", "s/. 45,500.50", "S/29.000"  → con prefijo de soles.
_PRICE_SOLES = re.compile(r"s/\.?\s*(\d{1,3}(?:[.,]\d{3})+(?:\.\d+)?|\d+(?:[.,]\d+)?)")
# Número suelto 4-6 dígitos (o con separador de miles), sin pegarse a letras/guion
# (evita capturar el "1234" de una placa de moto o los 8 dígitos de un DNI).
_PRICE_PLAIN = re.compile(
    r"(?<![\w-])(\d{1,3}(?:[.,]\d{3})+(?:\.\d+)?|\d{4,6}(?:\.\d+)?)(?![\w-])"
)

# Grupos de miles con coma o punto: "29,000" / "29.000" / "1.234.567".
_GROUPED_THOUSANDS = re.compile(r"^\d{1,3}(?:[.,]\d{3})+$")

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


def format_plate_display(plate: str | None) -> str:
    """Formatea una placa normalizada para mostrarla con guion (ej. COH099 → COH-099)."""
    if not plate:
        return "?"
    p = plate.strip().upper().replace("-", "").replace(" ", "")
    if re.fullmatch(r"[A-Z]{3}\d{3}", p):          # auto: ABC-123
        return f"{p[:3]}-{p[3:]}"
    if re.fullmatch(r"\d{4}[A-Z]{2}", p):          # moto A: 1234-AB
        return f"{p[:4]}-{p[4:]}"
    if re.fullmatch(r"[A-Z]{2}\d{4}", p):          # moto B: AB-1234
        return f"{p[:2]}-{p[2:]}"
    if re.fullmatch(r"[A-Z]\d[A-Z]\d{3}", p):      # trimoto: A1B-234
        return f"{p[:3]}-{p[3:]}"
    return p


def _to_amount(s: str) -> float:
    """Convierte un número textual a float respetando el formato peruano.

    Coma = separador de miles; punto = decimal. Pero también acepta el punto como
    separador de miles cuando el número viene agrupado de a 3 (ej. "29.000" → 29000).
    """
    s = s.strip()
    if _GROUPED_THOUSANDS.fullmatch(s):
        return float(s.replace(".", "").replace(",", ""))
    return float(s.replace(",", ""))


def parse_price(text: str) -> float | None:
    """Devuelve el precio en soles (float) o None.

    Soporta "32 mil", "29k", "S/32,000", "S/29.000", "32000 soles". El separador de
    miles puede ser coma o punto (agrupado de a 3); el punto suelto es decimal.
    """
    t = text.lower()

    m = _PRICE_MIL.search(t)
    if m:
        return float(m.group(1).replace(",", ".")) * 1000

    m = _PRICE_K.search(t)
    if m:
        return float(m.group(1).replace(",", ".")) * 1000

    m = _PRICE_SOLES.search(t)
    if m:
        return _to_amount(m.group(1))

    m = _PRICE_PLAIN.search(t)
    if m:
        return _to_amount(m.group(1))

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
