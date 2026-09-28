# Custom Output Directory Feature

## Overview
Added user-configurable output directories for meeting notes and recordings, both via CLI and UI.

## Changes Made

### 1. Configuration Module (`src/config.py`)

Added three new functions to set custom directories:

```python
def set_output_directory(output_dir: Path) -> None:
    """Set custom output directory for meeting notes."""
    
def set_recordings_directory(recordings_dir: Path) -> None:
    """Set custom recordings directory for audio files."""
    
def set_base_directory(base_dir: Path) -> None:
    """Set base directory for both notes and recordings.
    Creates /notes and /recordings subdirectories."""
```

### 2. CLI Commands (`src/main.py`)

#### `start` command
Added three new options:
- `--output-dir` / `-o`: Custom directory for meeting notes
- `--recordings-dir` / `-r`: Custom directory for recordings  
- `--base-dir` / `-b`: Base directory (creates /notes and /recordings subdirs)

**Examples:**
```bash
# Use custom base directory
python -m src.main start --title "Team Meeting" --base-dir ~/MyMeetings

# Use separate directories
python -m src.main start --title "Team Meeting" \
  --output-dir ~/Documents/Notes \
  --recordings-dir ~/Documents/Audio

# Quick shorthand
python -m src.main start -t "Meeting" -b ~/Meetings
```

#### `transcribe` command
Added `--output-dir` option:

```bash
python -m src.main transcribe audio.wav --output-dir ~/Documents/Transcripts
```

### 3. Desktop UI (`src/ui/app.py`)

Added output directory controls to the settings section:

**New UI Elements:**
- **Output Folder** text entry field
- **📁 Browse** button to select directory via file dialog
- Auto-updates status message when directory is set

**Location:** Right column, after audio device settings

**Features:**
- Shows placeholder: "Default: ~/Documents/ZoomNotes"
- Browse button opens native file picker
- Path is applied when recording starts
- Creates `/notes` and `/recordings` subdirectories automatically

## Usage Examples

### CLI Usage

```bash
# Default behavior (uses ~/Documents/ZoomNotes)
python -m src.main start --title "Meeting"

# Custom base directory
python -m src.main start --title "Meeting" --base-dir ~/Desktop/Meetings

# Output will be:
#  ~/Desktop/Meetings/notes/2026-01-06_Meeting.md
#  ~/Desktop/Meetings/recordings/2026-01-06_Meeting.wav

# Separate directories
python -m src.main start --title "Meeting" \
  --output-dir ~/Dropbox/Notes \
  --recordings-dir /Volumes/External/Audio

# From environment variable (set in .env)
export ZNT_NOTES_BASE=~/OneDrive/MeetingNotes
python -m src.main start --title "Meeting"
```

### UI Usage

1. Open the desktop app
2. In the settings section (right column), find "Output Folder"
3. Either:
   - Type the path directly (e.g., `~/Documents/MyMeetings`)
   - Click 📁 to browse and select a folder
4. Start recording - notes will be saved to:
   - `{selected_folder}/notes/` - Meeting notes (MD & HTML)
   - `{selected_folder}/recordings/` - Audio recordings (WAV)

### Environment Variable

You can also set the default in `.env`:

```env
# Set custom base directory
ZNT_NOTES_BASE=~/Library/CloudStorage/OneDrive/MeetingNotes/notes

# This affects recordings too:
# Recordings go to parent directory + "/recordings"
```

## Directory Structure

When you set a base directory, the app creates this structure:

```
{base_dir}/
├── notes/
│   ├── 2026-01-06_11-16_ATVE_Standup.md
│   ├── 2026-01-06_11-16_ATVE_Standup.html
│   └── ... (more notes)
└── recordings/
    ├── 2026-01-06_11-16_ATVE_Standup.wav
    └── ... (more recordings)
```

## Default Directories

If no custom directory is specified:
- **Notes**: `~/Documents/ZoomNotes/notes/`
- **Recordings**: `~/Documents/ZoomNotes/recordings/`

## Technical Details

### Path Resolution
- Paths support `~` (home directory expansion)
- Relative paths are converted to absolute
- Directories are created automatically if they don't exist
- All paths are validated before use

### Settings Persistence
- CLI: Applies for that session only
- UI: Applies when recording starts
- Environment: Persists across sessions
- Presets: Can include custom paths (future enhancement)

### Error Handling
- Invalid paths show error message
- Permission errors caught and displayed
- Falls back to default if creation fails

## Benefits

1. **Organize by project**: Keep different project meetings separate
2. **Cloud sync**: Save directly to Dropbox/OneDrive/iCloud
3. **External storage**: Use external drives for large recordings
4. **Team sharing**: Save to shared network drives
5. **Backup**: Easily configure backup-friendly locations

## Future Enhancements

Possible additions:
- [ ] Remember last-used directory
- [ ] Per-preset output directories
- [ ] Quick directory presets dropdown
- [ ] Auto-organize by date (YYYY/MM/DD subdirectories)
- [ ] Separate audio and notes directories in UI
- [ ] Browse button in CLI (interactive mode)
- [ ] Validate disk space before recording

## Testing

Test the feature:

```bash
# Test CLI
python -m src.main start -t "Test" -b /tmp/test-meetings
# Check: ls /tmp/test-meetings/notes/
# Check: ls /tmp/test-meetings/recordings/

# Test UI
# 1. Launch: python -m src.ui.app
# 2. Set output to /tmp/ui-test
# 3. Record a test meeting
# 4. Verify files in /tmp/ui-test/notes/ and /tmp/ui-test/recordings/
```

## Backward Compatibility

✅ Fully backward compatible:
- Existing `.env` configurations still work
- Default directories unchanged
- No breaking changes to API
- Existing presets continue to work


