"""
py2app build config -- produces a standalone macOS .app bundle
that doesn't require Python pre-installed on the machine that runs it.

MUST be built on macOS itself (py2app cannot cross-compile from Linux).

Build:
    ./build_mac_app.sh

Output:
    dist/clip-clap switches.app
"""

from setuptools import setup

APP = ['main.py']
OPTIONS = {
    'argv_emulation': False,
    'packages': ['bleak', 'qasync'],
    'plist': {
        'CFBundleName': 'clip-clap-community-fix',
        'CFBundleDisplayName': 'clip-clap-community-fix',
        'CFBundleIdentifier': 'local.clipclapcommunityfix',
        'CFBundleVersion': '0.1.0',
        'CFBundleShortVersionString': '0.1.0',
        'LSMinimumSystemVersion': '11.0',
        # Required for macOS to show the Bluetooth permission prompt at all --
        # without these keys CoreBluetooth silently returns no devices.
        'NSBluetoothAlwaysUsageDescription':
            'This app connects to your clip-clap switches over Bluetooth '
            'to read live power and switch them on/off.',
        'NSBluetoothPeripheralUsageDescription':
            'This app connects to your clip-clap switches over Bluetooth '
            'to read live power and switch them on/off.',
    },
}

setup(
    app=APP,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
