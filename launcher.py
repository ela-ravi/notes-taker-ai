#!/usr/bin/env python3
"""
Launcher script for Meeting Notes Taker.
This is the entry point for PyInstaller to properly handle imports.
"""

import sys
import os
import multiprocessing

# Required for frozen apps on macOS to prevent double-launch
if getattr(sys, 'frozen', False):
    multiprocessing.freeze_support()
    # Use 'spawn' method on macOS for frozen apps
    if sys.platform == 'darwin':
        multiprocessing.set_start_method('spawn', force=True)

# Ensure the src directory is in the path
if getattr(sys, 'frozen', False):
    # Running as compiled
    app_dir = os.path.dirname(sys.executable)
    # For macOS .app bundle, go up to Resources
    if 'Contents/MacOS' in app_dir:
        resources_dir = os.path.join(os.path.dirname(app_dir), 'Resources')
        if os.path.exists(resources_dir):
            app_dir = resources_dir
    # Add the app directory to path
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)
else:
    # Running as script
    app_dir = os.path.dirname(os.path.abspath(__file__))
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)

# Load environment variables from .env if it exists
from dotenv import load_dotenv

# Try multiple locations for .env (home directory first for bundled app)
env_locations = [
    os.path.join(os.path.expanduser('~'), '.meeting_notes.env'),
    os.path.join(app_dir, '.env'),
    os.path.join(os.path.dirname(app_dir), '.env'),
    '.env',
]

env_loaded = False
for env_path in env_locations:
    if os.path.exists(env_path):
        load_dotenv(env_path)
        env_loaded = True
        print(f"[Launcher] Loaded config from: {env_path}")
        break

if not env_loaded:
    print("[Launcher] Warning: No .env file found. Please create ~/.meeting_notes.env")

# Now import and run the app
from src.ui.app import main

if __name__ == "__main__":
    main()
