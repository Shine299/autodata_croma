"""Configuración global de la suite.

Regla del proyecto (Art. III de la constitución): los tests NUNCA tocan la cuota real
de Croma ni la API de IA. Aunque `.env` esté en `CROMA_MODE=live` para el runtime del
bot/demo, aquí forzamos `mock` y desactivamos Gemini en cada test.

`CromaClient.call` lee `settings.croma_mode` en tiempo de ejecución, así que basta con
fijar el atributo en el singleton compartido antes de cada test.
"""

import pytest

from app.config import settings


@pytest.fixture(autouse=True)
def _mock_mode_no_llm():
    prev_mode = settings.croma_mode
    prev_key = settings.gemini_api_key
    settings.croma_mode = "mock"
    settings.gemini_api_key = ""  # gemini.is_enabled() -> False => fallback determinista
    yield
    settings.croma_mode = prev_mode
    settings.gemini_api_key = prev_key
