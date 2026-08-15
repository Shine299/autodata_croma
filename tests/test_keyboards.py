"""D-07 — Tests del teclado inline.

Verifican el DoD: existen los 4 botones con su callback_data exacto y ninguno queda
sin acción (todos tienen respuesta y/o transición de estado definida en handlers).
"""

from app.bot.handlers import _CB_NEXT_STATE, _CB_REPLIES, on_callback  # noqa: F401
from app.bot.keyboards import (
    CB_APPRAISE,
    CB_DETAIL,
    CB_NEW,
    CB_SELLER,
    verdict_keyboard,
)


def _all_buttons(markup):
    return [btn for row in markup.inline_keyboard for btn in row]


def test_keyboard_has_four_buttons():
    buttons = _all_buttons(verdict_keyboard("ver_1"))
    assert len(buttons) == 4


def test_callback_data_prefixes():
    buttons = _all_buttons(verdict_keyboard("ver_1"))
    data = [b.callback_data for b in buttons]
    assert f"{CB_DETAIL}:ver_1" in data
    assert f"{CB_APPRAISE}:ver_1" in data
    assert f"{CB_SELLER}:ver_1" in data
    assert f"{CB_NEW}:" in data


def test_every_button_has_a_reply():
    """Ningún botón muerto: cada acción tiene copy de respuesta en el router."""
    for action in (CB_DETAIL, CB_APPRAISE, CB_SELLER, CB_NEW):
        assert action in _CB_REPLIES


def test_labels_non_empty():
    for btn in _all_buttons(verdict_keyboard("ver_1")):
        assert btn.text.strip()
