from datetime import datetime, time, timedelta, timezone
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.models import QuotaLogModel


class QuotaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def log_quota(
        self,
        source: str,
        endpoint: str,
        remaining: Optional[int],
        request_id: Optional[str],
        cache_hit: bool,
        latency_ms: int,
    ) -> None:
        """
        Inserta un nuevo registro en quota_log.
        """
        new_log = QuotaLogModel(
            source=source,
            endpoint=endpoint,
            remaining=remaining,
            request_id=request_id,
            cache_hit=cache_hit,
            latency_ms=latency_ms,
            created_at=datetime.now(timezone.utc)
        )
        self.session.add(new_log)
        await self.session.commit()

    async def get_daily_summary(self, mode: str, limit: int = 100) -> dict:
        """
        Retorna el resumen de cuota diaria del día de hoy en UTC.
        """
        # Calcular el inicio de hoy en UTC (timezone-aware)
        today_start = datetime.combine(datetime.now(timezone.utc).date(), time.min, tzinfo=timezone.utc)

        # Consultar los logs de hoy
        stmt = select(QuotaLogModel).where(QuotaLogModel.created_at >= today_start)
        result = await self.session.execute(stmt)
        logs = result.scalars().all()

        consumed_today = sum(1 for log in logs if not log.cache_hit)
        cached_today = sum(1 for log in logs if log.cache_hit)
        total_today = consumed_today + cached_today

        cache_hit_rate = float(cached_today) / total_today if total_today > 0 else 0.0

        # Obtener el último remaining reportado por Croma (no nulo)
        stmt_remaining = (
            select(QuotaLogModel.remaining)
            .where(QuotaLogModel.remaining.isnot(None))
            .order_by(QuotaLogModel.id.desc())
            .limit(1)
        )
        result_rem = await self.session.execute(stmt_remaining)
        last_remaining = result_rem.scalar_one_or_none()

        if last_remaining is None:
            remaining = max(limit - consumed_today, 0)
        else:
            remaining = last_remaining

        # Próximo reset de cuota (inicio del día siguiente en UTC)
        tomorrow_start = datetime.combine(datetime.now(timezone.utc).date() + timedelta(days=1), time.min, tzinfo=timezone.utc)
        reset_at = tomorrow_start.isoformat().replace("+00:00", "Z")

        return {
            "limit": limit,
            "remaining": remaining,
            "resetAt": reset_at,
            "consumedToday": consumed_today,
            "cacheHitRate": cache_hit_rate,
            "mode": mode,
        }
