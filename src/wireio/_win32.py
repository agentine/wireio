"""Windows serial port backend using ctypes and kernel32."""

from __future__ import annotations

import ctypes
import ctypes.wintypes
import sys
from typing import ClassVar

from wireio._base import SerialBase
from wireio._exceptions import ConfigError, PortNotFoundError, SerialError
from wireio._types import Parity, StopBits

if sys.platform != "win32":
    raise ImportError("_win32 module is only available on Windows")

kernel32 = ctypes.windll.kernel32

# Windows constants
GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
OPEN_EXISTING = 3
FILE_ATTRIBUTE_NORMAL = 0x80
FILE_FLAG_OVERLAPPED = 0x40000000
INVALID_HANDLE_VALUE = ctypes.wintypes.HANDLE(-1).value

# Purge flags
PURGE_TXCLEAR = 0x0004
PURGE_RXCLEAR = 0x0008

# Error codes
ERROR_IO_PENDING = 997

# Modem status bits
MS_CTS_ON = 0x0010
MS_DSR_ON = 0x0020
MS_RING_ON = 0x0040
MS_RLSD_ON = 0x0080

# Parity constants
NOPARITY = 0
ODDPARITY = 1
EVENPARITY = 2
MARKPARITY = 3
SPACEPARITY = 4

# Stop bits constants
ONESTOPBIT = 0
ONE5STOPBITS = 1
TWOSTOPBITS = 2


class DCB(ctypes.Structure):
    """Win32 DCB (Device Control Block) structure."""

    _fields_ = [
        ("DCBlength", ctypes.wintypes.DWORD),
        ("BaudRate", ctypes.wintypes.DWORD),
        ("fBitFields", ctypes.wintypes.DWORD),
        ("wReserved", ctypes.wintypes.WORD),
        ("XonLim", ctypes.wintypes.WORD),
        ("XoffLim", ctypes.wintypes.WORD),
        ("ByteSize", ctypes.wintypes.BYTE),
        ("Parity", ctypes.wintypes.BYTE),
        ("StopBits", ctypes.wintypes.BYTE),
        ("XonChar", ctypes.c_char),
        ("XoffChar", ctypes.c_char),
        ("ErrorChar", ctypes.c_char),
        ("EofChar", ctypes.c_char),
        ("EvtChar", ctypes.c_char),
        ("wReserved1", ctypes.wintypes.WORD),
    ]


class COMMTIMEOUTS(ctypes.Structure):
    """Win32 COMMTIMEOUTS structure."""

    _fields_ = [
        ("ReadIntervalTimeout", ctypes.wintypes.DWORD),
        ("ReadTotalTimeoutMultiplier", ctypes.wintypes.DWORD),
        ("ReadTotalTimeoutConstant", ctypes.wintypes.DWORD),
        ("WriteTotalTimeoutMultiplier", ctypes.wintypes.DWORD),
        ("WriteTotalTimeoutConstant", ctypes.wintypes.DWORD),
    ]


class COMSTAT(ctypes.Structure):
    """Win32 COMSTAT structure."""

    _fields_ = [
        ("fBitFields", ctypes.wintypes.DWORD),
        ("cbInQue", ctypes.wintypes.DWORD),
        ("cbOutQue", ctypes.wintypes.DWORD),
    ]


class Win32Serial(SerialBase):
    """Serial port implementation for Windows using ctypes."""

    _PARITY_MAP: ClassVar[dict[Parity, int]] = {
        Parity.NONE: NOPARITY,
        Parity.ODD: ODDPARITY,
        Parity.EVEN: EVENPARITY,
        Parity.MARK: MARKPARITY,
        Parity.SPACE: SPACEPARITY,
    }

    _STOPBITS_MAP: ClassVar[dict[StopBits, int]] = {
        StopBits.ONE: ONESTOPBIT,
        StopBits.ONE_POINT_FIVE: ONE5STOPBITS,
        StopBits.TWO: TWOSTOPBITS,
    }

    def __init__(self, *args: object, **kwargs: object) -> None:
        self._handle: int = INVALID_HANDLE_VALUE
        super().__init__(*args, **kwargs)

    def _open(self) -> None:
        port_name = self._port
        if not port_name.startswith("\\\\.\\"):
            port_name = f"\\\\.\\{port_name}"

        handle = kernel32.CreateFileW(
            port_name,
            GENERIC_READ | GENERIC_WRITE,
            0,
            None,
            OPEN_EXISTING,
            FILE_ATTRIBUTE_NORMAL,
            None,
        )
        if handle == INVALID_HANDLE_VALUE:
            err = ctypes.GetLastError()
            if err == 2:  # ERROR_FILE_NOT_FOUND
                raise PortNotFoundError(f"port not found: {self._port}")
            if err == 5:  # ERROR_ACCESS_DENIED
                raise PortNotFoundError(f"access denied: {self._port}")
            raise SerialError(
                f"failed to open {self._port}: Windows error {err}"
            )
        self._handle = handle

        try:
            self._configure()
        except Exception:
            kernel32.CloseHandle(self._handle)
            self._handle = INVALID_HANDLE_VALUE
            raise

    def _close(self) -> None:
        if self._handle != INVALID_HANDLE_VALUE:
            kernel32.CloseHandle(self._handle)
            self._handle = INVALID_HANDLE_VALUE

    def _read(self, size: int) -> bytes:
        buf = ctypes.create_string_buffer(size)
        bytes_read = ctypes.wintypes.DWORD(0)
        ok = kernel32.ReadFile(
            self._handle,
            buf,
            size,
            ctypes.byref(bytes_read),
            None,
        )
        if not ok:
            raise SerialError(
                f"read error: Windows error {ctypes.GetLastError()}"
            )
        return buf.raw[: bytes_read.value]

    def _write(self, data: bytes) -> int:
        bytes_written = ctypes.wintypes.DWORD(0)
        ok = kernel32.WriteFile(
            self._handle,
            data,
            len(data),
            ctypes.byref(bytes_written),
            None,
        )
        if not ok:
            raise SerialError(
                f"write error: Windows error {ctypes.GetLastError()}"
            )
        return bytes_written.value

    def _flush(self) -> None:
        if not kernel32.FlushFileBuffers(self._handle):
            raise SerialError(
                f"flush error: Windows error {ctypes.GetLastError()}"
            )

    def _in_waiting(self) -> int:
        errors = ctypes.wintypes.DWORD(0)
        comstat = COMSTAT()
        if not kernel32.ClearCommError(
            self._handle, ctypes.byref(errors), ctypes.byref(comstat)
        ):
            raise SerialError(
                f"in_waiting error: Windows error {ctypes.GetLastError()}"
            )
        return comstat.cbInQue

    def _configure(self) -> None:
        # Set DCB
        dcb = DCB()
        dcb.DCBlength = ctypes.sizeof(DCB)

        if not kernel32.GetCommState(self._handle, ctypes.byref(dcb)):
            raise SerialError(
                f"GetCommState failed: Windows error {ctypes.GetLastError()}"
            )

        dcb.BaudRate = self._config.baudrate
        dcb.ByteSize = self._config.bytesize.value
        dcb.Parity = self._PARITY_MAP[self._config.parity]
        dcb.StopBits = self._STOPBITS_MAP[self._config.stopbits]

        # Flow control bits
        flags = 0x00000001  # fBinary = 1
        if self._config.parity != Parity.NONE:
            flags |= 0x00000002  # fParity
        if self._config.rtscts or self._config.flow_control == 1:
            flags |= 0x00002000  # fRtsControl = RTS_CONTROL_HANDSHAKE
            flags |= 0x00000004  # fOutxCtsFlow
        if self._config.xonxoff or self._config.flow_control == 2:
            flags |= 0x00000100  # fOutX
            flags |= 0x00000200  # fInX
        if self._config.dsrdtr:
            flags |= 0x00000008  # fOutxDsrFlow
            flags |= 0x00000020  # fDtrControl = DTR_CONTROL_HANDSHAKE
        dcb.fBitFields = flags

        if not kernel32.SetCommState(self._handle, ctypes.byref(dcb)):
            raise ConfigError(
                f"SetCommState failed: Windows error {ctypes.GetLastError()}"
            )

        # Set timeouts
        timeouts = COMMTIMEOUTS()
        timeout = self._config.timeout
        if timeout is None:
            # Blocking read
            timeouts.ReadIntervalTimeout = 0
            timeouts.ReadTotalTimeoutMultiplier = 0
            timeouts.ReadTotalTimeoutConstant = 0
        elif timeout == 0:
            # Non-blocking read
            timeouts.ReadIntervalTimeout = 0xFFFFFFFF  # MAXDWORD
            timeouts.ReadTotalTimeoutMultiplier = 0
            timeouts.ReadTotalTimeoutConstant = 0
        else:
            timeouts.ReadIntervalTimeout = 0
            timeouts.ReadTotalTimeoutMultiplier = 0
            timeouts.ReadTotalTimeoutConstant = max(1, int(timeout * 1000))

        write_timeout = self._config.write_timeout
        if write_timeout is not None:
            timeouts.WriteTotalTimeoutMultiplier = 0
            timeouts.WriteTotalTimeoutConstant = max(
                1, int(write_timeout * 1000)
            )

        if not kernel32.SetCommTimeouts(
            self._handle, ctypes.byref(timeouts)
        ):
            raise ConfigError(
                f"SetCommTimeouts failed: Windows error {ctypes.GetLastError()}"
            )
