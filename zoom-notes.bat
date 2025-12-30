@echo off
REM Zoom Notes Taker - Quick Launch Script for Windows
REM Double-click to start recording any meeting (prompts for title)

REM Project location (absolute path) - UPDATE THIS
set PROJECT_DIR=/Volumes/Development/zoom-notes-taker

REM Notes storage location - UPDATE THIS to your preferred path
set ZNT_NOTES_BASE=%USERPROFILE%\OneDrive\meeting-notes

REM Change to project directory
cd /d "%PROJECT_DIR%" || (
    echo Error: Project directory not found at %PROJECT_DIR%
    echo Please update PROJECT_DIR in this script.
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat || (
    echo Error: Virtual environment not found.
    echo Please run: cd %PROJECT_DIR% ^&^& python -m venv venv ^&^& pip install -e .
    pause
    exit /b 1
)

REM Display banner
echo.
echo ========================================
echo          Zoom Notes Taker
echo ========================================
echo.

REM Prompt for meeting title
set /p meeting_title="Enter meeting title: "

REM Use default title if empty
if "%meeting_title%"=="" (
    for /f "tokens=1-5 delims=/:. " %%a in ("%date% %time%") do set meeting_title=Meeting %%a-%%b-%%c %%d:%%e
)

echo.
echo Starting recording: %meeting_title%
echo Press Ctrl+C to stop and generate notes.
echo.

REM Run the application
python -m src.main start --title "%meeting_title%"

REM Keep window open after completion
echo.
pause
