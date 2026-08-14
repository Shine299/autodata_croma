from app.schemas.common import CamelModel


class HealthResponse(CamelModel):
    status: str = "ok"


class QuotaResponse(CamelModel):
    limit: int
    remaining: int
    reset_at: str
    consumed_today: int
    cache_hit_rate: float
    mode: str
