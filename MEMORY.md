# AutoData — Estado del Proyecto

> **Agentes de IA: lean este archivo ANTES de tocar código.**
> Es la fuente de verdad sobre qué existe, qué falta y qué reglas respetar.

**Proyecto:** AutoData — Verificación vehicular + vendedor para Perú via Croma
**Hackathon:** GOV-TECH Croma · Entrega: **16 ago 2026, 6:30 p.m.**
**Rama activa:** `joaquin_sprint1`
**Sprint actual:** Sprint 1 — "Los datos entran"
**Última actualización:** 2026-08-14 (P3 cerró A-04, D-01, D-03)

---

## Sprint 1 — Estado de tareas

### Completado

| ID | Tarea | Dueño | Archivos |
|----|-------|-------|----------|
| A-01 | Estructura de carpetas, FastAPI, `/api/v1/health` → 200 | P1 | `app/main.py`, `app/api/health.py` |
| A-02 | Schemas Pydantic (7 recursos completos) | P1 | `app/schemas/` — vehicle, seller, verification, appraisal, conversation, job, health, common |
| A-05 | `.env.example` con todas las variables | P1 | `.env.example` |
| B-01 | `CromaClient` con httpx async, auth, timeout 40s | P1 | `app/integrations/croma/client.py` |
| B-02 | Modo mock: lee `fixtures/*.json` cuando `CROMA_MODE=mock` | P1 | `_mock_call()` en client.py |
| A-06 | 1 fixture real de Croma (3 fuentes) | P1 | `fixtures/sutran_sample.json`, `apeseg_soat_sample.json`, `sbs_soat_sample.json` |
| B-05 | Backoff en 429 con `Retry-After`, máx 2 reintentos | P1 | Tests en `tests/test_croma_client.py` (6 tests) |
| — | Config centralizada con pydantic-settings | P1 | `app/config.py` |
| — | `docs/quota-log.md` estructura lista | P1 | Tabla vacía, llenar al hacer llamadas `live` |
| A-03 | Proyecto Supabase + DDL de las 5 tablas | P4 | `croma_cache`, `verifications`, `appraisals`, `quota_log`, `conversations` — verificadas OK |
| A-04 | Bot @autodata_peru_bot creado, token en `.env`, responde desde el celular | P3 | Token en `.env` local (no versionado). Probado desde celular OK |
| D-01 | Esqueleto del bot: polling + `/start` + `/ayuda` (< 2 s) | P3 | `app/bot/main.py`, `app/bot/handlers.py`. Copy de `/start`/`/ayuda` es placeholder → **P5** cierra el tono |
| D-03 | Parser de texto libre: placa, precio, DNI | P3 | `app/bot/parsers.py`, `tests/test_parsers.py` — 18 tests verdes (15 casos + 3). Retorna schema `Extracted` |

### Pendiente

| ID | Tarea | Dueño | Notas |
|----|-------|-------|-------|
| A-07 | Prompts base para agentes | P5 | `08-PROMPTS.md` existe en `files/` |
| B-03 | Cache read-through contra `croma_cache` con TTL | P4 | No existe `app/repositories/cache_repo.py` |
| B-04 | Logging de cuota en tabla `quota_log` | P4 | Actualmente solo `print()`, no persiste |
| B-06 | Adapter SBS SOAT → schema `Insurance` | P2 | No existe `app/integrations/croma/sources/` |
| B-07 | Adapter APESEG SOAT + merge con SBS | P2 | — |
| B-08 | Adapter SUTRAN → schema `Infractions` | P2 | — |
| B-09 | Adapter Callao papeletas → merge en `Infractions` | P2 | — |
| B-10 | Adapter SAT Lima cuenta → schema `TaxDebt` | P2 | — |
| B-11 | Adapter SAT Lima capturas → schema `CaptureOrder` | P2 | — |
| C-02 | Validacion/normalizacion de placa | P2 | — |
| C-11 | `GET /api/v1/quota` con datos reales | P4 | — |
| E-02 | Landing page (1 pantalla con pitch) | P5 | `app/web/templates/` vacío |

---

## Avisos / handoffs entre roles

**→ P5 (de P3):** El parser de texto libre (**D-03**) ya está listo y verde.
- Código: `app/bot/parsers.py` — función `parse_free_text(text) -> Extracted` (placa, `asking_price`, `document_number`).
- Tests: `tests/test_parsers.py` → 18 verdes, incluye el caso ancla `"ABC-123 me lo dan a 32 mil"`.
- **Acción para P5:** en la **Puerta 1** te toca ejecutar la prueba "el parser acierta en 15 frases distintas (≥13/15)". Ya puedes encolarla; corre `pytest tests/test_parsers.py -q`. Si quieres agregar tus propias frases, mételas a `CASES` en ese test.
- Pendiente menor: el copy de `/start` y `/ayuda` (`app/bot/handlers.py`) es **placeholder** marcado `# copy final: P5`. El tono peruano lo cierras tú (`07-AGENTS.md §"Qué NO delegar"`).

**Bot vivo:** `@autodata_peru_bot`. Levantar con polling (ver "Cómo correr el bot" abajo).

---

## Cómo correr el bot (P3)

Desde la raíz del repo, en PowerShell:

```powershell
.\.venv\Scripts\python.exe -m app.bot.main
```

Requiere `TELEGRAM_BOT_TOKEN` en `.env` (A-04). Corre en modo polling; se detiene con `Ctrl+C`.
El `!` que usa Claude Code **no** va en PowerShell normal.

---

## Decisiones tecnicas ya tomadas

1. **Modo mock por default** — `CROMA_MODE=mock` en `.env`. Nadie gasta cuota sin autorizacion de P1.
2. **Schemas congelados** — `app/schemas/` solo los toca P1. Son el contrato de `03-API-DESIGN.md`.
3. **CromaClient ya existe** — Usar `app/integrations/croma/client.py`, no crear otro cliente HTTP. Interfaz: `await client.call(source, path, body, cache_key=..., ttl=...)` → `SourceResult`.
4. **`SourceResult` es dataclass** — en `app/integrations/croma/models.py`. Campos: `source, status, data, error, latency_ms, from_cache`.
5. **Fixtures por nombre** — patron: `fixtures/{source}_{lookup}.json` o `fixtures/{source}_sample.json` como fallback.
6. **Config en `app/config.py`** — `from app.config import settings`. Pydantic-settings lee de `.env`.
7. **FastAPI + httpx + python-telegram-bot v21** — stack definido, no agregar dependencias nuevas sin justificacion.
8. **Cuota limitada** — 100 requests/dia para TODO el equipo. ~5-6 requests por verificacion = ~16 verificaciones/dia max.

## Regla de dueño por carpeta

| Persona | Carpetas |
|---------|----------|
| P1 | `app/integrations/`, `app/core/`, `app/config.py`, `fixtures/`, `app/schemas/` |
| P2 | `app/services/`, `app/api/vehicles.py`, `app/api/verifications.py` |
| P3 | `app/bot/` |
| P4 | `app/repositories/`, `app/api/sellers.py`, `app/api/health.py`, migraciones |
| P5 | `app/web/`, `docs/`, textos y copy |

**No tocar carpetas de otro dueño sin coordinarse.**

---

## Que viene despues (Sprint 2 — "El producto decide")

> NO implementar Sprint 2 hasta que Puerta 1 cierre en verde.

Sprint 2 agrega: orquestacion concurrente (B-14), scoring/veredicto (C-04), endpoint de verificacion completa (C-05), tasacion (C-06), flujo conversacional del bot (D-02, D-04-D-07), verificacion de vendedor (B-12, B-13, C-03), pagina web del reporte (E-01).

---

## Reglas para agentes de IA

1. **Leer `files/00-CONTEXTO.md` a `files/04-PLAN-TECNICO.md`** antes de implementar.
2. **Respetar el contrato de API** de `files/03-API-DESIGN.md` — es ley.
3. **Nunca usar `CROMA_MODE=live`** sin autorizacion explicita de P1.
4. **Respetar dueño de carpeta** — ver tabla arriba.
5. **No agregar dependencias** sin justificacion. El `requirements.txt` actual basta para Sprint 1.
6. **Tests obligatorios** para logica no trivial. Usar `pytest` + `pytest-asyncio`.
7. **No crear archivos `.md` de documentacion** extra. Este archivo y `files/` son suficientes.
8. **Modo mock es el default** — todo desarrollo se hace sin tocar la red.

---

## Como actualizar este archivo

Cada vez que cierres una tarea:
1. Mueve la fila de "Pendiente" a "Completado" con los archivos creados/modificados.
2. Actualiza la fecha de "Ultima actualizacion".
3. Commitea el cambio junto con tu codigo.
