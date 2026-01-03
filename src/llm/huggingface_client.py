"""HuggingFace Inference API client for cloud LLM processing."""

import json
from dataclasses import dataclass
from typing import Any, Generator, Optional

from ..config import get_settings
from ..utils.logging_config import get_logger
from .base import LLMClient, LLMError

logger = get_logger("llm.huggingface")


@dataclass
class HuggingFaceConfig:
    """HuggingFace configuration."""

    model: str = "meta-llama/Llama-3.1-8B-Instruct"
    token: Optional[str] = None
    temperature: float = 0.3
    max_tokens: int = 4096
    timeout: float = 120.0


class HuggingFaceError(LLMError):
    """HuggingFace-related errors."""

    pass


class HuggingFaceClient(LLMClient):
    """
    Client for interacting with HuggingFace Inference API.

    This client handles communication with HuggingFace's cloud-hosted
    models for text generation, including meeting summarization tasks.
    """

    def __init__(self, config: Optional[HuggingFaceConfig] = None):
        """
        Initialize the HuggingFace client.

        Args:
            config: HuggingFace configuration
        """
        settings = get_settings()

        if config:
            self.config = config
        else:
            self.config = HuggingFaceConfig(
                model=settings.hf_model,
                token=settings.hf_token,
                temperature=settings.ollama_temperature,  # Reuse temperature setting
            )

        self._client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the HuggingFace InferenceClient."""
        try:
            from huggingface_hub import InferenceClient

            if not self.config.token:
                logger.warning("No HuggingFace token provided. Some models may not be accessible.")

            self._client = InferenceClient(
                model=self.config.model,
                token=self.config.token,
                timeout=self.config.timeout,
            )
        except ImportError:
            raise HuggingFaceError(
                "huggingface_hub package not installed. "
                "Run: pip install huggingface_hub"
            )

    def check_connection(self) -> bool:
        """
        Check if HuggingFace API is accessible.

        Returns:
            True if connected
        """
        try:
            # Try a simple API call to verify connection
            self._client.text_generation(
                "Hello",
                max_new_tokens=1,
            )
            return True
        except Exception as e:
            error_str = str(e).lower()
            if "401" in error_str or "unauthorized" in error_str:
                logger.error("HuggingFace authentication failed. Check your HF_TOKEN.")
            elif "rate limit" in error_str or "429" in error_str:
                logger.warning("HuggingFace rate limited, but connection works.")
                return True  # Rate limit means we're connected
            else:
                logger.error(f"Cannot connect to HuggingFace: {e}")
            return False

    def check_model_available(self) -> bool:
        """
        Check if the configured model is available.

        Returns:
            True if model is available
        """
        try:
            # Try to get model info
            from huggingface_hub import model_info

            info = model_info(self.config.model, token=self.config.token)
            # Check if model supports text-generation
            if info.pipeline_tag in ["text-generation", "text2text-generation"]:
                return True

            logger.warning(
                f"Model '{self.config.model}' is not a text generation model. "
                f"Pipeline: {info.pipeline_tag}"
            )
            return False
        except Exception as e:
            error_str = str(e).lower()
            if "401" in error_str or "unauthorized" in error_str:
                logger.error(
                    f"Cannot access model '{self.config.model}'. "
                    "Check your HF_TOKEN or model permissions."
                )
            elif "404" in error_str or "not found" in error_str:
                logger.error(f"Model '{self.config.model}' not found on HuggingFace.")
            else:
                logger.error(f"Error checking model: {e}")
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
            # Build messages for chat completion
            messages = []

            if system:
                messages.append({"role": "system", "content": system})

            messages.append({"role": "user", "content": prompt})

            # Try chat completion first (for instruct models)
            try:
                response = self._client.chat_completion(
                    messages=messages,
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                )
                return response.choices[0].message.content
            except Exception:
                # Fall back to text generation for non-chat models
                full_prompt = prompt
                if system:
                    full_prompt = f"{system}\n\n{prompt}"

                response = self._client.text_generation(
                    full_prompt,
                    max_new_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                    return_full_text=False,
                )
                return response

        except Exception as e:
            error_str = str(e).lower()
            if "rate limit" in error_str or "429" in error_str:
                raise HuggingFaceError(
                    "HuggingFace rate limit exceeded. Please wait a moment and try again, "
                    "or consider using Ollama (local) provider."
                )
            elif "401" in error_str or "unauthorized" in error_str:
                raise HuggingFaceError(
                    "HuggingFace authentication failed. "
                    "Please check your HF_TOKEN in .env file. "
                    "Get a token at: https://huggingface.co/settings/tokens"
                )
            else:
                logger.error(f"Error generating text: {e}")
                raise HuggingFaceError(f"Generation failed: {e}")

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

            # Try streaming chat completion
            try:
                stream = self._client.chat_completion(
                    messages=messages,
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                    stream=True,
                )

                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            except Exception:
                # Fall back to non-streaming
                yield self.generate(prompt, system)

        except Exception as e:
            logger.error(f"Error in stream generation: {e}")
            raise HuggingFaceError(f"Stream generation failed: {e}")

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
        List recommended models for text generation.

        Returns:
            List of recommended model names
        """
        # Return a curated list of good models for meeting summarization
        return [
            "meta-llama/Llama-3.1-8B-Instruct",
            "meta-llama/Llama-3.1-70B-Instruct",
            "mistralai/Mistral-7B-Instruct-v0.3",
            "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "Qwen/Qwen2.5-7B-Instruct",
        ]

    @property
    def provider_name(self) -> str:
        """Get the provider name."""
        return "HuggingFace"
