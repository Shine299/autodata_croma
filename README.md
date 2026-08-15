# AutoData

> Verifica el auto **y** al vendedor. Devuelve una decision y un precio, no un reporte.

Bot de Telegram que consulta 6 fuentes oficiales del gobierno peruano (via [Croma](https://usecroma.com)) para verificar vehiculos usados antes de comprar. Emite un veredicto GO / CAUTION / STOP, calcula un precio justo y genera un guion de negociacion.

Proyecto de hackathon GOV-TECH Croma 2026.

---

## Arquitectura

```
Telegram Bot (@autodata_peru_bot)
        |
   FastAPI (async)
        |
   CromaClient (httpx)  -->  Cache (Supabase/SQLite)
        |
   6 fuentes Croma Peru:
     - SBS SOAT (siniestros)
     - APESEG SOAT (poliza vigente)
     - SUTRAN (papeletas nacionales)
     - Callao (papeletas Callao)
     - SAT Lima cuenta (deuda tributaria)
     - SAT Lima capturas (orden de captura)
        |
   Scoring Engine  -->  Verdict: GO / CAUTION / STOP
        |
   Appraisal Engine  -->  Precio justo + guion de negociacion
```

## Stack

- Python 3.11+
- FastAPI + uvicorn
- httpx (async HTTP)
- Pydantic v2 + pydantic-settings
- python-telegram-bot v21
- SQLAlchemy async + asyncpg/aiosqlite
- pytest + pytest-asyncio

## Arranque rapido

```bash
git clone <repo> && cd autodata_croma
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # llenar las variables (ver tabla abajo)
uvicorn app.main:app --reload --port 8080
```

Verificar: `curl http://localhost:8080/api/v1/health` debe responder `200`.

## Variables de entorno

| Variable | Requerida | Default | Descripcion |
|----------|-----------|---------|-------------|
| `CROMA_API_KEY` | Si | — | API key de platform.usecroma.com |
| `CROMA_BASE_URL` | No | `https://api.croma.run` | URL base de Croma |
| `CROMA_MODE` | No | `mock` | `mock` lee de `fixtures/`, `live` consulta Croma real |
| `CROMA_TIMEOUT_SECONDS` | No | `40` | Timeout por request a Croma |
| `TELEGRAM_BOT_TOKEN` | Si* | — | Token de @BotFather (*solo si corres el bot) |
| `TELEGRAM_MODE` | No | `polling` | Modo del bot |
| `SUPABASE_URL` | No | — | URL del proyecto Supabase |
| `SUPABASE_KEY` | No | — | Key del proyecto Supabase |
| `DATABASE_URL` | No | — | Connection string PostgreSQL |
| `APP_ENV` | No | `dev` | Entorno de ejecucion |
| `PUBLIC_BASE_URL` | No | `http://localhost:8080` | URL publica del servicio |
| `INTERNAL_API_KEY` | No | — | Key para endpoints internos |

## Modo mock vs live

Por defecto `CROMA_MODE=mock` — lee respuestas de `fixtures/` sin consumir cuota. Usa este modo para desarrollo y tests.

`CROMA_MODE=live` consulta la API real de Croma. Cuota limitada: 100 requests/dia para todo el equipo (~16 verificaciones). Cada verificacion consulta 6 fuentes.

## Endpoints

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/quota` | Cuota diaria de Croma |
| POST | `/api/v1/verifications` | Verificacion vehicular completa |
| POST | `/api/v1/verifications/{id}/appraisals` | Tasacion y guion de negociacion |

### Ejemplo: verificacion

```bash
curl -X POST http://localhost:8080/api/v1/verifications \
  -H "Content-Type: application/json" \
  -d '{"plate": "ABC123"}'
```

## Tests

```bash
pytest -v
```

Los tests corren en modo mock (no consumen cuota).

## Estructura del proyecto

```
app/
  main.py              # FastAPI app
  config.py            # Settings (pydantic-settings)
  api/                 # Endpoints (health, quota, verifications)
  bot/                 # Telegram bot (handlers, parsers)
  integrations/croma/  # CromaClient + adapters por fuente
  services/            # Scoring, appraisal, plate validation
  schemas/             # Modelos Pydantic (contrato de API)
  repositories/        # Cache, quota log (Supabase/SQLite)
fixtures/              # Respuestas mock de Croma
  demo/                # 4 escenarios de demo congelados
tests/                 # pytest
files/                 # Documentacion del proyecto
```

## Escenarios de demo

| Placa | Escenario | Verdict esperado |
|-------|-----------|------------------|
| D0H-741 | Auto limpio, SOAT vigente | GO |
| DEF-456 | 3 siniestros SOAT | CAUTION |
| GHI-789 | Deuda alta + SOAT vencido | CAUTION |
| JKL-012 | Orden de captura vigente | STOP |
| *(live)* | Placa consultada en vivo ante el jurado | Lo que devuelva Croma |

## Equipo

Hackathon GOV-TECH Croma 2026 — 5 personas, 36 horas.
