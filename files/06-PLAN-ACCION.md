# 06 — Plan de Acción Scrum (5 personas · 3 sprints · ~36 h)

Entrega: **16 de agosto, 6:30 p. m.** Tiempos en formato relativo (`T-XX h`) para que el plan
funcione sin importar la hora de arranque.

---

## 1. Marco Scrum comprimido

Scrum de hackathon: mismas ceremonias, escala de horas en vez de semanas.

| Elemento Scrum | Equivalente aquí |
|---|---|
| Product Owner | **P5 (Producto)** — dueño del backlog y del criterio de "listo" |
| Scrum Master | **P1 (Tech Lead)** — remueve bloqueos, protege el alcance, custodia la cuota |
| Development Team | Los 5 |
| Product Backlog | `05-TASKS.md` |
| Sprint Backlog | Sección 3 de este documento |
| Definition of Done | `05-TASKS.md` §DoD global |
| Incremento | Al final de cada sprint hay algo **demostrable**, no solo código |
| Daily | Standup de 10 min cada 4 h |
| Sprint Review | **Puerta de testing** (§4) — obligatoria, cruzada, con checklist |
| Retro | 10 min al cierre de cada puerta. Una sola pregunta: ¿qué cambiamos para el siguiente? |

### Las 3 puertas (regla central)

> **Ningún sprint arranca hasta que la puerta de testing del anterior esté cerrada en verde.**

Si la puerta falla, el sprint siguiente arranca igual **pero con la corrección como primera
tarea del responsable**. Nunca se acumula deuda silenciosa: la puerta la cierra P1 en voz alta.

---

## 2. Mapa de sprints

| Sprint | Ventana | Duración | Objetivo (Sprint Goal) | Puerta |
|---|---|---|---|---|
| **Sprint 0** | T-36 → T-34 | 2 h | Alineamiento y congelado del contrato | — |
| **Sprint 1** | T-34 → T-26 | 8 h | **Los datos entran.** Croma responde y se cachea | 🚦 **Puerta 1** T-26 → T-25 |
| 🌙 Descanso | T-25 → T-18 | 7 h | Dormir | — |
| **Sprint 2** | T-18 → T-10 | 8 h | **El producto decide.** Veredicto, precio y bot completo | 🚦 **Puerta 2** T-10 → T-9 |
| **Sprint 3** | T-9 → T-3 | 6 h | **Está listo para usarse.** Endurecido, desplegado, demostrable | 🚦 **Puerta 3** T-3 → T-2 |
| Entrega | T-2 → T-0 | 2 h | Video, repo y formulario | — |

Cada participante tiene **un área asignada por sprint**. El área cambia de foco, la persona no
cambia de dominio: siempre profundiza sobre lo mismo.

---

## 3. Sprint Backlogs por participante

### 🔵 Sprint 0 — Alineamiento (T-36 → T-34) · TODOS JUNTOS

No se escribe código. Se lee y se acuerda.

| Min | Actividad | Facilita |
|---|---|---|
| 0-40 | Lectura individual de `00`, `01`, `02`, `03` | — |
| 40-70 | Ronda de objeciones al contrato de API → **se congela** | P1 |
| 70-80 | Confirmación de roles y canal de comunicación | P5 |
| 80-100 | P1 saca la API key y hace **1** llamada real → primer fixture | P1 |
| 100-120 | Prompt base para agentes validado por los 5 (`07-AGENTS.md`) | P5 |

**Incremento:** contrato congelado + 1 fixture real + los 5 alineados.

---

### 🟢 Sprint 1 — "Los datos entran" (T-34 → T-26) · 8 h

**Sprint Goal:** dada una placa, el sistema trae datos reales de Croma, los cachea y los
devuelve en el formato del contrato. Sin veredicto todavía. Sin bot todavía.

| | Área del sprint | Tareas | Incremento demostrable |
|---|---|---|---|
| **P1** | Infraestructura de Croma | A-01, A-02, A-05, A-06, B-01, B-02, B-05 | `CromaClient` funciona en mock y en live, con backoff |
| **P2** | Adapters de vehículo | B-06, B-07, B-08, B-09, B-10, B-11, C-02 | Las 6 fuentes mapeadas a los schemas del contrato |
| **P3** | Base conversacional | A-04, D-01, D-03 | Bot vivo, parser extrae placa/precio/DNI de texto libre |
| **P4** | Persistencia y cuota | A-03, B-03, B-04, C-11 | Caché funcionando + `/api/v1/quota` con datos reales |
| **P5** | Producto y contenido | A-07, E-02, plantillas de copy | Landing + todos los textos que verá el usuario |

**Daily a mitad de sprint (T-30):** ¿el contrato aguantó el contacto con los datos reales?

---

### 🚦 PUERTA 1 — Testing de integración de datos (T-26 → T-25) · 1 h

**Testing cruzado: nadie prueba lo suyo.**

| Prueba | La ejecuta | Criterio de aprobación |
|---|---|---|
| Las 6 fuentes responden en modo mock | P3 | 6/6 devuelven `SourceResult` válido |
| Segunda consulta a la misma placa no toca la red | P2 | El log muestra `from_cache: true` |
| Fuente caída no tumba la respuesta | P4 | Se apaga una fuente a propósito → status `error`, no excepción |
| Los schemas calzan con `03-API-DESIGN.md` | P1 | Revisión campo por campo, sin excepciones |
| El parser acierta en 15 frases distintas | P5 | ≥13/15 correctas |
| `/api/v1/quota` refleja el consumo real | P1 | El número coincide con `docs/quota-log.md` |

**Retro (10 min):** ¿qué nos frenó? ¿qué cambiamos para el Sprint 2?

**Si la puerta falla:** la corrección es la tarea #1 del responsable en el Sprint 2. Se anota.

---

### 🌙 Descanso obligatorio (T-25 → T-18) · 7 h

Dormir. Escalonado si quieren guardia: P1 y P3 primero, P2 y P4 después.
Un equipo sin dormir a T-4 h comete el error que le cuesta la demo.

---

### 🟡 Sprint 2 — "El producto decide" (T-18 → T-10) · 8 h

**Sprint Goal:** el sistema emite un veredicto correcto, calcula un precio justo, y el usuario
puede completar todo el flujo desde Telegram.

| | Área del sprint | Tareas | Incremento demostrable |
|---|---|---|---|
| **P1** | Orquestación y resiliencia | B-14, C-09, C-10 | 6 fuentes en paralelo + jobs async + envelope de errores |
| **P2** | Motor de decisión | **C-04 scoring**, C-05, C-06 | Los 4 escenarios devuelven el veredicto esperado |
| **P3** | Flujo conversacional completo | D-02, D-04, D-05, D-06, D-07 | Consulta end-to-end desde el celular, con progreso |
| **P4** | Verificación del vendedor | B-12, B-13, C-03, C-08 | SUNAT + SAT por DNI + bandera `SELLER_IS_DEALER` |
| **P5** | Lenguaje de salida | C-07, E-01 | Guion de negociación + página `/r/{id}` responsive |

**Daily a mitad de sprint (T-14):** ¿el alcance mínimo viable (§6) está asegurado? Cortar sin culpa.

---

### 🚦 PUERTA 2 — Testing funcional end-to-end (T-10 → T-9) · 1 h

| Prueba | La ejecuta | Criterio de aprobación |
|---|---|---|
| Los 4 escenarios dan el veredicto correcto | P3 | 4/4 exactos según HU-03 |
| Orden de captura fuerza `STOP` siempre | P5 | Aunque todo lo demás esté limpio |
| 2 fuentes caídas → veredicto tope `CAUTION` | P1 | Nunca `GO` a ciegas |
| Las deducciones del precio cuadran al centavo | P4 | Contra el fixture, a mano |
| Flujo completo desde el celular | P2 | Sin tocar el código, como usuario |
| El bot no consulta a una persona sin confirmar | P1 | Artículo VI verificado |
| Ningún mensaje muestra jerga registral | P5 | Lectura completa de todos los textos |

**Retro (10 min).** **Decisión de alcance:** con lo que queda, ¿qué se corta? Se decide aquí,
no a T-4 h con pánico.

---

### 🟠 Sprint 3 — "Listo para usarse" (T-9 → T-3) · 6 h

**Sprint Goal:** que un desconocido pueda usarlo sin romperlo, y que el jurado lo vea funcionar.

| | Área del sprint | Tareas | Incremento demostrable |
|---|---|---|---|
| **P1** | Datos de demo y cuota | **E-03 sembrado en live**, E-07 | 5 escenarios congelados + repo público limpio |
| **P2** | Casos borde y robustez | D-10 (con P3), bugfixes de la Puerta 2 | Los 7 casos borde de la spec §6 controlados |
| **P3** | UX de error y pulido | D-08, D-09, mensajes de error | Ningún camino termina en un mensaje feo |
| **P4** | Deploy y observabilidad | E-04, logs, health | URL pública estable + logs legibles |
| **P5** | Pitch | E-05, E-08, ensayo ×2 | Guion cronometrado en 3:00 |

> ⚠️ **E-03 es el momento de mayor riesgo del proyecto.** Es cuando se gasta cuota real.
> Solo P1 ejecuta, anota cada llamada y congela los fixtures de inmediato.

**T-4 h: FEATURE FREEZE.** Desde aquí solo bugfixes. Nada nuevo entra.

---

### 🚦 PUERTA 3 — Testing de demo (T-3 → T-2) · 1 h

| Prueba | La ejecuta | Criterio de aprobación |
|---|---|---|
| Ensayo completo cronometrado | Todos | ≤ 3:00 minutos |
| Las 4 placas responden desde caché | P5 | < 3 s cada una |
| 1 consulta en vivo con cuota reservada | P1 | Funciona y queda cuota para el jurado |
| El bot aguanta 30 min sin caerse | P4 | Sin reinicios |
| Cero stacktraces en cualquier flujo | P2 | Recorrido completo de caminos felices y de error |
| Repo sin secretos en el historial | P1 | `git log -p \| grep -i key` limpio |
| Los 5 saben responder las preguntas del jurado | P5 | Simulacro de Q&A con `09-DEMO-PITCH.md §3` |

---

### 🏁 Entrega (T-2 → T-0)

| Tiempo | Qué | Dueño |
|---|---|---|
| T-2h → T-1h | Grabar video de respaldo (E-06) | P5 + P3 |
| T-1h → T-40min | README público, limpieza final del repo | P1 |
| T-40min → T-30min | Revisión final del formulario | P5 |
| **T-30min** | **ENVIAR** (E-09) | P5 |

No se envía a las 6:29. Se envía a las 6:00.

---

## 4. Ceremonias y ritmo

| Ceremonia | Cuándo | Duración | Facilita |
|---|---|---|---|
| Sprint Planning | Inicio de cada sprint | 15 min | P1 |
| Daily | Cada 4 h | 10 min | P1 |
| Puerta de testing (Review) | Fin de cada sprint | 60 min | P5 |
| Retro | Al cerrar cada puerta | 10 min | P5 |

**Formato del daily — tres preguntas, nada más:**
1. ¿Qué cerré desde el último daily?
2. ¿Qué cierro antes del siguiente?
3. ¿Qué me bloquea?

**Regla de los 20 minutos:** bloqueado 20 min → lo dices en el canal. No se sufre en silencio.

---

## 5. Tablero (columnas del board)

```
BACKLOG  │  SPRINT ACTUAL  │  EN CURSO  │  EN REVISIÓN  │  HECHO  │  BLOQUEADO
```

- Máximo **2 tarjetas en curso por persona**. Es un límite duro, no una sugerencia.
- Una tarjeta pasa a HECHO solo cuando alguien **distinto al autor** la probó.
- BLOQUEADO se revisa en cada daily, sin excepción.

---

## 6. Alcance mínimo viable (red de seguridad)

Si en la Puerta 2 el equipo va atrasado, **esto es lo único innegociable**:

1. Bot de Telegram que recibe una placa.
2. Llamada real a **3 fuentes** de Croma: SBS (siniestros), SUTRAN (papeletas), SAT capturas.
3. Veredicto GO / CAUTION / STOP.
4. Precio justo calculado.

Eso solo ya cumple los tres criterios del jurado.

**Orden de corte si falta tiempo:**
página web del reporte → verificación del vendedor → mensajes progresivos → jobs asíncronos.

---

## 7. Regla de un dueño por carpeta

| Persona | Carpetas propias |
|---|---|
| P1 | `app/integrations/`, `app/core/`, `app/config.py`, `fixtures/` |
| P2 | `app/services/`, `app/api/vehicles.py`, `app/api/verifications.py` |
| P3 | `app/bot/` |
| P4 | `app/repositories/`, `app/api/sellers.py`, `app/api/health.py`, migraciones |
| P5 | `app/web/`, `docs/`, textos y copy |

`app/schemas/` lo toca **solo P1**, y solo para agregar campos. Así 5 personas y sus agentes
de IA no se pisan en los merges.
