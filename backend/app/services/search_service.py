"""
Search service for semantic search and chat functionality.

This service orchestrates the business logic for searching events using
embeddings and generating chat responses.
"""

import logging

import tiktoken

from app.adapters.openai_client import OpenAIAdapter
from app.domain.entities import (
    ChatResponse,
    Match,
    SearchRequest,
    SearchResult,
)
from app.repositories.base import EventRepository, MatchRepository

logger = logging.getLogger(__name__)

# Default tiktoken encoding for GPT-4 family models
_FALLBACK_ENCODING = "cl100k_base"


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """
    Count the number of tokens in a text string using tiktoken.

    Args:
        text: The text to count tokens for.
        model: The model name to use for encoding selection.

    Returns:
        Number of tokens in the text.
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding(_FALLBACK_ENCODING)
    return len(encoding.encode(text))


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
            normalized_question = self._normalize_query(request.query, request.language)

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

            # Step 5: Build context and generate response (with token budget guard)
            answer, token_meta = self._generate_answer(
                question=normalized_question,
                search_results=search_results,
                match_info=match_info,
                system_message=request.system_message,
                temperature=request.temperature,
                max_tokens=request.max_output_tokens,
                max_input_tokens=request.max_input_tokens,
            )

            # Update search_results to reflect any truncation
            kept_count = len(search_results) - token_meta["results_truncated"]
            search_results = search_results[:kept_count]

            # Build metadata
            metadata = {
                "match_id": request.match_id,
                "language": request.language,
                "search_algorithm": request.search_algorithm,
                "embedding_model": request.embedding_model,
                "results_count": len(search_results),
                "input_tokens": token_meta["input_tokens"],
                "max_input_tokens": token_meta["max_input_tokens"],
                "results_truncated": token_meta["results_truncated"],
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
        search_results: list[SearchResult],
        match_info: Match | None,
        system_message: str | None,
        temperature: float,
        max_tokens: int,
        max_input_tokens: int = 10000,
    ) -> tuple[str, dict]:
        """
        Generate an answer using the LLM based on search results.

        Enforces a token budget: if the total input tokens (system message +
        context + question) exceed max_input_tokens, the lowest-ranked search
        results are iteratively removed until the budget fits.

        Args:
            question: The question to answer
            search_results: Relevant events from search
            match_info: Match information
            system_message: Custom system message (or None for default)
            temperature: LLM temperature
            max_tokens: Maximum tokens in response
            max_input_tokens: Maximum input tokens budget

        Returns:
            Tuple of (answer string, token metadata dict)
        """
        # Build default system message if not provided
        if not system_message:
            system_message = """Answer the user's QUESTION using the EVENTS or GAME_RESULT listed above.
Keep your answer ground in the facts of the EVENTS or GAME_RESULT.
If the EVENTS or GAME_RESULT does not contain the facts to answer the QUESTION return "NONE. I cannot find an answer. Please refine the question."
"""

        # Check if system message + question alone exceed the budget
        base_tokens = count_tokens(system_message + "\n\nQUESTION: " + question)
        if base_tokens > max_input_tokens:
            logger.warning(
                f"Question + system message ({base_tokens} tokens) exceeds "
                f"budget ({max_input_tokens}). Cannot call LLM."
            )
            token_meta = {
                "input_tokens": base_tokens,
                "max_input_tokens": max_input_tokens,
                "results_truncated": len(search_results),
            }
            return (
                "ERROR: The question and system message exceed the token budget. "
                "Please reduce the question length or increase max_input_tokens.",
                token_meta,
            )

        # Build context from match info (fixed part)
        match_context_parts: list[str] = []
        if match_info:
            match_context_parts.append(f"GAME_RESULT: {match_info.display_name}")
            match_context_parts.append(
                f"Competition: {match_info.competition.name}, Season: {match_info.season.name}"
            )
            match_context_parts.append(f"Date: {match_info.match_date}")

        match_context = "\n".join(match_context_parts)

        # Sort results by rank ascending (rank 1 = most relevant)
        sorted_results = sorted(search_results, key=lambda r: r.rank)

        # Token budget guard: iteratively remove lowest-ranked results
        results_truncated = 0
        kept_results = list(sorted_results)

        while True:
            # Build context with current results
            context_parts = []
            if match_context:
                context_parts.append(match_context)
            if kept_results:
                context_parts.append("\nEVENTS:")
                for result in kept_results:
                    event = result.event
                    context_parts.append(
                        f"- {event.time_description}: {event.summary or 'No summary available'}"
                    )
            context = "\n".join(context_parts)

            # Count total input tokens
            full_input = system_message + "\n" + context + "\n\nQUESTION: " + question
            total_tokens = count_tokens(full_input)

            if total_tokens <= max_input_tokens:
                break

            if not kept_results:
                # No more results to remove but still over budget
                break

            # Remove the lowest-ranked result (last in sorted list)
            kept_results.pop()
            results_truncated += 1
            logger.info(
                f"Token budget guard: removed result (rank {sorted_results[len(sorted_results) - results_truncated].rank}), "
                f"{results_truncated} total truncated"
            )

        # Re-count final tokens
        final_context_parts = []
        if match_context:
            final_context_parts.append(match_context)
        if kept_results:
            final_context_parts.append("\nEVENTS:")
            for result in kept_results:
                event = result.event
                final_context_parts.append(
                    f"- {event.time_description}: {event.summary or 'No summary available'}"
                )
        context = "\n".join(final_context_parts)
        full_input = system_message + "\n" + context + "\n\nQUESTION: " + question
        input_tokens = count_tokens(full_input)

        token_meta = {
            "input_tokens": input_tokens,
            "max_input_tokens": max_input_tokens,
            "results_truncated": results_truncated,
        }

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
            return answer, token_meta
        except Exception as e:
            logger.error(f"Failed to generate answer: {e}")
            return "ERROR: Failed to generate answer. Please try again.", token_meta


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
