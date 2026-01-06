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
        extra="ignore",  # Ignore extra env vars like ZNT_PROJECT_DIR used by scripts
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

    # LLM Provider Configuration
    llm_provider: str = Field(
        default="groq",
        description="LLM provider: 'groq', 'ollama', or 'huggingface'",
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

    # HuggingFace Configuration
    hf_model: str = Field(
        default="meta-llama/Llama-3.1-8B-Instruct",
        description="HuggingFace model for summarization (when using huggingface provider)",
    )

    # Groq Configuration (Fast & Low-cost Cloud)
    groq_api_key: Optional[str] = Field(
        default=None,
        alias="GROQ_API_KEY",
        description="Groq API key for cloud LLM (get free key at console.groq.com)",
    )
    groq_model: str = Field(
        default="llama-3.1-8b-instant",
        description="Groq model for summarization (when using groq provider)",
    )

    # Supabase Configuration (for Cloud/SaaS mode)
    supabase_url: Optional[str] = Field(
        default=None,
        alias="SUPABASE_URL",
        description="Supabase project URL",
    )
    supabase_anon_key: Optional[str] = Field(
        default=None,
        alias="SUPABASE_ANON_KEY",
        description="Supabase anonymous key",
    )
    dodo_product_id: Optional[str] = Field(
        default=None,
        alias="DODO_PRODUCT_ID",
        description="Dodo Payments product ID for subscription",
    )

    # Provider Restriction (for SaaS/distributed builds)
    cloud_only: bool = Field(
        default=False,
        description="When true, only Cloud (Subscription) provider is shown to users",
    )

    # Output Configuration
    output_dir: Path = Field(
        default=Path.home() / "Documents" / "ZoomNotes" / "notes",
        alias="ZNT_NOTES_BASE",
        description="Directory for generated meeting notes",
    )
    recordings_dir: Path = Field(
        default=Path.home() / "Documents" / "ZoomNotes" / "recordings",
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
        self._resolve_paths()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.recordings_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_paths(self) -> None:
        """Convert relative paths to absolute paths in user's home directory."""
        # Expand ~ in paths
        self.output_dir = self.output_dir.expanduser()
        self.recordings_dir = self.recordings_dir.expanduser()
        # Fall back to defaults if still relative (e.g., ./output)
        if not self.output_dir.is_absolute():
            self.output_dir = Path.home() / "Documents" / "ZoomNotes" / "notes"
        if not self.recordings_dir.is_absolute():
            self.recordings_dir = Path.home() / "Documents" / "ZoomNotes" / "recordings"


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


def set_output_directory(output_dir: Path) -> None:
    """Set custom output directory for meeting notes.
    
    Args:
        output_dir: Path to the output directory
    """
    settings = get_settings()
    settings.output_dir = Path(output_dir).expanduser().resolve()
    settings.ensure_directories()


def set_recordings_directory(recordings_dir: Path) -> None:
    """Set custom recordings directory for audio files.
    
    Args:
        recordings_dir: Path to the recordings directory
    """
    settings = get_settings()
    settings.recordings_dir = Path(recordings_dir).expanduser().resolve()
    settings.ensure_directories()


def set_base_directory(base_dir: Path) -> None:
    """Set base directory for both notes and recordings.
    
    This will set:
    - output_dir to {base_dir}/notes
    - recordings_dir to {base_dir}/recordings
    
    Args:
        base_dir: Base directory path
    """
    settings = get_settings()
    base_path = Path(base_dir).expanduser().resolve()
    settings.output_dir = base_path / "notes"
    settings.recordings_dir = base_path / "recordings"
    settings.ensure_directories()
