from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.verification_repo import VerificationRepository

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

SOURCES = [
    {"name": "SBS", "desc": "Siniestralidad SOAT"},
    {"name": "APESEG", "desc": "Vigencia de póliza SOAT"},
    {"name": "SUTRAN", "desc": "Infracciones de tránsito"},
    {"name": "Callao", "desc": "Papeletas provinciales"},
    {"name": "SAT Lima", "desc": "Deuda vehicular y capturas"},
    {"name": "SUNAT", "desc": "Verificación del vendedor"},
]

# E-01 — mismo vocabulario de veredicto que la landing ("Qué hace AutoData").
_VERDICT_LABEL = {"GO": "COMPRA", "CAUTION": "OJO", "STOP": "NO COMPRES"}
_VERDICT_COLOR = {"GO": "emerald", "CAUTION": "yellow", "STOP": "red"}
_SEVERITY_EMOJI = {"critical": "🔴", "warning": "🟡", "info": "🔵"}


@router.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    return templates.TemplateResponse(request=request, name="landing.html", context={"sources": SOURCES})


@router.get("/r/{verification_id}", response_class=HTMLResponse)
async def report(request: Request, verification_id: str, db: AsyncSession = Depends(get_db)):
    """E-01 — página pública del reporte de una verificación (semáforo + fuentes)."""
    repo = VerificationRepository(db)
    payload = await repo.get_by_id(verification_id)

    if not payload:
        return templates.TemplateResponse(
            request=request,
            name="report.html",
            context={"found": False, "verification_id": verification_id},
            status_code=404,
        )

    verdict = str(payload.get("verdict", "")).upper()
    flags = [
        {**flag, "emoji": _SEVERITY_EMOJI.get(str(flag.get("severity", "info")).lower(), "•")}
        for flag in (payload.get("flags") or [])
    ]

    context = {
        "found": True,
        "verification_id": payload.get("verificationId", verification_id),
        "plate": payload.get("plate", "?"),
        "verdict": verdict,
        "verdict_label": _VERDICT_LABEL.get(verdict, verdict or "SIN VEREDICTO"),
        "verdict_color": _VERDICT_COLOR.get(verdict, "gray"),
        "risk_score": payload.get("riskScore"),
        "headline": payload.get("headline", ""),
        "summary": payload.get("summary", ""),
        "flags": flags,
        "confidence": payload.get("confidence") or {},
        "disclaimer": payload.get("disclaimer", ""),
    }
    return templates.TemplateResponse(request=request, name="report.html", context=context)
