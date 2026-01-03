"""Abstract base class for LLM clients."""

from abc import ABC, abstractmethod
from typing import Any, Generator, Optional


class LLMClient(ABC):
    """
    Abstract base class for LLM clients.

    Defines the interface that all LLM providers must implement,
    allowing for easy swapping between Ollama (local) and HuggingFace (cloud).
    """

    @abstractmethod
    def check_connection(self) -> bool:
        """
        Check if the LLM service is available.

        Returns:
            True if connected and ready
        """
        pass

    @abstractmethod
    def check_model_available(self) -> bool:
        """
        Check if the configured model is available.

        Returns:
            True if model is available
        """
        pass

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
    ) -> str:
        """
        Generate text from a prompt.

        Args:
            prompt: User prompt
            system: Optional system prompt

        Returns:
            Generated text
        """
        pass

    @abstractmethod
    def generate_json(
        self,
        prompt: str,
        system: Optional[str] = None,
    ) -> Any:
        """
        Generate and parse JSON response.

        Args:
            prompt: User prompt
            system: Optional system prompt

        Returns:
            Parsed JSON object, or None if parsing fails
        """
        pass

    def generate_stream(
        self,
        prompt: str,
        system: Optional[str] = None,
    ) -> Generator[str, None, None]:
        """
        Stream text generation (optional).

        Default implementation returns full response as single chunk.
        Subclasses can override for true streaming.

        Args:
            prompt: User prompt
            system: Optional system prompt

        Yields:
            Generated text chunks
        """
        yield self.generate(prompt, system)

    def list_models(self) -> list[str]:
        """
        List available models (optional).

        Default implementation returns empty list.
        Subclasses can override to provide model listing.

        Returns:
            List of model names
        """
        return []

    @property
    def provider_name(self) -> str:
        """
        Get the provider name for display purposes.

        Returns:
            Provider name (e.g., 'Ollama', 'HuggingFace')
        """
        return self.__class__.__name__.replace("Client", "")


class LLMError(Exception):
    """Base exception for LLM-related errors."""

    pass
