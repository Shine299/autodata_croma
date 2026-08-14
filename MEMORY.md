# AutoData — Estado del Proyecto

> **Agentes de IA: lean este archivo ANTES de tocar código.**
> Es la fuente de verdad sobre qué existe, qué falta y qué reglas respetar.

**Proyecto:** AutoData — Verificación vehicular + vendedor para Perú via Croma
**Hackathon:** GOV-TECH Croma · Entrega: **16 ago 2026, 6:30 p.m.**
**Rama activa:** `testing`
**Sprint actual:** Sprint 2 — "El producto decide" → 🟨 **EN CURSO** (P1, P3, P4 y P5 completados; P2 acaba de entregar C-04/C-05/C-06 en `carlos_p2_sprint2`, sin mergear todavía)
**Última actualización:** 2026-08-14 (P1 B-14/C-09/C-10, P3 D-02/D-06/D-07, P4 B-12/B-13/C-03/C-08 y P5 copy+E-01 [PR #15, sin mergear] en `testing` o listos para mergear — P2 C-04/C-05/C-06 recién subido en su rama, pendiente de merge)

---

## Sprint 2 — Estado de tareas

### Completado por P1 (Infra / Orquestación)

| ID | Tarea | Dueño | Archivos |
|----|-------|-------|----------|
| C-10 | Handler global de errores con envelope estándar | P1 | `app/main.py` (4 exception handlers), `tests/test_error_handler.py` (5 tests) |
| B-14 | Ejecución concurrente de 6 fuentes con `asyncio.gather` | P1 | `app/integrations/croma/orchestrator.py` (`fetch_all_sources`, `OrchestratorResult`), `tests/test_orchestrator.py` (4 tests) |
| C-09 | `GET /api/v1/jobs/{jobId}` + job store (shell — falta wiring `Prefer: respond-async` cuando C-05 esté mergeado) | P1 | `app/core/jobs.py` (`JobStore`, `JobState`), `app/api/jobs.py`, `tests/test_jobs.py` (5 tests) |

### Entregado por P2, pendiente de merge a `testing`

| ID | Tarea | Dueño | Archivos |
|----|-------|-------|----------|
| C-04 | Scoring + veredicto (GO/CAUTION/STOP) | P2 | `app/services/scoring.py`, `tests/test_scoring.py` |
| C-05 | `POST /verifications` (orquesta vehicle + seller + scoring) | P2 | `app/api/verifications.py`, `tests/test_verifications.py` |
| C-06 | Tasación: calcular precio justo | P2 | `app/services/appraisal.py`, `tests/test_appraisal.py` |

Rama `carlos_p2_sprint2`, commit `73f301e`. Desbloquea D-04, D-05 (wiring completo con C-09) y **C-07 (P5)**
en cuanto se mergee a `testing`.

### Completado por P3 (Bot Telegram)

| ID | Tarea | Dueño | Archivos |
|----|-------|-------|----------|
| D-02 | Máquina de estados (`IDLE→AWAITING_*→DONE`) persistida en `conversations` | P3 | `app/bot/states.py`, `app/repositories/models.py` (`ConversationModel`), `app/repositories/conversation_repo.py`, `on_text`+`next_state` en `app/bot/handlers.py`, `MessageHandler` en `app/bot/main.py`, `tests/test_conversation_repo.py` (7 tests, incluye supervivencia a reinicio con sqlite en archivo) |
| D-06 | Formateo del veredicto con semáforo (🟢🟡🔴) | P3 | `app/bot/formatters.py` (`format_verdict`), `tests/fixtures/verification_{go,caution,stop}.json`, `tests/test_formatters.py` (9 tests). Una columna, sin tablas → sin scroll horizontal en celular |
| D-07 | Botones inline (Ver detalle · Calcular precio · Verificar vendedor · Nueva consulta) | P3 | `app/bot/keyboards.py` (`verdict_keyboard`), `on_callback` router en `handlers.py`, `CallbackQueryHandler` en `main.py`, `tests/test_keyboards.py` (4 tests) |

### Completado por P4 (Data / Infra / Repositories)

| ID | Tarea | Dueño | Archivos |
|----|-------|-------|----------|
| B-12 | Adapter **SUNAT** por documento → `taxpayer` + detector `isVehicleTrader` | P4 | `app/integrations/croma/sources/sunat.py`, `fixtures/sunat_sample.json`, `fixtures/sunat_20100100101.json` |
| B-13 | Adapter **SAT Lima por DNI/RUC** → `personalDebt` + placas relacionadas | P4 | `app/integrations/croma/sources/sat_seller.py`, `fixtures/sat_seller_sample.json`, `fixtures/sat_seller_clean.json` |
| C-03 | `POST /api/v1/sellers/screenings` + validación de `consent` (Art. VI) + enmascarado | P4 | `app/services/seller.py`, `app/api/sellers.py`, `app/main.py` |
| C-08 | `GET /api/v1/verifications/{id}` desde Supabase/DB + hashing ético de documento | P4 | `app/repositories/verification_repo.py`, `app/api/verifications.py`, `app/main.py` |
| — | Modelos completos ORM (5 tablas: croma_cache, quota_log, verifications, appraisals, conversations) | P4 | `app/repositories/models.py` |
| — | Suite completa de tests automatizados de Sprint 2 P4 | P4 | `tests/test_adapters_sunat.py`, `tests/test_adapters_sat_seller.py`, `tests/test_sellers_api.py`, `tests/test_verification_persistence.py` |

### Completado por P5 (Producto)

| ID | Tarea | Dueño | Archivos |
|----|-------|-------|----------|
| — | Copy final peruano del bot (cierra el handoff de P3 en `docs/copy-placeholders-p5.md`) | P5 | `app/bot/handlers.py` (`_START_TEXT`, `_AYUDA_TEXT`, `_ASK_PLATE`, `_ASK_PRICE`, `_DONE`, `_CB_REPLIES`), `app/bot/formatters.py` (`_VERDICT_LABEL`). Fix aplicado: `_DONE` filtraba una nota de desarrollo interna (`D-04`) al usuario final |
| E-01 | Página pública `/r/{verificationId}` (semáforo + hallazgos + fuentes) | P5 | `app/web/routes.py`, `app/web/templates/report.html`, `tests/test_report_page.py` (5 tests, sembrados con `tests/fixtures/verification_{go,caution,stop}.json`). Vocabulario de veredicto (COMPRA/OJO/NO COMPRES) reutilizado de la landing de Sprint 1 |

Rama `chimbotano`, [PR #15](https://github.com/Shine299/autodata_croma/pull/15) → `testing`, sin mergear todavía.

### Bloqueado / pendiente de merge

| ID | Tarea | Dueño | Estado |
|----|-------|-------|--------|
| D-04 | Bot → `POST /verifications` + manejo de errores (502 amable) | P3 | C-05 ya existe en `carlos_p2_sprint2` — falta merge a `testing` |
| D-05 | Mensajes progresivos por fuente | P3 | C-09 (GET) listo ✅ — falta que C-05 (ya entregado por P2) se mergee para el wiring completo |
| C-07 | Guion de negociación (`negotiationScript`) | P5 | El prompt (`app/core/prompts.py::NEGOTIATION_SCRIPT`) ya está listo desde Sprint 1. `appraisal_service` (C-06) ya existe en `carlos_p2_sprint2` — falta que se mergee a `testing` para integrar contra la versión final |

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
| A-03 | Proyecto Supabase + DDL de las 5 tablas | P4 | `migrations/schema.sql`, `app/core/database.py`, `app/repositories/models.py` (verificadas OK) |
| A-04 | Bot @autodata_peru_bot creado, token en `.env`, responde desde el celular | P3 | Token en `.env` local (no versionado). Probado desde celular OK |
| D-01 | Esqueleto del bot: polling + `/start` + `/ayuda` (< 2 s) | P3 | `app/bot/main.py`, `app/bot/handlers.py`. Copy cerrado por P5 en Sprint 2 |
| D-03 | Parser de texto libre: placa, precio, DNI | P3 | `app/bot/parsers.py`, `tests/test_parsers.py` — 18 tests verdes (15 casos + 3). Retorna schema `Extracted` |
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

### Verificación de cierre (Puerta 1) — 2026-08-14

- ✅ Suite completa en verde en modo mock (sin gastar cuota).
- ✅ `app.main` importa; landing `/`, `/api/v1/health` y `/api/v1/quota` responden **200**.
- 🔧 **Entorno:** el `.venv` puede estar incompleto → correr `pip install -r requirements.txt`. Usar siempre `.\.venv\Scripts\python.exe`.
- 🔧 **Fix aplicado en `app/api/quota.py`:** degrada con gracia (try/except → 200 con `database: error: ...`) en vez de propagar stacktrace cuando la DB no responde.
- ⚠️ **DB:** el `.env` puede apuntar a una Supabase cuyo `DATABASE_URL` no resuelve DNS localmente; los tests usan el fallback SQLite en memoria de `app/core/database.py`. Validar la conexión real a Supabase con red antes de la demo.

---

## Avisos / handoffs entre roles

**→ P2 (de P1):** B-14 orquestador concurrente **LISTO**.
- Importar: `from app.integrations.croma.orchestrator import fetch_all_sources, OrchestratorResult`
- Firma: `await fetch_all_sources(client, plate) -> OrchestratorResult` — devuelve `insurance`, `infractions`, `tax_debt`, `capture_order`, `sources_summary`, `unverified_sources`.
- **Job store para C-05 async:** usar `from app.core.jobs import job_store`. Llamar `job_store.create(sources)`, lanzar `asyncio.create_task(...)`, retornar 202. Dentro del task usar `job_store.mark_source_done()` y `job_store.complete()`.

**→ P3 (de P1):** C-09 GET endpoint **LISTO** en `/api/v1/jobs/{jobId}`.
- Responde `JobResponse` con `progress`, `completedSources`, `pendingSources`, `status`.
- D-05 puede hacer polling a este endpoint. Falta que C-05 (P2, ya entregado en `carlos_p2_sprint2`) se mergee a `testing` para crear los jobs.

**→ P3 (de P5):** copy final peruano del bot cerrado (ver "Completado por P5" arriba). Claves y
`{placeholders}` de `docs/copy-placeholders-p5.md` respetados sin cambios. Ojo: `_DONE` cambió de
texto (ya no menciona `D-04`), por si algún test tuyo asertaba el string exacto.

**→ P2 (de P5):** **C-07 casi lista.** El prompt `NEGOTIATION_SCRIPT` ya está en `app/core/prompts.py`.
Ya viste que entregaste `appraisal.py` en `carlos_p2_sprint2` — en cuanto esté mergeado a `testing`,
P5 integra en menos de una hora.

**→ P2/P3 (de P4):** B-12/B-13 (adapters SUNAT + SAT Lima persona) y C-03 (`POST /sellers/screenings`)
ya no están pendientes — P4 los entregó completos. Ver tabla "Completado por P4" arriba.

**Bot vivo:** `@autodata_peru_bot`. Levantar con polling (ver "Cómo correr el bot" abajo).

---

## Cómo correr el bot (P3)

Desde la raíz del repo, en PowerShell:

```powershell
.\.venv\Scripts\python.exe -m app.bot.main
```

Requiere `TELEGRAM_BOT_TOKEN` en `.env` (A-04). Corre en modo polling; se detiene con `Ctrl+C`.

---

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

## Decisiones técnicas ya tomadas

1. **Modo mock por default** — `CROMA_MODE=mock` en `.env`. Nadie gasta cuota sin autorización de P1.
2. **Schemas congelados** — `app/schemas/` solo los toca P1. Son el contrato de `03-API-DESIGN.md`.
3. **CromaClient ya existe** — Usar `app/integrations/croma/client.py`, no crear otro cliente HTTP.
4. **`SourceResult` es dataclass** — en `app/integrations/croma/models.py`.
5. **Fixtures por nombre** — patrón: `fixtures/{source}_{lookup}.json` o `fixtures/{source}_sample.json`.
6. **FastAPI + httpx + python-telegram-bot v21** — stack definido, no agregar dependencias nuevas sin justificación.
7. **Cuota limitada** — 100 requests/día para todo el equipo.

---

## Reglas para agentes de IA

1. **Leer `files/00-CONTEXTO.md` a `files/04-PLAN-TECNICO.md`** antes de implementar.
2. **Respetar el contrato de API** de `files/03-API-DESIGN.md` — es ley.
3. **Nunca usar `CROMA_MODE=live`** sin autorización explícita de P1.
4. **Respetar dueño de carpeta** — ver tabla arriba.
5. **No agregar dependencias** sin justificación.
6. **Tests obligatorios** para lógica no trivial. Usar `pytest` + `pytest-asyncio`.
7. **No crear archivos `.md` de documentación** extra. Este archivo y `files/` son suficientes.
8. **Modo mock es el default** — todo desarrollo se hace sin tocar la red.

---

## Cómo actualizar este archivo

Cada vez que cierres una tarea:
1. Mueve la fila de "Pendiente/Bloqueado" a "Completado" (o a "Entregado, pendiente de merge" si tu rama aún no se mergeó a `testing`) con los archivos creados/modificados.
2. Actualiza la fecha de "Última actualización" y el resumen del encabezado.
3. Commitea el cambio junto con tu código.
