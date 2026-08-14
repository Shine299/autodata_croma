# AutoData — Estado del Proyecto

> **Agentes de IA: lean este archivo ANTES de tocar código.**
> Es la fuente de verdad sobre qué existe, qué falta y qué reglas respetar.

**Proyecto:** AutoData — Verificación vehicular + vendedor para Perú via Croma
**Hackathon:** GOV-TECH Croma · Entrega: **16 ago 2026, 6:30 p.m.**
**Rama activa:** `sprint2-arroz`
**Sprint actual:** Sprint 2 — "El producto decide" (P4 Completado)
**Última actualización:** 2026-08-14 (Sprint 2 P4 completado y verificado — 83/83 tests verdes)

---

## Sprint 2 — Tareas de Persona 4 (Data / Infra / Repositories)

### Completado por P4

| ID | Tarea | Dueño | Archivos |
|----|-------|-------|----------|
| B-12 | Adapter **SUNAT** por documento → `taxpayer` + detector `isVehicleTrader` | P4 | `app/integrations/croma/sources/sunat.py`, `fixtures/sunat_sample.json`, `fixtures/sunat_20100100101.json` |
| B-13 | Adapter **SAT Lima por DNI/RUC** → `personalDebt` + placas relacionadas | P4 | `app/integrations/croma/sources/sat_seller.py`, `fixtures/sat_seller_sample.json`, `fixtures/sat_seller_clean.json` |
| C-03 | `POST /api/v1/sellers/screenings` + validación de `consent` (Art. VI) + enmascarado | P4 | `app/services/seller.py`, `app/api/sellers.py`, `app/main.py` |
| C-08 | `GET /api/v1/verifications/{id}` desde Supabase/DB + hashing ético de documento | P4 | `app/repositories/verification_repo.py`, `app/api/verifications.py`, `app/main.py` |
| — | Modelos completos ORM (5 tablas: croma_cache, quota_log, verifications, appraisals, conversations) | P4 | `app/repositories/models.py` |
| — | Repositorio de estados de conversación para bot Telegram (D-02 readiness) | P4 | `app/repositories/conversation_repo.py` |
| — | Suite completa de tests automatizados de Sprint 2 P4 | P4 | `tests/test_adapters_sunat.py`, `tests/test_adapters_sat_seller.py`, `tests/test_sellers_api.py`, `tests/test_verification_persistence.py` |

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

---

## Verificación de cierre (Sprint 2 — P4) — 2026-08-14

- ✅ **Suite completa: 83/83 tests en verde** en modo mock.
- ✅ Endpoints `/api/v1/sellers/screenings` y `/api/v1/verifications/{id}` funcionales y testeados.
- ✅ Cumplimiento ético de privacidad (Art. VI): hash SHA-256 para documentos y enmascarado de salida (`*****789`).
- ✅ Detección de bandera estrella `SELLER_IS_DEALER` y `SELLER_HAS_DEBT`.

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

## Decisiones tecnicas ya tomadas

1. **Modo mock por default** — `CROMA_MODE=mock` en `.env`. Nadie gasta cuota sin autorizacion de P1.
2. **Schemas congelados** — `app/schemas/` solo los toca P1. Son el contrato de `03-API-DESIGN.md`.
3. **CromaClient ya existe** — Usar `app/integrations/croma/client.py`.
4. **`SourceResult` es dataclass** — en `app/integrations/croma/models.py`.
5. **Fixtures por nombre** — patron: `fixtures/{source}_{lookup}.json` o `fixtures/{source}_sample.json`.
6. **FastAPI + httpx + python-telegram-bot v21** — stack definido.
