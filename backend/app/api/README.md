# API Layer

## Propósito

La capa de API es la **interfaz HTTP** de la aplicación. Define todos los endpoints REST, maneja las peticiones HTTP, valida los datos de entrada y serializa las respuestas.

## Responsabilidades

✅ **Routing**: Definir rutas HTTP (GET, POST, PUT, DELETE, etc.)
✅ **Validación**: Validar parámetros de query, path, body usando Pydantic
✅ **Serialización**: Convertir objetos de dominio a DTOs (Data Transfer Objects)
✅ **Documentación**: Generar documentación OpenAPI/Swagger automática
✅ **Manejo de errores HTTP**: Convertir excepciones en respuestas HTTP apropiadas

❌ **NO debe contener**: Lógica de negocio, acceso directo a base de datos, lógica de transformación compleja

## Estructura

```
api/
├── v1/                    # Versión 1 de la API
│   ├── __init__.py
│   ├── models.py          # DTOs (Request/Response models)
│   ├── health.py          # Endpoints de health check
│   ├── matches.py         # Endpoints de partidos
│   ├── events.py          # Endpoints de eventos
│   └── chat.py            # Endpoints de búsqueda semántica
└── README.md
```

## Convenciones

### 1. Nombrado de Archivos

- Un archivo por recurso principal (e.g., `matches.py`, `events.py`)
- `models.py` para todos los DTOs de la versión
- Usar snake_case para nombres de archivo

### 2. Estructura de Endpoints

```python
from fastapi import APIRouter, Depends, HTTPException, Query, Path

router = APIRouter()

@router.get(
    "/resource/{id}",
    response_model=ResourceResponse,
    summary="Breve descripción",
    description="Descripción detallada del endpoint"
)
async def get_resource(
    id: int = Path(..., description="Resource ID"),
    param: str = Query(default="value", description="Query parameter"),
    repo: Repository = Depends(get_repository),
) -> ResourceResponse:
    """
    Docstring detallado del endpoint.

    Args:
        id: ID del recurso
        param: Parámetro opcional
        repo: Repositorio inyectado

    Returns:
        Respuesta serializada

    Raises:
        HTTPException: Si el recurso no existe
    """
    try:
        # Llamar al servicio o repositorio
        result = repo.get_by_id(id)

        if not result:
            raise HTTPException(status_code=404, detail="Not found")

        return ResourceResponse.from_domain(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 3. DTOs (Data Transfer Objects)

Los DTOs en `models.py` deben:

- Usar Pydantic BaseModel
- Tener validadores cuando sea necesario
- Documentar cada campo con `Field(description="...")`
- Separar modelos de request y response

```python
from pydantic import BaseModel, Field, field_validator

class SearchRequest(BaseModel):
    """DTO para búsqueda semántica."""

    query: str = Field(..., min_length=1, description="Texto a buscar")
    top_n: int = Field(default=10, ge=1, le=100, description="Número de resultados")

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validar que el query no esté vacío."""
        if not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()

class SearchResponse(BaseModel):
    """DTO para respuesta de búsqueda."""

    question: str
    answer: str
    results: List[ResultItem]

    class Config:
        from_attributes = True  # Permite crear desde objetos de dominio
```

## Patrones de Uso

### Dependency Injection

Usar FastAPI Depends para inyectar dependencias:

```python
from app.core.dependencies import get_match_repository
from app.repositories.base import MatchRepository

@router.get("/matches/{id}")
async def get_match(
    id: int,
    repo: MatchRepository = Depends(get_match_repository)
):
    return repo.get_by_id(id)
```

### Manejo de Errores

```python
from fastapi import HTTPException, status

# 404 Not Found
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Resource not found"
)

# 400 Bad Request
raise HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Invalid parameters"
)

# 500 Internal Server Error
raise HTTPException(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail="Internal error occurred"
)
```

### Query Parameters

```python
from typing import Optional
from fastapi import Query

@router.get("/items")
async def list_items(
    page: int = Query(default=1, ge=1, description="Page number"),
    size: int = Query(default=10, ge=1, le=100, description="Page size"),
    search: Optional[str] = Query(default=None, description="Search term")
):
    ...
```

## Versionado de API

- Usar prefijo `/api/v1/` para la versión 1
- Crear `/api/v2/` cuando haya breaking changes
- Mantener versiones anteriores durante período de deprecación

## Testing

Los endpoints deben testearse con:

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_match():
    response = client.get("/api/v1/matches/123")
    assert response.status_code == 200
    assert response.json()["match_id"] == 123
```

## Documentación Automática

FastAPI genera automáticamente:

- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`
- **OpenAPI JSON**: `/openapi.json`

Asegurar que todos los endpoints tengan:
- `summary`: Título corto
- `description`: Descripción detallada
- `response_model`: Modelo de respuesta
- Docstrings completos
