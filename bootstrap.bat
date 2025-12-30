@echo off
REM Zoom Notes Taker - Bootstrap Script for Windows
REM Run this script once after cloning the repository

setlocal EnableDelayedExpansion

echo.
echo ================================================================
echo           Zoom Notes Taker - Bootstrap Setup
echo ================================================================
echo.

REM Get script directory
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

echo [1/5] Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.10+
    goto :error
)
for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo OK: Python %PYTHON_VERSION%

echo.
echo [2/5] Creating virtual environment...
if exist "venv" (
    echo Virtual environment already exists
) else (
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        goto :error
    )
    echo OK: Virtual environment created
)

echo.
echo [3/5] Activating virtual environment...
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment activation script not found
    goto :error
)
call venv\Scripts\activate.bat
echo OK: Activated

echo.
echo [4/5] Installing dependencies...
pip install --upgrade pip -q
if errorlevel 1 (
    echo ERROR: Failed to upgrade pip
    goto :error
)
pip install -e . -q
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    goto :error
)
echo OK: Dependencies installed

echo.
echo [5/5] Setting up configuration...
REM Create .env from template if it doesn't exist
if exist ".env" (
    echo .env file already exists (keeping existing settings)
) else (
    if not exist ".env.example" (
        echo ERROR: .env.example not found
        goto :error
    )
    copy .env.example .env >nul
    echo OK: Created .env from .env.example
)

REM Set project path in .env using PowerShell
set "ESCAPED_DIR=%SCRIPT_DIR:\=/%"
powershell -Command "$content = Get-Content '.env' -Raw; if ($content -match 'ZNT_PROJECT_DIR=') { $content = $content -replace 'ZNT_PROJECT_DIR=.*', 'ZNT_PROJECT_DIR=%ESCAPED_DIR%' } else { $content += \"`nZNT_PROJECT_DIR=%ESCAPED_DIR%\" }; Set-Content '.env' $content -NoNewline"
echo OK: Project path configured
echo    Edit .env to customize other settings

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
echo   3. Set up audio (installs VB-Cable):
echo      scripts\setup-audio-windows.bat
echo.
echo   4. Edit .env if needed:
echo      notepad .env
echo.
echo   5. Start recording:
echo      Double-click zoom-notes.bat
echo.
goto :end

:error
echo.
echo ================================================================
echo                    Setup FAILED!
echo ================================================================
echo Please check the error message above and try again.
pause
exit /b 1

:end
pause
endlocal
