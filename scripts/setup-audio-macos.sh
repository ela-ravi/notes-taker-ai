#!/bin/bash
# macOS Audio Setup Script
# Automatically installs BlackHole and creates virtual audio devices

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║           macOS Audio Setup for Meeting Notes                ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}Error: This script is for macOS only.${NC}"
    exit 1
fi

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}[1/4]${NC} Checking Homebrew..."
if ! command -v brew &> /dev/null; then
    echo -e "${YELLOW}Homebrew not found. Installing...${NC}"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi
echo -e "${GREEN}✓ Homebrew installed${NC}"

echo ""
echo -e "${BLUE}[2/4]${NC} Checking BlackHole audio driver..."
if brew list blackhole-2ch &> /dev/null; then
    echo -e "${GREEN}✓ BlackHole already installed${NC}"
else
    echo -e "${YELLOW}Installing BlackHole 2ch...${NC}"
    brew install blackhole-2ch
    echo -e "${GREEN}✓ BlackHole installed${NC}"
    echo -e "${YELLOW}Note: You may need to allow the system extension in System Preferences → Security & Privacy${NC}"
    sleep 2
fi

echo ""
echo -e "${BLUE}[3/4]${NC} Creating virtual audio devices..."

# AppleScript to create Multi-Output Device and Aggregate Device
osascript <<'APPLESCRIPT'
-- Audio MIDI Setup automation
-- Creates Multi-Output Device and Aggregate Device for meeting recording

tell application "Audio MIDI Setup"
    activate
    delay 1
end tell

tell application "System Events"
    tell process "Audio MIDI Setup"
        -- Wait for window to be ready
        set maxWait to 10
        set waited to 0
        repeat until (exists window 1) or (waited > maxWait)
            delay 0.5
            set waited to waited + 0.5
        end repeat

        if not (exists window 1) then
            error "Audio MIDI Setup window did not open"
        end if

        -- Check if devices already exist
        set deviceList to name of every row of outline 1 of scroll area 1 of splitter group 1 of window 1

        set hasMultiOutput to false
        set hasAggregate to false

        repeat with deviceName in deviceList
            if deviceName as string contains "Multi-Output Device" then
                set hasMultiOutput to true
            end if
            if deviceName as string contains "Aggregate Device" then
                set hasAggregate to true
            end if
        end repeat

        -- Create Multi-Output Device if it doesn't exist
        if not hasMultiOutput then
            -- Click the + button and select Create Multi-Output Device
            click menu button 1 of window 1
            delay 0.5
            click menu item "Create Multi-Output Device" of menu 1 of menu button 1 of window 1
            delay 1
        end if

        -- Create Aggregate Device if it doesn't exist
        if not hasAggregate then
            -- Click the + button and select Create Aggregate Device
            click menu button 1 of window 1
            delay 0.5
            click menu item "Create Aggregate Device" of menu 1 of menu button 1 of window 1
            delay 1
        end if

    end tell
end tell

-- Quit Audio MIDI Setup
tell application "Audio MIDI Setup"
    quit
end tell
APPLESCRIPT

echo -e "${GREEN}✓ Virtual audio devices created${NC}"
echo ""
echo -e "${YELLOW}Important: Please manually configure the devices in Audio MIDI Setup:${NC}"
echo ""
echo "  1. Open Audio MIDI Setup (Spotlight → 'Audio MIDI Setup')"
echo ""
echo "  2. Configure Multi-Output Device:"
echo "     - Select 'Multi-Output Device' in the left panel"
echo "     - Check: Your speakers (e.g., MacBook Pro Speakers)"
echo "     - Check: BlackHole 2ch"
echo ""
echo "  3. Configure Aggregate Device:"
echo "     - Select 'Aggregate Device' in the left panel"
echo "     - Check: BlackHole 2ch"
echo "     - Check: Your microphone (e.g., MacBook Pro Microphone)"
echo ""

echo -e "${BLUE}[4/4]${NC} Updating .env configuration..."
ENV_FILE="$PROJECT_DIR/.env"
if [ -f "$ENV_FILE" ]; then
    if grep -q "^ZNT_AUDIO_DEVICE=" "$ENV_FILE"; then
        sed -i.bak "s|^ZNT_AUDIO_DEVICE=.*|ZNT_AUDIO_DEVICE=Aggregate Device|" "$ENV_FILE"
        rm -f "$ENV_FILE.bak"
    else
        echo "ZNT_AUDIO_DEVICE=Aggregate Device" >> "$ENV_FILE"
    fi
    echo -e "${GREEN}✓ .env updated with ZNT_AUDIO_DEVICE=Aggregate Device${NC}"
else
    echo -e "${YELLOW}Warning: .env file not found. Run bootstrap.sh first.${NC}"
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                    Audio Setup Complete!                     ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Open Audio MIDI Setup and verify device configuration"
echo "  2. In your meeting app, set Speaker to 'Multi-Output Device'"
echo "  3. Run: python -m src.main devices  to verify setup"
echo ""
