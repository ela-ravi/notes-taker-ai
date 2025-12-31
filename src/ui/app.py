"""Meeting Notes Taker - Desktop UI Application with Meeting Presets."""

import asyncio
import json
import platform
import subprocess
import threading
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Optional

import customtkinter as ctk
import sounddevice as sd

from ..config import get_settings
from ..notes.generator import MeetingRecorder
from ..notes.models import TranscriptSegment


# Presets file location
PRESETS_FILE = Path(__file__).parent.parent.parent / "meeting_presets.json"

# Default presets
DEFAULT_PRESETS = {
    "ATVE Standup": {
        "title": "ATVE Standup",
        "context": "Focus on blockers, progress updates, and sprint goals",
        "model": "llama3.1:8b",
        "whisper_model": "base",
        "auto_start": True,
    },
    "TNT Sports Standup": {
        "title": "TNT Sports Standup",
        "context": "Focus on blockers, progress updates, and sprint goals",
        "model": "llama3.1:8b",
        "whisper_model": "base",
        "auto_start": True,
    },
    "General Meeting": {
        "title": "",
        "context": "",
        "model": "llama3.1:8b",
        "whisper_model": "base",
        "auto_start": False,
    },
}


class MeetingNotesApp(ctk.CTk):
    """Main application window with meeting presets management."""

    def __init__(self):
        super().__init__()

        self.title("Meeting Notes Taker")
        self.geometry("1000x750")
        self.minsize(900, 650)

        # Set appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # State
        self._recorder: Optional[MeetingRecorder] = None
        self._recording = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._recording_thread: Optional[threading.Thread] = None
        self._notes_path: Optional[Path] = None
        self._presets = self._load_presets()
        self._current_preset: Optional[str] = None

        # Build UI
        self._create_widgets()
        self._check_ollama_status()
        self._load_audio_devices()
        self._load_ollama_models()
        self._populate_presets_list()

    def _load_presets(self) -> dict:
        """Load meeting presets from file."""
        if PRESETS_FILE.exists():
            try:
                with open(PRESETS_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return DEFAULT_PRESETS.copy()

    def _save_presets(self):
        """Save meeting presets to file."""
        try:
            with open(PRESETS_FILE, "w") as f:
                json.dump(self._presets, f, indent=2)
        except Exception as e:
            self._show_error(f"Failed to save presets: {e}")

    def _create_widgets(self):
        """Create all UI widgets."""
        # Main container
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Configure grid
        self.main_frame.grid_columnconfigure(0, weight=0, minsize=250)  # Sidebar
        self.main_frame.grid_columnconfigure(1, weight=1)  # Main content
        self.main_frame.grid_rowconfigure(0, weight=1)

        # Left sidebar - Presets
        self._create_sidebar()

        # Right content - Meeting settings
        self._create_main_content()

    def _create_sidebar(self):
        """Create the presets sidebar."""
        sidebar = ctk.CTkFrame(self.main_frame, width=250)
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=0)
        sidebar.grid_propagate(False)

        # Title
        title = ctk.CTkLabel(
            sidebar,
            text="Meeting Presets",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        title.pack(pady=(15, 10), padx=15, anchor="w")

        # Presets list frame
        list_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Scrollable frame for presets
        self.presets_scroll = ctk.CTkScrollableFrame(list_frame, fg_color="transparent")
        self.presets_scroll.pack(fill="both", expand=True)

        # Buttons frame
        btn_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)

        # New preset button
        new_btn = ctk.CTkButton(
            btn_frame,
            text="+ New Preset",
            command=self._new_preset,
            fg_color="#28a745",
            hover_color="#218838",
        )
        new_btn.pack(fill="x", pady=(0, 5))

        # Delete preset button
        self.delete_btn = ctk.CTkButton(
            btn_frame,
            text="Delete Preset",
            command=self._delete_preset,
            fg_color="#dc3545",
            hover_color="#c82333",
            state="disabled",
        )
        self.delete_btn.pack(fill="x")

    def _create_main_content(self):
        """Create the main content area."""
        content = ctk.CTkFrame(self.main_frame)
        content.grid(row=0, column=1, sticky="nsew", pady=0)

        # Configure grid
        content.grid_rowconfigure(3, weight=1)  # Transcript area
        content.grid_columnconfigure(0, weight=1)

        # Header with status
        self._create_header(content)

        # Meeting Settings
        self._create_settings_section(content)

        # Recording Controls
        self._create_controls_section(content)

        # Transcript Display
        self._create_transcript_section(content)

    def _create_header(self, parent):
        """Create the header with status indicators."""
        header = ctk.CTkFrame(parent)
        header.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))

        # Title
        title = ctk.CTkLabel(
            header,
            text="Meeting Configuration",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        title.pack(side="left", padx=10, pady=10)

        # Status indicators
        status_frame = ctk.CTkFrame(header, fg_color="transparent")
        status_frame.pack(side="right", padx=10, pady=10)

        # Ollama status
        ollama_label = ctk.CTkLabel(status_frame, text="Ollama:")
        ollama_label.pack(side="left", padx=(0, 5))

        self.ollama_status = ctk.CTkLabel(
            status_frame, text="●", text_color="yellow", font=ctk.CTkFont(size=16)
        )
        self.ollama_status.pack(side="left", padx=(0, 10))

        self.ollama_btn = ctk.CTkButton(
            status_frame,
            text="Start",
            width=60,
            height=28,
            command=self._start_ollama,
            state="disabled",
        )
        self.ollama_btn.pack(side="left", padx=(0, 10))

        # Refresh button
        refresh_btn = ctk.CTkButton(
            status_frame,
            text="↻",
            width=30,
            height=28,
            command=self._refresh_all,
        )
        refresh_btn.pack(side="left")

    def _create_settings_section(self, parent):
        """Create the meeting settings section."""
        settings_frame = ctk.CTkFrame(parent)
        settings_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 10))

        # Two columns layout
        settings_frame.grid_columnconfigure(0, weight=1)
        settings_frame.grid_columnconfigure(1, weight=1)

        # Left column - Basic settings
        left_col = ctk.CTkFrame(settings_frame, fg_color="transparent")
        left_col.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Preset name (for saving)
        self._create_field(left_col, "Preset Name:", "preset_name",
                          placeholder="Enter preset name to save...")

        # Meeting title
        self._create_field(left_col, "Meeting Title:", "meeting_title",
                          placeholder="Enter meeting title...")

        # Meeting context (TextArea)
        context_frame = ctk.CTkFrame(left_col, fg_color="transparent")
        context_frame.pack(fill="x", pady=5)

        context_label = ctk.CTkLabel(context_frame, text="Context:", width=120, anchor="w")
        context_label.pack(side="left", anchor="n", pady=(5, 0))

        self.meeting_context = ctk.CTkTextbox(
            context_frame,
            height=80,
            font=ctk.CTkFont(size=13),
        )
        self.meeting_context.pack(side="left", padx=10, fill="x", expand=True)

        # Right column - Advanced settings
        right_col = ctk.CTkFrame(settings_frame, fg_color="transparent")
        right_col.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        # LLM Model
        model_frame = ctk.CTkFrame(right_col, fg_color="transparent")
        model_frame.pack(fill="x", pady=5)

        model_label = ctk.CTkLabel(model_frame, text="LLM Model:", width=120, anchor="w")
        model_label.pack(side="left")

        self.model_dropdown = ctk.CTkComboBox(model_frame, width=200, state="readonly")
        self.model_dropdown.pack(side="left", padx=10, fill="x", expand=True)

        # Whisper Model
        whisper_frame = ctk.CTkFrame(right_col, fg_color="transparent")
        whisper_frame.pack(fill="x", pady=5)

        whisper_label = ctk.CTkLabel(whisper_frame, text="Whisper Model:", width=120, anchor="w")
        whisper_label.pack(side="left")

        self.whisper_dropdown = ctk.CTkComboBox(
            whisper_frame,
            width=200,
            values=["tiny", "base", "small", "medium", "large"],
            state="readonly"
        )
        self.whisper_dropdown.set("base")
        self.whisper_dropdown.pack(side="left", padx=10, fill="x", expand=True)

        # Audio Input Device
        input_frame = ctk.CTkFrame(right_col, fg_color="transparent")
        input_frame.pack(fill="x", pady=5)

        input_label = ctk.CTkLabel(input_frame, text="Audio Input:", width=120, anchor="w")
        input_label.pack(side="left")

        self.input_device = ctk.CTkComboBox(input_frame, width=200, state="readonly")
        self.input_device.pack(side="left", padx=10, fill="x", expand=True)

        # Audio Output Device
        output_frame = ctk.CTkFrame(right_col, fg_color="transparent")
        output_frame.pack(fill="x", pady=5)

        output_label = ctk.CTkLabel(output_frame, text="Audio Output:", width=120, anchor="w")
        output_label.pack(side="left")

        self.output_device = ctk.CTkComboBox(output_frame, width=200, state="readonly")
        self.output_device.pack(side="left", padx=10, fill="x", expand=True)

        # Save preset button
        save_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        save_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))

        self.save_preset_btn = ctk.CTkButton(
            save_frame,
            text="💾 Save as Preset",
            command=self._save_current_preset,
            width=150,
        )
        self.save_preset_btn.pack(side="right", padx=5)

        apply_audio_btn = ctk.CTkButton(
            save_frame,
            text="🔊 Apply Audio Settings",
            command=self._apply_audio_settings,
            width=150,
        )
        apply_audio_btn.pack(side="right", padx=5)

    def _create_field(self, parent, label: str, attr_name: str, placeholder: str = ""):
        """Create a labeled input field."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=5)

        lbl = ctk.CTkLabel(frame, text=label, width=120, anchor="w")
        lbl.pack(side="left")

        entry = ctk.CTkEntry(frame, placeholder_text=placeholder)
        entry.pack(side="left", padx=10, fill="x", expand=True)

        setattr(self, attr_name, entry)

    def _create_controls_section(self, parent):
        """Create the recording controls section."""
        controls = ctk.CTkFrame(parent, fg_color="transparent")
        controls.grid(row=2, column=0, sticky="ew", padx=15, pady=5)

        # Start/Stop button
        self.record_btn = ctk.CTkButton(
            controls,
            text="▶  Start Recording",
            font=ctk.CTkFont(size=18, weight="bold"),
            height=50,
            fg_color="#28a745",
            hover_color="#218838",
            command=self._toggle_recording,
        )
        self.record_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # Right side frame for notes button and status
        right_frame = ctk.CTkFrame(controls, fg_color="transparent")
        right_frame.pack(side="right")

        # Open notes button
        self.open_notes_btn = ctk.CTkButton(
            right_frame,
            text="📄 Open Notes",
            height=50,
            command=self._open_notes,
            state="disabled",
            width=120,
        )
        self.open_notes_btn.pack(side="top")

        # Status label below the Open Notes button
        self.status_label = ctk.CTkLabel(
            right_frame,
            text="Ready to record",
            text_color="gray",
            font=ctk.CTkFont(size=12),
        )
        self.status_label.pack(side="top", pady=(5, 0))

    def _create_transcript_section(self, parent):
        """Create the live transcript display section."""
        transcript_frame = ctk.CTkFrame(parent)
        transcript_frame.grid(row=3, column=0, sticky="nsew", padx=15, pady=(10, 15))

        # Section title
        title_frame = ctk.CTkFrame(transcript_frame, fg_color="transparent")
        title_frame.pack(fill="x", padx=15, pady=(10, 5))

        transcript_title = ctk.CTkLabel(
            title_frame,
            text="Live Transcript",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        transcript_title.pack(side="left")

        clear_btn = ctk.CTkButton(
            title_frame,
            text="Clear",
            width=60,
            height=25,
            command=self._clear_transcript,
        )
        clear_btn.pack(side="right")

        # Transcript textbox
        self.transcript_box = ctk.CTkTextbox(
            transcript_frame,
            font=ctk.CTkFont(size=13),
            state="disabled",
        )
        self.transcript_box.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def _populate_presets_list(self):
        """Populate the presets list in sidebar."""
        # Clear existing
        for widget in self.presets_scroll.winfo_children():
            widget.destroy()

        # Add presets
        for name in self._presets.keys():
            btn = ctk.CTkButton(
                self.presets_scroll,
                text=name,
                anchor="w",
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray30"),
                command=lambda n=name: self._select_preset(n),
            )
            btn.pack(fill="x", pady=2)

    def _select_preset(self, name: str):
        """Select and load a preset."""
        self._current_preset = name
        preset = self._presets.get(name, {})

        # Update UI fields
        self.preset_name.delete(0, "end")
        self.preset_name.insert(0, name)

        self.meeting_title.delete(0, "end")
        self.meeting_title.insert(0, preset.get("title", ""))

        self.meeting_context.delete("1.0", "end")
        self.meeting_context.insert("1.0", preset.get("context", ""))

        if preset.get("model"):
            self.model_dropdown.set(preset["model"])

        if preset.get("whisper_model"):
            self.whisper_dropdown.set(preset["whisper_model"])

        # Enable delete button
        self.delete_btn.configure(state="normal")

        # Highlight selected preset
        for widget in self.presets_scroll.winfo_children():
            if widget.cget("text") == name:
                widget.configure(fg_color=("gray75", "gray25"))
            else:
                widget.configure(fg_color="transparent")

    def _new_preset(self):
        """Create a new preset."""
        self._current_preset = None
        self.preset_name.delete(0, "end")
        self.meeting_title.delete(0, "end")
        self.meeting_context.delete("1.0", "end")
        self.model_dropdown.set("llama3.1:8b")
        self.whisper_dropdown.set("base")
        self.delete_btn.configure(state="disabled")

        # Clear selection highlight
        for widget in self.presets_scroll.winfo_children():
            widget.configure(fg_color="transparent")

    def _save_current_preset(self):
        """Save the current settings as a preset."""
        name = self.preset_name.get().strip()
        if not name:
            self._show_error("Please enter a preset name.")
            return

        self._presets[name] = {
            "title": self.meeting_title.get().strip(),
            "context": self.meeting_context.get("1.0", "end").strip(),
            "model": self.model_dropdown.get(),
            "whisper_model": self.whisper_dropdown.get(),
            "auto_start": False,
        }

        self._save_presets()
        self._populate_presets_list()
        self._select_preset(name)
        self._show_info(f"Preset '{name}' saved!")

    def _delete_preset(self):
        """Delete the currently selected preset."""
        if not self._current_preset:
            return

        if self._current_preset in self._presets:
            del self._presets[self._current_preset]
            self._save_presets()
            self._populate_presets_list()
            self._new_preset()
            self._show_info("Preset deleted.")

    def _check_ollama_status(self) -> bool:
        """Check if Ollama is running."""
        try:
            import urllib.request
            req = urllib.request.Request("http://localhost:11434/api/tags")
            with urllib.request.urlopen(req, timeout=2) as response:
                if response.status == 200:
                    self.ollama_status.configure(text="●", text_color="green")
                    self.ollama_btn.configure(state="disabled")
                    return True
        except Exception:
            pass

        self.ollama_status.configure(text="●", text_color="red")
        self.ollama_btn.configure(state="normal")
        return False

    def _start_ollama(self):
        """Start Ollama server."""
        self.ollama_status.configure(text="●", text_color="yellow")
        self.ollama_btn.configure(state="disabled")

        def start_server():
            try:
                if platform.system() == "Darwin":
                    subprocess.Popen(
                        ["ollama", "serve"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                else:
                    subprocess.Popen(
                        ["ollama", "serve"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0,
                    )
                import time
                for _ in range(20):
                    time.sleep(0.5)
                    if self._check_ollama_status():
                        self.after(0, self._load_ollama_models)
                        break
            except Exception as e:
                self.after(0, lambda: self._show_error(f"Failed to start Ollama: {e}"))

        threading.Thread(target=start_server, daemon=True).start()

    def _load_ollama_models(self):
        """Load available Ollama models."""
        def fetch_models():
            try:
                import urllib.request
                import json as json_lib
                req = urllib.request.Request("http://localhost:11434/api/tags")
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = json_lib.loads(response.read())
                    models = [m["name"] for m in data.get("models", [])]
                    self.after(0, lambda: self._update_models_dropdown(models))
            except Exception:
                self.after(0, lambda: self._update_models_dropdown(["llama3.1:8b"]))

        threading.Thread(target=fetch_models, daemon=True).start()

    def _update_models_dropdown(self, models: list):
        """Update the models dropdown."""
        if models:
            self.model_dropdown.configure(values=models)
            if "llama3.1:8b" in models:
                self.model_dropdown.set("llama3.1:8b")
            else:
                self.model_dropdown.set(models[0])

    def _load_audio_devices(self):
        """Load available audio devices."""
        try:
            devices = sd.query_devices()
            input_devices = []
            output_devices = []

            for device in devices:
                name = device["name"]
                if device["max_input_channels"] > 0:
                    input_devices.append(name)
                if device["max_output_channels"] > 0:
                    output_devices.append(name)

            input_devices = list(dict.fromkeys(input_devices))
            output_devices = list(dict.fromkeys(output_devices))

            self.input_device.configure(values=input_devices)
            self.output_device.configure(values=output_devices)

            settings = get_settings()
            if settings.audio_device in input_devices:
                self.input_device.set(settings.audio_device)
            elif "Aggregate Device" in input_devices:
                self.input_device.set("Aggregate Device")
            elif input_devices:
                self.input_device.set(input_devices[0])

            if "Multi-Output Device" in output_devices:
                self.output_device.set("Multi-Output Device")
            elif output_devices:
                self.output_device.set(output_devices[0])

        except Exception as e:
            self._show_error(f"Failed to load audio devices: {e}")

    def _apply_audio_settings(self):
        """Apply the selected audio settings."""
        input_dev = self.input_device.get()
        output_dev = self.output_device.get()

        if platform.system() == "Darwin":
            try:
                subprocess.run(["SwitchAudioSource", "-t", "input", "-s", input_dev], capture_output=True)
                subprocess.run(["SwitchAudioSource", "-t", "output", "-s", output_dev], capture_output=True)
                self._show_info("Audio settings applied!")
            except FileNotFoundError:
                self._show_info(
                    "SwitchAudioSource not installed.\n"
                    "Install with: brew install switchaudio-osx\n\n"
                    "Please set audio devices manually."
                )
        else:
            self._show_info("Please set audio devices manually in Windows Sound Settings.")

    def _refresh_all(self):
        """Refresh all status indicators."""
        self._check_ollama_status()
        self._load_audio_devices()
        self._load_ollama_models()

    def _toggle_recording(self):
        """Start or stop recording."""
        if self._recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self):
        """Start recording a meeting."""
        title = self.meeting_title.get().strip()
        if not title:
            title = f"Meeting {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            self.meeting_title.delete(0, "end")
            self.meeting_title.insert(0, title)

        context = self.meeting_context.get("1.0", "end").strip() or None
        model = self.model_dropdown.get()
        whisper_model = self.whisper_dropdown.get()

        if not self._check_ollama_status():
            self._show_error("Ollama is not running. Please start Ollama first.")
            return

        # Update settings
        settings = get_settings()
        settings.ollama_model = model
        settings.whisper_model = whisper_model
        settings.audio_device = self.input_device.get()

        # Update UI
        self._recording = True
        self.record_btn.configure(
            text="⏹  Stop Recording",
            fg_color="#dc3545",
            hover_color="#c82333",
        )
        self.status_label.configure(text="Recording...", text_color="red")
        self._disable_inputs()
        self.open_notes_btn.configure(state="disabled")

        # Clear transcript
        self._clear_transcript()

        # Start recording
        self._recording_thread = threading.Thread(
            target=self._run_recording,
            args=(title, context),
            daemon=True,
        )
        self._recording_thread.start()

    def _disable_inputs(self):
        """Disable all input fields during recording."""
        self.preset_name.configure(state="disabled")
        self.meeting_title.configure(state="disabled")
        self.meeting_context.configure(state="disabled")
        self.model_dropdown.configure(state="disabled")
        self.whisper_dropdown.configure(state="disabled")
        self.input_device.configure(state="disabled")
        self.output_device.configure(state="disabled")

    def _enable_inputs(self):
        """Re-enable all input fields."""
        self.preset_name.configure(state="normal")
        self.meeting_title.configure(state="normal")
        self.meeting_context.configure(state="normal")
        self.model_dropdown.configure(state="readonly")
        self.whisper_dropdown.configure(state="readonly")
        self.input_device.configure(state="readonly")
        self.output_device.configure(state="readonly")

    def _run_recording(self, title: str, context: Optional[str]):
        """Run the recording in a background thread."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        try:
            self._loop.run_until_complete(self._async_recording(title, context))
        except Exception as e:
            self.after(0, lambda: self._show_error(f"Recording error: {e}"))
        finally:
            self._loop.close()
            self._loop = None
            self._recording = False
            # Always reset the UI state when recording thread ends
            self.after(0, self._reset_recording_ui)

    async def _async_recording(self, title: str, context: Optional[str]):
        """Async recording coroutine."""
        def on_segment(segment: TranscriptSegment):
            text = segment.text.strip()
            if text:
                speaker = segment.speaker_label
                timestamp = segment.timestamp
                self.after(0, lambda: self._add_transcript(f"[{timestamp}] {speaker}: {text}\n"))

        self._recorder = MeetingRecorder(on_segment=on_segment)
        session = await self._recorder.start(title, custom_context=context)

        self.after(0, lambda: self.status_label.configure(
            text=f"Recording: {session.id}", text_color="red"
        ))

        while self._recording and self._recorder.is_recording:
            await asyncio.sleep(0.1)

        if self._recorder.is_recording:
            self.after(0, lambda: self.status_label.configure(
                text="Generating notes...", text_color="yellow"
            ))
            await self._recorder.stop()

            if self._recorder.current_session and self._recorder.current_session.notes_path:
                self._notes_path = Path(self._recorder.current_session.notes_path)
                self.after(0, self._on_recording_complete)

    def _stop_recording(self):
        """Stop the current recording."""
        self._recording = False
        self.status_label.configure(text="Stopping...", text_color="yellow")

    def _reset_recording_ui(self):
        """Reset the UI to non-recording state."""
        self._recording = False
        self.record_btn.configure(
            text="▶  Start Recording",
            fg_color="#28a745",
            hover_color="#218838",
        )
        self._enable_inputs()
        # Set appropriate status based on whether notes were generated
        if self._notes_path and self._notes_path.exists():
            self.status_label.configure(text="Notes generated!", text_color="green")
            self.open_notes_btn.configure(state="normal")
        else:
            self.status_label.configure(text="Ready to record", text_color="gray")

    def _on_recording_complete(self):
        """Handle successful recording completion with notes."""
        self.open_notes_btn.configure(state="normal")
        self.status_label.configure(text="Notes generated!", text_color="green")

    def _add_transcript(self, text: str):
        """Add text to the transcript display."""
        self.transcript_box.configure(state="normal")
        self.transcript_box.insert("end", text)
        self.transcript_box.see("end")
        self.transcript_box.configure(state="disabled")

    def _clear_transcript(self):
        """Clear the transcript display."""
        self.transcript_box.configure(state="normal")
        self.transcript_box.delete("1.0", "end")
        self.transcript_box.configure(state="disabled")

    def _open_notes(self):
        """Open the generated notes."""
        if self._notes_path:
            html_path = self._notes_path.with_suffix(".html")
            if html_path.exists():
                webbrowser.open(f"file://{html_path.absolute()}")
            elif self._notes_path.exists():
                webbrowser.open(f"file://{self._notes_path.absolute()}")

    def _show_error(self, message: str):
        """Show an error dialog."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Error")
        dialog.geometry("400x150")
        dialog.transient(self)
        dialog.grab_set()

        label = ctk.CTkLabel(dialog, text=message, wraplength=350)
        label.pack(pady=20, padx=20)

        btn = ctk.CTkButton(dialog, text="OK", command=dialog.destroy)
        btn.pack(pady=10)

    def _show_info(self, message: str):
        """Show an info dialog."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Info")
        dialog.geometry("400x180")
        dialog.transient(self)
        dialog.grab_set()

        label = ctk.CTkLabel(dialog, text=message, wraplength=350)
        label.pack(pady=20, padx=20)

        btn = ctk.CTkButton(dialog, text="OK", command=dialog.destroy)
        btn.pack(pady=10)


def main():
    """Run the application."""
    app = MeetingNotesApp()
    app.mainloop()


if __name__ == "__main__":
    main()
