"""Ingestion workflows: download, load, aggregate and embeddings rebuild."""

from __future__ import annotations

import json
import shutil
from collections.abc import Iterable
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Optional

import psycopg2
import pyodbc

from app.adapters.openai_client import OpenAIAdapter
from app.core.capabilities import normalize_source
from app.core.config import get_settings
from app.services.job_service import JobService
from app.services.statsbomb_service import StatsBombService


class IngestionService:
    """Service implementing end-to-end ingestion tasks."""

    def __init__(self, statsbomb: Optional[StatsBombService] = None):
        self.settings = get_settings()
        self.statsbomb = statsbomb if statsbomb is not None else StatsBombService()
        self.local_folder = Path(self.settings.repository.local_folder)
        self._prompt_template_cache: Optional[str] = None

    def _load_prompt_template(self) -> str:
        """Load and cache the event-summary prompt template from disk.

        The template lives at ``app/services/prompts/event_summary.md`` and uses
        ``str.format()`` placeholders. It is loaded once and memoized on the
        service instance so repeated summary generation does not hit the
        filesystem.
        """
        if self._prompt_template_cache is not None:
            return self._prompt_template_cache
        template_path = Path(__file__).resolve().parent / "prompts" / "event_summary.md"
        self._prompt_template_cache = template_path.read_text(encoding="utf-8")
        return self._prompt_template_cache

    @staticmethod
    def _safe_unlink(path: Path) -> bool:
        try:
            if path.exists() and path.is_file():
                path.unlink()
                return True
        except Exception:
            return False
        return False

    @staticmethod
    def _prune_empty_dirs(path: Path, stop_at: Path) -> None:
        current = path
        while current != stop_at and current.exists() and current.is_dir():
            if any(current.iterdir()):
                break
            current.rmdir()
            current = current.parent

    @staticmethod
    def _parse_match_ids(match_ids: list[int] | None) -> list[int]:
        if not match_ids:
            return []
        return sorted({int(v) for v in match_ids})

    def clear_downloaded_files(
        self,
        *,
        datasets: list[str],
        match_ids: list[int] | None = None,
        competition_id: int | None = None,
        season_id: int | None = None,
        delete_all: bool = False,
    ) -> dict[str, Any]:
        selected = [d.lower() for d in (datasets or ["matches", "lineups", "events"])]
        allowed = {"matches", "lineups", "events"}
        normalized = [d for d in selected if d in allowed]
        if not normalized:
            raise ValueError("At least one valid dataset is required")

        target_match_ids = self._parse_match_ids(match_ids)
        if competition_id is not None and season_id is not None:
            resolved = self.statsbomb.resolve_match_ids(
                match_ids=None,
                competition_id=competition_id,
                season_id=season_id,
            )
            target_match_ids = sorted(set(target_match_ids).union(set(resolved)))

        deleted_files: list[str] = []
        deleted_dirs: list[str] = []

        if delete_all:
            for dataset in normalized:
                root = self.local_folder / dataset
                if root.exists() and root.is_dir():
                    shutil.rmtree(root)
                    deleted_dirs.append(str(root))
            competitions_file = self.local_folder / "competitions.json"
            if competitions_file.exists() and self._safe_unlink(competitions_file):
                deleted_files.append(str(competitions_file))
            return {
                "deleted_count": len(deleted_files) + len(deleted_dirs),
                "deleted_files": deleted_files,
                "deleted_dirs": deleted_dirs,
                "filters": {
                    "datasets": normalized,
                    "match_ids": target_match_ids,
                    "competition_id": competition_id,
                    "season_id": season_id,
                    "delete_all": True,
                },
            }

        for dataset in normalized:
            if dataset in {"events", "lineups"}:
                root = self.local_folder / dataset
                if not root.exists():
                    continue

                if target_match_ids:
                    for match_id in target_match_ids:
                        file_path = root / f"{match_id}.json"
                        if self._safe_unlink(file_path):
                            deleted_files.append(str(file_path))
                else:
                    for file_path in root.glob("*.json"):
                        if self._safe_unlink(file_path):
                            deleted_files.append(str(file_path))

            if dataset == "matches":
                root = self.local_folder / "matches"
                if not root.exists():
                    continue

                if competition_id is not None and season_id is not None:
                    file_path = root / str(competition_id) / f"{season_id}.json"
                    if self._safe_unlink(file_path):
                        deleted_files.append(str(file_path))
                        self._prune_empty_dirs(file_path.parent, root)
                else:
                    for file_path in root.glob("**/*.json"):
                        if self._safe_unlink(file_path):
                            deleted_files.append(str(file_path))

        for dataset in normalized:
            root = self.local_folder / dataset
            if root.exists() and root.is_dir() and not any(root.iterdir()):
                root.rmdir()
                deleted_dirs.append(str(root))

        return {
            "deleted_count": len(deleted_files) + len(deleted_dirs),
            "deleted_files": deleted_files,
            "deleted_dirs": deleted_dirs,
            "filters": {
                "datasets": normalized,
                "match_ids": target_match_ids,
                "competition_id": competition_id,
                "season_id": season_id,
                "delete_all": False,
            },
        }

    @contextmanager
    def _get_connection(self, source: str):
        src = normalize_source(source)
        conn = None
        try:
            if src == "postgres":
                conn = psycopg2.connect(
                    host=self.settings.database.postgres_host,
                    database=self.settings.database.postgres_database,
                    user=self.settings.database.postgres_user,
                    password=self.settings.database.postgres_password,
                )
            elif src == "sqlserver":
                conn = pyodbc.connect(
                    "DRIVER={ODBC Driver 18 for SQL Server};"
                    f"SERVER={self.settings.database.sqlserver_host};"
                    f"DATABASE={self.settings.database.sqlserver_database};"
                    f"UID={self.settings.database.sqlserver_user};"
                    f"PWD={self.settings.database.sqlserver_password};"
                    "TrustServerCertificate=yes;"
                )
            else:
                raise ValueError(f"Unsupported source: {source}")
            yield conn
            conn.commit()
        except Exception:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def run_download_job(self, job_id: str, payload: dict[str, Any]) -> None:
        try:
            JobService.update(job_id, status="running", message="Resolving matches")
            datasets = [
                d.lower()
                for d in (payload.get("datasets") or ["matches", "lineups", "events"])
            ]
            match_ids = payload.get("match_ids") or []
            competition_id = payload.get("competition_id")
            season_id = payload.get("season_id")
            overwrite = bool(payload.get("overwrite", False))

            resolved_match_ids = self.statsbomb.resolve_match_ids(
                match_ids=match_ids,
                competition_id=competition_id,
                season_id=season_id,
            )

            total = (
                1
                if "matches" in datasets
                and competition_id is not None
                and season_id is not None
                else 0
            )
            total += len(resolved_match_ids) * len(
                [d for d in datasets if d in {"lineups", "events"}]
            )
            JobService.update(job_id, total=total, message="Downloading datasets")

            progress = 0
            files: list[str] = []
            if (
                "matches" in datasets
                and competition_id is not None
                and season_id is not None
            ):
                file_path = self.statsbomb.download_matches_catalog(
                    competition_id, season_id, overwrite
                )
                files.append(str(file_path))
                progress += 1
                JobService.update(
                    job_id, progress=progress, message=f"Downloaded {file_path.name}"
                )

            for match_id in resolved_match_ids:
                for dataset in [d for d in datasets if d in {"lineups", "events"}]:
                    file_path = self.statsbomb.download_match_file(
                        dataset, match_id, overwrite
                    )
                    files.append(str(file_path))
                    progress += 1
                    JobService.update(
                        job_id,
                        progress=progress,
                        message=f"Downloaded {dataset}/{match_id}.json",
                    )

            JobService.complete(
                job_id, {"match_ids": resolved_match_ids, "downloaded_files": files}
            )
        except Exception as e:
            JobService.fail(job_id, str(e))

    def run_load_job(self, job_id: str, payload: dict[str, Any]) -> None:
        source = normalize_source(payload.get("source", "postgres"))
        datasets = [
            d.lower() for d in (payload.get("datasets") or ["matches", "events"])
        ]
        match_ids = [int(v) for v in (payload.get("match_ids") or [])]
        try:
            JobService.update(
                job_id,
                status="running",
                total=len(datasets),
                message=f"Loading into {source}",
            )
            JobService.log(job_id, f"$ connect --source {source}")
            JobService.log(job_id, "$ load --datasets " + ",".join(datasets))
            if match_ids:
                JobService.log(
                    job_id, "$ filter --match-ids " + ",".join(map(str, match_ids))
                )

            result: dict[str, Any] = {}
            progress = 0
            with self._get_connection(source) as conn:
                if "matches" in datasets:
                    JobService.log(job_id, "$ execute load_matches")
                    result["matches"] = self._load_matches(conn, source, match_ids)
                    progress += 1
                    JobService.update(
                        job_id, progress=progress, message="Loaded matches"
                    )
                if "events" in datasets:
                    JobService.log(job_id, "$ execute load_events")
                    result["events"] = self._load_events(conn, source, match_ids)
                    progress += 1
                    JobService.update(
                        job_id, progress=progress, message="Loaded events"
                    )
                if "lineups" in datasets:
                    JobService.log(
                        job_id, "$ execute load_lineups (pending implementation)"
                    )
                    result["lineups"] = {
                        "skipped": True,
                        "reason": "lineups load pending",
                    }
                    progress += 1
                    JobService.update(
                        job_id, progress=progress, message="Skipped lineups (pending)"
                    )
            JobService.complete(job_id, result)
        except Exception as e:
            JobService.fail(job_id, str(e))

    def run_aggregate_job(self, job_id: str, payload: dict[str, Any]) -> None:
        source = normalize_source(payload.get("source", "postgres"))
        match_ids = [int(v) for v in (payload.get("match_ids") or [])]
        try:
            JobService.update(
                job_id,
                status="running",
                total=1,
                message=f"Building aggregations in {source}",
            )
            JobService.log(job_id, f"$ connect --source {source}")
            if match_ids:
                JobService.log(
                    job_id, "$ aggregate --match-ids " + ",".join(map(str, match_ids))
                )
            else:
                JobService.log(job_id, "$ aggregate --all-matches")
            with self._get_connection(source) as conn:
                rows = self._build_aggregations(conn, source, match_ids)
            JobService.update(job_id, progress=1, message="Aggregation build completed")
            JobService.complete(job_id, {"aggregated_rows": rows, "source": source})
        except Exception as e:
            JobService.fail(job_id, str(e))

    def run_rebuild_embeddings_job(self, job_id: str, payload: dict[str, Any]) -> None:
        source = normalize_source(payload.get("source", "postgres"))
        match_ids = [int(v) for v in (payload.get("match_ids") or [])]
        defaults = {
            "postgres": ["text-embedding-3-small"],
            "sqlserver": ["text-embedding-3-small"],
        }
        models = payload.get("embedding_models") or defaults[source]
        try:
            JobService.update(
                job_id, status="running", message=f"Rebuilding embeddings in {source}"
            )
            JobService.log(job_id, f"$ connect --source {source}")
            JobService.log(job_id, "$ embeddings --models " + ",".join(models))
            if match_ids:
                JobService.log(
                    job_id, "$ embeddings --match-ids " + ",".join(map(str, match_ids))
                )

            adapter = OpenAIAdapter()
            with self._get_connection(source) as conn:
                rows = self._fetch_summary_rows(conn, source, match_ids)
                JobService.update(
                    job_id,
                    total=len(rows),
                    message=f"Preparing {len(rows)} rows for embeddings",
                )
                updated = 0
                for idx, (row_id, summary) in enumerate(rows, start=1):
                    if not summary:
                        continue
                    self._update_embeddings_for_row(
                        conn, source, row_id, summary, models, adapter
                    )
                    updated += 1
                    if idx % 25 == 0 or idx == len(rows):
                        # Commit every 25 rows so progress is durable
                        conn.commit()
                        JobService.log(
                            job_id, f"$ embeddings progress {idx}/{len(rows)}"
                        )
                    JobService.update(
                        job_id, progress=idx, message=f"Embedded row {idx}/{len(rows)}"
                    )
            JobService.complete(
                job_id,
                {"updated_rows": updated, "source": source, "embedding_models": models},
            )
        except Exception as e:
            JobService.fail(job_id, str(e))

    def get_pipeline_status(self, source: str) -> list[dict[str, Any]]:
        """Return per-match pipeline state: events, aggregations, summaries, embeddings counts."""
        src = normalize_source(source)
        with self._get_connection(src) as conn:
            cur = conn.cursor()
            if src == "postgres":
                cur.execute(
                    """
                    SELECT m.match_id,
                           m.home_team_name || ' (' || m.home_score || ') - ' || m.away_team_name || ' (' || m.away_score || ')' AS display_name,
                           (SELECT COUNT(*) FROM events_details ed WHERE ed.match_id = m.match_id) AS events_count,
                           (SELECT COUNT(*) FROM events_details__quarter_minute a WHERE a.match_id = m.match_id) AS agg_count,
                           (SELECT COUNT(*) FROM events_details__quarter_minute a WHERE a.match_id = m.match_id AND a.summary IS NOT NULL) AS summary_count,
                           (SELECT COUNT(*) FROM events_details__quarter_minute a WHERE a.match_id = m.match_id AND a.summary_embedding_t3_small IS NOT NULL) AS embedding_count
                    FROM matches m
                    ORDER BY m.match_id
                    """
                )
            else:
                cur.execute(
                    """
                    SELECT m.match_id,
                           m.home_team_name + ' (' + CAST(m.home_score AS VARCHAR) + ') - ' + m.away_team_name + ' (' + CAST(m.away_score AS VARCHAR) + ')' AS display_name,
                           (SELECT COUNT(*) FROM events_details ed WHERE ed.match_id = m.match_id) AS events_count,
                           (SELECT COUNT(*) FROM events_details__15secs_agg a WHERE a.match_id = m.match_id) AS agg_count,
                           (SELECT COUNT(*) FROM events_details__15secs_agg a WHERE a.match_id = m.match_id AND a.summary IS NOT NULL) AS summary_count,
                           (SELECT COUNT(*) FROM events_details__15secs_agg a WHERE a.match_id = m.match_id AND a.embedding_3_small IS NOT NULL) AS embedding_count
                    FROM matches m
                    ORDER BY m.match_id
                    """
                )
            return [
                {
                    "match_id": int(row[0]),
                    "display_name": row[1] or "",
                    "events_count": int(row[2] or 0),
                    "agg_count": int(row[3] or 0),
                    "summary_count": int(row[4] or 0),
                    "embedding_count": int(row[5] or 0),
                }
                for row in cur.fetchall()
            ]

    def get_embeddings_status(self, source: str) -> dict[str, Any]:
        src = normalize_source(source)
        with self._get_connection(src) as conn:
            cur = conn.cursor()
            if src == "postgres":
                cur.execute(
                    """
                    SELECT COUNT(*),
                           SUM(CASE WHEN summary_embedding_t3_small IS NOT NULL THEN 1 ELSE 0 END),
                           SUM(CASE WHEN embedding_status = 'done' THEN 1 ELSE 0 END),
                           SUM(CASE WHEN embedding_status = 'error' THEN 1 ELSE 0 END),
                           SUM(CASE WHEN embedding_status = 'pending' OR embedding_status IS NULL THEN 1 ELSE 0 END)
                    FROM events_details__quarter_minute
                    """
                )
                row = cur.fetchone()
                return {
                    "source": "postgres",
                    "table": "events_details__quarter_minute",
                    "total_rows": int(row[0] or 0),
                    "coverage": {
                        "text-embedding-3-small": int(row[1] or 0),
                    },
                    "status": {
                        "done": int(row[2] or 0),
                        "error": int(row[3] or 0),
                        "pending": int(row[4] or 0),
                    },
                }

            cur.execute(
                """
                SELECT COUNT(*),
                       SUM(CASE WHEN embedding_3_small IS NOT NULL THEN 1 ELSE 0 END),
                       SUM(CASE WHEN embedding_status = 'done' THEN 1 ELSE 0 END),
                       SUM(CASE WHEN embedding_status = 'error' THEN 1 ELSE 0 END),
                       SUM(CASE WHEN embedding_status = 'pending' OR embedding_status IS NULL THEN 1 ELSE 0 END)
                FROM events_details__15secs_agg
                """
            )
            row = cur.fetchone()
            return {
                "source": "sqlserver",
                "table": "events_details__15secs_agg",
                "total_rows": int(row[0] or 0),
                "coverage": {
                    "text-embedding-3-small": int(row[1] or 0),
                },
                "status": {
                    "done": int(row[2] or 0),
                    "error": int(row[3] or 0),
                    "pending": int(row[4] or 0),
                },
            }

    def _iter_matches_from_local(self) -> Iterable[dict[str, Any]]:
        matches_root = self.local_folder / "matches"
        if not matches_root.exists():
            return
        for file_path in sorted(matches_root.glob("**/*.json")):
            try:
                with file_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get("match_id") is not None:
                            yield item
            except Exception:
                continue

    def _fetch_summary_rows(
        self, conn, source: str, match_ids: list[int]
    ) -> list[tuple[int, str]]:
        cur = conn.cursor()
        if source == "postgres":
            if match_ids:
                cur.execute(
                    """
                    SELECT id, summary
                    FROM events_details__quarter_minute
                    WHERE summary IS NOT NULL AND match_id = ANY(%s)
                    ORDER BY id
                    """,
                    (match_ids,),
                )
            else:
                cur.execute(
                    "SELECT id, summary FROM events_details__quarter_minute WHERE summary IS NOT NULL ORDER BY id"
                )
            return [(int(r[0]), r[1]) for r in cur.fetchall()]

        if match_ids:
            placeholders = ",".join("?" for _ in match_ids)
            cur.execute(
                f"SELECT id, summary FROM events_details__15secs_agg WHERE summary IS NOT NULL AND match_id IN ({placeholders}) ORDER BY id",
                match_ids,
            )
        else:
            cur.execute(
                "SELECT id, summary FROM events_details__15secs_agg WHERE summary IS NOT NULL ORDER BY id"
            )
        return [(int(r[0]), r[1]) for r in cur.fetchall()]

    def _fetch_aggregation_rows_for_summary(
        self, conn, source: str, match_ids: list[int]
    ) -> list[tuple[int, int, int, int, str]]:
        """Fetch rows from the aggregation table whose ``summary`` is NULL.

        Returns a list of tuples ``(id, period, minute, quarter_minute,
        events_json)`` ready to be fed to the prompt template. Only rows with
        ``summary IS NULL`` are returned so the job is resumable — re-running
        it after a partial failure only processes the remaining rows.

        Note: ``match_id`` is not returned here to keep the tuple shape small
        and stable. Callers that need it should fetch it via
        ``_fetch_match_id_by_row_id`` or include it in a custom query.
        """
        cur = conn.cursor()
        if source == "postgres":
            if match_ids:
                cur.execute(
                    """
                    SELECT id, period, minute, quarter_minute, json_
                    FROM events_details__quarter_minute
                    WHERE summary IS NULL AND match_id = ANY(%s)
                    ORDER BY id
                    """,
                    (match_ids,),
                )
            else:
                cur.execute(
                    """
                    SELECT id, period, minute, quarter_minute, json_
                    FROM events_details__quarter_minute
                    WHERE summary IS NULL
                    ORDER BY id
                    """
                )
            return [
                (int(r[0]), int(r[1] or 0), int(r[2] or 0), int(r[3] or 0), r[4] or "")
                for r in cur.fetchall()
            ]

        # SQL Server
        if match_ids:
            placeholders = ",".join("?" for _ in match_ids)
            cur.execute(
                f"""
                SELECT id, period, minute, _15secs, json_
                FROM events_details__15secs_agg
                WHERE summary IS NULL AND match_id IN ({placeholders})
                ORDER BY id
                """,
                match_ids,
            )
        else:
            cur.execute(
                """
                SELECT id, period, minute, _15secs, json_
                FROM events_details__15secs_agg
                WHERE summary IS NULL
                ORDER BY id
                """
            )
        return [
            (int(r[0]), int(r[1] or 0), int(r[2] or 0), int(r[3] or 0), r[4] or "")
            for r in cur.fetchall()
        ]

    def _update_summary_for_row(
        self, conn, source: str, row_id: int, summary: str
    ) -> None:
        """Write a generated summary back to the aggregation table."""
        cur = conn.cursor()
        if source == "postgres":
            cur.execute(
                "UPDATE events_details__quarter_minute SET summary = %s WHERE id = %s",
                (summary, row_id),
            )
            return
        cur.execute(
            "UPDATE events_details__15secs_agg SET summary = ? WHERE id = ?",
            (summary, row_id),
        )

    def run_full_pipeline_job(self, job_id: str, payload: dict[str, Any]) -> None:
        """Orchestrate the full ingestion pipeline as a single job.

        Runs the 5 stages in order:
        ``download → load → aggregate → summaries → embeddings``.

        Each stage is invoked with the orchestrator's ``job_id`` so its
        existing ``JobService.update()`` / ``complete()`` / ``fail()``
        calls feed progress into the same job record. Between stages, the
        orchestrator re-sets status to ``running`` (overriding the
        ``success`` set by the previous stage's ``complete`` call) and
        checks for ``error`` status to abort early.

        If any stage raises, the orchestrator marks the job as failed and
        does NOT run subsequent stages.
        """
        stages = [
            ("download", self.run_download_job),
            ("load", self.run_load_job),
            ("aggregate", self.run_aggregate_job),
            ("summaries", self.run_generate_summaries_job),
            ("embeddings", self.run_rebuild_embeddings_job),
        ]
        try:
            JobService.update(
                job_id,
                status="running",
                total=len(stages),
                message="Running full pipeline",
            )
            for idx, (stage_name, runner) in enumerate(stages, start=1):
                JobService.log(job_id, f"$ pipeline stage {stage_name} starting")
                try:
                    runner(job_id, payload)
                except Exception as e:
                    JobService.fail(job_id, f"{stage_name} raised: {e}")
                    return
                current = JobService.get(job_id)
                if current and current.get("status") == "error":
                    return  # sub-stage already called fail
                JobService.update(
                    job_id,
                    status="running",
                    progress=idx,
                    message=f"Stage {stage_name} completed",
                )
            JobService.complete(job_id, {"stages_completed": len(stages)})
        except Exception as e:
            JobService.fail(job_id, str(e))

    def _fetch_match_info_for_prompt(
        self, conn, source: str, match_ids: list[int]
    ) -> dict[int, dict[str, Any]]:
        """Fetch minimal match metadata needed to build the summary prompt.

        Returns a dict keyed by ``match_id`` with ``competition_name``,
        ``match_date``, ``home_team`` and ``away_team`` strings. Missing
        match_ids simply do not appear in the result.
        """
        if not match_ids:
            return {}
        cur = conn.cursor()
        if source == "postgres":
            cur.execute(
                """
                SELECT match_id, competition_name, match_date, home_team_name, away_team_name
                FROM matches
                WHERE match_id = ANY(%s)
                """,
                (match_ids,),
            )
        else:
            placeholders = ",".join("?" for _ in match_ids)
            cur.execute(
                f"""
                SELECT match_id, competition_name, match_date, home_team_name, away_team_name
                FROM matches
                WHERE match_id IN ({placeholders})
                """,
                match_ids,
            )
        result: dict[int, dict[str, Any]] = {}
        for row in cur.fetchall():
            result[int(row[0])] = {
                "competition_name": row[1] or "",
                "match_date": str(row[2]) if row[2] is not None else "",
                "home_team": row[3] or "",
                "away_team": row[4] or "",
            }
        return result

    def run_generate_summaries_job(self, job_id: str, payload: dict[str, Any]) -> None:
        """Populate ``summary`` for aggregation rows by calling the chat model.

        For each row in the aggregation table whose ``summary`` is NULL, build
        a prompt from the event-summary template, call
        ``OpenAIAdapter.create_chat_completion()``, strip the response, and
        UPDATE the row. Empty event buckets are skipped. Individual row
        failures are logged but do NOT abort the whole job — the job reports
        partial success via its ``result`` payload.
        """
        source = normalize_source(payload.get("source", "postgres"))
        match_ids = [int(v) for v in (payload.get("match_ids") or [])]
        language = payload.get("language") or "english"
        try:
            JobService.update(
                job_id,
                status="running",
                message=f"Generating summaries in {source}",
            )
            JobService.log(job_id, f"$ connect --source {source}")
            if match_ids:
                JobService.log(
                    job_id,
                    "$ summaries --match-ids " + ",".join(map(str, match_ids)),
                )
            else:
                JobService.log(job_id, "$ summaries --all-matches")

            template = self._load_prompt_template()
            adapter = OpenAIAdapter()
            updated = 0
            skipped = 0
            errored = 0
            with self._get_connection(source) as conn:
                match_info = self._fetch_match_info_for_prompt(conn, source, match_ids)
                rows = self._fetch_aggregation_rows_for_summary(conn, source, match_ids)
                JobService.update(
                    job_id,
                    total=len(rows),
                    message=f"Preparing {len(rows)} rows for summary generation",
                )
                # When the job targets a single match (the seed case), every row
                # belongs to that match and we can avoid a per-row match_id
                # lookup. When no match_ids are provided (bulk mode), the
                # prompt gets empty match_info placeholders — still valid, just
                # less context-rich.
                default_info: dict[str, Any] = {}
                if len(match_ids) == 1:
                    default_info = match_info.get(match_ids[0], {})
                for idx, (
                    row_id,
                    period,
                    minute,
                    quarter_minute,
                    events_json,
                ) in enumerate(rows, start=1):
                    if not events_json:
                        skipped += 1
                        JobService.update(
                            job_id,
                            progress=idx,
                            message=f"Skipped row {idx}/{len(rows)} (empty events)",
                        )
                        continue
                    info = default_info
                    try:
                        prompt = template.format(
                            language=language,
                            competition_name=info.get("competition_name", ""),
                            match_date=info.get("match_date", ""),
                            home_team=info.get("home_team", ""),
                            away_team=info.get("away_team", ""),
                            period=period,
                            minute=minute,
                            quarter_minute=quarter_minute,
                            events_json=events_json,
                        )
                        response = adapter.create_chat_completion(
                            messages=[
                                {
                                    "role": "system",
                                    "content": (
                                        "You are a football commentator producing "
                                        "factual, concise narration from event data."
                                    ),
                                },
                                {"role": "user", "content": prompt},
                            ],
                            temperature=0.2,
                            max_tokens=200,
                        )
                        summary = (response or "").strip()
                        if summary:
                            self._update_summary_for_row(conn, source, row_id, summary)
                            updated += 1
                    except Exception as e:
                        errored += 1
                        JobService.log(job_id, f"ERROR row {row_id}: {str(e)[:200]}")
                    if idx % 25 == 0 or idx == len(rows):
                        # Commit every 25 rows so progress is durable
                        conn.commit()
                        JobService.log(
                            job_id, f"$ summaries progress {idx}/{len(rows)}"
                        )
                    JobService.update(
                        job_id,
                        progress=idx,
                        message=f"Row {idx}/{len(rows)}",
                    )
            JobService.complete(
                job_id,
                {
                    "updated_rows": updated,
                    "skipped_rows": skipped,
                    "errored_rows": errored,
                    "source": source,
                },
            )
        except Exception as e:
            JobService.fail(job_id, str(e))

    def _load_matches(self, conn, source: str, match_ids: list[int]) -> dict[str, int]:
        inserted = 0
        seen: set[int] = set()
        cur = conn.cursor()

        for m in self._iter_matches_from_local():
            match_id = int(m["match_id"])
            if match_ids and match_id not in match_ids:
                continue
            if match_id in seen:
                continue
            seen.add(match_id)

            c = m.get("competition") or {}
            s = m.get("season") or {}
            ht = m.get("home_team") or {}
            at = m.get("away_team") or {}
            st = m.get("stadium") or {}
            rf = m.get("referee") or {}
            result = (
                f"{m.get('home_score')}-{m.get('away_score')}"
                if m.get("home_score") is not None
                else None
            )

            vals = [
                match_id,
                m.get("match_date"),
                c.get("competition_id"),
                c.get("country_name"),
                c.get("competition_name"),
                s.get("season_id"),
                s.get("season_name"),
                ht.get("home_team_id") or ht.get("id"),
                ht.get("home_team_name") or ht.get("name"),
                ht.get("home_team_gender") or ht.get("gender"),
                (ht.get("country") or {}).get("name"),
                None,
                None,
                at.get("away_team_id") or at.get("id"),
                at.get("away_team_name") or at.get("name"),
                at.get("away_team_gender") or at.get("gender"),
                (at.get("country") or {}).get("name"),
                None,
                None,
                m.get("home_score"),
                m.get("away_score"),
                result,
                m.get("match_week"),
                st.get("id"),
                st.get("name"),
                (st.get("country") or {}).get("name"),
                rf.get("id"),
                rf.get("name"),
                (rf.get("country") or {}).get("name"),
                json.dumps(m, ensure_ascii=False),
            ]

            if source == "postgres":
                cur.execute("DELETE FROM matches WHERE match_id = %s", (match_id,))
                ph = ",".join(["%s"] * 30)
            else:
                cur.execute("DELETE FROM matches WHERE match_id = ?", (match_id,))
                ph = ",".join(["?"] * 30)

            cur.execute(
                f"""
                INSERT INTO matches (
                    match_id, match_date,
                    competition_id, competition_country, competition_name,
                    season_id, season_name,
                    home_team_id, home_team_name, home_team_gender, home_team_country,
                    home_team_manager, home_team_manager_country,
                    away_team_id, away_team_name, away_team_gender, away_team_country,
                    away_team_manager, away_team_manager_country,
                    home_score, away_score, result, match_week,
                    stadium_id, stadium_name, stadium_country,
                    referee_id, referee_name, referee_country,
                    json_
                ) VALUES ({ph})
                """,
                vals,
            )
            inserted += 1

        return {"inserted": inserted}

    def _load_events(self, conn, source: str, match_ids: list[int]) -> dict[str, int]:
        events_inserted = 0
        details_inserted = 0
        cur = conn.cursor()

        for file_path in sorted((self.local_folder / "events").glob("*.json")):
            match_id = int(file_path.stem)
            if match_ids and match_id not in match_ids:
                continue

            with file_path.open("r", encoding="utf-8") as f:
                events = json.load(f)
            if not isinstance(events, list):
                continue

            if source == "postgres":
                cur.execute(
                    "DELETE FROM events_details WHERE match_id = %s", (match_id,)
                )
                cur.execute("DELETE FROM events WHERE match_id = %s", (match_id,))
                cur.execute(
                    "INSERT INTO events (match_id, json_) VALUES (%s, %s)",
                    (match_id, json.dumps(events, ensure_ascii=False)),
                )
                details_sql = """
                    INSERT INTO events_details (
                        match_id, id_guid, "index", period, timestamp, minute, second,
                        type_id, type, possession, possession_team_id, possession_team,
                        play_pattern_id, play_pattern, json_
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """
            else:
                cur.execute(
                    "DELETE FROM events_details WHERE match_id = ?", (match_id,)
                )
                cur.execute("DELETE FROM events WHERE match_id = ?", (match_id,))
                cur.execute(
                    "INSERT INTO events (match_id, json_) VALUES (?, ?)",
                    (match_id, json.dumps(events, ensure_ascii=False)),
                )
                details_sql = """
                    INSERT INTO events_details (
                        match_id, id_guid, index_, period, timestamp, minute, second,
                        type_id, type, possession, possession_team_id, possession_team,
                        play_pattern_id, play_pattern, json_
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """

            events_inserted += 1
            for e in events:
                et = e.get("type") or {}
                pt = e.get("possession_team") or {}
                pp = e.get("play_pattern") or {}
                vals = [
                    match_id,
                    e.get("id"),
                    e.get("index"),
                    e.get("period"),
                    e.get("timestamp"),
                    e.get("minute"),
                    e.get("second"),
                    et.get("id"),
                    et.get("name"),
                    e.get("possession"),
                    pt.get("id"),
                    pt.get("name"),
                    pp.get("id"),
                    pp.get("name"),
                    json.dumps(e, ensure_ascii=False),
                ]
                cur.execute(details_sql, vals)
                details_inserted += 1

        return {
            "events_inserted": events_inserted,
            "details_inserted": details_inserted,
        }

    def _build_aggregations(self, conn, source: str, match_ids: list[int]) -> int:
        cur = conn.cursor()
        if source == "postgres":
            if match_ids:
                cur.execute(
                    "DELETE FROM events_details__quarter_minute WHERE match_id = ANY(%s)",
                    (match_ids,),
                )
                cur.execute(
                    """
                    INSERT INTO events_details__quarter_minute (
                        match_id, period, minute, quarter_minute, count, json_, summary, summary_script
                    )
                    SELECT match_id, COALESCE(period,0), COALESCE(minute,0), (COALESCE(second,0)/15)+1,
                           COUNT(*), STRING_AGG(COALESCE(json_,''), ', '), NULL, NULL
                    FROM events_details
                    WHERE match_id = ANY(%s)
                    GROUP BY match_id, COALESCE(period,0), COALESCE(minute,0), (COALESCE(second,0)/15)+1
                    """,
                    (match_ids,),
                )
            else:
                cur.execute("DELETE FROM events_details__quarter_minute")
                cur.execute(
                    """
                    INSERT INTO events_details__quarter_minute (
                        match_id, period, minute, quarter_minute, count, json_, summary, summary_script
                    )
                    SELECT match_id, COALESCE(period,0), COALESCE(minute,0), (COALESCE(second,0)/15)+1,
                           COUNT(*), STRING_AGG(COALESCE(json_,''), ', '), NULL, NULL
                    FROM events_details
                    GROUP BY match_id, COALESCE(period,0), COALESCE(minute,0), (COALESCE(second,0)/15)+1
                    """
                )
            cur.execute("SELECT COUNT(*) FROM events_details__quarter_minute")
            return int(cur.fetchone()[0] or 0)

        if match_ids:
            placeholders = ",".join("?" for _ in match_ids)
            cur.execute(
                f"DELETE FROM events_details__15secs_agg WHERE match_id IN ({placeholders})",
                match_ids,
            )
            cur.execute(
                f"""
                INSERT INTO events_details__15secs_agg (
                    match_id, period, minute, _15secs, count, json_, summary, embedding_3_small
                )
                SELECT match_id, ISNULL(period,0), ISNULL(minute,0), (ISNULL(second,0)/15)+1,
                       COUNT(*), STRING_AGG(CAST(ISNULL(json_, '') AS NVARCHAR(MAX)), ', '), NULL, NULL
                FROM events_details
                WHERE match_id IN ({placeholders})
                GROUP BY match_id, ISNULL(period,0), ISNULL(minute,0), (ISNULL(second,0)/15)+1
                """,
                match_ids,
            )
        else:
            cur.execute("DELETE FROM events_details__15secs_agg")
            cur.execute(
                """
                INSERT INTO events_details__15secs_agg (
                    match_id, period, minute, _15secs, count, json_, summary, embedding_3_small
                )
                SELECT match_id, ISNULL(period,0), ISNULL(minute,0), (ISNULL(second,0)/15)+1,
                       COUNT(*), STRING_AGG(CAST(ISNULL(json_, '') AS NVARCHAR(MAX)), ', '), NULL, NULL
                FROM events_details
                GROUP BY match_id, ISNULL(period,0), ISNULL(minute,0), (ISNULL(second,0)/15)+1
                """
            )
        cur.execute("SELECT COUNT(*) FROM events_details__15secs_agg")
        return int(cur.fetchone()[0] or 0)

    def _update_embeddings_for_row(
        self,
        conn,
        source: str,
        row_id: int,
        summary: str,
        models: list[str],
        adapter: OpenAIAdapter,
    ) -> None:
        cur = conn.cursor()
        try:
            if source == "postgres":
                model_cols = {
                    "text-embedding-3-small": "summary_embedding_t3_small",
                }
                for model in models:
                    col = model_cols.get(model)
                    if not col:
                        continue
                    emb = adapter.create_embedding(text=summary, model=model)
                    emb_str = "[" + ",".join(map(str, emb)) + "]"
                    cur.execute(
                        f"UPDATE events_details__quarter_minute SET {col} = %s::vector WHERE id = %s",
                        (emb_str, row_id),
                    )
                cur.execute(
                    "UPDATE events_details__quarter_minute SET embedding_status = 'done', embedding_updated_at = NOW(), embedding_error = NULL WHERE id = %s",
                    (row_id,),
                )
                return

            model_cols = {
                "text-embedding-3-small": "embedding_3_small",
            }
            for model in models:
                col = model_cols.get(model)
                if not col:
                    continue
                emb = adapter.create_embedding(text=summary, model=model)
                emb_str = "[" + ",".join(map(str, emb)) + "]"
                # pyodbc promotes long strings to ntext; force VARCHAR for VECTOR CAST
                import pyodbc as _pyodbc

                cur.setinputsizes([(_pyodbc.SQL_VARCHAR, 0, 0)])
                cur.execute(
                    f"UPDATE events_details__15secs_agg SET {col} = CAST(? AS VECTOR(1536)) WHERE id = ?",
                    (emb_str, row_id),
                )
            cur.execute(
                "UPDATE events_details__15secs_agg SET embedding_status = 'done', embedding_updated_at = GETDATE(), embedding_error = NULL WHERE id = ?",
                (row_id,),
            )
        except Exception as e:
            # Mark the row as errored but don't stop the whole batch
            try:
                if source == "postgres":
                    cur.execute(
                        "UPDATE events_details__quarter_minute SET embedding_status = 'error', embedding_error = %s WHERE id = %s",
                        (str(e)[:500], row_id),
                    )
                else:
                    cur.execute(
                        "UPDATE events_details__15secs_agg SET embedding_status = 'error', embedding_error = ? WHERE id = ?",
                        (str(e)[:500], row_id),
                    )
            except Exception:
                pass
            raise
