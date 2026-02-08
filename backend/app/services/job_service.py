"""In-memory job tracking for ingestion workflows."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from threading import Lock
from typing import Any, Dict, List, Optional
from uuid import uuid4


@dataclass
class JobRecord:
    """Job metadata and execution state."""

    id: str
    type: str
    status: str
    source: Optional[str]
    payload: Dict[str, Any]
    created_at: str
    updated_at: str
    progress: int
    total: int
    message: str
    error: Optional[str]
    result: Dict[str, Any]


class JobService:
    """Thread-safe in-memory registry for async/background jobs."""

    _jobs: Dict[str, JobRecord] = {}
    _lock = Lock()

    @classmethod
    def create_job(
        cls,
        job_type: str,
        payload: Dict[str, Any],
        source: Optional[str] = None,
    ) -> JobRecord:
        """Create a new job and return its record."""
        now = datetime.utcnow().isoformat()
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
        )
        with cls._lock:
            cls._jobs[job.id] = job
        return job

    @classmethod
    def update(
        cls,
        job_id: str,
        *,
        status: Optional[str] = None,
        progress: Optional[int] = None,
        total: Optional[int] = None,
        message: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update mutable fields of a job."""
        with cls._lock:
            job = cls._jobs.get(job_id)
            if not job:
                return
            if status is not None:
                job.status = status
            if progress is not None:
                job.progress = progress
            if total is not None:
                job.total = total
            if message is not None:
                job.message = message
            if result is not None:
                job.result = result
            job.updated_at = datetime.utcnow().isoformat()

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
            job.updated_at = datetime.utcnow().isoformat()

    @classmethod
    def complete(cls, job_id: str, result: Optional[Dict[str, Any]] = None) -> None:
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
            job.updated_at = datetime.utcnow().isoformat()

    @classmethod
    def get(cls, job_id: str) -> Optional[Dict[str, Any]]:
        """Get one job by id."""
        with cls._lock:
            job = cls._jobs.get(job_id)
            return asdict(job) if job else None

    @classmethod
    def list(cls, limit: int = 100) -> List[Dict[str, Any]]:
        """List jobs sorted by creation date desc."""
        with cls._lock:
            jobs = list(cls._jobs.values())
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return [asdict(job) for job in jobs[:limit]]
