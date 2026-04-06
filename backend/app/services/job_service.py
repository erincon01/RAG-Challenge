"""In-memory job tracking for ingestion workflows."""

from __future__ import annotations

import builtins
from dataclasses import asdict, dataclass
from datetime import datetime
from threading import Lock
from typing import Any
from uuid import uuid4


@dataclass
class JobRecord:
    """Job metadata and execution state."""

    id: str
    type: str
    status: str
    source: str | None
    payload: dict[str, Any]
    created_at: str
    updated_at: str
    progress: int
    total: int
    message: str
    error: str | None
    result: dict[str, Any]
    logs: list[str]


class JobService:
    """Thread-safe in-memory registry for async/background jobs."""

    _jobs: dict[str, JobRecord] = {}
    _lock = Lock()
    _max_logs = 1000

    @staticmethod
    def _timestamp() -> str:
        return datetime.utcnow().isoformat()

    @classmethod
    def _append_log(cls, job: JobRecord, line: str) -> None:
        ts = cls._timestamp()
        job.logs.append(f"[{ts}] {line}")
        if len(job.logs) > cls._max_logs:
            job.logs = job.logs[-cls._max_logs :]

    @classmethod
    def create_job(
        cls,
        job_type: str,
        payload: dict[str, Any],
        source: str | None = None,
    ) -> JobRecord:
        """Create a new job and return its record."""
        now = cls._timestamp()
        job = JobRecord(
            id=str(uuid4()),
            type=job_type,
            status="pending",
            source=source,
            payload=payload,
            created_at=now,
            updated_at=now,
            progress=0,
            total=0,
            message="Job created",
            error=None,
            result={},
            logs=[],
        )
        cls._append_log(job, f"Job created ({job_type})")
        with cls._lock:
            cls._jobs[job.id] = job
        return job

    @classmethod
    def update(
        cls,
        job_id: str,
        *,
        status: str | None = None,
        progress: int | None = None,
        total: int | None = None,
        message: str | None = None,
        result: dict[str, Any] | None = None,
    ) -> None:
        """Update mutable fields of a job."""
        with cls._lock:
            job = cls._jobs.get(job_id)
            if not job:
                return
            if status is not None and status != job.status:
                job.status = status
                cls._append_log(job, f"Status changed to {status}")
            if progress is not None:
                job.progress = progress
            if total is not None:
                job.total = total
            if message is not None:
                job.message = message
                cls._append_log(job, message)
            if result is not None:
                job.result = result
            job.updated_at = cls._timestamp()

    @classmethod
    def log(cls, job_id: str, message: str) -> None:
        """Append one execution log line to a job."""
        with cls._lock:
            job = cls._jobs.get(job_id)
            if not job:
                return
            cls._append_log(job, message)
            job.updated_at = cls._timestamp()

    @classmethod
    def fail(cls, job_id: str, error: str) -> None:
        """Mark job as failed."""
        with cls._lock:
            job = cls._jobs.get(job_id)
            if not job:
                return
            job.status = "error"
            job.error = error
            job.message = "Job failed"
            cls._append_log(job, f"ERROR: {error}")
            job.updated_at = cls._timestamp()

    @classmethod
    def complete(cls, job_id: str, result: dict[str, Any] | None = None) -> None:
        """Mark job as completed."""
        with cls._lock:
            job = cls._jobs.get(job_id)
            if not job:
                return
            job.status = "success"
            job.message = "Job completed"
            job.progress = job.total if job.total > 0 else job.progress
            if result is not None:
                job.result = result
            cls._append_log(job, "Job completed successfully")
            job.updated_at = cls._timestamp()

    @classmethod
    def get(cls, job_id: str) -> dict[str, Any] | None:
        """Get one job by id."""
        with cls._lock:
            job = cls._jobs.get(job_id)
            return asdict(job) if job else None

    @classmethod
    def list(cls, limit: int = 100) -> builtins.list[dict[str, Any]]:
        """List jobs sorted by creation date desc."""
        with cls._lock:
            jobs = list(cls._jobs.values())
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return [asdict(job) for job in jobs[:limit]]

    @classmethod
    def clear(cls) -> int:
        """Clear all jobs and return number of removed records."""
        with cls._lock:
            count = len(cls._jobs)
            cls._jobs.clear()
        return count
