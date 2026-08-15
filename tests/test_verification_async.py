"""C-09 (enqueue) — Tests del modo asíncrono de POST /verifications.

Cubre el contrato (`Prefer: respond-async` → 202 con jobId + pollUrl) y el DoD de
progreso incremental: el runner lleva el job de pending → completed marcando las 6
fuentes, y el resultado final trae el veredicto.
"""

import pytest
from fastapi.testclient import TestClient

from app.core.jobs import job_store
from app.main import app
from app.schemas.verification import VerificationRequest
from app.services import verification_runner

client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def _fast_and_clean(monkeypatch):
    # Sin latencia simulada: los tests corren rápido.
    monkeypatch.setattr(verification_runner, "SOURCE_DELAY_SECONDS", 0.0)
    job_store._jobs.clear()
    yield
    job_store._jobs.clear()


def test_async_post_returns_202_with_job_and_poll_url():
    resp = client.post(
        "/api/v1/verifications",
        json={"plate": "ABC123_GO"},
        headers={"Prefer": "respond-async"},
    )
    assert resp.status_code == 202
    data = resp.json()["data"]
    assert data["status"] == "pending"
    assert data["jobId"]
    assert data["pollUrl"] == f"/api/v1/jobs/{data['jobId']}"

    # El job es consultable de inmediato en el endpoint de polling.
    poll = client.get(data["pollUrl"])
    assert poll.status_code == 200


def test_sync_post_still_returns_200():
    """El modo síncrono (sin Prefer) sigue intacto."""
    resp = client.post("/api/v1/verifications", json={"plate": "ABC123_GO"})
    assert resp.status_code == 200
    assert resp.json()["data"]["verdict"] == "GO"


@pytest.mark.asyncio
async def test_runner_drives_progress_to_completed():
    job = job_store.create(verification_runner.SOURCE_DISPLAYS)
    req = VerificationRequest(plate="ABC123_GO")

    await verification_runner.run_verification_job(job.job_id, req)

    done = job_store.get(job.job_id)
    assert done.status == "completed"
    assert done.progress == 100
    assert len(done.completed_sources) == len(verification_runner.SOURCE_DISPLAYS)
    assert not done.pending_sources
    assert done.result["data"]["verdict"] == "GO"


@pytest.mark.asyncio
async def test_runner_marks_failure(monkeypatch):
    async def _boom(_req):
        raise RuntimeError("fuentes caídas")

    monkeypatch.setattr(verification_runner, "build_verification", _boom)

    job = job_store.create(verification_runner.SOURCE_DISPLAYS)
    await verification_runner.run_verification_job(job.job_id, VerificationRequest(plate="X"))

    failed = job_store.get(job.job_id)
    assert failed.status == "failed"
    assert failed.error["type"] == "internal_error"
