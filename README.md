# Zoom Notes Taker

Automatic meeting notes generator from Zoom meetings using local AI. Captures audio, transcribes with Whisper, and generates summarized meeting notes with action items using Ollama LLM.

## Features

- **Local Processing**: All audio processing and AI inference runs locally - no cloud APIs required
- **Real-time Transcription**: Uses OpenAI Whisper for accurate speech-to-text
- **Smart Summarization**: Generates meeting summaries, key points, action items, and decisions using Ollama
- **Multi-language Support**: Supports multiple languages including Tamil, with auto-detection
- **HTML & Markdown Output**: Beautiful HTML reports and portable Markdown files
- **Auto-organized Notes**: Notes automatically saved to appropriate folders based on meeting type
- **Cross-platform**: Works on macOS and Windows

---

## Prerequisites

### All Platforms

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | 3.10+ | Runtime |
| Ollama | Latest | Local LLM inference |
| FFmpeg | Latest | Audio processing |

### macOS

| Requirement | Install Command |
|-------------|-----------------|
| Homebrew | `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"` |
| BlackHole | `brew install blackhole-2ch` |
| Ollama | `brew install ollama` |
| FFmpeg | `brew install ffmpeg` |

### Windows

| Requirement | Download |
|-------------|----------|
| VB-Cable | https://vb-audio.com/Cable/ |
| Ollama | https://ollama.ai |
| FFmpeg | https://ffmpeg.org/download.html |

---

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd zoom-notes-taker
```

### 2. Create Virtual Environment

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -e .
```

### 3a. Configure Launch Scripts (IMPORTANT for Windows/macOS)

Run the `setup_paths.py` script to automatically configure the project directory in your `.bat` and `.command` quick launch scripts. This step ensures they work correctly on your system.

```bash
python setup_paths.py
```

### 4. Download Ollama Model

```bash
ollama pull llama3.1:8b
```

### 5. Download Whisper Model (automatic on first run)

The Whisper model downloads automatically. To pre-download:

```bash
python -c "import whisper; whisper.load_model('base')"
```

### 6. Run Setup Check

```bash
python -m src.main setup
```

---

## Audio Configuration

### macOS Setup

1. **Install BlackHole**
   ```bash
   brew install blackhole-2ch
   ```

2. **Create Multi-Output Device** (for hearing + capturing Zoom audio)
   - Open **Audio MIDI Setup** (Spotlight → "Audio MIDI Setup")
   - Click **+** → **Create Multi-Output Device**
   - Check: **MacBook Pro Speakers** (or your speakers)
   - Check: **BlackHole 2ch**

3. **Create Aggregate Device** (for capturing both sides of conversation)
   - Click **+** → **Create Aggregate Device**
   - Check: **BlackHole 2ch**
   - Check: **MacBook Pro Microphone**

4. **Configure Zoom**
   - Settings → Audio
   - **Speaker**: Multi-Output Device
   - **Microphone**: MacBook Pro Microphone

5. **Update .env file**
   ```env
   ZNT_AUDIO_DEVICE=Aggregate Device
   ```

### Windows Setup

1. **Install VB-Cable** from https://vb-audio.com/Cable/

2. **Configure Windows Sound**
   - Settings → Sound → Output
   - Set **CABLE Input** as default playback device

3. **Configure Zoom**
   - Settings → Audio
   - **Speaker**: CABLE Input (VB-Audio Virtual Cable)
   - **Microphone**: Your physical microphone

4. **Update .env file**
   ```env
   ZNT_AUDIO_DEVICE=CABLE Output
   ```

---

## Configuration

Create a `.env` file in the project root:

```env
# Audio Settings
ZNT_AUDIO_DEVICE=Aggregate Device      # macOS: Aggregate Device, Windows: CABLE Output
ZNT_SAMPLE_RATE=16000

# Whisper Settings
ZNT_WHISPER_MODEL=base                 # tiny, base, small, medium, large
ZNT_WHISPER_LANGUAGE=                  # Empty for auto-detect, or: en, ta, es, etc.

# Ollama Settings
ZNT_OLLAMA_MODEL=llama3.1:8b
ZNT_OLLAMA_HOST=http://localhost:11434

# Output Settings (optional - scripts override this)
ZNT_OUTPUT_DIR=~/Documents/ZoomNotes/notes
ZNT_RECORDINGS_DIR=~/Documents/ZoomNotes/recordings
```

---

## Usage

### Quick Start Scripts

Double-click these scripts to start recording:

| Script | Platform | Description |
|--------|----------|-------------|
| `atve-standup.command` | macOS | ATVE Standup (auto-start) |
| `tnt-standup.command` | macOS | TNT Sports Standup (auto-start) |
| `zoom-notes.command` | macOS | General meeting (prompts for title) |
| `atve-standup.bat` | Windows | ATVE Standup (auto-start) |
| `tnt-standup.bat` | Windows | TNT Sports Standup (auto-start) |
| `zoom-notes.bat` | Windows | General meeting (prompts for title) |

### CLI Commands

```bash
# Activate virtual environment first
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Start recording a meeting
python -m src.main start --title "My Meeting"

# Transcribe an existing audio file
python -m src.main transcribe path/to/audio.wav --title "Past Meeting"

# Check setup and dependencies
python -m src.main setup

# List audio devices
python -m src.main devices

# Show current configuration
python -m src.main config
```

---

## Your First Meeting

### Step 1: Start Ollama Server

```bash
ollama serve
```

### Step 2: Configure Zoom Audio

- Set Zoom **Speaker** to Multi-Output Device (macOS) or CABLE Input (Windows)
- Keep Zoom **Microphone** as your regular microphone

### Step 3: Start Recording

**Option A: Using Script**
- Double-click `zoom-notes.command` (macOS) or `zoom-notes.bat` (Windows)
- Enter meeting title when prompted

**Option B: Using CLI**
```bash
source venv/bin/activate
python -m src.main start --title "Team Standup"
```

### Step 4: Join Your Zoom Meeting

Join or start your Zoom call. The app will capture audio in real-time.

### Step 5: Stop and Generate Notes

Press `Ctrl+C` to stop recording. The app will:
1. Process the audio
2. Transcribe with Whisper
3. Generate summary with Ollama
4. Save notes as Markdown and HTML
5. Auto-open the HTML in your browser

---

## Output Structure

Notes are automatically organized based on meeting title:

```
~/Library/CloudStorage/OneDrive-.../meeting-notes/
├── atve-meeting-notes/
│   └── 2024-12-30_ATVE_Standup.html
├── tnt-meeting-notes/
│   └── 2024-12-30_TNT_Sports_Standup.html
└── general/
    └── 2024-12-30_Team_Sync.html
```

### Folder Routing Rules

| Meeting Title Contains | Folder |
|------------------------|--------|
| "ATVE", "AT&VE" | `atve-meeting-notes/` |
| "TNT", "Sports" | `tnt-meeting-notes/` |
| Other | `general/` |

---

## Customizing Scripts

### Ensure Scripts are Configured

After initial installation or if you move the project, run `python setup_paths.py` to ensure all `.bat` and `.command` files correctly point to the project directory.

### Change Notes Storage Location

Edit the `ZNT_NOTES_BASE` variable in each script:

**macOS (.command files):**
```bash
export ZNT_NOTES_BASE="$HOME/Documents/MyNotes"
```

**Windows (.bat files):</b>
```cmd
set ZNT_NOTES_BASE=%USERPROFILE%\Documents\MyNotes
```

### Create Custom Meeting Scripts

The provided `atve-standup`, `tnt-standup`, and `zoom-notes` scripts are examples. You can create your own custom quick-launch scripts:
1. Copy an existing `.bat` (for Windows) or `.command` (for macOS) file.
2. Rename it (e.g., `my-team-meeting.bat`).
3. Edit the new script:
    *   Change `MEETING_TITLE` for fixed-title meetings.
    *   Change `ZNT_NOTES_BASE` if you want a different storage location for these specific notes.


---

## Troubleshooting

### "Audio device not found"

```bash
# List available devices
python -m src.main devices

# Update .env with correct device name
ZNT_AUDIO_DEVICE=<device name from list>
```

### "Ollama connection failed"

```bash
# Start Ollama server
ollama serve

# Check if model is installed
ollama list

# Pull model if missing
ollama pull llama3.1:8b
```

### "Only hearing one side of conversation"

- **macOS**: Ensure you're using Aggregate Device (not just BlackHole)
- **Windows**: Ensure Zoom speaker is set to CABLE Input

### "Transcription is slow"

- Use a smaller Whisper model: `ZNT_WHISPER_MODEL=tiny`
- Ensure you have sufficient RAM (8GB+ recommended)

---

## Project Structure

```
zoom-notes-taker/
├── src/
│   ├── audio/           # Audio capture and device management
│   ├── llm/             # Ollama client and summarization
│   ├── notes/           # Notes generation and templates
│   ├── transcription/   # Whisper transcription engine
│   ├── utils/           # Utilities and file handling
│   ├── config.py        # Application settings
│   ├── config_platform.py  # Platform-specific configs
│   └── main.py          # CLI entry point
├── *.command            # macOS launch scripts
├── *.bat                # Windows launch scripts
├── .env                 # Configuration (create this)
├── pyproject.toml       # Python project config
└── README.md            # This file
```

---

## Language Support

Set language in `.env`:

```env
# Auto-detect language
ZNT_WHISPER_LANGUAGE=

# Specific language codes
ZNT_WHISPER_LANGUAGE=en    # English
ZNT_WHISPER_LANGUAGE=ta    # Tamil
ZNT_WHISPER_LANGUAGE=es    # Spanish
ZNT_WHISPER_LANGUAGE=fr    # French
ZNT_WHISPER_LANGUAGE=de    # German
ZNT_WHISPER_LANGUAGE=ja    # Japanese
ZNT_WHISPER_LANGUAGE=zh    # Chinese
```

---

## License

MIT License
