@echo off
setlocal EnableDelayedExpansion
REM Meeting Notes Taker - Desktop UI Launcher
REM Double-click to open the graphical interface

REM Get script directory
set SCRIPT_DIR=%~dp0

REM Check for .env file
if not exist "%SCRIPT_DIR%.env" (
    echo Error: .env file not found
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
    echo Error: Project directory not found
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat || (
    echo Error: Virtual environment not found
    echo Please run bootstrap.bat first.
    pause
    exit /b 1
)

REM Check if customtkinter is installed, install if not
python -c "import customtkinter" 2>nul
if errorlevel 1 (
    echo Installing GUI dependencies...
    pip install customtkinter Pillow -q
)

REM Run the UI application
python -m src.ui.app
