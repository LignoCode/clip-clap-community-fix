#!/usr/bin/env bash
set -euo pipefail

# clip-clap switches -- macOS dev setup.
# Finds (or installs) Python 3.10+, copies this app to a destination
# folder, creates a venv there, and installs requirements.
#
# Usage: ./install_mac.sh [destination folder]
#        defaults to ~/Applications/clipclap-switches

APP_NAME="clip-clap-community-fix"
DEFAULT_DEST="$HOME/Applications/clip-clap-community-fix"
DEST="${1:-$DEFAULT_DEST}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REQUIRED_MAJOR=3
REQUIRED_MINOR=10   # code uses `X | None` syntax, needs 3.10+

echo "== $APP_NAME setup =="

find_python() {
    for candidate in python3.13 python3.12 python3.11 python3.10 python3; do
        if command -v "$candidate" >/dev/null 2>&1; then
            ver=$("$candidate" -c 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")' 2>/dev/null) || continue
            major="${ver%%.*}"; minor="${ver##*.}"
            if [ "$major" -eq "$REQUIRED_MAJOR" ] && [ "$minor" -ge "$REQUIRED_MINOR" ]; then
                echo "$candidate"; return 0
            fi
        fi
    done
    return 1
}

PYTHON_BIN=""
if PYTHON_BIN=$(find_python); then
    echo "Found suitable Python: $PYTHON_BIN ($($PYTHON_BIN --version 2>&1))"
else
    echo "No Python $REQUIRED_MAJOR.$REQUIRED_MINOR+ found."
    if ! command -v brew >/dev/null 2>&1; then
        echo "Homebrew isn't installed either."
        echo "This will run Homebrew's official installer (https://brew.sh):"
        echo '  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
        read -p "Proceed? [y/N] " -n 1 -r; echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Aborting. Install Python $REQUIRED_MAJOR.$REQUIRED_MINOR+ yourself and re-run."
            exit 1
        fi
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        eval "$(/opt/homebrew/bin/brew shellenv 2>/dev/null || /usr/local/bin/brew shellenv)"
    fi
    echo "Installing Python via Homebrew..."
    brew install python@3.12
    PYTHON_BIN=$(find_python) || { echo "Still no suitable Python found. Aborting."; exit 1; }
    echo "Now using: $PYTHON_BIN ($($PYTHON_BIN --version 2>&1))"
fi

if [ "$SCRIPT_DIR" != "$DEST" ]; then
    echo "Installing to: $DEST"
    mkdir -p "$DEST"
    rsync -a --exclude 'venv' --exclude '__pycache__' --exclude '.git' --exclude 'build' --exclude 'dist' \
        "$SCRIPT_DIR"/ "$DEST"/
else
    echo "Already running from destination folder, skipping copy."
fi

cd "$DEST"
if [ ! -d venv ]; then
    echo "Creating virtual environment..."
    "$PYTHON_BIN" -m venv venv
fi
echo "Installing requirements..."
./venv/bin/pip install --upgrade pip -q
./venv/bin/pip install -r requirements.txt -q

echo
echo "Done. To run:"
echo "  cd \"$DEST\""
echo "  source venv/bin/activate"
echo "  python3 main.py"
echo
echo "First scan will prompt for Bluetooth permission. If it doesn't,"
echo "check System Settings > Privacy & Security > Bluetooth."
