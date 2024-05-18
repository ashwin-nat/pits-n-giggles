@echo off
setlocal

REM Check if Python is installed
where python > nul 2>nul
if %errorlevel% neq 0 (
    echo Python not found. Please install Python before running this application.
    exit /b 1
)

REM Install prerequisites using pip
pip install -r requirements.txt

REM Run the Python script
python app.py --packet-capture-mode disabled --telemetry-port 20777 --server-port 5000 --post-race-data-autosave --log-file png.log --udp-custom-action-code 12

REM Pause to keep the command prompt window open
pause

endlocal
