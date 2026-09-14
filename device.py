"""
Manages one persistent BLE connection to a single clip-clap switch.
Auto-reconnects if the link drops, and polls status on an interval
while connected. Emits Qt signals so the UI updates itself.
"""

import asyncio

from PyQt5.QtCore import QObject, pyqtSignal
from bleak import BleakClient, BleakScanner

import protocol

POLL_INTERVAL_S = 5.0
RECONNECT_DELAY_S = 5.0
SCAN_TIMEOUT_S = 15.0
CONNECT_TIMEOUT_S = 15.0


class ClipClapDevice(QObject):
    status_changed = pyqtSignal(bool, float)     # is_on, watts
    connection_changed = pyqtSignal(str)          # "connecting" | "connected" | "disconnected" | "not found"

    def __init__(self, address: str, name: str = "CLIPMETER"):
        super().__init__()
        self.address = address
        self.name = name
        self.client: BleakClient | None = None
        self._running = False
        self._task: asyncio.Task | None = None

    def start(self):
        """Begin the background connect/poll/reconnect loop."""
        if self._task is None:
            self._running = True
            self._task = asyncio.ensure_future(self._run())

    async def stop(self):
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass
            self._task = None
        if self.client is not None and self.client.is_connected:
            await self.client.disconnect()
        self.client = None

    async def switch(self, on: bool):
        """Toggle the relay. Requires a prior successful password check,
        which this performs automatically before the first switch."""
        if self.client is None or not self.client.is_connected:
            return
        await self.client.write_gatt_char(
            protocol.UUID_WRITE, protocol.cmd_check_password(), response=False
        )
        await asyncio.sleep(0.3)
        await self.client.write_gatt_char(
            protocol.UUID_WRITE, protocol.cmd_switch(on), response=False
        )

    def _on_notify(self, _, data: bytearray):
        result = protocol.parse_status(bytes(data))
        if result is not None:
            is_on, watts = result
            self.status_changed.emit(is_on, watts)

    async def _run(self):
        while self._running:
            client = None
            try:
                self.connection_changed.emit("connecting")
                ble_device = await BleakScanner.find_device_by_address(
                    self.address, timeout=SCAN_TIMEOUT_S
                )
                if ble_device is None:
                    self.connection_changed.emit("not found")
                    await asyncio.sleep(RECONNECT_DELAY_S)
                    continue

                # Connect with an explicit timeout -- without this, a stuck
                # GATT handshake can hang indefinitely with no feedback at all.
                client = BleakClient(ble_device)
                await asyncio.wait_for(client.connect(), timeout=CONNECT_TIMEOUT_S)

                self.client = client
                await client.start_notify(protocol.UUID_NOTIFY, self._on_notify)
                self.connection_changed.emit("connected")

                while self._running and client.is_connected:
                    try:
                        await client.write_gatt_char(
                            protocol.UUID_WRITE,
                            protocol.cmd_notify_meter(),
                            response=False,
                        )
                    except Exception:
                        break
                    await asyncio.sleep(POLL_INTERVAL_S)

            except asyncio.CancelledError:
                raise
            except Exception as e:
                # Never swallow this silently -- print so it's visible in the
                # terminal instead of just freezing on "connecting" forever.
                print(f"[{self.name} / {self.address}] connection error: {e!r}")
            finally:
                if client is not None:
                    # Always attempt to disconnect, even if connect() never
                    # completed -- otherwise a timed-out attempt leaves BlueZ
                    # thinking a connection is still in progress, and every
                    # retry collides with it (org.bluez.Error.InProgress).
                    try:
                        await client.disconnect()
                    except Exception:
                        pass

            self.client = None
            if self._running:
                self.connection_changed.emit("disconnected")
                await asyncio.sleep(RECONNECT_DELAY_S)
