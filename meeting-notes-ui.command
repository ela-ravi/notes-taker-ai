#!/bin/bash
# Meeting Notes Taker - Desktop UI Launcher
# Double-click to open the graphical interface

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

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

# Activate virtual environment
source venv/bin/activate || {
    echo -e "${RED}Error: Virtual environment not found${NC}"
    echo "Please run bootstrap.sh first."
    read -p "Press Enter to close..."
    exit 1
}

# Check if customtkinter is installed
if ! python -c "import customtkinter" 2>/dev/null; then
    echo -e "${GREEN}Installing GUI dependencies...${NC}"
    pip install customtkinter Pillow -q
fi

# Run the UI application
python -m src.ui.app
