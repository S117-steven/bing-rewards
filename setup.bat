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
    echo         Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/5] Creating virtual environment...
if not exist ".venv" (
    python -m venv .venv
    echo      Created .venv
) else (
    echo      .venv already exists, skipping
)

echo [2/5] Installing dependencies...
.venv\Scripts\pip.exe install -r requirements.txt --quiet
echo      Done

echo [3/5] Auto-detecting Edge profile...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$username = $env:USERNAME; " ^
    "$edgePath = Join-Path $env:LOCALAPPDATA 'Microsoft\Edge\User Data'; " ^
    "Write-Output ''; " ^
    "Write-Output ('  Windows user: ' + $username); " ^
    "Write-Output ('  Edge data: ' + $edgePath); " ^
    "if (Test-Path $edgePath) { " ^
    "  Write-Output '  Edge data directory found!'; " ^
    "  $profiles = Get-ChildItem $edgePath -Directory | Where-Object { $_.Name -match '^Default$|^Profile \d+$' } | Select-Object -ExpandProperty Name; " ^
    "  Write-Output ('  Available profiles: ' + ($profiles -join ', ')); " ^
    "} else { " ^
    "  Write-Output '  WARNING: Edge data directory not found!'; " ^
    "  Write-Output '  Please make sure Edge browser is installed.'; " ^
    "}"

echo.
echo [4/5] Generating config.json...
if not exist "config.json" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "$username = $env:USERNAME; " ^
        "$edgePath = Join-Path $env:LOCALAPPDATA 'Microsoft\Edge\User Data'; " ^
        "$profile = 'Profile 1'; " ^
        "if (Test-Path $edgePath) { " ^
        "  $profiles = Get-ChildItem $edgePath -Directory | Where-Object { $_.Name -match '^Default$|^Profile \d+$' } | Select-Object -ExpandProperty Name; " ^
        "  if ($profiles -contains 'Default') { $profile = 'Default' } " ^
        "  elseif ($profiles.Count -gt 0) { $profile = $profiles[0] } " ^
        "} " ^
        "$edgePathEsc = $edgePath -replace '\\', '\\\\'; " ^
        "$json = @{" +
        "  python_exe = '.venv\\Scripts\\python.exe'; " ^
        "  edge_user_data_path = $edgePathEsc; " ^
        "  edge_source_profile = $profile; " ^
        "  search_count = 23 " ^
        "} | ConvertTo-Json -Depth 3; " ^
        "[System.IO.File]::WriteAllText('config.json', $json, [System.Text.Encoding]::UTF8); " ^
        "Write-Output ('  Created config.json'); " ^
        "Write-Output ('  Edge path: ' + $edgePath); " ^
        "Write-Output ('  Profile: ' + $profile)"
) else (
    echo      config.json already exists, skipping
)

echo.
echo [5/5] Creating desktop shortcut...
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
echo   What was done:
echo   - Virtual environment created
echo   - Dependencies installed
echo   - config.json generated (auto-detected)
echo   - Desktop shortcut created
echo.
echo   Next step: Double-click the desktop shortcut
echo              "Bing双号刷积分" to run!
echo.
echo   If the profile is wrong, edit config.json:
echo   %cd%\config.json
echo ========================================
pause
