# North Tracks - 1-Click PowerShell Installer
Write-Host ""
Write-Host "  ● Installing North Tracks 320k Studio Audio Downloader..." -ForegroundColor Cyan

# 1. Check Python
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "  ✕ Python is not found on your system." -ForegroundColor Red
    Write-Host "    Installing Python via winget..." -ForegroundColor Yellow
    winget install -e --id Python.Python.3.11 --accept-package-agreements --accept-source-agreements
    $env:PATH = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
}

# 2. Project Directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $scriptDir -or -not (Test-Path "$scriptDir\pyproject.toml")) {
    $targetDir = "$env:USERPROFILE\.northtracks\source"
    if (-not (Test-Path $targetDir)) {
        New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
        Write-Host "  ● Downloading North Tracks repository..." -ForegroundColor Cyan
        git clone https://github.com/nishantkumrmishra/north-tracks.git $targetDir
    } else {
        git -C $targetDir pull
    }
    $scriptDir = $targetDir
}

# 3. Pip Install
Write-Host "  ● Installing dependencies and registering CLI command..." -ForegroundColor Cyan
python -m pip install -e $scriptDir --no-warn-script-location

# 4. Global Shim in WindowsApps (Instantly on PATH everywhere)
$shimPath = "$env:LOCALAPPDATA\Microsoft\WindowsApps\northtracks.cmd"
"@echo off`npython -m musicdl.cli %*" | Out-File -FilePath $shimPath -Encoding ascii

Write-Host ""
Write-Host "  ──────────────────────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host "  ✓ North Tracks installed successfully!" -ForegroundColor Green
Write-Host "    You can now open any PowerShell or CMD terminal and type:" -ForegroundColor White
Write-Host "    › northtracks" -ForegroundColor Cyan
Write-Host "  ──────────────────────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host ""
