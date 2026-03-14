"""wireio — Modern Python serial port library."""

from __future__ import annotations

import sys

from wireio._config import SerialConfig
from wireio._exceptions import (
    ConfigError,
    PortNotFoundError,
    SerialError,
    SerialTimeoutError,
)
from wireio._ports import PortInfo, list_ports
from wireio._types import ByteSize, FlowControl, Parity, StopBits

__all__ = [
    "Serial",
    "SerialConfig",
    "SerialError",
    "PortNotFoundError",
    "ConfigError",
    "SerialTimeoutError",
    "PortInfo",
    "list_ports",
    "Parity",
    "StopBits",
    "ByteSize",
    "FlowControl",
]

__version__ = "0.1.0"


def _get_serial_class() -> type:
    if sys.platform in ("linux", "darwin", "freebsd"):
        from wireio._posix import PosixSerial

        return PosixSerial
    if sys.platform == "win32":
        from wireio._win32 import Win32Serial

        return Win32Serial
    raise SerialError(f"unsupported platform: {sys.platform}")


Serial = _get_serial_class()
