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
if settings.is_azure():
    # Azure-specific logic
    settings.validate_required_for_azure()
elif settings.is_local():
    # Local-specific logic
    pass
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

- `DB_SERVER_AZURE_POSTGRES`: PostgreSQL host
- `DB_NAME_AZURE_POSTGRES`: PostgreSQL database name
- `DB_USER_AZURE_POSTGRES`: PostgreSQL username
- `DB_PASSWORD_AZURE_POSTGRES`: PostgreSQL password

### Database (SQL Server)

- `DB_SERVER_AZURE`: SQL Server host
- `DB_NAME_AZURE`: SQL Server database name
- `DB_USER_AZURE`: SQL Server username
- `DB_PASSWORD_AZURE`: SQL Server password

### OpenAI/Azure OpenAI

- `OPENAI_ENDPOINT`: Azure OpenAI endpoint URL
- `OPENAI_KEY`: API key
- `OPENAI_MODEL`: Primary model name - default: `gpt-4`
- `OPENAI_MODEL2`: Secondary model name - default: `gpt-4`

### Repository

- `REPO_OWNER`: GitHub repository owner - default: `statsbomb`
- `REPO_NAME`: GitHub repository name - default: `open-data`
- `LOCAL_FOLDER`: Local data folder path - default: `./data`

## Migration Guide

### Before (old pattern)

```python
import os

db_host = os.getenv('DB_SERVER_AZURE_POSTGRES')
db_name = os.getenv('DB_NAME_AZURE_POSTGRES')
api_key = os.getenv('OPENAI_KEY')
```

### After (new pattern)

```python
from config import settings

db_host = settings.database.postgres_host
db_name = settings.database.postgres_database
api_key = settings.openai.api_key
```

## Validation

The configuration module validates settings at startup:

1. **Type validation**: Ensures all values match their expected types
2. **Environment validation**: Ensures `ENVIRONMENT` is one of: `local`, `azure`, `test`
3. **Required fields (Azure mode)**: When `ENVIRONMENT=azure`, validates all Azure-specific configuration is present

To manually validate Azure requirements:

```python
from config import settings

settings.validate_required_for_azure()
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
