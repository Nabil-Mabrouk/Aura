#!/bin/bash

# A robust script to activate a virtual environment and start a uvicorn agent server.

# Check for exactly two arguments: the application directory and the port.
if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <app_directory> <port>" >&2
  exit 1
fi

APP_DIR="$1"
PORT="$2"

# --- Virtual Environment Activation ---
# Go up one level from the script's location to the project root to find the venv.
# This assumes the script is run from the project root.
VENV_PATH="./venv"

if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
  # For Windows (Git Bash)
  ACTIVATE_SCRIPT="$VENV_PATH/Scripts/activate"
else
  # For Linux/macOS
  ACTIVATE_SCRIPT="$VENV_PATH/bin/activate"
fi

if [ ! -f "$ACTIVATE_SCRIPT" ]; then
    echo "Error: Virtual environment activation script not found at $ACTIVATE_SCRIPT" >&2
    exit 1
fi

echo "AGENT_RUNNER: Activating venv from $ACTIVATE_SCRIPT..."
source "$ACTIVATE_SCRIPT" || { echo "Error: Failed to activate virtual environment." >&2; exit 1; }
echo "AGENT_RUNNER: Virtual environment activated."

# --- Run the Uvicorn Server ---
echo "AGENT_RUNNER: Starting uvicorn for 'main:app' in '$APP_DIR' on port '$PORT'..."
uvicorn main:app --host 127.0.0.1 --port "$PORT" --app-dir "$APP_DIR" || { echo "Error: Failed to run uvicorn." >&2; exit 1; }