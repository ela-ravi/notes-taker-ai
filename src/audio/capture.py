"""Audio capture module using sounddevice."""

import asyncio
import wave
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from queue import Queue
from threading import Event, Thread
from typing import Callable, Optional

import numpy as np
import sounddevice as sd

from ..config import get_settings
from ..utils.logging_config import get_logger
from .device import AudioDevice, AudioDeviceManager

logger = get_logger("audio.capture")


@dataclass
class AudioConfig:
    """Audio capture configuration."""

    sample_rate: int = 16000  # Optimal for Whisper
    channels: int = 1  # Mono for speech
    dtype: str = "float32"
    blocksize: int = 1024  # Samples per block
    device_name: str = "BlackHole 2ch"


@dataclass
class AudioChunk:
    """Represents a chunk of audio data."""

    data: np.ndarray
    timestamp: datetime = field(default_factory=datetime.now)
    sample_rate: int = 16000
    channels: int = 1

    @property
    def duration(self) -> float:
        """Duration of the chunk in seconds."""
        return len(self.data) / self.sample_rate


class AudioCapture:
    """Captures audio from system audio devices."""

    def __init__(
        self,
        config: Optional[AudioConfig] = None,
        on_chunk: Optional[Callable[[AudioChunk], None]] = None,
    ):
        """
        Initialize audio capture.

        Args:
            config: Audio configuration
            on_chunk: Callback function for each audio chunk
        """
        settings = get_settings()
        self.config = config or AudioConfig(
            sample_rate=settings.sample_rate,
            channels=settings.channels,
            device_name=settings.audio_device,
        )
        self.on_chunk = on_chunk

        self.device_manager = AudioDeviceManager(self.config.device_name)
        self.audio_queue: Queue[np.ndarray] = Queue()
        self.is_recording = Event()
        self.is_paused = Event()

        self._stream: Optional[sd.InputStream] = None
        self._recording_thread: Optional[Thread] = None
        self._all_audio: list[np.ndarray] = []
        self._start_time: Optional[datetime] = None

    def _get_device_info(self) -> tuple[int, int]:
        """Get the device ID and input channel count for the configured audio device."""
        device = self.device_manager.find_device(self.config.device_name)
        if device is None:
            raise RuntimeError(
                f"Audio device '{self.config.device_name}' not found. "
                f"Please check your audio settings or install BlackHole: "
                f"brew install blackhole-2ch"
            )
        if not device.is_input:
            raise RuntimeError(
                f"Device '{device.name}' is not an input device."
            )
        return device.id, device.max_input_channels

    def _audio_callback(
        self,
        indata: np.ndarray,
        frames: int,
        time_info: dict,
        status: sd.CallbackFlags,
    ) -> None:
        """Callback function for audio stream."""
        if status:
            logger.warning(f"Audio callback status: {status}")

        if self.is_recording.is_set() and not self.is_paused.is_set():
            # Copy data to avoid issues with buffer reuse
            audio_copy = indata.copy()

            # Mix all channels to mono by averaging
            if audio_copy.ndim > 1 and audio_copy.shape[1] > 1:
                audio_data = audio_copy.mean(axis=1).astype(np.float32)
            else:
                audio_data = audio_copy.flatten()

            self.audio_queue.put(audio_data)

    def _process_audio_queue(self) -> None:
        """Process audio chunks from the queue."""
        chunk_buffer: list[np.ndarray] = []
        chunk_samples = int(self.config.sample_rate * 2)  # 2 seconds per chunk

        while self.is_recording.is_set():
            try:
                # Get audio data with timeout
                audio_data = self.audio_queue.get(timeout=0.1)
                chunk_buffer.append(audio_data)
                self._all_audio.append(audio_data)

                # Check if we have enough for a chunk
                total_samples = sum(len(d) for d in chunk_buffer)
                if total_samples >= chunk_samples:
                    # Combine and create chunk
                    combined = np.concatenate(chunk_buffer)
                    chunk = AudioChunk(
                        data=combined[:chunk_samples],
                        sample_rate=self.config.sample_rate,
                        channels=self.config.channels,
                    )

                    # Keep remaining samples
                    remaining = combined[chunk_samples:]
                    chunk_buffer = [remaining] if len(remaining) > 0 else []

                    # Call the chunk callback
                    if self.on_chunk:
                        try:
                            self.on_chunk(chunk)
                        except Exception as e:
                            logger.error(f"Error in chunk callback: {e}")

            except Exception:
                # Queue.get timeout, continue
                pass

        # Process any remaining audio
        if chunk_buffer and self.on_chunk:
            combined = np.concatenate(chunk_buffer)
            if len(combined) > 0:
                chunk = AudioChunk(
                    data=combined,
                    sample_rate=self.config.sample_rate,
                    channels=self.config.channels,
                )
                try:
                    self.on_chunk(chunk)
                except Exception as e:
                    logger.error(f"Error in final chunk callback: {e}")

    def start(self) -> None:
        """Start audio capture."""
        if self.is_recording.is_set():
            logger.warning("Recording already in progress")
            return

        try:
            device_id, input_channels = self._get_device_info()
            logger.info(f"Starting audio capture on device {device_id} with {input_channels} channels")

            self._start_time = datetime.now()
            self._all_audio = []
            self.is_recording.set()
            self.is_paused.clear()

            # Create and start audio stream
            # Use all available input channels to capture from Aggregate Device
            # (includes both BlackHole and Microphone channels)
            self._stream = sd.InputStream(
                device=device_id,
                channels=input_channels,  # Capture all channels, mix to mono in callback
                samplerate=self.config.sample_rate,
                dtype=self.config.dtype,
                blocksize=self.config.blocksize,
                callback=self._audio_callback,
            )
            self._stream.start()

            # Start processing thread
            self._recording_thread = Thread(
                target=self._process_audio_queue,
                daemon=True,
            )
            self._recording_thread.start()

            logger.info("Audio capture started")

        except Exception as e:
            self.is_recording.clear()
            logger.error(f"Failed to start audio capture: {e}")
            raise

    def stop(self) -> np.ndarray:
        """
        Stop audio capture and return the full recording.

        Returns:
            Complete audio recording as numpy array
        """
        if not self.is_recording.is_set():
            logger.warning("No recording in progress")
            return np.array([])

        logger.info("Stopping audio capture...")
        self.is_recording.clear()

        # Stop stream
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        # Wait for processing thread
        if self._recording_thread:
            self._recording_thread.join(timeout=2.0)
            self._recording_thread = None

        # Combine all audio
        if self._all_audio:
            full_audio = np.concatenate(self._all_audio)
            duration = len(full_audio) / self.config.sample_rate
            logger.info(f"Recording stopped. Duration: {duration:.1f} seconds")
            return full_audio

        return np.array([])

    def pause(self) -> None:
        """Pause audio capture."""
        if self.is_recording.is_set():
            self.is_paused.set()
            logger.info("Recording paused")

    def resume(self) -> None:
        """Resume audio capture."""
        if self.is_recording.is_set():
            self.is_paused.clear()
            logger.info("Recording resumed")

    def save_recording(self, audio: np.ndarray, path: Path) -> None:
        """
        Save audio recording to a WAV file.

        Args:
            audio: Audio data as numpy array
            path: Path to save the WAV file
        """
        if len(audio) == 0:
            logger.warning("No audio data to save")
            return

        path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to 16-bit PCM
        audio_int16 = (audio * 32767).astype(np.int16)

        with wave.open(str(path), "wb") as wf:
            wf.setnchannels(self.config.channels)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(self.config.sample_rate)
            wf.writeframes(audio_int16.tobytes())

        logger.info(f"Recording saved to {path}")

    @property
    def duration(self) -> float:
        """Get the current recording duration in seconds."""
        if not self._all_audio:
            return 0.0
        total_samples = sum(len(d) for d in self._all_audio)
        return total_samples / self.config.sample_rate

    @property
    def is_active(self) -> bool:
        """Check if recording is active."""
        return self.is_recording.is_set()


async def capture_audio_async(
    duration: float,
    config: Optional[AudioConfig] = None,
) -> np.ndarray:
    """
    Capture audio asynchronously for a specified duration.

    Args:
        duration: Duration to capture in seconds
        config: Audio configuration

    Returns:
        Audio data as numpy array
    """
    capture = AudioCapture(config=config)
    capture.start()

    await asyncio.sleep(duration)

    return capture.stop()
