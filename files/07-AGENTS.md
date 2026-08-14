# 07 — Trabajo Híbrido con Agentes de IA

> Este archivo tiene doble función: es la regla para el equipo **y** es el archivo que se le
> entrega al agente (Claude Code, Cursor, Copilot) como contexto permanente.
> Si tu herramienta soporta `AGENTS.md` o `CLAUDE.md` en la raíz, copia este contenido ahí.

---

## PARTE 1 — Instrucciones para el agente

### Contexto del proyecto

Estás trabajando en **AutoData**, un bot de Telegram que verifica vehículos usados en Perú
usando la API de Croma (datos de gobierno). Proyecto de hackathon, 5 desarrolladores,
deadline de 36 horas.

**Antes de escribir código, lee en este orden:**
`00-CONTEXTO.md` → `01-CONSTITUTION.md` → `02-SPEC.md` → `03-API-DESIGN.md` → `04-PLAN-TECNICO.md`

### Reglas que no puedes romper

1. **Nunca escribas código que llame a la API real de Croma en desarrollo o en tests.**
   La cuota es de 100 requests/día para todo el equipo. Usa siempre `CROMA_MODE=mock`
   leyendo de `fixtures/`.
2. **Respeta el contrato de `03-API-DESIGN.md` al carácter.** Nombres de campos, tipos,
   estructura de envelope. Si crees que un campo debería llamarse distinto, **dilo, no lo cambies**.
3. **No agregues features que no estén en `02-SPEC.md`.** Si detectas algo que falta,
   escríbelo como comentario `# PROPUESTA:` y sigue con lo pedido.
4. **No inventes fuentes de datos.** Croma Perú tiene exactamente 8 fuentes, listadas en
   `00-CONTEXTO.md §5.4`. **No existe SUNARP ni MTC en Croma.** Si tu código los menciona,
   está mal.
5. **Ninguna fuente caída puede tumbar la respuesta completa.** Siempre `SourceResult` con
   `status`, nunca una excepción que se propague al usuario.
6. **Nunca almacenes documentos de identidad en claro.** Solo hash + últimos 3 dígitos.
7. **JSON en camelCase, Python en snake_case.** Usa alias de Pydantic para el puente.
8. **Todo async.** `httpx.AsyncClient`, `asyncio.gather`. Nada de `requests` bloqueante.

### Formato de tus respuestas

- Entrega el archivo completo, no fragmentos con `# ... resto igual`.
- Si tocas más de 3 archivos, primero lista qué vas a cambiar y espera confirmación.
- Incluye los tests cuando la tarea lo pida.
- Si algo del spec es ambiguo, **pregunta antes de asumir**. Una suposición tuya cuesta más
  tiempo de depuración que una pregunta.

### Lo que NO debes hacer

- ❌ Refactorizar código que no te pidieron tocar.
- ❌ Cambiar la estructura de carpetas.
- ❌ Agregar dependencias nuevas sin justificarlas.
- ❌ Escribir manejo de errores genérico que se trague las excepciones silenciosamente.
- ❌ Generar datos de ejemplo que parezcan reales (placas y DNIs reales de personas).
  Usa placas ficticias tipo `ABC123`, `XYZ789`.

---

## PARTE 2 — Reglas para el equipo humano

### El ciclo SDD híbrido

```
   HUMANO                    AGENTE                    HUMANO
┌────────────┐          ┌──────────────┐          ┌────────────┐
│  Escribe   │  ──────▶ │   Genera     │ ──────▶  │  Revisa,   │
│  la tarea  │          │   código     │          │  prueba,   │
│  con DoD   │          │              │          │  mergea    │
└────────────┘          └──────────────┘          └────────────┘
     ▲                                                   │
     └───────────── si no cumple el DoD ─────────────────┘
```

**El agente propone. El humano decide.** Nadie mergea código que no leyó completo.

### Cómo pedirle una tarea a un agente

**❌ Mal:** *"hazme el endpoint de vehículos"*

**✅ Bien:**
```
Contexto adjunto: 01-CONSTITUTION.md, 02-SPEC.md, 03-API-DESIGN.md, 04-PLAN-TECNICO.md

Tarea C-01 del backlog.
Implementa POST /api/v1/vehicles/inspections en app/api/vehicles.py.

- Contrato exacto: sección "Recurso 1 — Vehículo" de 03-API-DESIGN.md
- Usa CromaClient de app/integrations/croma/client.py (ya existe, no lo modifiques)
- Llama las 6 fuentes con asyncio.gather, return_exceptions=True
- Una fuente caída → status "error" en sourcesSummary, no excepción
- Modo mock obligatorio
- Incluye tests en tests/test_vehicles.py con los 4 escenarios de fixtures/demo/

DoD: el response valida contra VehicleInspectionResponse y los 4 escenarios pasan.
```

### Los 4 pecados capitales del trabajo con agentes (y cómo evitarlos)

| Pecado | Síntoma | Antídoto |
|---|---|---|
| **Deriva de contexto** | Cada dev tiene un agente con una versión distinta del proyecto en la cabeza | Todos adjuntan los mismos 4 .md. Siempre. |
| **Alcance inflado** | El agente "de yapa" agregó autenticación JWT que nadie pidió | Artículo IX + revisar el diff completo antes de mergear |
| **Merge conflict masivo** | Dos agentes reescribieron el mismo archivo distinto | Un dueño por carpeta. PRs chicos y frecuentes. |
| **Confianza ciega** | Se mergea código que nadie leyó y a T-2h nada funciona | Regla: si no lo leíste, no lo mergeas. Sin excepción. |

### Qué SÍ delegar al agente

✅ Adapters y mappers (input y output bien definidos)
✅ Schemas Pydantic desde el contrato de API
✅ Parsers con casos de prueba (placas, montos, documentos)
✅ Tests unitarios
✅ Formateo de mensajes de Telegram
✅ DDL de SQL y migraciones
✅ Boilerplate: config, logging, manejo de errores

### Qué NO delegar

❌ Las reglas de scoring y el veredicto (es la lógica de negocio diferencial, la decide un humano)
❌ El copy que ve el usuario final (el tono peruano no lo saca bien un modelo, lo escribe P5)
❌ Decisiones de arquitectura y de alcance
❌ El guion del pitch
❌ Cualquier cosa que consuma cuota real de Croma

### Checklist antes de cada merge

- [ ] Leí el diff completo, línea por línea.
- [ ] Corre en modo mock sin tocar la red.
- [ ] Respeta el contrato de `03-API-DESIGN.md`.
- [ ] No agregó dependencias sin avisar.
- [ ] No agregó features fuera de la spec.
- [ ] No hay keys ni tokens en el código.
- [ ] Actualicé el estado de la tarea en `05-TASKS.md`.
