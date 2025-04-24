#!/bin/bash

# Move to the directory where the script is located
cd "$(dirname "$0")"

# Move to project root (one level up from /scripts)
cd ..

# Check if Python 3 is installed
if command -v python &> /dev/null; then
    echo "Python 3 is installed."
else
    echo "Python 3 is not installed. Please install Python 3 before proceeding."
    exit 1
fi

# Check if virtual environment exists, create if not
if [ ! -d "png-venv" ]; then
    echo "Creating virtual environment 'png-venv'..."
    python -m venv png-venv
fi

# Activate virtual environment
source png-venv/bin/activate

# Upgrade pip and install prerequisites
python -m pip install --upgrade pip
pip install -r requirements.txt

# Set PYTHONPATH and run the app as a module
PYTHONPATH="$(pwd)" python -O -m apps.save_viewer.telemetry_post_race_data_viewer
