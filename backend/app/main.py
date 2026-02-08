"""
FastAPI main application entry point.

This module initializes the FastAPI application with all routers,
middleware, and configuration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import (
    health,
    matches,
    events,
    chat,
    capabilities,
    statsbomb,
    ingestion,
    embeddings,
)
from app.core.config import get_settings

settings = get_settings()

# Create FastAPI application
app = FastAPI(
    title="RAG Challenge API",
    description="Backend API for RAG Challenge - UEFA Euro match analysis with embeddings",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "RAG Challenge API",
        "version": "0.1.0",
        "status": "running",
        "environment": settings.environment,
        "docs": "/docs",
    }


# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(matches.router, prefix="/api/v1", tags=["matches"])
app.include_router(events.router, prefix="/api/v1", tags=["events"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(capabilities.router, prefix="/api/v1", tags=["capabilities"])
app.include_router(statsbomb.router, prefix="/api/v1", tags=["statsbomb"])
app.include_router(ingestion.router, prefix="/api/v1", tags=["ingestion"])
app.include_router(embeddings.router, prefix="/api/v1", tags=["embeddings"])


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Handle uncaught exceptions globally.

    In production, this should log the error and return a generic message.
    In development, it can return more details.
    """
    if settings.debug:
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "detail": str(exc),
                "type": type(exc).__name__,
            },
        )
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
