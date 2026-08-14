# 05 — Backlog de Tareas

> **SDD paso 4.** Cada tarea es atómica, tiene dueño, una tarea de la que depende, y un
> Definition of Done verificable. Si una tarea no se puede verificar, está mal escrita.

**Dueños:** `P1` Tech Lead · `P2` Backend Core · `P3` Bot · `P4` Data/Infra · `P5` Producto

Leyenda de estado: ⬜ pendiente · 🟨 en curso · ✅ hecho · ⛔ bloqueada

---

## Épica A — Fundaciones (bloque 1, todos en paralelo)

| ID | Tarea | Dueño | Depende | DoD |
|---|---|---|---|---|
| A-01 | Crear repo, estructura de carpetas de `04-PLAN-TECNICO.md`, `.env.example`, README | P1 | — | `git clone` + `uvicorn app.main:app` levanta y `/api/v1/health` responde 200 |
| A-02 | Definir **todos** los schemas Pydantic según `03-API-DESIGN.md` | P1 | A-01 | `/docs` de FastAPI muestra los 7 recursos con sus schemas exactos |
| A-03 | Proyecto Supabase + correr el DDL de las 5 tablas | P4 | — | Las tablas existen y se pueden insertar filas desde el dashboard |
| ✅ A-04 | Crear el bot en @BotFather, obtener token, `/start` responde "hola" | P3 | — | Se puede escribir al bot desde el celular y contesta |
| A-05 | Obtener `CROMA_API_KEY` en platform.usecroma.com y repartirla por canal privado | P1 | — | Todos tienen la key en su `.env` local |
| A-06 | Probar **manualmente** con curl 1 endpoint de Croma y guardar el JSON crudo | P1 | A-05 | `fixtures/sbs_sample.json` existe. Consumo anotado en `docs/quota-log.md` |
| A-07 | Leer los 6 docs de contexto y armar el prompt base para los agentes | P5 | — | `08-PROMPTS.md` validado por el equipo |

---

## Épica B — Integración con Croma (el corazón)

| ID | Tarea | Dueño | Depende | DoD |
|---|---|---|---|---|
| B-01 | `CromaClient` con httpx async, auth, timeout, `SourceResult` | P1 | A-02 | Test unitario con `httpx.MockTransport` en verde |
| B-02 | **Modo mock**: leer `fixtures/*.json` cuando `CROMA_MODE=mock` | P1 | B-01 | Todo el equipo desarrolla sin gastar cuota. Verificado por P4 |
| B-03 | Caché read-through contra `croma_cache` con TTL por fuente | P4 | B-01, A-03 | Segunda llamada a la misma placa no toca la red (log lo prueba) |
| B-04 | Logging de cuota en `quota_log` + tolerancia a headers ausentes | P4 | B-01 | `GET /api/v1/quota` devuelve datos reales |
| B-05 | Backoff en 429 respetando `Retry-After`, máx. 2 reintentos | P1 | B-01 | Test simula 429 y verifica el reintento |
| B-06 | Adapter **SBS SOAT** + mapper a `insurance` | P2 | B-02 | Fixture real mapeado a `InsuranceSchema` sin campos nulos inesperados |
| B-07 | Adapter **APESEG SOAT** + merge con SBS | P2 | B-06 | `hasActiveSoat` correcto en los 4 escenarios sembrados |
| B-08 | Adapter **SUTRAN** + mapper a `infractions` (incluye `total` PEN y `severeCount`) | P2 | B-02 | Suma de montos coincide con el fixture |
| B-09 | Adapter **Callao papeletas** + merge en `infractions` | P2 | B-08 | Items del Callao aparecen con `source: "CALLAO"` |
| B-10 | Adapter **SAT Lima cuenta** (por placa) → `taxDebt` | P2 | B-02 | Deuda total correcta |
| B-11 | Adapter **SAT Lima capturas** → `captureOrder` | P2 | B-02 | Placa con captura devuelve `hasCaptureOrder: true` |
| B-12 | Adapter **SUNAT** por documento → `taxpayer` + flag `isVehicleTrader` | P4 | B-02 | Detecta correctamente actividad de venta de vehículos |
| B-13 | Adapter **SAT Lima por DNI/RUC** → `personalDebt` | P4 | B-02 | Devuelve placas relacionadas |
| B-14 | Ejecución concurrente de las 6 fuentes con `asyncio.gather` | P1 | B-06..B-11 | Latencia total ≈ la fuente más lenta, no la suma |

---

## Épica C — Endpoints de la API

| ID | Tarea | Dueño | Depende | DoD |
|---|---|---|---|---|
| C-01 | `POST /api/v1/vehicles/inspections` | P2 | B-14 | Response idéntico al contrato de `03-API-DESIGN.md` |
| C-02 | Validación y normalización de placa (`ABC-123`→`ABC123`, motos) | P2 | A-02 | 10 casos de test, incluyendo inválidos → `400 invalid_plate` |
| C-03 | `POST /api/v1/sellers/screenings` + validación de `consent` | P4 | B-12, B-13 | `consent: false` → `400`. Documento enmascarado en el response |
| C-04 | `scoring_service`: flags, riskScore y verdict con las reglas de la spec | P2 | C-01 | Tabla de 8 casos de test cubre todas las reglas de HU-03 |
| C-05 | `POST /api/v1/verifications` orquestando vehículo + vendedor + score | P2 | C-01, C-03, C-04 | Los 4 escenarios sembrados devuelven el veredicto esperado |
| C-06 | `appraisal_service` + `POST /verifications/{id}/appraisals` | P2 | C-05 | Deducciones cuadran al centavo con el fixture |
| C-07 | Generación del `negotiationScript` (plantilla + datos) | P5 | C-06 | Texto legible, en español peruano, sin jerga registral |
| C-08 | `GET /verifications/{id}` desde Supabase | P4 | C-05, A-03 | Se recupera una verificación creada hace 10 min |
| C-09 | `GET /api/v1/jobs/{jobId}` + modo async con `Prefer: respond-async` | P1 | C-05 | Progreso incremental visible en el polling |
| C-10 | Handler global de errores con el envelope estándar | P1 | A-02 | Ningún endpoint devuelve stacktrace |
| C-11 | `GET /api/v1/health` y `GET /api/v1/quota` | P4 | B-04 | Ambos responden 200 con datos reales |

---

## Épica D — Bot de Telegram

| ID | Tarea | Dueño | Depende | DoD |
|---|---|---|---|---|
| ✅ D-01 | Esqueleto del bot con polling + `/start` + `/ayuda` | P3 | A-04 | Responde en < 2 s |
| D-02 | Máquina de estados (`IDLE → AWAITING_* → DONE`) persistida en `conversations` | P3 | A-03 | El estado sobrevive a un reinicio del proceso |
| ✅ D-03 | Parser de texto libre: placa, precio ("32 mil", "S/32,000"), DNI | P3 | — | 15 casos de test, incluye "ABC-123 me lo dan a 32 mil" |
| D-04 | Llamada del bot a `POST /verifications` y manejo de errores | P3 | C-05, D-02 | Un 502 de la API produce un mensaje amable, no un crash |
| D-05 | **Mensajes progresivos** por fuente conforme van llegando | P3 | C-09, D-04 | Se ven 4-5 mensajes secuenciales, no un bloque final |
| D-06 | Formateo del veredicto con emojis de semáforo y jerarquía visual | P3 | D-04 | Legible en pantalla de celular sin hacer scroll horizontal |
| D-07 | Botones inline: Ver detalle · Calcular precio · Verificar vendedor · Nueva consulta | P3 | D-06 | Los 4 botones funcionan |
| D-08 | Flujo de verificación de vendedor **con confirmación explícita** | P3 | C-03, D-07 | El bot no consulta a nadie sin un "sí" del usuario |
| D-09 | Flujo de tasación: pide precio, muestra deducciones y guion copiable | P3 | C-06, C-07 | El guion se puede copiar de un toque |
| D-10 | Mensajes de error para cada caso borde de la spec §6 | P3 | D-04 | Los 7 casos borde probados a mano |

---

## Épica E — Web, demo y entrega

| ID | Tarea | Dueño | Depende | DoD |
|---|---|---|---|---|
| E-01 | Página `/r/{verificationId}` responsive con semáforo y fuentes | P5 | C-08 | Se ve bien en celular y en proyector |
| E-02 | Landing de 1 pantalla con el pitch y un ejemplo | P5 | — | Explica el producto en 10 segundos de lectura |
| E-03 | Sembrar las 5 placas en modo `live` y congelar fixtures | P1 | B-02, C-05 | `fixtures/demo/` con los 5 escenarios. Cuota anotada |
| E-04 | Deploy en Railway/Render con variables de entorno | P4 | C-11 | URL pública responde `/api/v1/health` |
| E-05 | Guion de demo de 3 minutos escrito y cronometrado | P5 | — | `09-DEMO-PITCH.md` completo, ensayado 2 veces |
| E-06 | Grabar video de respaldo de la demo | P5 | E-03, D-09 | MP4 < 3 min, audio claro, subido a Drive |
| E-07 | README público del repo con arquitectura y cómo correr | P1 | todo | Un tercero puede levantarlo siguiendo el README |
| E-08 | Slide de "límites conocidos y roadmap" (SUNARP, MTC) | P5 | — | Honesto y con plan, no una excusa |
| E-09 | Enviar el formulario de entrega | P5 | E-04, E-06 | Confirmación recibida antes de las 6:30 p. m. |

---

## Definition of Done global

Una tarea está hecha cuando:
1. El código está en `main` y no rompe el arranque.
2. Cumple exactamente el contrato de `03-API-DESIGN.md`.
3. Funciona en modo `mock` sin tocar la cuota.
4. Un compañero distinto al autor lo probó al menos una vez.
5. Su fila en esta tabla está en ✅.
