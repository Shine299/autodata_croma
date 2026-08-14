from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.quota import router as quota_router
from app.api.sellers import router as sellers_router
from app.api.verifications import router as verifications_router
from app.web.routes import router as web_router

app = FastAPI(title="AutoData", version="0.1.0")

app.include_router(health_router, prefix="/api/v1")
app.include_router(quota_router, prefix="/api/v1")
app.include_router(sellers_router, prefix="/api/v1")
app.include_router(verifications_router, prefix="/api/v1")
app.include_router(web_router)
