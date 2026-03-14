"""Cross-platform serial port discovery."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass


@dataclass(slots=True)
class PortInfo:
    """Information about a serial port."""

    device: str
    name: str = ""
    description: str = ""
    hwid: str = ""
    vid: int | None = None
    pid: int | None = None
    serial_number: str = ""
    location: str = ""
    manufacturer: str = ""
    product: str = ""
    interface: str = ""


def list_ports() -> list[PortInfo]:
    """Enumerate available serial ports on the system."""
    if sys.platform == "linux":
        return _list_ports_linux()
    if sys.platform == "darwin":
        return _list_ports_macos()
    if sys.platform == "win32":
        return _list_ports_windows()
    return []


def _list_ports_linux() -> list[PortInfo]:
    """Enumerate serial ports on Linux via /sys/class/tty."""
    ports: list[PortInfo] = []

    tty_dir = "/sys/class/tty"
    if not os.path.isdir(tty_dir):
        return ports

    for name in sorted(os.listdir(tty_dir)):
        device_dir = os.path.join(tty_dir, name, "device")
        if not os.path.exists(device_dir):
            continue

        dev_path = f"/dev/{name}"
        if not os.path.exists(dev_path):
            continue

        info = PortInfo(device=dev_path, name=name)

        # Try to read driver info
        driver_link = os.path.join(device_dir, "driver")
        if os.path.islink(driver_link):
            info.description = os.path.basename(os.readlink(driver_link))

        # Try USB device info
        subsystem_link = os.path.join(device_dir, "subsystem")
        if os.path.islink(subsystem_link):
            subsystem = os.path.basename(os.readlink(subsystem_link))
            if subsystem == "usb-serial" or subsystem == "usb":
                _read_usb_info_linux(device_dir, info)

        ports.append(info)

    # Also check /dev/serial/by-id for symlinked USB serial devices
    serial_by_id = "/dev/serial/by-id"
    if os.path.isdir(serial_by_id):
        known_devices = {p.device for p in ports}
        for link_name in sorted(os.listdir(serial_by_id)):
            link_path = os.path.join(serial_by_id, link_name)
            real_path = os.path.realpath(link_path)
            if real_path not in known_devices and os.path.exists(real_path):
                ports.append(
                    PortInfo(
                        device=real_path,
                        name=os.path.basename(real_path),
                        description=link_name,
                    )
                )

    return ports


def _read_usb_info_linux(device_dir: str, info: PortInfo) -> None:
    """Read USB device info from sysfs."""
    # Walk up to find the USB device
    usb_dir = device_dir
    for _ in range(5):
        parent = os.path.dirname(usb_dir)
        if parent == usb_dir:
            break
        usb_dir = parent
        vid_path = os.path.join(usb_dir, "idVendor")
        if os.path.isfile(vid_path):
            break
    else:
        return

    info.vid = _read_hex(os.path.join(usb_dir, "idVendor"))
    info.pid = _read_hex(os.path.join(usb_dir, "idProduct"))
    info.serial_number = _read_text(os.path.join(usb_dir, "serial"))
    info.manufacturer = _read_text(os.path.join(usb_dir, "manufacturer"))
    info.product = _read_text(os.path.join(usb_dir, "product"))

    if info.vid is not None and info.pid is not None:
        sn = info.serial_number or ""
        info.hwid = f"USB VID:PID={info.vid:04X}:{info.pid:04X}"
        if sn:
            info.hwid += f" SER={sn}"


def _read_text(path: str) -> str:
    """Read a sysfs text file, returning empty string on failure."""
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return ""


def _read_hex(path: str) -> int | None:
    """Read a hex value from a sysfs file."""
    text = _read_text(path)
    if text:
        try:
            return int(text, 16)
        except ValueError:
            pass
    return None


def _list_ports_macos() -> list[PortInfo]:
    """Enumerate serial ports on macOS by scanning /dev."""
    ports: list[PortInfo] = []
    dev_dir = "/dev"

    for name in sorted(os.listdir(dev_dir)):
        if not (
            name.startswith("tty.") or name.startswith("cu.")
        ):
            continue
        dev_path = os.path.join(dev_dir, name)
        if not os.path.exists(dev_path):
            continue

        description = ""
        if "usbserial" in name or "usbmodem" in name:
            description = "USB Serial"
        elif "Bluetooth" in name:
            description = "Bluetooth Serial"

        ports.append(
            PortInfo(
                device=dev_path,
                name=name,
                description=description,
            )
        )

    return ports


def _list_ports_windows() -> list[PortInfo]:
    """Enumerate serial ports on Windows via registry."""
    ports: list[PortInfo] = []

    if sys.platform != "win32":
        return ports

    import winreg

    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"HARDWARE\DEVICEMAP\SERIALCOMM",
        )
        try:
            i = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, i)
                    ports.append(
                        PortInfo(
                            device=str(value),
                            name=str(value),
                            description=name,
                        )
                    )
                    i += 1
                except OSError:
                    break
        finally:
            winreg.CloseKey(key)
    except OSError:
        pass

    return ports
