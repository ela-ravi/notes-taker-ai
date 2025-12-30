"""File utility functions."""

from datetime import datetime
from pathlib import Path
from typing import Optional


def ensure_directory(path: Path) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path

    Returns:
        The directory path
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_output_path(
    output_dir: Path,
    title: str,
    extension: str = ".md",
    timestamp: Optional[datetime] = None,
) -> Path:
    """
    Generate an output file path with timestamp.

    Args:
        output_dir: Directory for output files
        title: Meeting title (will be sanitized)
        extension: File extension (default: .md)
        timestamp: Optional timestamp (default: now)

    Returns:
        Path to the output file
    """
    if timestamp is None:
        timestamp = datetime.now()

    # Sanitize title for filename
    safe_title = sanitize_filename(title)

    # Format timestamp
    date_str = timestamp.strftime("%Y-%m-%d_%H-%M")

    # Create filename
    filename = f"{date_str}_{safe_title}{extension}"

    return output_dir / filename


def sanitize_filename(filename: str, max_length: int = 50) -> str:
    """
    Sanitize a string for use as a filename.

    Args:
        filename: Original filename
        max_length: Maximum length for the filename

    Returns:
        Sanitized filename
    """
    # Replace problematic characters
    replacements = {
        "/": "-",
        "\\": "-",
        ":": "-",
        "*": "",
        "?": "",
        '"': "",
        "<": "",
        ">": "",
        "|": "",
        " ": "_",
    }

    result = filename
    for old, new in replacements.items():
        result = result.replace(old, new)

    # Remove leading/trailing underscores and dots
    result = result.strip("_.")

    # Truncate if too long
    if len(result) > max_length:
        result = result[:max_length].rstrip("_")

    return result or "meeting"


def get_recording_path(
    recordings_dir: Path,
    title: str,
    timestamp: Optional[datetime] = None,
) -> Path:
    """
    Generate a recording file path.

    Args:
        recordings_dir: Directory for recordings
        title: Meeting title
        timestamp: Optional timestamp (default: now)

    Returns:
        Path to the recording file
    """
    return get_output_path(recordings_dir, title, extension=".wav", timestamp=timestamp)
