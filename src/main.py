"""
Zoom Notes Taker - CLI Entry Point

Automatic meeting notes generator from Zoom meetings using local AI.
"""

import asyncio
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.text import Text

from .audio.device import AudioDeviceManager
from .config import get_settings, reload_settings
from .llm.ollama_client import OllamaClient
from .notes.generator import MeetingRecorder, NotesGenerator
from .transcription.livekit_engine import TranscriptSegment
from .utils.logging_config import setup_logging

console = Console()

# Global state for recording
_recorder: Optional[MeetingRecorder] = None
_stop_event: Optional[asyncio.Event] = None


@click.group()
@click.version_option(version="1.0.0", prog_name="zoom-notes")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def cli(verbose: bool):
    """
    Zoom Notes Taker - Capture and summarize meetings locally.

    Use 'zoom-notes setup' to configure your system before first use.
    """
    level = 10 if verbose else 20  # DEBUG or INFO
    setup_logging(level=level)


@cli.command()
@click.option("--title", "-t", prompt="Meeting title", help="Title for the meeting")
def start(title: str):
    """Start recording a Zoom meeting."""
    global _recorder, _stop_event

    console.print(Panel(
        f"[bold green]Recording:[/bold green] {title}\n\n"
        "Press [bold]Ctrl+C[/bold] to stop recording and generate notes.",
        title="Zoom Notes Taker",
    ))

    # Track segments for live display
    segments: list[TranscriptSegment] = []

    def on_segment(segment: TranscriptSegment):
        """Handle new transcript segment."""
        segments.append(segment)
        # Display in real-time
        speaker = segment.speaker_label
        text = segment.text.strip()
        if text:
            console.print(f"[dim]{segment.timestamp}[/dim] [cyan]{speaker}:[/cyan] {text}")

    async def run_recording():
        global _recorder, _stop_event

        _stop_event = asyncio.Event()
        _recorder = MeetingRecorder(on_segment=on_segment)

        # Set up signal handler for this event loop
        loop = asyncio.get_event_loop()
        loop.add_signal_handler(signal.SIGINT, lambda: _stop_event.set())

        try:
            session = await _recorder.start(title)
            console.print(f"[green]Session started:[/green] {session.id}")
            console.print("[dim]Listening for audio...[/dim]\n")

            # Wait for stop signal (Ctrl+C)
            await _stop_event.wait()
            console.print("\n[yellow]Stopping recording...[/yellow]")

        except Exception as e:
            console.print(f"\n[red]Error: {e}[/red]")

        finally:
            if _recorder and _recorder.is_recording:
                console.print("\n[yellow]Processing...[/yellow]")

                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                ) as progress:
                    task = progress.add_task("Generating notes...", total=None)

                    try:
                        notes = await _recorder.stop()

                        progress.update(task, description="Complete!")

                        # Display results
                        console.print()
                        console.print(Panel(
                            f"[bold]Summary:[/bold]\n{notes.summary}\n\n"
                            f"[bold]Key Points:[/bold] {len(notes.key_points)}\n"
                            f"[bold]Action Items:[/bold] {len(notes.action_items)}\n"
                            f"[bold]Speakers:[/bold] {notes.speaker_count}",
                            title="Meeting Notes Generated",
                            border_style="green",
                        ))

                        if _recorder.current_session and _recorder.current_session.notes_path:
                            console.print(
                                f"\n[green]Notes saved to:[/green] {_recorder.current_session.notes_path}"
                            )

                    except Exception as e:
                        console.print(f"[red]Error generating notes:[/red] {e}")

    # Run the async recording
    asyncio.run(run_recording())


@cli.command()
@click.argument("audio_file", type=click.Path(exists=True, path_type=Path))
@click.option("--output", "-o", type=click.Path(path_type=Path), help="Output file path")
@click.option("--title", "-t", default="Meeting Notes", help="Meeting title")
def transcribe(audio_file: Path, output: Optional[Path], title: str):
    """Transcribe an existing audio file and generate notes."""
    console.print(f"[blue]Transcribing:[/blue] {audio_file}")

    def on_progress(message: str, percentage: float):
        pass  # Progress is shown via Progress bar

    async def run_transcription():
        generator = NotesGenerator(on_progress=on_progress)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        ) as progress:
            task = progress.add_task("Processing...", total=100)

            def update_progress(message: str, percentage: float):
                progress.update(task, completed=percentage, description=message)

            generator.on_progress = update_progress

            # Determine output path
            if output is None:
                output_path = generator.get_default_output_path(title)
            else:
                output_path = output

            # Generate notes
            notes = await generator.generate_from_audio_file(
                audio_path=audio_file,
                title=title,
                output_path=output_path,
            )

            progress.update(task, completed=100, description="Complete!")

        # Display results
        console.print()
        console.print(Panel(
            f"[bold]Summary:[/bold]\n{notes.summary}\n\n"
            f"[bold]Duration:[/bold] {notes.formatted_duration}\n"
            f"[bold]Key Points:[/bold] {len(notes.key_points)}\n"
            f"[bold]Action Items:[/bold] {len(notes.action_items)}",
            title="Meeting Notes",
            border_style="green",
        ))

        console.print(f"\n[green]Notes saved to:[/green] {output_path}")

    asyncio.run(run_transcription())


@cli.command()
def setup():
    """Run initial setup and check dependencies."""
    console.print(Panel(
        "[bold]Zoom Notes Taker Setup[/bold]\n\n"
        "Checking system requirements...",
        title="Setup",
    ))

    checks = []

    # Check Python version
    py_version = sys.version_info
    py_ok = py_version >= (3, 10)
    checks.append(("Python 3.10+", py_ok, f"{py_version.major}.{py_version.minor}.{py_version.micro}"))

    # Check BlackHole
    device_manager = AudioDeviceManager()
    blackhole_ok = device_manager.check_blackhole_installed()
    checks.append(("BlackHole Audio", blackhole_ok, "Install: brew install blackhole-2ch"))

    # Check Ollama
    ollama_client = OllamaClient()
    ollama_ok = ollama_client.check_connection()
    checks.append(("Ollama Server", ollama_ok, "Install: brew install ollama && ollama serve"))

    # Check Ollama model
    model_ok = False
    settings = get_settings()
    if ollama_ok:
        model_ok = ollama_client.check_model_available()
    checks.append((f"Ollama Model ({settings.ollama_model})", model_ok, f"Run: ollama pull {settings.ollama_model}"))

    # Check WhisperLiveKit
    try:
        import whisperlivekit
        whisper_ok = True
        whisper_msg = "Installed"
    except ImportError:
        try:
            import whisper
            whisper_ok = True
            whisper_msg = "Fallback to openai-whisper"
        except ImportError:
            whisper_ok = False
            whisper_msg = "Run: pip install whisperlivekit"
    checks.append(("WhisperLiveKit/Whisper", whisper_ok, whisper_msg))

    # Display results
    console.print()
    table = Table(title="System Requirements")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Notes", style="dim")

    all_ok = True
    for name, ok, note in checks:
        status = "[green]✓[/green]" if ok else "[red]✗[/red]"
        table.add_row(name, status, note if not ok else "")
        if not ok:
            all_ok = False

    console.print(table)
    console.print()

    if all_ok:
        console.print("[green]All requirements met! You're ready to use Zoom Notes Taker.[/green]")
        console.print("\nTo start recording: [bold]zoom-notes start[/bold]")
    else:
        console.print("[yellow]Some requirements are missing. Please install them before using.[/yellow]")

    # Show audio setup instructions if BlackHole is installed but needs configuration
    if blackhole_ok:
        console.print()
        console.print(Panel(
            "[bold]Audio Setup Instructions:[/bold]\n\n"
            "1. Open [cyan]Audio MIDI Setup[/cyan] (search in Spotlight)\n"
            "2. Click [cyan]+[/cyan] at bottom left → Create Multi-Output Device\n"
            "3. Check both your speakers AND BlackHole 2ch\n"
            "4. Set Multi-Output Device as your system output\n"
            "5. In Zoom, use this Multi-Output Device for audio",
            title="Configure Audio Routing",
            border_style="blue",
        ))


@cli.command()
def devices():
    """List available audio devices."""
    device_manager = AudioDeviceManager()

    table = Table(title="Audio Devices")
    table.add_column("ID", style="cyan", width=4)
    table.add_column("Name", style="white")
    table.add_column("Input", style="green", width=6)
    table.add_column("Output", style="blue", width=6)
    table.add_column("Sample Rate", style="dim", width=12)

    for device in device_manager._devices:
        input_ch = str(device.max_input_channels) if device.is_input else "-"
        output_ch = str(device.max_output_channels) if device.is_output else "-"

        # Highlight BlackHole
        name = device.name
        if "blackhole" in name.lower():
            name = f"[bold green]{name}[/bold green]"

        table.add_row(
            str(device.id),
            name,
            input_ch,
            output_ch,
            f"{device.default_sample_rate:.0f}",
        )

    console.print(table)

    # Check for BlackHole
    if device_manager.check_blackhole_installed():
        console.print("\n[green]✓ BlackHole detected[/green]")
    else:
        console.print("\n[yellow]BlackHole not found. Install with: brew install blackhole-2ch[/yellow]")


@cli.command()
def config():
    """Show current configuration."""
    settings = get_settings()

    table = Table(title="Current Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Audio Device", settings.audio_device)
    table.add_row("Sample Rate", f"{settings.sample_rate} Hz")
    table.add_row("Whisper Model", settings.whisper_model)
    table.add_row("Language", settings.whisper_language)
    table.add_row("Diarization", "Enabled" if settings.enable_diarization else "Disabled")
    table.add_row("Ollama Model", settings.ollama_model)
    table.add_row("Ollama Host", settings.ollama_host)
    table.add_row("Output Directory", str(settings.output_dir))
    table.add_row("Recordings Directory", str(settings.recordings_dir))

    console.print(table)
    console.print("\n[dim]Edit .env file to change settings[/dim]")


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
