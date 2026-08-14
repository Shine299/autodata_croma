# 00 — Contexto del Proyecto

Este documento existe para que cualquier persona **o agente de IA** entienda el problema
completo sin necesidad de contexto externo. Léelo entero antes de tocar código.

---

## 1. La competencia (Croma GOV-TECH Hackathon)

- **Fechas:** 12 al 16 de agosto de 2026. Entrega: **16 ago, 6:30 p. m.**
- **Equipos:** de 1 a 5 personas.
- **Única condición técnica:** la solución debe incluir Croma, vía **API** o vía **MCP**.
- **Premio:** USD 300 + 6 meses de Croma gratis. Un solo ganador.

### Criterios de evaluación (traducir cada decisión a estos tres ejes)

| Criterio | La pregunta que responde | Cómo lo atacamos |
|---|---|---|
| **Originalidad** | ¿Es una idea que nadie más trajo? | Verificamos al **vendedor**, no solo la placa. Nadie en Perú lo hace. |
| **Uso de Croma** | ¿Qué tan central es la plataforma? | Croma es el 100% de nuestra capa de datos. Sin Croma no hay producto. |
| **Impacto y production readiness** | ¿Resuelve un problema real y qué tan cerca está de usarse? | Bot funcional en Telegram, caché real, manejo de errores, límites documentados. |

> Frase clave del organizador: *"Buscamos soluciones de impacto: proyectos que conviertan
> datos públicos en algo que la gente realmente pueda usar."*

---

## 2. El problema

Comprar un auto usado en Perú obliga a revisar información dispersa en **20+ portales
estatales** (SUNARP, SAT Lima, SAT provinciales, SBS, SUTRAN, MTC, APESEG, ATU, PIT, Infogas).
Cada portal tiene su propio captcha, su propio formato y su propia jerga.

Resultado: el comprador promedio **no hace la verificación**, o **paga para que otro la haga**.

### El síntoma que confirma el problema

`automotor.pe` publica una "consulta vehicular gratuita" que en realidad es un **directorio de
~35 enlaces** a portales del Estado. No consulta nada: el usuario hace los clics. Su CTA
principal es un enlace a WhatsApp para pedir el "Reporte Vehicular Detallado" premium con
asesoría personalizada.

**Insight central:** los usuarios que llegan buscando la consulta gratis terminan pagando
~S/ 35 por WhatsApp. No están pagando por datos (todos son públicos y gratuitos). Están
pagando por **no tener que usar una interfaz**. Eso no es analfabetismo digital, es una
preferencia de canal: quieren **delegar**, no navegar.

---

## 3. El mercado (nicho)

**Usuario primario:** persona que va a comprar un auto o moto usado en Perú, de particular a
particular (Facebook Marketplace, NeoAuto, ferias, contactos). Compra 1 vez cada 4–6 años.

**Usuario secundario (el que paga recurrente):** vendedores particulares que quieren cerrar
rápido, concesionarias de seminuevos, y compradores/tasadores profesionales.

**Contexto de mercado:** el volumen de transferencias de vehículos usados en Perú se cuenta
en cientos de miles de unidades al año (SUNARP), muy por encima del volumen de vehículos
nuevos. Es un mercado grande, informal y con asimetría de información brutal a favor del
vendedor.

**Dolores concretos que vamos a resolver:**

1. No sé si el auto tiene deudas que se transfieren conmigo.
2. No sé si el auto chocó y me lo están ocultando.
3. No sé si al auto se lo pueden llevar al depósito (orden de captura del SAT).
4. No sé si el que me vende es realmente el dueño, o es un revendedor disfrazado.
5. Aunque supiera todo lo anterior, **no sé cuánto descontar del precio**.

---

## 4. Competencia — panorama real

| Jugador | Qué hace | Modelo | Debilidad explotable |
|---|---|---|---|
| **automotor.pe** | Directorio de ~35 enlaces a portales estatales | Lead-gen → WhatsApp premium (~S/ 35) | No consulta nada. Toda la fricción la carga el usuario. |
| **Mi Torito** (mitorito.pe) | Consolida 20+ fuentes (SUNARP, SAT Lima/Callao/Chiclayo/Trujillo/Cusco, SBS, MTC, APESEG, ATU, SUTRAN, JNE, Infogas). Semáforo de riesgo, PDF con verificación por ID único, app móvil, producto empresas con carga de lotes | Básico gratis; avanzado S/ 15.90, pack de 3 por S/ 40.90 | **Es nuestro competidor serio.** Entrega un documento, no una decisión. No verifica al vendedor. No vive en el chat. |
| **Plaqui** (plaqui.pe) | Reporte por placa, promete 35+ fuentes en <10 s, gravámenes, prendas, GNV, robo, orden de captura | Pago por reporte, sin suscripción | Mismo formato "reporte". Sin canal conversacional. |
| **Autofact.pe** | Jugador regional (CL/CO/PE) con marca y SEO fuertes | Reporte pagado | Genérico, no adaptado al lenguaje del comprador peruano. |
| **El Estado** | SUNARP, SBS, SUTRAN, APESEG ofrecen consultas **gratuitas** | Gratis | Dispersión + captcha + jerga técnica. Es el "producto gratis" contra el que competimos. |

### Conclusión estratégica

> Un consolidador de consultas por placa **ya existe, cuesta S/ 15.90 y tiene app**.
> Presentar eso en el hackathon = perder en *Originalidad* y además ofrecer **menos**
> cobertura que Mi Torito (porque Croma no tiene SUNARP).

**No competimos en cantidad de fuentes. Competimos en tres huecos que nadie tocó:**

1. **Todos consultan la placa. Nadie consulta al vendedor.**
2. **Todos entregan un reporte. Nadie entrega una decisión y un precio.**
3. **Todos viven en una web. El dinero ya se mueve en el chat.**

---

## 5. Límites duros de Croma (RESTRICCIONES NO NEGOCIABLES)

> ⚠️ Todo agente de IA debe respetar esta sección. Violarla rompe la demo.

### 5.1 Cuotas

| Bucket | Límite | Aplica a |
|---|---|---|
| Default | **100 requests / día** | Todos los endpoints de país |
| Extract & Generate | 60 / hora | `extract-json`, `extract-markdown`, `generate-json` |
| Web Search | 10 / hora | `web-search` |
| Research | 10 / hora | `research` |

- El límite es **por organización, no por key**. Agregar keys NO multiplica la cuota.
- Un **batch cuenta como 1 request por ítem**.
- Los **cache hits del lado de Croma igual consumen cuota**.

**Implicancia crítica:** una verificación completa consume ~5–6 requests
→ **≈16 verificaciones por día para TODO el equipo.**
→ Caché local obligatorio + placas sembradas para la demo. Ver `04-PLAN-TECNICO.md`.

### 5.2 Headers de cuota (loguearlos siempre)

`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`, `X-Request-Id`, `X-Cache`.

El limitador **falla abierto**: si el backend de rate-limit no está disponible, los requests
pasan y NO se emiten headers. **Nunca asumir que los headers existen.**

### 5.3 Error 429

Devuelve envelope `rate_limit_error` + header `Retry-After` en segundos. Backoff obligatorio.

### 5.4 Cobertura Perú — lo que SÍ tenemos (8 fuentes)

| Fuente | Endpoint | Input | Valor para el producto |
|---|---|---|---|
| SBS SOAT | `POST /pe/sbs/soat/v1` | `plate` | **Siniestralidad** (accidentes últimos 5 años) + pólizas históricas |
| APESEG SOAT | `POST /pe/apeseg/soat/v1` | `plate` | Historial de certificados, `has_active_soat` |
| SUTRAN | `POST /pe/sutran/infracciones/v1` | `plate` | Papeletas **nacionales** + `total` en PEN + gravedad |
| Callao | `POST /pe/callao/papeletas/v1` | `plate` | Papeletas de la provincia del Callao |
| SAT Lima cuenta | `POST /pe/sat-lima/...` | `dni`\|`ruc`\|`placa`\|`papeleta` | Deuda: impuesto vehicular + multas |
| SAT Lima capturas | `POST /pe/sat-lima/capturas/...` | `plate` | **Orden de captura / internamiento** ← señal killer |
| SUNAT | por RUC / documento / nombre | `dni`\|`ruc`\|nombre | Ficha del contribuyente → perfil del vendedor |
| RREE | carné de extranjería | nº carné | Vendedor extranjero |

### 5.5 Cobertura Perú — lo que NO tenemos (ser honestos en el pitch)

❌ **SUNARP** (cadena de propietarios, precios declarados, gravámenes, prendas, anotación de robo)
❌ **MTC** (revisión técnica)
❌ ATU, PIT/fotopapeletas, Infogas (GNV)
❌ SATs de provincia (Trujillo, Arequipa, Chiclayo, Cusco…)

**Decisión de producto:** NO prometemos SUNARP ni MTC. Construimos sobre lo que Croma sí
domina y lo declaramos abiertamente en el pitch. Reconocer el límite **suma** en
*production readiness*; inventarlo resta credibilidad y se cae en el Q&A.

> Alternativa evaluada y descartada para el MVP: usar `extract-json` sobre los portales
> públicos. SUNARP tiene captcha → no asumible en 1.5 días. Queda como roadmap.

### 5.6 Endpoints asíncronos

**SBS y SUTRAN son async jobs.** Por defecto esperan inline y devuelven `{ data }`, pero
soportan polling o `callback_url`.

**Decisión:** usar respuestas parciales para que la UI muestre tarjetas apareciendo una por
una. En video de demo se ve infinitamente mejor que un spinner de 20 segundos.

---

## 6. Recursos

- Docs: https://docs.usecroma.com/
- Índice completo para agentes: https://docs.usecroma.com/llms.txt
- Plataforma / API key: https://platform.usecroma.com/
- App de ejemplo MCP open source: https://chat.usecroma.com/
- Bases de la hackathon: https://usecroma.com/es/changelog/hackathon-govtech
