#!/bin/bash
# GEORGIN Accounting System - Terminal (TUI) Launcher
cd "$(dirname "$0")"
export GEORGIN_DATA="/Volumes/Workspace/Projects/Clipper/GEORGIN tra"
echo "Starting GEORGIN Accounting System (Terminal Mode)..."
echo "Data: $GEORGIN_DATA"
echo ""
python3 georgin_tui.py
