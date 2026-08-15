# AutoData — Estado del Proyecto

> **Agentes de IA: lean este archivo ANTES de tocar código.**
> Es la fuente de verdad sobre qué existe, qué falta y qué reglas respetar.

**Proyecto:** AutoData — Verificación vehicular + vendedor para Perú via Croma
**Hackathon:** GOV-TECH Croma · Entrega: **16 ago 2026, 6:30 p.m.**
**Rama activa:** `testing`
**Sprint actual:** Sprint 3 — "Listo para usarse" → 🟢 **INICIADO** (Sprint 2 dado por concluido por decisión del equipo, chat 20:37 14/8: Joaquin "pasen al 3", confirmado por Carlos/Brayan — Puerta 2 formal no se documentó con checklist propio, pero suite en 147/147 verde)
**Última actualización:** 2026-08-14 (P3 cerró D-02/D-04/D-05/D-06/D-07 + fix de integración; suite 147/147 — equipo avanza a Sprint 3)

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

---

## Sprint 2 — Estado de tareas

### Completado por P3 (rama `jose-p3-sprint2`, commit `9e7eae9` — pendiente push + merge a `testing`)

| ID | Tarea | Archivos |
|----|-------|----------|
| D-02 | Máquina de estados persistida en `conversations` (sobrevive a reinicio) | `app/bot/states.py`, `app/repositories/conversation_repo.py`, `app/bot/handlers.py` |
| D-04 | Bot llama a `POST /verifications` por HTTP; 502/timeout → mensaje amable, no crash | `app/bot/api_client.py`, `app/bot/handlers.py`, `app/config.py` (nuevo `api_base_url`) |
| D-05 | Mensajes progresivos por fuente (polling de `/jobs/{id}`), con fallback síncrono a D-04 | `app/bot/job_client.py`, `app/bot/handlers.py` |
| D-06 | Veredicto formateado (semáforo, 1 columna) cableado al flujo real | `app/bot/formatters.py` |
| D-07 | 4 botones inline bajo el veredicto | `app/bot/keyboards.py`, `on_callback` en `handlers.py` |
| C-09 (enqueue) | Modo async en `POST /verifications` (`Prefer: respond-async` → 202 + jobId + pollUrl) que alimenta el `job_store` fuente por fuente | `app/api/verifications.py`, `app/services/verification_runner.py` |

Tests nuevos: `tests/test_bot_verification_flow.py`, `tests/test_bot_progress.py`, `tests/test_verification_async.py`. **Suite completa: 147/147 verde.**

### Fix de integración del Sprint 2 (coordinado — tocó carpetas de P1/P2/P4)

Un merge había regresado `app/main.py` (solo 4 routers, sin exception handlers) → **15 tests en rojo**. Reparado:
- **C-10** — `app/main.py` reconstruido: registra los routers de **sellers** y **web** + 4 exception handlers con el envelope `{"error":{...}}` (`03-API-DESIGN.md §L16`). El handler desenvuelve detalles dict, así `sellers.py` NO se tocó.
- **C-08** — nueva ruta `GET /verifications/{id}` en `app/api/verifications.py`.
- Asserts alineados al envelope: `tests/test_sellers_api.py` (×2), `tests/test_verification_persistence.py` (×1).
- **P1/P2/P4: revisen estos cambios en sus carpetas al mergear** — fueron necesarios para cerrar la integración.

---

## Sprint 3 — "Listo para usarse" (EN CURSO)

> Arrancado por decisión del equipo (chat 20:37, 14/8). Feature freeze a T-4h: desde ahí solo bugfixes.

| | Área del sprint | Tareas | Incremento demostrable |
|---|---|---|---|
| **P1** | Datos de demo y cuota | **E-03** (sembrado en live — momento de mayor riesgo, solo P1 ejecuta), E-07 | 5 escenarios congelados + repo público limpio |
| **P2** | Casos borde y robustez | D-10 (con P3), bugfixes | Los 7 casos borde de la spec §6 controlados |
| **P3** | UX de error y pulido | D-08, D-09, mensajes de error | Ningún camino termina en un mensaje feo |
| **P4** | Deploy y observabilidad | E-04, logs, health | URL pública estable + logs legibles |
| **P5** | Pitch | **E-05** (guion cronometrado, ensayo ×2), **E-08** (slide de límites y roadmap) | Guion cronometrado en 3:00 |

### Estado de P5 en Sprint 3

| ID | Tarea | Estado | Nota |
|----|-------|--------|------|
| E-05 | Guion de demo de 3 min, cronometrado | 🟡 Contenido completo en `files/09-DEMO-PITCH.md` (guion con tiempos, Q&A del jurado, checklist, plan B) | Falta el **ensayo ×2 cronometrado con el equipo** — no es trabajo de archivo |
| E-08 | Slide "límites conocidos y roadmap" (SUNARP, MTC) | 🔴 El contenido existe dentro del guion (min 2:15–2:45) pero no como pieza visual separada | Falta crear el slide |
| — | Copy del `negotiationScript` | 🟡 Funciona (P2 lo implementó en `app/services/appraisal.py` con texto propio, sin usar `NEGOTIATION_SCRIPT` de `app/core/prompts.py`) | Opcional: P5 puede pulir el texto con P2. No bloqueante |

### Después de Sprint 3 (Puerta 3 + Entrega) — tareas de P5

- **Puerta 3:** verificar que las 4 placas cacheadas responden en < 3 s; facilitar el simulacro de Q&A del jurado.
- **E-06** grabar video de respaldo (con P3) · **E-09** enviar el formulario de entrega (antes de las 6:00 p.m., no 6:29).

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

**→ P1 / P3 / P4 / P5 (de P2):** Orquestación y reglas de negocio cerradas (**C-04, C-05, C-06**).
- **Acción para P3:** Ya puedes implementar **D-04** y **D-09** consumiendo los endpoints `POST /api/v1/verifications` y `POST /verifications/{id}/appraisals`.
- **Acción para P5:** El schema de tasación ya retorna el `negotiationScript` (C-07).
- **Acción para P4:** Cuando tengas **C-03** listo, reemplaza el mock en `app/services/sellers.py`.
- **Acción para P1:** Cuando tengas **C-01** listo, reemplaza el mock en `app/services/vehicles.py`.


**→ Todos (de P3):** Bloque de P3 del Sprint 2 cerrado (commit `9e7eae9`; falta push + merge a `testing`).
- **Supabase / DB (IMPORTANTE):** el `DATABASE_URL` con host directo `db.<ref>.supabase.co` **ya NO resuelve**
  (Supabase lo deprecó). Usar el **session pooler**:
  `postgresql://postgres.<ref>:<pass con @ como %40>@aws-0-sa-east-1.pooler.supabase.com:5432/postgres`
  (región del proyecto = **sa-east-1**; el usuario debe llevar el ref; las 5 tablas ya existen). El proyecto está ACTIVO.
- **Red:** Telegram queda **bloqueado en la red de la universidad** (DNS ok, TCP a api.telegram.org cae); correr el
  bot con internet propio / hotspot.
- **Antes del Sprint 3:** falta pasar la **Puerta 2** (testing end-to-end, `06-PLAN-ACCION.md` §Puerta 2).

**Bot vivo:** `@autodata_peru_bot`. Levantar con polling (ver "Cómo correr el bot" abajo).

---

## Cómo correr el bot (P3)

Desde la raíz del repo, en PowerShell, en **dos ventanas** (el bot le pide el veredicto a la API):

```powershell
# Ventana 1 — API
.\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
# Ventana 2 — bot
.\.venv\Scripts\python.exe -m app.bot.main
```

Requiere `TELEGRAM_BOT_TOKEN` y el `DATABASE_URL` del **pooler** en `.env` (ver handoff de P3 arriba).
Corre en modo polling; se detiene con `Ctrl+C`. En modo mock una placa escribible siempre da 🟢 GO.

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
