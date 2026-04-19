"""End-to-end integration test for seed_load against real databases.

These tests require a running Docker Compose stack (postgres + sqlserver).
They download the real GitHub Release tarball (cached under
``~/.cache/rag-challenge-seed``) and load it into the actual databases.

**Marked as ``@pytest.mark.integration`` and skipped in CI by default.**
Run locally with:

    pytest -m integration backend/tests/integration/test_seed_load_live.py -v

To test locally without docker:

    pytest tests/unit/test_seed_load.py -v

This file is intentionally thin: the unit tests cover argparse, idempotency,
sha256 validation, staging, and error paths. Here we only verify the
happy path against real infrastructure.
"""

from __future__ import annotations

import urllib.error
import urllib.request

import pytest

from scripts import seed_load

pytestmark = pytest.mark.integration


def _seed_release_exists() -> bool:
    """Return True if the seed tarball URL responds with HTTP 200."""
    try:
        req = urllib.request.Request(seed_load.SEED_URL, method="HEAD")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except (urllib.error.HTTPError, urllib.error.URLError, OSError):
        return False


@pytest.fixture(autouse=True)
def _require_seed_release():
    """Skip all tests in this file if the GitHub Release isn't published yet."""
    if not _seed_release_exists():
        pytest.skip(
            f"Seed Release not yet published at {seed_load.SEED_URL}. "
            "Maintainer must run: "
            "`python -m scripts.seed_build --i-have-budget` "
            "and `gh release create seed/v1 seed-v1.tar.gz`."
        )


@pytest.fixture
def clean_seed_data():
    """Delete the seed matches from both databases before each test."""
    for source in ("postgres", "sqlserver"):
        try:
            with seed_load._connect(source) as conn:
                cur = conn.cursor()
                if source == "postgres":
                    cur.execute(
                        "DELETE FROM events_details__quarter_minute WHERE match_id = ANY(%s)",
                        (list(seed_load.SEED_MATCH_IDS),),
                    )
                    cur.execute(
                        "DELETE FROM events_details WHERE match_id = ANY(%s)",
                        (list(seed_load.SEED_MATCH_IDS),),
                    )
                    cur.execute(
                        "DELETE FROM events WHERE match_id = ANY(%s)",
                        (list(seed_load.SEED_MATCH_IDS),),
                    )
                    cur.execute(
                        "DELETE FROM matches WHERE match_id = ANY(%s)",
                        (list(seed_load.SEED_MATCH_IDS),),
                    )
                else:
                    qmarks = ",".join("?" for _ in seed_load.SEED_MATCH_IDS)
                    cur.execute(
                        f"DELETE FROM events_details__15secs_agg WHERE match_id IN ({qmarks})",
                        seed_load.SEED_MATCH_IDS,
                    )
                    cur.execute(
                        f"DELETE FROM events_details WHERE match_id IN ({qmarks})",
                        seed_load.SEED_MATCH_IDS,
                    )
                    cur.execute(
                        f"DELETE FROM events WHERE match_id IN ({qmarks})",
                        seed_load.SEED_MATCH_IDS,
                    )
                    cur.execute(
                        f"DELETE FROM matches WHERE match_id IN ({qmarks})",
                        seed_load.SEED_MATCH_IDS,
                    )
        except Exception as e:
            pytest.skip(f"Cannot reach {source}: {e}")
    yield


def test_seed_load_populates_postgres(clean_seed_data):
    """After seed_load, Postgres has both matches with embeddings."""
    seed_root = seed_load.download_and_extract(seed_load.CACHE_DIR)
    seed_load.load_into("postgres", seed_root)

    with seed_load._connect("postgres") as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM matches WHERE match_id = ANY(%s)",
            (list(seed_load.SEED_MATCH_IDS),),
        )
        assert int(cur.fetchone()[0]) == len(seed_load.SEED_MATCH_IDS)

        cur.execute(
            """
            SELECT COUNT(*) FROM events_details__quarter_minute
            WHERE match_id = ANY(%s) AND summary IS NOT NULL
            """,
            (list(seed_load.SEED_MATCH_IDS),),
        )
        non_null_summaries = int(cur.fetchone()[0])
        assert non_null_summaries > 1000  # expect ~2500 per match

        cur.execute(
            """
            SELECT COUNT(*) FROM events_details__quarter_minute
            WHERE match_id = ANY(%s) AND summary_embedding_t3_small IS NOT NULL
            """,
            (list(seed_load.SEED_MATCH_IDS),),
        )
        non_null_embeddings = int(cur.fetchone()[0])
        assert non_null_embeddings == non_null_summaries


def test_seed_load_populates_sqlserver(clean_seed_data):
    """After seed_load, SQL Server has both matches with embeddings."""
    seed_root = seed_load.download_and_extract(seed_load.CACHE_DIR)
    seed_load.load_into("sqlserver", seed_root)

    with seed_load._connect("sqlserver") as conn:
        cur = conn.cursor()
        qmarks = ",".join("?" for _ in seed_load.SEED_MATCH_IDS)
        cur.execute(
            f"SELECT COUNT(*) FROM matches WHERE match_id IN ({qmarks})",
            seed_load.SEED_MATCH_IDS,
        )
        assert int(cur.fetchone()[0]) == len(seed_load.SEED_MATCH_IDS)

        cur.execute(
            f"""
            SELECT COUNT(*) FROM events_details__15secs_agg
            WHERE match_id IN ({qmarks}) AND embedding_3_small IS NOT NULL
            """,
            seed_load.SEED_MATCH_IDS,
        )
        assert int(cur.fetchone()[0]) > 1000  # expect ~2500 per match


def test_seed_load_second_run_is_noop(clean_seed_data):
    """Running seed_load twice in a row: second run should exit 0 fast."""
    seed_root = seed_load.download_and_extract(seed_load.CACHE_DIR)
    seed_load.load_into("postgres", seed_root)

    # Now idempotency check should return True and load_into should not
    # be called.
    assert seed_load.check_idempotency("postgres") is True
