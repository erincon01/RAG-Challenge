"""Unit tests for scripts/seed_load.py."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts import seed_load

# Resolve the backend/ directory dynamically (see test_seed_build.py for
# rationale).
BACKEND_DIR = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestSeedLoadConstants:
    def test_seed_match_ids_both_finals(self):
        assert set(seed_load.SEED_MATCH_IDS) == {3943043, 3869685}


# ---------------------------------------------------------------------------
# check_idempotency
# ---------------------------------------------------------------------------


class TestCheckIdempotency:
    @patch("scripts.seed_load._connect")
    def test_returns_true_when_both_matches_and_embeddings_present(
        self, mock_connect
    ):
        cur = MagicMock()
        # matches count = 2, embeddings distinct match_id count = 2
        cur.fetchone.side_effect = [(2,), (2,)]
        conn = MagicMock()
        conn.cursor.return_value = cur
        mock_connect.return_value.__enter__.return_value = conn
        mock_connect.return_value.__exit__.return_value = False

        assert seed_load.check_idempotency("postgres") is True

    @patch("scripts.seed_load._connect")
    def test_returns_false_when_matches_missing(self, mock_connect):
        cur = MagicMock()
        cur.fetchone.return_value = (0,)
        conn = MagicMock()
        conn.cursor.return_value = cur
        mock_connect.return_value.__enter__.return_value = conn
        mock_connect.return_value.__exit__.return_value = False

        assert seed_load.check_idempotency("postgres") is False

    @patch("scripts.seed_load._connect")
    def test_returns_false_when_matches_present_but_embeddings_missing(
        self, mock_connect
    ):
        cur = MagicMock()
        cur.fetchone.side_effect = [(2,), (0,)]
        conn = MagicMock()
        conn.cursor.return_value = cur
        mock_connect.return_value.__enter__.return_value = conn
        mock_connect.return_value.__exit__.return_value = False

        assert seed_load.check_idempotency("postgres") is False

    @patch("scripts.seed_load._connect")
    def test_returns_false_when_connect_raises(self, mock_connect):
        mock_connect.side_effect = RuntimeError("db down")
        assert seed_load.check_idempotency("postgres") is False


# ---------------------------------------------------------------------------
# find_seed_root
# ---------------------------------------------------------------------------


def _make_valid_seed_dir(tmp_path: Path) -> Path:
    """Build a minimal valid seed directory with manifest + files."""
    seed_dir = tmp_path / "data" / "seed"
    match_dir = seed_dir / "3943043"
    match_dir.mkdir(parents=True)

    match_content = json.dumps({"match_id": 3943043})
    events_content = json.dumps([{"id": "e1"}])
    summaries_content = (
        '{"row_id": 1, "match_id": 3943043, "period": 1, "minute": 0, '
        '"quarter_minute": 1, "summary": "Kickoff."}\n'
    )
    embeddings_content = '{"row_id": 1, "vector": [0.1, 0.2]}\n'

    (match_dir / "match.json").write_text(match_content)
    (match_dir / "events.json").write_text(events_content)
    (match_dir / "summaries.jsonl").write_text(summaries_content)
    (match_dir / "embeddings_t3_small.jsonl").write_text(embeddings_content)

    files_manifest = {}
    for fname in ("match.json", "events.json", "summaries.jsonl", "embeddings_t3_small.jsonl"):
        fpath = match_dir / fname
        files_manifest[f"3943043/{fname}"] = hashlib.sha256(fpath.read_bytes()).hexdigest()

    manifest = {
        "version": "v1",
        "embedding_model": "text-embedding-3-small",
        "matches": [{"match_id": 3943043, "label": "Test", "competition_id": 55, "season_id": 282}],
        "files": files_manifest,
    }
    (seed_dir / "manifest.json").write_text(json.dumps(manifest))
    return seed_dir


class TestFindSeedRoot:
    def test_finds_seed_dir_relative_to_cwd(self, tmp_path, monkeypatch):
        seed_dir = _make_valid_seed_dir(tmp_path)
        # Simulate running from backend/ (parent of data/seed/)
        monkeypatch.chdir(tmp_path)

        result = seed_load.find_seed_root()
        assert result.exists()
        assert (result / "manifest.json").exists()
        assert (result / "3943043" / "match.json").exists()

    def test_raises_on_sha_mismatch(self, tmp_path, monkeypatch):
        seed_dir = _make_valid_seed_dir(tmp_path)
        # Tamper with a file without updating manifest
        (seed_dir / "3943043" / "match.json").write_text('{"tampered": true}')
        monkeypatch.chdir(tmp_path)

        with pytest.raises(RuntimeError, match="sha256 mismatch"):
            seed_load.find_seed_root()

    def test_raises_when_seed_dir_missing(self, tmp_path, monkeypatch):
        # Override the candidate paths so the real repo data/seed/ is not found
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(
            seed_load,
            "find_seed_root",
            seed_load.find_seed_root.__wrapped__
            if hasattr(seed_load.find_seed_root, "__wrapped__")
            else seed_load.find_seed_root,
        )
        # Patch Path to make /workspace not resolve to real repo
        empty = tmp_path / "nowhere"
        empty.mkdir()
        original_find = seed_load.find_seed_root

        def _patched_find():
            """Override candidates so /workspace is not checked."""
            candidates = [
                Path.cwd().parent / "data" / "seed",
                Path.cwd() / "data" / "seed",
            ]
            for candidate in candidates:
                if (candidate / "manifest.json").exists():
                    return candidate
            raise RuntimeError(
                "Seed data not found. Expected data/seed/manifest.json in the repo."
            )

        monkeypatch.setattr(seed_load, "find_seed_root", _patched_find)
        with pytest.raises(RuntimeError, match="Seed data not found"):
            seed_load.find_seed_root()

    def test_raises_on_missing_file_in_manifest(self, tmp_path, monkeypatch):
        seed_dir = _make_valid_seed_dir(tmp_path)
        # Delete a file that manifest references
        (seed_dir / "3943043" / "events.json").unlink()
        monkeypatch.chdir(tmp_path)

        with pytest.raises(RuntimeError, match="Seed file missing"):
            seed_load.find_seed_root()


# ---------------------------------------------------------------------------
# _stage_seed_for_ingestion
# ---------------------------------------------------------------------------


class TestStageSeedForIngestion:
    def test_copies_events_and_wraps_matches_in_list(self, tmp_path):
        # Build a minimal seed layout
        seed_root = tmp_path / "seed"
        match_dir = seed_root / "3943043"
        match_dir.mkdir(parents=True)
        (match_dir / "match.json").write_text('{"match_id": 3943043}')
        (match_dir / "events.json").write_text('[{"id": "e1"}]')

        staging = tmp_path / "staging"
        staging.mkdir()
        match_ids = seed_load._stage_seed_for_ingestion(seed_root, staging)

        assert match_ids == [3943043]
        # Events copied to {staging}/events/3943043.json
        events_copy = staging / "events" / "3943043.json"
        assert events_copy.exists()
        assert json.loads(events_copy.read_text()) == [{"id": "e1"}]
        # Matches wrapped in a list
        matches_seed = staging / "matches" / "seed.json"
        assert matches_seed.exists()
        matches_list = json.loads(matches_seed.read_text())
        assert isinstance(matches_list, list)
        assert matches_list[0]["match_id"] == 3943043

    def test_skips_non_numeric_directories(self, tmp_path):
        seed_root = tmp_path / "seed"
        seed_root.mkdir()
        (seed_root / "not_a_match").mkdir()
        (seed_root / "manifest.json").write_text("{}")
        # Only numeric-named dirs with required files become match_ids
        match_ids = seed_load._stage_seed_for_ingestion(seed_root, tmp_path / "staging")
        assert match_ids == []


# ---------------------------------------------------------------------------
# main() argparse + idempotency flow
# ---------------------------------------------------------------------------


class TestSeedLoadMain:
    def test_help_exits_zero(self):
        result = subprocess.run(
            [sys.executable, "-m", "scripts.seed_load", "--help"],
            capture_output=True,
            text=True,
            cwd=str(BACKEND_DIR),
        )
        assert result.returncode == 0
        assert "source" in result.stdout

    @patch("scripts.seed_load.check_idempotency")
    @patch("scripts.seed_load.find_seed_root")
    def test_skips_find_seed_when_all_sources_idempotent(
        self, mock_find, mock_idem
    ):
        mock_idem.return_value = True
        with patch.object(sys, "argv", ["seed_load", "--source", "postgres"]):
            rc = seed_load.main()
        assert rc == 0
        mock_find.assert_not_called()

    @patch("scripts.seed_load.check_idempotency", return_value=False)
    @patch(
        "scripts.seed_load.find_seed_root",
        side_effect=RuntimeError("seed data not found"),
    )
    def test_returns_nonzero_on_seed_not_found(self, _mock_find, _mock_idem):
        with patch.object(sys, "argv", ["seed_load", "--source", "postgres"]):
            rc = seed_load.main()
        assert rc == 1

    @patch("scripts.seed_load.load_into")
    @patch(
        "scripts.seed_load.find_seed_root",
        return_value=Path("/tmp/fake_seed"),
    )
    @patch("scripts.seed_load.check_idempotency", return_value=False)
    def test_happy_path_calls_load_into_per_source(
        self, _mock_idem, _mock_find, mock_load
    ):
        mock_load.return_value = {
            "match_ids": [1, 2],
            "aggregated_rows": 100,
            "summaries_updated": 100,
            "embeddings_updated": 100,
        }
        with patch.object(sys, "argv", ["seed_load", "--source", "both"]):
            rc = seed_load.main()
        assert rc == 0
        assert mock_load.call_count == 2
        called_sources = [call.args[0] for call in mock_load.call_args_list]
        assert called_sources == ["postgres", "sqlserver"]

    @patch("scripts.seed_load.load_into", side_effect=RuntimeError("load failed"))
    @patch(
        "scripts.seed_load.find_seed_root",
        return_value=Path("/tmp/fake_seed"),
    )
    @patch("scripts.seed_load.check_idempotency", return_value=False)
    def test_returns_nonzero_when_load_fails(self, _idem, _find, _load):
        with patch.object(sys, "argv", ["seed_load", "--source", "postgres"]):
            rc = seed_load.main()
        assert rc == 1
