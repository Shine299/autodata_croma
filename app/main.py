import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.api.health import router as health_router
from app.api.quota import router as quota_router
from app.api.verifications import router as verifications_router

app = FastAPI(title="AutoData", version="0.1.0")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {
            "type": "client_error" if exc.status_code < 500 else "server_error",
            "code": str(exc.detail) if isinstance(exc.detail, str) else "error",
            "message": str(exc.detail),
            "requestId": str(uuid.uuid4()),
        }},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": {
            "type": "server_error",
            "code": "internal_error",
            "message": "Error interno del servidor",
            "requestId": str(uuid.uuid4()),
        }},
    )


app.include_router(health_router, prefix="/api/v1")
app.include_router(quota_router, prefix="/api/v1")
app.include_router(verifications_router, prefix="/api/v1")

