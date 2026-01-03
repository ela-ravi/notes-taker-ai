"""
Zoom Notes Taker - CLI Entry Point

Automatic meeting notes generator from Zoom meetings using local AI.
"""

import asyncio
import signal
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table

from .audio.device import AudioDeviceManager
from .config import get_settings
from .config_platform import get_platform_config
from .llm.factory import create_llm_client, get_available_providers
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


def select_llm_provider() -> str:
    """Display available LLM providers and let user select one."""
    settings = get_settings()
    providers = get_available_providers()

    console.print("\n[bold cyan]Available LLM Providers:[/bold cyan]")
    table = Table(show_header=True, header_style="bold")
    table.add_column("#", style="dim", width=4)
    table.add_column("Provider", style="cyan")
    table.add_column("Model", style="white")
    table.add_column("Status", style="green")

    available_providers = []
    for idx, p in enumerate(providers, 1):
        status = "[green]Ready[/green]" if p["available"] else f"[red]{p['reason']}[/red]"
        is_default = " (default)" if p["id"] == settings.llm_provider else ""
        table.add_row(str(idx), p["name"] + is_default, p["model"], status)
        available_providers.append(p)

    console.print(table)

    # Prompt for selection
    console.print(f"\n[dim]Press Enter to use default ({settings.llm_provider})[/dim]")
    choice = click.prompt(
        "Select provider number",
        default="",
        show_default=False,
    )

    if not choice:
        return settings.llm_provider

    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(available_providers):
            selected = available_providers[idx]
            if not selected["available"]:
                console.print(f"[yellow]Warning: {selected['name']} is not available. {selected['reason']}[/yellow]")
            return selected["id"]

    return settings.llm_provider


def select_ollama_model() -> str:
    """Display available Ollama models and let user select one."""
    settings = get_settings()
    default_model = settings.ollama_model

    # Get available models
    ollama_client = OllamaClient()
    if not ollama_client.check_connection():
        console.print("[yellow]Warning: Cannot connect to Ollama. Using default model.[/yellow]")
        return default_model

    available_models = ollama_client.list_models()

    if not available_models:
        console.print("[yellow]No models found in Ollama. Using default.[/yellow]")
        return default_model

    # Display available models
    console.print("\n[bold cyan]Available Ollama Models:[/bold cyan]")
    table = Table(show_header=True, header_style="bold")
    table.add_column("#", style="dim", width=4)
    table.add_column("Model", style="cyan")
    table.add_column("", style="green")

    for idx, model in enumerate(available_models, 1):
        is_default = "(default)" if default_model in model or model.startswith(default_model.split(":")[0]) else ""
        table.add_row(str(idx), model, is_default)

    console.print(table)

    # Prompt for selection
    console.print(f"\n[dim]Press Enter to use default ({default_model})[/dim]")
    choice = click.prompt(
        "Select model number or name",
        default="",
        show_default=False,
    )

    if not choice:
        return default_model

    # Handle numeric selection
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(available_models):
            return available_models[idx]
        console.print("[yellow]Invalid selection, using default.[/yellow]")
        return default_model

    # Handle name input - check if it matches any available model
    for model in available_models:
        if choice.lower() in model.lower():
            return model

    console.print(f"[yellow]Model '{choice}' not found, using default.[/yellow]")
    return default_model


@cli.command()
@click.option("--title", "-t", prompt="Meeting title", help="Title for the meeting")
@click.option("--provider", "-p", default=None, type=click.Choice(["ollama", "huggingface", "groq"]), help="LLM provider (default: from config)")
@click.option("--model", "-m", default=None, help="Model to use (default: from config)")
@click.option("--default-model", "-d", is_flag=True, help="Use default provider and model without prompting")
@click.option("--context", "-c", default=None, help="Additional context for notes generation (e.g., 'Focus on action items for frontend team')")
def start(title: str, provider: Optional[str], model: Optional[str], default_model: bool, context: Optional[str]):
    """Start recording a Zoom meeting."""
    global _recorder, _stop_event

    settings = get_settings()

    # Select provider
    if provider is not None:
        selected_provider = provider
    elif default_model:
        selected_provider = settings.llm_provider
    else:
        selected_provider = select_llm_provider()

    # Update settings with selected provider
    settings.llm_provider = selected_provider

    # Select model based on provider
    if model is not None:
        selected_model = model
    elif default_model:
        if selected_provider == "ollama":
            selected_model = settings.ollama_model
        elif selected_provider == "groq":
            selected_model = settings.groq_model
        else:
            selected_model = settings.hf_model
    elif selected_provider == "ollama":
        selected_model = select_ollama_model()
    elif selected_provider == "groq":
        # For Groq, use the default model
        selected_model = settings.groq_model
    else:
        # For HuggingFace, use the default model
        selected_model = settings.hf_model

    # Update settings with selected model
    if selected_provider == "ollama":
        settings.ollama_model = selected_model
    elif selected_provider == "groq":
        settings.groq_model = selected_model
    else:
        settings.hf_model = selected_model

    provider_names = {
        "ollama": "Ollama (Local)",
        "groq": "Groq (Cloud - Fast)",
        "huggingface": "HuggingFace (Cloud)",
    }
    provider_display = provider_names.get(selected_provider, selected_provider)
    panel_text = (
        f"[bold green]Recording:[/bold green] {title}\n"
        f"[bold blue]Provider:[/bold blue] {provider_display}\n"
        f"[bold blue]Model:[/bold blue] {selected_model}"
    )
    if context:
        panel_text += f"\n[bold yellow]Context:[/bold yellow] {context[:50]}{'...' if len(context) > 50 else ''}"
    panel_text += "\n\nPress [bold]Ctrl+C[/bold] to stop recording and generate notes."

    console.print(Panel(panel_text, title="Meeting Notes Taker"))

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
        try:
            loop.add_signal_handler(signal.SIGINT, lambda: _stop_event.set())
        except NotImplementedError:
            # Signal handlers are not supported on Windows.
            # We rely on KeyboardInterrupt to stop the loop.
            pass

        try:
            session = await _recorder.start(title, custom_context=context)
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
                            md_path = Path(_recorder.current_session.notes_path)
                            html_path = md_path.with_suffix(".html")
                            folder_name = md_path.parent.name
                            console.print(f"\n[green]Notes saved to:[/green] [cyan]{folder_name}[/cyan]")
                            console.print(f"  Markdown: {md_path}")
                            console.print(f"  HTML:     {html_path}")

                            # Auto-open HTML in browser
                            import webbrowser
                            webbrowser.open(f"file://{html_path.absolute()}")

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

    def on_progress(_message: str, _percentage: float):
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

        html_path = output_path.with_suffix(".html")
        console.print(f"\n[green]Notes saved:[/green]")
        console.print(f"  Markdown: {output_path}")
        console.print(f"  HTML:     {html_path}")

        # Auto-open HTML in browser
        import webbrowser
        webbrowser.open(f"file://{html_path.absolute()}")

    asyncio.run(run_transcription())


@cli.command()
def setup():
    """Run initial setup and check dependencies."""
    platform_cfg = get_platform_config()

    console.print(Panel(
        f"[bold]Zoom Notes Taker Setup[/bold]\n\n"
        f"Platform: {platform_cfg.name}\n"
        "Checking system requirements...",
        title="Setup",
    ))

    checks = []

    # Check Python version
    py_version = sys.version_info
    py_ok = py_version >= (3, 10)
    checks.append(("Python 3.10+", py_ok, f"{py_version.major}.{py_version.minor}.{py_version.micro}"))

    # Check Virtual Audio Device (platform-specific)
    device_manager = AudioDeviceManager()
    virtual_audio_ok = device_manager.check_blackhole_installed()
    audio_device_name = platform_cfg.audio.virtual_audio_device.split()[0]  # First word (BlackHole, CABLE, etc.)
    checks.append((f"{audio_device_name} Audio", virtual_audio_ok, platform_cfg.audio.install_instructions))

    # Check Ollama
    ollama_client = OllamaClient()
    ollama_ok = ollama_client.check_connection()
    ollama_install = "brew install ollama && ollama serve" if platform_cfg.name == "macOS" else "https://ollama.ai"
    checks.append(("Ollama Server", ollama_ok, ollama_install))

    # Check Ollama model
    model_ok = False
    settings = get_settings()
    if ollama_ok:
        model_ok = ollama_client.check_model_available()
    checks.append((f"Ollama Model ({settings.ollama_model})", model_ok, f"Run: ollama pull {settings.ollama_model}"))

    # Check WhisperLiveKit
    import importlib.util
    if importlib.util.find_spec("whisperlivekit"):
        whisper_ok = True
        whisper_msg = "Installed"
    elif importlib.util.find_spec("whisper"):
        whisper_ok = True
        whisper_msg = "Fallback to openai-whisper"
    else:
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

    # Show platform-specific audio setup instructions
    if virtual_audio_ok:
        console.print()
        console.print(Panel(
            f"[bold]{platform_cfg.name} Audio Setup:[/bold]\n\n"
            f"{platform_cfg.audio.setup_instructions}",
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
    table.add_row("Language", settings.whisper_language or "auto-detect")
    table.add_row("Diarization", "Enabled" if settings.enable_diarization else "Disabled")
    table.add_row("", "")  # Separator
    provider_names = {
        "ollama": "Ollama (Local)",
        "groq": "Groq (Cloud - Fast)",
        "huggingface": "HuggingFace (Cloud)",
    }
    provider_display = provider_names.get(settings.llm_provider, settings.llm_provider)
    table.add_row("LLM Provider", provider_display)
    table.add_row("Groq Model", settings.groq_model)
    table.add_row("Groq API Key", "Configured" if settings.groq_api_key else "[dim]Not set[/dim]")
    table.add_row("Ollama Model", settings.ollama_model)
    table.add_row("Ollama Host", settings.ollama_host)
    table.add_row("HuggingFace Model", settings.hf_model)
    table.add_row("HF Token", "Configured" if settings.hf_token else "[dim]Not set[/dim]")
    table.add_row("", "")  # Separator
    table.add_row("Output Directory", str(settings.output_dir))
    table.add_row("Recordings Directory", str(settings.recordings_dir))

    console.print(table)

    # Show provider status
    console.print("\n[bold]LLM Provider Status:[/bold]")
    providers = get_available_providers()
    for p in providers:
        status = "[green]Ready[/green]" if p["available"] else f"[red]Not available[/red] - {p['reason']}"
        console.print(f"  {p['name']}: {status}")

    console.print("\n[dim]Edit .env file to change settings[/dim]")


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
