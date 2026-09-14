"""Continuous BLE scan for clip-clap switches, filtered by their service UUID."""

import asyncio

from PyQt5.QtCore import QObject, pyqtSignal
from bleak import BleakScanner

import protocol


class Scanner(QObject):
    device_found = pyqtSignal(str, str, int)  # address, name, rssi

    def __init__(self):
        super().__init__()
        self._scanner: BleakScanner | None = None
        self._running = False

    def _detection_callback(self, ble_device, advertisement_data):
        uuids = [u.lower() for u in (advertisement_data.service_uuids or [])]
        name = ble_device.name or advertisement_data.local_name or ""
        looks_like_clipclap = (
            protocol.UUID_SERVICE in uuids
            or "clip-clap" in name.lower()
            or "clipmeter" in name.lower()
        )
        if looks_like_clipclap:
            rssi = advertisement_data.rssi if advertisement_data.rssi is not None else -100
            self.device_found.emit(ble_device.address, name, rssi)

    def start(self):
        if self._running:
            return
        self._running = True
        asyncio.ensure_future(self._start_async())

    async def _start_async(self):
        try:
            self._scanner = BleakScanner(detection_callback=self._detection_callback)
            await self._scanner.start()
        except Exception as e:
            print(f"Scan failed to start (is Bluetooth on?): {e}")
            self._running = False

    def stop(self):
        if not self._running:
            return
        self._running = False
        asyncio.ensure_future(self._stop_async())

    async def _stop_async(self):
        if self._scanner is not None:
            await self._scanner.stop()
            self._scanner = None
