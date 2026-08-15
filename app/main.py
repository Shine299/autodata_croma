import logging
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.health import router as health_router
from app.api.jobs import router as jobs_router
from app.api.quota import router as quota_router
from app.api.sellers import router as sellers_router
from app.api.verifications import router as verifications_router
from app.core.logging import ObservabilityMiddleware
from app.web.routes import router as web_router
from app.schemas.common import ErrorDetail, ErrorEnvelope

logger = logging.getLogger("autodata.main")

app = FastAPI(
    title="AutoData API",
    description="Plataforma de verificación vehicular y screening de vendedor para Perú vía Croma",
    version="0.1.0",
)


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
app.include_router(jobs_router, prefix="/api/v1")
app.include_router(quota_router, prefix="/api/v1")
app.include_router(sellers_router, prefix="/api/v1")
app.include_router(verifications_router, prefix="/api/v1")
app.include_router(web_router)  # sin prefijo: expone "/" y "/r/{id}"


# --- C-10: manejo global de errores con el envelope estándar --------------
# Contrato: "todo error viene envuelto en `error`" (03-API-DESIGN.md §L16).
_STATUS_TYPE_MAP = {
    400: "validation_error",
    404: "not_found",
    429: "rate_limit_error",
    502: "upstream_error",
}


def _error_response(status: int, type_: str, code: str, message: str) -> JSONResponse:
    envelope = ErrorEnvelope(error=ErrorDetail(type=type_, code=code, message=message))
    return JSONResponse(status_code=status, content=envelope.model_dump(by_alias=True))


@app.exception_handler(RequestValidationError)
async def _validation_error(_req: Request, exc: RequestValidationError) -> JSONResponse:
    first = exc.errors()[0] if exc.errors() else {}
    msg = first.get("msg", "Datos inválidos en la solicitud.")
    return _error_response(400, "validation_error", "invalid_request", msg)


@app.exception_handler(StarletteHTTPException)
async def _http_exception(_req: Request, exc: StarletteHTTPException) -> JSONResponse:
    detail = exc.detail
    # Si el endpoint ya entregó un detail con forma de envelope ({"error": {...}}),
    # lo normalizamos al envelope top-level preservando type/code/message.
    if isinstance(detail, dict) and isinstance(detail.get("error"), dict):
        err = detail["error"]
        return _error_response(
            exc.status_code,
            err.get("type", _STATUS_TYPE_MAP.get(exc.status_code, "internal_error")),
            err.get("code", "error"),
            err.get("message", ""),
        )
    # Caso normal: detail es un string con el código de error.
    type_ = _STATUS_TYPE_MAP.get(exc.status_code, "internal_error")
    code = detail if isinstance(detail, str) else "error"
    return _error_response(exc.status_code, type_, code, str(detail))


@app.exception_handler(ValueError)
async def _value_error(_req: Request, exc: ValueError) -> JSONResponse:
    return _error_response(400, "validation_error", str(exc), str(exc))


@app.exception_handler(Exception)
async def _catch_all(_req: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception")
    return _error_response(500, "internal_error", "internal_error", "Error interno del servidor.")
