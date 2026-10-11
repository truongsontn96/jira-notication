@echo off
REM Build script for Windows

echo ================================================
echo Building Jira Alert Monitor to .exe
echo ================================================

REM Activate virtual environment (if exists)
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Build with PyInstaller
pyinstaller --onefile ^
    --windowed ^
    --name "JiraAlertMonitor" ^
    --icon=icon.ico ^
    --add-data "config;config" ^
    --hidden-import=pygame ^
    --hidden-import=PyQt5 ^
    main.py

echo.
echo ================================================
echo Build completed!
echo EXE file: dist\JiraAlertMonitor.exe
echo ================================================
pause
