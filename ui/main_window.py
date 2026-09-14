"""Main window: a Scan tab (radar + discovered list) and a Known switches
tab (persistent list with live status, on/off control)."""

import asyncio

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QListWidget, QListWidgetItem, QPushButton, QTableWidget,
    QTableWidgetItem, QInputDialog, QLabel, QHeaderView, QMessageBox,
)

from scanner import Scanner
from store import Store
from device import ClipClapDevice
from ui.radar_widget import RadarWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("clip-clap switches")
        self.resize(700, 520)

        self.store = Store()
        self.scanner = Scanner()
        self.scanner.device_found.connect(self._on_device_found)

        self.devices: dict[str, ClipClapDevice] = {}
        self._discovered: dict[str, str] = {}

        tabs = QTabWidget()
        tabs.addTab(self._build_scan_tab(), "Scan")
        tabs.addTab(self._build_known_tab(), "Known switches")
        self.setCentralWidget(tabs)

        self._load_known_switches()

    # ---------------- Scan tab ----------------

    def _build_scan_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.radar = RadarWidget()
        layout.addWidget(self.radar)

        layout.addWidget(QLabel("Double-click a device to add it to known switches:"))
        self.scan_list = QListWidget()
        self.scan_list.itemDoubleClicked.connect(self._add_from_scan)
        layout.addWidget(self.scan_list)

        btn_row = QHBoxLayout()
        self.scan_button = QPushButton("Start scanning")
        self.scan_button.clicked.connect(self._toggle_scan)
        btn_row.addWidget(self.scan_button)
        layout.addLayout(btn_row)

        return widget

    def _toggle_scan(self):
        if self.scan_button.text() == "Start scanning":
            self.scan_list.clear()
            self.radar.clear()
            self._discovered.clear()
            self.radar.start_sweep()
            self.scanner.start()
            self.scan_button.setText("Stop scanning")
        else:
            self.scanner.stop()
            self.radar.stop_sweep()
            self.scan_button.setText("Start scanning")

    def _on_device_found(self, address, name, rssi):
        self.radar.update_device(address, name, rssi)
        if address not in self._discovered:
            self._discovered[address] = name
            item = QListWidgetItem(f"{name or '(unnamed)'}    {address}    RSSI {rssi}")
            item.setData(Qt.UserRole, (address, name))
            self.scan_list.addItem(item)

    def _add_from_scan(self, item):
        address, name = item.data(Qt.UserRole)
        if address in self.devices:
            QMessageBox.information(self, "Already added", f"{name or address} is already in known switches.")
            return
        display_name, ok = QInputDialog.getText(
            self, "Name this switch", "Friendly name:", text=name or "clip-clap switch"
        )
        if not ok or not display_name.strip():
            return
        display_name = display_name.strip()
        self.store.add(address, display_name)
        self._add_known_device(address, display_name)

    # ---------------- Known switches tab ----------------

    def _build_known_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Name", "Status", "Power (W)", "Connection"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        self.on_button = QPushButton("Turn on")
        self.on_button.clicked.connect(lambda: self._switch_selected(True))
        self.off_button = QPushButton("Turn off")
        self.off_button.clicked.connect(lambda: self._switch_selected(False))
        self.remove_button = QPushButton("Remove")
        self.remove_button.clicked.connect(self._remove_selected)
        btn_row.addWidget(self.on_button)
        btn_row.addWidget(self.off_button)
        btn_row.addWidget(self.remove_button)
        layout.addLayout(btn_row)

        return widget

    def _load_known_switches(self):
        for mac, name, _last_power, _last_on in self.store.all():
            self._add_known_device(mac, name, start=True)

    def _add_known_device(self, mac: str, name: str, start: bool = True):
        if mac in self.devices:
            return
        dev = ClipClapDevice(mac, name)
        dev.status_changed.connect(lambda on, w, mac=mac: self._on_status(mac, on, w))
        dev.connection_changed.connect(lambda state, mac=mac: self._on_connection(mac, state))
        self.devices[mac] = dev

        row = self.table.rowCount()
        self.table.insertRow(row)
        name_item = QTableWidgetItem(name)
        name_item.setData(Qt.UserRole, mac)
        self.table.setItem(row, 0, name_item)
        self.table.setItem(row, 1, QTableWidgetItem("-"))
        self.table.setItem(row, 2, QTableWidgetItem("-"))
        self.table.setItem(row, 3, QTableWidgetItem("connecting"))

        if start:
            dev.start()

    def _row_for_mac(self, mac: str):
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0).data(Qt.UserRole) == mac:
                return row
        return None

    def _on_status(self, mac: str, is_on: bool, watts: float):
        self.store.update_status(mac, is_on, watts)
        row = self._row_for_mac(mac)
        if row is not None:
            self.table.item(row, 1).setText("ON" if is_on else "OFF")
            self.table.item(row, 2).setText(f"{watts:.3f}")

    def _on_connection(self, mac: str, state: str):
        row = self._row_for_mac(mac)
        if row is not None:
            self.table.item(row, 3).setText(state)

    def _selected_mac(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        return self.table.item(row, 0).data(Qt.UserRole)

    def _switch_selected(self, on: bool):
        mac = self._selected_mac()
        if mac is None:
            return
        dev = self.devices.get(mac)
        if dev is None:
            return
        if dev.client is None or not dev.client.is_connected:
            QMessageBox.warning(
                self, "Not connected",
                f"{dev.name} isn't connected yet (still \"{self._current_connection_text(mac)}\") "
                "-- wait for the Connection column to say 'connected' first.",
            )
            return
        asyncio.ensure_future(dev.switch(on))

    def _current_connection_text(self, mac: str) -> str:
        row = self._row_for_mac(mac)
        return self.table.item(row, 3).text() if row is not None else "unknown"

    def _remove_selected(self):
        mac = self._selected_mac()
        if mac is None:
            return
        row = self._row_for_mac(mac)
        dev = self.devices.pop(mac, None)
        if dev is not None:
            asyncio.ensure_future(dev.stop())
        if row is not None:
            self.table.removeRow(row)
        self.store.remove(mac)

    def closeEvent(self, event):
        for dev in self.devices.values():
            asyncio.ensure_future(dev.stop())
        self.scanner.stop()
        event.accept()
