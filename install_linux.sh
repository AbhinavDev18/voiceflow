#!/usr/bin/env bash
set -euo pipefail

sudo apt update
sudo apt install -y     python3-venv     python3-dev     portaudio19-dev     xwayland     libxcb-cursor0     ydotool     ydotoold

sudo usermod -aG input "$USER"

echo
echo "System packages installed."
echo "Log out and back in once so the input-group membership is refreshed."
echo "Then create the Python environment with:"
echo "  python3 -m venv .venv"
echo "  .venv/bin/python -m pip install -r requirements.txt"
