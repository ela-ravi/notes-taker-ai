#!/bin/bash
# Zoom Notes Taker - Quick Launch Script
# Double-click to run from Finder

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get project directory from script location
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Source .env for configuration
if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
else
    echo -e "${RED}Error: .env file not found at $SCRIPT_DIR${NC}"
    echo "Please run bootstrap.sh first."
    read -p "Press Enter to close..."
    exit 1
fi

# Use ZNT_PROJECT_DIR from .env, or fall back to script location
PROJECT_DIR="${ZNT_PROJECT_DIR:-$SCRIPT_DIR}"

# Change to project directory
cd "$PROJECT_DIR" || {
    echo -e "${RED}Error: Project directory not found at $PROJECT_DIR${NC}"
    echo "Please run bootstrap.sh to configure."
    read -p "Press Enter to close..."
    exit 1
}

# Activate virtual environment
source venv/bin/activate || {
    echo "Error: Virtual environment not found."
    echo "Please run: cd $PROJECT_DIR && python3 -m venv venv && pip install -e ."
    read -p "Press Enter to close..."
    exit 1
}

# Display banner
echo -e "${BLUE}"
echo "╔══════════════════════════════════════╗"
echo "║       Zoom Notes Taker               ║"
echo "╚══════════════════════════════════════╝"
echo -e "${NC}"

# Prompt for meeting title
echo -e "${GREEN}Enter meeting title:${NC}"
read -p "> " meeting_title

# Use default title if empty
if [ -z "$meeting_title" ]; then
    meeting_title="Meeting $(date '+%Y-%m-%d %H:%M')"
fi

echo ""
echo -e "${BLUE}Starting recording: ${meeting_title}${NC}"
echo "Press Ctrl+C to stop and generate notes."
echo ""

# Run the application
python -m src.main start --title "$meeting_title"

# Keep terminal open after completion
echo ""
read -p "Press Enter to close..."
