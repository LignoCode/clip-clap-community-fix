# clip-clap-community-fix

> [!CAUTION]
> **WARNING: THIS APP IS ALPHA NOT FOR GENERAL USE.**
> IT IS UNDER ACTIVE DEVELOPMENT AND CAN BREAK YOUR COMPUTER OR DEVICES CONNECTED TO THE SWITCH!

A small PyQt5 desktop app to discover, remember, and monitor Max Hauri
clip-clap switches (CLIPMETER) over Bluetooth LE -- live power readings and
on/off control, without needing the official phone app.

Not affiliated with Max Hauri. The BLE protocol was reverse-engineered from
the official `com.mh.meter` Android app for personal interoperability -- no
original source code is included here, just a clean Python reimplementation
of the wire protocol.

## Setup

    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

## Run

    python3 main.py

## Structure

- `protocol.py`  -- the wire protocol (frame format, checksum, command builders/parsers)
- `device.py`    -- ClipClapDevice: one persistent, self-reconnecting BLE connection with live status
- `scanner.py`   -- continuous BLE scan filtered to clip-clap devices
- `store.py`     -- SQLite persistence for the known-switches list (~/.config/clipclap-app/switches.db)
- `ui/main_window.py` -- Scan tab + Known switches tab
- `ui/radar_widget.py` -- radar-style live scan visualization

## Notes

- Switching a relay on/off automatically does a password check first
  (default password "0000"), matching what the real app does.
- Known switches reconnect automatically if the connection drops, and
  poll status every 5 seconds while connected.

## macOS

Two options, both untested on real hardware since this was built on Linux --
expect a round of debugging together against your actual Mac.

**Quick dev setup** (run via Terminal, needs Python installed):

    ./install_mac.sh [destination folder]

Finds or installs Python 3.10+ (via Homebrew), copies the app to the
destination (default `~/Applications/clipclap-switches`), and sets up a venv
with requirements installed.

**Standalone .app bundle** (no Python needed to *run* it afterward):

    ./build_mac_app.sh

Produces `dist/clip-clap switches.app` via py2app. PyQt5 apps can be finicky
to bundle correctly (Qt plugin paths in particular) -- if it fails or launches
to a blank/broken window, run the binary directly from Terminal (path printed
at the end of the build) to see the actual error, and we'll fix it from there.
If py2app proves too painful, PyInstaller is the usual fallback and worth
trying instead.

**Important:** macOS doesn't expose real Bluetooth MAC addresses to apps
(CoreBluetooth gives out random per-app UUIDs instead, for privacy). Known
switches saved on Linux won't resolve on macOS -- a macOS install needs its
own fresh scan and builds its own known-switches list. This is expected.
