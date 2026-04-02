"""
Unit tests for StatsBombService — mocked HTTP requests.

No real network calls.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest
import requests

from app.services.statsbomb_service import StatsBombService


@pytest.fixture
def service():
    with patch("app.services.statsbomb_service.get_settings") as mock_settings:
        settings = MagicMock()
        settings.repository.repo_owner = "statsbomb"
        settings.repository.repo_name = "open-data"
        settings.repository.local_folder = "/tmp/statsbomb_test"
        mock_settings.return_value = settings
        yield StatsBombService()


COMPETITIONS_DATA = [
    {"competition_id": 55, "season_id": 282, "competition_name": "UEFA Euro", "season_name": "2024"},
    {"competition_id": 11, "season_id": 90, "competition_name": "La Liga", "season_name": "2023/24"},
]

MATCHES_DATA = [
    {"match_id": 3943043, "home_team": {"home_team_name": "Spain"}, "away_team": {"away_team_name": "England"}},
    {"match_id": 3943044, "home_team": {"home_team_name": "France"}, "away_team": {"away_team_name": "Portugal"}},
]


def _mock_response(data, status_code=200):
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = data
    response.text = json.dumps(data)
    if status_code >= 400:
        response.raise_for_status.side_effect = requests.HTTPError(f"HTTP {status_code}")
    else:
        response.raise_for_status.return_value = None
    return response


# ===========================================================================
# list_competitions
# ===========================================================================

class TestListCompetitions:
    def test_returns_competition_list(self, service):
        with patch("requests.get", return_value=_mock_response(COMPETITIONS_DATA)):
            result = service.list_competitions()

        assert len(result) == 2
        assert result[0]["competition_id"] == 55

    def test_calls_correct_url(self, service):
        with patch("requests.get", return_value=_mock_response([])) as mock_get:
            service.list_competitions()

        url = mock_get.call_args[0][0]
        assert "competitions.json" in url
        assert "raw.githubusercontent.com" in url

    def test_raises_on_http_error(self, service):
        with patch("requests.get", return_value=_mock_response({}, 500)):
            with pytest.raises(requests.HTTPError):
                service.list_competitions()


# ===========================================================================
# list_matches
# ===========================================================================

class TestListMatches:
    def test_returns_match_list(self, service):
        with patch("requests.get", return_value=_mock_response(MATCHES_DATA)):
            result = service.list_matches(55, 282)

        assert len(result) == 2
        assert result[0]["match_id"] == 3943043

    def test_returns_empty_list_on_404(self, service):
        with patch("requests.get", return_value=_mock_response({}, 404)):
            result = service.list_matches(55, 999)

        assert result == []

    def test_raises_on_500(self, service):
        with patch("requests.get", return_value=_mock_response({}, 500)):
            with pytest.raises(requests.HTTPError):
                service.list_matches(55, 282)

    def test_calls_correct_url(self, service):
        with patch("requests.get", return_value=_mock_response([])) as mock_get:
            service.list_matches(55, 282)

        url = mock_get.call_args[0][0]
        assert "matches/55/282.json" in url


# ===========================================================================
# resolve_match_ids
# ===========================================================================

class TestResolveMatchIds:
    def test_returns_explicit_match_ids_sorted(self, service):
        result = service.resolve_match_ids([3, 1, 2], None, None)
        assert result == [1, 2, 3]

    def test_deduplicates_match_ids(self, service):
        result = service.resolve_match_ids([1, 1, 2, 2], None, None)
        assert result == [1, 2]

    def test_resolves_from_competition_and_season(self, service):
        with patch("requests.get", return_value=_mock_response(MATCHES_DATA)):
            result = service.resolve_match_ids(None, 55, 282)

        assert sorted(result) == [3943043, 3943044]

    def test_returns_empty_when_no_inputs(self, service):
        result = service.resolve_match_ids(None, None, None)
        assert result == []

    def test_explicit_ids_take_precedence_over_competition(self, service):
        with patch("requests.get") as mock_get:
            result = service.resolve_match_ids([999], 55, 282)

        assert result == [999]
        mock_get.assert_not_called()


# ===========================================================================
# download_match_file
# ===========================================================================

class TestDownloadMatchFile:
    def test_skips_if_exists_and_no_overwrite(self, service, tmp_path):
        service.local_folder = tmp_path
        target = tmp_path / "events" / "3943043.json"
        target.parent.mkdir(parents=True)
        target.write_text('{"existing": true}')

        with patch("requests.get") as mock_get:
            result = service.download_match_file("events", 3943043, overwrite=False)

        mock_get.assert_not_called()
        assert result == target

    def test_downloads_if_overwrite_true(self, service, tmp_path):
        service.local_folder = tmp_path
        target = tmp_path / "events" / "3943043.json"
        target.parent.mkdir(parents=True)
        target.write_text('{"old": true}')

        content = '{"new": true}'
        with patch("requests.get", return_value=_mock_response(json.loads(content))) as mock_get:
            # need text attribute
            resp = _mock_response({})
            resp.text = content
            mock_get.return_value = resp
            service.download_match_file("events", 3943043, overwrite=True)

        assert target.read_text() == content

    def test_creates_parent_directories(self, service, tmp_path):
        service.local_folder = tmp_path
        resp = _mock_response({})
        resp.text = '[]'

        with patch("requests.get", return_value=resp):
            result = service.download_match_file("lineups", 111, overwrite=True)

        assert result.parent.exists()

    def test_raises_on_http_error(self, service, tmp_path):
        service.local_folder = tmp_path
        with patch("requests.get", return_value=_mock_response({}, 404)):
            with pytest.raises(requests.HTTPError):
                service.download_match_file("events", 9999999, overwrite=True)


# ===========================================================================
# download_matches_catalog
# ===========================================================================

class TestDownloadMatchesCatalog:
    def test_skips_if_exists_and_no_overwrite(self, service, tmp_path):
        service.local_folder = tmp_path
        target = tmp_path / "matches" / "55" / "282.json"
        target.parent.mkdir(parents=True)
        target.write_text("[]")

        with patch("requests.get") as mock_get:
            result = service.download_matches_catalog(55, 282, overwrite=False)

        mock_get.assert_not_called()
        assert result == target

    def test_downloads_catalog(self, service, tmp_path):
        service.local_folder = tmp_path
        content = json.dumps(MATCHES_DATA)
        resp = _mock_response(MATCHES_DATA)
        resp.text = content

        with patch("requests.get", return_value=resp):
            result = service.download_matches_catalog(55, 282, overwrite=True)

        assert result.exists()
        assert result.read_text() == content
