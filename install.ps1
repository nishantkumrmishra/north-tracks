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

# 2. Install northtracks directly from PyPI
Write-Host "  ● Downloading and installing northtracks via pip..." -ForegroundColor Cyan
python -m pip install --upgrade northtracks --no-warn-script-location

# 3. Global Shim in WindowsApps (Instantly on PATH everywhere)
$shimPath = "$env:LOCALAPPDATA\Microsoft\WindowsApps\northtracks.cmd"
"@echo off`npython -m musicdl.cli %*" | Out-File -FilePath $shimPath -Encoding ascii

Write-Host ""
Write-Host "  ──────────────────────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host "  ✓ North Tracks installed successfully!" -ForegroundColor Green
Write-Host "    You can now open any PowerShell or CMD terminal and type:" -ForegroundColor White
Write-Host "    › northtracks" -ForegroundColor Cyan
Write-Host "  ──────────────────────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host ""
