"""Dev-path seed loader: loads pre-computed seed dataset into local DBs.

Runs during ``.devcontainer/post-create.sh`` the first time a developer
opens the repo in VS Code / Docker. Does NOT call OpenAI — reads
pre-computed seed files from ``data/seed/`` in the repository.

Idempotent: if both seed matches are already present with non-null
embeddings, exits 0 in ~100 ms without touching files or DB.

Graceful degrade: any failure (missing files, sha mismatch, DB down)
logs a clear warning and exits non-zero; the calling post-create script
is expected to continue anyway so the devcontainer still starts.

Usage:
    python -m scripts.seed_load                  # both sources
    python -m scripts.seed_load --source postgres
    python -m scripts.seed_load --source sqlserver
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable

SEED_MATCH_IDS = (3943043, 3869685)


# ---------------------------------------------------------------------------
# Idempotency check
# ---------------------------------------------------------------------------


def check_idempotency(source: str) -> bool:
    """Return True if both seed matches are fully loaded in this source.

    "Fully loaded" means: the ``matches`` table has both match_ids AND
    the aggregation table has at least one row per match_id with a
    non-null ``summary_embedding_t3_small`` (postgres) or
    ``embedding_3_small`` (sqlserver). If so the seed is already there
    and we can skip everything.
    """
    try:
        with _connect(source) as conn:
            cur = conn.cursor()
            placeholders = (
                "ANY(%s)"
                if source == "postgres"
                else "(" + ",".join("?" for _ in SEED_MATCH_IDS) + ")"
            )
            params: tuple[Any, ...] = (
                (list(SEED_MATCH_IDS),) if source == "postgres" else SEED_MATCH_IDS
            )

            cur.execute(
                f"SELECT COUNT(*) FROM matches WHERE match_id {'= ANY(%s)' if source == 'postgres' else 'IN ' + placeholders}",
                params,
            )
            row = cur.fetchone()
            if int(row[0] or 0) < len(SEED_MATCH_IDS):
                return False

            if source == "postgres":
                cur.execute(
                    """
                    SELECT COUNT(DISTINCT match_id)
                    FROM events_details__quarter_minute
                    WHERE match_id = ANY(%s)
                      AND summary_embedding_t3_small IS NOT NULL
                    """,
                    (list(SEED_MATCH_IDS),),
                )
            else:
                qmarks = ",".join("?" for _ in SEED_MATCH_IDS)
                cur.execute(
                    f"""
                    SELECT COUNT(DISTINCT match_id)
                    FROM events_details__15secs_agg
                    WHERE match_id IN ({qmarks})
                      AND embedding_3_small IS NOT NULL
                    """,
                    SEED_MATCH_IDS,
                )
            row = cur.fetchone()
            return int(row[0] or 0) >= len(SEED_MATCH_IDS)
    except Exception as e:
        print(f"[seed-load] Idempotency check failed for {source}: {e}")
        return False


# ---------------------------------------------------------------------------
# Locate + verify seed files
# ---------------------------------------------------------------------------


def find_seed_root() -> Path:
    """Locate the seed data directory in the repository.

    Searches for ``data/seed/`` relative to the backend directory
    (typical layout: ``backend/`` is the cwd, ``data/seed/`` is at repo root).

    Returns the path to the seed root directory containing match subdirs.
    Raises on missing directory or sha mismatch.
    """
    # Try common locations: relative to cwd (backend/) or via /workspace (devcontainer)
    candidates = [
        Path.cwd().parent / "data" / "seed",       # running from backend/
        Path.cwd() / "data" / "seed",               # running from repo root
        Path("/workspace") / "data" / "seed",        # devcontainer
    ]
    seed_root = None
    for candidate in candidates:
        if (candidate / "manifest.json").exists():
            seed_root = candidate
            break

    if seed_root is None:
        raise RuntimeError(
            "Seed data not found. Expected data/seed/manifest.json in the repo. "
            "Make sure you are running from the backend/ or repo root directory."
        )

    manifest_path = seed_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    for relative_path, expected_sha in manifest.get("files", {}).items():
        file_path = seed_root / relative_path
        if not file_path.exists():
            raise RuntimeError(f"Seed file missing: {relative_path}")
        actual_sha = hashlib.sha256(file_path.read_bytes()).hexdigest()
        if actual_sha != expected_sha:
            raise RuntimeError(
                f"sha256 mismatch on {relative_path}: "
                f"expected {expected_sha[:12]}, got {actual_sha[:12]}"
            )

    print(f"[seed-load] Seed verified: {len(manifest.get('files', {}))} files OK")
    return seed_root


# ---------------------------------------------------------------------------
# DB connection helpers
# ---------------------------------------------------------------------------


@contextmanager
def _connect(source: str):
    """Open a raw connection for postgres or sqlserver using env vars."""
    conn = None
    try:
        if source == "postgres":
            import psycopg2

            conn = psycopg2.connect(
                host=os.environ.get("POSTGRES_HOST", "postgres"),
                port=int(os.environ.get("POSTGRES_PORT", "5432")),
                database=os.environ.get("POSTGRES_DB", "rag_challenge"),
                user=os.environ.get("POSTGRES_USER", "postgres"),
                password=os.environ.get("POSTGRES_PASSWORD", "postgres_local_pwd"),
            )
        elif source == "sqlserver":
            import pyodbc

            conn = pyodbc.connect(
                "DRIVER={ODBC Driver 18 for SQL Server};"
                f"SERVER={os.environ.get('SQLSERVER_HOST', 'sqlserver')};"
                f"DATABASE={os.environ.get('SQLSERVER_DB', 'rag_challenge')};"
                f"UID={os.environ.get('SQLSERVER_USER', 'sa')};"
                f"PWD={os.environ.get('SQLSERVER_PASSWORD', 'SqlServer_Local_Pwd123!')};"
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


# ---------------------------------------------------------------------------
# Stage files into the format IngestionService expects
# ---------------------------------------------------------------------------


def _stage_seed_for_ingestion(seed_root: Path, staging_dir: Path) -> list[int]:
    """Copy seed files into the layout expected by IngestionService.

    The seed directory has:
        data/seed/<match_id>/match.json       (single match dict)
        data/seed/<match_id>/events.json      (list of events)

    IngestionService._iter_matches_from_local reads
    ``{local_folder}/matches/**/*.json`` expecting a list of dicts.
    IngestionService._load_events reads
    ``{local_folder}/events/<match_id>.json`` as a list of events.

    This helper copies+wraps accordingly.
    """
    matches_dir = staging_dir / "matches"
    events_dir = staging_dir / "events"
    matches_dir.mkdir(parents=True, exist_ok=True)
    events_dir.mkdir(parents=True, exist_ok=True)

    match_ids: list[int] = []
    all_matches_list: list[dict[str, Any]] = []

    for match_dir in sorted(seed_root.iterdir()):
        if not match_dir.is_dir():
            continue
        try:
            match_id = int(match_dir.name)
        except ValueError:
            continue

        match_json_path = match_dir / "match.json"
        events_json_path = match_dir / "events.json"
        if not match_json_path.exists() or not events_json_path.exists():
            continue

        with match_json_path.open("r", encoding="utf-8") as f:
            match_data = json.load(f)
        all_matches_list.append(match_data)

        shutil.copyfile(events_json_path, events_dir / f"{match_id}.json")
        match_ids.append(match_id)

    # Single file with all matches so _iter_matches_from_local picks them up
    (matches_dir / "seed.json").write_text(
        json.dumps(all_matches_list, ensure_ascii=False), encoding="utf-8"
    )
    return sorted(match_ids)


# ---------------------------------------------------------------------------
# Apply summaries + embeddings from JSONL files
# ---------------------------------------------------------------------------


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def _apply_summaries_and_embeddings(
    conn, source: str, seed_root: Path, match_ids: list[int]
) -> dict[str, int]:
    """Update aggregation rows with pre-computed summaries and embeddings.

    Matches seed rows to DB rows by (match_id, period, minute, quarter_minute)
    because the auto-increment ``id`` will differ between the build machine
    and the loading machine.
    """
    cur = conn.cursor()
    stats = {"summaries_updated": 0, "embeddings_updated": 0}

    for match_id in match_ids:
        match_dir = seed_root / str(match_id)

        # Build a (period, minute, quarter_minute) -> DB id lookup for this match
        if source == "postgres":
            cur.execute(
                """
                SELECT id, period, minute, quarter_minute
                FROM events_details__quarter_minute
                WHERE match_id = %s
                """,
                (match_id,),
            )
        else:
            cur.execute(
                """
                SELECT id, period, minute, _15secs
                FROM events_details__15secs_agg
                WHERE match_id = ?
                """,
                (match_id,),
            )
        id_by_key = {
            (int(r[1] or 0), int(r[2] or 0), int(r[3] or 0)): int(r[0])
            for r in cur.fetchall()
        }

        # Summaries
        summaries_path = match_dir / "summaries.jsonl"
        if summaries_path.exists():
            for rec in _iter_jsonl(summaries_path):
                key = (
                    int(rec.get("period") or 0),
                    int(rec.get("minute") or 0),
                    int(rec.get("quarter_minute") or 0),
                )
                db_id = id_by_key.get(key)
                if db_id is None:
                    continue
                if source == "postgres":
                    cur.execute(
                        "UPDATE events_details__quarter_minute SET summary = %s WHERE id = %s",
                        (rec["summary"], db_id),
                    )
                else:
                    cur.execute(
                        "UPDATE events_details__15secs_agg SET summary = ? WHERE id = ?",
                        (rec["summary"], db_id),
                    )
                stats["summaries_updated"] += 1

        # Embeddings (t3_small)
        emb_path = match_dir / "embeddings_t3_small.jsonl"
        if emb_path.exists():
            # Embeddings file keys by row_id from the build machine. That id
            # won't match here; but we exported summaries.jsonl in the same
            # order, so we can use the matched db_id from the summaries
            # write-back. For this version we re-match by position within
            # the match: read both files in parallel.
            summaries_records = (
                list(_iter_jsonl(summaries_path)) if summaries_path.exists() else []
            )
            embedding_records = list(_iter_jsonl(emb_path))
            if len(summaries_records) != len(embedding_records):
                print(
                    f"[seed-load]   WARN: summaries/embeddings count mismatch "
                    f"for {match_id}: {len(summaries_records)} vs {len(embedding_records)}"
                )
            for s_rec, e_rec in zip(summaries_records, embedding_records):
                key = (
                    int(s_rec.get("period") or 0),
                    int(s_rec.get("minute") or 0),
                    int(s_rec.get("quarter_minute") or 0),
                )
                db_id = id_by_key.get(key)
                if db_id is None:
                    continue
                vector = e_rec["vector"]
                vector_str = "[" + ",".join(str(v) for v in vector) + "]"
                if source == "postgres":
                    cur.execute(
                        "UPDATE events_details__quarter_minute "
                        "SET summary_embedding_t3_small = %s::vector, "
                        "embedding_status = 'done' WHERE id = %s",
                        (vector_str, db_id),
                    )
                else:
                    # pyodbc promotes long strings (>4000 chars) to ntext,
                    # which SQL Server cannot CAST to VECTOR. Force VARCHAR.
                    import pyodbc as _pyodbc

                    cur.setinputsizes([(_pyodbc.SQL_VARCHAR, 0, 0)])
                    cur.execute(
                        "UPDATE events_details__15secs_agg "
                        "SET embedding_3_small = CAST(? AS VECTOR(1536)), "
                        "embedding_status = 'done' WHERE id = ?",
                        (vector_str, db_id),
                    )
                stats["embeddings_updated"] += 1

    return stats


# ---------------------------------------------------------------------------
# Main load flow
# ---------------------------------------------------------------------------


def load_into(source: str, seed_root: Path) -> dict[str, int]:
    """Full load sequence for a single source (postgres or sqlserver)."""
    print(f"[seed-load] Loading into {source}")
    # Stage files into the layout IngestionService expects
    with tempfile.TemporaryDirectory() as tmp:
        staging_dir = Path(tmp)
        match_ids = _stage_seed_for_ingestion(seed_root, staging_dir)
        print(f"[seed-load]   staged match_ids: {match_ids}")

        # Import here to avoid top-level import cost when idempotent short-circuits
        from app.services.ingestion_service import IngestionService

        service = IngestionService()
        # Point the service at our temp staging dir for this load
        service.local_folder = staging_dir

        with _connect(source) as conn:
            matches_result = service._load_matches(conn, source, match_ids)
            print(f"[seed-load]   matches: {matches_result}")
            events_result = service._load_events(conn, source, match_ids)
            print(f"[seed-load]   events: {events_result}")
            agg_count = service._build_aggregations(conn, source, match_ids)
            print(f"[seed-load]   aggregated rows: {agg_count}")
            stats = _apply_summaries_and_embeddings(conn, source, seed_root, match_ids)
            print(
                f"[seed-load]   summaries_updated={stats['summaries_updated']} "
                f"embeddings_updated={stats['embeddings_updated']}"
            )
            return {
                "match_ids": match_ids,
                "aggregated_rows": agg_count,
                **stats,
            }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Load the pre-computed seed dataset into local DBs"
    )
    parser.add_argument(
        "--source",
        choices=["postgres", "sqlserver", "both"],
        default="both",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Reload even if idempotency check passes",
    )
    args = parser.parse_args()

    sources = ["postgres", "sqlserver"] if args.source == "both" else [args.source]

    # Idempotency check per source
    to_load: list[str] = []
    for src in sources:
        if args.force:
            to_load.append(src)
            continue
        if check_idempotency(src):
            print(f"[seed-load] {src}: already seeded, skipping")
        else:
            to_load.append(src)

    if not to_load:
        print("[seed-load] Nothing to do — all sources already seeded")
        return 0

    # Locate + verify seed files in the repo
    try:
        seed_root = find_seed_root()
    except Exception as e:
        print(f"[seed-load] ERROR locating seed data: {e}", file=sys.stderr)
        return 1

    errors = 0
    for src in to_load:
        try:
            load_into(src, seed_root)
        except Exception as e:
            print(f"[seed-load] ERROR loading {src}: {e}", file=sys.stderr)
            errors += 1

    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
