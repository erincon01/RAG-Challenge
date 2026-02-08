"""Domain exceptions."""

from typing import Any


class DomainException(Exception):
    """Base exception for domain errors."""

    pass


class EntityNotFoundError(DomainException):
    """Raised when an entity is not found."""

    def __init__(self, entity_type: str, entity_id: Any):
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} with id {entity_id} not found")


class ValidationError(DomainException):
    """Raised when domain validation fails."""

    pass


class DatabaseConnectionError(DomainException):
    """Raised when database connection fails."""

    pass


class EmbeddingGenerationError(DomainException):
    """Raised when embedding generation fails."""

    pass
