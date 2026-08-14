# AutoData — Estado del Proyecto

> **Agentes de IA: lean este archivo ANTES de tocar código.**
> Es la fuente de verdad sobre qué existe, qué falta y qué reglas respetar.

**Proyecto:** AutoData — Verificación vehicular + vendedor para Perú via Croma
**Hackathon:** GOV-TECH Croma · Entrega: **16 ago 2026, 6:30 p.m.**
**Rama activa:** `testing`
**Sprint actual:** Sprint 2 — "El producto decide" → 🟨 **EN CURSO**
**Última actualización:** 2026-08-14 (Sprint 2: P1 B-14/C-09/C-10 + P3 D-02/D-06/D-07 — suite 86/86 verdes)

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
| B-06 | Adapter SBS SOAT → schema `Insurance` | P2 | `app/integrations/croma/sources/sbs.py`. Rama `carlos_p2_sprint1` |
| B-07 | Adapter APESEG SOAT + merge con SBS | P2 | `sources/apeseg.py` — `merge_insurance_sources()` |
| B-08 | Adapter SUTRAN → schema `Infractions` | P2 | `sources/sutran.py` — clasificación de severidad con fallback |
| B-09 | Adapter Callao papeletas → merge en `Infractions` | P2 | `sources/callao.py` — `merge_infractions()` |
| B-10 | Adapter SAT Lima cuenta → schema `TaxDebt` | P2 | `sources/sat_debt.py` |
| B-11 | Adapter SAT Lima capturas → schema `CaptureOrder` | P2 | `sources/sat_captures.py` |
| C-02 | Validación/normalización de placa | P2 | `app/services/plate.py` — 4 formatos peruanos, 20 tests en `tests/test_plate.py` |
| — | Fixtures SAT y Callao | P2 | `fixtures/callao_sample.json`, `sat_lima_sample.json`, `sat_capturas_sample.json` |
| — | Tests de adapters | P2 | `tests/test_adapters_insurance.py`, `test_adapters_infractions.py`, `test_adapters_sat.py` (16 tests) |
| A-07 | Prompts base del producto | P5 | `app/core/prompts.py` — 4 prompts: identidad, extracción, veredicto, negociación |
| E-02 | Landing page (1 pantalla con pitch) | P5 | `app/web/templates/landing.html`, `app/web/routes.py` — servida en `/` |

### Pendiente

Sprint 1 completo. No hay tareas pendientes. **Listo para arrancar Sprint 2.**

### Verificación de cierre (Puerta 1) — 2026-08-14

- ✅ **Suite completa: 65/65 tests en verde** en modo mock (sin gastar cuota).
- ✅ `app.main` importa; landing `/`, `/api/v1/health` y `/api/v1/quota` responden **200**.
- 🔧 **Entorno:** el `.venv` estaba incompleto → se corrió `pip install -r requirements.txt`. Sin ese install `app.main` no importa (falta `fastapi`) y 4 módulos de test no colectan (falta `sqlalchemy`). Usar siempre `.\.venv\Scripts\python.exe`.
- 🔧 **Fix aplicado en `app/api/quota.py`:** ahora degrada con gracia (try/except → 200 con `database: error: ...`) igual que `/health`, en vez de propagar stacktrace cuando la DB no responde. README actualizado con nota de install + sección "Verificar que arranca".
- ⚠️ **DB:** el `.env` apunta a una Supabase cuyo `DATABASE_URL` no resuelve DNS localmente; los tests usan el fallback SQLite en memoria de `app/core/database.py`. Validar la conexión real a Supabase en un entorno con red antes de la demo.

### Observaciones del review

- **P4 modificó `app/api/health.py`** — ahora incluye check de DB (`SELECT 1`). Mejora aceptable.
- **P4 `pytest.ini` usa `asyncio_mode = auto`** — la rama P1 usa `strict`. Unificar al mergear.
- **P4 `QuotaLogModel.id` usa `Integer`** en ORM pero DDL dice `BIGSERIAL`. Menor para hackathon.
- **P3 parser de moto** — el caso `1234-AB a 32 mil` (placa moto + precio) no está testeado. Bajo riesgo.

---

## Sprint 2 — Estado de tareas

### Completado — suite total 86/86 verdes

| ID | Tarea | Dueño | Archivos |
|----|-------|-------|----------|
| C-10 | Handler global de errores con envelope estándar | P1 | `app/main.py` (4 exception handlers), `tests/test_error_handler.py` (5 tests) |
| B-14 | Ejecución concurrente de 6 fuentes con `asyncio.gather` | P1 | `app/integrations/croma/orchestrator.py` (`fetch_all_sources`, `OrchestratorResult`), `tests/test_orchestrator.py` (4 tests) |
| C-09 | `GET /api/v1/jobs/{jobId}` + job store (shell — falta wiring `Prefer: respond-async` cuando C-05 exista) | P1 | `app/core/jobs.py` (`JobStore`, `JobState`), `app/api/jobs.py`, `tests/test_jobs.py` (5 tests) |
| D-02 | Máquina de estados (`IDLE→AWAITING_*→DONE`) persistida en `conversations` | P3 | `app/bot/states.py`, `app/repositories/models.py` (`ConversationModel`), `app/repositories/conversation_repo.py`, `on_text`+`next_state` en `app/bot/handlers.py`, `MessageHandler` en `app/bot/main.py`, `tests/test_conversation_repo.py` (7 tests) |
| D-06 | Formateo del veredicto con semáforo | P3 | `app/bot/formatters.py` (`format_verdict`), `tests/test_formatters.py` (9 tests) |
| D-07 | Botones inline (Ver detalle / Calcular precio / Verificar vendedor / Nueva consulta) | P3 | `app/bot/keyboards.py` (`verdict_keyboard`), `on_callback` router en `handlers.py`, `tests/test_keyboards.py` (4 tests) |

### Bloqueado (dependencias inexistentes)

| ID | Tarea | Bloqueado por |
|----|-------|---------------|
| D-04 | Bot → `POST /verifications` + manejo de errores (502 amable) | **C-05 (P2) no existe.** Pedir ETA a P2 |
| D-05 | Mensajes progresivos por fuente | C-09 GET listo ✅ — falta **C-05 (P2)** para el wiring completo |

> D-05 ya puede hacer polling a `GET /api/v1/jobs/{jobId}`. Falta que C-05 cree los jobs al recibir `Prefer: respond-async`.

### Pendiente Sprint 2

| ID | Tarea | Dueño | Bloqueado por |
|----|-------|-------|---------------|
| C-01 | `POST /vehicles/inspections` | P2 | B-14 ✅ listo — P2 importa `fetch_all_sources` de `app.integrations.croma.orchestrator` |
| C-04 | Scoring + veredicto (GO/CAUTION/STOP) | P2 | — |
| C-05 | `POST /verifications` (orquesta vehicle + seller + scoring) | P2 | C-01, C-04 |
| C-06 | Tasación: calcular precio justo | P2 | C-05 |
| B-12 | Adapter SUNAT → seller screening | P2 | — |
| B-13 | Adapter SAT Lima persona → deuda vendedor | P2 | — |
| C-03 | `POST /sellers/screenings` | P2 | B-12, B-13 |
| D-04 | Bot → POST /verifications | P3 | C-05 |
| D-05 | Mensajes progresivos por fuente | P3 | C-05 + C-09 wiring |
| E-01 | Página web del reporte de verificación | P5 | C-05 |

---

## Avisos / handoffs entre roles

**→ P2 (de P1):** B-14 orquestador concurrente **LISTO**.
- Importar: `from app.integrations.croma.orchestrator import fetch_all_sources, OrchestratorResult`
- Firma: `await fetch_all_sources(client, plate) -> OrchestratorResult` — devuelve `insurance`, `infractions`, `tax_debt`, `capture_order`, `sources_summary`, `unverified_sources`.
- **Acción para P2:** Implementar C-01 (`POST /vehicles/inspections`) envolviendo `OrchestratorResult` en `VehicleInspectionResponse` con `inspection_id` y timestamps.
- **Job store para C-05 async:** Cuando implementes `Prefer: respond-async` en C-05, usar `from app.core.jobs import job_store`. Llamar `job_store.create(sources)`, lanzar `asyncio.create_task(...)`, retornar 202. Dentro del task usar `job_store.mark_source_done()` y `job_store.complete()`.

**→ P3 (de P1):** C-09 GET endpoint **LISTO** en `/api/v1/jobs/{jobId}`.
- Responde `JobResponse` con `progress`, `completedSources`, `pendingSources`, `status`.
- D-05 puede hacer polling a este endpoint. Falta que C-05 (P2) cree los jobs.

**→ P5 (de P3):** el copy final peruano del bot está como placeholder en `docs/copy-placeholders-p5.md`.

**→ P2 (de P3):** D-04 espera **C-05** (`POST /verifications`). C-09 ya existe.

**Bot vivo:** `@autodata_peru_bot`. Levantar con polling (ver "Cómo correr el bot" abajo).

---

## Regla de dueño por carpeta

| Persona | Carpetas |
|---------|----------|
| P1 | `app/integrations/`, `app/core/`, `app/config.py`, `fixtures/`, `app/schemas/` |
| P2 | `app/services/`, `app/api/vehicles.py`, `app/api/verifications.py` |
| P3 | `app/bot/` |
| P4 | `app/repositories/`, `app/api/sellers.py`, `app/api/health.py`, migraciones |
| P5 | `app/web/`, `docs/`, textos y copy |

---

## Sprint 2 — "El producto decide" (EN CURSO)

> Puerta 1 cerró en verde. Sprint 2 arrancó.

**Avance:** P1 entregó B-14 (orquestador), C-09 (jobs GET), C-10 (error handler). P3 entregó D-02/D-06/D-07 (bot states, formatter, keyboards). **Bloqueante principal: C-05 (P2)** — desbloquea D-04, D-05, E-01 y completa C-09.

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

1. **Modo mock por default** — `CROMA_MODE=mock` en `.env`. Nadie gasta cuota sin autorizacion de P1.
2. **Schemas congelados** — `app/schemas/` solo los toca P1. Son el contrato de `03-API-DESIGN.md`.
3. **CromaClient ya existe** — Usar `app/integrations/croma/client.py`.
4. **`SourceResult` es dataclass** — en `app/integrations/croma/models.py`.
5. **Fixtures por nombre** — patron: `fixtures/{source}_{lookup}.json` o `fixtures/{source}_sample.json`.
6. **FastAPI + httpx + python-telegram-bot v21** — stack definido.
