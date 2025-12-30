"""Transcription processor for batch audio processing."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Optional

import numpy as np

from ..utils.logging_config import get_logger
from .livekit_engine import LiveKitEngine, TranscriptSegment, TranscriptionResult

logger = get_logger("transcription.processor")


@dataclass
class ProcessorState:
    """State of the transcription processor."""

    segments: list[TranscriptSegment] = field(default_factory=list)
    start_time: Optional[datetime] = None
    audio_buffer: list[np.ndarray] = field(default_factory=list)


class TranscriptionProcessor:
    """
    Processes audio and produces transcriptions.

    Collects audio chunks and transcribes them when stopped.
    """

    def __init__(
        self,
        engine: Optional[LiveKitEngine] = None,
        on_segment: Optional[Callable[[TranscriptSegment], None]] = None,
        sample_rate: int = 16000,
    ):
        """
        Initialize the transcription processor.

        Args:
            engine: LiveKitEngine instance (created if not provided)
            on_segment: Callback for each transcribed segment
            sample_rate: Audio sample rate
        """
        self.engine = engine or LiveKitEngine()
        self.on_segment = on_segment
        self.sample_rate = sample_rate
        self._state = ProcessorState()
        self._is_running = False

    async def start(self) -> None:
        """Start the transcription processor."""
        logger.info("Starting transcription processor")
        self._state = ProcessorState(start_time=datetime.now())
        self._is_running = True

    async def stop(self) -> TranscriptionResult:
        """
        Stop the processor and transcribe collected audio.

        Returns:
            Complete transcription result
        """
        if not self._is_running:
            return TranscriptionResult()

        logger.info("Stopping transcription processor")
        self._is_running = False

        # Combine all audio
        if not self._state.audio_buffer:
            logger.warning("No audio data collected")
            return TranscriptionResult()

        audio = np.concatenate(self._state.audio_buffer)
        logger.info(f"Processing {len(audio) / self.sample_rate:.1f} seconds of audio")

        # Transcribe
        try:
            result = await self.engine.transcribe_audio(audio, self.sample_rate)

            # Call segment callbacks
            if self.on_segment:
                for segment in result.segments:
                    self.on_segment(segment)

            return result

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return TranscriptionResult()

    def add_audio_sync(self, chunk) -> None:
        """
        Add an audio chunk synchronously.

        Args:
            chunk: AudioChunk with audio data
        """
        if self._is_running and hasattr(chunk, 'data'):
            self._state.audio_buffer.append(chunk.data)

    @property
    def is_running(self) -> bool:
        """Check if processor is running."""
        return self._is_running
