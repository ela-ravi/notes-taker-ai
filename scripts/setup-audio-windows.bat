@echo off
REM Windows Audio Setup Script
REM Checks for VB-Cable and configures audio settings

setlocal EnableDelayedExpansion

echo.
echo ================================================================
echo          Windows Audio Setup for Meeting Notes
echo ================================================================
echo.

REM Get script directory
set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%..

echo [1/3] Checking for VB-Cable installation...

REM Check if VB-Cable is installed by looking for the device
powershell -Command "Get-CimInstance Win32_SoundDevice | Where-Object { $_.Name -like '*VB-Audio*' -or $_.Name -like '*CABLE*' }" > nul 2>&1
if %errorlevel% equ 0 (
    echo OK: VB-Cable is installed
    goto :configure
)

REM Alternative check via registry
reg query "HKLM\SOFTWARE\VB-Audio" >nul 2>&1
if %errorlevel% equ 0 (
    echo OK: VB-Cable is installed
    goto :configure
)

REM VB-Cable not found
echo.
echo ================================================================
echo                  VB-Cable Not Found
echo ================================================================
echo.
echo VB-Cable virtual audio driver is required but not installed.
echo.
echo Please install VB-Cable manually:
echo.
echo   1. Download from: https://vb-audio.com/Cable/
echo.
echo   2. Extract the ZIP file
echo.
echo   3. Right-click VBCABLE_Setup_x64.exe and select "Run as administrator"
echo.
echo   4. Click "Install Driver" and follow the prompts
echo.
echo   5. Restart your computer if prompted
echo.
echo   6. Run this script again after installation
echo.
echo ================================================================
echo.

REM Try to open the download page
choice /C YN /M "Open VB-Cable download page in browser"
if %errorlevel% equ 1 (
    start https://vb-audio.com/Cable/
)

pause
exit /b 1

:configure
echo.
echo [2/3] Configuring audio settings...

REM Update .env file
set ENV_FILE=%PROJECT_DIR%\.env
if exist "%ENV_FILE%" (
    powershell -Command "$content = Get-Content '%ENV_FILE%' -Raw; if ($content -match 'ZNT_AUDIO_DEVICE=') { $content = $content -replace 'ZNT_AUDIO_DEVICE=.*', 'ZNT_AUDIO_DEVICE=CABLE Output (VB-Audio Virtual Cable)' } else { $content += \"`nZNT_AUDIO_DEVICE=CABLE Output (VB-Audio Virtual Cable)\" }; Set-Content '%ENV_FILE%' $content -NoNewline"
    echo OK: .env updated with VB-Cable device
) else (
    echo Warning: .env file not found. Run bootstrap.bat first.
)

echo.
echo [3/3] Audio configuration instructions...
echo.
echo ================================================================
echo                  Windows Audio Configuration
echo ================================================================
echo.
echo Configure Windows Sound Settings:
echo.
echo   Option A: Change system-wide output (affects all apps)
echo   --------------------------------------------------
echo   1. Right-click speaker icon in system tray
echo   2. Select "Sound settings"
echo   3. Under "Output", select "CABLE Input (VB-Audio Virtual Cable)"
echo.
echo   Option B: Change only in meeting app (recommended)
echo   --------------------------------------------------
echo   - Zoom: Settings ^> Audio ^> Speaker ^> CABLE Input
echo   - Teams: Settings ^> Devices ^> Speaker ^> CABLE Input
echo   - Slack: Settings ^> Audio ^& Video ^> Speaker ^> CABLE Input
echo   - Google Meet: Settings ^> Audio ^> Speaker ^> CABLE Input
echo.
echo   After recording, switch back to your regular speakers/headphones.
echo.
echo ================================================================
echo.
echo Setup complete! Run 'python -m src.main devices' to verify.
echo.
pause
