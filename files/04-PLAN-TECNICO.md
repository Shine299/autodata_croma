# 04 — Plan Técnico

> **SDD paso 3 — el CÓMO.** Deriva de `02-SPEC.md` y `03-API-DESIGN.md`. No agrega alcance.

---

## 1. Stack elegido

| Capa | Tecnología | Por qué |
|---|---|---|
| API | **FastAPI** (Python 3.11+) | Async nativo (clave: 6 llamadas a Croma en paralelo), validación con Pydantic que calza 1:1 con el contrato de API, docs OpenAPI automáticas para la demo |
| Cliente HTTP | **httpx** (AsyncClient) | Concurrencia real con `asyncio.gather` |
| Bot | **python-telegram-bot** v21 (async) | Aprobación instantánea vs WhatsApp Business API, botones inline, mensajes progresivos |
| BD + caché | **Supabase (PostgreSQL)** | Hosted, cero setup, `JSONB` para guardar respuestas crudas, dashboard para revisar datos en vivo |
| Web del reporte | **Jinja2 + Tailwind CDN** servido por FastAPI | Un solo despliegue, sin build step, responsive gratis |
| Deploy | **Railway** o **Render** (free tier) | Deploy desde Git en minutos, HTTPS gratis (Telegram exige HTTPS para webhook) |
| Gestión de deps | `uv` o `pip` + `requirements.txt` | Lo que el equipo ya maneje |

**Descartado y por qué:** WhatsApp Business API (aprobación lenta) · Node/Go/Rust (el equipo
va más rápido en Python) · frontend SPA (no aporta a los criterios del jurado).

> Nota: durante la hackathon el bot corre con **polling** (`run_polling`), no webhook.
> Cero configuración de HTTPS. El webhook queda documentado en la API para el pitch.

---

## 2. Arquitectura

```
┌──────────────┐
│   Telegram   │
└──────┬───────┘
       │ polling
┌──────▼────────────────────────────────────────────────┐
│  app/bot/            handlers, FSM, formateo de chat   │
└──────┬─────────────────────────────────────────────────┘
       │ llamadas internas (mismo proceso)
┌──────▼─────────────────────────────────────────────────┐
│  app/api/            routers FastAPI (contrato 03)     │
├────────────────────────────────────────────────────────┤
│  app/services/                                         │
│    verification_service   orquesta todo                │
│    scoring_service        veredicto + riskScore        │
│    appraisal_service      precio justo + guion         │
├────────────────────────────────────────────────────────┤
│  app/integrations/croma/                               │
│    client.py     httpx, auth, backoff, headers cuota   │
│    sources/      sbs, apeseg, sutran, callao, sat, sunat│
│    mappers.py    Croma JSON → modelos del dominio      │
│    mock.py       fixtures locales (modo desarrollo)    │
├────────────────────────────────────────────────────────┤
│  app/repositories/   cache_repo, verification_repo     │
└──────┬─────────────────────────────────────────────────┘
       │
┌──────▼───────┐
│  Supabase    │
└──────────────┘
```

### Estructura de carpetas

```
autodata/
├── app/
│   ├── main.py
│   ├── config.py                  # settings vía pydantic-settings
│   ├── api/
│   │   ├── vehicles.py
│   │   ├── sellers.py
│   │   ├── verifications.py
│   │   ├── appraisals.py
│   │   ├── conversations.py
│   │   ├── jobs.py
│   │   └── health.py
│   ├── schemas/                   # Pydantic = contrato de 03-API-DESIGN.md
│   ├── services/
│   ├── integrations/croma/
│   ├── repositories/
│   ├── bot/
│   │   ├── main.py
│   │   ├── handlers.py
│   │   ├── states.py
│   │   ├── parsers.py             # extraer placa, precio, DNI de texto libre
│   │   └── formatters.py          # dominio → mensajes de Telegram
│   ├── web/templates/
│   └── core/                      # errores, logging, rate limiter
├── fixtures/                      # respuestas congeladas de Croma (Artículo III)
├── docs/                          # ESTA carpeta
├── tests/
├── .env.example
└── requirements.txt
```

---

## 3. Modelo de datos (Supabase)

```sql
-- Caché de respuestas crudas de Croma. La pieza más importante del proyecto.
create table croma_cache (
  id            uuid primary key default gen_random_uuid(),
  source        text not null,          -- 'SBS' | 'SUTRAN' | 'SUNAT' ...
  lookup_key    text not null,          -- placa normalizada o hash del documento
  payload       jsonb not null,         -- respuesta cruda, tal cual
  status        text not null,          -- 'ok' | 'not_found' | 'error'
  fetched_at    timestamptz not null default now(),
  expires_at    timestamptz not null,
  unique (source, lookup_key)
);
create index on croma_cache (expires_at);

create table verifications (
  id            uuid primary key default gen_random_uuid(),
  plate         text not null,
  seller_hash   text,                   -- sha256 del documento. NUNCA en claro (Art. VI)
  asking_price  numeric,
  verdict       text not null,
  risk_score    int  not null,
  flags         jsonb not null default '[]',
  payload       jsonb not null,         -- response completo del endpoint
  channel       text,
  created_at    timestamptz not null default now()
);
create index on verifications (plate);

create table appraisals (
  id              uuid primary key default gen_random_uuid(),
  verification_id uuid references verifications(id) on delete cascade,
  asking_price    numeric not null,
  fair_price      numeric not null,
  deductions      jsonb not null default '[]',
  script          text,
  created_at      timestamptz not null default now()
);

create table quota_log (
  id          bigserial primary key,
  source      text not null,
  endpoint    text not null,
  remaining   int,
  request_id  text,
  cache_hit   boolean not null default false,
  latency_ms  int,
  created_at  timestamptz not null default now()
);

create table conversations (
  chat_id     text primary key,
  state       text not null default 'IDLE',
  context     jsonb not null default '{}',
  updated_at  timestamptz not null default now()
);
```

**TTL de caché por fuente:**

| Fuente | TTL | Razón |
|---|---|---|
| SBS SOAT | 7 días | El campo `data_through` es mensual |
| APESEG | 24 h | |
| SUTRAN / Callao | 24 h | |
| SAT Lima cuenta | 12 h | Deuda cambia con pagos |
| SAT Lima capturas | 12 h | Señal crítica, no envejecer mucho |
| SUNAT | 7 días | Ficha de contribuyente cambia poco |

---

## 4. Cliente de Croma — requisitos obligatorios

```python
# app/integrations/croma/client.py — contrato que debe cumplir
class CromaClient:
    async def call(self, path: str, body: dict, *, cache_key: str, ttl: timedelta) -> SourceResult
```

**Debe implementar, sin excepción:**

1. **Modo mock** (`CROMA_MODE=mock`) que lee de `fixtures/` sin tocar la red. Default en dev.
2. **Caché read-through** contra `croma_cache` antes de cualquier request.
3. **Auth**: header `Authorization: Bearer $CROMA_API_KEY`.
4. **Logging de cuota**: leer `X-RateLimit-Remaining`, `X-Request-Id`, `X-Cache` y escribir en
   `quota_log`. Los headers **pueden no venir** (el limitador falla abierto) → nunca asumirlos.
5. **Backoff en 429**: respetar `Retry-After`, máximo 2 reintentos, luego error controlado.
6. **Timeout** de 40 s por fuente. Al vencer: `status = "error"`, no excepción propagada.
7. **Nunca tumbar la verificación completa** por una fuente caída → `SourceResult` siempre.
8. **Ejecución concurrente**: `asyncio.gather(..., return_exceptions=True)`.

```python
@dataclass
class SourceResult:
    source: str
    status: Literal["ok", "not_found", "error", "skipped"]
    data: dict | None
    error: str | None
    latency_ms: int
    from_cache: bool
```

---

## 5. Motor de scoring (`scoring_service`)

```python
WEIGHTS = {
    "CAPTURE_ORDER":    100,   # override → STOP directo
    "HIGH_ACCIDENTS":    30,   # >= 3 siniestros
    "ACCIDENTS":         20,   # 1-2 siniestros
    "HIGH_DEBT":         25,   # > S/ 3000
    "DEBT":              15,   # S/ 500 - 3000
    "SEVERE_INFRACTION": 15,   # al menos una "Muy Grave"
    "SOAT_MISSING":      15,
    "SOAT_EXPIRED":      10,
    "SELLER_IS_DEALER":  20,   # dice particular, tiene RUC de venta de vehículos
    "SELLER_HAS_DEBT":   10,
    "SOURCES_UNAVAILABLE": 5,
}

# Umbrales
#   riskScore >= 60  o  CAPTURE_ORDER presente  → STOP
#   riskScore 25-59                              → CAUTION
#   riskScore < 25                               → GO
#
# Reglas de seguridad (Art. V):
#   - CAPTURE_ORDER siempre fuerza STOP, sin importar el score.
#   - Si unverifiedSources >= 2, el veredicto máximo es CAUTION (nunca GO).
```

## 6. Motor de tasación (`appraisal_service`)

```python
deductions = []
deductions += [("Deuda transferible", vehicle.infractions.total + vehicle.taxDebt.total, "SUTRAN + SAT Lima")]
deductions += [("Siniestros registrados", min(accidents * 0.04, 0.20) * asking, "SBS")]
deductions += [("Renovación de SOAT", 350, "APESEG")] if not has_active_soat else []

fair_price = max(asking - sum(d.amount for d in deductions), 0)
# Si verdict == STOP por CAPTURE_ORDER → recommendation = "NO_COMPRAR", fair_price = 0
```

---

## 7. Configuración (`.env.example`)

```bash
CROMA_API_KEY=
CROMA_BASE_URL=https://api.croma.run
CROMA_MODE=mock                 # mock | live   ← default mock (Artículo III)
CROMA_TIMEOUT_SECONDS=40

TELEGRAM_BOT_TOKEN=
TELEGRAM_MODE=polling

SUPABASE_URL=
SUPABASE_KEY=
DATABASE_URL=

APP_ENV=dev
PUBLIC_BASE_URL=http://localhost:8080
INTERNAL_API_KEY=
```

## 8. Placas sembradas para la demo

Consultar **una sola vez** en modo `live`, guardar en `fixtures/` y congelar.

| # | Escenario | Veredicto esperado | Qué demuestra |
|---|---|---|---|
| 1 | Auto limpio, SOAT vigente, sin deuda | `GO` | El camino feliz |
| 2 | 2+ siniestros SOAT | `CAUTION` | El dato que el vendedor oculta |
| 3 | Deuda alta en papeletas | `CAUTION` + descuento grande | La conversión a soles |
| 4 | Orden de captura vigente | `STOP` | El momento wow |
| 5 | *(en vivo ante el jurado)* | el que salga | Que es real, no un video |

---

## 9. Riesgos técnicos y mitigación

| Riesgo | Prob. | Impacto | Mitigación |
|---|---|---|---|
| Se acaba la cuota de 100/día | **Alta** | Crítico | Modo mock por default, caché, quota_log, solo el Tech Lead autoriza `live` |
| Fuente oficial caída el día de la demo | Media | Alto | Caché de las 5 placas + degradación elegante ya especificada |
| SBS/SUTRAN tardan demasiado | Alta | Medio | Concurrencia + mensajes progresivos + timeout de 40 s |
| Deploy falla a última hora | Media | Alto | Demo funciona en localhost con ngrok como plan B |
| El parser de texto libre falla en vivo | Media | Medio | Botones inline como camino alternativo siempre visible |
| Merge conflicts entre 5 personas | Alta | Medio | Un dueño por carpeta, PRs chicos, contrato de API congelado |
