# AutoData — Estado del Proyecto

> **Agentes de IA: lean este archivo ANTES de tocar código.**
> Es la fuente de verdad sobre qué existe, qué falta y qué reglas respetar.

**Proyecto:** AutoData — Verificación vehicular + vendedor para Perú via Croma
**Hackathon:** GOV-TECH Croma · Entrega: **16 ago 2026, 6:30 p.m.**
**Rama activa:** `testing`
**Sprint actual:** Sprint 2 — "El producto decide" → 🟨 **EN CURSO** (P3 avanzó D-02/D-06/D-07)
**Última actualización:** 2026-08-14 (Sprint 2: bot D-02/D-06/D-07 hechos — suite 85/85 verdes)

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

## Sprint 2 — Estado de tareas (bot, P3)

### Completado (P3) — suite total 85/85 verdes

| ID | Tarea | Dueño | Archivos |
|----|-------|-------|----------|
| D-02 | Máquina de estados (`IDLE→AWAITING_*→DONE`) persistida en `conversations` | P3 | `app/bot/states.py`, `app/repositories/models.py` (`ConversationModel`), `app/repositories/conversation_repo.py`, `on_text`+`next_state` en `app/bot/handlers.py`, `MessageHandler` en `app/bot/main.py`, `tests/test_conversation_repo.py` (7 tests, incluye supervivencia a reinicio con sqlite en archivo) |
| D-06 | Formateo del veredicto con semáforo (🟢🟡🔴) | P3 | `app/bot/formatters.py` (`format_verdict`), `tests/fixtures/verification_{go,caution,stop}.json`, `tests/test_formatters.py` (9 tests). Una columna, sin tablas → sin scroll horizontal en celular |
| D-07 | Botones inline (Ver detalle · Calcular precio · Verificar vendedor · Nueva consulta) | P3 | `app/bot/keyboards.py` (`verdict_keyboard`), `on_callback` router en `handlers.py`, `CallbackQueryHandler` en `main.py`, `tests/test_keyboards.py` (4 tests) |

### Bloqueado (dependencias inexistentes)

| ID | Tarea | Bloqueado por |
|----|-------|---------------|
| D-04 | Bot → `POST /verifications` + manejo de errores (502 amable) | **C-05 (P2) no existe en ninguna rama.** Pedir ETA a P2 |
| D-05 | Mensajes progresivos por fuente | **C-09 (P1) no existe.** El más bloqueado. Pedir ETA a P1 |

> Decisión (P3): **bloqueo estricto por dependencia**, sin stubs. D-04/D-05 esperan a C-05/C-09.

### Verificación (2026-08-14)

- ✅ **85/85 tests verdes** en modo mock (65 de Sprint 1 + 20 nuevos de D-02/D-06/D-07).
- ✅ `from app.bot.main import build_application` importa sin romper.
- Cambios en working tree de la rama `testing`, **sin commitear** (a la espera de review de un compañero, DoD §4).

---

## Avisos / handoffs entre roles

**→ P1 / P3 (de P2):** Validación de placa (**C-02**) y los 6 adapters vehiculares (**B-06..B-11**) listos y testeados (35 tests verdes).
- Código de normalización: `app/services/plate.py` — funciones `normalize_plate(plate)` y `is_valid_plate(plate)`.
- Adapters y mergers: `app/integrations/croma/sources/` (`sbs.py`, `apeseg.py`, `sutran.py`, `callao.py`, `sat_debt.py`, `sat_captures.py`).
- Tests: `tests/test_plate.py`, `tests/test_adapters_insurance.py`, `tests/test_adapters_infractions.py`, `tests/test_adapters_sat.py`.
- **Acción para P1:** Ya puedes implementar **B-14** (concurrencia de 6 fuentes con `asyncio.gather`) consumiendo estos mappers.
- **Acción para P3:** En la **Puerta 1** puedes verificar que las 6 fuentes mapean y responden contra `SourceResult`.

**→ P5 (de P3):** el copy final peruano del bot está como placeholder. Lista de textos a reemplazar
(con sus claves y `{placeholders}` que **no** deben cambiar) en `docs/copy-placeholders-p5.md`. Cubre
`_ASK_PLATE/_ASK_PRICE/_DONE`, los 4 `_CB_REPLIES` y las etiquetas de veredicto (`LUZ VERDE/CON CUIDADO/ALTO`).

**→ P2/P1 (de P3):** D-04 espera **C-05** (`POST /verifications`) y D-05 espera **C-09** (jobs async).
Ninguno existe aún en el repo. Avisar cuando estén en `testing` para desbloquear el bot.

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

## Sprint 2 — "El producto decide" (EN CURSO)

> Puerta 1 cerró en verde. Sprint 2 arrancó.

Sprint 2 agrega: orquestacion concurrente (B-14), scoring/veredicto (C-04), endpoint de verificacion completa (C-05), tasacion (C-06), flujo conversacional del bot (D-02, D-04-D-07), verificacion de vendedor (B-12, B-13, C-03), pagina web del reporte (E-01).

**Avance:** bot D-02/D-06/D-07 hechos (P3). Bloqueantes clave del bot: **C-05 (P2)** y **C-09 (P1)** aún no existen → D-04/D-05 en espera. Ver "Sprint 2 — Estado de tareas" arriba.

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
