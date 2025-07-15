#!/bin/bash
# This script runs the Python script to reset the expansion database.

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Run the Python script
"$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/scripts/reset_expansion_db.py" "$@"
