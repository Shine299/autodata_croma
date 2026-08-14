# 10 — Librería de Prompts de Planificación

Prompts listos para copiar y pegar en la ceremonia de planificación. Se ejecutan **al inicio de
cada sprint y en el cierre de cada tarde**, y producen el plan de lo que avanza cada persona.

**Cómo se usa:** el facilitador (P1 para planning, P5 para review y retro) pega el prompt en su
agente con los `.md` de contexto adjuntos, comparte el output en el canal del equipo, y el
equipo lo valida en 5 minutos. El agente redacta el plan; **el equipo lo aprueba**.

**Contexto que se adjunta siempre:** `00-CONTEXTO.md`, `01-CONSTITUTION.md`, `02-SPEC.md`,
`03-API-DESIGN.md`, `05-TASKS.md`, `06-PLAN-ACCION.md`.

---

## Índice

| Prompt | Cuándo se ejecuta | Quién lo corre |
|---|---|---|
| [P-01 Planificación de sprint](#p-01) | Al abrir cada sprint | P1 |
| [P-02 Plan individual](#p-02) | Al abrir cada sprint, uno por persona | Cada quien |
| [P-03 Cierre de tarde](#p-03) | **Cada tarde, sin falta** | P1 |
| [P-04 Daily](#p-04) | Cada 4 h | P1 |
| [P-05 Puerta de testing](#p-05) | Al cerrar cada sprint | P5 |
| [P-06 Retrospectiva](#p-06) | Tras cada puerta | P5 |
| [P-07 Triaje de bloqueos](#p-07) | Cuando alguien lleva 20 min trabado | P1 |
| [P-08 Decisión de recorte](#p-08) | Puerta 2, o cuando se va tarde | P5 |
| [P-09 Auditoría de cuota](#p-09) | Antes de cada sprint y antes de la demo | P1 |
| [P-10 Reasignación por desbalance](#p-10) | Si alguien va sobrecargado o libre | P1 |
| [P-11 Handoff entre sprints](#p-11) | Al cambiar de foco de área | Cada quien |
| [P-12 Simulacro de jurado](#p-12) | Puerta 3 | P5 |

---

<a name="p-01"></a>
## P-01 · Planificación de sprint

> Se corre al abrir Sprint 1, 2 y 3. Produce el sprint backlog validado.

```
Actúa como Scrum Master del proyecto AutoData. Contexto adjunto.

ESTADO ACTUAL:
- Sprint que arranca: {1 | 2 | 3}
- Horas restantes hasta la entrega: {N}
- Tareas cerradas hasta ahora (IDs de 05-TASKS.md): {lista}
- Tareas que quedaron abiertas del sprint anterior: {lista}
- Resultado de la puerta de testing anterior: {aprobada | fallos: ...}
- Ausencias o disponibilidad reducida: {ninguna | P{n} solo {x} horas}

Genera el sprint backlog:

1. SPRINT GOAL en una sola frase, en términos de qué podrá demostrarse al final.
2. Tabla por participante (P1..P5) con: área del sprint, tareas asignadas con su ID,
   estimación en horas, y el incremento demostrable que produce.
3. Ruta crítica: qué tareas bloquean a otras personas. Márcalas para que se hagan primero.
4. Las 3 tareas que, si no se cierran, hacen fracasar el sprint.
5. Qué se corta primero si vamos tarde, en orden.

Restricciones:
- Respeta la regla de un dueño por carpeta (06-PLAN-ACCION.md §7).
- Máximo 2 tareas en curso por persona a la vez.
- No asignes a nadie más horas de las que quedan en el sprint.
- Ninguna tarea que consuma cuota real de Croma salvo E-03, y esa es solo de P1.
- No inventes tareas nuevas: usa los IDs de 05-TASKS.md. Si detectas un hueco real,
  proponlo al final como "TAREA FALTANTE" y espera aprobación.

Formato: markdown, tablas, sin preámbulo.
```

---

<a name="p-02"></a>
## P-02 · Plan individual del sprint

> Cada participante lo corre para sí mismo tras el P-01.

```
Contexto adjunto. Soy {P1 Tech Lead | P2 Backend Core | P3 Bot | P4 Data/Infra | P5 Producto}.

Sprint {N}. Mis tareas asignadas: {IDs}
Horas disponibles: {N}

Arma mi plan de trabajo:

1. Orden de ejecución de mis tareas, justificando por dependencias (no por preferencia).
2. Para cada tarea: archivos exactos que voy a tocar y el DoD verificable.
3. Qué necesito de otra persona antes de poder arrancar, y en qué momento pedírselo.
4. Qué entrego yo que otro está esperando, y cuándo debería estar listo.
5. Para cada tarea, si conviene delegarla a un agente de IA o hacerla a mano
   (criterio: 07-AGENTS.md §"Qué SÍ / NO delegar").
6. Mi punto de control a mitad de sprint: qué debería estar listo para saber que voy bien.

Sé concreto con archivos y rutas. Nada de "implementar la lógica".
```

---

<a name="p-03"></a>
## P-03 · Cierre de tarde ⭐

> **El prompt central de la rutina.** Se corre cada tarde antes de cortar. Produce el plan
> del siguiente tramo por fase, sprint y participante.

```
Actúa como Scrum Master de AutoData. Contexto adjunto. Es el cierre de la tarde.

REPORTE DE HOY (uno por persona):
- P1: cerró {...} | en curso {...} | bloqueado por {...}
- P2: cerró {...} | en curso {...} | bloqueado por {...}
- P3: cerró {...} | en curso {...} | bloqueado por {...}
- P4: cerró {...} | en curso {...} | bloqueado por {...}
- P5: cerró {...} | en curso {...} | bloqueado por {...}

Horas restantes hasta la entrega: {N}
Sprint en curso: {N}
Cuota de Croma consumida hoy: {N}/100
Incidentes del día: {ninguno | ...}

Produce:

1. SEMÁFORO DEL PROYECTO — verde / ámbar / rojo, con la razón en una línea.
   Compara el avance real contra el mapa de sprints de 06-PLAN-ACCION.md §2.

2. ESTADO POR FASE
   Tabla: Sprint 1 / Sprint 2 / Sprint 3, con % completado y qué falta en cada uno.

3. PLAN DEL SIGUIENTE TRAMO, POR PARTICIPANTE
   Para cada P1..P5: las 2 o 3 tareas concretas del próximo tramo, con IDs, en orden,
   y el resultado esperado al terminar.

4. RUTA CRÍTICA DE MAÑANA
   Qué tarea bloquea a más gente. Esa se ataca primero, sin discusión.

5. RIESGOS ACTIVOS
   Contrastados con 04-PLAN-TECNICO.md §9. Cuáles se materializaron y cuáles siguen latentes.

6. DECISIONES QUE EL EQUIPO DEBE TOMAR ANTES DE SEGUIR
   Máximo 3. Formuladas como pregunta cerrada, con la opción que recomiendas.

7. ¿HAY QUE RECORTAR ALCANCE?
   Sí o no. Si es sí, qué exactamente y por qué, en orden de corte de 06-PLAN-ACCION.md §6.

Sé brutalmente honesto con el semáforo. Un ámbar declarado a tiempo salva el proyecto;
un verde optimista lo hunde. Si los números no dan, dilo.
```

---

<a name="p-04"></a>
## P-04 · Daily (cada 4 horas)

```
Contexto adjunto. Daily de AutoData, {N} horas para la entrega.

Reportes:
- P1: {hice} / {haré} / {bloqueo}
- P2: {hice} / {haré} / {bloqueo}
- P3: {hice} / {haré} / {bloqueo}
- P4: {hice} / {haré} / {bloqueo}
- P5: {hice} / {haré} / {bloqueo}

En máximo 12 líneas:
1. ¿Vamos a llegar al sprint goal? Sí / No / En riesgo, con la razón.
2. Bloqueos que se resuelven entre nosotros ahora mismo: quién ayuda a quién.
3. Bloqueos externos que hay que rodear: cómo.
4. Una sola acción correctiva para las próximas 4 horas.

Nada de resúmenes largos. El daily dura 10 minutos.
```

---

<a name="p-05"></a>
## P-05 · Puerta de testing (Sprint Review)

```
Contexto adjunto. Cierre del Sprint {N} de AutoData.

Lo que el equipo dice haber terminado: {lista de IDs}

Genera el protocolo de testing cruzado de la Puerta {N}:

1. Toma la tabla de la Puerta {N} en 06-PLAN-ACCION.md y expándela: por cada prueba,
   los pasos exactos para ejecutarla y el resultado esperado literal.
2. Agrega las pruebas que falten según lo que realmente se construyó en este sprint.
3. Asigna cada prueba a alguien que NO haya escrito ese código.
4. Por cada criterio de aceptación de las historias de 02-SPEC.md tocadas en este sprint,
   indica cómo se verifica y quién lo verifica.
5. Define el criterio de aprobación de la puerta: cuántas pruebas deben pasar para abrir
   el siguiente sprint, y cuáles son bloqueantes absolutas.

Al final, una checklist marcable de una línea por prueba.
No asumas que algo funciona porque está en el backlog como hecho.
```

---

<a name="p-06"></a>
## P-06 · Retrospectiva (10 minutos)

```
Contexto adjunto. Retro del Sprint {N}.

Lo que pasó:
- Planeado: {IDs} | Cerrado: {IDs} | Arrastrado: {IDs}
- Resultado de la puerta: {aprobada | fallos}
- Fricciones que reportó el equipo: {...}

En máximo 10 líneas:
1. Una cosa que funcionó y hay que mantener.
2. Una cosa que nos costó tiempo y por qué (causa raíz, no síntoma).
3. UN solo cambio concreto para el siguiente sprint. Uno, no cinco.
4. Si el problema vino del trabajo con agentes de IA, qué regla de 07-AGENTS.md
   hay que ajustar o reforzar.

No hagas una lista de buenas intenciones. Un cambio, accionable, con dueño.
```

---

<a name="p-07"></a>
## P-07 · Triaje de bloqueo

> Se corre cuando alguien lleva 20 minutos trabado (regla del Artículo VIII).

```
Contexto adjunto. Bloqueo activo.

Persona: {P{n}} · Tarea: {ID} · Tiempo trabado: {N} min
Síntoma: {qué pasa}
Ya intenté: {qué probó}
Evidencia: {error, log, response}

Responde:
1. Causa raíz más probable y qué evidencia la sostiene.
2. Verificación de 2 minutos para confirmarla o descartarla.
3. Solución si se confirma.
4. Rodeo temporal si la solución toma más de 30 min: cómo desbloquear al resto del equipo
   mientras tanto (mock, stub, dato quemado — indicando cómo revertirlo después).
5. ¿Esta tarea es de la ruta crítica? Si no lo es, ¿conviene posponerla?

Prioriza desbloquear al equipo por encima de resolver bien el problema.
```

---

<a name="p-08"></a>
## P-08 · Decisión de recorte de alcance

```
Contexto adjunto. Evaluación de alcance de AutoData.

Horas restantes: {N}
Cerrado: {IDs}
Pendiente: {IDs} con estimación {horas}
Velocidad real observada en los sprints anteriores: {tareas por hora}

Analiza:
1. Con la velocidad real (no la optimista), ¿qué alcanza a terminarse? Muestra la cuenta.
2. Contrasta contra el alcance mínimo viable de 06-PLAN-ACCION.md §6: ¿está asegurado?
3. Qué se corta, en orden, y qué impacto tiene cada corte en los tres criterios del jurado
   (originalidad / uso de Croma / production readiness).
4. Qué es imposible cortar sin perder el sentido del producto.
5. Plan revisado por participante con el alcance recortado.

Sé conservador con las estimaciones. Es preferible entregar menos y que funcione,
que entregar más y que se caiga en la demo.
```

---

<a name="p-09"></a>
## P-09 · Auditoría de cuota de Croma

> El Artículo III es el riesgo número uno del proyecto. Este prompt se corre antes de cada
> sprint y obligatoriamente antes de la demo.

```
Contexto adjunto, especialmente 00-CONTEXTO.md §5 y 01-CONSTITUTION.md Artículo III.

Estado de cuota:
- Consumido hoy: {N}/100
- Registro de llamadas (docs/quota-log.md): {resumen}
- Tasa de cache hit: {N}%
- Escenarios de demo ya sembrados: {cuáles}
- Horas hasta la demo: {N}

Analiza:
1. ¿Alcanza la cuota para lo que falta? Muestra el cálculo: qué tareas pendientes
   consumen requests y cuántos cada una.
2. ¿Hay algún consumo que no debería estar ocurriendo? (tests, desarrollo sin mock,
   llamadas repetidas sin caché). Señálalo.
3. ¿Cuántos requests hay que reservar para la consulta en vivo ante el jurado, y están
   protegidos?
4. Si la cuota está en riesgo, plan de contingencia concreto.
5. Recordatorio de qué está prohibido hacer con la cuota en las próximas horas.

Recuerda: el límite es por organización, no por key. Los cache hits del lado de Croma
igual consumen. Un batch cuenta como un request por ítem.
```

---

<a name="p-10"></a>
## P-10 · Reasignación por desbalance

```
Contexto adjunto.

Situación: {P{n} va sobrecargado / P{n} terminó y está libre / P{n} se ausenta {N} horas}
Sprint en curso: {N} · Horas restantes: {N}

Propone una reasignación:
1. Qué tareas se mueven, de quién a quién, y por qué esa persona es la adecuada
   (considerando qué área viene trabajando desde el Sprint 1).
2. Qué contexto necesita recibir quien las asume: archivos, decisiones tomadas, gotchas.
3. Qué NO se debe mover porque requiere el contexto acumulado del dueño original.
4. Cómo evitar que la reasignación rompa la regla de un dueño por carpeta.
5. Plan actualizado por participante.

Mover una tarea cuesta tiempo de transferencia de contexto. Solo propón movimientos
donde el beneficio sea claramente mayor a ese costo.
```

---

<a name="p-11"></a>
## P-11 · Handoff entre sprints

> Cada persona lo corre al terminar un sprint, para dejar su área lista para el siguiente foco.

```
Contexto adjunto. Soy {P{n}}. Cierro el Sprint {N}.

Lo que construí: {archivos y tareas}
Lo que queda a medias: {...}

Genera mi documento de handoff:
1. Estado real de mi área en 5 líneas: qué funciona, qué no, qué está a medias.
2. Decisiones técnicas que tomé y que el resto necesita conocer.
3. Deuda técnica que dejé, con su nivel de riesgo para la demo.
4. Trampas: qué se rompe si alguien toca X sin saber Y.
5. Qué necesito del equipo en el próximo sprint para mi nueva área de foco.

Escríbelo para alguien que no vio mi código. Sin adornos.
```

---

<a name="p-12"></a>
## P-12 · Simulacro de jurado

```
Contexto adjunto, especialmente 09-DEMO-PITCH.md y 00-CONTEXTO.md §4 (competencia).

Actúa como jurado de la hackathon GOV-TECH de Croma. Eres exigente, técnico, y conoces
el mercado peruano de consulta vehicular.

Nuestro pitch: {pegar el guion o describir la demo}

Haz lo siguiente:
1. Califica del 1 al 10 cada criterio (originalidad / uso de Croma / impacto y production
   readiness), con la justificación de por qué no es un 10.
2. Hazme las 6 preguntas más incómodas que se te ocurran, incluyendo al menos una sobre
   los competidores existentes y una sobre las fuentes que NO cubrimos.
3. Señala la parte de la demo donde perdemos la atención del jurado.
4. Un cambio concreto al guion que suba la calificación más alta.

No seas amable. Prefiero que me destruyas ahora y no el jurado real.
```

---

## Rutina diaria recomendada

| Momento | Prompt | Duración |
|---|---|---|
| Inicio de sprint | P-01 + P-02 (cada uno) | 15 min |
| Cada 4 h | P-04 | 10 min |
| Al trabarse 20 min | P-07 | 5 min |
| **Cada tarde, al cortar** | **P-03** | **15 min** |
| Fin de sprint | P-05 → P-06 → P-11 | 60 + 10 + 10 min |
| Antes de cada sprint | P-09 | 5 min |
| Si se va tarde | P-08 | 10 min |
| Puerta 3 | P-12 | 20 min |

**Regla:** el output de cualquier prompt es una **propuesta**. El equipo lo valida en 5 minutos
antes de convertirlo en plan. El agente organiza; las personas deciden.
