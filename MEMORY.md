# AutoData — Estado del Proyecto

> **Agentes de IA: lean este archivo ANTES de tocar código.**
> Es la fuente de verdad sobre qué existe, qué falta y qué reglas respetar.

**Proyecto:** AutoData — Verificación vehicular + vendedor para Perú via Croma
**Hackathon:** GOV-TECH Croma · Entrega: **16 ago 2026, 6:30 p.m.**
**Rama activa:** `testing`
**Sprint actual:** Sprint 3 — "Listo para usarse"
**Última actualización:** 2026-08-14 (P1 cerró E-03/E-07; P4 cerró E-04 + observabilidad; P5 cerró E-08)

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

## 🔴 EL BOT NO RESPONDE — diagnóstico y qué falta (2026-08-15)

Síntoma: el botón de la landing abre Telegram pero el bot no contesta.

**Descartado — no es la landing.** Los 3 botones apuntan a `https://t.me/autodata_peru_bot`,
reciben el click (verificado con `elementFromPoint`, nada los tapa) y la URL responde
**HTTP 200** con el título real "AutoData Perú". El bot existe.

**Causa real: el proceso del bot no está corriendo.** Es polling — necesita un proceso vivo
que pregunte a Telegram por mensajes. Sin `TELEGRAM_BOT_TOKEN` crashea al arrancar
(`telegram.error.InvalidToken`).

### Arreglado por P5 (deploy — se tocó área de P4, coordinar)

| Archivo | Bug | Arreglo |
|---|---|---|
| `Dockerfile` | `HEALTHCHECK` usaba `os.environ` **sin importar `os`** → `NameError`, el healthcheck fallaba siempre | Agregado `import os` |
| `Dockerfile` | `CMD` sólo levantaba uvicorn. Railway construye desde el Dockerfile, así que el `Procfile` se ignora y **el bot nunca arrancaba en producción** | `CMD` con switch: `PROCESS=bot` → bot; sin la variable → uvicorn |
| `docker-compose.yml` | El servicio `bot` no recibía `TELEGRAM_BOT_TOKEN` → habría crasheado igual | Token pasado desde el `.env` local |

### Falta (no lo puede hacer P5)

1. **P3 (José)** tiene el token — es el único. O corre el bot local, o lo carga como variable
   de entorno en Railway.
2. **P4 (Brayan)** debe crear en Railway un **segundo servicio** desde la misma imagen con
   `PROCESS=bot`. Con un solo servicio sigue levantando sólo la API.
3. Para que el bot dé veredictos, la API debe estar viva y accesible en `API_BASE_URL`.

---

## Regla de dueño por carpeta

| Persona | Carpetas |
|---------|----------|
| P1 | `app/integrations/`, `app/core/`, `app/config.py`, `fixtures/`, `app/schemas/` |
| P2 | `app/services/`, `app/api/vehicles.py`, `app/api/verifications.py` |
| P3 | `app/bot/` |
| P4 | `app/repositories/`, `app/api/sellers.py`, `app/api/health.py`, migraciones, infra/deploy |
| P5 | `app/web/`, `docs/`, textos y copy |
