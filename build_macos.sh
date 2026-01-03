#!/bin/bash
# Build script for macOS Meeting Notes Taker app

set -e

echo "========================================"
echo "Building Meeting Notes Taker for macOS"
echo "========================================"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist

# Ensure dependencies are installed
echo "Checking dependencies..."
pip install pyinstaller pillow -q

# Build the app
echo "Building app bundle..."
pyinstaller MeetingNotes.spec --noconfirm

# Check if build succeeded
if [ -d "dist/Meeting Notes.app" ]; then
    echo ""
    echo "========================================"
    echo "Build successful!"
    echo "========================================"
    echo ""
    echo "App location: dist/Meeting Notes.app"
    echo ""
    echo "To test, run:"
    echo "  open 'dist/Meeting Notes.app'"
    echo ""
    echo "To create DMG installer, run:"
    echo "  ./create_dmg.sh"
    echo ""
else
    echo "Build failed!"
    exit 1
fi
