"""API tests for CORS middleware behavior."""

import pytest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient


def _make_app(origins: list[str]) -> FastAPI:
    """Create a minimal FastAPI app with CORS middleware for testing."""
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/v1/health")
    def health():
        return {"status": "ok"}

    return app


class TestCorsMiddleware:
    def test_cors_allows_configured_origin(self):
        """3.4 — Verify Access-Control-Allow-Origin present for allowed origin."""
        app = _make_app(["http://localhost:5173", "http://localhost:8000"])
        client = TestClient(app, raise_server_exceptions=False)

        response = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"

    def test_cors_rejects_unknown_origin(self):
        """3.5 — Verify header absent for unknown origin."""
        app = _make_app(["http://localhost:5173", "http://localhost:8000"])
        client = TestClient(app, raise_server_exceptions=False)

        response = client.options(
            "/api/v1/health",
            headers={
                "Origin": "https://evil.example.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert "access-control-allow-origin" not in response.headers
