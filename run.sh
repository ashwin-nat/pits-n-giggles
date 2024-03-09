#!/bin/bash

# Check if Python 3 is installed
if command -v python3 &> /dev/null; then
    echo "Python 3 is installed."
else
    echo "Python 3 is not installed. Please install Python 3 before proceeding."
    exit 1
fi

python3 app.py --packet-capture-mode disabled --telemetry-port 20777 --server-port 5000