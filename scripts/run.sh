#!/bin/bash

# Exit on error
set -e

# Move to the directory where the script is located (scripts/)
cd "$(dirname "$0")"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3 before proceeding."
    exit 1
fi

# Check if virtual environment exists in scripts/, create if not
if [ ! -d "png-venv" ]; then
    echo "Creating virtual environment 'png-venv' in scripts/..."
    python3 -m venv png-venv
fi

# Activate the virtual environment
source png-venv/bin/activate

# Upgrade pip and install requirements from project root
python -m pip install --upgrade pip
pip install -r ../requirements.txt

# Set PYTHONPATH to project root and run the app
PYTHONPATH="$(pwd)/.." python -O -m apps.launcher
