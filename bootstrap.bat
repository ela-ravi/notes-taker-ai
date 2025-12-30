@echo off
REM Zoom Notes Taker - Bootstrap Script for Windows
REM Run this script once after cloning the repository

echo.
echo ================================================================
echo           Zoom Notes Taker - Bootstrap Setup
echo ================================================================
echo.

REM Get script directory
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

echo [1/6] Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.10+
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo OK: Python %PYTHON_VERSION%

echo.
echo [2/6] Creating virtual environment...
if exist "venv" (
    echo Virtual environment already exists
) else (
    python -m venv venv
    echo OK: Virtual environment created
)

echo.
echo [3/6] Activating virtual environment...
call venv\Scripts\activate.bat
echo OK: Activated

echo.
echo [4/6] Installing dependencies...
pip install --upgrade pip -q
pip install -e . -q
echo OK: Dependencies installed

echo.
echo [5/6] Configuring launch scripts...
REM Update PROJECT_DIR in all .bat files using PowerShell
for %%f in (*.bat) do (
    if not "%%f"=="bootstrap.bat" (
        powershell -Command "(Get-Content '%%f') -replace '^set PROJECT_DIR=.*', 'set PROJECT_DIR=%SCRIPT_DIR:\=\\%' | Set-Content '%%f'" >nul 2>&1
        echo   Updated: %%f
    )
)
echo OK: Scripts configured

echo.
echo [6/6] Setting up configuration...
if exist ".env" (
    echo .env file already exists (keeping existing)
) else (
    copy .env.example .env >nul
    echo OK: Created .env from .env.example
    echo    Edit .env to customize your settings
)

echo.
echo ================================================================
echo                    Setup Complete!
echo ================================================================
echo.
echo Next steps:
echo.
echo   1. Install and start Ollama:
echo      Download from: https://ollama.ai
echo      Then run: ollama serve
echo.
echo   2. Pull the LLM model:
echo      ollama pull llama3.1:8b
echo.
echo   3. Install VB-Cable (virtual audio):
echo      Download from: https://vb-audio.com/Cable/
echo.
echo   4. Configure audio (see README.md for detailed instructions):
echo      python -m src.main setup
echo.
echo   5. Edit .env if needed:
echo      notepad .env
echo.
echo   6. Start recording:
echo      Double-click zoom-notes.bat
echo.
pause
