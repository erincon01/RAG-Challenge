"""Unit tests for CORS origins configuration in Settings."""

import pytest

from app.core.config import Settings


class TestCorsOriginsConfig:
    def test_cors_origins_parsed_from_env(self, monkeypatch):
        """3.1 — Verify comma-separated CORS_ORIGINS is split into a list."""
        monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com,https://admin.example.com")

        s = Settings()
        assert s.cors_origins == [
            "https://app.example.com",
            "https://admin.example.com",
        ]

    def test_cors_origins_default_when_unset(self, monkeypatch):
        """3.2 — Verify default localhost origins when CORS_ORIGINS is not set."""
        monkeypatch.delenv("CORS_ORIGINS", raising=False)

        s = Settings()
        assert "http://localhost:5173" in s.cors_origins
        assert "http://localhost:8000" in s.cors_origins

    def test_cors_origins_strips_whitespace(self, monkeypatch):
        """3.3 — Verify whitespace is trimmed from each origin."""
        monkeypatch.setenv(
            "CORS_ORIGINS", "http://localhost:5173 , http://localhost:8000 "
        )

        s = Settings()
        assert s.cors_origins == [
            "http://localhost:5173",
            "http://localhost:8000",
        ]
