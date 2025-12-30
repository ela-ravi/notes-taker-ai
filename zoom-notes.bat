@echo off
setlocal EnableDelayedExpansion
REM Zoom Notes Taker - Quick Launch Script for Windows
REM Double-click to start recording any meeting (prompts for title)

REM Get script directory
set SCRIPT_DIR=%~dp0

REM Check for .env file
if not exist "%SCRIPT_DIR%.env" (
    echo Error: .env file not found at %SCRIPT_DIR%
    echo Please run bootstrap.bat first.
    pause
    exit /b 1
)

REM Load configuration from .env file
for /f "usebackq tokens=1,* delims==" %%a in ("%SCRIPT_DIR%.env") do (
    set "line=%%a"
    if not "!line:~0,1!"=="#" (
        if not "%%b"=="" (
            set "%%a=%%b"
        )
    )
)

REM Use ZNT_PROJECT_DIR from .env, or fall back to script location
if not defined ZNT_PROJECT_DIR set "ZNT_PROJECT_DIR=%SCRIPT_DIR:~0,-1%"
set "PROJECT_DIR=%ZNT_PROJECT_DIR%"

REM Change to project directory
cd /d "%PROJECT_DIR%" || (
    echo Error: Project directory not found at %PROJECT_DIR%
    echo Please run bootstrap.bat to configure.
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
