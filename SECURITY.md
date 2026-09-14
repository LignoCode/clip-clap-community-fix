# Security Advisory

---

## **Overview**
`clip-clap-community-fix` is a community-driven desktop application for discovering, monitoring, and controlling **Max Hauri Clip-Clap Bluetooth LE switches (CLIPMETER)**. This advisory outlines security considerations and best practices for users.

---

## **Security Considerations**

### **Bluetooth LE (BLE) Communication**
- **Risk**: BLE communication in this implementation is **not encrypted by default**. An attacker with physical proximity could potentially eavesdrop on unencrypted BLE traffic between the app and your switches.
- **Mitigation**: Use this app only in **trusted environments** (e.g., home networks). Avoid public or high-risk areas where BLE traffic could be intercepted.

---

### **Default Password**
- **Risk**: The app uses the **default password (`"0000"`)** for Clip-Clap switches.
- **Mitigation**: If your device supports it, **change the default password** to a strong, unique value.

---
### **Local Data Storage**
- **Risk**: The app stores **known switch identifiers** in a local SQLite database (`~/.config/clipclap-app/switches.db`). This file contains Bluetooth addresses and device metadata but **no credentials or sensitive data**.
- **Mitigation**: The database is local to your machine. Delete it if no longer needed:
  ```bash
  rm ~/.config/clipclap-app/switches.db

# Known Vulnerabilities

| ID  | Issue                          | Impact                          | Severity | Status  | Workaround                          |
|-----|--------------------------------|---------------------------------|----------|---------|-------------------------------------|
| 1   | No BLE encryption              | Eavesdropping risk              | Medium   | Open    | Use in trusted environments only.   |
| 2   | Default password (`"0000"`)    | Unauthorized access risk       | Medium   | Open    | Change device password if possible.  |
| 3   | macOS random Bluetooth UUIDs   | Devices must be re-scanned      | Low      | Open    | Expected behavior; no workaround.    |
| 4   | Local SQLite database          | Local data exposure if shared   | Low      | Open    | Delete the file if no longer needed.|
