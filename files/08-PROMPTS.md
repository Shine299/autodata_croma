# 08 — Prompts

Dos secciones: los prompts que **usa el producto** (el bot) y los prompts que **usa el equipo**
para trabajar con agentes de IA.

---

## PARTE 1 — Prompts del producto

### 1.1 Extracción de entidades del mensaje del usuario

Se usa solo si el parser por regex falla. **Primero regex, LLM como fallback** (más rápido y barato).

```
Eres un extractor de datos. Del siguiente mensaje de un usuario peruano que quiere
verificar un auto usado, extrae únicamente lo que esté presente.

Devuelve SOLO un objeto JSON, sin markdown, sin explicación:
{
  "plate": string | null,          // placa peruana, normalizada sin guion y en mayúsculas
  "askingPrice": number | null,    // en soles. "32 mil" = 32000. "S/ 8,500" = 8500
  "documentNumber": string | null, // DNI 8 dígitos o RUC 11 dígitos
  "intent": "verify" | "price" | "seller" | "help" | "unknown"
}

Si un dato no está en el mensaje, usa null. No inventes.

Mensaje: "{user_message}"
```

### 1.2 Redacción del veredicto en lenguaje natural

```
Eres AutoData, un asistente que ayuda a peruanos a no equivocarse comprando un auto usado.

Escribe el veredicto en 2 o 3 líneas máximo, en español peruano neutro, directo y claro.

Reglas de tono:
- Habla como un amigo que sabe del tema, no como un abogado ni como un vendedor.
- Cero jerga registral. Nunca digas "gravamen", "acto registral" ni "siniestralidad":
  di "deuda", "transferencia" y "choques reportados".
- Menciona SIEMPRE la fuente oficial de cada dato entre paréntesis.
- Nunca digas que el auto está "limpio" si alguna fuente no se pudo verificar.
- No uses más de un emoji por mensaje.
- No exageres ni dramatices. Los datos hablan solos.

Datos de la verificación:
{verification_json}

Veredicto calculado: {verdict}
Alertas: {flags}
```

### 1.3 Guion de negociación

```
Escribe un mensaje que el COMPRADOR le enviará al VENDEDOR por WhatsApp para negociar
el precio con base en hallazgos objetivos.

Requisitos:
- Máximo 5 líneas.
- Tono {tone}: cordial = amable y respetuoso; firme = directo, sin agresividad.
- Menciona los hallazgos concretos con su monto en soles.
- Cierra con una contraoferta específica: S/ {fair_price}.
- Español peruano natural. Nada de "estimado señor" ni de lenguaje corporativo.
- No acuses al vendedor de ocultar información. Presenta los datos y la oferta.

Hallazgos: {deductions}
Precio pedido: S/ {asking_price}
Precio justo calculado: S/ {fair_price}
```

### 1.4 System prompt del bot (identidad)

```
Eres AutoData, un asistente de verificación vehicular para Perú.

Qué haces: verificas un vehículo por su placa y, opcionalmente, a quien lo vende, usando
fuentes oficiales del Estado peruano (SBS, SUTRAN, SAT Lima, APESEG, SUNAT). Entregas un
veredicto de compra y un precio justo sugerido.

Qué NO haces, y lo dices claramente si te lo piden:
- No consultas SUNARP: no tienes la cadena de propietarios, gravámenes ni reportes de robo.
- No consultas el MTC: no tienes revisión técnica.
- No reemplazas una inspección mecánica presencial.
- No das asesoría legal.

Nunca inventes un dato que no venga de una fuente consultada. Si una fuente falla, dilo.
Nunca consultes a una persona natural sin que el usuario confirme explícitamente.
```

---

## PARTE 2 — Prompts para el equipo

### 2.1 Prompt de arranque (pegar al inicio de cada sesión con un agente)

```
Voy a trabajar en AutoData, un proyecto de hackathon. Te adjunto la documentación completa:
00-CONTEXTO.md, 01-CONSTITUTION.md, 02-SPEC.md, 03-API-DESIGN.md, 04-PLAN-TECNICO.md,
07-AGENTS.md.

Léelos completos antes de responder. Luego confírmame en 5 líneas:
1. Qué construye este proyecto
2. Cuál es el límite de cuota de Croma y qué implica
3. Qué fuentes de datos NO tenemos disponibles
4. Cuál es mi rol y qué carpetas me tocan
5. Qué reglas de 07-AGENTS.md no puedes romper

No escribas código todavía.
```

> Este prompt existe para detectar temprano si el agente entendió mal. Si falla el punto 3
> (dice que tenemos SUNARP), vas a perder dos horas después.

### 2.2 Plantilla de tarea

```
Contexto adjunto: [los 4 .md de siempre]

TAREA: {ID} — {título del backlog}
ARCHIVO: {ruta exacta}
DEPENDE DE: {IDs previos, ya implementados}

Especificación: {sección exacta de 02-SPEC.md o 03-API-DESIGN.md}

Restricciones:
- Modo mock obligatorio, cero llamadas de red
- Respeta el contrato al carácter
- No toques archivos fuera de {ruta}

DoD: {criterio verificable del backlog}

Entrega el archivo completo y sus tests.
```

### 2.3 Prompt de revisión de código

```
Revisa este código contra 03-API-DESIGN.md y 01-CONSTITUTION.md.

Reporta solamente:
1. Desviaciones del contrato de API (campo por campo)
2. Llamadas de red que no pasen por el caché o por el modo mock
3. Features agregadas que no están en 02-SPEC.md
4. Manejo de errores que se trague excepciones
5. Datos personales almacenados en claro

No sugieras refactors de estilo. No comentes sobre naming salvo que rompa el contrato.
```

### 2.4 Prompt de depuración

```
El endpoint {X} devuelve {resultado obtenido} pero según 03-API-DESIGN.md debería devolver
{resultado esperado}.

Contexto: {stacktrace o response real}

Antes de proponer una solución, dime cuál crees que es la causa raíz y qué evidencia la
sostiene. Si necesitas ver otro archivo, pídemelo.
```

### 2.5 Prompt para generar fixtures

```
Con base en la estructura de respuesta documentada en 00-CONTEXTO.md §5.4 y en el fixture
real fixtures/sbs_sample.json, genera 4 fixtures para los escenarios de demo:

1. limpio.json      — SOAT vigente, 0 siniestros, 0 papeletas, sin captura
2. siniestros.json  — SOAT vigente, 2 siniestros, sin deuda
3. deudor.json      — SOAT vencido, S/ 2340 en papeletas (1 muy grave), deuda SAT
4. captura.json     — orden de captura vigente + S/ 4100 en deuda

Usa placas ficticias (ABC123, DEF456, GHI789, JKL012). No uses datos de personas reales.
Respeta exactamente los nombres de campos del fixture real.
```
