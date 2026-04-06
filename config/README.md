# Configuration Module

This module provides centralized, type-safe configuration management for the RAG Challenge application using Pydantic Settings.

## Features

- **Type-safe**: All configuration values are validated using Pydantic models
- **Environment-aware**: Supports `local`, `azure`, and `test` environments
- **Fail-fast**: Missing required configuration causes startup failure
- **Single source of truth**: All `os.getenv()` calls should be replaced with this module
- **IDE-friendly**: Full autocomplete and type hints

## Usage

### Basic Usage

```python
from config import settings

# Access database configuration
postgres_host = settings.database.postgres_host
postgres_db = settings.database.postgres_database

# Access OpenAI configuration
api_key = settings.openai.api_key
model = settings.openai.model

# Access repository configuration
repo_owner = settings.repository.repo_owner
local_folder = settings.repository.local_folder

# Check environment
if settings.is_local():
    # Local Docker development
    pass
elif settings.is_azure():
    # Azure-hosted deployment
    settings.validate_required()
```

### Dependency Injection (FastAPI)

```python
from fastapi import Depends
from config import Settings, get_settings

@app.get("/health")
async def health_check(settings: Settings = Depends(get_settings)):
    return {
        "status": "healthy",
        "environment": settings.environment,
        "database": {
            "postgres": settings.database.postgres_host,
            "sqlserver": settings.database.sqlserver_host
        }
    }
```

## Configuration Files

### `.env` (local development)

Create a `.env` file in the project root based on `.env.example`:

```bash
cp .env.example .env
```

Then edit `.env` with your actual values.

### `.env.example`

Template file with all available configuration options. Keep this file updated when adding new configuration variables.

## Environment Variables

### Application Settings

- `ENVIRONMENT`: Environment mode (`local`, `azure`, `test`) - default: `local`
- `DEBUG`: Enable debug mode - default: `false`
- `LOG_LEVEL`: Logging level - default: `INFO`

### Database (PostgreSQL)

- `POSTGRES_HOST`: PostgreSQL host (Docker: `postgres`, local: `localhost`)
- `POSTGRES_DB`: PostgreSQL database name
- `POSTGRES_USER`: PostgreSQL username
- `POSTGRES_PASSWORD`: PostgreSQL password

### Database (SQL Server)

- `SQLSERVER_HOST`: SQL Server host (Docker: `sqlserver`, local: `localhost`)
- `SQLSERVER_DB`: SQL Server database name
- `SQLSERVER_USER`: SQL Server username
- `SQLSERVER_PASSWORD`: SQL Server password

### OpenAI / Azure OpenAI

- `OPENAI_PROVIDER`: Provider to use (`azure` or `openai`) - default: `azure`
- `OPENAI_ENDPOINT`: Azure OpenAI endpoint URL (required for Azure provider)
- `OPENAI_KEY`: API key
- `OPENAI_MODEL`: Primary model name - default: `gpt-4`
- `OPENAI_MODEL2`: Secondary model name - default: `gpt-4`

### Repository

- `REPO_OWNER`: GitHub repository owner - default: `statsbomb`
- `REPO_NAME`: GitHub repository name - default: `open-data`
- `LOCAL_FOLDER`: Local data folder path - default: `./data`

## Migration Guide

### Before (old Azure-specific pattern)

```python
import os

db_host = os.getenv('DB_SERVER_AZURE_POSTGRES')
db_name = os.getenv('DB_NAME_AZURE_POSTGRES')
api_key = os.getenv('OPENAI_KEY')
```

### After (new portable pattern)

```python
from config import settings

db_host = settings.database.postgres_host   # env: POSTGRES_HOST
db_name = settings.database.postgres_database  # env: POSTGRES_DB
api_key = settings.openai.api_key           # env: OPENAI_KEY
```

## Validation

The configuration module validates settings at startup:

1. **Type validation**: Ensures all values match their expected types
2. **Environment validation**: Ensures `ENVIRONMENT` is one of: `local`, `azure`, `test`
3. **Required fields**: When not in test mode, validates all required configuration is present

To manually validate:

```python
from config import settings

settings.validate_required()
```

## Best Practices

1. **Never use `os.getenv()` directly** - Always use the settings module
2. **Read configuration once** - Settings are loaded at startup, don't reload them
3. **Keep `.env.example` updated** - Document all new environment variables
4. **Fail fast** - If configuration is missing, let the application fail at startup
5. **Separate by environment** - Use different `.env` files for different environments

## Testing

For testing, either:

1. Set `ENVIRONMENT=test` in your test `.env` file
2. Override settings in your tests:

```python
from config import Settings

def test_something():
    test_settings = Settings(environment="test")
    # Use test_settings in your test
```
