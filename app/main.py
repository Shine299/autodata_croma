import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.health import router as health_router
from app.api.jobs import router as jobs_router
from app.api.quota import router as quota_router
from app.web.routes import router as web_router
from app.schemas.common import ErrorDetail, ErrorEnvelope

app = FastAPI(title="AutoData", version="0.1.0")

app.include_router(health_router, prefix="/api/v1")
app.include_router(jobs_router, prefix="/api/v1")
app.include_router(quota_router, prefix="/api/v1")
app.include_router(web_router)


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
    type_ = _STATUS_TYPE_MAP.get(exc.status_code, "internal_error")
    code = exc.detail if isinstance(exc.detail, str) else "error"
    return _error_response(exc.status_code, type_, code, str(exc.detail))


@app.exception_handler(ValueError)
async def _value_error(_req: Request, exc: ValueError) -> JSONResponse:
    return _error_response(400, "validation_error", str(exc), str(exc))


@app.exception_handler(Exception)
async def _catch_all(_req: Request, exc: Exception) -> JSONResponse:
    logging.exception("Unhandled exception")
    return _error_response(500, "internal_error", "internal_error", "Error interno del servidor.")

