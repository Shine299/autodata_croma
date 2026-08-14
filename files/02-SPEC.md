# 02 — Especificación Funcional (SPEC)

> **SDD paso 2 — el QUÉ.** Este documento describe comportamiento observable, no
> implementación. Si aquí aparece un nombre de librería o de framework, está mal escrito.

---

## 1. Producto en una frase

**AutoData** es un asistente de Telegram que, con la placa de un vehículo y el documento de
quien lo vende, entrega en menos de un minuto un **veredicto de compra**, las **alertas
críticas** y un **precio justo sugerido con guion de negociación** — usando exclusivamente
datos oficiales del Estado peruano vía Croma.

## 2. Propuesta de valor diferencial

| Lo que hace la competencia | Lo que hace AutoData |
|---|---|
| Verifica la placa | Verifica la placa **y a la persona que vende** |
| Entrega un reporte de 20 fuentes | Entrega un **veredicto**: COMPRA / OJO / NO COMPRES |
| Muestra datos | Convierte los datos a **soles de descuento** |
| Vive en una web | Vive **en el chat**, donde el usuario ya está |
| Jerga registral | Lenguaje de comprador peruano |

## 3. Personas

**Marco, 32, comprador primerizo.** Vio un Yaris 2016 en Marketplace a S/ 32,000. No sabe
qué revisar. Le da flojera y desconfianza entrar a portales del Estado. Tiene WhatsApp y
Telegram. Quiere que alguien le diga *"cómpralo"* o *"no lo compres"*.

**Rosa, 45, vende su auto.** Su auto está limpio y quiere probarlo para cerrar rápido y no
regatear tanto. (Usuario secundario — habilita el modelo de negocio.)

---

## 4. Historias de usuario y criterios de aceptación

### HU-01 — Verificar un vehículo por placa
**Como** comprador, **quiero** enviar una placa **para** conocer las alertas del vehículo.

**Criterios de aceptación**
- [ ] Acepto formatos `ABC-123`, `ABC123`, `A1B-234` y placas de moto; normalizo a mayúsculas sin guion.
- [ ] Si la placa es inválida en formato, respondo con el error y un ejemplo, sin llamar a Croma.
- [ ] Consulto SBS SOAT, APESEG, SUTRAN, Callao, SAT Lima cuenta y SAT Lima capturas.
- [ ] Devuelvo por cada fuente: estado (`ok` / `not_found` / `error`) y su fecha de reporte.
- [ ] Si una fuente falla, el resultado global **no falla**: se marca `unverified` esa sección.
- [ ] Tiempo objetivo de respuesta: < 45 s con fuentes reales, < 3 s con caché.

### HU-02 — Verificar al vendedor por documento
**Como** comprador, **quiero** verificar a quien me vende **para** saber si es quien dice ser.

**Criterios de aceptación**
- [ ] Acepto DNI (8 dígitos), RUC (11 dígitos) y carné de extranjería (8 dígitos).
- [ ] El bot pide **confirmación explícita** antes de consultar a una persona.
- [ ] Consulto SUNAT (ficha del contribuyente) y SAT Lima por documento (deuda personal).
- [ ] Detecto y reporto la bandera **"se presenta como particular pero tiene RUC activo con
      actividad de venta de vehículos"** → es revendedor, no particular.
- [ ] Detecto deuda vehicular a nombre del vendedor en otras placas.
- [ ] Nunca muestro domicilio fiscal completo ni datos no relacionados a la transacción.

### HU-03 — Recibir un veredicto claro
**Como** comprador, **quiero** una conclusión, no una tabla.

**Criterios de aceptación**
- [ ] El veredicto es uno de tres: `GO` (compra), `CAUTION` (ojo), `STOP` (no compres).
- [ ] El veredicto va acompañado de un `riskScore` de 0 a 100 y de las banderas que lo causaron.
- [ ] Reglas mínimas obligatorias:
  - Orden de captura vigente del SAT → **STOP** siempre, sin importar lo demás.
  - Siniestros SOAT ≥ 2 en 5 años → mínimo **CAUTION**.
  - Deuda total > S/ 1,000 → mínimo **CAUTION**.
  - SOAT no vigente → mínimo **CAUTION**.
  - Vendedor con RUC de venta de vehículos declarándose particular → mínimo **CAUTION**.
  - Todo limpio y verificado → **GO**.
- [ ] Si 2 o más fuentes fallaron, el veredicto máximo posible es `CAUTION` (nunca `GO` a ciegas).

### HU-04 — Obtener precio justo y guion de negociación
**Como** comprador, **quiero** saber cuánto ofrecer.

**Criterios de aceptación**
- [ ] Recibo el precio pedido por el vendedor como input opcional.
- [ ] Calculo `fairPrice = askingPrice − Σ deducciones`.
- [ ] Cada deducción se muestra con su **concepto, monto y fuente** (nada de números mágicos).
- [ ] Deducciones del MVP:
  - Deuda transferible (papeletas + impuesto vehicular): 100% del monto.
  - Cada siniestro SOAT registrado: 4% del precio pedido (máx. 20%).
  - SOAT vencido: costo estimado de renovación S/ 350.
  - Orden de captura: no se calcula precio, se recomienda no comprar.
- [ ] Genero un **mensaje listo para copiar y pegar** al vendedor, en tono cordial y firme.

### HU-05 — Conversar en Telegram
**Como** usuario, **quiero** resolver todo en el chat.

**Criterios de aceptación**
- [ ] `/start` explica qué hace el bot en máximo 4 líneas.
- [ ] Puedo escribir en lenguaje natural: *"placa ABC123, me lo venden a 32 mil"*.
- [ ] El bot extrae placa, precio y documento del texto libre.
- [ ] Si falta un dato, el bot lo pide de a uno, nunca todos juntos.
- [ ] Mientras consulta, el bot muestra progreso ("Revisando papeletas SUTRAN…").
- [ ] Los resultados llegan en **mensajes progresivos**, no en un bloque único al final.
- [ ] Botones inline: `Ver detalle` · `Calcular precio` · `Verificar vendedor` · `Nueva consulta`.

### HU-06 — Ver el reporte completo en web *(nice to have)*
**Como** usuario, **quiero** un link con el detalle para compartirlo.

**Criterios de aceptación**
- [ ] El bot entrega un link público `/r/{verificationId}`.
- [ ] La página es responsive, muestra semáforo, alertas, fuentes y fecha de consulta.
- [ ] La página funciona sin JavaScript pesado (server-side render simple).

---

## 5. Flujo principal (happy path)

```
Usuario: /start
Bot:     Hola. Mándame la placa del auto que quieres comprar y te digo si te conviene.
Usuario: ABC-123, me lo venden a 32 mil
Bot:     Buscando ABC-123… ⏳
Bot:     ✅ SOAT vigente (Interseguro, vence 19/02/2027)
Bot:     ⚠️ 2 siniestros reportados a la SBS en los últimos 5 años
Bot:     ⚠️ S/ 1,840 en papeletas SUTRAN (3 infracciones, 1 muy grave)
Bot:     🛑 ORDEN DE CAPTURA vigente en SAT Lima
Bot:     ── VEREDICTO: NO COMPRES ──
         Este auto puede ser internado al depósito en cualquier momento.
         [Ver detalle] [Verificar al vendedor] [Nueva consulta]
```

## 6. Casos borde obligatorios

| Caso | Comportamiento esperado |
|---|---|
| Placa no existe en ninguna fuente | "No encontramos registros para esa placa. Verifica que esté bien escrita." |
| Croma devuelve 429 | Mensaje amable + reintento con `Retry-After`. Nunca mostrar el error crudo. |
| Una fuente cae | Sección marcada `no verificado`, veredicto tope `CAUTION`. |
| Timeout de fuente async | Se entrega lo que sí llegó y se avisa qué falta. |
| Usuario manda texto sin placa | Se pide la placa con un ejemplo. |
| Usuario manda DNI sin confirmar | Se pide confirmación explícita antes de consultar. |
| Placa ya consultada hace <24 h | Se sirve de caché, se indica la fecha de la consulta original. |

## 7. Métricas de éxito de la demo

- 4 placas sembradas responden en < 3 s (desde caché).
- 1 placa en vivo responde con datos reales de Croma delante del jurado.
- 0 stacktraces visibles.
- El veredicto y el precio se explican solos, sin que el presentador tenga que traducir.

## 8. Fuera de alcance (roadmap para el pitch)

SUNARP (cadena de dueños, gravámenes, robo) · MTC revisión técnica · SATs de provincia ·
Infogas GNV · pagos in-app · sello QR verificado para avisos de marketplace ·
API B2B para concesionarias · alertas post-compra de papeletas nuevas · WhatsApp Business API.
