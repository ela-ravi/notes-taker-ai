# How to Retry Failed Meeting Summaries

If your meeting notes show "Authentication failed" errors but the transcript is correct, you can regenerate the summary without re-recording.

## Quick Fix

### Option 1: Use the `retry` Command (Recommended)

```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows

# Retry with auto-detection of available provider
python -m src.main retry output/2026-01-06_11-16_ATVE_Standup.html

# Or specify a provider explicitly
python -m src.main retry output/2026-01-06_11-16_ATVE_Standup.html --provider ollama
python -m src.main retry output/2026-01-06_11-16_ATVE_Standup.html --provider groq
```

The command:
1. Extracts the full transcript from your existing HTML or Markdown file
2. Uses an available local provider (Ollama/Groq) to regenerate the summary
3. Overwrites the files with the corrected version
4. Opens the new HTML in your browser

### Option 2: Use Fallback Providers

The app now automatically tries fallback providers when authentication fails:

**Fallback order**: Cloud (if logged in) → Groq (if API key set) → Ollama (local)

Just re-record your meeting, and if cloud auth fails, it will automatically use Groq or Ollama.

## Supported Providers

| Provider | Requires | Speed | Cost |
|----------|----------|-------|------|
| **ollama** | Local Ollama server | Medium | Free |
| **groq** | GROQ_API_KEY in .env | Fast | Free (with limits) |
| **huggingface** | HF_TOKEN in .env | Slow | Free |
| **cloud** | Login to app | Fast | Paid subscription |

## Setup Alternative Providers

### Ollama (Local - Recommended for retry)

```bash
# Install Ollama
brew install ollama  # macOS
# or download from https://ollama.ai

# Start Ollama
ollama serve

# Pull a model
ollama pull llama3.1:8b
```

### Groq (Cloud - Fast & Free)

1. Get API key from https://console.groq.com
2. Add to `.env`:
   ```env
   GROQ_API_KEY=gsk_...
   ```

## Why Did Authentication Fail?

The authentication error happens when:
1. **Token expired**: Your login session expired during the meeting (sessions last 1 hour by default)
2. **Network issue**: Connection to Supabase was interrupted
3. **Rate limiting**: Too many requests to the cloud service

## Prevention

To avoid this in future:
1. **Use Ollama for long meetings** (no auth required)
2. **Check login status** before starting a meeting
3. **Save the recording** - you can always transcribe it later with `zoom-notes transcribe`

## Example Workflow

```bash
# Find your failed notes file
ls -lt output/

# Retry with Ollama (no login needed)
python -m src.main retry output/2026-01-06_11-16_ATVE_Standup.html --provider ollama

# Or let it auto-select the best available provider
python -m src.main retry output/2026-01-06_11-16_ATVE_Standup.html
```

## Check Available Providers

```bash
# See which providers are ready to use
python -m src.main config
```

Look for the "LLM Provider Status" section at the bottom.

## Troubleshooting

### "No available providers!"

Install Ollama or configure Groq:
```bash
brew install ollama
ollama serve
ollama pull llama3.1:8b
```

### "Could not extract transcript from file"

Make sure your file has a "Full Transcript" section. If the file is corrupted, you may need to re-record.

### "ModuleNotFoundError: No module named 'bs4'"

Install the missing dependency:
```bash
pip install beautifulsoup4
```

## Need Help?

- Check logs in your output files
- Run `python -m src.main setup` to verify your installation
- Make sure at least one LLM provider is configured

