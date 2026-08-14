from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.quota import router as quota_router
from app.api.verifications import router as verifications_router

app = FastAPI(title="AutoData", version="0.1.0")

app.include_router(health_router, prefix="/api/v1")
app.include_router(quota_router, prefix="/api/v1")
app.include_router(verifications_router, prefix="/api/v1")

