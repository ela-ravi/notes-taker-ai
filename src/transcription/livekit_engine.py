"""Transcription engine using faster-whisper for speech-to-text."""

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

import numpy as np

from ..config import get_settings
from ..utils.logging_config import get_logger

logger = get_logger("transcription.engine")


@dataclass
class TranscriptSegment:
    """Represents a segment of transcribed text."""

    text: str
    start_time: float
    end_time: float
    speaker_id: Optional[int] = None
    confidence: float = 1.0
    is_final: bool = False

    @property
    def speaker_label(self) -> str:
        """Get formatted speaker label."""
        if self.speaker_id is not None:
            return f"Speaker {self.speaker_id + 1}"
        return "Unknown"

    @property
    def timestamp(self) -> str:
        """Get formatted timestamp."""
        minutes = int(self.start_time // 60)
        seconds = int(self.start_time % 60)
        return f"[{minutes:02d}:{seconds:02d}]"


@dataclass
class TranscriptionResult:
    """Complete transcription result."""

    segments: list[TranscriptSegment] = field(default_factory=list)
    full_text: str = ""
    duration: float = 0.0
    speaker_count: int = 0

    def get_formatted_transcript(self) -> str:
        """Get transcript formatted with speaker labels and timestamps."""
        lines = []
        for segment in self.segments:
            lines.append(f"{segment.timestamp} **{segment.speaker_label}:** {segment.text}")
        return "\n".join(lines)

    def get_speakers(self) -> set[int]:
        """Get unique speaker IDs."""
        return {s.speaker_id for s in self.segments if s.speaker_id is not None}


class LiveKitEngine:
    """
    Transcription engine using faster-whisper.

    Provides speech-to-text transcription with optional speaker diarization.
    """

    def __init__(
        self,
        model: str = "base",
        language: str = "en",
        enable_diarization: bool = True,
        on_segment: Optional[Callable[[TranscriptSegment], None]] = None,
    ):
        """
        Initialize the transcription engine.

        Args:
            model: Whisper model size (tiny, base, small, medium, large)
            language: Language code for transcription
            enable_diarization: Enable speaker diarization (simplified)
            on_segment: Callback for each transcribed segment
        """
        settings = get_settings()

        self.model = model or settings.whisper_model
        self.language = language or settings.whisper_language
        self.enable_diarization = enable_diarization
        self.on_segment = on_segment

        self._whisper_model = None
        self._is_initialized = False

    def _initialize_engine(self) -> None:
        """Initialize the whisper model."""
        if self._is_initialized:
            return

        # Use openai-whisper (more compatible)
        self._initialize_openai_whisper()

    def _initialize_openai_whisper(self) -> None:
        """Initialize fallback openai-whisper."""
        try:
            import whisper

            logger.info(f"Loading openai-whisper model: {self.model}")
            self._whisper_model = whisper.load_model(self.model)
            self._use_openai_whisper = True
            self._is_initialized = True
            logger.info("openai-whisper model loaded")

        except ImportError:
            raise RuntimeError(
                "No transcription engine available. Install faster-whisper or openai-whisper"
            )

    async def transcribe_audio(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000,
    ) -> TranscriptionResult:
        """
        Transcribe audio data.

        Args:
            audio: Audio data as numpy array (float32, mono)
            sample_rate: Audio sample rate

        Returns:
            TranscriptionResult with segments and full text
        """
        self._initialize_engine()

        # Ensure audio is float32
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)

        # Resample if necessary
        if sample_rate != 16000:
            from scipy import signal
            num_samples = int(len(audio) * 16000 / sample_rate)
            audio = signal.resample(audio, num_samples)

        # Run transcription in thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, self._transcribe_openai_whisper, audio
        )
        return result

    def _transcribe_faster_whisper(self, audio: np.ndarray) -> TranscriptionResult:
        """Transcribe using faster-whisper."""
        segments_list: list[TranscriptSegment] = []
        full_text_parts = []

        # Transcribe
        segments, info = self._whisper_model.transcribe(
            audio,
            language=self.language,
            beam_size=5,
            word_timestamps=True,
            vad_filter=True,
        )

        # Simple speaker assignment based on pauses
        current_speaker = 0
        last_end_time = 0.0

        for segment in segments:
            # Assign speaker based on pause detection (simple heuristic)
            if self.enable_diarization and segment.start - last_end_time > 1.5:
                # Long pause might indicate speaker change
                current_speaker = (current_speaker + 1) % 2

            transcript_segment = TranscriptSegment(
                text=segment.text.strip(),
                start_time=segment.start,
                end_time=segment.end,
                speaker_id=current_speaker if self.enable_diarization else None,
                is_final=True,
            )

            segments_list.append(transcript_segment)
            full_text_parts.append(segment.text.strip())
            last_end_time = segment.end

            if self.on_segment:
                self.on_segment(transcript_segment)

        # Count unique speakers
        speaker_ids = {s.speaker_id for s in segments_list if s.speaker_id is not None}

        return TranscriptionResult(
            segments=segments_list,
            full_text=" ".join(full_text_parts),
            duration=info.duration if hasattr(info, 'duration') else len(audio) / 16000,
            speaker_count=len(speaker_ids),
        )

    def _transcribe_openai_whisper(self, audio: np.ndarray) -> TranscriptionResult:
        """Transcribe using openai-whisper."""
        # If language is empty/None, let Whisper auto-detect
        transcribe_kwargs = {
            "word_timestamps": True,
        }
        if self.language:
            transcribe_kwargs["language"] = self.language

        result = self._whisper_model.transcribe(audio, **transcribe_kwargs)

        segments_list: list[TranscriptSegment] = []
        current_speaker = 0
        last_end_time = 0.0

        for seg in result.get("segments", []):
            # Simple speaker assignment
            if self.enable_diarization and seg["start"] - last_end_time > 1.5:
                current_speaker = (current_speaker + 1) % 2

            transcript_segment = TranscriptSegment(
                text=seg["text"].strip(),
                start_time=seg["start"],
                end_time=seg["end"],
                speaker_id=current_speaker if self.enable_diarization else None,
                is_final=True,
            )

            segments_list.append(transcript_segment)
            last_end_time = seg["end"]

            if self.on_segment:
                self.on_segment(transcript_segment)

        speaker_ids = {s.speaker_id for s in segments_list if s.speaker_id is not None}

        return TranscriptionResult(
            segments=segments_list,
            full_text=result.get("text", "").strip(),
            duration=len(audio) / 16000,
            speaker_count=len(speaker_ids),
        )

    async def transcribe_file(self, file_path: Path) -> TranscriptionResult:
        """
        Transcribe an audio file.

        Args:
            file_path: Path to the audio file

        Returns:
            TranscriptionResult
        """
        import wave

        logger.info(f"Transcribing file: {file_path}")

        with wave.open(str(file_path), "rb") as wf:
            sample_rate = wf.getframerate()
            n_channels = wf.getnchannels()
            n_frames = wf.getnframes()
            audio_bytes = wf.readframes(n_frames)

        # Convert to numpy array
        audio = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0

        # Convert to mono if stereo
        if n_channels > 1:
            audio = audio.reshape(-1, n_channels).mean(axis=1)

        return await self.transcribe_audio(audio, sample_rate)

    def close(self) -> None:
        """Clean up resources."""
        self._whisper_model = None
        self._is_initialized = False
