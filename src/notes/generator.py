"""Meeting notes generator - orchestrates the full pipeline."""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional
from uuid import uuid4

from ..config import get_settings
from ..llm.ollama_client import OllamaClient
from ..llm.summarizer import MeetingSummarizer
from ..transcription.livekit_engine import LiveKitEngine, TranscriptionResult
from ..utils.file_utils import get_output_path, get_recording_path, get_smart_output_dir
from ..utils.logging_config import get_logger
from .models import (
    ActionItem,
    Decision,
    MeetingNotes,
    MeetingSession,
    Speaker,
    TranscriptSegment,
)
from .templates import render_meeting_notes, render_meeting_notes_html

logger = get_logger("notes.generator")


class NotesGenerator:
    """
    Orchestrates the full meeting notes generation pipeline.

    This class coordinates:
    1. Audio transcription (via LiveKitEngine)
    2. AI summarization (via MeetingSummarizer)
    3. Notes formatting and output
    """

    def __init__(
        self,
        on_progress: Optional[Callable[[str, float], None]] = None,
    ):
        """
        Initialize the notes generator.

        Args:
            on_progress: Callback for progress updates (message, percentage)
        """
        self.settings = get_settings()
        self.on_progress = on_progress

        self._transcription_engine: Optional[LiveKitEngine] = None
        self._summarizer: Optional[MeetingSummarizer] = None

    def _report_progress(self, message: str, percentage: float) -> None:
        """Report progress to callback if set."""
        logger.info(f"[{percentage:.0f}%] {message}")
        if self.on_progress:
            self.on_progress(message, percentage)

    def _get_transcription_engine(self) -> LiveKitEngine:
        """Get or create transcription engine."""
        if self._transcription_engine is None:
            self._transcription_engine = LiveKitEngine(
                model=self.settings.whisper_model,
                language=self.settings.whisper_language,
                enable_diarization=self.settings.enable_diarization,
            )
        return self._transcription_engine

    def _get_summarizer(self) -> MeetingSummarizer:
        """Get or create summarizer."""
        if self._summarizer is None:
            self._summarizer = MeetingSummarizer()
        return self._summarizer

    async def generate_from_audio_file(
        self,
        audio_path: Path,
        title: str = "Meeting Notes",
        output_path: Optional[Path] = None,
    ) -> MeetingNotes:
        """
        Generate meeting notes from an audio file.

        Args:
            audio_path: Path to the audio file
            title: Meeting title
            output_path: Optional output path for notes

        Returns:
            MeetingNotes object
        """
        self._report_progress("Loading audio file...", 0)

        # Validate file exists
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Get file info for duration estimate
        import wave
        try:
            with wave.open(str(audio_path), "rb") as wf:
                duration_seconds = wf.getnframes() / wf.getframerate()
        except Exception:
            duration_seconds = 0

        self._report_progress("Transcribing audio...", 10)

        # Transcribe
        engine = self._get_transcription_engine()
        transcription = await engine.transcribe_file(audio_path)

        self._report_progress("Analyzing transcript...", 50)

        # Generate notes from transcription
        notes = await self._generate_notes_from_transcription(
            transcription=transcription,
            title=title,
            duration_minutes=duration_seconds / 60,
        )

        self._report_progress("Formatting notes...", 90)

        # Save if output path provided
        if output_path:
            self.save_notes(notes, output_path)

        self._report_progress("Complete!", 100)
        return notes

    async def generate_from_transcript(
        self,
        transcript: str,
        title: str = "Meeting Notes",
        duration_minutes: float = 0,
        output_path: Optional[Path] = None,
    ) -> MeetingNotes:
        """
        Generate meeting notes from a transcript string.

        Args:
            transcript: The meeting transcript text
            title: Meeting title
            duration_minutes: Meeting duration
            output_path: Optional output path for notes

        Returns:
            MeetingNotes object
        """
        self._report_progress("Analyzing transcript...", 20)

        # Create a simple TranscriptionResult from text
        transcription = TranscriptionResult(
            full_text=transcript,
            duration=duration_minutes * 60,
        )

        notes = await self._generate_notes_from_transcription(
            transcription=transcription,
            title=title,
            duration_minutes=duration_minutes,
        )

        if output_path:
            self.save_notes(notes, output_path)

        self._report_progress("Complete!", 100)
        return notes

    async def _generate_notes_from_transcription(
        self,
        transcription: TranscriptionResult,
        title: str,
        duration_minutes: float,
        custom_context: Optional[str] = None,
    ) -> MeetingNotes:
        """Generate notes from a transcription result.

        Args:
            transcription: The transcription result
            title: Meeting title
            duration_minutes: Meeting duration
            custom_context: Optional user-provided context/instructions
        """
        # Get summarizer
        summarizer = self._get_summarizer()

        self._report_progress("Generating summary...", 55)

        # Get the transcript text
        if transcription.full_text:
            transcript_text = transcription.full_text
        elif transcription.segments:
            transcript_text = " ".join(s.text for s in transcription.segments)
        else:
            transcript_text = ""

        # Generate summary using LLM
        summary_result = summarizer.summarize(transcript_text, custom_context=custom_context)

        self._report_progress("Extracting insights...", 75)

        # Convert transcription segments to our model
        segments = []
        for seg in transcription.segments:
            segments.append(
                TranscriptSegment(
                    text=seg.text,
                    start_time=seg.start_time,
                    end_time=seg.end_time,
                    speaker_id=seg.speaker_id,
                )
            )

        # Build speakers list
        speaker_ids = set(s.speaker_id for s in segments if s.speaker_id is not None)
        speakers = [Speaker(id=sid) for sid in sorted(speaker_ids)]

        # Convert action items
        action_items = []
        for item in summary_result.action_items:
            action_items.append(
                ActionItem(
                    description=item.task,
                    assignee=item.assignee,
                    due_date=item.deadline,
                )
            )

        # Convert decisions
        decisions = []
        for dec in summary_result.decisions:
            decisions.append(
                Decision(
                    description=dec.decision,
                    rationale=dec.rationale,
                    stakeholders=dec.stakeholders,
                )
            )

        # Build final notes
        notes = MeetingNotes(
            title=title,
            date=datetime.now(),
            duration_minutes=duration_minutes or (transcription.duration / 60),
            summary=summary_result.summary,
            key_points=summary_result.key_points,
            action_items=action_items,
            decisions=decisions,
            transcript_segments=segments,
            speakers=speakers,
            meeting_type=summary_result.meeting_type,
        )

        return notes

    def save_notes(self, notes: MeetingNotes, path: Path) -> None:
        """
        Save meeting notes to markdown and HTML files.

        Args:
            notes: MeetingNotes object
            path: Output file path (for markdown)
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        # Save markdown
        markdown = render_meeting_notes(notes)
        path.write_text(markdown, encoding="utf-8")
        logger.info(f"Markdown notes saved to: {path}")

        # Save HTML
        html_path = path.with_suffix(".html")
        html_content = render_meeting_notes_html(notes)
        html_path.write_text(html_content, encoding="utf-8")
        logger.info(f"HTML notes saved to: {html_path}")

    def get_default_output_path(self, title: str) -> Path:
        """Get the default output path for a meeting based on title."""
        # Use smart folder selection based on meeting title
        output_dir = get_smart_output_dir(title)
        output_dir.mkdir(parents=True, exist_ok=True)
        return get_output_path(output_dir, title)


class MeetingRecorder:
    """
    High-level class for recording and generating notes from live meetings.

    Combines audio capture, transcription, and notes generation into
    a simple interface.
    """

    def __init__(
        self,
        on_segment: Optional[Callable] = None,
        on_progress: Optional[Callable[[str, float], None]] = None,
    ):
        """
        Initialize the meeting recorder.

        Args:
            on_segment: Callback for real-time transcript segments
            on_progress: Callback for progress updates
        """
        from ..audio.capture import AudioCapture
        from ..transcription.processor import TranscriptionProcessor

        self.settings = get_settings()
        self.on_segment = on_segment
        self.on_progress = on_progress

        self._session: Optional[MeetingSession] = None
        self._capture: Optional[AudioCapture] = None
        self._processor: Optional[TranscriptionProcessor] = None
        self._generator = NotesGenerator(on_progress=on_progress)
        self._custom_context: Optional[str] = None

    async def start(self, title: str = "Meeting", custom_context: Optional[str] = None) -> MeetingSession:
        """
        Start recording a meeting.

        Args:
            title: Meeting title
            custom_context: Optional user-provided context/instructions for notes

        Returns:
            MeetingSession object
        """
        self._custom_context = custom_context
        from ..audio.capture import AudioCapture
        from ..transcription.processor import TranscriptionProcessor
        from ..transcription.livekit_engine import LiveKitEngine

        if self._session and self._session.is_active:
            raise RuntimeError("A recording is already in progress")

        # Create session
        self._session = MeetingSession(
            id=str(uuid4())[:8],
            title=title,
            start_time=datetime.now(),
        )

        # Set up transcription
        engine = LiveKitEngine(
            model=self.settings.whisper_model,
            language=self.settings.whisper_language,
            enable_diarization=self.settings.enable_diarization,
        )

        self._processor = TranscriptionProcessor(
            engine=engine,
            on_segment=self.on_segment,
        )

        # Set up audio capture
        self._capture = AudioCapture(
            on_chunk=self._processor.add_audio_sync,
        )

        # Start components
        await self._processor.start()
        self._capture.start()

        logger.info(f"Recording started: {title}")
        return self._session

    async def stop(self) -> MeetingNotes:
        """
        Stop recording and generate notes.

        Returns:
            Generated MeetingNotes
        """
        if not self._session or not self._session.is_active:
            raise RuntimeError("No recording in progress")

        logger.info("Stopping recording...")
        self._session.status = "processing"
        self._session.end_time = datetime.now()

        # Stop capture and get audio
        audio = self._capture.stop()

        # Stop processor and get transcription
        transcription = await self._processor.stop()

        # Save audio if we have any
        if len(audio) > 0:
            self.settings.ensure_directories()
            audio_path = get_recording_path(
                self.settings.recordings_dir,
                self._session.title,
                self._session.start_time,
            )
            self._capture.save_recording(audio, audio_path)
            self._session.audio_path = str(audio_path)

        # Generate notes
        if self.on_progress:
            self.on_progress("Generating meeting notes...", 50)

        notes = await self._generator._generate_notes_from_transcription(
            transcription=transcription,
            title=self._session.title,
            duration_minutes=self._session.duration_minutes,
            custom_context=self._custom_context,
        )

        # Save notes
        output_path = self._generator.get_default_output_path(self._session.title)
        self._generator.save_notes(notes, output_path)
        self._session.notes_path = str(output_path)
        self._session.notes = notes
        self._session.status = "completed"

        if self.on_progress:
            self.on_progress("Complete!", 100)

        return notes

    @property
    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self._session is not None and self._session.is_active

    @property
    def current_session(self) -> Optional[MeetingSession]:
        """Get the current session."""
        return self._session
