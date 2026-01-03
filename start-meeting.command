#!/bin/bash
# Meeting Notes - One-Click Launcher
# Handles Ollama, audio setup, and starts recording

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              Meeting Notes - Starting Up                     ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Source .env for configuration
if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
else
    echo -e "${RED}Error: .env file not found${NC}"
    echo "Please run bootstrap.sh first."
    read -p "Press Enter to close..."
    exit 1
fi

PROJECT_DIR="${ZNT_PROJECT_DIR:-$SCRIPT_DIR}"
cd "$PROJECT_DIR" || exit 1

# =============================================================================
# Step 1: Check and Start Ollama
# =============================================================================
echo -e "${BLUE}[1/4]${NC} Checking Ollama..."

# Check if ollama is installed
if ! command -v ollama &> /dev/null; then
    echo -e "${RED}✗ Ollama is not installed${NC}"
    echo ""
    echo "Please install Ollama first:"
    echo ""
    echo -e "  ${YELLOW}brew install ollama${NC}"
    echo ""
    echo "  Or download from: https://ollama.ai"
    echo ""
    echo "After installing, run this script again."
    read -p "Press Enter to close..."
    exit 1
fi

# Check if ollama is running
if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo -e "${YELLOW}Starting Ollama...${NC}"
    # Start ollama in background
    ollama serve &> /dev/null &
    OLLAMA_PID=$!

    # Wait for ollama to be ready (max 10 seconds)
    for i in {1..20}; do
        if curl -s http://localhost:11434/api/tags &> /dev/null; then
            echo -e "${GREEN}✓ Ollama started${NC}"
            break
        fi
        sleep 0.5
    done

    if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
        echo -e "${RED}✗ Failed to start Ollama${NC}"
        echo "Please start Ollama manually: ollama serve"
        read -p "Press Enter to close..."
        exit 1
    fi
else
    echo -e "${GREEN}✓ Ollama is running${NC}"
fi

# Check if model is available
MODEL="${ZNT_OLLAMA_MODEL:-llama3.1:8b}"
if ! ollama list 2>/dev/null | grep -q "${MODEL%%:*}"; then
    echo -e "${YELLOW}Model $MODEL not found. Pulling...${NC}"
    ollama pull "$MODEL"
fi

# =============================================================================
# Step 2: Switch Audio Input to Aggregate Device
# =============================================================================
echo ""
echo -e "${BLUE}[2/4]${NC} Setting audio input to Aggregate Device..."

AUDIO_INPUT_OK=false

if command -v SwitchAudioSource &> /dev/null; then
    if SwitchAudioSource -t input -s "Aggregate Device" 2>/dev/null; then
        echo -e "${GREEN}✓ Input: Aggregate Device${NC}"
        AUDIO_INPUT_OK=true
    fi
fi

if [ "$AUDIO_INPUT_OK" = false ]; then
    echo -e "${RED}✗ Could not automatically set audio input${NC}"
    echo ""
    echo "Manual steps required:"
    echo -e "  1. Open ${YELLOW}System Settings → Sound → Input${NC}"
    echo -e "  2. Select ${YELLOW}Aggregate Device${NC}"
    echo ""
    echo "Options:"
    echo -e "  ${GREEN}[S]kip${NC} - Continue anyway, set audio input manually now"
    echo -e "  ${RED}[Q]uit${NC} - Stop script, set audio manually, then run script again"
    echo ""
    read -p "Enter choice (S/Q): " choice
    case "$choice" in
        [Qq]*)
            echo ""
            echo "Script stopped. Please:"
            echo "  1. Set audio input to 'Aggregate Device' manually"
            echo "  2. Set audio output to 'Multi-Output Device' manually"
            echo "  3. Run this script again"
            read -p "Press Enter to close..."
            exit 0
            ;;
        *)
            echo -e "${YELLOW}Continuing... Please set audio input manually.${NC}"
            ;;
    esac
fi

# =============================================================================
# Step 3: Switch Audio Output to Multi-Output Device
# =============================================================================
echo ""
echo -e "${BLUE}[3/4]${NC} Setting audio output to Multi-Output Device..."

AUDIO_OUTPUT_OK=false

if command -v SwitchAudioSource &> /dev/null; then
    if SwitchAudioSource -t output -s "Multi-Output Device" 2>/dev/null; then
        echo -e "${GREEN}✓ Output: Multi-Output Device${NC}"
        AUDIO_OUTPUT_OK=true
    fi
fi

if [ "$AUDIO_OUTPUT_OK" = false ]; then
    echo -e "${RED}✗ Could not automatically set audio output${NC}"
    echo ""
    echo "Manual steps required:"
    echo -e "  1. Open ${YELLOW}System Settings → Sound → Output${NC}"
    echo -e "  2. Select ${YELLOW}Multi-Output Device${NC}"
    echo ""
    echo "Options:"
    echo -e "  ${GREEN}[S]kip${NC} - Continue anyway, set audio output manually now"
    echo -e "  ${RED}[Q]uit${NC} - Stop script, set audio manually, then run script again"
    echo ""
    read -p "Enter choice (S/Q): " choice
    case "$choice" in
        [Qq]*)
            echo ""
            echo "Script stopped. Please:"
            echo "  1. Set audio output to 'Multi-Output Device' manually"
            echo "  2. Run this script again"
            read -p "Press Enter to close..."
            exit 0
            ;;
        *)
            echo -e "${YELLOW}Continuing... Please set audio output manually.${NC}"
            ;;
    esac
fi

# =============================================================================
# Step 4: Start Recording
# =============================================================================
echo ""
echo -e "${BLUE}[4/4]${NC} Starting meeting notes..."
echo ""

# Activate virtual environment
source venv/bin/activate || {
    echo -e "${RED}Error: Virtual environment not found${NC}"
    read -p "Press Enter to close..."
    exit 1
}

# Display banner
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                    Ready to Record!                          ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Prompt for meeting title
echo -e "${GREEN}Enter meeting title:${NC}"
read -p "> " meeting_title

# Use default title if empty
if [ -z "$meeting_title" ]; then
    meeting_title="Meeting $(date '+%Y-%m-%d %H:%M')"
fi

# Prompt for optional context
echo ""
echo -e "${GREEN}Additional context for notes (optional):${NC}"
echo -e "${YELLOW}Examples: 'Focus on action items for frontend team', 'Sprint planning - extract story points'${NC}"
read -p "> " meeting_context

echo ""
echo -e "${BLUE}Recording: ${meeting_title}${NC}"
if [ -n "$meeting_context" ]; then
    echo -e "${YELLOW}Context: ${meeting_context}${NC}"
fi
echo -e "${YELLOW}Press Ctrl+C to stop and generate notes.${NC}"
echo ""

# Run the application
if [ -n "$meeting_context" ]; then
    python -m src.main start --title "$meeting_title" --context "$meeting_context"
else
    python -m src.main start --title "$meeting_title"
fi

# =============================================================================
# Cleanup: Restore audio settings (optional)
# =============================================================================
echo ""
echo -e "${BLUE}Recording complete.${NC}"

if command -v SwitchAudioSource &> /dev/null; then
    echo ""
    read -p "Restore audio to regular speakers? (y/n): " restore
    if [[ "$restore" =~ ^[Yy]$ ]]; then
        # Try common speaker names
        SwitchAudioSource -t output -s "MacBook Pro Speakers" 2>/dev/null || \
        SwitchAudioSource -t output -s "Built-in Output" 2>/dev/null || \
        SwitchAudioSource -t output -s "External Headphones" 2>/dev/null
        echo -e "${GREEN}✓ Audio restored${NC}"
    fi
else
    echo ""
    echo -e "${YELLOW}Remember to restore your audio output to regular speakers.${NC}"
fi

echo ""
read -p "Press Enter to close..."
