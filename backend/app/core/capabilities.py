"""Capabilities matrix per data source."""

from typing import Dict, List


SOURCE_CAPABILITIES: Dict[str, Dict[str, List[str]]] = {
    "postgres": {
        "embedding_models": [
            "text-embedding-ada-002",
            "text-embedding-3-small",
            "text-embedding-3-large",
            "multilingual-e5-small:v1",
        ],
        "search_algorithms": [
            "cosine",
            "inner_product",
            "l2_euclidean",
            "l1_manhattan",
        ],
    },
    "sqlserver": {
        "embedding_models": [
            "text-embedding-ada-002",
            "text-embedding-3-small",
        ],
        "search_algorithms": [
            "cosine",
            "inner_product",
            "l2_euclidean",
        ],
    },
}


def normalize_source(source: str) -> str:
    """Normalize source aliases to canonical source names."""
    src = source.lower()
    if src in {"postgres", "postgresql", "azure-postgres"}:
        return "postgres"
    if src in {"sqlserver", "sql-server", "azure-sql"}:
        return "sqlserver"
    return src


def get_source_capabilities(source: str) -> Dict[str, List[str]]:
    """Get capability descriptor for a source."""
    normalized = normalize_source(source)
    if normalized not in SOURCE_CAPABILITIES:
        raise ValueError(f"Unsupported database source: {source}")
    return SOURCE_CAPABILITIES[normalized]


def validate_search_capabilities(
    source: str,
    embedding_model: str,
    search_algorithm: str,
) -> None:
    """Validate model/algorithm against source capabilities."""
    caps = get_source_capabilities(source)
    if embedding_model not in caps["embedding_models"]:
        raise ValueError(
            f"Embedding model '{embedding_model}' is not supported for source '{normalize_source(source)}'"
        )
    if search_algorithm not in caps["search_algorithms"]:
        raise ValueError(
            f"Search algorithm '{search_algorithm}' is not supported for source '{normalize_source(source)}'"
        )
