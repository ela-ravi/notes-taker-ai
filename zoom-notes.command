#!/bin/bash
# Zoom Notes Taker - Quick Launch Script
# This script can be moved anywhere and run with a double-click

# Project location (absolute path)
PROJECT_DIR="/Volumes/Development/zoom-notes-taker"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Change to project directory
cd "$PROJECT_DIR" || {
    echo "Error: Project directory not found at $PROJECT_DIR"
    echo "Please update PROJECT_DIR in this script."
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
