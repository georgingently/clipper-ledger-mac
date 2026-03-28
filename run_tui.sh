#!/bin/bash
# GEORGIN Accounting System - Terminal (TUI) Launcher
cd "$(dirname "$0")"
echo "Starting GEORGIN Accounting System (Terminal Mode)..."
echo "Set GEORGIN_DATA before launch if you want to skip folder selection."
echo ""
python3 georgin_tui.py
