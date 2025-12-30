"""LLM integration module with Ollama."""

from .ollama_client import OllamaClient
from .summarizer import MeetingSummarizer

__all__ = ["OllamaClient", "MeetingSummarizer"]
