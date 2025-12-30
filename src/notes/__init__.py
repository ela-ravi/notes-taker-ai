"""Meeting notes generation module."""

from .generator import NotesGenerator
from .models import MeetingNotes, ActionItem, Decision, Speaker, TranscriptSegment

__all__ = ["NotesGenerator", "MeetingNotes", "ActionItem", "Decision", "Speaker", "TranscriptSegment"]
