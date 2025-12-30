#!/bin/bash
# Zoom Notes Taker - Bootstrap Script
# Run this script once after cloning the repository

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║           Zoom Notes Taker - Bootstrap Setup                 ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}[1/5]${NC} Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    echo -e "${RED}Error: Python 3.10+ required. Found: $PYTHON_VERSION${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python $PYTHON_VERSION${NC}"

echo ""
echo -e "${BLUE}[2/5]${NC} Creating virtual environment..."
if [ -d "venv" ]; then
    echo -e "${YELLOW}  Virtual environment already exists${NC}"
else
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

echo ""
echo -e "${BLUE}[3/5]${NC} Activating virtual environment..."
source venv/bin/activate
echo -e "${GREEN}✓ Activated${NC}"

echo ""
echo -e "${BLUE}[4/5]${NC} Installing dependencies..."
pip install --upgrade pip -q
pip install -e . -q
echo -e "${GREEN}✓ Dependencies installed${NC}"

echo ""
echo -e "${BLUE}[5/5]${NC} Setting up configuration..."
# Create .env from template if it doesn't exist
if [ -f ".env" ]; then
    echo -e "${YELLOW}  .env file already exists (keeping existing settings)${NC}"
else
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env from .env.example${NC}"
fi

# Set project path in .env
if grep -q "^ZNT_PROJECT_DIR=" .env; then
    sed -i.bak "s|^ZNT_PROJECT_DIR=.*|ZNT_PROJECT_DIR=$SCRIPT_DIR|" .env
    rm -f .env.bak
else
    echo "ZNT_PROJECT_DIR=$SCRIPT_DIR" >> .env
fi
echo -e "${GREEN}✓ Project path: $SCRIPT_DIR${NC}"
echo -e "${YELLOW}  → Edit .env to customize other settings${NC}"

# Make scripts executable
chmod +x *.command 2>/dev/null || true
chmod +x scripts/*.sh 2>/dev/null || true

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                    Setup Complete!                           ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo ""
echo "  1. Install and start Ollama:"
echo -e "     ${YELLOW}brew install ollama${NC}"
echo -e "     ${YELLOW}ollama serve${NC}"
echo ""
echo "  2. Pull the LLM model:"
echo -e "     ${YELLOW}ollama pull llama3.1:8b${NC}"
echo ""
echo "  3. Set up audio (installs BlackHole & creates virtual devices):"
echo -e "     ${YELLOW}./scripts/setup-audio-macos.sh${NC}"
echo ""
echo "  4. Edit .env if needed:"
echo -e "     ${YELLOW}nano .env${NC}"
echo ""
echo "  5. Start recording:"
echo -e "     ${YELLOW}./zoom-notes.command${NC}  (or double-click in Finder)"
echo ""
