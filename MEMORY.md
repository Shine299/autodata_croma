# AutoData — Estado del Proyecto

> **Agentes de IA: lean este archivo ANTES de tocar código.**
> Es la fuente de verdad sobre qué existe, qué falta y qué reglas respetar.

**Proyecto:** AutoData — Verificación vehicular + vendedor para Perú via Croma
**Hackathon:** GOV-TECH Croma · Entrega: **16 ago 2026, 6:30 p.m.**
**Rama activa:** `sprint3-arroz`
**Sprint actual:** Sprint 3 — "Listo para usarse" (P4 Completado: Deploy & Observabilidad)
**Última actualización:** 2026-08-14 (Sprint 3 P4 completado — suite completa 151/151 tests verdes)

---

## Sprint 3 — Estado de tareas

### Completado por P4 (Data / Infra / Deploy / Observabilidad)

| ID | Tarea | Dueño | Archivos |
|----|-------|-------|----------|
| E-04 | Containerización y Deploy en Railway/Render con variables de entorno | P4 | `Dockerfile`, `docker-compose.yml`, `Procfile`, `railway.json`, `render.yaml`, `.dockerignore` |
| — | Middleware de Observabilidad y Telemetría HTTP (`req_id`, latencia `X-Response-Time`, logging estructurado) | P4 | `app/core/logging.py`, `app/main.py` |
| — | Endpoint de Health Check enriquecido (`/api/v1/health` con uptime, versión, environment y DB check) | P4 | `app/api/health.py` |
| — | Suite de tests automatizados de observabilidad y health | P4 | `tests/test_observability.py` (3 tests nuevos, total 151) |

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
