"""SQLite persistence for known switches."""

import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path.home() / ".config" / "clipclap-app" / "switches.db"


class Store:
    def __init__(self, path: Path = DEFAULT_DB_PATH):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(path))
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS switches (
                mac TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                last_power REAL DEFAULT 0,
                last_on INTEGER DEFAULT 0
            )
            """
        )
        self.conn.commit()

    def add(self, mac: str, name: str):
        self.conn.execute(
            "INSERT OR IGNORE INTO switches (mac, name) VALUES (?, ?)", (mac, name)
        )
        self.conn.commit()

    def remove(self, mac: str):
        self.conn.execute("DELETE FROM switches WHERE mac=?", (mac,))
        self.conn.commit()

    def rename(self, mac: str, name: str):
        self.conn.execute("UPDATE switches SET name=? WHERE mac=?", (name, mac))
        self.conn.commit()

    def update_status(self, mac: str, is_on: bool, watts: float):
        self.conn.execute(
            "UPDATE switches SET last_on=?, last_power=? WHERE mac=?",
            (int(is_on), watts, mac),
        )
        self.conn.commit()

    def all(self):
        """Returns list of (mac, name, last_power, last_on)."""
        cur = self.conn.execute(
            "SELECT mac, name, last_power, last_on FROM switches ORDER BY name"
        )
        return cur.fetchall()
