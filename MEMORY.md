# AutoData — Estado del Proyecto

> **Agentes de IA: lean este archivo ANTES de tocar código.**
> Es la fuente de verdad sobre qué existe, qué falta y qué reglas respetar.

**Proyecto:** AutoData — Verificación vehicular + vendedor para Perú via Croma
**Hackathon:** GOV-TECH Croma · Entrega: **16 ago 2026, 6:30 p.m.**
**Rama activa:** `testing`
**Sprint actual:** Sprint 3 — "Listo para usarse"
**Última actualización:** 2026-08-15 (Croma **live** + IA de fraseo Gemini + `/ayuda` ampliado + fix seller/tasación)

---

## 🆕 Cambios 2026-08-15 — Croma en vivo + IA + /ayuda (rama `testing`)

**Por qué:** la competencia exige consumir la herramienta **Croma real**, no el demo. Además
se pidió lenguaje más natural (IA gratuita) y un `/ayuda` más completo.

1. **El bot ahora consume Croma REAL.** `CROMA_MODE=live` en `.env` (los **tests siguen en
   `mock`**: `tests/conftest.py` fuerza mock y apaga la IA, Art. III). Verificado en vivo:
   SBS, SUTRAN, SAT Lima y el vendedor (SUNAT+SAT) responden con datos reales de
   `https://api.croma.run`. Los endpoints reales están en `https://api.croma.run/catalog`.
   - Todas las rutas usan sufijo `/v1`. Ojo con dos detalles que se corrigieron:
     - **SAT Lima cuenta** (deuda por placa) NO recibe `{plate}`; recibe
       `{"document_type":"placa","document_number":<placa>}` (ver `_source_body` en
       `app/services/vehicles.py`).
     - **Vendedor**: SUNAT por DNI = `POST /pe/sunat/document/v1` (`document_type`/`document_number`);
       por RUC = `POST /pe/sunat/ruc/v1` (`{"ruc":...}`); deuda = `POST /pe/sat-lima/account-status/v1`.
       Antes apuntaban a rutas inventadas (`/api/v1/croma/...`). Arreglado en `app/services/seller.py`.
   - **Cuota real: 500 requests/24h POR endpoint** (no 100 totales). Igual hay caché en
     `fixtures/demo/` para la demo rápida.
   - ⚠️ **Latencia de Croma alta** (20–40s por fuente en pruebas); algunas dan timeout y el
     veredicto queda tope `CAUTION`. Para el demo veloz usar las 4 placas sembradas
     (`fixtures/demo/`, `CROMA_MODE=mock`) y **una sola** placa en vivo ante el jurado.
   - Nota: el fan-out de 6 fuentes va con `CromaClient()` **sin sesión** (un `AsyncSession`
     no es seguro en `asyncio.gather` → daba errores de caché). Por eso el path live no
     escribe caché ni `quota_log`; se prioriza correctitud sobre la optimización.

2. **D-08 arreglado (vendedor real).** Antes `create_verification` usaba un **mock duro**
   (`app/services/sellers.py`, importaba de `tests/`) → nunca tocaba Croma. Ese archivo se
   **eliminó**. Ahora el flujo completo usa `perform_seller_screening` (SUNAT + SAT reales).

3. **D-09 arreglado (tasación real).** Antes la tasación estaba clavada a la placa demo
   `D0H-741`. Se agregó `plate` a `AppraisalRequest`; el bot manda `ctx["plate"]` y el
   endpoint tasa la placa real (o la recupera de la verificación guardada, C-08).

4. **IA de fraseo (Gemini, gratis, bajo consumo) — solo naturaliza texto.** El veredicto y
   el precio SIEMPRE se calculan con las reglas deterministas; la IA nunca los decide.
   - Nuevo `app/integrations/llm/gemini.py` (httpx, modelo `gemini-flash-lite-latest`).
     **Falla abierto**: sin key o ante cualquier error devuelve `None` y el bot usa su
     texto de siempre. Verificado en vivo con la key del equipo ✅.
   - ⚠️ **Modelo:** usar `gemini-flash-lite-latest` (lite = menor consumo y "latest" no se
     deprecia). `gemini-2.0-flash` y `gemini-2.5-flash-lite` YA devuelven 404.
   - Se usa en 3 puntos (handlers.py): resumen del veredicto, guion de negociación, y
     respuesta amable cuando no se entiende el mensaje. Prompts en `app/core/prompts.py`.
   - **Config nueva en `.env`:** `GEMINI_API_KEY=` (key gratuita de aistudio.google.com — ya
     puesta), `GEMINI_MODEL=gemini-flash-lite-latest`, `LLM_ENABLED=true`.

5. **`/ayuda` ampliado** (`_AYUDA_TEXT` en `handlers.py`): las 6 fuentes y qué detecta cada
   una, ejemplos copiables, cómo leer el semáforo 🟢🟡🔴 + precio/guion, y límites honestos.

6. **C-09 async restaurado.** El merge a `testing` había regresado `create_verification` a una
   versión síncrona que rompía 2 tests async. Se restauró el modo `Prefer: respond-async`
   (202 + job) delegando en `build_verification`. **Suite: 162 verde.**

7. **Asistente de compra (UX honesta).** El chatbot ya no solo consulta; entrega un reporte
   estructurado. Decisiones del usuario: (a) marca/modelo/año/km/precio de mercado se marcan
   **NO_DISPONIBLE** (Croma Perú no los da; requieren SUNARP/MTC), nunca se inventan; (b) el
   precio objetivo = **precio pedido − deducciones VERIFICADAS** (el cliente trae el precio);
   (c) la IA **no** toca el veredicto (100% determinista).
   - `app/bot/formatters.py` reescrito: secciones INFORMACIÓN VERIFICADA / PENDIENTE /
     NO_DISPONIBLE / ANÁLISIS DEL PRECIO / RIESGOS / RECOMENDACIÓN / CONFIANZA. Recomendación:
     🟢 COMPRAR · 🟡 NEGOCIAR · 🔴 NO COMPRAR · ⚪ INFORMACIÓN INSUFICIENTE (obligatoria si una
     fuente crítica —orden de captura— no respondió). Confianza 🟢/🟡/🔴 según fuentes verificadas.
     Nunca dice "verificado/limpio" si una fuente falló. `purchase_recommendation()` /
     `confidence_level()` son deterministas (basadas en `verdict` + `confidence`).
   - `app/bot/parsers.py`: acepta `COH 099` (espacio), `29k`, `S/29.000`; `format_plate_display`
     muestra la placa con guion. Ya no re-pregunta una placa válida.
   - La tasación se calcula dentro de `build_verification` cuando viene el precio (un solo paso).
   - **Persistencia verificada:** el estado de conversación (placa, precio, contexto) se guarda en
     la tabla `conversations` de **Supabase** y sobrevive a un reinicio del proceso (probado en vivo).
   - **Botón "Ver detalle" (`CB_DETAIL`) implementado:** antes era un stub que devolvía el UUID.
     Ahora `on_text` guarda la verificación en `ctx["last_verification"]` y el botón la renderiza
     con `format_detail()` (papeletas ítem por ítem, póliza SOAT, deuda desglosada, estado de cada
     fuente con latencia, id de consulta). Test: `test_format_detail_shows_items_and_sources`.
   - **Bugfix (importante):** si el chat quedaba en estado `DONE` de una consulta previa, al saludar
     ("Hola") el bot **re-disparaba la verificación en vano** (mostraba el error de fuente caída). El
     fallback de `next_state` ahora nunca devuelve un estado terminal (vuelve a `IDLE`), y `on_text`
     solo verifica si el contexto tiene placa. Test: `test_greeting_while_done_does_not_reverify`.

**Pendiente menor (no bloqueante):** la respuesta "placa sin registros" ya no devuelve 404
amable a nivel API (el bot igual valida la placa antes de llamar). Revisar D-10 caso 1 si se
quiere el mensaje dedicado.

---

## Sprint 3 — Estado de tareas

### Completado por P4 (Data / Infra / Deploy / Observabilidad)

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

| E-03 | Sembrar 5 placas en live y congelar fixtures | P1 | `fixtures/demo/` (24 archivos), `docs/quota-log.md`, `app/integrations/croma/client.py` |
| E-07 | README publico del repo | P1 | `README.md` reescrito para terceros |
| E-04 | Deploy + observabilidad (Docker, Railway/Render, telemetría) | P4 | `Dockerfile`, `docker-compose.yml`, `Procfile`, `railway.json`, `render.yaml`, `app/core/logging.py` |
| E-08 | Slide "límites conocidos y roadmap" (SUNARP, MTC) | P5 | `app/web/templates/limites.html`, ruta `/limites` en `app/web/routes.py` |

### Pendiente

| ID | Tarea | Dueño | Notas |
|----|-------|-------|-------|
| D-08 | Flujo de vendedor con confirmación explícita | P3 | — |
| D-09 | Flujo de tasación con guion copiable | P3 | — |
| D-10 | Mensajes de error para los 7 casos borde | P3 + P2 | — |
| E-05 | Guion de demo cronometrado | P5 | Contenido listo en `files/09-DEMO-PITCH.md`. Falta el **ensayo ×2 con cronómetro** (no es trabajo de archivo) |
| E-06 | Grabar video de respaldo | P5 + P3 | Depende de E-03 ✅ y D-09 |
| E-09 | Enviar el formulario de entrega | P5 | Antes de las 6:00 p.m., no 6:29 |

> **Nota:** A-07 (prompts base) y E-02 (landing) figuraban como pendientes de P5 en una versión
> anterior de este archivo. Ambos están **completados y mergeados** desde Sprint 1 —
> ver `app/core/prompts.py` y `app/web/templates/landing.html`. Igual E-01 (`report.html`).

### ⚠️ ALERTA — `app/main.py` quedó roto en el merge de `testing` (665c9c3)

El merge de Sprint 3 dejó `app/main.py` sin 3 imports (`logging`, `RequestValidationError`,
`StarletteHTTPException`). Efecto: **la app no importaba** y **9 módulos de test no colectaban**
(la suite entera no corría, no era "151/151 verde").

- **P5 agregó solo los 3 imports** (cambio mínimo para desbloquear; sin tocar lógica de nadie).
- **Queda pendiente para P1/P2/P4** — no es de P5 y no se tocó:
  1. `app/main.py` tiene **handlers duplicados**: `HTTPException`/`Exception` registrados dos veces
     (versión de P1 en líneas ~25-48 y versión con envelope en ~81-108). Gana el último registrado,
     pero conviene borrar el duplicado.
  2. `ObservabilityMiddleware` **se importa pero nunca se registra** (`app.add_middleware` no existe)
     → la observabilidad de P4 no está activa. Esto rompe `tests/test_observability.py`.
  3. **13 tests en rojo** tras desbloquear la colección: `test_error_handler`, `test_jobs`,
     `test_observability`, `test_sellers_api`, `test_verification_async`, `test_verifications`.
     Todos en carpetas de P1/P2/P3/P4. Los 144 restantes pasan.

### Observaciones del review

- **P4 modificó `app/api/health.py`** — ahora incluye check de DB (`SELECT 1`). Mejora aceptable.
- **P4 `pytest.ini` usa `asyncio_mode = auto`** — la rama P1 usa `strict`. Unificar al mergear.
- **P4 `QuotaLogModel.id` usa `Integer`** en ORM pero DDL dice `BIGSERIAL`. Menor para hackathon.
- **P3 parser de moto** — el caso `1234-AB a 32 mil` (placa moto + precio) no está testeado. Bajo riesgo.

---

## Sprint 2 — Estado de tareas

### Completado

| ID | Tarea | Dueño | Archivos |
|----|-------|-------|----------|
| B-12 | Adapter **SUNAT** por documento → `taxpayer` + detector `isVehicleTrader` | P4 | `app/integrations/croma/sources/sunat.py`, `fixtures/sunat_sample.json`, `fixtures/sunat_20100100101.json` |
| B-13 | Adapter **SAT Lima por DNI/RUC** → `personalDebt` + placas relacionadas | P4 | `app/integrations/croma/sources/sat_seller.py`, `fixtures/sat_seller_sample.json`, `fixtures/sat_seller_clean.json` |
| C-03 | `POST /api/v1/sellers/screenings` + validación de `consent` (Art. VI) + enmascarado | P4 | `app/services/seller.py`, `app/api/sellers.py`, `app/main.py` |
| C-08 | `GET /api/v1/verifications/{id}` desde Supabase/DB + hashing ético de documento | P4 | `app/repositories/verification_repo.py`, `app/api/verifications.py`, `app/main.py` |
| D-02 | Máquina de estados (`IDLE→AWAITING_*→DONE`) persistida en `conversations` | P3 | `app/bot/states.py`, `app/repositories/conversation_repo.py`, `app/bot/handlers.py` |
| D-04 | Bot llama a `POST /verifications` por HTTP con manejo de errores (502 amable) | P3 | `app/bot/api_client.py`, `app/bot/handlers.py` |
| D-05 | Mensajes progresivos por fuente (polling `/jobs/{id}`) | P3 | `app/bot/job_client.py`, `app/bot/handlers.py` |
| D-06 | Formateo del veredicto con semáforo (🟢🟡🔴) | P3 | `app/bot/formatters.py` |
| D-07 | 4 botones inline bajo el veredicto | P3 | `app/bot/keyboards.py`, `handlers.py` |
| C-04 | `scoring_service`: flags, riskScore y verdict | P2 | `app/services/scoring.py` |
| C-05 | `POST /api/v1/verifications` orquestando datos | P2 | `app/api/verifications.py` |
| C-06 | `appraisal_service` + `POST /verifications/{id}/appraisals` | P2 | `app/services/appraisal.py` |
| E-01 | Página web de reporte `/r/{id}` | P5 | `app/web/templates/report.html`, `app/web/routes.py` |

---

## Sprint 1 — Estado de tareas

### Completado

| ID | Tarea | Dueño | Archivos |
|----|-------|-------|----------|
| A-01 | Estructura de carpetas, FastAPI, `/api/v1/health` → 200 | P1 | `app/main.py`, `app/api/health.py` |
| A-02 | Schemas Pydantic (7 recursos completos) | P1 | `app/schemas/` |
| A-05 | `.env.example` con todas las variables | P1 | `.env.example` |
| B-01 | `CromaClient` con httpx async, auth, timeout 40s | P1 | `app/integrations/croma/client.py` |
| B-02 | Modo mock: lee `fixtures/*.json` cuando `CROMA_MODE=mock` | P1 | `_mock_call()` en client.py |
| A-06 | 1 fixture real de Croma (3 fuentes) | P1 | `fixtures/sutran_sample.json`, `apeseg_soat_sample.json`, `sbs_soat_sample.json` |
| B-05 | Backoff en 429 con `Retry-After`, máx 2 reintentos | P1 | Tests en `tests/test_croma_client.py` |
| A-03 | Proyecto Supabase + DDL de las 5 tablas | P4 | `migrations/schema.sql`, `app/core/database.py`, `app/repositories/models.py` |
| A-04 | Bot @autodata_peru_bot creado | P3 | Token en `.env` local |
| D-01 | Esqueleto del bot: polling + `/start` + `/ayuda` | P3 | `app/bot/main.py`, `app/bot/handlers.py` |
| D-03 | Parser de texto libre: placa, precio, DNI | P3 | `app/bot/parsers.py` |
| B-03 | Cache read-through contra `croma_cache` con TTL | P4 | `app/repositories/cache_repo.py` |
| B-04 | Logging de cuota en tabla `quota_log` | P4 | `app/repositories/quota_repo.py` |
| C-11 | `GET /api/v1/quota` con datos reales | P4 | `app/api/quota.py` |

---

## Verificación de cierre (Sprint 3 — P4) — 2026-08-14

- ✅ **Suite completa: 151/151 tests en verde** (`pytest`).
- ✅ Archivos de despliegue listos (`Dockerfile`, `docker-compose.yml`, `Procfile`, `railway.json`, `render.yaml`).
- ✅ Telemetría y observabilidad activas en todos los endpoints HTTP.
- ✅ `/api/v1/health` con payload enriquecido (uptime, versión, environment, database status).

---

## Regla de dueño por carpeta

| Persona | Carpetas |
|---------|----------|
| P1 | `app/integrations/`, `app/core/`, `app/config.py`, `fixtures/`, `app/schemas/` |
| P2 | `app/services/`, `app/api/vehicles.py`, `app/api/verifications.py` |
| P3 | `app/bot/` |
| P4 | `app/repositories/`, `app/api/sellers.py`, `app/api/health.py`, migraciones, infra/deploy |
| P5 | `app/web/`, `docs/`, textos y copy |
