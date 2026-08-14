# AutoData — Estado del Proyecto

> **Agentes de IA: lean este archivo ANTES de tocar código.**
> Es la fuente de verdad sobre qué existe, qué falta y qué reglas respetar.

**Proyecto:** AutoData — Verificación vehicular + vendedor para Perú via Croma
**Hackathon:** GOV-TECH Croma · Entrega: **16 ago 2026, 6:30 p.m.**
**Rama activa:** `sprint1-arroz`
**Sprint actual:** Sprint 1 — "Los datos entran"
**Última actualización:** 2026-08-14 (P2 cerró C-04, C-05, C-06)

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
| A-03 | Proyecto Supabase + DDL de las 5 tablas | P4 | `migrations/schema.sql`, `app/core/database.py`, `app/repositories/models.py` (verificadas OK) |
| B-03 | Cache read-through contra `croma_cache` con TTL | P4 | `app/repositories/cache_repo.py`, `app/integrations/croma/client.py` |
| B-04 | Logging de cuota en tabla `quota_log` | P4 | `app/repositories/quota_repo.py`, `app/integrations/croma/client.py` |
| C-11 | `GET /api/v1/quota` con datos reales | P4 | `app/api/quota.py`, `app/api/health.py`, `app/main.py` |
| — | Tests automatizados de persistencia, integración y APIs | P4 | `tests/test_persistence.py`, `tests/test_croma_client_integration.py`, `tests/test_api_endpoints.py`, `pytest.ini` |
| C-02 | Validación y normalización de placa (autos, motos A/B, trimotos) | P2 | `app/services/plate.py`, `tests/test_plate.py` (20 tests verdes) |
| B-06 | Adapter SBS SOAT → schema `Insurance` | P2 | `app/integrations/croma/sources/sbs.py`, `tests/test_adapters_insurance.py` |
| B-07 | Adapter APESEG SOAT + merge con SBS (`hasActiveSoat`, póliza vigente) | P2 | `app/integrations/croma/sources/apeseg.py`, `tests/test_adapters_insurance.py` |
| B-08 | Adapter SUTRAN → schema `Infractions` (`total` PEN, `severeCount`) | P2 | `app/integrations/croma/sources/sutran.py`, `tests/test_adapters_infractions.py` |
| B-09 | Adapter Callao papeletas + merge en `Infractions` (`source: CALLAO`) | P2 | `app/integrations/croma/sources/callao.py`, `fixtures/callao_sample.json`, `tests/test_adapters_infractions.py` |
| B-10 | Adapter SAT Lima cuenta → schema `TaxDebt` | P2 | `app/integrations/croma/sources/sat_debt.py`, `fixtures/sat_lima_sample.json`, `tests/test_adapters_sat.py` |
| B-11 | Adapter SAT Lima capturas → schema `CaptureOrder` | P2 | `app/integrations/croma/sources/sat_captures.py`, `fixtures/sat_capturas_sample.json`, `tests/test_adapters_sat.py` |
| C-04 | `scoring_service`: flags, riskScore y verdict | P2 | `app/services/scoring.py`, `tests/test_scoring.py` |
| C-05 | `POST /api/v1/verifications` orquestando datos | P2 | `app/api/verifications.py`, `tests/test_verifications.py` |
| C-06 | `appraisal_service` + `POST /verifications/{id}/appraisals` | P2 | `app/services/appraisal.py`, `tests/test_appraisal.py` |

### Pendiente

| ID | Tarea | Dueño | Notas |
|----|-------|-------|-------|
| A-07 | Prompts base para agentes | P5 | `08-PROMPTS.md` existe en `files/` |
| E-02 | Landing page (1 pantalla con pitch) | P5 | `app/web/templates/` vacío |

### Observaciones del review

- **P4 modificó `app/api/health.py`** — ahora incluye check de DB (`SELECT 1`). Mejora aceptable.
- **P4 `pytest.ini` usa `asyncio_mode = auto`** — la rama P1 usa `strict`. Unificar al mergear.
- **P4 `QuotaLogModel.id` usa `Integer`** en ORM pero DDL dice `BIGSERIAL`. Menor para hackathon.
- **P3 parser de moto** — el caso `1234-AB a 32 mil` (placa moto + precio) no está testeado. Bajo riesgo.

---

## Avisos / handoffs entre roles

**→ P1 / P3 (de P2):** Validación de placa (**C-02**) y los 6 adapters vehiculares (**B-06..B-11**) listos y testeados (35 tests verdes).
- Código de normalización: `app/services/plate.py` — funciones `normalize_plate(plate)` y `is_valid_plate(plate)`.
- Adapters y mergers: `app/integrations/croma/sources/` (`sbs.py`, `apeseg.py`, `sutran.py`, `callao.py`, `sat_debt.py`, `sat_captures.py`).
- Tests: `tests/test_plate.py`, `tests/test_adapters_insurance.py`, `tests/test_adapters_infractions.py`, `tests/test_adapters_sat.py`.
- **Acción para P1:** Ya puedes implementar **B-14** (concurrencia de 6 fuentes con `asyncio.gather`) consumiendo estos mappers.
- **Acción para P3:** En la **Puerta 1** puedes verificar que las 6 fuentes mapean y responden contra `SourceResult`.

**→ P1 / P3 / P4 / P5 (de P2):** Orquestación y reglas de negocio cerradas (**C-04, C-05, C-06**).
- **Acción para P3:** Ya puedes implementar **D-04** y **D-09** consumiendo los endpoints `POST /api/v1/verifications` y `POST /verifications/{id}/appraisals`.
- **Acción para P5:** El schema de tasación ya retorna el `negotiationScript` (C-07).
- **Acción para P4:** Cuando tengas **C-03** listo, reemplaza el mock en `app/services/sellers.py`.
- **Acción para P1:** Cuando tengas **C-01** listo, reemplaza el mock en `app/services/vehicles.py`.


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
