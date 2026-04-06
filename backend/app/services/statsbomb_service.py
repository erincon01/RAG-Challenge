"""StatsBomb discovery and download helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import requests

from app.core.config import get_settings


class StatsBombService:
    """Service for reading StatsBomb competition/match catalogs."""

    def __init__(self):
        self.settings = get_settings()
        self.owner = self.settings.repository.repo_owner
        self.repo = self.settings.repository.repo_name
        self.local_folder = Path(self.settings.repository.local_folder)
        self.base_raw = (
            f"https://raw.githubusercontent.com/{self.owner}/{self.repo}/master/data"
        )
        self.timeout = 60

    def list_competitions(self) -> list[dict[str, Any]]:
        """List competitions from remote StatsBomb repository."""
        url = f"{self.base_raw}/competitions.json"
        response = requests.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def list_matches(self, competition_id: int, season_id: int) -> list[dict[str, Any]]:
        """List matches for a competition/season pair from remote catalog."""
        url = f"{self.base_raw}/matches/{competition_id}/{season_id}.json"
        response = requests.get(url, timeout=self.timeout)
        if response.status_code == 404:
            return []
        response.raise_for_status()
        return response.json()

    def resolve_match_ids(
        self,
        match_ids: list[int] | None,
        competition_id: int | None,
        season_id: int | None,
    ) -> list[int]:
        """Resolve match ids from explicit list or from competition+season."""
        if match_ids:
            return sorted({int(m) for m in match_ids})
        if competition_id is not None and season_id is not None:
            matches = self.list_matches(competition_id, season_id)
            return sorted({int(m["match_id"]) for m in matches if "match_id" in m})
        return []

    def download_match_file(
        self, dataset: str, match_id: int, overwrite: bool = False
    ) -> Path:
        """Download one match file for dataset (events or lineups)."""
        target = self.local_folder / dataset / f"{match_id}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and not overwrite:
            return target

        url = f"{self.base_raw}/{dataset}/{match_id}.json"
        response = requests.get(url, timeout=self.timeout)
        response.raise_for_status()
        target.write_text(response.text, encoding="utf-8")
        return target

    def download_matches_catalog(
        self,
        competition_id: int,
        season_id: int,
        overwrite: bool = False,
    ) -> Path:
        """Download one matches catalog file for competition/season."""
        target = (
            self.local_folder / "matches" / str(competition_id) / f"{season_id}.json"
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and not overwrite:
            return target

        url = f"{self.base_raw}/matches/{competition_id}/{season_id}.json"
        response = requests.get(url, timeout=self.timeout)
        response.raise_for_status()
        target.write_text(response.text, encoding="utf-8")
        return target
