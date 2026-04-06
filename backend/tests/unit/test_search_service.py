"""
Unit tests for SearchService — mocked repositories and OpenAI adapter.

Tests the orchestration logic: translation, embedding, search, answer generation.
"""

from unittest.mock import MagicMock, patch
from datetime import date

import pytest

from app.services.search_service import SearchService, count_tokens
from app.domain.entities import (
    SearchRequest,
    SearchAlgorithm,
    EmbeddingModel,
    ChatResponse,
)
from app.domain.exceptions import EmbeddingGenerationError

from tests.conftest import (
    make_match,
    make_event,
    make_search_result,
    make_mock_match_repo,
    make_mock_event_repo,
    make_mock_openai_adapter,
)


@pytest.fixture
def service(mock_match_repo, mock_event_repo, mock_openai_adapter):
    return SearchService(
        match_repo=mock_match_repo,
        event_repo=mock_event_repo,
        openai_adapter=mock_openai_adapter,
    )


@pytest.fixture
def mock_match_repo():
    return make_mock_match_repo()


@pytest.fixture
def mock_event_repo():
    return make_mock_event_repo()


@pytest.fixture
def mock_openai_adapter():
    return make_mock_openai_adapter()


def make_request(**kwargs) -> SearchRequest:
    defaults = dict(match_id=3943043, query="Who scored the first goal?")
    defaults.update(kwargs)
    return SearchRequest(**defaults)


# ===========================================================================
# search_and_chat — happy path
# ===========================================================================

class TestSearchAndChatHappyPath:
    def test_search_and_chat_valid_request_returns_chat_response(self, service):
        request = make_request()
        result = service.search_and_chat(request)
        assert isinstance(result, ChatResponse)

    def test_question_preserved_in_response(self, service):
        request = make_request(query="Who scored?")
        result = service.search_and_chat(request)
        assert result.question == "Who scored?"

    def test_normalized_question_is_set(self, service, mock_openai_adapter):
        mock_openai_adapter.translate_to_english.return_value = "Who scored?"
        request = make_request(query="Who scored?", language="english")
        result = service.search_and_chat(request)
        assert result.normalized_question == "Who scored?"

    def test_embedding_called_with_normalized_query(self, service, mock_openai_adapter):
        request = make_request(query="hello", language="english")
        service.search_and_chat(request)
        mock_openai_adapter.create_embedding.assert_called_once_with(
            text="hello", model=EmbeddingModel.T3_SMALL
        )

    def test_search_called_with_embedding(self, service, mock_event_repo, mock_openai_adapter):
        embedding = [0.5] * 1536
        mock_openai_adapter.create_embedding.return_value = embedding
        request = make_request()
        service.search_and_chat(request)
        mock_event_repo.search_by_embedding.assert_called_once()
        call_kwargs = mock_event_repo.search_by_embedding.call_args
        assert call_kwargs[1]["query_embedding"] == embedding or call_kwargs[0][1] == embedding

    def test_search_results_in_response(self, service, mock_event_repo):
        events = [make_event(i) for i in range(3)]
        results = [make_search_result(e, i + 1) for i, e in enumerate(events)]
        mock_event_repo.search_by_embedding.return_value = results
        request = make_request()
        response = service.search_and_chat(request)
        assert len(response.search_results) == 3

    def test_match_info_fetched_when_requested(self, service, mock_match_repo):
        request = make_request(include_match_info=True)
        response = service.search_and_chat(request)
        mock_match_repo.get_by_id.assert_called_once_with(request.match_id)
        assert response.match_info is not None

    def test_match_info_not_fetched_when_not_requested(self, service, mock_match_repo):
        request = make_request(include_match_info=False)
        response = service.search_and_chat(request)
        mock_match_repo.get_by_id.assert_not_called()
        assert response.match_info is None

    def test_search_and_chat_mocked_llm_returns_expected_answer(self, service, mock_openai_adapter):
        mock_openai_adapter.create_chat_completion.return_value = "Spain won 2-1."
        request = make_request()
        response = service.search_and_chat(request)
        assert response.answer == "Spain won 2-1."

    def test_metadata_contains_key_fields(self, service):
        request = make_request(match_id=99, search_algorithm=SearchAlgorithm.COSINE)
        response = service.search_and_chat(request)
        assert response.metadata["match_id"] == 99
        assert "search_algorithm" in response.metadata
        assert "results_count" in response.metadata

    def test_metadata_results_count_matches_search_results(self, service, mock_event_repo):
        mock_event_repo.search_by_embedding.return_value = [make_search_result() for _ in range(5)]
        response = service.search_and_chat(make_request())
        assert response.metadata["results_count"] == 5


# ===========================================================================
# Query normalization / translation
# ===========================================================================

class TestQueryNormalization:
    def test_english_query_not_translated(self, service, mock_openai_adapter):
        request = make_request(query="Who scored?", language="english")
        service.search_and_chat(request)
        mock_openai_adapter.translate_to_english.assert_not_called()

    def test_spanish_query_translated(self, service, mock_openai_adapter):
        mock_openai_adapter.translate_to_english.return_value = "Who scored?"
        request = make_request(query="¿Quién marcó?", language="spanish")
        response = service.search_and_chat(request)
        mock_openai_adapter.translate_to_english.assert_called_once_with("¿Quién marcó?", "spanish")

    def test_translation_failure_uses_original_query(self, service, mock_openai_adapter):
        mock_openai_adapter.translate_to_english.side_effect = Exception("API down")
        request = make_request(query="¿Quién marcó?", language="spanish")
        response = service.search_and_chat(request)
        # Should fall back to original query, not raise
        assert response.normalized_question == "¿Quién marcó?"

    def test_normalized_query_used_for_embedding(self, service, mock_openai_adapter):
        mock_openai_adapter.translate_to_english.return_value = "Who scored the goal?"
        request = make_request(query="¿Quién marcó?", language="spanish")
        service.search_and_chat(request)
        mock_openai_adapter.create_embedding.assert_called_once_with(
            text="Who scored the goal?", model=request.embedding_model
        )


# ===========================================================================
# Answer generation
# ===========================================================================

class TestAnswerGeneration:
    def test_chat_completion_called(self, service, mock_openai_adapter):
        request = make_request()
        service.search_and_chat(request)
        mock_openai_adapter.create_chat_completion.assert_called_once()

    def test_custom_system_message_passed(self, service, mock_openai_adapter):
        custom_msg = "You are a football expert."
        request = make_request(system_message=custom_msg)
        service.search_and_chat(request)
        call_args = mock_openai_adapter.create_chat_completion.call_args
        messages = call_args[1].get("messages") or call_args[0][0]
        system_content = messages[0]["content"]
        assert custom_msg == system_content

    def test_default_system_message_used_when_none(self, service, mock_openai_adapter):
        request = make_request(system_message=None)
        service.search_and_chat(request)
        call_args = mock_openai_adapter.create_chat_completion.call_args
        messages = call_args[1].get("messages") or call_args[0][0]
        assert messages[0]["role"] == "system"
        assert len(messages[0]["content"]) > 0

    def test_chat_failure_returns_error_message(self, service, mock_openai_adapter):
        mock_openai_adapter.create_chat_completion.side_effect = Exception("timeout")
        request = make_request()
        response = service.search_and_chat(request)
        assert "ERROR" in response.answer or "error" in response.answer.lower()

    def test_temperature_passed_to_llm(self, service, mock_openai_adapter):
        request = make_request(temperature=0.9)
        service.search_and_chat(request)
        call_args = mock_openai_adapter.create_chat_completion.call_args
        assert call_args[1].get("temperature") == 0.9 or call_args[0][1] == 0.9

    def test_match_display_name_in_context(self, service, mock_match_repo, mock_openai_adapter):
        match = make_match(home_score=3, away_score=0)
        mock_match_repo.get_by_id.return_value = match
        request = make_request(include_match_info=True)
        service.search_and_chat(request)
        call_args = mock_openai_adapter.create_chat_completion.call_args
        messages = call_args[1].get("messages") or call_args[0][0]
        user_content = messages[1]["content"]
        assert "Spain" in user_content or "England" in user_content

    def test_empty_search_results_handled(self, service, mock_event_repo):
        mock_event_repo.search_by_embedding.return_value = []
        request = make_request()
        response = service.search_and_chat(request)
        assert response.search_results == []

    def test_event_summaries_in_context(self, service, mock_event_repo, mock_openai_adapter):
        event = make_event(summary="Oyarzabal scores the winning goal")
        mock_event_repo.search_by_embedding.return_value = [make_search_result(event)]
        service.search_and_chat(make_request())
        call_args = mock_openai_adapter.create_chat_completion.call_args
        messages = call_args[1].get("messages") or call_args[0][0]
        user_content = messages[1]["content"]
        assert "Oyarzabal scores" in user_content


# ===========================================================================
# Error propagation
# ===========================================================================

class TestErrorPropagation:
    def test_embedding_error_propagates(self, service, mock_openai_adapter):
        mock_openai_adapter.create_embedding.side_effect = EmbeddingGenerationError("rate limit")
        with pytest.raises(EmbeddingGenerationError):
            service.search_and_chat(make_request())

    def test_repo_search_error_propagates(self, service, mock_event_repo):
        mock_event_repo.search_by_embedding.side_effect = Exception("DB timeout")
        with pytest.raises(Exception, match="DB timeout"):
            service.search_and_chat(make_request())


# ===========================================================================
# Token counting utility
# ===========================================================================

class TestCountTokens:
    def test_count_tokens_returns_positive_int(self):
        """Verify tiktoken integration returns a positive integer."""
        result = count_tokens("Hello, world!", model="gpt-4")
        assert isinstance(result, int)
        assert result > 0

    def test_count_tokens_empty_string_returns_zero(self):
        """Empty string should return 0 tokens."""
        result = count_tokens("", model="gpt-4")
        assert result == 0

    def test_count_tokens_unknown_model_uses_fallback(self):
        """Unknown model should fall back to cl100k_base without error."""
        result = count_tokens("Hello, world!", model="unknown-model-xyz")
        assert isinstance(result, int)
        assert result > 0


# ===========================================================================
# Token budget guard — truncation and metadata
# ===========================================================================

class TestTokenBudgetGuard:
    def test_generate_answer_within_budget_includes_all_results(
        self, service, mock_event_repo, mock_openai_adapter
    ):
        """When context fits within budget, no results should be truncated."""
        events = [make_event(event_id=i, summary=f"Event {i}") for i in range(5)]
        results = [make_search_result(e, rank=i + 1) for i, e in enumerate(events)]
        mock_event_repo.search_by_embedding.return_value = results
        mock_openai_adapter.create_chat_completion.return_value = "Answer."

        request = make_request(max_input_tokens=100000)
        response = service.search_and_chat(request)

        assert len(response.search_results) == 5
        assert response.metadata.get("results_truncated") == 0

    def test_generate_answer_over_budget_truncates_lowest_ranked(
        self, service, mock_event_repo, mock_openai_adapter
    ):
        """When context exceeds budget, lowest-ranked results should be dropped."""
        # Create events with long summaries to blow the budget
        long_summary = "x " * 500  # ~500 tokens per event
        events = [make_event(event_id=i, summary=long_summary) for i in range(10)]
        results = [make_search_result(e, rank=i + 1) for i, e in enumerate(events)]
        mock_event_repo.search_by_embedding.return_value = results
        mock_openai_adapter.create_chat_completion.return_value = "Answer."

        # Set a low budget so truncation must happen
        request = make_request(max_input_tokens=500)
        response = service.search_and_chat(request)

        # Some results must have been truncated
        assert response.metadata.get("results_truncated", 0) > 0
        assert len(response.search_results) < 10

    def test_generate_answer_question_exceeds_budget_returns_error(
        self, service, mock_event_repo, mock_openai_adapter
    ):
        """When the question + system message alone exceed budget, return error without calling LLM."""
        # Very long question
        long_question = "word " * 2000
        mock_event_repo.search_by_embedding.return_value = []

        request = make_request(query=long_question, max_input_tokens=50)
        response = service.search_and_chat(request)

        # Should not call LLM
        mock_openai_adapter.create_chat_completion.assert_not_called()
        # Response should indicate error
        assert "ERROR" in response.answer or "budget" in response.answer.lower()

    def test_response_metadata_includes_token_usage(
        self, service, mock_event_repo, mock_openai_adapter
    ):
        """Metadata should include input_tokens, max_input_tokens, results_truncated."""
        events = [make_event(event_id=1, summary="Short event")]
        results = [make_search_result(events[0], rank=1)]
        mock_event_repo.search_by_embedding.return_value = results
        mock_openai_adapter.create_chat_completion.return_value = "Answer."

        request = make_request(max_input_tokens=100000)
        response = service.search_and_chat(request)

        assert "input_tokens" in response.metadata
        assert "max_input_tokens" in response.metadata
        assert "results_truncated" in response.metadata
        assert isinstance(response.metadata["input_tokens"], int)
        assert response.metadata["max_input_tokens"] == 100000
        assert response.metadata["results_truncated"] == 0

    def test_truncation_removes_highest_rank_first(
        self, service, mock_event_repo, mock_openai_adapter
    ):
        """Truncation should remove the highest-rank (lowest relevance) results first."""
        long_summary = "x " * 500
        events = [make_event(event_id=i, summary=long_summary) for i in range(5)]
        results = [make_search_result(e, rank=i + 1) for i, e in enumerate(events)]
        mock_event_repo.search_by_embedding.return_value = results
        mock_openai_adapter.create_chat_completion.return_value = "Answer."

        request = make_request(max_input_tokens=500)
        response = service.search_and_chat(request)

        # Remaining results should have the lowest rank numbers (most relevant)
        remaining_ranks = [r.rank for r in response.search_results]
        for rank in remaining_ranks:
            assert rank <= len(remaining_ranks)
