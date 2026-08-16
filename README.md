# AutoData

> Verifica el auto **y** al vendedor. Devuelve una decision y un precio, no un reporte.

Bot de Telegram que consulta 6 fuentes oficiales del gobierno peruano (via [Croma](https://usecroma.com)) para verificar vehiculos usados antes de comprar. Emite un veredicto GO / CAUTION / STOP, calcula un precio justo y genera un guion de negociacion.

Proyecto de hackathon GOV-TECH Croma 2026.

---

## Arquitectura

Son **2 procesos** que corren a la vez: el **bot** (habla con el usuario en Telegram) y la
**API** (el cerebro: consulta fuentes, puntua y tasa). El bot NO consulta Croma directamente;
le pide todo a la API por HTTP. **Si la API no esta corriendo, el bot no funciona.**

```
   Usuario  ──(Telegram)──▶  BOT  ──HTTP :8000──▶  API (FastAPI)
                          (polling)             │
                                                ├─ CromaClient (httpx)
                                                │     CROMA_MODE=mock → lee fixtures/*.json
                                                │     CROMA_MODE=live → Croma real (api.croma.run)
                                                │        6 fuentes en paralelo:
                                                │        SBS SOAT · APESEG SOAT · SUTRAN ·
                                                │        Callao · SAT cuenta · SAT capturas
                                                │        (+ vendedor: SUNAT · SAT por documento)
                                                ├─ Scoring Engine  → Verdict GO / CAUTION / STOP
                                                ├─ Appraisal       → Precio objetivo = pedido − deducciones
                                                └─ IA Gemini (opcional)  → SOLO tono/saludos
                                                        el veredicto y el precio son deterministas
   Persistencia: Supabase/Postgres (conversacion, cache, cuota). El estado del chat sobrevive reinicios.
```

- **`app/bot/`** — bot de Telegram: maquina de estados, parsers de placa/precio/DNI, formateo del
  reporte y capa de IA de fraseo (`app/integrations/llm/gemini.py`, con fallback si falla).
- **`app/api/` + `app/services/`** — la API: orquesta las fuentes, calcula veredicto y tasacion.
- **`app/integrations/croma/`** — `CromaClient` + un adapter por fuente.

> La IA (Gemini) **nunca** decide el veredicto ni el precio: eso lo calcula codigo determinista.
> La IA solo pone tono natural en el saludo y en el "no te entendi". Marca/modelo/anio/precio de
> mercado NO existen en Croma Peru → el bot los marca como *NO DISPONIBLE*, nunca los inventa.

## Stack

- Python 3.11+
- FastAPI + uvicorn
- httpx (async HTTP)
- Pydantic v2 + pydantic-settings
- python-telegram-bot v21
- SQLAlchemy async + asyncpg/aiosqlite
- Google Gemini (IA de tono, opcional, via REST con httpx)
- pytest + pytest-asyncio

## Instalacion (una vez)

```bash
git clone <repo> && cd autodata_croma
python -m venv .venv
# Windows PowerShell:  .\.venv\Scripts\Activate.ps1
# Linux/Mac:           source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # llenar las variables (ver tabla abajo)
```

## Correr el chatbot (demo)

El chatbot son **2 procesos**: primero la **API**, luego el **bot**. Abre **2 terminales** en
la carpeta del proyecto.

**Terminal 1 — la API (dejala abierta):**

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Verifica que vive (navegador o `curl`): `http://127.0.0.1:8000/api/v1/health` → `{"status":"ok"}`.

**Terminal 2 — el bot:**

```powershell
.\.venv\Scripts\python.exe -m app.bot.main
```

Ahora escribe al bot en Telegram: manda una placa (`DEF-456`), te pedira el precio (`29 mil`)
y respondera con el reporte completo.

> ⚠️ **Puerto 8000 obligatorio**: el bot consume la API en `http://127.0.0.1:8000`
> (`api_base_url` en `app/config.py`). Si la API no esta corriendo o esta en otro puerto, el
> bot mostrara **"🔌 No pude conectar con el servidor de AutoData"**. Arranca siempre la API
> ANTES que el bot; si cierras la Terminal 1, el bot deja de funcionar.

### Mock vs live (misma orquestacion, solo cambia `CROMA_MODE` en `.env`)

| `CROMA_MODE` | De donde saca los datos | Cuando usarlo |
|--------------|-------------------------|---------------|
| `mock` | `fixtures/*.json` (offline, instantaneo) | Pruebas y demo rapida. Placas: `D0H-741`, `DEF-456`, `GHI-789`, `JKL-012` |
| `live` | Croma real (`api.croma.run`) | Ante el jurado. Usa una **placa peruana real**; es lento (20-40s) |

Los **mismos 2 comandos** sirven para ambos modos. Si cambias `CROMA_MODE`, **reinicia la API**
(Ctrl+C en Terminal 1 y vuelve a arrancarla) para que tome el nuevo modo.

En `live` necesitas `CROMA_API_KEY` valida e internet que no bloquee `api.telegram.org` ni
`api.croma.run` (la red de la U suele bloquearlos → usa hotspot).

## Variables de entorno

| Variable | Requerida | Default | Descripcion |
|----------|-----------|---------|-------------|
| `CROMA_API_KEY` | Si | — | API key de platform.usecroma.com |
| `CROMA_BASE_URL` | No | `https://api.croma.run` | URL base de Croma |
| `CROMA_MODE` | No | `mock` | `mock` lee de `fixtures/`, `live` consulta Croma real |
| `CROMA_TIMEOUT_SECONDS` | No | `40` | Timeout por request a Croma |
| `TELEGRAM_BOT_TOKEN` | Si* | — | Token de @BotFather (*solo si corres el bot) |
| `TELEGRAM_MODE` | No | `polling` | Modo del bot |
| `GEMINI_API_KEY` | No | — | Key gratuita de Google AI Studio (IA de tono). Vacia = bot funciona igual (fallback) |
| `GEMINI_MODEL` | No | `gemini-flash-lite-latest` | Modelo de la IA de fraseo (lite = pocos tokens) |
| `LLM_ENABLED` | No | `true` | Activa/desactiva la IA de tono |
| `SUPABASE_URL` | No | — | URL del proyecto Supabase |
| `SUPABASE_KEY` | No | — | Key del proyecto Supabase |
| `DATABASE_URL` | No | — | Connection string PostgreSQL (persiste conversacion/cache/cuota) |
| `APP_ENV` | No | `dev` | Entorno de ejecucion |
| `PUBLIC_BASE_URL` | No | `http://localhost:8080` | URL publica del servicio |
| `INTERNAL_API_KEY` | No | — | Key para endpoints internos |

> El bot consume la API en `http://127.0.0.1:8000` (constante `api_base_url` en `app/config.py`).
> Si mueves el puerto de la API, cambia tambien esa constante.

## Modo mock vs live

Por defecto `CROMA_MODE=mock` — lee respuestas de `fixtures/` sin consumir cuota. Usa este modo
para desarrollo, tests y la demo rapida.

`CROMA_MODE=live` consulta la API real de Croma (`api.croma.run`). Cuota real: **500 requests /
24h por endpoint**. Cada verificacion consulta 6 fuentes del vehiculo (+2 del vendedor si aplica).
La latencia de Croma es alta (20-40s por fuente); algunas pueden dar timeout y el reporte sale con
partes *no verificado* + confianza baja (comportamiento honesto, no un bug).

El catalogo real de endpoints de Croma esta en `https://api.croma.run/catalog`.

## Endpoints

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/quota` | Cuota diaria de Croma |
| POST | `/api/v1/verifications` | Verificacion completa. Con header `Prefer: respond-async` → `202` + `jobId` (progreso incremental) |
| GET | `/api/v1/jobs/{jobId}` | Estado/progreso de una verificacion async |
| GET | `/api/v1/verifications/{id}` | Recupera una verificacion guardada |
| POST | `/api/v1/verifications/{id}/appraisals` | Tasacion + guion (acepta `plate` y `askingPrice`) |
| POST | `/api/v1/sellers/screenings` | Screening del vendedor (SUNAT + SAT), requiere `consent: true` |

### Ejemplo: verificacion

```bash
curl -X POST http://127.0.0.1:8000/api/v1/verifications \
  -H "Content-Type: application/json" \
  -d '{"plate": "DEF456", "askingPrice": 29000}'
```

## Tests

```bash
# Windows PowerShell:
.\.venv\Scripts\python.exe -m pytest -q
# Linux/Mac:
pytest -q
```

`tests/conftest.py` fuerza `CROMA_MODE=mock` y desactiva la IA en toda la suite, asi que los
tests **nunca** tocan la cuota real de Croma ni la API de Gemini.

## Estructura del proyecto

```
app/
  main.py              # FastAPI app (routers + manejo global de errores)
  config.py            # Settings (pydantic-settings). Incluye api_base_url y GEMINI_*
  api/                 # Endpoints (health, quota, verifications, jobs, sellers, web)
  bot/                 # Telegram bot: handlers (maquina de estados), parsers,
                       #   formatters (reporte), keyboards, job_client (async)
  integrations/croma/  # CromaClient + un adapter por fuente
  integrations/llm/    # gemini.py — IA de tono (opcional, con fallback)
  services/            # Scoring, appraisal, plate, vehicles, seller, verification_runner
  schemas/             # Modelos Pydantic (contrato de API)
  repositories/        # Cache, quota log, conversacion (Supabase/SQLite)
  web/                 # Landing y pagina de reporte /r/{id}
fixtures/              # Respuestas mock de Croma
  demo/                # 4 escenarios de demo congelados
tests/                 # pytest (conftest fuerza mock + IA off)
files/                 # Documentacion del proyecto (SPEC, plan, tareas)
```

### Los 2 procesos (recordatorio)

| Proceso | Comando | Que hace |
|---------|---------|----------|
| **API** | `uvicorn app.main:app --port 8000` | Consulta fuentes, puntua, tasa. Debe correr primero |
| **Bot** | `python -m app.bot.main` | Habla con el usuario en Telegram; llama a la API por HTTP |

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
