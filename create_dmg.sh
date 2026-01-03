#!/bin/bash
# Create DMG installer for Meeting Notes Taker

set -e

APP_NAME="Meeting Notes"
DMG_NAME="MeetingNotes-1.0.0"
VOLUME_NAME="Meeting Notes Installer"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if app exists
if [ ! -d "dist/${APP_NAME}.app" ]; then
    echo "Error: dist/${APP_NAME}.app not found!"
    echo "Run ./build_macos.sh first"
    exit 1
fi

echo "Creating DMG installer..."

# Create a temporary directory for DMG contents
DMG_TEMP="dist/dmg_temp"
rm -rf "$DMG_TEMP"
mkdir -p "$DMG_TEMP"

# Copy app to temp directory
cp -R "dist/${APP_NAME}.app" "$DMG_TEMP/"

# Create symlink to Applications folder
ln -s /Applications "$DMG_TEMP/Applications"

# Create README for the DMG
cat > "$DMG_TEMP/README.txt" << 'EOF'
Meeting Notes Taker - Installation

1. Drag "Meeting Notes" to the Applications folder
2. Open the app from Applications
3. If you see a security warning, go to:
   System Settings > Privacy & Security > Open Anyway

First Run Setup:
- The app will ask for microphone permissions
- Configure your audio input device in the app settings
- For best results, install BlackHole for audio routing:
  https://github.com/ExistentialAudio/BlackHole

Support: https://github.com/your-repo/issues
EOF

# Remove any existing DMG
rm -f "dist/${DMG_NAME}.dmg"

# Create DMG
hdiutil create -volname "$VOLUME_NAME" \
    -srcfolder "$DMG_TEMP" \
    -ov -format UDZO \
    "dist/${DMG_NAME}.dmg"

# Clean up
rm -rf "$DMG_TEMP"

echo ""
echo "========================================"
echo "DMG created successfully!"
echo "========================================"
echo ""
echo "Location: dist/${DMG_NAME}.dmg"
echo ""
echo "To test, run:"
echo "  open dist/${DMG_NAME}.dmg"
echo ""
