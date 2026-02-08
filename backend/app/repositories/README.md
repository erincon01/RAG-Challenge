# Repositories Layer

## Propósito

La capa de **repositorios** es responsable del **acceso a datos**. Abstrae los detalles de cómo se almacenan y recuperan los datos, permitiendo que el resto de la aplicación trabaje con entidades de dominio sin conocer detalles de la base de datos.

## Responsabilidades

✅ **Acceso a Datos**: Ejecutar queries SQL y recuperar datos
✅ **Mapeo**: Convertir filas de BD a entidades de dominio y viceversa
✅ **Abstracción**: Ocultar detalles específicos del motor de BD
✅ **Transacciones**: Gestionar conexiones y transacciones de BD
✅ **Query Building**: Construir queries dinámicas según parámetros

❌ **NO debe contener**: Lógica de negocio, validación de reglas, serialización HTTP

## Estructura

```
repositories/
├── __init__.py
├── base.py                # Interfaces abstractas
├── postgres.py            # Implementación PostgreSQL
├── sqlserver.py           # Implementación SQL Server
└── README.md
```

## Patrón Repository

### Interfaz Base (Contrato)

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from contextlib import contextmanager

from app.domain.entities import Match, Event


class BaseRepository(ABC):
    """Repositorio base con operaciones comunes."""

    @abstractmethod
    @contextmanager
    def get_connection(self):
        """Obtener conexión a base de datos."""
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """Probar conexión."""
        pass


class MatchRepository(BaseRepository):
    """Repositorio para entidades Match."""

    @abstractmethod
    def get_by_id(self, match_id: int) -> Optional[Match]:
        """Obtener partido por ID."""
        pass

    @abstractmethod
    def get_all(
        self,
        competition_name: Optional[str] = None,
        season_name: Optional[str] = None,
        limit: int = 100,
    ) -> List[Match]:
        """Obtener todos los partidos con filtros opcionales."""
        pass

    @abstractmethod
    def get_competitions(self) -> List[Competition]:
        """Obtener todas las competiciones."""
        pass
```

### Implementación Concreta

```python
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import logging

from app.core.config import get_settings
from app.domain.entities import Match, Competition
from app.domain.exceptions import DatabaseConnectionError
from app.repositories.base import MatchRepository

logger = logging.getLogger(__name__)
settings = get_settings()


class PostgresMatchRepository(MatchRepository):
    """Implementación PostgreSQL del repositorio de partidos."""

    def __init__(self):
        """Inicializar con configuración de BD."""
        self.db_config = {
            "host": settings.database.postgres_host,
            "database": settings.database.postgres_database,
            "user": settings.database.postgres_user,
            "password": settings.database.postgres_password,
        }

    @contextmanager
    def get_connection(self):
        """Context manager para conexiones."""
        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            yield conn
            conn.commit()
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise DatabaseConnectionError(f"Failed to connect: {e}")
        finally:
            if conn:
                conn.close()

    def get_by_id(self, match_id: int) -> Optional[Match]:
        """Implementación específica de PostgreSQL."""
        query = """
            SELECT
                match_id, match_date,
                competition_id, competition_name,
                home_team_name, away_team_name,
                home_score, away_score
            FROM matches
            WHERE match_id = %s
        """

        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (match_id,))
                row = cur.fetchone()

                if not row:
                    return None

                return self._row_to_match(dict(row))

    def _row_to_match(self, row: Dict[str, Any]) -> Match:
        """
        Mapear fila de BD a entidad de dominio.

        Método privado que convierte estructura de BD a objeto de dominio.
        """
        return Match(
            match_id=row["match_id"],
            match_date=row["match_date"],
            competition=Competition(
                competition_id=row["competition_id"],
                name=row["competition_name"],
            ),
            home_team_name=row["home_team_name"],
            away_team_name=row["away_team_name"],
            home_score=row["home_score"],
            away_score=row["away_score"],
        )
```

## Convenciones

### 1. Separación por Motor de BD

Crear una implementación por cada motor de base de datos:

- `PostgresMatchRepository` → PostgreSQL
- `SQLServerMatchRepository` → SQL Server
- `MongoMatchRepository` → MongoDB (si se usa)

### 2. Queries Parametrizadas

**✅ CORRECTO** (queries parametrizadas):
```python
query = "SELECT * FROM matches WHERE match_id = %s"
cursor.execute(query, (match_id,))
```

**❌ INCORRECTO** (interpolación de strings - riesgo de SQL injection):
```python
query = f"SELECT * FROM matches WHERE match_id = {match_id}"
cursor.execute(query)
```

### 3. Context Managers para Conexiones

Siempre usar context managers para gestionar conexiones:

```python
@contextmanager
def get_connection(self):
    conn = None
    try:
        conn = psycopg2.connect(**self.db_config)
        yield conn
        conn.commit()  # Commit automático si no hay errores
    except Exception as e:
        if conn:
            conn.rollback()  # Rollback automático en caso de error
        raise
    finally:
        if conn:
            conn.close()  # Cerrar siempre
```

### 4. Mapeo Row → Entity

Crear métodos privados `_row_to_entity`:

```python
def _row_to_match(self, row: Dict[str, Any]) -> Match:
    """Convertir fila de BD a entidad Match."""
    return Match(
        match_id=row["match_id"],
        match_date=row["match_date"],
        # ... resto de campos
    )
```

### 5. Logging

Registrar operaciones importantes:

```python
logger.info(f"Fetching match {match_id}")
logger.error(f"Failed to fetch match {match_id}: {e}")
logger.debug(f"Query: {query}")
```

## Patrones Comunes

### Query Dinámica con Filtros

```python
def get_all(
    self,
    competition_name: Optional[str] = None,
    season_name: Optional[str] = None,
    limit: int = 100,
) -> List[Match]:
    """Construir query dinámica según filtros."""

    query = "SELECT * FROM matches WHERE 1=1"
    params = []

    if competition_name:
        query += " AND competition_name = %s"
        params.append(competition_name)

    if season_name:
        query += " AND season_name = %s"
        params.append(season_name)

    query += " ORDER BY match_date DESC LIMIT %s"
    params.append(limit)

    with self.get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
            return [self._row_to_match(dict(row)) for row in rows]
```

### Búsqueda por Vector (pgvector)

```python
def search_by_embedding(
    self,
    search_request: SearchRequest,
    query_embedding: List[float],
) -> List[SearchResult]:
    """Búsqueda por similaridad vectorial."""

    # Convertir embedding a formato PostgreSQL
    embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

    # Operador de pgvector según algoritmo
    operator_map = {
        "cosine": "<=>",
        "inner_product": "<#>",
        "l2": "<->",
    }
    operator = operator_map[search_request.algorithm]

    query = f"""
        SELECT
            *,
            summary_embedding {operator} %s::vector AS score
        FROM events
        WHERE match_id = %s
        ORDER BY score
        LIMIT %s
    """

    with self.get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                query,
                (embedding_str, search_request.match_id, search_request.top_n),
            )
            rows = cur.fetchall()
            return [self._row_to_search_result(dict(row)) for row in rows]
```

### Transacciones Múltiples

```python
def create_match_with_events(
    self,
    match: Match,
    events: List[Event],
) -> Match:
    """Crear partido y eventos en una transacción."""

    with self.get_connection() as conn:
        with conn.cursor() as cur:
            # Insertar partido
            cur.execute(
                "INSERT INTO matches (...) VALUES (...) RETURNING match_id",
                (match.home_team, match.away_team, ...),
            )
            match_id = cur.fetchone()[0]

            # Insertar eventos
            for event in events:
                cur.execute(
                    "INSERT INTO events (...) VALUES (...)",
                    (match_id, event.minute, event.description, ...),
                )

            # Si hay error, rollback automático por el context manager
            return self.get_by_id(match_id)
```

## Factory Pattern

Usar factory para crear repositorios:

```python
class PostgresRepositoryFactory:
    """Factory para crear repositorios PostgreSQL."""

    def create_match_repository(self) -> MatchRepository:
        return PostgresMatchRepository()

    def create_event_repository(self) -> EventRepository:
        return PostgresEventRepository()


class SQLServerRepositoryFactory:
    """Factory para crear repositorios SQL Server."""

    def create_match_repository(self) -> MatchRepository:
        return SQLServerMatchRepository()

    def create_event_repository(self) -> EventRepository:
        return SQLServerEventRepository()
```

## Diferencias por Motor de BD

### PostgreSQL
```python
# Placeholder: %s
query = "SELECT * FROM matches WHERE id = %s"
cur.execute(query, (match_id,))

# pgvector operators
query = "SELECT * FROM events WHERE embedding <=> %s::vector"
```

### SQL Server
```python
# Placeholder: ?
query = "SELECT * FROM matches WHERE id = ?"
cur.execute(query, (match_id,))

# TOP en lugar de LIMIT
query = "SELECT TOP (?) * FROM matches"

# VECTOR_DISTANCE function
query = "SELECT * FROM events WHERE VECTOR_DISTANCE('cosine', embedding, ?)"
```

## Testing

Testear repositorios con base de datos de prueba:

```python
import pytest
from app.repositories.postgres import PostgresMatchRepository

@pytest.fixture
def test_db():
    # Setup: crear BD de prueba
    ...
    yield connection
    # Teardown: limpiar BD de prueba
    ...

def test_get_match_by_id(test_db):
    repo = PostgresMatchRepository()

    match = repo.get_by_id(123)

    assert match is not None
    assert match.match_id == 123
```

## Buenas Prácticas

1. **Nunca exponer detalles de BD**: Solo retornar entidades de dominio
2. **Queries parametrizadas**: Siempre usar placeholders
3. **Context managers**: Para gestionar conexiones automáticamente
4. **Logging**: Registrar queries y errores
5. **Connection pooling**: Considerar usar para producción
6. **Índices**: Asegurar que existan índices apropiados
7. **N+1 queries**: Evitar ejecutar queries en loops
