#!/usr/bin/env bash
set -euo pipefail
# Builds the standalone .app bundle. Must be run ON macOS.

cd "$(dirname "${BASH_SOURCE[0]}")"

python3 -m venv build_venv
source build_venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
pip install py2app -q

rm -rf build dist
python3 setup.py py2app

deactivate

echo
echo "Built: dist/clip-clap-community-fix.app"
echo "Drag it into /Applications, or just double-click it from dist/ to test."
echo
echo "If it fails to launch or Bluetooth doesn't work, run it from Terminal"
echo "to see errors:"
echo "  dist/clip-clap\\ switches.app/Contents/MacOS/clip-clap\\ switches"
