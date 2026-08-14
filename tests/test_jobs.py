import pytest
from fastapi.testclient import TestClient

from app.core.jobs import JobStore, job_store
from app.main import app

client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def _clear_jobs():
    job_store._jobs.clear()
    yield
    job_store._jobs.clear()


def test_get_nonexistent_returns_404_envelope():
    resp = client.get("/api/v1/jobs/nonexistent")
    assert resp.status_code == 404
    body = resp.json()
    assert body["error"]["type"] == "not_found"
    assert body["error"]["code"] == "job_not_found"


def test_create_and_get_job():
    sources = ["SBS", "SUTRAN", "APESEG", "Callao", "SAT_LIMA", "SAT_CAPTURAS"]
    job = job_store.create(sources)
    resp = client.get(f"/api/v1/jobs/{job.job_id}")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "pending"
    assert data["progress"] == 0
    assert len(data["pendingSources"]) == 6
    assert len(data["completedSources"]) == 0


def test_mark_source_done_updates_progress():
    sources = ["SBS", "SUTRAN", "APESEG", "Callao", "SAT_LIMA", "SAT_CAPTURAS"]
    job = job_store.create(sources)
    job_store.mark_source_done(job.job_id, "SBS")
    job_store.mark_source_done(job.job_id, "SUTRAN")
    job_store.mark_source_done(job.job_id, "APESEG")
    resp = client.get(f"/api/v1/jobs/{job.job_id}")
    data = resp.json()["data"]
    assert data["progress"] == 50
    assert "SBS" in data["completedSources"]
    assert "SBS" not in data["pendingSources"]


def test_complete_job():
    job = job_store.create(["SBS"])
    job_store.mark_source_done(job.job_id, "SBS")
    job_store.complete(job.job_id, {"verdict": "GO"})
    resp = client.get(f"/api/v1/jobs/{job.job_id}")
    data = resp.json()["data"]
    assert data["status"] == "completed"
    assert data["progress"] == 100
    assert data["result"]["verdict"] == "GO"


def test_fail_job():
    job = job_store.create(["SBS"])
    job_store.fail(job.job_id, {"type": "upstream_error", "message": "timeout"})
    resp = client.get(f"/api/v1/jobs/{job.job_id}")
    data = resp.json()["data"]
    assert data["status"] == "failed"
    assert data["error"]["type"] == "upstream_error"
