"""Cloud LLM client that uses Supabase Edge Function as proxy."""

import json
import os
from typing import Any, Generator, Optional

import httpx

from .base import LLMClient


class CloudLLMClientError(Exception):
    """Exception raised by CloudLLMClient."""

    def __init__(self, message: str, code: Optional[str] = None, status_code: Optional[int] = None):
        super().__init__(message)
        self.code = code
        self.status_code = status_code


class LimitReachedError(CloudLLMClientError):
    """Exception raised when free tier limit is reached."""

    def __init__(self, message: str, current: int, limit: int, tier: str):
        super().__init__(message, code="LIMIT_REACHED", status_code=402)
        self.current = current
        self.limit = limit
        self.tier = tier


class CloudLLMClient(LLMClient):
    """LLM client that uses Supabase Edge Function for authenticated API calls."""

    # Available models through the cloud proxy (Groq models)
    MODELS = [
        "llama-3.1-8b-instant",
        "llama-3.1-70b-versatile",
        "llama-3.3-70b-versatile",
        "mixtral-8x7b-32768",
        "gemma2-9b-it",
    ]

    def __init__(
        self,
        access_token: str,
        supabase_url: Optional[str] = None,
        model: str = "llama-3.1-8b-instant",
        temperature: float = 0.3,
        token_refresh_callback: Optional[callable] = None,
    ):
        """Initialize the Cloud LLM client.

        Args:
            access_token: Supabase access token for authentication
            supabase_url: Supabase project URL (defaults to SUPABASE_URL env var)
            model: Model to use for generation
            temperature: Temperature for generation
            token_refresh_callback: Optional callback to get a fresh token if auth fails
        """
        self._access_token = access_token
        self._supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self._token_refresh_callback = token_refresh_callback

        if not self._supabase_url:
            raise ValueError("SUPABASE_URL environment variable is required")

        self._model = model
        self._temperature = temperature
        self._client = httpx.Client(timeout=120)

        # Track usage info from last request
        self._last_usage_info: Optional[dict] = None

    @property
    def provider_name(self) -> str:
        """Get the provider name."""
        return "cloud"

    @property
    def last_usage_info(self) -> Optional[dict]:
        """Get usage info from the last request."""
        return self._last_usage_info

    def _get_endpoint(self) -> str:
        """Get the summarize edge function endpoint."""
        return f"{self._supabase_url}/functions/v1/summarize"

    def _get_headers(self) -> dict:
        """Get request headers with auth."""
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

    def check_connection(self) -> bool:
        """Check if the cloud service is accessible."""
        try:
            # Simple health check by making a minimal request
            response = self._client.post(
                self._get_endpoint(),
                headers=self._get_headers(),
                json={
                    "model": self._model,
                    "messages": [{"role": "user", "content": "hi"}],
                    "max_tokens": 5,
                },
                timeout=10,
            )
            # 401 means auth issue but service is up
            # 402 means limit reached but service is up
            # 200 means everything works
            return response.status_code in [200, 401, 402]
        except Exception:
            return False

    def check_model_available(self) -> bool:
        """Check if the configured model is available."""
        return self._model in self.MODELS

    def list_models(self) -> list[str]:
        """List available models."""
        return self.MODELS.copy()

    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        """Generate a response from the LLM.

        Args:
            prompt: User prompt
            system: Optional system prompt

        Returns:
            Generated response text

        Raises:
            LimitReachedError: If free tier limit is reached
            CloudLLMClientError: For other API errors
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self._client.post(
            self._get_endpoint(),
            headers=self._get_headers(),
            json={
                "model": self._model,
                "messages": messages,
                "temperature": self._temperature,
            },
        )

        # Try to refresh token on auth error
        if response.status_code == 401 and self._token_refresh_callback:
            new_token = self._token_refresh_callback()
            if new_token:
                self._access_token = new_token
                # Retry with new token
                response = self._client.post(
                    self._get_endpoint(),
                    headers=self._get_headers(),
                    json={
                        "model": self._model,
                        "messages": messages,
                        "temperature": self._temperature,
                    },
                )

        return self._handle_response(response)

    def generate_json(self, prompt: str, system: Optional[str] = None) -> Any:
        """Generate a JSON response from the LLM.

        Args:
            prompt: User prompt requesting JSON output
            system: Optional system prompt

        Returns:
            Parsed JSON object

        Raises:
            LimitReachedError: If free tier limit is reached
            CloudLLMClientError: For other API errors
        """
        # Add JSON instruction to system prompt
        json_system = (system or "") + "\n\nRespond with valid JSON only."

        messages = []
        messages.append({"role": "system", "content": json_system.strip()})
        messages.append({"role": "user", "content": prompt})

        response = self._client.post(
            self._get_endpoint(),
            headers=self._get_headers(),
            json={
                "model": self._model,
                "messages": messages,
                "temperature": self._temperature,
                "response_format": {"type": "json_object"},
            },
        )

        # Try to refresh token on auth error
        if response.status_code == 401 and self._token_refresh_callback:
            new_token = self._token_refresh_callback()
            if new_token:
                self._access_token = new_token
                # Retry with new token
                response = self._client.post(
                    self._get_endpoint(),
                    headers=self._get_headers(),
                    json={
                        "model": self._model,
                        "messages": messages,
                        "temperature": self._temperature,
                        "response_format": {"type": "json_object"},
                    },
                )

        text = self._handle_response(response)

        # Parse JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise CloudLLMClientError(f"Failed to parse JSON response: {e}")

    def generate_stream(
        self,
        prompt: str,
        system: Optional[str] = None
    ) -> Generator[str, None, None]:
        """Generate a streaming response from the LLM.

        Note: Streaming is not yet implemented for cloud client.
        Falls back to non-streaming generation.

        Args:
            prompt: User prompt
            system: Optional system prompt

        Yields:
            Response text chunks
        """
        # For now, just yield the full response
        # TODO: Implement SSE streaming when edge function supports it
        response = self.generate(prompt, system)
        yield response

    def _handle_response(self, response: httpx.Response) -> str:
        """Handle API response.

        Args:
            response: HTTP response

        Returns:
            Generated text content

        Raises:
            LimitReachedError: If free tier limit is reached
            CloudLLMClientError: For other API errors
        """
        if response.status_code == 401:
            raise CloudLLMClientError(
                "Authentication failed. Please sign in again.",
                code="AUTH_FAILED",
                status_code=401,
            )

        if response.status_code == 402:
            data = response.json()
            raise LimitReachedError(
                message=data.get("message", "Free tier limit reached"),
                current=data.get("current", 0),
                limit=data.get("limit", 3),
                tier=data.get("tier", "free"),
            )

        if response.status_code != 200:
            try:
                error_data = response.json()
                error_msg = error_data.get("error", response.text)
            except Exception:
                error_msg = response.text
            raise CloudLLMClientError(
                f"API error: {error_msg}",
                status_code=response.status_code,
            )

        data = response.json()

        # Store usage info
        self._last_usage_info = data.get("_usage_info")

        # Extract content from OpenAI-style response
        try:
            content = data["choices"][0]["message"]["content"]
            return content
        except (KeyError, IndexError) as e:
            raise CloudLLMClientError(f"Unexpected response format: {e}")

    def update_token(self, access_token: str) -> None:
        """Update the access token.

        Args:
            access_token: New access token
        """
        self._access_token = access_token

    def set_model(self, model: str) -> None:
        """Set the model to use.

        Args:
            model: Model name
        """
        if model not in self.MODELS:
            raise ValueError(f"Unknown model: {model}. Available: {self.MODELS}")
        self._model = model

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
