@echo off
REM TNT Sports Standup - Quick Launch Script for Windows
REM Double-click to start recording TNT Sports standup meetings

REM Project location (absolute path) - UPDATE THIS
set PROJECT_DIR=C:\Development\zoom-notes-taker

REM Notes storage location - UPDATE THIS to your preferred path
set ZNT_NOTES_BASE=%USERPROFILE%\OneDrive\meeting-notes

REM Fixed meeting title
set MEETING_TITLE=TNT Sports Standup

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
echo        TNT Sports Standup Notes
echo ========================================
echo.

echo Starting recording: %MEETING_TITLE%
echo Press Ctrl+C to stop and generate notes.
echo.

REM Run the application with fixed title and default model
python -m src.main start --title "%MEETING_TITLE%" --default-model

REM Keep window open after completion
echo.
pause
