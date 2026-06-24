@echo off
chcp 65001 >nul
echo ========================================
echo   Bing Rewards - Setup
echo ========================================
echo.

cd /d "%~dp0"

:: Check Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.10+ first.
    pause
    exit /b 1
)

echo [1/4] Creating virtual environment...
if not exist ".venv" (
    python -m venv .venv
    echo      Created .venv
) else (
    echo      .venv already exists, skipping
)

echo [2/4] Installing dependencies...
.venv\Scripts\pip.exe install -r requirements.txt --quiet
echo      Done

echo [3/4] Creating config.json...
if not exist "config.json" (
    copy config.example.json config.json >nul
    echo      Created config.json - PLEASE EDIT IT with your paths!
    echo      File: %cd%\config.json
) else (
    echo      config.json already exists, skipping
)

echo [4/4] Creating desktop shortcut...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$desktop = [Environment]::GetFolderPath('Desktop'); " ^
    "$sh = New-Object -ComObject WScript.Shell; " ^
    "$lnk = $sh.CreateShortcut((Join-Path $desktop 'Bing双号刷积分.lnk')); " ^
    "$lnk.TargetPath = '%cd%\launcher.bat'; " ^
    "$lnk.WorkingDirectory = '%cd%'; " ^
    "$lnk.Description = 'Bing Rewards'; " ^
    "$lnk.IconLocation = 'shell32.dll,175'; " ^
    "$lnk.WindowStyle = 7; " ^
    "$lnk.Save(); " ^
    "Write-Output '      Shortcut created on Desktop'"

echo.
echo ========================================
echo   Setup complete!
echo.
echo   Next steps:
echo   1. Edit config.json with your Edge profile path
echo   2. Double-click the desktop shortcut to run
echo ========================================
pause
