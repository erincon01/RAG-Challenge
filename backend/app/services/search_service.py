"""
Search service for semantic search and chat functionality.

This service orchestrates the business logic for searching events using
embeddings and generating chat responses.
"""

import logging
from typing import List, Optional

from app.domain.entities import (
    SearchRequest,
    SearchResult,
    ChatResponse,
    Match,
    SearchAlgorithm,
    EmbeddingModel,
)
from app.repositories.base import MatchRepository, EventRepository
from app.adapters.openai_client import OpenAIAdapter

logger = logging.getLogger(__name__)


class SearchService:
    """Service for semantic search and chat operations."""

    def __init__(
        self,
        match_repo: MatchRepository,
        event_repo: EventRepository,
        openai_adapter: OpenAIAdapter,
    ):
        """
        Initialize the search service.

        Args:
            match_repo: Match repository instance
            event_repo: Event repository instance
            openai_adapter: OpenAI adapter instance
        """
        self.match_repo = match_repo
        self.event_repo = event_repo
        self.openai_adapter = openai_adapter

    def search_and_chat(self, request: SearchRequest) -> ChatResponse:
        """
        Perform semantic search and generate a chat response.

        This is the main orchestration method that:
        1. Translates the query to English if needed
        2. Generates an embedding for the query
        3. Searches for similar events
        4. Builds a context from search results
        5. Generates a chat response using the LLM

        Args:
            request: Search request parameters

        Returns:
            ChatResponse with answer and search results
        """
        try:
            # Step 1: Translate query if needed
            normalized_question = self._normalize_query(
                request.query, request.language
            )

            # Step 2: Generate embedding for the query
            query_embedding = self.openai_adapter.create_embedding(
                text=normalized_question, model=request.embedding_model
            )

            # Step 3: Search for similar events
            search_results = self.event_repo.search_by_embedding(
                search_request=request, query_embedding=query_embedding
            )

            # Step 4: Get match info if requested
            match_info = None
            if request.include_match_info:
                match_info = self.match_repo.get_by_id(request.match_id)

            # Step 5: Build context and generate response
            answer = self._generate_answer(
                question=normalized_question,
                search_results=search_results,
                match_info=match_info,
                system_message=request.system_message,
                temperature=request.temperature,
                max_tokens=request.max_output_tokens,
            )

            # Build metadata
            metadata = {
                "match_id": request.match_id,
                "language": request.language,
                "search_algorithm": request.search_algorithm,
                "embedding_model": request.embedding_model,
                "results_count": len(search_results),
            }

            return ChatResponse(
                question=request.query,
                normalized_question=normalized_question,
                answer=answer,
                search_results=search_results,
                match_info=match_info,
                metadata=metadata,
            )

        except Exception as e:
            logger.error(f"Search and chat failed: {e}")
            raise

    def _normalize_query(self, query: str, language: str) -> str:
        """
        Normalize the query by translating to English if needed.

        Args:
            query: Original query
            language: Query language

        Returns:
            Normalized query in English
        """
        if language.lower() == "english":
            return query

        try:
            return self.openai_adapter.translate_to_english(query, language)
        except Exception as e:
            logger.warning(f"Translation failed, using original query: {e}")
            return query

    def _generate_answer(
        self,
        question: str,
        search_results: List[SearchResult],
        match_info: Optional[Match],
        system_message: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """
        Generate an answer using the LLM based on search results.

        Args:
            question: The question to answer
            search_results: Relevant events from search
            match_info: Match information
            system_message: Custom system message (or None for default)
            temperature: LLM temperature
            max_tokens: Maximum tokens in response

        Returns:
            Generated answer
        """
        # Build default system message if not provided
        if not system_message:
            system_message = """Answer the user's QUESTION using the EVENTS or GAME_RESULT listed above.
Keep your answer ground in the facts of the EVENTS or GAME_RESULT.
If the EVENTS or GAME_RESULT does not contain the facts to answer the QUESTION return "NONE. I cannot find an answer. Please refine the question."
"""

        # Build context from match info
        context_parts = []

        if match_info:
            context_parts.append(f"GAME_RESULT: {match_info.display_name}")
            context_parts.append(
                f"Competition: {match_info.competition.name}, Season: {match_info.season.name}"
            )
            context_parts.append(f"Date: {match_info.match_date}")

        # Build context from search results
        if search_results:
            context_parts.append("\nEVENTS:")
            for result in search_results:
                event = result.event
                context_parts.append(
                    f"- {event.time_description}: {event.summary or 'No summary available'}"
                )

        context = "\n".join(context_parts)

        # Build messages for chat completion
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"{context}\n\nQUESTION: {question}"},
        ]

        # Generate response
        try:
            answer = self.openai_adapter.create_chat_completion(
                messages=messages, temperature=temperature, max_tokens=max_tokens
            )
            return answer
        except Exception as e:
            logger.error(f"Failed to generate answer: {e}")
            return "ERROR: Failed to generate answer. Please try again."


def get_search_service(
    match_repo: MatchRepository,
    event_repo: EventRepository,
    openai_adapter: OpenAIAdapter,
) -> SearchService:
    """
    Create a search service instance.

    This function is used for dependency injection.

    Args:
        match_repo: Match repository
        event_repo: Event repository
        openai_adapter: OpenAI adapter

    Returns:
        SearchService instance
    """
    return SearchService(
        match_repo=match_repo,
        event_repo=event_repo,
        openai_adapter=openai_adapter,
    )
