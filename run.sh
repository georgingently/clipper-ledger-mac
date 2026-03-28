#!/bin/bash
# GEORGIN Accounting System - Mac Launcher
cd "$(dirname "$0")"
export GEORGIN_DATA="/Volumes/Workspace/Projects/Clipper/GEORGIN tra"
echo "Starting GEORGIN Accounting System..."
echo "Data: $GEORGIN_DATA"
echo "Open browser at: http://localhost:5050"
echo "Press Ctrl+C to stop."
python3 app.py
