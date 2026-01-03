"""Factory for creating LLM clients based on configuration."""

from typing import Optional

from ..config import get_settings
from ..utils.logging_config import get_logger
from .base import LLMClient

logger = get_logger("llm.factory")

# Global access token for cloud provider (set by UI before recording)
_cloud_access_token: Optional[str] = None


def set_cloud_access_token(token: Optional[str]) -> None:
    """Set the access token for cloud provider.

    This should be called by the UI before starting recording when using cloud provider.

    Args:
        token: Access token from auth manager, or None to clear
    """
    global _cloud_access_token
    _cloud_access_token = token


def get_cloud_access_token() -> Optional[str]:
    """Get the currently set cloud access token."""
    return _cloud_access_token


def create_llm_client(
    provider: Optional[str] = None,
    access_token: Optional[str] = None,
) -> LLMClient:
    """
    Create an LLM client based on the configured provider.

    Args:
        provider: Override provider ("ollama", "huggingface", "groq", or "cloud").
                  If None, uses the configured default.
        access_token: Access token for cloud provider authentication.
                      Required when provider is "cloud".

    Returns:
        LLMClient instance

    Raises:
        ValueError: If provider is unknown or cloud provider lacks token
    """
    settings = get_settings()
    selected_provider = provider or settings.llm_provider

    if selected_provider == "cloud":
        from .cloud_client import CloudLLMClient

        # Use provided token or global token
        token = access_token or _cloud_access_token
        if not token:
            raise ValueError(
                "Cloud provider requires an access token. "
                "Please sign in first."
            )

        logger.info("Creating Cloud client (Supabase Edge Function proxy)")
        return CloudLLMClient(
            access_token=token,
            model=settings.groq_model,  # Cloud uses Groq on backend
        )

    elif selected_provider == "groq":
        from .groq_client import GroqClient

        logger.info(f"Creating Groq client with model: {settings.groq_model}")
        return GroqClient()

    elif selected_provider == "huggingface":
        from .huggingface_client import HuggingFaceClient

        logger.info(f"Creating HuggingFace client with model: {settings.hf_model}")
        return HuggingFaceClient()

    elif selected_provider == "ollama":
        from .ollama_client import OllamaClient

        logger.info(f"Creating Ollama client with model: {settings.ollama_model}")
        return OllamaClient()

    else:
        raise ValueError(
            f"Unknown LLM provider: {selected_provider}. "
            f"Valid options are: 'ollama', 'huggingface', 'groq', 'cloud'"
        )


def get_available_providers(access_token: Optional[str] = None) -> list[dict]:
    """
    Get list of available LLM providers with their status.

    Args:
        access_token: Optional access token for checking cloud provider

    Returns:
        List of provider info dicts with keys: name, id, available, reason
    """
    import os

    settings = get_settings()
    providers = []

    # Check Cloud (SaaS mode - requires login)
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")

    if supabase_url and supabase_key:
        if access_token:
            providers.append({
                "name": "Cloud (Subscription)",
                "id": "cloud",
                "available": True,
                "reason": None,
                "model": settings.groq_model,
            })
        else:
            providers.append({
                "name": "Cloud (Subscription)",
                "id": "cloud",
                "available": False,
                "reason": "Sign in required",
                "model": settings.groq_model,
            })
    else:
        providers.append({
            "name": "Cloud (Subscription)",
            "id": "cloud",
            "available": False,
            "reason": "Supabase not configured",
            "model": settings.groq_model,
        })

    # Check Groq (recommended for SaaS - fast & cheap)
    if settings.groq_api_key:
        try:
            from .groq_client import GroqClient

            client = GroqClient()
            groq_available = client.check_connection()
            providers.append({
                "name": "Groq (Cloud - Fast)",
                "id": "groq",
                "available": groq_available,
                "reason": None if groq_available else "Groq connection failed",
                "model": settings.groq_model,
            })
        except Exception as e:
            providers.append({
                "name": "Groq (Cloud - Fast)",
                "id": "groq",
                "available": False,
                "reason": str(e),
                "model": settings.groq_model,
            })
    else:
        providers.append({
            "name": "Groq (Cloud - Fast)",
            "id": "groq",
            "available": False,
            "reason": "GROQ_API_KEY not configured",
            "model": settings.groq_model,
        })

    # Check Ollama
    try:
        from .ollama_client import OllamaClient

        client = OllamaClient()
        ollama_available = client.check_connection()
        providers.append({
            "name": "Ollama (Local)",
            "id": "ollama",
            "available": ollama_available,
            "reason": None if ollama_available else "Ollama server not running",
            "model": settings.ollama_model,
        })
    except Exception as e:
        providers.append({
            "name": "Ollama (Local)",
            "id": "ollama",
            "available": False,
            "reason": str(e),
            "model": settings.ollama_model,
        })

    # Check HuggingFace
    if settings.hf_token:
        try:
            from .huggingface_client import HuggingFaceClient

            client = HuggingFaceClient()
            hf_available = client.check_connection()
            providers.append({
                "name": "HuggingFace (Cloud)",
                "id": "huggingface",
                "available": hf_available,
                "reason": None if hf_available else "HuggingFace connection failed",
                "model": settings.hf_model,
            })
        except Exception as e:
            providers.append({
                "name": "HuggingFace (Cloud)",
                "id": "huggingface",
                "available": False,
                "reason": str(e),
                "model": settings.hf_model,
            })
    else:
        providers.append({
            "name": "HuggingFace (Cloud)",
            "id": "huggingface",
            "available": False,
            "reason": "HF_TOKEN not configured",
            "model": settings.hf_model,
        })

    return providers
