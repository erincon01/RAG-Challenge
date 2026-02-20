# ADR-002: Centralized Configuration with Pydantic Settings

## Status

**Accepted** - 2026-02-08

## Context

The current codebase has configuration management issues:

- **Scattered `os.getenv()` calls**: Configuration is read from environment variables directly throughout the codebase
- **No type safety**: Environment variables are strings, leading to runtime type errors
- **No validation**: Missing or invalid configuration is discovered at runtime, often deep in execution
- **Code duplication**: Same configuration read multiple times in different modules
- **No single source of truth**: Hard to know what configuration is actually required
- **Environment-specific logic**: `if` statements scattered throughout code checking environment
- **Testing difficulty**: Hard to override configuration in tests
- **Documentation drift**: `.env.example` doesn't match actual usage

**Examples of problems:**
```python
# Repeated across multiple files
db_host = os.getenv('POSTGRES_HOST')  # Could be None
db_port = int(os.getenv('DB_PORT', '5432'))       # Manual type conversion

# No way to know if required until runtime
if not db_host:
    # Fails deep in execution, not at startup
    raise ValueError("Missing POSTGRES_HOST")
```

## Decision

Implement **centralized configuration management** using Pydantic Settings:

### Core Principles

1. **Single source of truth**: All configuration in `config/settings.py`
2. **Type safety**: Pydantic models enforce types at parse time
3. **Fail fast**: Invalid or missing config causes startup failure, not runtime failure
4. **Environment awareness**: Built-in support for `local`, `azure`, `test` environments
5. **Validation**: Custom validators for complex requirements
6. **IDE friendly**: Full autocomplete and type hints

### Implementation

```python
# config/settings.py
from pydantic_settings import BaseSettings

class DatabaseConfig(BaseSettings):
    postgres_host: str
    postgres_database: str
    postgres_user: str
    postgres_password: str
    # ... SQL Server config

class OpenAIConfig(BaseSettings):
    endpoint: str
    api_key: str
    model: str = "gpt-4"

class Settings(BaseSettings):
    environment: Literal["local", "azure", "test"] = "local"
    database: DatabaseConfig
    openai: OpenAIConfig
    # ...

settings = Settings()  # Load once at startup
```

### Usage Pattern

**Before:**
```python
import os
db_host = os.getenv('POSTGRES_HOST')
api_key = os.getenv('OPENAI_KEY')
```

**After:**
```python
from config import settings
db_host = settings.database.postgres_host  # Type-safe, validated
api_key = settings.openai.api_key
```

### Configuration Structure

- **Nested configs**: Group related settings (database, openai, repository)
- **Defaults**: Sensible defaults where appropriate
- **Environment files**: Load from `.env` automatically
- **Field aliases**: Map to existing environment variable names
- **Validation methods**: Custom validation for complex rules

## Consequences

### Positive

✅ **Type safety**: Catch configuration errors at startup, not runtime
✅ **Single read**: Environment variables read once, not on every access
✅ **Better IDE support**: Autocomplete, go-to-definition, refactoring
✅ **Easier testing**: Override settings easily in tests
✅ **Self-documenting**: Pydantic models document expected configuration
✅ **Validation**: Enforce rules (e.g., required fields for Azure environment)
✅ **Fail fast**: Application won't start with invalid config
✅ **Reduced bugs**: Type errors caught by mypy/pyright
✅ **Dependency injection**: Easy to inject in FastAPI with `Depends()`
✅ **Consistent**: One way to access configuration everywhere

### Negative

⚠️ **Migration effort**: Need to update all existing `os.getenv()` calls
⚠️ **New dependency**: Adds `pydantic` and `pydantic-settings` to requirements
⚠️ **Learning curve**: Team needs to learn Pydantic Settings API
⚠️ **Startup overhead**: Slight increase in startup time for validation (negligible)

### Trade-offs

- **Strictness vs Flexibility**: More validation means less flexibility, but fewer runtime errors
- **Upfront vs Runtime errors**: Fail at startup is better than fail during execution

## Migration Strategy

1. ✅ Create `config/` module with Settings classes
2. ✅ Update `.env.example` with all configuration
3. ✅ Add `pydantic` and `pydantic-settings` to requirements.txt
4. ⏳ Migrate modules one by one to use `settings`
5. ⏳ Remove all `os.getenv()` calls
6. ⏳ Add validation for environment-specific requirements
7. ⏳ Update documentation

### Validation Strategy

- **Local environment**: Minimal required config, use defaults
- **Azure environment**: Strict validation, all Azure config required
- **Test environment**: Override with test-specific values

```python
if settings.environment == "azure":
    settings.validate_required_for_azure()  # Fails if missing config
```

## Alternatives Considered

### Alternative 1: python-decouple
**Rejected** - Less type safety, no Pydantic integration, weaker validation

### Alternative 2: dynaconf
**Rejected** - More features than needed, steeper learning curve, not Pydantic-based

### Alternative 3: Keep current approach + add validation
**Rejected** - Doesn't solve fundamental issues of scattered reads and lack of type safety

### Alternative 4: dataclasses + environ
**Rejected** - Pydantic provides superior validation and integration with FastAPI

## Implementation Checklist

- [x] Create `config/settings.py` with all configuration classes
- [x] Create `config/__init__.py` for clean imports
- [x] Update `.env.example` with complete list of variables
- [x] Add dependencies to `requirements.txt`
- [x] Document usage in `config/README.md`
- [ ] Migrate `python_modules/module_data.py` to use settings
- [ ] Migrate `python_modules/module_github.py` to use settings
- [ ] Migrate `python_modules/module_azure_openai.py` to use settings
- [ ] Migrate `app.py` to use settings
- [ ] Remove all direct `os.getenv()` calls
- [ ] Add CI check to prevent new `os.getenv()` usage

## References

- [Pydantic Settings Documentation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [12-Factor App - Config](https://12factor.net/config)
- [FastAPI Settings and Environment Variables](https://fastapi.tiangolo.com/advanced/settings/)

## Related ADRs

- [ADR-001: Adoption of Layered Architecture](ADR-001-layered-architecture.md) - Settings will be used throughout all layers
- [ADR-004: Local Docker Infrastructure](ADR-004-local-docker-infrastructure.md) - Settings support different environments
