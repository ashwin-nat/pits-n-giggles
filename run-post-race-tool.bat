@echo off
setlocal

REM Check if Python is installed
where python > nul 2>nul
if %errorlevel% neq 0 (
    echo Python not found. Please install Python before running this application.
    exit /b 1
)

REM Run the Python script
python utils/telemetry_post_race_data_viewer.py

REM Pause to keep the command prompt window open
pause

endlocal