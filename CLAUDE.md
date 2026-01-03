# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Development Commands

### Setup
```bash
./bootstrap.sh              # macOS/Linux - creates venv, installs deps
bootstrap.bat               # Windows equivalent
pip install -e ".[dev]"     # Install with dev tools (pytest, black, ruff, mypy)
pip install -e ".[gui]"     # Install with GUI dependencies
```

### Running
```bash
python -m src.main start --title "Meeting"   # CLI mode
./meeting-notes-ui.command                    # Desktop UI (macOS)
meeting-notes-ui.bat                          # Desktop UI (Windows)
python -m src.main setup                      # Check system dependencies
python -m src.main devices                    # List audio devices
```

### Code Quality
```bash
ruff check src/             # Linting (line-length: 100)
black src/                  # Formatting
mypy src/                   # Type checking
pytest                      # Run tests
```

### Building Distribution
```bash
./build_macos.sh           # Build macOS .app bundle (PyInstaller)
./create_dmg.sh            # Create macOS DMG installer
```

## Architecture

This is a meeting notes application that captures audio, transcribes speech, and generates AI summaries.

### Core Pipeline
```
Audio Capture → Whisper Transcription → LLM Summarization → Notes (MD/HTML)
(sounddevice)   (livekit_engine.py)     (summarizer.py)     (generator.py)
```

### Key Modules

- **`src/audio/`** - Real-time audio capture, device detection (BlackHole/VB-Cable)
- **`src/transcription/`** - Whisper-based speech-to-text via LiveKit engine
- **`src/llm/`** - Multi-provider LLM support with factory pattern:
  - `factory.py` - Provider selection based on config
  - `cloud_client.py` - Supabase Edge Function proxy (SaaS mode)
  - `groq_client.py` - Groq API (fast cloud inference)
  - `ollama_client.py` - Local Ollama
  - `huggingface_client.py` - HuggingFace Inference API
- **`src/notes/`** - Notes generation, data models, Markdown/HTML templates
- **`src/auth/`** - Supabase authentication for SaaS mode
- **`src/ui/`** - CustomTkinter desktop GUI

### Configuration

Settings use Pydantic with `ZNT_` prefix for environment variables. See `.env.example` for all options.

### Dual Operating Modes

1. **Standalone**: Local LLM (Ollama) or direct API calls
2. **SaaS**: User auth + subscriptions via Supabase backend (`backend/supabase/`)

### Patterns

- Async-first I/O operations
- Factory pattern for LLM provider selection
- Callback-based event handling for transcription segments
- Platform-specific audio device handling (macOS vs Windows)

## Session Management

### Current Implementation

| Component | Location | Description |
|-----------|----------|-------------|
| **MeetingSession** | `src/notes/models.py:145-173` | Dataclass tracking id, title, timestamps, status, paths |
| **MeetingRecorder** | `src/notes/generator.py:285-430` | Lifecycle management (start → recording → processing → completed) |
| **Auth sessions** | `src/auth/auth_manager.py` | Supabase auth tokens persisted to `~/.meeting_notes_session.json` |
| **UI state** | `src/ui/app.py` | In-memory recording state tracking |

### Session States
```
recording → processing → completed
                      ↘ error
```

### Not Yet Implemented

- **Session History/Persistence** - No database of past sessions
- **Session Recovery** - Cannot resume interrupted recordings
- **Pause/Resume** - Currently all-or-nothing recording
- **Multi-session Support** - Only one active session at a time
- **Session Sync** - No backend sync for session data

## Next Steps (Potential Features)

1. **Session Persistence** - Store session history in SQLite or JSON file
2. **Pause/Resume** - Allow pausing and resuming recordings
3. **Session Recovery** - Resume after crashes or unexpected exits
4. **Session History UI** - View and manage past sessions in the desktop app
5. **Backend Sync** - Sync session metadata to Supabase for SaaS users
