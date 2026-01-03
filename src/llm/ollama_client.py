"""Ollama API client for local LLM processing."""

import json
from dataclasses import dataclass
from typing import Any, Generator, Optional

import ollama as ollama_lib

from ..config import get_settings
from ..utils.logging_config import get_logger
from .base import LLMClient, LLMError

logger = get_logger("llm.ollama")


@dataclass
class OllamaConfig:
    """Ollama configuration."""

    model: str = "llama3.2"
    host: str = "http://localhost:11434"
    temperature: float = 0.3
    max_tokens: int = 4096
    timeout: float = 120.0


class OllamaError(LLMError):
    """Ollama-related errors."""

    pass


class OllamaClient(LLMClient):
    """
    Client for interacting with local Ollama LLM.

    This client handles communication with the Ollama server for
    text generation, including meeting summarization tasks.
    """

    def __init__(self, config: Optional[OllamaConfig] = None):
        """
        Initialize the Ollama client.

        Args:
            config: Ollama configuration
        """
        settings = get_settings()

        if config:
            self.config = config
        else:
            self.config = OllamaConfig(
                model=settings.ollama_model,
                host=settings.ollama_host,
                temperature=settings.ollama_temperature,
            )

        self._client = ollama_lib.Client(host=self.config.host)
        self._model_verified = False

    def check_connection(self) -> bool:
        """
        Check if Ollama server is running.

        Returns:
            True if connected
        """
        try:
            self._client.list()
            return True
        except Exception as e:
            logger.error(f"Cannot connect to Ollama: {e}")
            return False

    def check_model_available(self) -> bool:
        """
        Check if the configured model is available.

        Returns:
            True if model is available
        """
        try:
            result = self._client.list()

            # Handle both old dict format and new object format
            if hasattr(result, 'models'):
                models = result.models
                model_names = [getattr(m, 'model', str(m)) for m in models]
            elif isinstance(result, dict):
                models = result.get("models", [])
                model_names = [m.get("name", "") if isinstance(m, dict) else str(m) for m in models]
            else:
                model_names = []

            # Check for exact match or partial match
            for name in model_names:
                if self.config.model in name or name.startswith(self.config.model):
                    return True

            logger.warning(
                f"Model '{self.config.model}' not found. "
                f"Available: {', '.join(model_names)}"
            )
            return False

        except Exception as e:
            logger.error(f"Error checking model: {e}")
            return False

    def pull_model(self) -> bool:
        """
        Pull the configured model if not available.

        Returns:
            True if successful
        """
        try:
            logger.info(f"Pulling model: {self.config.model}")
            self._client.pull(self.config.model)
            logger.info("Model pulled successfully")
            return True
        except Exception as e:
            logger.error(f"Error pulling model: {e}")
            return False

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
        messages = []

        if system:
            messages.append({"role": "system", "content": system})

        messages.append({"role": "user", "content": prompt})

        try:
            response = self._client.chat(
                model=self.config.model,
                messages=messages,
                options={
                    "temperature": self.config.temperature,
                    "num_predict": self.config.max_tokens,
                },
            )

            return response["message"]["content"]

        except Exception as e:
            logger.error(f"Error generating text: {e}")
            raise OllamaError(f"Generation failed: {e}")

    def generate_stream(
        self,
        prompt: str,
        system: Optional[str] = None,
    ) -> Generator[str, None, None]:
        """
        Stream text generation.

        Args:
            prompt: User prompt
            system: Optional system prompt

        Yields:
            Generated text chunks
        """
        messages = []

        if system:
            messages.append({"role": "system", "content": system})

        messages.append({"role": "user", "content": prompt})

        try:
            stream = self._client.chat(
                model=self.config.model,
                messages=messages,
                stream=True,
                options={
                    "temperature": self.config.temperature,
                    "num_predict": self.config.max_tokens,
                },
            )

            for chunk in stream:
                content = chunk.get("message", {}).get("content", "")
                if content:
                    yield content

        except Exception as e:
            logger.error(f"Error in stream generation: {e}")
            raise OllamaError(f"Stream generation failed: {e}")

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
            Parsed JSON object
        """
        response = self.generate(prompt, system)

        # Try to extract JSON from response
        try:
            # Try direct parse first
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Try to find JSON in response
        try:
            # Look for array
            start = response.find("[")
            end = response.rfind("]") + 1
            if start != -1 and end > start:
                return json.loads(response[start:end])

            # Look for object
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(response[start:end])

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from response: {e}")
            logger.debug(f"Response was: {response}")

        return None

    def list_models(self) -> list[str]:
        """
        List available models.

        Returns:
            List of model names
        """
        try:
            result = self._client.list()

            # Handle both old dict format and new object format
            if hasattr(result, 'models'):
                models = result.models
                return [getattr(m, 'model', str(m)) for m in models]
            elif isinstance(result, dict):
                models = result.get("models", [])
                return [m.get("name", "") if isinstance(m, dict) else str(m) for m in models]
            return []
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []

    @property
    def provider_name(self) -> str:
        """Get the provider name."""
        return "Ollama"
