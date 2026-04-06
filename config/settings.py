"""
Centralized configuration management using Pydantic Settings.

This module provides type-safe, validated configuration management for the RAG Challenge application.
All environment variables are read once at startup and validated, following fail-fast principle.
"""

from typing import List, Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseSettings):
    """Database configuration for Postgres and SQL Server."""

    # PostgreSQL
    postgres_host: str = Field(default="", alias="POSTGRES_HOST")
    postgres_database: str = Field(default="", alias="POSTGRES_DB")
    postgres_user: str = Field(default="", alias="POSTGRES_USER")
    postgres_password: str = Field(default="", alias="POSTGRES_PASSWORD")

    # SQL Server
    sqlserver_host: str = Field(default="", alias="SQLSERVER_HOST")
    sqlserver_database: str = Field(default="", alias="SQLSERVER_DB")
    sqlserver_user: str = Field(default="", alias="SQLSERVER_USER")
    sqlserver_password: str = Field(default="", alias="SQLSERVER_PASSWORD")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


class OpenAIConfig(BaseSettings):
    """OpenAI/Azure OpenAI configuration."""

    provider: str = Field(default="azure", alias="OPENAI_PROVIDER")  # "azure" or "openai"
    endpoint: str = Field(default="", alias="OPENAI_ENDPOINT")
    api_key: str = Field(default="", alias="OPENAI_KEY")
    model: str = Field(default="gpt-4", alias="OPENAI_MODEL")
    model2: str = Field(default="gpt-4", alias="OPENAI_MODEL2")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


class RepositoryConfig(BaseSettings):
    """GitHub repository and local storage configuration."""

    repo_owner: str = Field(default="statsbomb", alias="REPO_OWNER")
    repo_name: str = Field(default="open-data", alias="REPO_NAME")
    local_folder: str = Field(default="./data", alias="LOCAL_FOLDER")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


class Settings(BaseSettings):
    """Main application settings."""

    # Environment
    environment: Literal["local", "azure", "test"] = Field(default="local")

    # Sub-configurations
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    repository: RepositoryConfig = Field(default_factory=RepositoryConfig)

    # CORS
    cors_origins_str: str = Field(
        default="http://localhost:5173,http://localhost:8000",
        alias="CORS_ORIGINS",
    )

    @property
    def cors_origins(self) -> List[str]:
        """Return CORS origins as a list, splitting on commas."""
        return [origin.strip() for origin in self.cors_origins_str.split(",")]

    # Application settings
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment is one of the allowed values."""
        allowed = ["local", "azure", "test"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of {allowed}, got {v}")
        return v

    def is_azure(self) -> bool:
        """Check if running in Azure environment."""
        return self.environment == "azure"

    def is_local(self) -> bool:
        """Check if running in local environment."""
        return self.environment == "local"

    def is_test(self) -> bool:
        """Check if running in test environment."""
        return self.environment == "test"

    def validate_required(self) -> None:
        """
        Validate that all required configuration is present.
        Call this method at startup when running in production-like mode.
        """
        if self.is_test():
            return

        missing = []

        # Check database config
        if not self.database.postgres_host:
            missing.append("POSTGRES_HOST")
        if not self.database.postgres_database:
            missing.append("POSTGRES_DB")
        if not self.database.postgres_user:
            missing.append("POSTGRES_USER")
        if not self.database.postgres_password:
            missing.append("POSTGRES_PASSWORD")

        if not self.database.sqlserver_host:
            missing.append("SQLSERVER_HOST")
        if not self.database.sqlserver_database:
            missing.append("SQLSERVER_DB")
        if not self.database.sqlserver_user:
            missing.append("SQLSERVER_USER")
        if not self.database.sqlserver_password:
            missing.append("SQLSERVER_PASSWORD")

        # Check OpenAI config
        if not self.openai.endpoint:
            missing.append("OPENAI_ENDPOINT")
        if not self.openai.api_key:
            missing.append("OPENAI_KEY")

        if missing:
            raise ValueError(
                f"Missing required configuration: {', '.join(missing)}"
            )


# Global settings instance - initialized once at module import
settings = Settings()


def get_settings() -> Settings:
    """
    Get the global settings instance.
    Useful for dependency injection in FastAPI.
    """
    return settings
