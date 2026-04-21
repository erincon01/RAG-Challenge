"""Background ingestion orchestration endpoints."""

from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator

from app.core.capabilities import normalize_source
from app.core.dependencies import IngestionSvc
from app.services.job_service import JobService

router = APIRouter()


def _normalize_datasets(values: list[str]) -> list[str]:
    allowed = {"matches", "lineups", "events"}
    normalized = [v.lower().strip() for v in values]
    invalid = [v for v in normalized if v not in allowed]
    if invalid:
        raise ValueError(f"Unsupported dataset(s): {', '.join(invalid)}")
    # Preserve order while de-duplicating
    unique: list[str] = []
    for item in normalized:
        if item not in unique:
            unique.append(item)
    return unique


class JobCreateResponse(BaseModel):
    job_id: str
    status: str
    type: str


class JobListResponse(BaseModel):
    items: list[dict[str, Any]]


class ClearJobsResponse(BaseModel):
    removed_jobs: int


class DownloadRequest(BaseModel):
    datasets: list[str] = Field(
        default_factory=lambda: ["matches", "lineups", "events"]
    )
    match_ids: list[int] = Field(default_factory=list)
    competition_id: int | None = None
    season_id: int | None = None
    overwrite: bool = False

    @field_validator("datasets")
    @classmethod
    def validate_datasets(cls, values: list[str]) -> list[str]:
        return _normalize_datasets(values)


class DownloadCleanupRequest(BaseModel):
    datasets: list[str] = Field(
        default_factory=lambda: ["matches", "lineups", "events"]
    )
    match_ids: list[int] = Field(default_factory=list)
    competition_id: int | None = None
    season_id: int | None = None
    delete_all: bool = False

    @field_validator("datasets")
    @classmethod
    def validate_datasets(cls, values: list[str]) -> list[str]:
        return _normalize_datasets(values)


class DownloadCleanupResponse(BaseModel):
    deleted_count: int
    deleted_files: list[str]
    deleted_dirs: list[str]
    filters: dict[str, Any]


class LoadRequest(BaseModel):
    source: str = "postgres"
    datasets: list[str] = Field(default_factory=lambda: ["matches", "events"])
    match_ids: list[int] = Field(default_factory=list)

    @field_validator("source")
    @classmethod
    def validate_source(cls, value: str) -> str:
        return normalize_source(value)


class AggregateRequest(BaseModel):
    source: str = "postgres"
    match_ids: list[int] = Field(default_factory=list)

    @field_validator("source")
    @classmethod
    def validate_source(cls, value: str) -> str:
        return normalize_source(value)


class EmbeddingsRebuildRequest(BaseModel):
    source: str = "postgres"
    match_ids: list[int] = Field(default_factory=list)
    embedding_models: list[str] | None = None

    @field_validator("source")
    @classmethod
    def validate_source(cls, value: str) -> str:
        return normalize_source(value)


class SummariesGenerateRequest(BaseModel):
    source: str = "postgres"
    match_ids: list[int] = Field(default_factory=list)
    language: str = "english"

    @field_validator("source")
    @classmethod
    def validate_source(cls, value: str) -> str:
        return normalize_source(value)


class FullPipelineRequest(BaseModel):
    source: str = "postgres"
    match_ids: list[int] = Field(default_factory=list)
    competition_id: int | None = None
    season_id: int | None = None
    datasets: list[str] = Field(
        default_factory=lambda: ["matches", "lineups", "events"]
    )
    language: str = "english"
    embedding_models: list[str] | None = None
    overwrite: bool = False

    @field_validator("source")
    @classmethod
    def validate_source(cls, value: str) -> str:
        return normalize_source(value)

    @field_validator("datasets")
    @classmethod
    def validate_datasets(cls, values: list[str]) -> list[str]:
        return _normalize_datasets(values)


def _create_background_job(
    background_tasks: BackgroundTasks,
    *,
    job_type: str,
    payload: dict[str, Any],
    source: str | None,
    runner,
) -> JobCreateResponse:
    job = JobService.create_job(job_type=job_type, payload=payload, source=source)
    background_tasks.add_task(runner, job.id, payload)
    return JobCreateResponse(job_id=job.id, status=job.status, type=job.type)


@router.post(
    "/ingestion/download",
    response_model=JobCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create StatsBomb download job",
)
async def start_download_job(
    request: DownloadRequest,
    background_tasks: BackgroundTasks,
    service: IngestionSvc,
) -> JobCreateResponse:
    if not request.match_ids and (
        request.competition_id is None or request.season_id is None
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide match_ids or both competition_id and season_id",
        )

    payload = request.model_dump()
    return _create_background_job(
        background_tasks,
        job_type="download",
        payload=payload,
        source=None,
        runner=service.run_download_job,
    )


@router.post(
    "/ingestion/download/cleanup",
    response_model=DownloadCleanupResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete downloaded files by filters or entirely",
)
async def cleanup_downloaded_files(
    request: DownloadCleanupRequest,
    service: IngestionSvc,
) -> DownloadCleanupResponse:
    try:
        result = service.clear_downloaded_files(
            datasets=request.datasets,
            match_ids=request.match_ids,
            competition_id=request.competition_id,
            season_id=request.season_id,
            delete_all=request.delete_all,
        )
        return DownloadCleanupResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup downloaded files: {e}",
        )


@router.post(
    "/ingestion/load",
    response_model=JobCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create database load job",
)
async def start_load_job(
    request: LoadRequest,
    background_tasks: BackgroundTasks,
    service: IngestionSvc,
) -> JobCreateResponse:
    payload = request.model_dump()
    return _create_background_job(
        background_tasks,
        job_type="load",
        payload=payload,
        source=request.source,
        runner=service.run_load_job,
    )


@router.post(
    "/ingestion/aggregate",
    response_model=JobCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create aggregation build job",
)
async def start_aggregate_job(
    request: AggregateRequest,
    background_tasks: BackgroundTasks,
    service: IngestionSvc,
) -> JobCreateResponse:
    payload = request.model_dump()
    return _create_background_job(
        background_tasks,
        job_type="aggregate",
        payload=payload,
        source=request.source,
        runner=service.run_aggregate_job,
    )


@router.post(
    "/ingestion/embeddings/rebuild",
    response_model=JobCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create embeddings rebuild job",
)
async def start_rebuild_embeddings_job(
    request: EmbeddingsRebuildRequest,
    background_tasks: BackgroundTasks,
    service: IngestionSvc,
) -> JobCreateResponse:
    payload = request.model_dump()
    return _create_background_job(
        background_tasks,
        job_type="embeddings_rebuild",
        payload=payload,
        source=request.source,
        runner=service.run_rebuild_embeddings_job,
    )


@router.post(
    "/ingestion/summaries/generate",
    response_model=JobCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create summary generation job",
)
async def start_generate_summaries_job(
    request: SummariesGenerateRequest,
    background_tasks: BackgroundTasks,
    service: IngestionSvc,
) -> JobCreateResponse:
    payload = request.model_dump()
    return _create_background_job(
        background_tasks,
        job_type="summaries_generate",
        payload=payload,
        source=request.source,
        runner=service.run_generate_summaries_job,
    )


@router.post(
    "/ingestion/full-pipeline",
    response_model=JobCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Run full ingestion pipeline (download→load→aggregate→summaries→embeddings)",
)
async def start_full_pipeline_job(
    request: FullPipelineRequest,
    background_tasks: BackgroundTasks,
    service: IngestionSvc,
) -> JobCreateResponse:
    if not request.match_ids and (
        request.competition_id is None or request.season_id is None
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide match_ids or both competition_id and season_id",
        )

    payload = request.model_dump()
    return _create_background_job(
        background_tasks,
        job_type="full_pipeline",
        payload=payload,
        source=request.source,
        runner=service.run_full_pipeline_job,
    )


@router.get(
    "/ingestion/pipeline-status",
    status_code=status.HTTP_200_OK,
    summary="Get per-match pipeline status",
)
async def get_pipeline_status(
    service: IngestionSvc,
    source: str = Query(default="postgres"),
) -> list[dict]:
    src = normalize_source(source)
    return service.get_pipeline_status(src)


@router.get(
    "/ingestion/jobs",
    response_model=JobListResponse,
    status_code=status.HTTP_200_OK,
    summary="List ingestion jobs",
)
async def list_jobs(
    limit: int = Query(default=100, ge=1, le=500),
) -> JobListResponse:
    return JobListResponse(items=JobService.list(limit=limit))


@router.delete(
    "/ingestion/jobs",
    response_model=ClearJobsResponse,
    status_code=status.HTTP_200_OK,
    summary="Clear ingestion jobs",
)
async def clear_jobs() -> ClearJobsResponse:
    removed = JobService.clear()
    return ClearJobsResponse(removed_jobs=removed)


@router.get(
    "/ingestion/jobs/{job_id}",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get ingestion job",
)
async def get_job(job_id: str) -> dict[str, Any]:
    job = JobService.get(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )
    return job
