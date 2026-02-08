"""
API client for communicating with the RAG Challenge backend.

This client provides a simple interface for the Streamlit frontend
to interact with the FastAPI backend via HTTP.
"""

import os
import requests
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class APIClient:
    """Client for RAG Challenge backend API."""

    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize the API client.

        Args:
            base_url: Base URL of the backend API (e.g., "http://localhost:8000")
                     If not provided, reads from BACKEND_URL environment variable
        """
        self.base_url = base_url or os.getenv("BACKEND_URL", "http://localhost:8000")
        self.api_base = f"{self.base_url}/api/v1"
        self.timeout = 30  # seconds

    def _handle_response(self, response: requests.Response) -> Any:
        """
        Handle API response and raise exceptions for errors.

        Args:
            response: Response object from requests

        Returns:
            Parsed JSON response

        Raises:
            requests.HTTPError: If response status code indicates error
        """
        try:
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            logger.error(f"API error: {e}")
            logger.error(f"Response content: {response.text}")
            raise
        except requests.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise

    # Health endpoints
    def health_check(self) -> Dict[str, Any]:
        """
        Check API health.

        Returns:
            Health status information
        """
        response = requests.get(
            f"{self.api_base}/health",
            timeout=self.timeout,
        )
        return self._handle_response(response)

    # Competition endpoints
    def get_competitions(self, source: str = "postgres") -> List[Dict[str, Any]]:
        """
        Get all competitions.

        Args:
            source: Database source ("postgres" or "sqlserver")

        Returns:
            List of competitions
        """
        response = requests.get(
            f"{self.api_base}/competitions",
            params={"source": source},
            timeout=self.timeout,
        )
        return self._handle_response(response)

    # Match endpoints
    def get_matches(
        self,
        source: str = "postgres",
        competition_name: Optional[str] = None,
        season_name: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get matches with optional filters.

        Args:
            source: Database source ("postgres" or "sqlserver")
            competition_name: Filter by competition name
            season_name: Filter by season name
            limit: Maximum number of results

        Returns:
            List of matches
        """
        params = {
            "source": source,
            "limit": limit,
        }
        if competition_name:
            params["competition_name"] = competition_name
        if season_name:
            params["season_name"] = season_name

        response = requests.get(
            f"{self.api_base}/matches",
            params=params,
            timeout=self.timeout,
        )
        return self._handle_response(response)

    def get_match(self, match_id: int, source: str = "postgres") -> Dict[str, Any]:
        """
        Get match details by ID.

        Args:
            match_id: Match ID
            source: Database source ("postgres" or "sqlserver")

        Returns:
            Match details
        """
        response = requests.get(
            f"{self.api_base}/matches/{match_id}",
            params={"source": source},
            timeout=self.timeout,
        )
        return self._handle_response(response)

    # Event endpoints
    def get_events(
        self,
        match_id: int,
        source: str = "postgres",
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get events for a match.

        Args:
            match_id: Match ID
            source: Database source ("postgres" or "sqlserver")
            limit: Maximum number of results

        Returns:
            List of events
        """
        params = {
            "match_id": match_id,
            "source": source,
        }
        if limit:
            params["limit"] = limit

        response = requests.get(
            f"{self.api_base}/events",
            params=params,
            timeout=self.timeout,
        )
        return self._handle_response(response)

    def get_event(self, event_id: int, source: str = "postgres") -> Dict[str, Any]:
        """
        Get event details by ID.

        Args:
            event_id: Event ID
            source: Database source ("postgres" or "sqlserver")

        Returns:
            Event details
        """
        response = requests.get(
            f"{self.api_base}/events/{event_id}",
            params={"source": source},
            timeout=self.timeout,
        )
        return self._handle_response(response)

    # Chat/Search endpoint
    def search(
        self,
        match_id: int,
        query: str,
        source: str = "postgres",
        language: str = "english",
        search_algorithm: str = "cosine",
        embedding_model: str = "text-embedding-3-small",
        top_n: int = 10,
        temperature: float = 0.1,
        max_input_tokens: int = 10000,
        max_output_tokens: int = 5000,
        include_match_info: bool = True,
        system_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Perform semantic search with AI-powered response.

        Args:
            match_id: Match ID to search
            query: Search query
            source: Database source ("postgres" or "sqlserver")
            language: Query language
            search_algorithm: Similarity algorithm ("cosine", "inner_product", "l2_euclidean")
            embedding_model: Embedding model to use
            top_n: Number of results to return
            temperature: LLM temperature
            max_input_tokens: Maximum input tokens
            max_output_tokens: Maximum output tokens
            include_match_info: Include match information in response
            system_message: Custom system message for LLM

        Returns:
            Search response with answer and results
        """
        payload = {
            "match_id": match_id,
            "query": query,
            "language": language,
            "search_algorithm": search_algorithm,
            "embedding_model": embedding_model,
            "top_n": top_n,
            "temperature": temperature,
            "max_input_tokens": max_input_tokens,
            "max_output_tokens": max_output_tokens,
            "include_match_info": include_match_info,
        }

        if system_message:
            payload["system_message"] = system_message

        response = requests.post(
            f"{self.api_base}/chat/search",
            params={"source": source},
            json=payload,
            timeout=60,  # Longer timeout for AI operations
        )
        return self._handle_response(response)


# Global client instance
_client = None


def get_api_client() -> APIClient:
    """
    Get the global API client instance.

    Returns:
        APIClient instance
    """
    global _client
    if _client is None:
        _client = APIClient()
    return _client
