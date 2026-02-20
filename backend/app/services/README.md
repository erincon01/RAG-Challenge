# Services Layer

## Propósito

La capa de **servicios** contiene la **lógica de negocio** de la aplicación. Orquesta operaciones complejas que involucran múltiples repositorios, adapters externos, y transformaciones de datos.

## Responsabilidades

✅ **Lógica de Negocio**: Implementar reglas y casos de uso de la aplicación
✅ **Orquestación**: Coordinar múltiples repositorios y adapters
✅ **Transformaciones**: Convertir datos entre capas (Domain ↔ DTOs)
✅ **Validación de Negocio**: Validar reglas que van más allá de tipos de datos
✅ **Transacciones**: Gestionar transacciones que afectan múltiples entidades

❌ **NO debe contener**: Detalles de HTTP, SQL directo, detalles de APIs externas

## Estructura

```
services/
├── __init__.py
├── search_service.py      # Servicio de búsqueda semántica
├── match_service.py        # Servicio de gestión de partidos (futuro)
└── README.md
```

## Patrón de Servicio

### Estructura Básica

```python
from typing import List
import logging

from app.domain.entities import Match, SearchRequest, SearchResult
from app.domain.exceptions import EntityNotFoundError, ValidationError
from app.repositories.base import MatchRepository, EventRepository
from app.adapters.openai_client import OpenAIAdapter

logger = logging.getLogger(__name__)


class MatchService:
    """Servicio para operaciones de negocio relacionadas con partidos."""

    def __init__(
        self,
        match_repo: MatchRepository,
        event_repo: EventRepository,
    ):
        """
        Inicializar servicio con sus dependencias.

        Args:
            match_repo: Repositorio de partidos
            event_repo: Repositorio de eventos
        """
        self.match_repo = match_repo
        self.event_repo = event_repo

    def get_match_with_events(self, match_id: int) -> Dict[str, Any]:
        """
        Obtener partido con sus eventos.

        Este es un ejemplo de orquestación: combina datos de múltiples repositorios.

        Args:
            match_id: ID del partido

        Returns:
            Diccionario con partido y eventos

        Raises:
            EntityNotFoundError: Si el partido no existe
        """
        # 1. Obtener partido
        match = self.match_repo.get_by_id(match_id)
        if not match:
            raise EntityNotFoundError("Match", match_id)

        # 2. Obtener eventos del partido
        events = self.event_repo.get_events_by_match(match_id)

        # 3. Aplicar lógica de negocio
        # (por ejemplo, filtrar eventos, calcular estadísticas, etc.)

        # 4. Retornar resultado orquestado
        return {
            "match": match,
            "events": events,
            "total_events": len(events),
            "periods": self._group_by_period(events),
        }

    def _group_by_period(self, events: List[Event]) -> Dict[int, List[Event]]:
        """
        Agrupar eventos por período.

        Método privado para lógica de negocio interna.
        """
        periods = {}
        for event in events:
            period = event.period
            if period not in periods:
                periods[period] = []
            periods[period].append(event)
        return periods
```

## Convenciones

### 1. Inyección de Dependencias

Los servicios reciben sus dependencias en el constructor:

```python
def __init__(
    self,
    match_repo: MatchRepository,
    event_repo: EventRepository,
    openai_adapter: OpenAIAdapter,
):
    self.match_repo = match_repo
    self.event_repo = event_repo
    self.openai_adapter = openai_adapter
```

### 2. Un Servicio por Dominio

- `SearchService`: Búsqueda semántica y chat
- `MatchService`: Operaciones sobre partidos
- `EventService`: Operaciones sobre eventos

No mezclar responsabilidades de diferentes dominios.

### 3. Métodos Públicos vs Privados

**Métodos públicos** (sin `_`):
- Casos de uso completos
- Validación de entrada
- Manejo de excepciones
- Logging

**Métodos privados** (con `_`):
- Lógica auxiliar
- Transformaciones internas
- No se exponen fuera del servicio

```python
class SearchService:
    # Método público - caso de uso completo
    def search_and_chat(self, request: SearchRequest) -> ChatResponse:
        normalized_query = self._normalize_query(request.query)
        embedding = self._generate_embedding(normalized_query)
        results = self._search(embedding)
        answer = self._generate_answer(results)
        return ChatResponse(...)

    # Métodos privados - lógica interna
    def _normalize_query(self, query: str) -> str:
        ...

    def _generate_embedding(self, query: str) -> List[float]:
        ...
```

### 4. Logging

Usar logging para rastrear operaciones:

```python
import logging

logger = logging.getLogger(__name__)

def process_match(self, match_id: int):
    logger.info(f"Processing match {match_id}")

    try:
        result = self._do_processing(match_id)
        logger.info(f"Successfully processed match {match_id}")
        return result
    except Exception as e:
        logger.error(f"Failed to process match {match_id}: {e}")
        raise
```

### 5. Manejo de Excepciones

Usar excepciones de dominio:

```python
from app.domain.exceptions import (
    EntityNotFoundError,
    ValidationError,
    EmbeddingGenerationError,
)

def get_match(self, match_id: int) -> Match:
    match = self.match_repo.get_by_id(match_id)

    if not match:
        raise EntityNotFoundError("Match", match_id)

    return match
```

## Patrones Comunes

### Orquestación Multi-Repositorio

```python
def get_full_match_data(self, match_id: int) -> FullMatchData:
    """Combinar datos de múltiples fuentes."""

    # 1. Obtener datos base
    match = self.match_repo.get_by_id(match_id)
    events = self.event_repo.get_events_by_match(match_id)

    # 2. Enriquecer con datos externos
    lineups = self.lineup_repo.get_by_match(match_id)

    # 3. Calcular métricas
    statistics = self._calculate_statistics(events)

    # 4. Combinar todo
    return FullMatchData(
        match=match,
        events=events,
        lineups=lineups,
        statistics=statistics,
    )
```

### Validación de Reglas de Negocio

```python
def create_match(self, match_data: MatchCreate) -> Match:
    """Crear un nuevo partido con validaciones de negocio."""

    # Validar regla de negocio
    if match_data.home_score < 0 or match_data.away_score < 0:
        raise ValidationError("Scores cannot be negative")

    # Validar que los equipos sean diferentes
    if match_data.home_team_id == match_data.away_team_id:
        raise ValidationError("Home and away teams must be different")

    # Validar que no exista partido duplicado
    existing = self.match_repo.find_by_teams_and_date(
        match_data.home_team_id,
        match_data.away_team_id,
        match_data.match_date,
    )
    if existing:
        raise ValidationError("Match already exists")

    # Crear partido
    return self.match_repo.create(match_data)
```

### Pipeline de Procesamiento

```python
def search_and_chat(self, request: SearchRequest) -> ChatResponse:
    """Pipeline multi-paso para búsqueda y respuesta."""

    # Paso 1: Normalizar entrada
    normalized_query = self._normalize_query(request.query, request.language)

    # Paso 2: Generar embedding
    embedding = self.openai_adapter.create_embedding(normalized_query)

    # Paso 3: Buscar eventos similares
    search_results = self.event_repo.search_by_embedding(request, embedding)

    # Paso 4: Obtener contexto adicional
    match_info = self.match_repo.get_by_id(request.match_id)

    # Paso 5: Generar respuesta
    answer = self._generate_answer(
        normalized_query,
        search_results,
        match_info,
        request.system_message,
    )

    # Paso 6: Construir respuesta final
    return ChatResponse(
        question=request.query,
        normalized_question=normalized_query,
        answer=answer,
        search_results=search_results,
        match_info=match_info,
    )
```

## Testing

Los servicios deben testearse con mocks:

```python
from unittest.mock import Mock, patch
import pytest

def test_search_service():
    # Arrange
    mock_match_repo = Mock()
    mock_event_repo = Mock()
    mock_openai = Mock()

    service = SearchService(mock_match_repo, mock_event_repo, mock_openai)

    # Configure mocks
    mock_openai.create_embedding.return_value = [0.1, 0.2, 0.3]
    mock_event_repo.search_by_embedding.return_value = [...]

    # Act
    result = service.search_and_chat(search_request)

    # Assert
    assert result.answer is not None
    mock_openai.create_embedding.assert_called_once()
    mock_event_repo.search_by_embedding.assert_called_once()
```

## Buenas Prácticas

1. **Single Responsibility**: Cada servicio tiene un propósito claro
2. **Dependency Injection**: Facilita testing y reemplazo de componentes
3. **Inmutabilidad**: Preferir objetos inmutables cuando sea posible
4. **Fail Fast**: Validar entrada temprano, fallar rápido
5. **Logging**: Registrar operaciones importantes y errores
6. **Documentación**: Docstrings claros para todos los métodos públicos
