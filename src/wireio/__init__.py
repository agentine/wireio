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
from wireio._types import ByteSize, FlowControl, Parity, StopBits

__all__ = [
    "Serial",
    "SerialConfig",
    "SerialError",
    "PortNotFoundError",
    "ConfigError",
    "SerialTimeoutError",
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
    raise SerialError(f"unsupported platform: {sys.platform}")


Serial = _get_serial_class()
