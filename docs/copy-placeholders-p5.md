# Copy placeholders para P5 — Bot (Sprint 2)

> Estructura y lógica ya resueltas por P3 (D-02/D-06/D-07). Lo que falta es el **tono
> peruano final**. P5: reemplaza los textos; **no cambies las claves ni los `{placeholders}`**
> ni el formato Markdown (negritas, `\n`). Los `{plate}`, `{price}`, `{vid}` se rellenan solos.

## `app/bot/handlers.py`

| Constante | Cuándo se muestra | Texto actual (placeholder) |
|---|---|---|
| `_ASK_PLATE` | El usuario no mandó una placa válida | "Mándame la placa del auto (ej. `ABC-123`) y lo reviso. 🚗" |
| `_ASK_PRICE` | Ya tengo la placa, pido el precio | "Anotada la placa *{plate}*. ¿A cuánto te lo ofrecen? (ej. `32 mil`)" |
| `_DONE` | Tengo placa + precio | "Listo: placa *{plate}* a *S/ {price:,.0f}*. …" |
| `_API_ERROR` | La API no respondió (502/timeout) al verificar (D-04) | "😕 No pude terminar la verificación ahora mismo…" |
| `_PROGRESS` | Cada fuente que va llegando en el modo progresivo (D-05) | "🔎 Consultando *{source}*…" |
| `_CB_REPLIES[detail]` | Botón "Ver detalle" | "Abre el detalle completo aquí: {vid}" |
| `_CB_REPLIES[appraise]` | Botón "Calcular precio" | "Dale, ¿a cuánto te lo ofrecen? Escríbeme el precio…" |
| `_CB_REPLIES[seller]` | Botón "Verificar vendedor" | "Para revisar al vendedor necesito tu *sí* explícito…" |
| `_CB_REPLIES[new]` | Botón "Nueva consulta" | "¡Listo! Mándame otra placa cuando quieras. 🚗" |

## `app/bot/formatters.py`

| Constante | Uso | Actual |
|---|---|---|
| `_VERDICT_LABEL[GO]` | Etiqueta del semáforo verde | "LUZ VERDE" |
| `_VERDICT_LABEL[CAUTION]` | Amarillo | "CON CUIDADO" |
| `_VERDICT_LABEL[STOP]` | Rojo | "ALTO" |

> `headline`, `summary`, `disclaimer` y los `title`/`detail` de cada flag **vienen de la API**
> (scoring de P2), no del bot: si su tono no gusta, se ajusta en el backend, no aquí.

## `app/bot/handlers.py` (D-01, ya existía)
`_START_TEXT` y `_AYUDA_TEXT` también son placeholders de P5.
