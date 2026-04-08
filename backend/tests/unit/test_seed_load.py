"""Unit tests for scripts/seed_load.py."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tarfile
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
    def test_seed_version_matches_build(self):
        assert seed_load.SEED_VERSION == "v1"

    def test_seed_match_ids_both_finals(self):
        assert set(seed_load.SEED_MATCH_IDS) == {3943043, 3869685}

    def test_seed_url_points_to_github_release(self):
        assert "github.com/erincon01/RAG-Challenge/releases" in seed_load.SEED_URL
        assert "seed-v1.tar.gz" in seed_load.SEED_URL


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
# download_and_extract
# ---------------------------------------------------------------------------


def _make_valid_tarball(tmp_path: Path) -> Path:
    """Build a minimal valid seed tarball with manifest + files."""
    build = tmp_path / "build"
    seed_dir = build / "seed" / "v1"
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

    tarball = tmp_path / "seed-v1.tar.gz"
    with tarfile.open(tarball, "w:gz") as tar:
        tar.add(build / "seed", arcname="seed")
    return tarball


class TestDownloadAndExtract:
    def test_extracts_valid_tarball_and_verifies_manifest(self, tmp_path, monkeypatch):
        tarball = _make_valid_tarball(tmp_path)
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()

        # Pre-place the tarball so download is skipped
        import shutil as _sh

        _sh.copyfile(tarball, cache_dir / "seed-v1.tar.gz")

        result = seed_load.download_and_extract(cache_dir)
        assert result.exists()
        assert (result / "manifest.json").exists()
        assert (result / "3943043" / "match.json").exists()

    def test_raises_on_sha_mismatch(self, tmp_path):
        tarball = _make_valid_tarball(tmp_path)
        # Unpack, tamper, re-pack
        extract_dir = tmp_path / "extracted"
        extract_dir.mkdir()
        with tarfile.open(tarball, "r:gz") as tar:
            tar.extractall(extract_dir, filter="data")
        (extract_dir / "seed" / "v1" / "3943043" / "match.json").write_text(
            '{"tampered": true}'
        )
        # Re-pack without updating manifest
        tampered = tmp_path / "tampered.tar.gz"
        with tarfile.open(tampered, "w:gz") as tar:
            tar.add(extract_dir / "seed", arcname="seed")

        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        import shutil as _sh

        _sh.copyfile(tampered, cache_dir / "seed-v1.tar.gz")

        with pytest.raises(RuntimeError, match="sha256 mismatch"):
            seed_load.download_and_extract(cache_dir)

    def test_raises_on_missing_manifest(self, tmp_path):
        # Build a tarball without manifest.json
        build = tmp_path / "build"
        seed_dir = build / "seed" / "v1" / "3943043"
        seed_dir.mkdir(parents=True)
        (seed_dir / "match.json").write_text("{}")
        tarball = tmp_path / "bad.tar.gz"
        with tarfile.open(tarball, "w:gz") as tar:
            tar.add(build / "seed", arcname="seed")

        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        import shutil as _sh

        _sh.copyfile(tarball, cache_dir / "seed-v1.tar.gz")
        with pytest.raises(RuntimeError, match="manifest.json"):
            seed_load.download_and_extract(cache_dir)


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
    @patch("scripts.seed_load.download_and_extract")
    def test_skips_download_when_all_sources_idempotent(
        self, mock_download, mock_idem
    ):
        mock_idem.return_value = True
        with patch.object(sys, "argv", ["seed_load", "--source", "postgres"]):
            rc = seed_load.main()
        assert rc == 0
        mock_download.assert_not_called()

    @patch("scripts.seed_load.check_idempotency", return_value=False)
    @patch(
        "scripts.seed_load.download_and_extract",
        side_effect=RuntimeError("network error"),
    )
    def test_returns_nonzero_on_download_failure(self, _mock_dl, _mock_idem):
        with patch.object(sys, "argv", ["seed_load", "--source", "postgres"]):
            rc = seed_load.main()
        assert rc == 1

    @patch("scripts.seed_load.load_into")
    @patch(
        "scripts.seed_load.download_and_extract",
        return_value=Path("/tmp/fake_seed"),
    )
    @patch("scripts.seed_load.check_idempotency", return_value=False)
    def test_happy_path_calls_load_into_per_source(
        self, _mock_idem, _mock_dl, mock_load
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
        "scripts.seed_load.download_and_extract",
        return_value=Path("/tmp/fake_seed"),
    )
    @patch("scripts.seed_load.check_idempotency", return_value=False)
    def test_returns_nonzero_when_load_fails(self, _idem, _dl, _load):
        with patch.object(sys, "argv", ["seed_load", "--source", "postgres"]):
            rc = seed_load.main()
        assert rc == 1
