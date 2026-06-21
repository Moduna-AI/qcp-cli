# Installer for qcp (Query Companion) on Windows.
# Usage (PowerShell):
#   irm https://raw.githubusercontent.com/Moduna-AI/qcp-cli/main/scripts/install.ps1 | iex

$ErrorActionPreference = "Stop"

function Write-Info($msg) { Write-Host $msg -ForegroundColor Cyan }
function Write-Ok($msg) { Write-Host $msg -ForegroundColor Green }
function Write-Err($msg) { Write-Host $msg -ForegroundColor Red }

if (-not (Get-Command python -ErrorAction SilentlyContinue) -and
    -not (Get-Command python3 -ErrorAction SilentlyContinue)) {
    Write-Err "Python was not found on PATH. Install Python 3.14+ from https://www.python.org/downloads/ and re-run this script."
    exit 1
}

$python = if (Get-Command python3 -ErrorAction SilentlyContinue) { "python3" } else { "python" }

Write-Info "Installing qcp via pip..."

if (Get-Command pipx -ErrorAction SilentlyContinue) {
    pipx install qcp
} else {
    & $python -m pip install --user --upgrade qcp
}

if (-not (Get-Command qcp -ErrorAction SilentlyContinue)) {
    Write-Info "Note: 'qcp' isn't on PATH yet. Make sure your Python Scripts folder is on PATH, e.g.:"
    Write-Host '  $env:Path += ";$env:APPDATA\Python\Python3xx\Scripts"'
}

Write-Ok "qcp installed! Run 'qcp init' to connect a database, then 'qcp auth' to add your Gemini key."
