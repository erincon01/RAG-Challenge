"""
OpenAI/Azure OpenAI adapter for embedding and chat completions.

This adapter provides a unified interface for interacting with OpenAI services.
Supports both Azure OpenAI and direct OpenAI API via OPENAI_PROVIDER setting.
"""

import logging
import time

from openai import APIError, AzureOpenAI, OpenAI, RateLimitError

from app.core.config import get_settings
from app.domain.exceptions import EmbeddingGenerationError

logger = logging.getLogger(__name__)
settings = get_settings()

# Retry configuration
MAX_RETRIES = 5
INITIAL_BACKOFF = 1.0  # seconds
MAX_BACKOFF = 60.0
BATCH_SIZE = 50  # texts per API call for batch embeddings


class OpenAIAdapter:
    """Adapter for OpenAI/Azure OpenAI API calls."""

    def __init__(self):
        """Initialize the OpenAI client based on configured provider."""
        provider = getattr(settings.openai, "provider", "azure")
        if provider == "openai":
            self.client = OpenAI(api_key=settings.openai.api_key)
        else:
            self.client = AzureOpenAI(
                azure_endpoint=settings.openai.endpoint,
                api_key=settings.openai.api_key,
                api_version="2024-06-01",
            )

    def create_embedding(self, text: str, model: str = "text-embedding-3-small") -> list[float]:
        """
        Generate an embedding vector for the given text with retry logic.

        Args:
            text: Text to embed
            model: Embedding model to use

        Returns:
            Embedding vector as list of floats

        Raises:
            EmbeddingGenerationError: If embedding generation fails after retries
        """
        return self._call_with_retry(
            lambda: self.client.embeddings.create(input=text, model=model).data[0].embedding,
            operation="create_embedding",
        )

    def create_embeddings_batch(self, texts: list[str], model: str = "text-embedding-3-small") -> list[list[float]]:
        """
        Generate embedding vectors for multiple texts in batches.

        Sends texts in batches to reduce HTTP round-trips and handles
        rate limiting with exponential backoff.

        Args:
            texts: List of texts to embed
            model: Embedding model to use

        Returns:
            List of embedding vectors (same order as input texts)

        Raises:
            EmbeddingGenerationError: If embedding generation fails after retries
        """
        all_embeddings: list[list[float]] = []

        for i in range(0, len(texts), BATCH_SIZE):
            batch = texts[i : i + BATCH_SIZE]

            embeddings = self._call_with_retry(
                lambda b=batch: [item.embedding for item in self.client.embeddings.create(input=b, model=model).data],
                operation=f"create_embeddings_batch[{i}:{i + len(batch)}]",
            )
            all_embeddings.extend(embeddings)

            # Small delay between batches to stay under rate limits
            if i + BATCH_SIZE < len(texts):
                time.sleep(0.1)

        return all_embeddings

    def create_chat_completion(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 5000,
    ) -> str:
        """
        Generate a chat completion using the LLM with retry logic.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model to use (defaults to settings.openai.model)
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response

        Returns:
            The generated text response

        Raises:
            Exception: If chat completion fails after retries
        """
        if model is None:
            model = settings.openai.model

        return self._call_with_retry(
            lambda: self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            .choices[0]
            .message.content,
            operation="create_chat_completion",
        )

    def translate_to_english(self, text: str, source_language: str) -> str:
        """
        Translate text from source language to English.

        Args:
            text: Text to translate
            source_language: Source language

        Returns:
            Translated text in English
        """
        if source_language.lower() == "english":
            return text

        messages = [
            {
                "role": "system",
                "content": f"Translate the following text from {source_language} to English. "
                f"Return only the translation, nothing else.",
            },
            {"role": "user", "content": text},
        ]

        try:
            return self.create_chat_completion(messages=messages, temperature=0.1, max_tokens=500)
        except Exception as e:
            logger.error(f"Failed to translate text: {e}")
            return text

    def _call_with_retry(self, fn, operation: str = "api_call"):
        """
        Execute an API call with exponential backoff retry on rate limits.

        Args:
            fn: Callable that performs the API call
            operation: Description for logging

        Returns:
            The result of the API call

        Raises:
            EmbeddingGenerationError: If all retries are exhausted
        """
        backoff = INITIAL_BACKOFF
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                return fn()
            except RateLimitError as e:
                if attempt == MAX_RETRIES:
                    logger.error(f"{operation}: rate limit exhausted after {MAX_RETRIES} retries")
                    raise EmbeddingGenerationError(f"Rate limit exceeded: {e}")
                logger.warning(
                    f"{operation}: rate limited, retrying in {backoff:.1f}s (attempt {attempt}/{MAX_RETRIES})"
                )
                time.sleep(backoff)
                backoff = min(backoff * 2, MAX_BACKOFF)
            except APIError as e:
                if attempt == MAX_RETRIES:
                    logger.error(f"{operation}: API error after {MAX_RETRIES} retries: {e}")
                    raise EmbeddingGenerationError(f"API error: {e}")
                logger.warning(f"{operation}: API error, retrying in {backoff:.1f}s (attempt {attempt}/{MAX_RETRIES})")
                time.sleep(backoff)
                backoff = min(backoff * 2, MAX_BACKOFF)
            except Exception as e:
                logger.error(f"{operation} failed: {e}")
                raise EmbeddingGenerationError(f"Failed {operation}: {e}")


def get_openai_adapter() -> OpenAIAdapter:
    """
    Get an OpenAI adapter instance.

    This function is used for dependency injection in FastAPI.

    Returns:
        OpenAIAdapter instance
    """
    return OpenAIAdapter()
