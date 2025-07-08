@echo off
setlocal enabledelayedexpansion

REM Move to the directory where this script is located (scripts/)
cd /d "%~dp0"

REM Check if Python is installed
where python > nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python before running this application.
    pause
    exit /b 1
)

REM Create virtual environment in scripts/ if it doesn't exist
if not exist "png-venv" (
    echo Creating virtual environment "png-venv"...
    python -m venv png-venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

REM Activate virtual environment
call png-venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)

REM Upgrade pip and install requirements
echo Installing/upgrading required packages...
python -m pip install --upgrade pip
pip install -r ..\requirements.txt

REM Run the app from project root
set PYTHONPATH=%cd%\..
python -O -m apps.launcher

REM Pause so user can read output
pause
endlocal
