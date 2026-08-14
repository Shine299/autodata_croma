# 09 — Demo, Pitch y Entrega

---

## 1. Guion de la demo (3 minutos)

### 0:00 – 0:30 · El problema, con evidencia

> "En Perú, verificar un auto usado obliga a revisar más de 20 portales del Estado, cada uno
> con su captcha. Miren esto: la 'consulta vehicular gratuita' más buscada del país es en
> realidad un directorio de 35 enlaces. El usuario hace los clics. Y cuando se cansa, hay un
> botón de WhatsApp donde le cobran 35 soles por hacerlos por él."
>
> "Nadie paga por los datos. Los datos son públicos y gratis. Pagan por no tener que usar
> una interfaz."

*(Mostrar automotor.pe en pantalla, 5 segundos. La evidencia visual vale más que la frase.)*

### 0:30 – 1:00 · La solución

> "AutoData vive donde el usuario ya está: en el chat. Le mandas la placa y te devuelve
> tres cosas que nadie más te da junto: un veredicto, las alertas críticas, y cuánto
> deberías pagar."

### 1:00 – 2:15 · Demo en vivo (Telegram proyectado desde el celular)

```
Usuario: ABC-123, me lo venden a 32 mil
```

Mostrar los mensajes progresivos llegando uno por uno:

1. ✅ SOAT vigente — Interseguro, vence 19/02/2027 *(APESEG)*
2. ⚠️ 2 siniestros reportados en 5 años *(SBS)*
3. ⚠️ S/ 1,840 en papeletas, 1 muy grave *(SUTRAN)*
4. 🛑 **Orden de captura vigente** *(SAT Lima)*
5. **VEREDICTO: NO COMPRES** — este auto puede ser internado en cualquier momento.

Tocar `[Verificar al vendedor]` → confirmación → screening:

> ⚠️ "Se presenta como particular, pero tiene RUC activo desde 2019 con actividad de venta
> de vehículos. Es revendedor." *(SUNAT)*

**Decir en voz alta:** *"Todas las plataformas peruanas verifican la placa. Ninguna verifica
a quien te la vende. Este es el dato que cambia la conversación."*

Luego, segunda placa (una limpia) → tocar `[Calcular precio]`:

> Precio pedido: S/ 32,000
> − S/ 1,840 papeletas pendientes *(SUTRAN)*
> − S/ 2,560 por 2 siniestros *(SBS)*
> **Precio justo: S/ 27,600**
> *(y el mensaje listo para copiar y pegar al vendedor)*

### 2:15 – 2:45 · Croma como corazón + honestidad

> "Todo esto son 6 endpoints de Croma consultados en paralelo: SBS, APESEG, SUTRAN, Callao,
> SAT Lima cuenta y SAT Lima capturas. Más SUNAT para el vendedor. Sin Croma no hay producto."
>
> "Y les digo lo que **no** hacemos: no tenemos SUNARP ni MTC. No damos cadena de propietarios
> ni revisión técnica. Cubrimos las señales que cambian la decisión de compra, y lo decimos
> en la interfaz. Preferimos un producto honesto a uno que promete de más."

*(Mostrar `/api/v1/quota` en pantalla: cuota consumida, tasa de cache hit. Eso es production
readiness demostrada, no declarada.)*

### 2:45 – 3:00 · Cierre y modelo

> "El comprador de auto usado compra una vez cada cinco años. Por eso el que paga no debería
> ser él. El siguiente paso es un sello verificado con QR para avisos de Marketplace y una
> API para concesionarias: ellos pagan, el comprador ve el reporte gratis, y cada aviso con
> el sello es distribución gratuita."

---

## 2. Cómo cada parte de la demo ataca un criterio

| Criterio del jurado | Qué de la demo lo demuestra |
|---|---|
| **Originalidad** | La verificación del vendedor (`SELLER_IS_DEALER`) y la conversión a soles. Nadie más lo hace. |
| **Uso de Croma** | 7 endpoints de Croma en paralelo. La frase "sin Croma no hay producto" es literal. |
| **Impacto y production readiness** | Bot funcional en Telegram, caché real, `/quota` visible, manejo de errores, límites declarados |

---

## 3. Preguntas probables del jurado (y respuestas)

**"¿Esto no lo hace ya Mi Torito?"**
> Mi Torito consolida más fuentes que nosotros, sí, incluyendo SUNARP. Pero entrega un
> documento. Nosotros entregamos una decisión y un precio, verificamos a la contraparte —
> que nadie hace — y vivimos en el chat, no en una web. Competimos en la capa de decisión,
> no en la de datos.

**"¿Por qué no tienen SUNARP?"**
> Croma no lo expone todavía. Evaluamos hacer scraping con `extract-json`, pero SUNARP tiene
> captcha y no era realizable en 36 horas de forma confiable. Preferimos no prometerlo.

**"¿Cómo manejan la cuota de 100 requests diarios?"**
> Caché read-through en Postgres con TTL por fuente, modo mock para todo el desarrollo, y
> logging de cada request. Pueden verlo en `/api/v1/quota`. En producción, el caché
> compartido entre usuarios hace que la misma placa consultada por 10 compradores distintos
> cueste 6 requests, no 60.

**"¿No es riesgoso consultar datos de personas?"**
> Por eso pedimos confirmación explícita antes de cualquier consulta a una persona, mostramos
> solo señales relevantes a la transacción, y guardamos el documento hasheado, nunca en claro.
> Está en el artículo VI de nuestra constitución de proyecto.

**"¿Qué tan real es esto? ¿Funciona fuera de la demo?"**
> Denme una placa ahora mismo. *(Y consultar en vivo. Por eso se reserva cuota.)*

---

## 4. Checklist de entrega

### Antes de grabar
- [ ] Los 4 escenarios sembrados responden en < 3 s desde caché
- [ ] Cuota reservada para 1 consulta en vivo ante el jurado
- [ ] Bot corriendo estable por al menos 30 min sin caerse
- [ ] Ningún stacktrace visible en ningún flujo
- [ ] Celular en modo avión-para-notificaciones (nada de mensajes personales en pantalla)
- [ ] Batería del laptop y del celular al 100%

### Repo
- [ ] README con arquitectura, cómo correr, y captura del bot
- [ ] `.env.example` completo, **sin keys reales**
- [ ] Historial de git limpio de secretos (revisar con `git log -p | grep -i key`)
- [ ] Esta carpeta `docs/` incluida — es parte del entregable y demuestra el método
- [ ] Licencia y créditos del equipo

### Video de respaldo
- [ ] Menos de 3 minutos
- [ ] Audio claro, sin ruido de fondo
- [ ] Se ve la pantalla del celular con nitidez
- [ ] Subido a Drive/YouTube con link público probado en incógnito

### Formulario
- [ ] Link del repo
- [ ] Link del video
- [ ] Link del deploy público
- [ ] Nombres de los 5 integrantes
- [ ] **Enviado antes de las 6:00 p. m.**, no a las 6:29

---

## 5. Plan B

| Si falla | Entonces |
|---|---|
| Internet en la sede | Video de respaldo + capturas |
| Deploy caído | Correr en localhost, proyectar desde el laptop |
| Croma devuelve 429 en vivo | Usar las placas cacheadas y explicar la cuota (suma puntos si se explica bien) |
| El bot no responde | Mostrar la API directo desde `/docs` de FastAPI |
| Se cae Telegram | Página web del reporte `/r/{id}` |
