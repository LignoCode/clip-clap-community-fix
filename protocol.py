"""
Max Hauri clip-clap switch (CLIPMETER) BLE protocol.

Frame format for both commands (write) and responses (notify):
    [0x0F] [LEN] [CMD] [0x00] [...payload...] [CHECKSUM] [0xFF] [0xFF]

Reverse-engineered from the official com.mh.meter Android app.
"""

UUID_SERVICE = "0000fff0-0000-1000-8000-00805f9b34fb"
UUID_VERSION = "0000fff1-0000-1000-8000-00805f9b34fb"   # firmware upgrade data only
UUID_WRITE = "0000fff3-0000-1000-8000-00805f9b34fb"     # write commands here
UUID_NOTIFY = "0000fff4-0000-1000-8000-00805f9b34fb"    # responses arrive here

DEFAULT_PASSWORD = "0000"


def build_frame(cmd: int, payload: bytes) -> bytes:
    """Replicates Cmd.base() from the official app exactly."""
    frame = bytearray(len(payload) + 7)
    frame[0] = 0x0F
    frame[1] = len(payload) + 3
    frame[2] = cmd
    frame[3] = 0
    frame[4:4 + len(payload)] = payload
    checksum = 1
    for b in frame[2:len(frame) - 3]:
        checksum += b
    frame[len(frame) - 3] = checksum & 0xFF
    frame[len(frame) - 2] = 0xFF
    frame[len(frame) - 1] = 0xFF
    return bytes(frame)


def cmd_notify_meter() -> bytes:
    """Request current relay state + live power (cmd 4)."""
    return build_frame(4, bytes([0, 0]))


def cmd_switch(on: bool) -> bytes:
    """Switch the relay on/off (cmd 3)."""
    return build_frame(3, bytes([1 if on else 0, 0, 0]))


def cmd_check_password(pwd: str = DEFAULT_PASSWORD) -> bytes:
    """Password check, mirroring the app's checkPsw(meter, 0, pwd, '0000') call."""
    digits_new = [int(c) for c in pwd]
    digits_old = [int(c) for c in DEFAULT_PASSWORD]
    payload = bytes([0] + digits_new + digits_old)  # flag=0 -> "check", not "change"
    return build_frame(23, payload)


def parse_status(data: bytes):
    """
    Parse a cmd-4 (notifyMeter) response frame.
    Returns (is_on, watts) or None if this isn't a status frame.
    """
    if len(data) < 10 or data[0] != 0x0F or data[2] != 4:
        return None
    is_on = data[4] == 1
    raw_mw = (data[6] << 24) | (data[7] << 16) | (data[8] << 8) | data[9]
    return is_on, raw_mw / 1000.0
