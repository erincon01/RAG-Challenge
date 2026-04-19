"""Maintainer-only script to build the seed dataset tarball.

This script exports the two seed matches (Euro 2024 Final + World Cup 2022
Final) into a tarball that can be published as a GitHub Release asset so
new developers don't need an OpenAI key on first run.

**Requires:** `OPENAI_KEY` in `.env` or `.env.docker`, a running Docker
stack (postgres + sqlserver + backend), and ~$0.50 of OpenAI budget.

Flow:
    1. Validate OPENAI_KEY is set.
    2. POST /ingestion/full-pipeline for both match_ids (one job per match
       to get per-match progress).
    3. Poll job status until success or failure.
    4. Read matches + aggregation rows directly from Postgres.
    5. Serialize to ``seed/v1/<match_id>/`` directory with:
       - match.json   (raw StatsBomb row)
       - events.json  (raw StatsBomb events)
       - summaries.jsonl  (one {row_id, summary} per line)
       - embeddings_t3_small.jsonl  (one {row_id, vector} per line)
    6. Write manifest.json with sha256 checksums.
    7. Create seed-v1.tar.gz.
    8. Print upload instructions.

Usage:
    python -m scripts.seed_build --i-have-budget --output ./seed-v1.tar.gz
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tarfile
import time
from pathlib import Path
from typing import Any

import httpx
import psycopg2

SEED_MATCH_IDS: dict[int, dict[str, Any]] = {
    3943043: {
        "label": "Euro 2024 Final (Spain 2-1 England)",
        "competition_id": 55,
        "season_id": 282,
    },
    3869685: {
        "label": "World Cup 2022 Final (Argentina 3-3 France, pens 4-2)",
        "competition_id": 43,
        "season_id": 106,
    },
}

SEED_VERSION = "v1"
EMBEDDING_MODEL = "text-embedding-3-small"
BACKEND_URL_DEFAULT = "http://localhost:8000"


def _require_api_key() -> None:
    """Fail fast if no OpenAI key is configured."""
    key = os.environ.get("OPENAI_KEY") or os.environ.get("OPENAI_API_KEY")
    if not key:
        sys.stderr.write(
            "ERROR: OPENAI_KEY not set. This script makes paid API calls.\n"
            "Set it in backend/.env or .env.docker (both gitignored) or "
            "export it in the shell before running.\n"
        )
        sys.exit(2)


def _run_full_pipeline(backend_url: str, match_id: int, meta: dict[str, Any]) -> None:
    """POST /ingestion/full-pipeline for a single match and wait for success."""
    payload = {
        "source": "postgres",
        "match_ids": [match_id],
        "competition_id": meta["competition_id"],
        "season_id": meta["season_id"],
        "datasets": ["matches", "lineups", "events"],
        "embedding_models": [EMBEDDING_MODEL],
    }
    print(f"[build] Starting full pipeline for match {match_id} ({meta['label']})")
    with httpx.Client(base_url=backend_url, timeout=60.0) as client:
        resp = client.post("/api/v1/ingestion/full-pipeline", json=payload)
        resp.raise_for_status()
        job_id = resp.json()["job_id"]
        print(f"[build]   job_id={job_id}")

        while True:
            time.sleep(5)
            status_resp = client.get(f"/api/v1/ingestion/jobs/{job_id}")
            status_resp.raise_for_status()
            job = status_resp.json()
            print(
                f"[build]   status={job['status']} "
                f"progress={job['progress']}/{job['total']} "
                f"message={job['message']}"
            )
            if job["status"] == "success":
                return
            if job["status"] == "error":
                sys.stderr.write(
                    f"ERROR: pipeline failed for {match_id}: {job.get('error')}\n"
                )
                sys.exit(3)


def _export_match(conn, match_id: int, seed_dir: Path) -> dict[str, str]:
    """Read a single match from Postgres and write seed files for it.

    Returns a dict of filename -> sha256 for the manifest.
    """
    match_dir = seed_dir / str(match_id)
    match_dir.mkdir(parents=True, exist_ok=True)
    checksums: dict[str, str] = {}

    cur = conn.cursor()

    # Raw match row from the matches table
    cur.execute("SELECT json_ FROM matches WHERE match_id = %s", (match_id,))
    row = cur.fetchone()
    if not row:
        raise RuntimeError(f"Match {match_id} not in database after pipeline ran")
    match_json = row[0]
    if isinstance(match_json, str):
        match_json = json.loads(match_json)
    (match_dir / "match.json").write_text(
        json.dumps(match_json, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Raw events
    cur.execute("SELECT json_ FROM events WHERE match_id = %s", (match_id,))
    row = cur.fetchone()
    if not row:
        raise RuntimeError(f"Events for {match_id} not in database")
    events_json = row[0]
    if isinstance(events_json, str):
        events_json = json.loads(events_json)
    (match_dir / "events.json").write_text(
        json.dumps(events_json, ensure_ascii=False), encoding="utf-8"
    )

    # Summaries — one JSONL row per aggregation bucket
    cur.execute(
        """
        SELECT id, match_id, period, minute, quarter_minute, summary
        FROM events_details__quarter_minute
        WHERE match_id = %s AND summary IS NOT NULL
        ORDER BY id
        """,
        (match_id,),
    )
    summaries_path = match_dir / "summaries.jsonl"
    with summaries_path.open("w", encoding="utf-8") as f:
        for r in cur.fetchall():
            f.write(
                json.dumps(
                    {
                        "row_id": int(r[0]),
                        "match_id": int(r[1]),
                        "period": int(r[2] or 0),
                        "minute": int(r[3] or 0),
                        "quarter_minute": int(r[4] or 0),
                        "summary": r[5],
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    # Embeddings — one JSONL row per bucket with the t3_small vector
    cur.execute(
        """
        SELECT id, summary_embedding_t3_small::text
        FROM events_details__quarter_minute
        WHERE match_id = %s AND summary_embedding_t3_small IS NOT NULL
        ORDER BY id
        """,
        (match_id,),
    )
    embeddings_path = match_dir / "embeddings_t3_small.jsonl"
    with embeddings_path.open("w", encoding="utf-8") as f:
        for r in cur.fetchall():
            # pgvector returns "[0.1, 0.2, ...]" string; parse to list for storage
            vector_str = r[1]
            vector = json.loads(vector_str)
            f.write(json.dumps({"row_id": int(r[0]), "vector": vector}) + "\n")

    # Compute sha256 for each file
    for name in (
        "match.json",
        "events.json",
        "summaries.jsonl",
        "embeddings_t3_small.jsonl",
    ):
        path = match_dir / name
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        checksums[f"{match_id}/{name}"] = sha
        print(f"[build]     {match_id}/{name}  sha256={sha[:12]}...")

    return checksums


def _connect_postgres() -> Any:
    """Open a psycopg2 connection using env vars."""
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        database=os.environ.get("POSTGRES_DB", "rag_challenge"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", "postgres_local_pwd"),
    )


def build_seed(
    output: Path, backend_url: str, match_ids: list[int], skip_pipeline: bool
) -> None:
    """Main entry point for building the seed tarball."""
    if not skip_pipeline:
        _require_api_key()
        for match_id in match_ids:
            _run_full_pipeline(backend_url, match_id, SEED_MATCH_IDS[match_id])

    work_dir = Path.cwd() / ".seed-build-tmp"
    seed_root = work_dir / "seed" / SEED_VERSION
    if work_dir.exists():
        import shutil

        shutil.rmtree(work_dir)
    seed_root.mkdir(parents=True)

    all_checksums: dict[str, str] = {}
    print(f"[build] Exporting {len(match_ids)} match(es) from Postgres")
    with _connect_postgres() as conn:
        for match_id in match_ids:
            all_checksums.update(_export_match(conn, match_id, seed_root))

    # Manifest
    manifest = {
        "version": SEED_VERSION,
        "embedding_model": EMBEDDING_MODEL,
        "matches": [
            {
                "match_id": mid,
                "label": SEED_MATCH_IDS[mid]["label"],
                "competition_id": SEED_MATCH_IDS[mid]["competition_id"],
                "season_id": SEED_MATCH_IDS[mid]["season_id"],
            }
            for mid in match_ids
        ],
        "files": all_checksums,
    }
    manifest_path = seed_root / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Tar it up
    print(f"[build] Creating {output}")
    with tarfile.open(output, "w:gz") as tar:
        tar.add(work_dir / "seed", arcname="seed")

    tar_sha = hashlib.sha256(output.read_bytes()).hexdigest()
    print(f"[build] Done: {output}")
    print(f"[build] sha256: {tar_sha}")
    print("[build]")
    print("[build] Next steps:")
    print("[build]   1. Review the tarball contents:")
    print(f"[build]      tar tzf {output} | head -20")
    print("[build]   2. Upload to GitHub Release:")
    print(f"[build]      gh release create seed/{SEED_VERSION} {output} \\")
    print(f"[build]          --title 'Seed dataset {SEED_VERSION}' \\")
    print(
        "[build]          --notes 'Pre-computed summaries and embeddings for "
        "Euro 2024 + WC 2022 finals.'"
    )
    print("[build]   3. Update SEED_SHA256 in scripts/seed_load.py if needed.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build the seed dataset tarball (maintainer-only)"
    )
    parser.add_argument(
        "--i-have-budget",
        action="store_true",
        help="Explicit flag: you acknowledge this runs paid OpenAI calls.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("./seed-v1.tar.gz"),
        help="Output tarball path (default: ./seed-v1.tar.gz)",
    )
    parser.add_argument(
        "--backend-url",
        default=BACKEND_URL_DEFAULT,
        help=f"Backend base URL (default: {BACKEND_URL_DEFAULT})",
    )
    parser.add_argument(
        "--match-ids",
        default=",".join(str(m) for m in SEED_MATCH_IDS),
        help="Comma-separated list of match_ids to seed",
    )
    parser.add_argument(
        "--skip-pipeline",
        action="store_true",
        help="Skip the full-pipeline step (assume data is already in Postgres)",
    )
    args = parser.parse_args()

    if not args.i_have_budget and not args.skip_pipeline:
        sys.stderr.write(
            "ERROR: pass --i-have-budget to acknowledge this runs paid "
            "OpenAI calls, or --skip-pipeline if data is already in Postgres.\n"
        )
        sys.exit(1)

    match_ids = [int(m) for m in args.match_ids.split(",") if m.strip()]
    unknown = [m for m in match_ids if m not in SEED_MATCH_IDS]
    if unknown:
        sys.stderr.write(f"ERROR: unknown match_ids: {unknown}\n")
        sys.exit(1)

    build_seed(args.output, args.backend_url, match_ids, args.skip_pipeline)


if __name__ == "__main__":
    main()
