"""Unit tests for scripts/seed_build.py — argparse and validation only.

The actual export flow requires a running Postgres + OpenAI key, so it's
covered by the (deferred) integration test. Here we verify the CLI
guardrails and SEED_MATCH_IDS constants.
"""

from __future__ import annotations

import subprocess
import sys

import pytest

from scripts import seed_build


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestSeedConstants:
    def test_seed_version_is_v1(self):
        assert seed_build.SEED_VERSION == "v1"

    def test_seed_match_ids_has_both_finals(self):
        assert 3943043 in seed_build.SEED_MATCH_IDS  # Euro 2024
        assert 3869685 in seed_build.SEED_MATCH_IDS  # World Cup 2022
        assert len(seed_build.SEED_MATCH_IDS) == 2

    def test_euro_2024_metadata_correct(self):
        euro = seed_build.SEED_MATCH_IDS[3943043]
        assert euro["competition_id"] == 55
        assert euro["season_id"] == 282
        assert "Spain" in euro["label"]
        assert "England" in euro["label"]

    def test_world_cup_2022_metadata_correct(self):
        wc = seed_build.SEED_MATCH_IDS[3869685]
        assert wc["competition_id"] == 43
        assert wc["season_id"] == 106
        assert "Argentina" in wc["label"]
        assert "France" in wc["label"]

    def test_embedding_model_is_t3_small(self):
        assert seed_build.EMBEDDING_MODEL == "text-embedding-3-small"


# ---------------------------------------------------------------------------
# CLI: --i-have-budget required
# ---------------------------------------------------------------------------


class TestCliBudgetFlag:
    def test_refuses_without_budget_flag(self, tmp_path):
        """Running without --i-have-budget must fail with non-zero exit."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "scripts.seed_build",
                "--output",
                str(tmp_path / "x.tar.gz"),
            ],
            capture_output=True,
            text=True,
            cwd="/workspace/backend",
        )
        assert result.returncode != 0
        assert "--i-have-budget" in result.stderr

    def test_skip_pipeline_bypasses_budget_check(self, tmp_path, monkeypatch):
        """With --skip-pipeline you don't need --i-have-budget, but you still
        need Postgres — so the call will fail at _connect_postgres, not at
        the budget check."""
        # Run as subprocess to inspect stderr; expect failure at postgres
        # connect, not at budget check.
        env = {"PATH": "/usr/bin:/usr/local/bin", "POSTGRES_HOST": "nonexistent-host-xyz"}
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "scripts.seed_build",
                "--skip-pipeline",
                "--output",
                str(tmp_path / "x.tar.gz"),
            ],
            capture_output=True,
            text=True,
            cwd="/workspace/backend",
            env=env,
        )
        # Should fail later (at postgres connect), not at the budget
        # guard. The guard message should NOT appear.
        assert "--i-have-budget" not in result.stderr


# ---------------------------------------------------------------------------
# CLI: --match-ids validation
# ---------------------------------------------------------------------------


class TestCliMatchIdsValidation:
    def test_rejects_unknown_match_id(self, tmp_path):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "scripts.seed_build",
                "--i-have-budget",
                "--match-ids",
                "999999",
                "--output",
                str(tmp_path / "x.tar.gz"),
            ],
            capture_output=True,
            text=True,
            cwd="/workspace/backend",
        )
        assert result.returncode != 0
        assert "unknown match_ids" in result.stderr

    def test_accepts_single_known_match_id_with_skip_pipeline(self, tmp_path):
        """Accept a single seed match_id and proceed past argparse (will
        fail later at postgres connect, which is OK here)."""
        env = {"PATH": "/usr/bin:/usr/local/bin", "POSTGRES_HOST": "nonexistent-host-xyz"}
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "scripts.seed_build",
                "--skip-pipeline",
                "--match-ids",
                "3943043",
                "--output",
                str(tmp_path / "x.tar.gz"),
            ],
            capture_output=True,
            text=True,
            cwd="/workspace/backend",
            env=env,
        )
        # Argparse passed (no "unknown match_ids"); failure is elsewhere
        assert "unknown match_ids" not in result.stderr


# ---------------------------------------------------------------------------
# _require_api_key
# ---------------------------------------------------------------------------


class TestRequireApiKey:
    def test_exits_when_no_key(self, monkeypatch):
        monkeypatch.delenv("OPENAI_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(SystemExit) as exc_info:
            seed_build._require_api_key()
        assert exc_info.value.code == 2

    def test_passes_when_openai_key_set(self, monkeypatch):
        monkeypatch.setenv("OPENAI_KEY", "sk-test")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        # Should not raise
        seed_build._require_api_key()

    def test_passes_when_openai_api_key_set(self, monkeypatch):
        monkeypatch.delenv("OPENAI_KEY", raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        seed_build._require_api_key()
