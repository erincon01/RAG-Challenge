"""Ingestion workflows: download, load, aggregate and embeddings rebuild."""

from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import psycopg2
import pyodbc

from app.adapters.openai_client import OpenAIAdapter
from app.core.capabilities import normalize_source
from app.core.config import get_settings
from app.services.job_service import JobService
from app.services.statsbomb_service import StatsBombService


class IngestionService:
    """Service implementing end-to-end ingestion tasks."""

    def __init__(self):
        self.settings = get_settings()
        self.statsbomb = StatsBombService()
        self.local_folder = Path(self.settings.repository.local_folder)

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
                    (
                        "DRIVER={ODBC Driver 18 for SQL Server};"
                        f"SERVER={self.settings.database.sqlserver_host};"
                        f"DATABASE={self.settings.database.sqlserver_database};"
                        f"UID={self.settings.database.sqlserver_user};"
                        f"PWD={self.settings.database.sqlserver_password};"
                        "TrustServerCertificate=yes;"
                    )
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

    def run_download_job(self, job_id: str, payload: Dict[str, Any]) -> None:
        try:
            JobService.update(job_id, status="running", message="Resolving matches")
            datasets = [d.lower() for d in (payload.get("datasets") or ["matches", "lineups", "events"])]
            match_ids = payload.get("match_ids") or []
            competition_id = payload.get("competition_id")
            season_id = payload.get("season_id")
            overwrite = bool(payload.get("overwrite", False))

            resolved_match_ids = self.statsbomb.resolve_match_ids(
                match_ids=match_ids,
                competition_id=competition_id,
                season_id=season_id,
            )

            total = (1 if "matches" in datasets and competition_id is not None and season_id is not None else 0)
            total += len(resolved_match_ids) * len([d for d in datasets if d in {"lineups", "events"}])
            JobService.update(job_id, total=total, message="Downloading datasets")

            progress = 0
            files: List[str] = []
            if "matches" in datasets and competition_id is not None and season_id is not None:
                file_path = self.statsbomb.download_matches_catalog(competition_id, season_id, overwrite)
                files.append(str(file_path))
                progress += 1
                JobService.update(job_id, progress=progress, message=f"Downloaded {file_path.name}")

            for match_id in resolved_match_ids:
                for dataset in [d for d in datasets if d in {"lineups", "events"}]:
                    file_path = self.statsbomb.download_match_file(dataset, match_id, overwrite)
                    files.append(str(file_path))
                    progress += 1
                    JobService.update(job_id, progress=progress, message=f"Downloaded {dataset}/{match_id}.json")

            JobService.complete(job_id, {"match_ids": resolved_match_ids, "downloaded_files": files})
        except Exception as e:
            JobService.fail(job_id, str(e))

    def run_load_job(self, job_id: str, payload: Dict[str, Any]) -> None:
        source = normalize_source(payload.get("source", "postgres"))
        datasets = [d.lower() for d in (payload.get("datasets") or ["matches", "events"])]
        match_ids = [int(v) for v in (payload.get("match_ids") or [])]
        try:
            JobService.update(job_id, status="running", total=len(datasets), message=f"Loading into {source}")
            result: Dict[str, Any] = {}
            progress = 0
            with self._get_connection(source) as conn:
                if "matches" in datasets:
                    result["matches"] = self._load_matches(conn, source, match_ids)
                    progress += 1
                    JobService.update(job_id, progress=progress, message="Loaded matches")
                if "events" in datasets:
                    result["events"] = self._load_events(conn, source, match_ids)
                    progress += 1
                    JobService.update(job_id, progress=progress, message="Loaded events")
                if "lineups" in datasets:
                    result["lineups"] = {"skipped": True, "reason": "lineups load pending"}
                    progress += 1
                    JobService.update(job_id, progress=progress, message="Skipped lineups (pending)")
            JobService.complete(job_id, result)
        except Exception as e:
            JobService.fail(job_id, str(e))

    def run_aggregate_job(self, job_id: str, payload: Dict[str, Any]) -> None:
        source = normalize_source(payload.get("source", "postgres"))
        match_ids = [int(v) for v in (payload.get("match_ids") or [])]
        try:
            JobService.update(job_id, status="running", total=1, message=f"Building aggregations in {source}")
            with self._get_connection(source) as conn:
                rows = self._build_aggregations(conn, source, match_ids)
            JobService.update(job_id, progress=1)
            JobService.complete(job_id, {"aggregated_rows": rows, "source": source})
        except Exception as e:
            JobService.fail(job_id, str(e))

    def run_rebuild_embeddings_job(self, job_id: str, payload: Dict[str, Any]) -> None:
        source = normalize_source(payload.get("source", "postgres"))
        match_ids = [int(v) for v in (payload.get("match_ids") or [])]
        defaults = {
            "postgres": ["text-embedding-ada-002", "text-embedding-3-small", "text-embedding-3-large"],
            "sqlserver": ["text-embedding-ada-002", "text-embedding-3-small"],
        }
        models = payload.get("embedding_models") or defaults[source]
        try:
            JobService.update(job_id, status="running", message=f"Rebuilding embeddings in {source}")
            adapter = OpenAIAdapter()
            with self._get_connection(source) as conn:
                rows = self._fetch_summary_rows(conn, source, match_ids)
                JobService.update(job_id, total=len(rows))
                updated = 0
                for idx, (row_id, summary) in enumerate(rows, start=1):
                    if not summary:
                        continue
                    self._update_embeddings_for_row(conn, source, row_id, summary, models, adapter)
                    updated += 1
                    JobService.update(job_id, progress=idx, message=f"Embedded row {idx}/{len(rows)}")
            JobService.complete(job_id, {"updated_rows": updated, "source": source, "embedding_models": models})
        except Exception as e:
            JobService.fail(job_id, str(e))

    def get_embeddings_status(self, source: str) -> Dict[str, Any]:
        src = normalize_source(source)
        with self._get_connection(src) as conn:
            cur = conn.cursor()
            if src == "postgres":
                cur.execute(
                    """
                    SELECT COUNT(*),
                           SUM(CASE WHEN summary_embedding_ada_002 IS NOT NULL THEN 1 ELSE 0 END),
                           SUM(CASE WHEN summary_embedding_t3_small IS NOT NULL THEN 1 ELSE 0 END),
                           SUM(CASE WHEN summary_embedding_t3_large IS NOT NULL THEN 1 ELSE 0 END),
                           SUM(CASE WHEN summary_embedding IS NOT NULL THEN 1 ELSE 0 END)
                    FROM events_details__quarter_minute
                    """
                )
                row = cur.fetchone()
                return {
                    "source": "postgres",
                    "table": "events_details__quarter_minute",
                    "total_rows": int(row[0] or 0),
                    "coverage": {
                        "text-embedding-ada-002": int(row[1] or 0),
                        "text-embedding-3-small": int(row[2] or 0),
                        "text-embedding-3-large": int(row[3] or 0),
                    },
                }

            cur.execute(
                """
                SELECT COUNT(*),
                       SUM(CASE WHEN embedding_ada_002 IS NOT NULL THEN 1 ELSE 0 END),
                       SUM(CASE WHEN embedding_3_small IS NOT NULL THEN 1 ELSE 0 END)
                FROM events_details__15secs_agg
                """
            )
            row = cur.fetchone()
            return {
                "source": "sqlserver",
                "table": "events_details__15secs_agg",
                "total_rows": int(row[0] or 0),
                "coverage": {
                    "text-embedding-ada-002": int(row[1] or 0),
                    "text-embedding-3-small": int(row[2] or 0),
                },
            }

    def _iter_matches_from_local(self) -> Iterable[Dict[str, Any]]:
        matches_root = self.local_folder / "matches"
        if not matches_root.exists():
            return []
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

    def _fetch_summary_rows(self, conn, source: str, match_ids: List[int]) -> List[Tuple[int, str]]:
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
                cur.execute("SELECT id, summary FROM events_details__quarter_minute WHERE summary IS NOT NULL ORDER BY id")
            return [(int(r[0]), r[1]) for r in cur.fetchall()]

        if match_ids:
            placeholders = ",".join("?" for _ in match_ids)
            cur.execute(
                f"SELECT id, summary FROM events_details__15secs_agg WHERE summary IS NOT NULL AND match_id IN ({placeholders}) ORDER BY id",
                match_ids,
            )
        else:
            cur.execute("SELECT id, summary FROM events_details__15secs_agg WHERE summary IS NOT NULL ORDER BY id")
        return [(int(r[0]), r[1]) for r in cur.fetchall()]

    def _load_matches(self, conn, source: str, match_ids: List[int]) -> Dict[str, int]:
        inserted = 0
        seen: set[int] = set()
        cur = conn.cursor()

        for m in self._iter_matches_from_local():
            match_id = int(m.get("match_id"))
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
            result = f"{m.get('home_score')}-{m.get('away_score')}" if m.get("home_score") is not None else None

            vals = [
                match_id, m.get("match_date"),
                c.get("competition_id"), c.get("country_name"), c.get("competition_name"),
                s.get("season_id"), s.get("season_name"),
                ht.get("home_team_id") or ht.get("id"), ht.get("home_team_name") or ht.get("name"), ht.get("home_team_gender") or ht.get("gender"), (ht.get("country") or {}).get("name"),
                None, None,
                at.get("away_team_id") or at.get("id"), at.get("away_team_name") or at.get("name"), at.get("away_team_gender") or at.get("gender"), (at.get("country") or {}).get("name"),
                None, None,
                m.get("home_score"), m.get("away_score"), result, m.get("match_week"),
                st.get("id"), st.get("name"), (st.get("country") or {}).get("name"),
                rf.get("id"), rf.get("name"), (rf.get("country") or {}).get("name"),
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

    def _load_events(self, conn, source: str, match_ids: List[int]) -> Dict[str, int]:
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
                cur.execute("DELETE FROM events_details WHERE match_id = %s", (match_id,))
                cur.execute("DELETE FROM events WHERE match_id = %s", (match_id,))
                cur.execute("INSERT INTO events (match_id, json_) VALUES (%s, %s)", (match_id, json.dumps(events, ensure_ascii=False)))
                details_sql = """
                    INSERT INTO events_details (
                        match_id, id_guid, "index", period, timestamp, minute, second,
                        type_id, type, possession, possession_team_id, possession_team,
                        play_pattern_id, play_pattern, json_
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """
            else:
                cur.execute("DELETE FROM events_details WHERE match_id = ?", (match_id,))
                cur.execute("DELETE FROM events WHERE match_id = ?", (match_id,))
                cur.execute("INSERT INTO events (match_id, json_) VALUES (?, ?)", (match_id, json.dumps(events, ensure_ascii=False)))
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
                    match_id, e.get("id"), e.get("index"), e.get("period"), e.get("timestamp"), e.get("minute"), e.get("second"),
                    et.get("id"), et.get("name"), e.get("possession"), pt.get("id"), pt.get("name"), pp.get("id"), pp.get("name"),
                    json.dumps(e, ensure_ascii=False),
                ]
                cur.execute(details_sql, vals)
                details_inserted += 1

        return {"events_inserted": events_inserted, "details_inserted": details_inserted}

    def _build_aggregations(self, conn, source: str, match_ids: List[int]) -> int:
        cur = conn.cursor()
        if source == "postgres":
            if match_ids:
                cur.execute("DELETE FROM events_details__quarter_minute WHERE match_id = ANY(%s)", (match_ids,))
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
            cur.execute(f"DELETE FROM events_details__15secs_agg WHERE match_id IN ({placeholders})", match_ids)
            cur.execute(
                f"""
                INSERT INTO events_details__15secs_agg (
                    match_id, period, minute, _15secs, count, json_, summary, embedding_3_small, embedding_ada_002
                )
                SELECT match_id, ISNULL(period,0), ISNULL(minute,0), (ISNULL(second,0)/15)+1,
                       COUNT(*), STRING_AGG(CAST(ISNULL(json_, '') AS NVARCHAR(MAX)), ', '), NULL, NULL, NULL
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
                    match_id, period, minute, _15secs, count, json_, summary, embedding_3_small, embedding_ada_002
                )
                SELECT match_id, ISNULL(period,0), ISNULL(minute,0), (ISNULL(second,0)/15)+1,
                       COUNT(*), STRING_AGG(CAST(ISNULL(json_, '') AS NVARCHAR(MAX)), ', '), NULL, NULL, NULL
                FROM events_details
                GROUP BY match_id, ISNULL(period,0), ISNULL(minute,0), (ISNULL(second,0)/15)+1
                """
            )
        cur.execute("SELECT COUNT(*) FROM events_details__15secs_agg")
        return int(cur.fetchone()[0] or 0)

    def _update_embeddings_for_row(self, conn, source: str, row_id: int, summary: str, models: List[str], adapter: OpenAIAdapter) -> None:
        cur = conn.cursor()
        if source == "postgres":
            model_cols = {
                "text-embedding-ada-002": "summary_embedding_ada_002",
                "text-embedding-3-small": "summary_embedding_t3_small",
                "text-embedding-3-large": "summary_embedding_t3_large",
            }
            for model in models:
                col = model_cols.get(model)
                if not col:
                    continue
                emb = adapter.create_embedding(text=summary, model=model)
                emb_str = "[" + ",".join(map(str, emb)) + "]"
                cur.execute(f"UPDATE events_details__quarter_minute SET {col} = %s::vector WHERE id = %s", (emb_str, row_id))
            return

        model_cols = {
            "text-embedding-ada-002": "embedding_ada_002",
            "text-embedding-3-small": "embedding_3_small",
        }
        for model in models:
            col = model_cols.get(model)
            if not col:
                continue
            emb = adapter.create_embedding(text=summary, model=model)
            emb_str = "[" + ",".join(map(str, emb)) + "]"
            cur.execute(f"UPDATE events_details__15secs_agg SET {col} = CAST(? AS VECTOR(1536)) WHERE id = ?", (emb_str, row_id))
