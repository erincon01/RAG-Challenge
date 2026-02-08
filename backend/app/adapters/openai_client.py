"""
OpenAI/Azure OpenAI adapter for embedding and chat completions.

This adapter provides a unified interface for interacting with OpenAI services,
whether using direct OpenAI API or Azure OpenAI.
"""

import logging
from typing import List, Optional
from openai import AzureOpenAI

from app.core.config import get_settings
from app.domain.exceptions import EmbeddingGenerationError

logger = logging.getLogger(__name__)
settings = get_settings()


class OpenAIAdapter:
    """Adapter for OpenAI/Azure OpenAI API calls."""

    def __init__(self):
        """Initialize the OpenAI client."""
        self.client = AzureOpenAI(
            azure_endpoint=settings.openai.endpoint,
            api_key=settings.openai.api_key,
            api_version="2024-02-01",
        )

    def create_embedding(
        self, text: str, model: str = "text-embedding-3-small"
    ) -> List[float]:
        """
        Generate an embedding vector for the given text.

        Args:
            text: Text to embed
            model: Embedding model to use

        Returns:
            Embedding vector as list of floats

        Raises:
            EmbeddingGenerationError: If embedding generation fails
        """
        try:
            response = self.client.embeddings.create(input=text, model=model)
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to create embedding: {e}")
            raise EmbeddingGenerationError(f"Failed to create embedding: {e}")

    def create_chat_completion(
        self,
        messages: List[dict],
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 5000,
    ) -> str:
        """
        Generate a chat completion using the LLM.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model to use (defaults to settings.openai.model)
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response

        Returns:
            The generated text response

        Raises:
            Exception: If chat completion fails
        """
        if model is None:
            model = settings.openai.model

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Failed to create chat completion: {e}")
            raise

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
            return self.create_chat_completion(
                messages=messages, temperature=0.1, max_tokens=500
            )
        except Exception as e:
            logger.error(f"Failed to translate text: {e}")
            # Return original text if translation fails
            return text


def get_openai_adapter() -> OpenAIAdapter:
    """
    Get an OpenAI adapter instance.

    This function is used for dependency injection in FastAPI.

    Returns:
        OpenAIAdapter instance
    """
    return OpenAIAdapter()
