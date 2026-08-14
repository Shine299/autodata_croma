from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import get_db
from app.repositories.quota_repo import QuotaRepository

router = APIRouter()

@router.get("/quota")
async def get_quota_summary(db: AsyncSession = Depends(get_db)):
    """
    Retorna el resumen de consumo de la cuota diaria de Croma.
    """
    quota_repo = QuotaRepository(db)
    summary = await quota_repo.get_daily_summary(
        mode=settings.croma_mode,
        limit=100  # Límite por defecto según plan técnico
    )
    return {"data": summary}
