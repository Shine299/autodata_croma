"""D-02 — Estados de la conversación del bot.

Máquina de estados mínima del hilo Telegram, persistida en la tabla `conversations`
(ver migrations/schema.sql, tabla 5). El estado sobrevive a un reinicio del proceso
porque vive en la base, no en memoria.

Flujo feliz de una consulta de vehículo:

    IDLE ──(placa)──▶ AWAITING_PRICE ──(precio)──▶ DONE
      │                                              │
      └──────────── "nueva consulta" ◀──────────────┘

`AWAITING_SELLER_CONSENT` es el punto de espera del flujo de vendedor (D-08), que
exige un "sí" explícito antes de consultar a nadie.
"""

from enum import Enum


class State(str, Enum):
    IDLE = "IDLE"
    AWAITING_PLATE = "AWAITING_PLATE"
    AWAITING_PRICE = "AWAITING_PRICE"
    AWAITING_SELLER_CONSENT = "AWAITING_SELLER_CONSENT"
    DONE = "DONE"


#: Estado inicial de todo chat nuevo.
INITIAL = State.IDLE
