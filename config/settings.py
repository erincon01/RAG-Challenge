"""
Centralized configuration management using Pydantic Settings.

This module provides type-safe, validated configuration management for the RAG Challenge application.
All environment variables are read once at startup and validated, following fail-fast principle.
"""

import os
from typing import Literal, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseSettings):
    """Database configuration for Postgres and SQL Server."""

    # PostgreSQL Azure Configuration
    postgres_host: str = Field(default="", alias="DB_SERVER_AZURE_POSTGRES")
    postgres_database: str = Field(default="", alias="DB_NAME_AZURE_POSTGRES")
    postgres_user: str = Field(default="", alias="DB_USER_AZURE_POSTGRES")
    postgres_password: str = Field(default="", alias="DB_PASSWORD_AZURE_POSTGRES")

    # SQL Server Azure Configuration
    sqlserver_host: str = Field(default="", alias="DB_SERVER_AZURE")
    sqlserver_database: str = Field(default="", alias="DB_NAME_AZURE")
    sqlserver_user: str = Field(default="", alias="DB_USER_AZURE")
    sqlserver_password: str = Field(default="", alias="DB_PASSWORD_AZURE")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


class OpenAIConfig(BaseSettings):
    """OpenAI/Azure OpenAI configuration."""

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

    def validate_required_for_azure(self) -> None:
        """
        Validate that all Azure-specific configuration is present.
        Call this method at startup when running in Azure mode.
        """
        if not self.is_azure():
            return

        missing = []

        # Check database config
        if not self.database.postgres_host:
            missing.append("DB_SERVER_AZURE_POSTGRES")
        if not self.database.postgres_database:
            missing.append("DB_NAME_AZURE_POSTGRES")
        if not self.database.postgres_user:
            missing.append("DB_USER_AZURE_POSTGRES")
        if not self.database.postgres_password:
            missing.append("DB_PASSWORD_AZURE_POSTGRES")

        if not self.database.sqlserver_host:
            missing.append("DB_SERVER_AZURE")
        if not self.database.sqlserver_database:
            missing.append("DB_NAME_AZURE")
        if not self.database.sqlserver_user:
            missing.append("DB_USER_AZURE")
        if not self.database.sqlserver_password:
            missing.append("DB_PASSWORD_AZURE")

        # Check OpenAI config
        if not self.openai.endpoint:
            missing.append("OPENAI_ENDPOINT")
        if not self.openai.api_key:
            missing.append("OPENAI_KEY")

        if missing:
            raise ValueError(
                f"Missing required configuration for Azure environment: {', '.join(missing)}"
            )


# Global settings instance - initialized once at module import
settings = Settings()


def get_settings() -> Settings:
    """
    Get the global settings instance.
    Useful for dependency injection in FastAPI.
    """
    return settings
