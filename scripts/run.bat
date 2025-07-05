@echo off
setlocal

REM Move to the directory where this script is located
cd /d "%~dp0"

REM Move to project root (one level up from /scripts)
cd ..

REM Check if Python is installed
where python > nul 2>nul
if %errorlevel% neq 0 (
    echo Python not found. Please install Python before running this application.
    pause
    exit /b 1
)

REM Check if virtual environment exists; create if not
if not exist "png-venv" (
    echo Creating virtual environment "png-venv"...
    python -m venv png-venv
)

REM Activate virtual environment
call png-venv\Scripts\activate

REM Upgrade pip and install required packages
echo Installing/upgrading required packages...
python -m pip install --upgrade pip
pip install -r requirements.txt

REM Run the app with correct PYTHONPATH
set PYTHONPATH=%cd%
python -O -m apps.backend

REM Keep window open after running
pause

endlocal
