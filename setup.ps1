# Setup Script for Windows
# Run this in PowerShell (Run as Administrator)

Write-Host "=== Jira Alert Monitor Setup ===" -ForegroundColor Green

# Enable script execution for current session
Write-Host "Enabling script execution..." -ForegroundColor Yellow
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

# Create virtual environment
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
python -m venv venv

# Activate and install
Write-Host "Installing dependencies..." -ForegroundColor Yellow
& ".\venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\venv\Scripts\pip.exe" install -r requirements.txt

Write-Host ""
Write-Host "=== Setup Completed! ===" -ForegroundColor Green
Write-Host ""
Write-Host "To run the app:" -ForegroundColor Cyan
Write-Host "  .\venv\Scripts\python.exe main.py" -ForegroundColor White
Write-Host ""
Write-Host "Or use the run script:" -ForegroundColor Cyan
Write-Host "  .\run.ps1" -ForegroundColor White
