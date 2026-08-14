from datetime import datetime, time, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import get_db
from app.repositories.quota_repo import QuotaRepository

router = APIRouter()

DEFAULT_LIMIT = 100  # Límite por defecto según plan técnico


@router.get("/quota")
async def get_quota_summary(db: AsyncSession = Depends(get_db)):
    """
    Retorna el resumen de consumo de la cuota diaria de Croma.

    Si la base de datos no responde, degrada con gracia (igual que /health)
    en vez de propagar una excepción: ninguna fuente caída tumba la respuesta.
    """
    quota_repo = QuotaRepository(db)
    try:
        summary = await quota_repo.get_daily_summary(
            mode=settings.croma_mode,
            limit=DEFAULT_LIMIT,
        )
    except Exception as e:
        tomorrow_start = datetime.combine(
            datetime.now(timezone.utc).date() + timedelta(days=1),
            time.min,
            tzinfo=timezone.utc,
        )
        summary = {
            "limit": DEFAULT_LIMIT,
            "remaining": DEFAULT_LIMIT,
            "resetAt": tomorrow_start.isoformat().replace("+00:00", "Z"),
            "consumedToday": 0,
            "cacheHitRate": 0.0,
            "mode": settings.croma_mode,
            "database": f"error: {e}",
        }
    return {"data": summary}
