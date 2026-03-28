#!/bin/bash
# GEORGIN Accounting System - Mac Launcher
cd "$(dirname "$0")"
echo "Starting GEORGIN Accounting System..."
echo "The app will ask for the GEORGIN data folder if GEORGIN_DATA is not set."
echo "Open browser at: http://localhost:5050"
echo "Press Ctrl+C to stop."
python3 app.py
