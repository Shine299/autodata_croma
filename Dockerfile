# AutoData — Production Containerfile (P4 - Sprint 3 / E-04)
# Multi-stage Python 3.12 slim build

FROM python:3.12-slim AS builder

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

COPY requirements.txt .
RUN pip install --user --no-warn-script-location -r requirements.txt

# Final runtime stage
FROM python:3.12-slim AS runner

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/home/appuser/.local/bin:$PATH \
    PORT=8000 \
    APP_ENV=production

# Security: run as non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local
COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

# Healthcheck targeting public API endpoint
# (usaba os.environ sin importar `os` — fallaba siempre con NameError)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import os, urllib.request, sys; sys.exit(0 if urllib.request.urlopen('http://localhost:' + str(os.environ.get('PORT', 8000)) + '/api/v1/health').getcode() == 200 else 1)"

# Una sola imagen, dos procesos. Railway construye desde este Dockerfile, así que
# el `Procfile` se ignora y el bot nunca arrancaba: la API quedaba viva y el bot
# muerto. Con PROCESS=bot el mismo contenedor levanta el bot de Telegram.
#   - Servicio API : (sin PROCESS)  → uvicorn
#   - Servicio bot : PROCESS=bot    → python -m app.bot.main
CMD ["sh", "-c", "if [ \"$PROCESS\" = \"bot\" ]; then exec python -m app.bot.main; else exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}; fi"]
