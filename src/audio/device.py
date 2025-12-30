"""Audio device detection and management."""

from dataclasses import dataclass
from typing import Optional

import sounddevice as sd

from ..utils.logging_config import get_logger

logger = get_logger("audio.device")


@dataclass
class AudioDevice:
    """Represents an audio device."""

    id: int
    name: str
    max_input_channels: int
    max_output_channels: int
    default_sample_rate: float
    is_input: bool
    is_output: bool


class AudioDeviceManager:
    """Manages audio device detection and selection."""

    def __init__(self, preferred_device: str = "BlackHole 2ch"):
        """
        Initialize the device manager.

        Args:
            preferred_device: Name of the preferred audio device
        """
        self.preferred_device = preferred_device
        self._devices: list[AudioDevice] = []
        self._refresh_devices()

    def _refresh_devices(self) -> None:
        """Refresh the list of available audio devices."""
        self._devices = []
        try:
            devices = sd.query_devices()
            for idx, device in enumerate(devices):
                self._devices.append(
                    AudioDevice(
                        id=idx,
                        name=device["name"],
                        max_input_channels=device["max_input_channels"],
                        max_output_channels=device["max_output_channels"],
                        default_sample_rate=device["default_samplerate"],
                        is_input=device["max_input_channels"] > 0,
                        is_output=device["max_output_channels"] > 0,
                    )
                )
        except Exception as e:
            logger.error(f"Failed to query audio devices: {e}")

    def get_input_devices(self) -> list[AudioDevice]:
        """Get all available input devices."""
        return [d for d in self._devices if d.is_input]

    def get_output_devices(self) -> list[AudioDevice]:
        """Get all available output devices."""
        return [d for d in self._devices if d.is_output]

    def find_device(self, name: str) -> Optional[AudioDevice]:
        """
        Find a device by name (partial match).

        Args:
            name: Device name to search for

        Returns:
            AudioDevice if found, None otherwise
        """
        name_lower = name.lower()
        for device in self._devices:
            if name_lower in device.name.lower():
                return device
        return None

    def find_blackhole_device(self) -> Optional[AudioDevice]:
        """
        Find the BlackHole virtual audio device.

        Returns:
            AudioDevice if found, None otherwise
        """
        return self.find_device(self.preferred_device)

    def get_preferred_input_device(self) -> Optional[AudioDevice]:
        """
        Get the preferred input device (BlackHole or default).

        Returns:
            AudioDevice if found, None otherwise
        """
        # Try to find BlackHole first
        blackhole = self.find_blackhole_device()
        if blackhole and blackhole.is_input:
            return blackhole

        # Fall back to default input device
        try:
            default_id = sd.default.device[0]
            if default_id is not None and 0 <= default_id < len(self._devices):
                return self._devices[default_id]
        except Exception:
            pass

        # Return first available input device
        input_devices = self.get_input_devices()
        return input_devices[0] if input_devices else None

    def check_blackhole_installed(self) -> bool:
        """
        Check if BlackHole is installed.

        Returns:
            True if BlackHole is found
        """
        return self.find_blackhole_device() is not None

    def print_devices(self) -> None:
        """Print all available audio devices."""
        print("\n[bold]Available Audio Devices:[/bold]\n")
        print(f"{'ID':<4} {'Name':<40} {'In':<4} {'Out':<4} {'Sample Rate':<12}")
        print("-" * 70)
        for device in self._devices:
            in_ch = device.max_input_channels if device.is_input else "-"
            out_ch = device.max_output_channels if device.is_output else "-"
            print(
                f"{device.id:<4} {device.name[:39]:<40} {in_ch:<4} {out_ch:<4} {device.default_sample_rate:<12.0f}"
            )
