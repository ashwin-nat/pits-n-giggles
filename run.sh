#!/bin/bash

# Check if Python 3 is installed
if command -v python &> /dev/null; then
    echo "Python 3 is installed."
else
    echo "Python 3 is not installed. Please install Python 3 before proceeding."
    exit 1
fi

pip install -r requirements.txt
python app.py --packet-capture-mode disabled --telemetry-port 20777 --server-port 5000 --post-race-data-autosave --log-file png.log --udp-custom-action-code 12 --refresh-interval 100