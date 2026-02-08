# Domain Layer

## Propósito

La capa de **dominio** contiene el **núcleo de la lógica de negocio**. Define las entidades, value objects, reglas de negocio y excepciones específicas del dominio. Es la capa más importante y debe ser **independiente de frameworks y tecnologías**.

## Responsabilidades

✅ **Entidades de Dominio**: Objetos que representan conceptos del negocio
✅ **Value Objects**: Objetos inmutables sin identidad propia
✅ **Reglas de Negocio**: Lógica que debe cumplirse siempre
✅ **Excepciones de Dominio**: Errores específicos del negocio
✅ **Enums y Constantes**: Valores permitidos y configuración del dominio

❌ **NO debe contener**: SQL, HTTP, detalles de frameworks, lógica de UI

## Estructura

```
domain/
├── __init__.py
├── entities.py            # Entidades principales
├── value_objects.py       # Objetos de valor (futuro)
├── exceptions.py          # Excepciones de dominio
└── README.md
```

## Entidades de Dominio

Las entidades son objetos con **identidad única** que persisten en el tiempo.

### Características de una Entidad

1. **Tiene identidad única** (ID)
2. **Tiene ciclo de vida** (se crea, modifica, elimina)
3. **Puede tener estado mutable**
4. **Encapsula lógica de negocio**

### Ejemplo: Entidad Match

```python
from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Match:
    """
    Entidad de dominio para un partido de fútbol.

    Representa un partido completo con sus equipos, resultado, y metadata.
    Esta es una entidad porque tiene identidad única (match_id) y ciclo de vida.
    """

    # Identidad
    match_id: int

    # Atributos básicos
    match_date: date
    home_score: int
    away_score: int

    # Relaciones
    competition: "Competition"
    season: "Season"
    home_team: "Team"
    away_team: "Team"

    # Opcionales
    stadium: Optional["Stadium"] = None
    referee: Optional["Referee"] = None

    # Métodos de dominio (lógica de negocio)
    @property
    def display_name(self) -> str:
        """Formato legible del partido."""
        return f"{self.home_team.name} ({self.home_score}) - {self.away_team.name} ({self.away_score})"

    @property
    def winner(self) -> Optional["Team"]:
        """Determinar equipo ganador."""
        if self.home_score > self.away_score:
            return self.home_team
        elif self.away_score > self.home_score:
            return self.away_team
        return None  # Empate

    @property
    def is_draw(self) -> bool:
        """Verificar si fue empate."""
        return self.home_score == self.away_score

    def validate(self) -> None:
        """
        Validar reglas de negocio.

        Raises:
            ValidationError: Si no cumple reglas de negocio
        """
        if self.home_score < 0 or self.away_score < 0:
            raise ValidationError("Scores cannot be negative")

        if self.home_team.team_id == self.away_team.team_id:
            raise ValidationError("Home and away teams must be different")
```

## Value Objects

Los value objects son objetos **inmutables sin identidad**. Se definen por sus valores.

### Características de un Value Object

1. **No tiene identidad única**
2. **Inmutable** (no cambia después de crearse)
3. **Se compara por valor**, no por referencia
4. **Puede encapsular validación**

### Ejemplo: Value Object Competition

```python
from dataclasses import dataclass


@dataclass(frozen=True)  # frozen=True hace el objeto inmutable
class Competition:
    """
    Value object para una competición.

    Es un value object porque se identifica por sus valores (id, nombre, país)
    y no tiene ciclo de vida propio.
    """

    competition_id: int
    country: str
    name: str

    def __post_init__(self):
        """Validar al crear."""
        if not self.name:
            raise ValueError("Competition name cannot be empty")
        if not self.country:
            raise ValueError("Competition country cannot be empty")
```

## Enums y Constantes

Usar Enums para valores permitidos:

```python
from enum import Enum


class SearchAlgorithm(str, Enum):
    """Algoritmos de búsqueda por similaridad."""

    COSINE = "cosine"
    INNER_PRODUCT = "inner_product"
    L1_MANHATTAN = "l1_manhattan"
    L2_EUCLIDEAN = "l2_euclidean"


class EmbeddingModel(str, Enum):
    """Modelos de embeddings soportados."""

    ADA_002 = "text-embedding-ada-002"
    T3_SMALL = "text-embedding-3-small"
    T3_LARGE = "text-embedding-3-large"
    E5_SMALL = "multilingual-e5-small:v1"
```

## Excepciones de Dominio

Crear excepciones específicas del dominio:

```python
class DomainException(Exception):
    """Excepción base para errores de dominio."""
    pass


class EntityNotFoundError(DomainException):
    """Entidad no encontrada."""

    def __init__(self, entity_type: str, entity_id: any):
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} with id {entity_id} not found")


class ValidationError(DomainException):
    """Error de validación de reglas de negocio."""
    pass


class EmbeddingGenerationError(DomainException):
    """Error al generar embeddings."""
    pass
```

## Request/Response Objects

Objetos para casos de uso específicos:

```python
@dataclass
class SearchRequest:
    """Request para búsqueda semántica."""

    match_id: int
    query: str
    language: str = "english"
    search_algorithm: SearchAlgorithm = SearchAlgorithm.COSINE
    embedding_model: EmbeddingModel = EmbeddingModel.T3_SMALL
    top_n: int = 10
    temperature: float = 0.1

    def __post_init__(self):
        """Validar parámetros."""
        if self.top_n < 1:
            self.top_n = 10
        if self.top_n > 100:
            self.top_n = 100
        if self.temperature < 0 or self.temperature > 2:
            self.temperature = 0.1


@dataclass
class SearchResult:
    """Resultado individual de búsqueda."""

    event: "EventDetail"
    similarity_score: float
    rank: int
```

## Reglas de Negocio

### Validación en Entidades

```python
@dataclass
class Match:
    match_id: int
    home_score: int
    away_score: int

    def __post_init__(self):
        """Validar al crear la entidad."""
        self.validate()

    def validate(self) -> None:
        """Aplicar reglas de negocio."""
        if self.home_score < 0:
            raise ValidationError("Home score cannot be negative")
        if self.away_score < 0:
            raise ValidationError("Away score cannot be negative")
```

### Métodos de Negocio

```python
@dataclass
class Team:
    team_id: int
    name: str
    country: str

    def can_play_against(self, other_team: "Team") -> bool:
        """Verificar si puede jugar contra otro equipo."""
        return self.team_id != other_team.team_id

    def is_from_same_country(self, other_team: "Team") -> bool:
        """Verificar si es del mismo país."""
        return self.country == other_team.country
```

## Patrones de Uso

### Rich Domain Model

Mover lógica al dominio en lugar de servicios:

**❌ INCORRECTO** (lógica en servicio):
```python
# En servicio
def get_winner(match: Match) -> Optional[Team]:
    if match.home_score > match.away_score:
        return match.home_team
    elif match.away_score > match.home_score:
        return match.away_team
    return None
```

**✅ CORRECTO** (lógica en dominio):
```python
# En Match entity
@property
def winner(self) -> Optional[Team]:
    if self.home_score > self.away_score:
        return self.home_team
    elif self.away_score > self.home_score:
        return self.away_team
    return None

# En servicio (uso simple)
winner = match.winner
```

### Inmutabilidad

Usar `frozen=True` para value objects:

```python
@dataclass(frozen=True)
class Competition:
    competition_id: int
    name: str

# Esto causará error:
# comp.name = "Nuevo nombre"  # FrozenInstanceError
```

### Factory Methods

Crear métodos estáticos para construcción compleja:

```python
@dataclass
class Match:
    match_id: int
    # ...

    @classmethod
    def create_new(
        cls,
        home_team: Team,
        away_team: Team,
        competition: Competition,
        match_date: date,
    ) -> "Match":
        """Factory method para crear un nuevo partido."""
        # Validaciones
        if not home_team.can_play_against(away_team):
            raise ValidationError("Teams cannot play against themselves")

        # Crear con valores por defecto
        return cls(
            match_id=0,  # Será asignado por la BD
            match_date=match_date,
            competition=competition,
            home_team=home_team,
            away_team=away_team,
            home_score=0,
            away_score=0,
            result="pending",
        )
```

## Testing del Dominio

El dominio debe ser fácil de testear sin dependencias:

```python
import pytest
from app.domain.entities import Match, Team
from app.domain.exceptions import ValidationError


def test_match_winner():
    """Test para lógica de negocio pura."""
    home = Team(team_id=1, name="Home", country="Spain")
    away = Team(team_id=2, name="Away", country="France")

    match = Match(
        match_id=1,
        home_team=home,
        away_team=away,
        home_score=2,
        away_score=1,
        # ...
    )

    assert match.winner == home
    assert not match.is_draw


def test_negative_score_validation():
    """Test de validación de reglas."""
    with pytest.raises(ValidationError):
        match = Match(
            match_id=1,
            home_score=-1,  # Inválido
            away_score=0,
            # ...
        )
        match.validate()
```

## Principios Clave

1. **Domain-Driven Design**: El dominio es el corazón de la aplicación
2. **Independencia**: No depende de frameworks ni infraestructura
3. **Expresividad**: El código expresa conceptos del negocio
4. **Validación**: Las entidades se validan a sí mismas
5. **Inmutabilidad**: Preferir objetos inmutables cuando sea posible
6. **Rich Model**: Mover lógica al dominio, no a servicios

## Buenas Prácticas

1. **Nombres del Negocio**: Usar términos del dominio (Match, Team, Competition)
2. **Métodos de Dominio**: Agregar métodos que expresen reglas de negocio
3. **Validación Temprana**: Validar en `__post_init__`
4. **Excepciones Específicas**: Crear excepciones propias del dominio
5. **Sin Dependencias**: El dominio no debe importar de otras capas
6. **Testeable**: Fácil de testear sin mocks ni BD
