"""
Unit tests for JobService — state machine, logging, thread safety.

No external dependencies.
"""

import threading
import time

import pytest

from app.services.job_service import JobService, JobRecord


@pytest.fixture(autouse=True)
def clear_jobs():
    """Ensure a clean state before and after every test."""
    JobService.clear()
    yield
    JobService.clear()


# ===========================================================================
# Job creation
# ===========================================================================

class TestJobCreation:
    def test_create_returns_job_record(self):
        job = JobService.create_job("download", {"match_ids": [1]})
        assert isinstance(job, JobRecord)
        assert job.type == "download"
        assert job.status == "pending"
        assert job.source is None
        assert job.progress == 0
        assert job.total == 0
        assert job.error is None

    def test_create_with_source(self):
        job = JobService.create_job("load", {}, source="postgres")
        assert job.source == "postgres"

    def test_create_generates_unique_ids(self):
        j1 = JobService.create_job("download", {})
        j2 = JobService.create_job("download", {})
        assert j1.id != j2.id

    def test_create_adds_initial_log(self):
        job = JobService.create_job("download", {})
        assert len(job.logs) >= 1
        assert "download" in job.logs[0].lower() or "created" in job.logs[0].lower()

    def test_created_job_is_retrievable(self):
        job = JobService.create_job("aggregate", {"source": "postgres"})
        retrieved = JobService.get(job.id)
        assert retrieved is not None
        assert retrieved["id"] == job.id


# ===========================================================================
# Status transitions
# ===========================================================================

class TestStatusTransitions:
    def test_update_status_to_running(self):
        job = JobService.create_job("download", {})
        JobService.update(job.id, status="running", message="Downloading...")
        data = JobService.get(job.id)
        assert data["status"] == "running"
        assert data["message"] == "Downloading..."

    def test_complete_sets_success(self):
        job = JobService.create_job("load", {})
        JobService.complete(job.id, result={"loaded": 10})
        data = JobService.get(job.id)
        assert data["status"] == "success"
        assert data["result"]["loaded"] == 10
        assert data["message"] == "Job completed"

    def test_complete_fills_progress_to_total(self):
        job = JobService.create_job("load", {})
        JobService.update(job.id, total=100, progress=50)
        JobService.complete(job.id)
        data = JobService.get(job.id)
        assert data["progress"] == data["total"]

    def test_fail_sets_error_state(self):
        job = JobService.create_job("aggregate", {})
        JobService.fail(job.id, "Connection refused")
        data = JobService.get(job.id)
        assert data["status"] == "error"
        assert data["error"] == "Connection refused"
        assert data["message"] == "Job failed"

    def test_update_progress_and_total(self):
        job = JobService.create_job("download", {})
        JobService.update(job.id, progress=5, total=20)
        data = JobService.get(job.id)
        assert data["progress"] == 5
        assert data["total"] == 20

    def test_update_nonexistent_job_does_not_raise(self):
        JobService.update("nonexistent-id", status="running")  # no exception

    def test_fail_nonexistent_job_does_not_raise(self):
        JobService.fail("nonexistent-id", "error")  # no exception

    def test_complete_nonexistent_job_does_not_raise(self):
        JobService.complete("nonexistent-id")  # no exception

    def test_status_change_appends_log(self):
        job = JobService.create_job("download", {})
        initial_log_count = len(job.logs)
        JobService.update(job.id, status="running")
        data = JobService.get(job.id)
        assert len(data["logs"]) > initial_log_count


# ===========================================================================
# Logging
# ===========================================================================

class TestJobLogging:
    def test_log_appends_message(self):
        job = JobService.create_job("download", {})
        JobService.log(job.id, "Processing match 123")
        data = JobService.get(job.id)
        assert any("Processing match 123" in line for line in data["logs"])

    def test_log_includes_timestamp(self):
        job = JobService.create_job("download", {})
        JobService.log(job.id, "test message")
        data = JobService.get(job.id)
        last_log = data["logs"][-1]
        assert "[" in last_log and "]" in last_log  # ISO timestamp wrapper

    def test_log_nonexistent_job_does_not_raise(self):
        JobService.log("nonexistent-id", "some message")

    def test_log_truncates_at_max(self):
        job = JobService.create_job("download", {})
        for i in range(JobService._max_logs + 50):
            JobService.log(job.id, f"line {i}")
        data = JobService.get(job.id)
        assert len(data["logs"]) <= JobService._max_logs

    def test_fail_appends_error_to_logs(self):
        job = JobService.create_job("load", {})
        JobService.fail(job.id, "Timeout after 30s")
        data = JobService.get(job.id)
        assert any("Timeout after 30s" in line for line in data["logs"])


# ===========================================================================
# List and retrieval
# ===========================================================================

class TestJobListAndGet:
    def test_get_returns_none_for_missing(self):
        result = JobService.get("does-not-exist")
        assert result is None

    def test_get_returns_dict(self):
        job = JobService.create_job("download", {})
        data = JobService.get(job.id)
        assert isinstance(data, dict)
        assert data["id"] == job.id

    def test_list_returns_all_jobs(self):
        JobService.create_job("download", {})
        JobService.create_job("load", {})
        JobService.create_job("aggregate", {})
        jobs = JobService.list()
        assert len(jobs) == 3

    def test_list_sorted_desc_by_created_at(self):
        j1 = JobService.create_job("download", {})
        time.sleep(0.01)  # ensure different timestamp
        j2 = JobService.create_job("load", {})
        jobs = JobService.list()
        ids = [j["id"] for j in jobs]
        assert ids[0] == j2.id
        assert ids[1] == j1.id

    def test_list_respects_limit(self):
        for _ in range(10):
            JobService.create_job("download", {})
        jobs = JobService.list(limit=3)
        assert len(jobs) == 3

    def test_list_empty_when_no_jobs(self):
        assert JobService.list() == []


# ===========================================================================
# Clear
# ===========================================================================

class TestJobClear:
    def test_clear_returns_count(self):
        JobService.create_job("download", {})
        JobService.create_job("load", {})
        count = JobService.clear()
        assert count == 2

    def test_clear_removes_all_jobs(self):
        JobService.create_job("download", {})
        JobService.clear()
        assert JobService.list() == []

    def test_clear_empty_returns_zero(self):
        assert JobService.clear() == 0


# ===========================================================================
# Thread safety
# ===========================================================================

class TestJobServiceThreadSafety:
    def test_concurrent_job_creation(self):
        results = []

        def create():
            job = JobService.create_job("download", {})
            results.append(job.id)

        threads = [threading.Thread(target=create) for _ in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 50
        assert len(set(results)) == 50  # all IDs unique
        assert len(JobService.list(limit=100)) == 50

    def test_concurrent_updates_no_errors(self):
        job = JobService.create_job("download", {})
        errors = []

        def update_progress(i):
            try:
                JobService.update(job.id, progress=i)
                JobService.log(job.id, f"step {i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=update_progress, args=(i,)) for i in range(30)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Unexpected errors in concurrent updates: {errors}"

    def test_concurrent_complete_and_log(self):
        job = JobService.create_job("load", {})
        errors = []

        def work(i):
            try:
                JobService.log(job.id, f"Processing item {i}")
                if i == 25:
                    JobService.complete(job.id)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=work, args=(i,)) for i in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
