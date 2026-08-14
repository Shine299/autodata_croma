# AutoData — Hackathon GOV-TECH Croma

> Verifica el auto **y** al vendedor. Devuelve una decisión y un precio, no un reporte.

Deadline de entrega: **16 de agosto, 6:30 p. m.**
Equipo: 5 personas · Metodología: **SDD (Spec-Driven Development)** sobre **Scrum**
(3 sprints con puertas de testing), ejecutada de forma híbrida con agentes de IA.

---

## Cómo usar esta documentación

Esta carpeta **es el contexto del proyecto**. Todo agente de IA (Claude Code, Cursor, Copilot)
debe recibir estos archivos antes de escribir una línea de código. El orden de lectura importa:

| # | Archivo | Para qué sirve | Quién lo lee |
|---|---------|----------------|--------------|
| 0 | [`00-CONTEXTO.md`](./00-CONTEXTO.md) | Problema, mercado, competencia, límites duros de Croma | Todos + agentes |
| 1 | [`01-CONSTITUTION.md`](./01-CONSTITUTION.md) | Reglas no negociables del proyecto (SDD paso 1) | Todos + agentes |
| 2 | [`02-SPEC.md`](./02-SPEC.md) | QUÉ construimos: historias, criterios de aceptación (SDD paso 2) | Todos + agentes |
| 3 | [`03-API-DESIGN.md`](./03-API-DESIGN.md) | Contrato de API: recurso → endpoint → request/response | Backend + Bot |
| 4 | [`04-PLAN-TECNICO.md`](./04-PLAN-TECNICO.md) | CÓMO lo construimos: stack, arquitectura, modelo de datos (SDD paso 3) | Backend + Data |
| 5 | [`05-TASKS.md`](./05-TASKS.md) | Backlog atómico con IDs, dueños y Definition of Done (SDD paso 4) | Todos |
| 6 | [`06-PLAN-ACCION.md`](./06-PLAN-ACCION.md) | **Plan Scrum:** 3 sprints, puertas de testing, backlog por participante | Todos |
| 7 | [`07-AGENTS.md`](./07-AGENTS.md) | Reglas de trabajo híbrido humano ↔ agente de IA | Todos + agentes |
| 8 | [`08-PROMPTS.md`](./08-PROMPTS.md) | Prompts del producto (el bot) + prompts de desarrollo | Bot + todos |
| 9 | [`09-DEMO-PITCH.md`](./09-DEMO-PITCH.md) | Guion de la demo de 3 minutos y checklist de entrega | Producto |
| 10 | [`10-LIBRERIA-PROMPTS.md`](./10-LIBRERIA-PROMPTS.md) | **12 prompts de ceremonia:** planning, daily, cierre de tarde, puertas, retro | Scrum Master + todos |

---

## Ritmo del proyecto

```
Sprint 0        Sprint 1          🚦     Sprint 2          🚦     Sprint 3        🚦
Alineamiento →  Los datos      Puerta →  El producto    Puerta →  Listo para   Puerta → Entrega
   2 h          entran (8 h)     1        decide (8 h)     2       usarse (6 h)   3
```

Cada participante mantiene su dominio durante los 3 sprints, cambiando de foco en cada uno.
**Ningún sprint arranca hasta que la puerta anterior cierre en verde.** Ver `06-PLAN-ACCION.md`.

El prompt **P-03 (cierre de tarde)** de `10-LIBRERIA-PROMPTS.md` es la rutina que sostiene
todo esto: se ejecuta cada tarde y produce el plan del día siguiente por fase, sprint y persona.

---

## Regla de oro del proyecto

> **Si no está en la spec, no se codea. Si se codea algo nuevo, primero se actualiza la spec.**

Los agentes de IA generan código rápido pero divergente. La spec es la única fuente de verdad
que mantiene a 5 personas y N agentes construyendo la misma cosa.

---

## Arranque rápido

```bash
git clone <repo> && cd autodata
cp .env.example .env        # pedir CROMA_API_KEY y TELEGRAM_BOT_TOKEN al Tech Lead
docker compose up -d        # postgres local (o usar Supabase directo)
uv sync                     # o: pip install -r requirements.txt
uvicorn app.main:app --reload
```

> ⚠️ **Instala siempre las dependencias antes de correr o testear.** Un `.venv` sin
> `pip install -r requirements.txt` no importa `app.main` (falta `fastapi`) ni colecta los
> tests que usan `sqlalchemy`.

### Verificar que arranca

```bash
pytest -q                                   # la suite completa debe pasar en verde (mock, sin cuota)
uvicorn app.main:app --reload               # /api/v1/health y /api/v1/quota responden 200
```

`/api/v1/health` y `/api/v1/quota` degradan con gracia si la base de datos no responde
(devuelven 200 con un campo `database: error: ...`), nunca un stacktrace.

Ver [`04-PLAN-TECNICO.md`](./04-PLAN-TECNICO.md) para el detalle.
