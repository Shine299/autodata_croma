# 03 — Diseño de API

> Metodología aplicada a cada endpoint:
> **1️⃣ Identificar el recurso → 2️⃣ Realizar el EndPoint → 3️⃣ Identificar JSON Request / JSON Response**
>
> Base URL local: `http://localhost:8080`
> Prefijo: `/api/v1`
> Auth interna: header `X-Api-Key` (solo para consumo del bot; el bot y la API viven juntos en el MVP).

---

## Convenciones globales

- JSON en **camelCase**. Fechas en **ISO-8601**. Montos en **number** (decimal), moneda aparte en ISO-4217 (`PEN`).
- Todo response de éxito viene envuelto en `data`.
- Todo error viene envuelto en `error`.

**Envelope de error (estándar del proyecto)**

```jsonc
{
  "error": {
    "type": "validation_error | not_found | rate_limit_error | upstream_error | internal_error",
    "code": "invalid_plate",
    "message": "La placa no tiene un formato válido.",
    "requestId": "req_8f2c..."
  }
}
```

**Códigos HTTP usados:** `200` OK · `201` Created · `202` Accepted (async) · `400` validación ·
`404` no encontrado · `429` cuota excedida · `502` fuente oficial caída · `500` interno.

**Enums del dominio**

```jsonc
verdict       : "GO" | "CAUTION" | "STOP"
sourceStatus  : "ok" | "not_found" | "error" | "skipped"
documentType  : "DNI" | "RUC" | "CE"
flagCode      : "CAPTURE_ORDER" | "SOAT_EXPIRED" | "SOAT_MISSING" | "HIGH_ACCIDENTS"
              | "ACCIDENTS" | "HIGH_DEBT" | "DEBT" | "SEVERE_INFRACTION"
              | "SELLER_IS_DEALER" | "SELLER_HAS_DEBT" | "SELLER_NOT_FOUND"
              | "SOURCES_UNAVAILABLE"
severity      : "info" | "warning" | "critical"
```

---

# Recurso 1 — Vehículo (`vehicle`)

### 1️⃣ Identificar el recurso
¿Quién es nuestro recurso cuando revisamos un auto por placa? → **Vehículo (`vehicle`)**.
La acción que ejecutamos sobre él es una **inspección documental** (`inspection`), que es un
sub-recurso: un vehículo tiene muchas inspecciones a lo largo del tiempo.

### 2️⃣ Realizar EndPoint

```jsx
POST: localhost:8080/api/v1/vehicles/inspections
```

Complementarios:

```jsx
GET: localhost:8080/api/v1/vehicles/inspections/{inspectionId}
GET: localhost:8080/api/v1/vehicles/{plate}/inspections        // historial
```

### 3️⃣ JSON Request

```jsonc
{
  "plate": string,            // requerido. "ABC-123" | "ABC123" | "A1B234"
  "sources": string[],        // opcional. default: todas
                              // ["SBS","APESEG","SUTRAN","CALLAO","SAT_LIMA","SAT_CAPTURAS"]
  "forceRefresh": boolean     // opcional. default false. Ignora caché. Consume cuota.
}
```

### 3️⃣ JSON Response `200`

```jsonc
{
  "data": {
    "inspectionId": string,
    "plate": string,               // normalizada: "ABC123"
    "createdAt": string,           // ISO-8601
    "fromCache": boolean,
    "cachedAt": string | null,

    "insurance": {
      "status": string,            // sourceStatus
      "hasActiveSoat": boolean,
      "company": string | null,
      "policyNumber": string | null,
      "startDate": string | null,
      "endDate": string | null,
      "accidentCount": number,     // siniestralidad SBS últimos 5 años
      "policyCount": number,
      "dataThrough": string | null,
      "source": "SBS + APESEG"
    },

    "infractions": {
      "status": string,
      "hasInfractions": boolean,
      "count": number,
      "currency": "PEN",
      "total": number,
      "severeCount": number,
      "items": [
        {
          "documentNumber": string,
          "documentType": string,
          "documentDate": string | null,
          "infractionCode": string,
          "classification": string,   // "Muy Grave" | "Grave" | "Leve"
          "source": "SUTRAN" | "CALLAO"
        }
      ]
    },

    "taxDebt": {
      "status": string,
      "hasDebt": boolean,
      "currency": "PEN",
      "total": number,
      "items": [
        { "concept": string, "period": string, "amount": number }
      ],
      "source": "SAT_LIMA"
    },

    "captureOrder": {
      "status": string,
      "hasCaptureOrder": boolean,
      "issuedAt": string | null,
      "reason": string | null,
      "source": "SAT_LIMA"
    },

    "sourcesSummary": [
      { "source": string, "status": string, "latencyMs": number, "error": string | null }
    ],
    "unverifiedSources": string[]
  }
}
```

**Errores propios:** `400 invalid_plate` · `429 rate_limited` · `502 upstream_error`.

---

# Recurso 2 — Vendedor (`seller`)

### 1️⃣ Identificar el recurso
¿Quién es el recurso cuando verificamos a la contraparte? → **Vendedor (`seller`)**.
La acción es un **screening** (`screening`): una revisión de antecedentes relevantes a la
transacción. Es el diferencial del producto.

### 2️⃣ Realizar EndPoint

```jsx
POST: localhost:8080/api/v1/sellers/screenings
```

```jsx
GET: localhost:8080/api/v1/sellers/screenings/{screeningId}
```

### 3️⃣ JSON Request

```jsonc
{
  "documentType": string,      // "DNI" | "RUC" | "CE"
  "documentNumber": string,    // 8 dígitos DNI/CE, 11 dígitos RUC
  "claimedRole": string,       // "PARTICULAR" | "DEALER" | "UNKNOWN"  ← lo que el vendedor dice ser
  "consent": boolean           // requerido true. El usuario confirmó la consulta.
}
```

### 3️⃣ JSON Response `200`

```jsonc
{
  "data": {
    "screeningId": string,
    "documentType": string,
    "documentMasked": string,      // "*****123"
    "createdAt": string,

    "taxpayer": {
      "status": string,            // sourceStatus
      "found": boolean,
      "name": string | null,
      "ruc": string | null,
      "taxpayerStatus": string | null,   // "ACTIVO" | "BAJA DE OFICIO" ...
      "condition": string | null,        // "HABIDO" | "NO HABIDO"
      "mainActivity": string | null,
      "isVehicleTrader": boolean,        // actividad económica = venta de vehículos
      "registeredAt": string | null,
      "source": "SUNAT"
    },

    "personalDebt": {
      "status": string,
      "hasDebt": boolean,
      "currency": "PEN",
      "total": number,
      "itemCount": number,
      "relatedPlates": string[],
      "source": "SAT_LIMA"
    },

    "flags": [
      { "code": string, "severity": string, "title": string, "detail": string }
    ],
    "sourcesSummary": [
      { "source": string, "status": string, "latencyMs": number, "error": string | null }
    ]
  }
}
```

> **Bandera estrella:** `SELLER_IS_DEALER` — se dispara cuando `claimedRole = "PARTICULAR"`
> y `taxpayer.isVehicleTrader = true`. Es la señal que ningún competidor peruano entrega.

---

# Recurso 3 — Verificación (`verification`)

### 1️⃣ Identificar el recurso
El recurso agregador del producto: la **Verificación** cruza vehículo + vendedor + precio
y produce el veredicto. Es lo que el usuario percibe como "el resultado".

### 2️⃣ Realizar EndPoint

```jsx
POST: localhost:8080/api/v1/verifications
GET:  localhost:8080/api/v1/verifications/{verificationId}
GET:  localhost:8080/api/v1/verifications/{verificationId}/report
```

### 3️⃣ JSON Request

```jsonc
{
  "plate": string,                  // requerido
  "askingPrice": number | null,     // opcional. En PEN.
  "currency": "PEN",
  "seller": {                       // opcional. Si viene, se ejecuta el screening.
    "documentType": string,
    "documentNumber": string,
    "claimedRole": string,
    "consent": boolean
  },
  "channel": string                 // "telegram" | "web" | "api"
}
```

### 3️⃣ JSON Response `200`

```jsonc
{
  "data": {
    "verificationId": string,
    "createdAt": string,
    "plate": string,

    "verdict": string,             // "GO" | "CAUTION" | "STOP"
    "riskScore": number,           // 0-100. Mayor = peor.
    "headline": string,            // 1 línea en lenguaje natural para el chat
    "summary": string,             // 2-3 líneas

    "flags": [
      {
        "code": string,
        "severity": string,
        "title": string,
        "detail": string,
        "source": string
      }
    ],

    "vehicle":  { /* objeto data de vehicles/inspections */ },
    "seller":   { /* objeto data de sellers/screenings */ } | null,
    "appraisal":{ /* objeto data de appraisals */ }        | null,

    "confidence": {
      "verifiedSources": number,
      "totalSources": number,
      "capped": boolean            // true si el veredicto fue limitado por fuentes caídas
    },
    "reportUrl": string,           // "https://.../r/{verificationId}"
    "disclaimer": string
  }
}
```

**Response `202` (modo asíncrono, cuando `Prefer: respond-async`)**

```jsonc
{
  "data": { "jobId": string, "status": "pending", "pollUrl": "/api/v1/jobs/{jobId}" }
}
```

---

# Recurso 4 — Tasación (`appraisal`)

### 1️⃣ Identificar el recurso
¿Quién es el recurso cuando convertimos hallazgos en dinero? → **Tasación (`appraisal`)**.
Es un sub-recurso de la verificación: una verificación puede tener varias tasaciones
(el vendedor baja el precio, se recalcula).

### 2️⃣ Realizar EndPoint

```jsx
POST: localhost:8080/api/v1/verifications/{verificationId}/appraisals
```

### 3️⃣ JSON Request

```jsonc
{
  "askingPrice": number,      // requerido. PEN
  "currency": "PEN",
  "tone": string              // "cordial" | "firme"  → afecta el guion generado
}
```

### 3️⃣ JSON Response `200`

```jsonc
{
  "data": {
    "appraisalId": string,
    "verificationId": string,
    "currency": "PEN",
    "askingPrice": number,
    "fairPrice": number,
    "totalDeduction": number,
    "deductionPct": number,          // 0-100

    "deductions": [
      {
        "concept": string,           // "Papeletas SUTRAN pendientes"
        "amount": number,
        "basis": string,             // "100% del monto adeudado"
        "source": string             // "SUTRAN"
      }
    ],

    "recommendation": string,        // "NEGOCIAR" | "NO_COMPRAR" | "PRECIO_JUSTO"
    "negotiationScript": string,     // mensaje listo para copiar y pegar al vendedor
    "notes": string[]
  }
}
```

**Regla:** si `verdict = "STOP"` por `CAPTURE_ORDER`, este endpoint responde
`recommendation: "NO_COMPRAR"` y `fairPrice: 0`. No se negocia un auto que se pueden llevar.

---

# Recurso 5 — Conversación (`conversation`)

### 1️⃣ Identificar el recurso
El recurso del canal es la **Conversación**: el hilo entre el usuario de Telegram y el bot.
Los **mensajes** son su sub-recurso.

### 2️⃣ Realizar EndPoint

```jsx
POST: localhost:8080/api/v1/conversations/messages     // webhook de Telegram
GET:  localhost:8080/api/v1/conversations/{chatId}     // estado del hilo (debug)
```

### 3️⃣ JSON Request (normalizado, independiente del proveedor de chat)

```jsonc
{
  "channel": "telegram",
  "chatId": string,
  "messageId": string,
  "text": string,
  "callbackData": string | null,   // botones inline
  "receivedAt": string
}
```

### 3️⃣ JSON Response

```jsonc
{
  "data": {
    "chatId": string,
    "state": string,               // "IDLE"|"AWAITING_PLATE"|"AWAITING_PRICE"|"AWAITING_SELLER"|"DONE"
    "extracted": {
      "plate": string | null,
      "askingPrice": number | null,
      "documentNumber": string | null
    },
    "replies": [
      {
        "text": string,
        "parseMode": "Markdown",
        "buttons": [ { "label": string, "action": string } ]
      }
    ]
  }
}
```

---

# Recurso 6 — Job asíncrono (`job`)

### 1️⃣ Identificar el recurso
SBS y SUTRAN son lentos. El recurso que representa un trabajo en curso es el **Job**.

### 2️⃣ Realizar EndPoint

```jsx
GET: localhost:8080/api/v1/jobs/{jobId}
```

### 3️⃣ JSON Response

```jsonc
{
  "data": {
    "jobId": string,
    "status": string,          // "pending" | "running" | "completed" | "failed"
    "progress": number,        // 0-100
    "completedSources": string[],
    "pendingSources": string[],
    "result": object | null,   // verificación completa cuando status = "completed"
    "error": object | null,
    "createdAt": string,
    "updatedAt": string
  }
}
```

---

# Recurso 7 — Salud y cuota (`health`, `quota`)

### 2️⃣ Realizar EndPoint

```jsx
GET: localhost:8080/api/v1/health
GET: localhost:8080/api/v1/quota
```

### 3️⃣ JSON Response `/quota`

```jsonc
{
  "data": {
    "limit": number,
    "remaining": number,
    "resetAt": string,
    "consumedToday": number,
    "cacheHitRate": number,        // 0-1
    "mode": "live" | "mock"
  }
}
```

> Este endpoint existe por el **Artículo III** de la constitución. Se revisa antes de cada
> llamada real y **se muestra en la demo** como prueba de production readiness.

---

## Mapa de dependencias con Croma

| Endpoint AutoData | Endpoints Croma que consume | Costo en cuota |
|---|---|---|
| `POST /vehicles/inspections` | SBS SOAT, APESEG SOAT, SUTRAN, Callao, SAT Lima cuenta, SAT Lima capturas | **6** |
| `POST /sellers/screenings` | SUNAT (doc), SAT Lima cuenta (dni/ruc) | **2** |
| `POST /verifications` | los dos anteriores | **hasta 8** |
| `POST /appraisals` | ninguno (cálculo local) | **0** |
| `POST /conversations/messages` | ninguno directo | **0** |

> ⚠️ Con 100 requests/día: **máximo ~12 verificaciones completas diarias para todo el equipo.**
> El caché no es una optimización, es un requisito de supervivencia.
