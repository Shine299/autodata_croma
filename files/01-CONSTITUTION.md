# 01 — Constitución del Proyecto

> **SDD paso 1.** Principios inmutables. Ningún humano ni agente los puede violar sin
> aprobación explícita del Tech Lead. Si un agente propone algo que rompe un artículo,
> se rechaza el output completo.

---

## Artículo I — La spec manda

Ninguna línea de código existe sin una historia en `02-SPEC.md` y una tarea en `05-TASKS.md`.
Si durante la implementación aparece una necesidad nueva:

1. Se para el código.
2. Se actualiza la spec (2 minutos).
3. Se recién implementa.

**Prohibido:** "lo agregué de paso porque el agente lo sugirió".

## Artículo II — El contrato de API es sagrado

`03-API-DESIGN.md` define request y response de cada endpoint. Backend y bot se desarrollan
**en paralelo contra ese contrato**, no uno esperando al otro.

- El que cambia un contrato avisa en el canal del equipo **antes** de mergear.
- Nombres de campos en **camelCase** en JSON, **snake_case** en Python/BD.
- Nunca romper un campo existente durante la hackathon: solo agregar.

## Artículo III — Cuota de Croma antes que cualquier feature

La cuota es **100 requests/día para todo el equipo**. Por lo tanto:

- ❌ Prohibido llamar a Croma desde tests automáticos.
- ❌ Prohibido llamar a Croma en desarrollo sin caché activo.
- ✅ Todo desarrollo usa el **modo mock** (`CROMA_MODE=mock`) contra fixtures JSON.
- ✅ Solo el Tech Lead autoriza llamadas reales, y se anotan en `docs/quota-log.md`.
- ✅ Las 4 placas de la demo se consultan **una sola vez** y se congelan como fixtures.

**Violar este artículo = quedarse sin demo.** Es la falla más probable del proyecto.

## Artículo IV — Entregable funcional sobre entregable bonito

Prioridad estricta cuando falte tiempo:

1. El bot responde en Telegram con datos reales de Croma.
2. El veredicto y el precio se calculan bien.
3. El manejo de errores no revienta en vivo.
4. Recién ahí: UI web, PDF, animaciones, landing.

## Artículo V — Honestidad de datos

- Nunca inventar una fuente que no consultamos.
- Nunca mostrar un dato sin decir de qué entidad viene y con qué fecha.
- Si una fuente falla, se dice **"no pudimos verificar X"**, jamás se asume "está limpio".
- El disclaimer legal va en toda salida: *esto no reemplaza una inspección mecánica ni la
  publicidad registral de SUNARP*.

## Artículo VI — Ética y datos personales

Consultamos datos públicos, pero estamos perfilando personas. Por lo tanto:

- Solo mostramos señales **relevantes a la transacción** (¿es dueño?, ¿tiene deuda vehicular?,
  ¿es revendedor formal?). Nada más.
- No almacenamos DNIs en claro: se guarda **hash** + los últimos 3 dígitos para display.
- No guardamos historial de consultas de terceros más allá del TTL de caché.
- El bot pide confirmación explícita antes de consultar a una persona natural.
- Este punto **se menciona en el pitch**. Suma en production readiness.

## Artículo VII — Trabajo híbrido con agentes

- El agente **propone**, el humano **decide y mergea**. Nadie mergea código que no leyó.
- Todo prompt significativo se guarda en `08-PROMPTS.md` para que sea reproducible.
- Cada agente recibe: `01-CONSTITUTION.md` + `02-SPEC.md` + `03-API-DESIGN.md` + su tarea.
  Nunca solo la tarea suelta.
- Ver reglas completas en `07-AGENTS.md`.

## Artículo VIII — Ritmo y bloqueos

- Standups de 5 minutos cada 4 horas (ver `06-PLAN-ACCION.md`).
- **Regla de los 20 minutos:** si estás bloqueado 20 min, lo dices en el canal. No se sufre solo.
- Feature freeze a **T-4h**. Desde ahí solo bugfixes, grabación y pitch.

## Artículo IX — Alcance congelado

El MVP es exactamente lo que dice `02-SPEC.md`. Todo lo demás va a la sección
"Roadmap / fuera de alcance". Sirve para el pitch como visión, no como código.

**Fuera de alcance explícito:** pagos, login de usuarios, app móvil nativa, SUNARP, MTC,
scraping con captcha, panel de administración, multi-idioma.
