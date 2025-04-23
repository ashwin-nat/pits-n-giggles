@echo off
setlocal

REM Check if Python is installed
where python > nul 2>nul
if %errorlevel% neq 0 (
    echo Python not found. Please install Python before running this application.
    exit /b 1
)

REM Check if virtual environment exists, create if not
if not exist "png-venv" (
    echo Creating virtual environment "png-venv"...
    python -m venv png-venv
)

REM Activate virtual environment
call png-venv\Scripts\activate

REM Upgrade pip and install prerequisites
python -m pip install --upgrade pip
pip install -r requirements.txt

REM Run the app module
python -O -m apps.backend.app

REM Pause to keep the command prompt window open
pause

endlocal
