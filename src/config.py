"""Configuration management using Pydantic Settings."""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="ZNT_",
        case_sensitive=False,
    )

    # Audio Configuration
    audio_device: str = Field(
        default="BlackHole 2ch",
        description="Name of the audio input device to capture from",
    )
    sample_rate: int = Field(
        default=16000,
        description="Audio sample rate in Hz (16000 is optimal for Whisper)",
    )
    channels: int = Field(
        default=1,
        description="Number of audio channels (1 for mono)",
    )
    chunk_duration: float = Field(
        default=30.0,
        description="Duration of audio chunks in seconds",
    )

    # Whisper Configuration
    whisper_model: str = Field(
        default="base",
        description="Whisper model size: tiny, base, small, medium, large",
    )
    whisper_language: Optional[str] = Field(
        default=None,
        description="Language code for transcription (e.g., 'en', 'ta'). Empty for auto-detect.",
    )
    enable_diarization: bool = Field(
        default=True,
        description="Enable speaker diarization",
    )

    # Ollama Configuration
    ollama_model: str = Field(
        default="llama3.2",
        description="Ollama model to use for summarization",
    )
    ollama_host: str = Field(
        default="http://localhost:11434",
        description="Ollama server URL",
    )
    ollama_temperature: float = Field(
        default=0.3,
        description="Temperature for LLM generation (lower = more deterministic)",
    )

    # Output Configuration
    output_dir: Path = Field(
        default=Path("./output"),
        description="Directory for generated meeting notes",
    )
    recordings_dir: Path = Field(
        default=Path("./recordings"),
        description="Directory for audio recordings",
    )

    # Hugging Face Token (for speaker diarization models)
    hf_token: Optional[str] = Field(
        default=None,
        alias="HF_TOKEN",
        description="Hugging Face token for pyannote models",
    )

    def ensure_directories(self) -> None:
        """Create output directories if they don't exist."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.recordings_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Force reload settings from environment."""
    global _settings
    _settings = Settings()
    return _settings
