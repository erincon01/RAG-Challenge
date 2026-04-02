"""Unit tests for IngestionService utility methods."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.services.ingestion_service import IngestionService


# ---------------------------------------------------------------------------
# _parse_match_ids
# ---------------------------------------------------------------------------

class TestParseMatchIds:
    def test_empty_list_returns_empty(self):
        assert IngestionService._parse_match_ids([]) == []

    def test_none_returns_empty(self):
        assert IngestionService._parse_match_ids(None) == []

    def test_deduplicates_and_sorts(self):
        result = IngestionService._parse_match_ids([3, 1, 2, 1])
        assert result == [1, 2, 3]

    def test_preserves_single_id(self):
        result = IngestionService._parse_match_ids([3943043])
        assert result == [3943043]


# ---------------------------------------------------------------------------
# _safe_unlink
# ---------------------------------------------------------------------------

class TestSafeUnlink:
    def test_deletes_existing_file(self, tmp_path):
        f = tmp_path / "test.json"
        f.write_text("{}")
        result = IngestionService._safe_unlink(f)
        assert result is True
        assert not f.exists()

    def test_returns_false_for_nonexistent_file(self, tmp_path):
        f = tmp_path / "missing.json"
        result = IngestionService._safe_unlink(f)
        assert result is False

    def test_returns_false_for_directory(self, tmp_path):
        d = tmp_path / "subdir"
        d.mkdir()
        result = IngestionService._safe_unlink(d)
        assert result is False


# ---------------------------------------------------------------------------
# _prune_empty_dirs
# ---------------------------------------------------------------------------

class TestPruneEmptyDirs:
    def test_prunes_empty_parent_dir(self, tmp_path):
        subdir = tmp_path / "a" / "b"
        subdir.mkdir(parents=True)
        IngestionService._prune_empty_dirs(subdir, tmp_path)
        assert not subdir.exists()
        assert not (tmp_path / "a").exists()

    def test_stops_at_stop_path(self, tmp_path):
        subdir = tmp_path / "data"
        subdir.mkdir()
        IngestionService._prune_empty_dirs(subdir, tmp_path)
        # tmp_path itself should not be deleted (it's the stop boundary)
        assert tmp_path.exists()

    def test_does_not_prune_non_empty_dir(self, tmp_path):
        subdir = tmp_path / "data"
        subdir.mkdir()
        (subdir / "file.txt").write_text("data")
        IngestionService._prune_empty_dirs(subdir, tmp_path)
        assert subdir.exists()


# ---------------------------------------------------------------------------
# _iter_matches_from_local
# ---------------------------------------------------------------------------

class TestIterMatchesFromLocal:
    def test_empty_when_matches_dir_missing(self, tmp_path):
        svc = IngestionService.__new__(IngestionService)
        svc.local_folder = tmp_path
        result = list(svc._iter_matches_from_local())
        assert result == []

    def test_yields_matches_from_json_files(self, tmp_path):
        matches_dir = tmp_path / "matches" / "55"
        matches_dir.mkdir(parents=True)
        matches_data = [
            {"match_id": 1, "competition": {"competition_id": 55}},
            {"match_id": 2, "competition": {"competition_id": 55}},
        ]
        (matches_dir / "282.json").write_text(json.dumps(matches_data))

        svc = IngestionService.__new__(IngestionService)
        svc.local_folder = tmp_path
        result = list(svc._iter_matches_from_local())
        assert len(result) == 2

    def test_skips_items_without_match_id(self, tmp_path):
        matches_dir = tmp_path / "matches"
        matches_dir.mkdir(parents=True)
        matches_data = [
            {"match_id": 1},
            {"no_match_id": True},
        ]
        (matches_dir / "file.json").write_text(json.dumps(matches_data))

        svc = IngestionService.__new__(IngestionService)
        svc.local_folder = tmp_path
        result = list(svc._iter_matches_from_local())
        assert len(result) == 1

    def test_skips_non_list_json(self, tmp_path):
        matches_dir = tmp_path / "matches"
        matches_dir.mkdir(parents=True)
        (matches_dir / "bad.json").write_text('{"not": "a list"}')

        svc = IngestionService.__new__(IngestionService)
        svc.local_folder = tmp_path
        result = list(svc._iter_matches_from_local())
        assert result == []

    def test_skips_invalid_json_files(self, tmp_path):
        matches_dir = tmp_path / "matches"
        matches_dir.mkdir(parents=True)
        (matches_dir / "broken.json").write_text("not json at all {")

        svc = IngestionService.__new__(IngestionService)
        svc.local_folder = tmp_path
        result = list(svc._iter_matches_from_local())
        assert result == []


# ---------------------------------------------------------------------------
# clear_downloaded_files
# ---------------------------------------------------------------------------

class TestClearDownloadedFiles:
    def _make_svc(self, tmp_path):
        svc = IngestionService.__new__(IngestionService)
        svc.local_folder = tmp_path
        svc.statsbomb = MagicMock()
        svc.settings = MagicMock()
        return svc

    def test_delete_all_removes_dataset_dirs(self, tmp_path):
        events_dir = tmp_path / "events"
        events_dir.mkdir()
        (events_dir / "1.json").write_text("{}")

        svc = self._make_svc(tmp_path)
        result = svc.clear_downloaded_files(datasets=["events"], delete_all=True)

        assert not events_dir.exists()
        assert result["filters"]["delete_all"] is True

    def test_delete_specific_match_id(self, tmp_path):
        events_dir = tmp_path / "events"
        events_dir.mkdir()
        (events_dir / "42.json").write_text("{}")
        (events_dir / "43.json").write_text("{}")

        svc = self._make_svc(tmp_path)
        result = svc.clear_downloaded_files(datasets=["events"], match_ids=[42])

        assert not (events_dir / "42.json").exists()
        assert (events_dir / "43.json").exists()

    def test_delete_all_json_when_no_match_id_filter(self, tmp_path):
        events_dir = tmp_path / "events"
        events_dir.mkdir()
        (events_dir / "1.json").write_text("{}")
        (events_dir / "2.json").write_text("{}")

        svc = self._make_svc(tmp_path)
        result = svc.clear_downloaded_files(datasets=["events"], match_ids=[])

        assert result["deleted_count"] >= 2

    def test_returns_result_dict_structure(self, tmp_path):
        svc = self._make_svc(tmp_path)
        result = svc.clear_downloaded_files(datasets=["events"])

        assert "deleted_count" in result
        assert "deleted_files" in result
        assert "deleted_dirs" in result
        assert "filters" in result

    def test_invalid_dataset_raises_value_error(self, tmp_path):
        svc = self._make_svc(tmp_path)
        with pytest.raises(ValueError):
            svc.clear_downloaded_files(datasets=["invalid_only"])

    def test_delete_competitions_file_when_delete_all(self, tmp_path):
        comp_file = tmp_path / "competitions.json"
        comp_file.write_text("[]")

        svc = self._make_svc(tmp_path)
        result = svc.clear_downloaded_files(datasets=["matches"], delete_all=True)

        assert not comp_file.exists()

    def test_matches_dataset_deletes_by_competition_season(self, tmp_path):
        matches_dir = tmp_path / "matches" / "55"
        matches_dir.mkdir(parents=True)
        match_file = matches_dir / "282.json"
        match_file.write_text("[]")

        svc = self._make_svc(tmp_path)
        result = svc.clear_downloaded_files(
            datasets=["matches"],
            competition_id=55,
            season_id=282,
        )

        assert not match_file.exists()
