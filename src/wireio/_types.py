"""Serial port type enums."""

from __future__ import annotations

from enum import IntEnum


class Parity(IntEnum):
    """Parity checking mode."""

    NONE = 0
    EVEN = 1
    ODD = 2
    MARK = 3
    SPACE = 4


class StopBits(IntEnum):
    """Number of stop bits."""

    ONE = 1
    ONE_POINT_FIVE = 15  # 1.5 encoded as 15 to stay int
    TWO = 2


class ByteSize(IntEnum):
    """Number of data bits."""

    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8


class FlowControl(IntEnum):
    """Flow control mode."""

    NONE = 0
    HARDWARE = 1  # RTS/CTS
    SOFTWARE = 2  # XON/XOFF
