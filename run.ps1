# Run Jira Alert Monitor
# Simple run script for Windows PowerShell

Write-Host "Starting Jira Alert Monitor..." -ForegroundColor Green

# Check if venv exists
if (-not (Test-Path ".\venv\Scripts\python.exe")) {
    Write-Host "Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run setup.ps1 first" -ForegroundColor Yellow
    exit 1
}

# Run the app
& ".\venv\Scripts\python.exe" main.py
