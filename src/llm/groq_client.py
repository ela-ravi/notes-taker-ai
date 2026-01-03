"""Groq API client for fast, low-cost cloud LLM processing."""

import json
from dataclasses import dataclass
from typing import Any, Generator, Optional

from ..config import get_settings
from ..utils.logging_config import get_logger
from .base import LLMClient, LLMError

logger = get_logger("llm.groq")


@dataclass
class GroqConfig:
    """Groq configuration."""

    model: str = "llama-3.1-8b-instant"
    api_key: Optional[str] = None
    temperature: float = 0.3
    max_tokens: int = 4096
    timeout: float = 120.0


class GroqError(LLMError):
    """Groq-related errors."""

    pass


class GroqClient(LLMClient):
    """
    Client for interacting with Groq API.

    Groq provides extremely fast inference using custom LPU chips,
    with very competitive pricing for cloud LLM processing.
    """

    # Available models on Groq
    AVAILABLE_MODELS = [
        "llama-3.1-8b-instant",      # Fast, good quality
        "llama-3.1-70b-versatile",   # Higher quality, slower
        "llama-3.3-70b-versatile",   # Latest Llama 3.3
        "mixtral-8x7b-32768",        # Mixtral, large context
        "gemma2-9b-it",              # Google Gemma 2
    ]

    def __init__(self, config: Optional[GroqConfig] = None):
        """
        Initialize the Groq client.

        Args:
            config: Groq configuration
        """
        settings = get_settings()

        if config:
            self.config = config
        else:
            self.config = GroqConfig(
                model=settings.groq_model,
                api_key=settings.groq_api_key,
                temperature=settings.ollama_temperature,  # Reuse temperature setting
            )

        self._client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the Groq client."""
        try:
            from groq import Groq

            if not self.config.api_key:
                raise GroqError(
                    "Groq API key not configured. "
                    "Get your free API key at: https://console.groq.com/keys"
                )

            self._client = Groq(
                api_key=self.config.api_key,
                timeout=self.config.timeout,
            )
        except ImportError:
            raise GroqError(
                "groq package not installed. "
                "Run: pip install groq"
            )

    def check_connection(self) -> bool:
        """
        Check if Groq API is accessible.

        Returns:
            True if connected
        """
        if not self.config.api_key:
            logger.error("Groq API key not configured")
            return False

        try:
            # Try a minimal API call to verify connection
            self._client.chat.completions.create(
                model=self.config.model,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=1,
            )
            return True
        except Exception as e:
            error_str = str(e).lower()
            if "401" in error_str or "invalid api key" in error_str:
                logger.error("Groq authentication failed. Check your GROQ_API_KEY.")
            elif "rate limit" in error_str or "429" in error_str:
                logger.warning("Groq rate limited, but connection works.")
                return True  # Rate limit means we're connected
            else:
                logger.error(f"Cannot connect to Groq: {e}")
            return False

    def check_model_available(self) -> bool:
        """
        Check if the configured model is available.

        Returns:
            True if model is available
        """
        # Groq has a fixed set of models, check against known list
        if self.config.model in self.AVAILABLE_MODELS:
            return True

        # Try to use the model anyway (in case of new models)
        try:
            self._client.chat.completions.create(
                model=self.config.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1,
            )
            return True
        except Exception as e:
            logger.error(f"Model '{self.config.model}' not available: {e}")
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
        try:
            messages = []

            if system:
                messages.append({"role": "system", "content": system})

            messages.append({"role": "user", "content": prompt})

            response = self._client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
            )

            return response.choices[0].message.content

        except Exception as e:
            error_str = str(e).lower()
            if "rate limit" in error_str or "429" in error_str:
                raise GroqError(
                    "Groq rate limit exceeded. Please wait a moment and try again. "
                    "Free tier allows 6,000 requests/day."
                )
            elif "401" in error_str or "invalid api key" in error_str:
                raise GroqError(
                    "Groq authentication failed. "
                    "Please check your GROQ_API_KEY in .env file. "
                    "Get a free API key at: https://console.groq.com/keys"
                )
            else:
                logger.error(f"Error generating text: {e}")
                raise GroqError(f"Generation failed: {e}")

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
        try:
            messages = []

            if system:
                messages.append({"role": "system", "content": system})

            messages.append({"role": "user", "content": prompt})

            stream = self._client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                stream=True,
            )

            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"Error in stream generation: {e}")
            raise GroqError(f"Stream generation failed: {e}")

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
        List available Groq models.

        Returns:
            List of model names
        """
        return self.AVAILABLE_MODELS.copy()

    @property
    def provider_name(self) -> str:
        """Get the provider name."""
        return "Groq"
