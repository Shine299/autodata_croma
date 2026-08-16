"""D-06 — Tests del formateo del veredicto.

Verifican el DoD: cada veredicto produce su emoji de semáforo, aparecen headline y
todos los flags, y ninguna línea usa `|` de tabla (heurística de "no scroll horizontal").
"""

import json
from pathlib import Path

import pytest

from app.bot.formatters import format_verdict
from app.bot.parsers import format_plate_display

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "fixture,emoji",
    [
        ("verification_go.json", "🟢"),
        ("verification_caution.json", "🟡"),
        ("verification_stop.json", "🔴"),
    ],
)
def test_verdict_emoji_present(fixture, emoji):
    text = format_verdict(_load(fixture))
    assert emoji in text


def test_headline_and_plate_present():
    data = _load("verification_stop.json")
    text = format_verdict(data)
    assert data["headline"] in text
    # La placa se muestra con guion (COH099 → COH-099).
    assert format_plate_display(data["plate"]) in text


def test_all_flags_rendered():
    data = _load("verification_stop.json")
    text = format_verdict(data)
    for flag in data["flags"]:
        assert flag["title"] in text


@pytest.mark.parametrize(
    "fixture",
    ["verification_go.json", "verification_caution.json", "verification_stop.json"],
)
def test_no_table_pipes(fixture):
    """Sin `|`: nada de tablas → no fuerza scroll horizontal en el celular."""
    text = format_verdict(_load(fixture))
    assert "|" not in text


def test_capped_sources_warning_shown():
    text = format_verdict(_load("verification_caution.json"))
    assert "5/6" in text
    assert "⚠️" in text
