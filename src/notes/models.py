"""Data models for meeting notes."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Speaker:
    """Represents a meeting participant/speaker."""

    id: int
    label: str = ""
    name: Optional[str] = None
    speaking_time: float = 0.0  # seconds

    def __post_init__(self):
        if not self.label:
            self.label = f"Speaker {self.id + 1}"

    @property
    def display_name(self) -> str:
        """Get display name (name if set, otherwise label)."""
        return self.name or self.label


@dataclass
class TranscriptSegment:
    """A segment of the transcript with speaker and timing info."""

    text: str
    start_time: float
    end_time: float
    speaker_id: Optional[int] = None

    @property
    def timestamp(self) -> str:
        """Get formatted timestamp [MM:SS]."""
        minutes = int(self.start_time // 60)
        seconds = int(self.start_time % 60)
        return f"[{minutes:02d}:{seconds:02d}]"

    @property
    def speaker_label(self) -> str:
        """Get speaker label."""
        if self.speaker_id is not None:
            return f"Speaker {self.speaker_id + 1}"
        return "Unknown"

    @property
    def duration(self) -> float:
        """Duration of the segment in seconds."""
        return self.end_time - self.start_time


@dataclass
class ActionItem:
    """An action item from the meeting."""

    description: str
    assignee: Optional[str] = None
    due_date: Optional[str] = None
    priority: str = "medium"
    completed: bool = False

    def to_markdown_row(self) -> str:
        """Convert to markdown table row."""
        assignee = self.assignee or "-"
        due = self.due_date or "-"
        return f"| {self.description} | {assignee} | {due} |"


@dataclass
class Decision:
    """A decision made during the meeting."""

    description: str
    rationale: Optional[str] = None
    stakeholders: list[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        """Convert to markdown format."""
        parts = [f"- **{self.description}**"]
        if self.rationale:
            parts.append(f"  - Rationale: {self.rationale}")
        if self.stakeholders:
            parts.append(f"  - Stakeholders: {', '.join(self.stakeholders)}")
        return "\n".join(parts)


@dataclass
class MeetingNotes:
    """Complete meeting notes."""

    title: str
    date: datetime
    duration_minutes: float = 0.0

    # Content
    summary: str = ""
    key_points: list[str] = field(default_factory=list)
    action_items: list[ActionItem] = field(default_factory=list)
    decisions: list[Decision] = field(default_factory=list)
    transcript_segments: list[TranscriptSegment] = field(default_factory=list)

    # Metadata
    speakers: list[Speaker] = field(default_factory=list)
    meeting_type: str = "other"
    attendees: list[str] = field(default_factory=list)

    @property
    def full_transcript(self) -> str:
        """Get the full transcript text."""
        return " ".join(seg.text for seg in self.transcript_segments)

    @property
    def formatted_transcript(self) -> str:
        """Get transcript with timestamps and speaker labels."""
        lines = []
        for seg in self.transcript_segments:
            lines.append(f"{seg.timestamp} **{seg.speaker_label}:** {seg.text}")
        return "\n".join(lines)

    @property
    def speaker_count(self) -> int:
        """Number of unique speakers."""
        return len(self.speakers)

    @property
    def formatted_date(self) -> str:
        """Get formatted date string."""
        return self.date.strftime("%B %d, %Y at %H:%M")

    @property
    def formatted_duration(self) -> str:
        """Get formatted duration string."""
        hours = int(self.duration_minutes // 60)
        minutes = int(self.duration_minutes % 60)
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes} minutes"


@dataclass
class MeetingSession:
    """Represents an active or completed meeting recording session."""

    id: str
    title: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "recording"  # recording, processing, completed, error
    audio_path: Optional[str] = None
    notes_path: Optional[str] = None
    notes: Optional[MeetingNotes] = None
    error: Optional[str] = None

    @property
    def duration_seconds(self) -> float:
        """Get session duration in seconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.now() - self.start_time).total_seconds()

    @property
    def duration_minutes(self) -> float:
        """Get session duration in minutes."""
        return self.duration_seconds / 60

    @property
    def is_active(self) -> bool:
        """Check if session is still recording."""
        return self.status == "recording"
