"""
Unit tests for OpenAIAdapter — mock client, retry logic, batch embeddings.

All OpenAI API calls are mocked — no real API calls.
"""

from unittest.mock import MagicMock, patch, call
import pytest

from openai import RateLimitError, APIError

from app.adapters.openai_client import (
    OpenAIAdapter,
    MAX_RETRIES,
    INITIAL_BACKOFF,
    BATCH_SIZE,
)
from app.domain.exceptions import EmbeddingGenerationError


def _make_embedding_response(vectors: list[list[float]]):
    """Helper to build a mock embeddings API response."""
    response = MagicMock()
    response.data = [MagicMock(embedding=v) for v in vectors]
    return response


def _make_chat_response(content: str):
    """Helper to build a mock chat completions API response."""
    response = MagicMock()
    response.choices = [MagicMock(message=MagicMock(content=content))]
    return response


def _make_rate_limit_error():
    return RateLimitError(
        message="Rate limit exceeded",
        response=MagicMock(status_code=429, headers={}),
        body={"error": {"message": "Rate limit exceeded", "type": "rate_limit_error"}},
    )


def _make_api_error():
    return APIError(
        message="Internal server error",
        request=MagicMock(),
        body={"error": {"message": "Internal error"}},
    )


# ---------------------------------------------------------------------------
# Fixture: adapter with mocked OpenAI client
# ---------------------------------------------------------------------------

@pytest.fixture
def adapter_and_mock():
    """Returns (adapter, mock_client) with patched OpenAI constructor."""
    mock_client = MagicMock()
    with patch("app.adapters.openai_client.AzureOpenAI", return_value=mock_client), \
         patch("app.adapters.openai_client.OpenAI", return_value=mock_client), \
         patch("app.adapters.openai_client.settings") as mock_settings:
        mock_settings.openai.provider = "azure"
        mock_settings.openai.api_key = "test-key"
        mock_settings.openai.endpoint = "https://test.openai.azure.com"
        mock_settings.openai.model = "gpt-4o"
        adapter = OpenAIAdapter()
        adapter.client = mock_client
        yield adapter, mock_client


# ===========================================================================
# create_embedding
# ===========================================================================

class TestCreateEmbedding:
    def test_returns_vector(self, adapter_and_mock):
        adapter, mock_client = adapter_and_mock
        expected = [0.1, 0.2, 0.3]
        mock_client.embeddings.create.return_value = _make_embedding_response([expected])

        result = adapter.create_embedding("hello world", model="text-embedding-3-small")

        assert result == expected
        mock_client.embeddings.create.assert_called_once_with(
            input="hello world", model="text-embedding-3-small"
        )

    def test_uses_provided_model(self, adapter_and_mock):
        adapter, mock_client = adapter_and_mock
        mock_client.embeddings.create.return_value = _make_embedding_response([[0.5] * 1536])

        adapter.create_embedding("text", model="text-embedding-ada-002")

        args, kwargs = mock_client.embeddings.create.call_args
        assert kwargs["model"] == "text-embedding-ada-002"

    def test_raises_on_non_api_error(self, adapter_and_mock):
        adapter, mock_client = adapter_and_mock
        mock_client.embeddings.create.side_effect = ValueError("unexpected")

        with pytest.raises(EmbeddingGenerationError):
            adapter.create_embedding("text")


# ===========================================================================
# create_embeddings_batch
# ===========================================================================

class TestCreateEmbeddingsBatch:
    def test_single_batch(self, adapter_and_mock):
        adapter, mock_client = adapter_and_mock
        texts = ["a", "b", "c"]
        vectors = [[0.1] * 10, [0.2] * 10, [0.3] * 10]
        mock_client.embeddings.create.return_value = _make_embedding_response(vectors)

        result = adapter.create_embeddings_batch(texts)

        assert len(result) == 3
        assert result[0] == [0.1] * 10

    def test_multiple_batches(self, adapter_and_mock):
        adapter, mock_client = adapter_and_mock
        texts = [f"text-{i}" for i in range(BATCH_SIZE + 5)]

        # First batch: BATCH_SIZE vectors, second batch: 5 vectors
        batch1 = [[float(i)] * 3 for i in range(BATCH_SIZE)]
        batch2 = [[float(i)] * 3 for i in range(5)]

        mock_client.embeddings.create.side_effect = [
            _make_embedding_response(batch1),
            _make_embedding_response(batch2),
        ]

        with patch("app.adapters.openai_client.time.sleep"):
            result = adapter.create_embeddings_batch(texts)

        assert len(result) == BATCH_SIZE + 5
        assert mock_client.embeddings.create.call_count == 2

    def test_empty_input_returns_empty(self, adapter_and_mock):
        adapter, mock_client = adapter_and_mock
        result = adapter.create_embeddings_batch([])
        assert result == []
        mock_client.embeddings.create.assert_not_called()

    def test_inter_batch_sleep_called(self, adapter_and_mock):
        adapter, mock_client = adapter_and_mock
        texts = [f"text-{i}" for i in range(BATCH_SIZE + 1)]

        mock_client.embeddings.create.side_effect = [
            _make_embedding_response([[0.1] * 3 for _ in range(BATCH_SIZE)]),
            _make_embedding_response([[0.2] * 3]),
        ]

        with patch("app.adapters.openai_client.time.sleep") as mock_sleep:
            adapter.create_embeddings_batch(texts)

        mock_sleep.assert_called_once()  # exactly once between batches


# ===========================================================================
# create_chat_completion
# ===========================================================================

class TestCreateChatCompletion:
    def test_returns_content(self, adapter_and_mock):
        adapter, mock_client = adapter_and_mock
        mock_client.chat.completions.create.return_value = _make_chat_response("Spain won 2-1.")

        messages = [{"role": "user", "content": "Who won?"}]
        result = adapter.create_chat_completion(messages)

        assert result == "Spain won 2-1."

    def test_uses_settings_model_by_default(self, adapter_and_mock):
        adapter, mock_client = adapter_and_mock
        mock_client.chat.completions.create.return_value = _make_chat_response("ok")

        adapter.create_chat_completion([{"role": "user", "content": "hi"}])

        args, kwargs = mock_client.chat.completions.create.call_args
        assert kwargs["model"] == "gpt-4o"  # from mock settings

    def test_uses_provided_model(self, adapter_and_mock):
        adapter, mock_client = adapter_and_mock
        mock_client.chat.completions.create.return_value = _make_chat_response("ok")

        adapter.create_chat_completion([{"role": "user", "content": "hi"}], model="gpt-4-turbo")

        args, kwargs = mock_client.chat.completions.create.call_args
        assert kwargs["model"] == "gpt-4-turbo"

    def test_passes_temperature_and_max_tokens(self, adapter_and_mock):
        adapter, mock_client = adapter_and_mock
        mock_client.chat.completions.create.return_value = _make_chat_response("ok")

        adapter.create_chat_completion(
            [{"role": "user", "content": "hi"}],
            temperature=0.7,
            max_tokens=200,
        )

        args, kwargs = mock_client.chat.completions.create.call_args
        assert kwargs["temperature"] == 0.7
        assert kwargs["max_tokens"] == 200


# ===========================================================================
# translate_to_english
# ===========================================================================

class TestTranslateToEnglish:
    def test_english_returned_as_is(self, adapter_and_mock):
        adapter, mock_client = adapter_and_mock
        result = adapter.translate_to_english("Who scored?", "english")
        assert result == "Who scored?"
        mock_client.chat.completions.create.assert_not_called()

    def test_other_language_calls_api(self, adapter_and_mock):
        adapter, mock_client = adapter_and_mock
        mock_client.chat.completions.create.return_value = _make_chat_response("Who scored?")

        result = adapter.translate_to_english("¿Quién marcó?", "spanish")

        assert result == "Who scored?"
        mock_client.chat.completions.create.assert_called_once()

    def test_translation_failure_returns_original(self, adapter_and_mock):
        adapter, mock_client = adapter_and_mock
        mock_client.chat.completions.create.side_effect = Exception("API down")

        result = adapter.translate_to_english("¿Quién marcó?", "spanish")

        assert result == "¿Quién marcó?"


# ===========================================================================
# Retry logic (_call_with_retry)
# ===========================================================================

class TestRetryLogic:
    def test_retries_on_rate_limit_then_succeeds(self, adapter_and_mock):
        adapter, mock_client = adapter_and_mock
        rate_error = _make_rate_limit_error()
        success_response = _make_embedding_response([[0.1] * 3])

        mock_client.embeddings.create.side_effect = [rate_error, success_response]

        with patch("app.adapters.openai_client.time.sleep"):
            result = adapter.create_embedding("text")

        assert result == [0.1] * 3
        assert mock_client.embeddings.create.call_count == 2

    def test_retries_on_api_error_then_succeeds(self, adapter_and_mock):
        adapter, mock_client = adapter_and_mock
        api_error = _make_api_error()
        success_response = _make_embedding_response([[0.2] * 3])

        mock_client.embeddings.create.side_effect = [api_error, api_error, success_response]

        with patch("app.adapters.openai_client.time.sleep"):
            result = adapter.create_embedding("text")

        assert result == [0.2] * 3
        assert mock_client.embeddings.create.call_count == 3

    def test_raises_after_max_retries_rate_limit(self, adapter_and_mock):
        adapter, mock_client = adapter_and_mock
        mock_client.embeddings.create.side_effect = _make_rate_limit_error()

        with patch("app.adapters.openai_client.time.sleep"):
            with pytest.raises(EmbeddingGenerationError, match="Rate limit"):
                adapter.create_embedding("text")

        assert mock_client.embeddings.create.call_count == MAX_RETRIES

    def test_raises_after_max_retries_api_error(self, adapter_and_mock):
        adapter, mock_client = adapter_and_mock
        mock_client.embeddings.create.side_effect = _make_api_error()

        with patch("app.adapters.openai_client.time.sleep"):
            with pytest.raises(EmbeddingGenerationError, match="API error"):
                adapter.create_embedding("text")

        assert mock_client.embeddings.create.call_count == MAX_RETRIES

    def test_raises_immediately_on_unexpected_error(self, adapter_and_mock):
        adapter, mock_client = adapter_and_mock
        mock_client.embeddings.create.side_effect = ValueError("bad input")

        with pytest.raises(EmbeddingGenerationError):
            adapter.create_embedding("text")

        # Should NOT retry on non-rate-limit errors
        assert mock_client.embeddings.create.call_count == 1

    def test_exponential_backoff_timing(self, adapter_and_mock):
        adapter, mock_client = adapter_and_mock
        rate_error = _make_rate_limit_error()
        success = _make_embedding_response([[0.1] * 3])

        mock_client.embeddings.create.side_effect = [rate_error, rate_error, success]

        with patch("app.adapters.openai_client.time.sleep") as mock_sleep:
            adapter.create_embedding("text")

        calls = mock_sleep.call_args_list
        assert len(calls) == 2
        # Second backoff should be double the first
        first_delay = calls[0][0][0]
        second_delay = calls[1][0][0]
        assert second_delay == first_delay * 2
        assert first_delay == INITIAL_BACKOFF
