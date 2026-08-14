from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

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


@router.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    return templates.TemplateResponse(request=request, name="landing.html", context={"sources": SOURCES})
