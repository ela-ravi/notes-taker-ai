"""Platform-specific configurations for macOS and Windows."""

import platform
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class AudioConfig:
    """Audio device configuration."""
    virtual_audio_device: str
    virtual_audio_names: list[str]
    install_instructions: str
    setup_instructions: str


@dataclass
class PlatformConfig:
    """Platform-specific configuration."""
    name: str
    audio: AudioConfig
    default_notes_path: Path
    script_extension: str
    venv_activate: str


# macOS Configuration
MACOS_CONFIG = PlatformConfig(
    name="macOS",
    audio=AudioConfig(
        virtual_audio_device="BlackHole 2ch",
        virtual_audio_names=["BlackHole", "Aggregate Device", "Multi-Output Device"],
        install_instructions="brew install blackhole-2ch",
        setup_instructions="""
1. Open Audio MIDI Setup (search in Spotlight)
2. Click + at bottom left → Create Multi-Output Device
3. Check both your speakers AND BlackHole 2ch
4. Create Aggregate Device with BlackHole + Microphone
5. In Zoom:
   - Speaker: Multi-Output Device
   - Microphone: Your physical microphone
6. Set ZNT_AUDIO_DEVICE='Aggregate Device' in .env
""".strip(),
    ),
    default_notes_path=Path.home() / "Documents/ZoomNotes/notes",
    script_extension=".command",
    venv_activate="source venv/bin/activate",
)


# Windows Configuration
WINDOWS_CONFIG = PlatformConfig(
    name="Windows",
    audio=AudioConfig(
        virtual_audio_device="CABLE Output",
        virtual_audio_names=["CABLE Output", "VB-Cable", "Virtual Audio Cable", "CABLE Input", "VoiceMeeter"],
        install_instructions="Download from https://vb-audio.com/Cable/",
        setup_instructions="""
1. Install VB-Cable from https://vb-audio.com/Cable/
2. In Windows Sound Settings:
   - Set 'CABLE Input' as default playback device
3. In Zoom Settings → Audio:
   - Speaker: CABLE Input (VB-Audio Virtual Cable)
   - Microphone: Your physical microphone
4. Set ZNT_AUDIO_DEVICE='CABLE Output' in .env
""".strip(),
    ),
    default_notes_path=Path.home() / "Documents/ZoomNotes/notes",
    script_extension=".bat",
    venv_activate="venv\\Scripts\\activate.bat",
)


# Linux Configuration
LINUX_CONFIG = PlatformConfig(
    name="Linux",
    audio=AudioConfig(
        virtual_audio_device="pulse",
        virtual_audio_names=["pulse", "PulseAudio", "pipewire"],
        install_instructions="Install PulseAudio or PipeWire",
        setup_instructions="""
1. Install PulseAudio: sudo apt install pulseaudio
2. Use pavucontrol to configure audio routing
3. Set up a virtual sink for capturing application audio
4. Set ZNT_AUDIO_DEVICE to your virtual sink name in .env
""".strip(),
    ),
    default_notes_path=Path.home() / "Documents/ZoomNotes/notes",
    script_extension=".sh",
    venv_activate="source venv/bin/activate",
)


def get_platform_config() -> PlatformConfig:
    """Get configuration for the current platform."""
    system = platform.system()
    if system == "Darwin":
        return MACOS_CONFIG
    elif system == "Windows":
        return WINDOWS_CONFIG
    else:
        return LINUX_CONFIG


def get_default_audio_device() -> str:
    """Get the default virtual audio device for the current platform."""
    return get_platform_config().audio.virtual_audio_device


def get_virtual_audio_names() -> list[str]:
    """Get list of virtual audio device names to search for."""
    return get_platform_config().audio.virtual_audio_names


def get_audio_install_instructions() -> str:
    """Get installation instructions for virtual audio driver."""
    return get_platform_config().audio.install_instructions


def get_audio_setup_instructions() -> str:
    """Get setup instructions for audio routing."""
    return get_platform_config().audio.setup_instructions
