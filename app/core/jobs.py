from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class JobState:
    job_id: str
    status: str
    progress: int
    completed_sources: list[str]
    pending_sources: list[str]
    result: dict | None
    error: dict | None
    created_at: datetime
    updated_at: datetime


class JobStore:
    # ponytail: in-memory dict, DB-backed JobRepository if persistence matters
    def __init__(self) -> None:
        self._jobs: dict[str, JobState] = {}

    def create(self, all_sources: list[str]) -> JobState:
        now = datetime.now(timezone.utc)
        job = JobState(
            job_id=uuid.uuid4().hex[:12],
            status="pending",
            progress=0,
            completed_sources=[],
            pending_sources=list(all_sources),
            result=None,
            error=None,
            created_at=now,
            updated_at=now,
        )
        self._jobs[job.job_id] = job
        return job

    def get(self, job_id: str) -> JobState | None:
        return self._jobs.get(job_id)

    def mark_running(self, job_id: str) -> None:
        job = self._jobs.get(job_id)
        if job:
            job.status = "running"
            job.updated_at = datetime.now(timezone.utc)

    def mark_source_done(self, job_id: str, source: str) -> None:
        job = self._jobs.get(job_id)
        if not job:
            return
        if source in job.pending_sources:
            job.pending_sources.remove(source)
        if source not in job.completed_sources:
            job.completed_sources.append(source)
        total = len(job.completed_sources) + len(job.pending_sources)
        job.progress = int(len(job.completed_sources) / total * 100) if total else 100
        job.updated_at = datetime.now(timezone.utc)

    def complete(self, job_id: str, result: dict) -> None:
        job = self._jobs.get(job_id)
        if not job:
            return
        job.status = "completed"
        job.progress = 100
        job.result = result
        job.pending_sources = []
        job.updated_at = datetime.now(timezone.utc)

    def fail(self, job_id: str, error: dict) -> None:
        job = self._jobs.get(job_id)
        if not job:
            return
        job.status = "failed"
        job.error = error
        job.updated_at = datetime.now(timezone.utc)


job_store = JobStore()
