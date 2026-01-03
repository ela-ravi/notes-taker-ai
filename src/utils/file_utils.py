"""File utility functions."""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

# Meeting type folders
MEETING_FOLDERS = {
    "atve": "atve-meeting-notes",
    "tnt": "tnt-meeting-notes",
    "general": "general",
}


def get_notes_base_path() -> Path:
    """Get the base path for meeting notes from environment variable.

    Checks both ZNT_NOTES_BASE and ZNT_OUTPUT_DIR for backwards compatibility.
    Always returns an absolute path in a writable location.
    """
    # Check both env vars for compatibility
    base = os.environ.get("ZNT_NOTES_BASE") or os.environ.get("ZNT_OUTPUT_DIR")
    if base:
        path = Path(base).expanduser()  # Expand ~ to home directory
        # Ensure absolute path - relative paths cause issues in bundled apps
        if path.is_absolute():
            return path
    # Fallback to default in user's home directory (always writable)
    return Path.home() / "Documents" / "ZoomNotes" / "notes"


def get_meeting_folder(title: str) -> str:
    """
    Determine the appropriate folder based on meeting title.

    Args:
        title: Meeting title

    Returns:
        Folder name (atve-meeting-notes, tnt-meeting-notes, or general)
    """
    title_lower = title.lower()

    # Check for ATVE keywords
    if any(keyword in title_lower for keyword in ["atve", "at&ve", "at & ve"]):
        return MEETING_FOLDERS["atve"]

    # Check for TNT keywords
    if any(keyword in title_lower for keyword in ["tnt", "sports"]):
        return MEETING_FOLDERS["tnt"]

    # Default to general
    return MEETING_FOLDERS["general"]


def get_smart_output_dir(title: str) -> Path:
    """
    Get the output directory based on meeting title.

    Args:
        title: Meeting title

    Returns:
        Path to the appropriate output directory
    """
    folder = get_meeting_folder(title)
    return get_notes_base_path() / folder


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
