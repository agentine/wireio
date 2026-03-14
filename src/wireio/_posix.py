"""POSIX serial port backend using termios and fcntl."""

from __future__ import annotations

import errno
import fcntl
import os
import select
import struct
import termios
from typing import ClassVar

from wireio._base import SerialBase
from wireio._exceptions import ConfigError, PortNotFoundError, SerialError
from wireio._types import ByteSize, Parity, StopBits


class PosixSerial(SerialBase):
    """Serial port implementation for POSIX systems (Linux, macOS)."""

    _BAUDRATE_MAP: ClassVar[dict[int, int]] = {
        50: termios.B50,
        75: termios.B75,
        110: termios.B110,
        134: termios.B134,
        150: termios.B150,
        200: termios.B200,
        300: termios.B300,
        600: termios.B600,
        1200: termios.B1200,
        1800: termios.B1800,
        2400: termios.B2400,
        4800: termios.B4800,
        9600: termios.B9600,
        19200: termios.B19200,
        38400: termios.B38400,
        57600: termios.B57600,
        115200: termios.B115200,
        230400: termios.B230400,
    }

    _BYTESIZE_MAP: ClassVar[dict[ByteSize, int]] = {
        ByteSize.FIVE: termios.CS5,
        ByteSize.SIX: termios.CS6,
        ByteSize.SEVEN: termios.CS7,
        ByteSize.EIGHT: termios.CS8,
    }

    def __init__(self, *args: object, **kwargs: object) -> None:
        self._fd: int = -1
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]

    def _open(self) -> None:
        try:
            self._fd = os.open(
                self._port,
                os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK,
            )
        except FileNotFoundError:
            raise PortNotFoundError(f"port not found: {self._port}") from None
        except PermissionError:
            raise PortNotFoundError(
                f"permission denied: {self._port}"
            ) from None
        except OSError as e:
            raise SerialError(f"failed to open {self._port}: {e}") from e

        try:
            # Clear O_NONBLOCK after open (we handle timeouts ourselves)
            flags = fcntl.fcntl(self._fd, fcntl.F_GETFL)
            fcntl.fcntl(self._fd, fcntl.F_SETFL, flags & ~os.O_NONBLOCK)
        except OSError as e:
            os.close(self._fd)
            self._fd = -1
            raise SerialError(f"failed to configure {self._port}: {e}") from e

        try:
            self._configure()
        except Exception:
            os.close(self._fd)
            self._fd = -1
            raise

    def _close(self) -> None:
        if self._fd >= 0:
            try:
                os.close(self._fd)
            except OSError:
                pass
            self._fd = -1

    def _read(self, size: int) -> bytes:
        timeout = self._config.timeout
        if timeout == 0:
            # Non-blocking
            return self._read_nonblocking(size)
        if timeout is None:
            # Blocking forever
            return self._read_blocking(size)
        # Timed read
        return self._read_timed(size, timeout)

    def _read_nonblocking(self, size: int) -> bytes:
        try:
            ready, _, _ = select.select([self._fd], [], [], 0)
            if not ready:
                return b""
            return os.read(self._fd, size)
        except OSError as e:
            if e.errno == errno.EAGAIN:
                return b""
            raise SerialError(f"read error: {e}") from e

    def _read_blocking(self, size: int) -> bytes:
        buf = bytearray()
        while len(buf) < size:
            try:
                chunk = os.read(self._fd, size - len(buf))
                if not chunk:
                    break
                buf.extend(chunk)
            except OSError as e:
                if e.errno == errno.EAGAIN:
                    select.select([self._fd], [], [])
                    continue
                raise SerialError(f"read error: {e}") from e
        return bytes(buf)

    def _read_timed(self, size: int, timeout: float) -> bytes:
        buf = bytearray()
        remaining = timeout
        while len(buf) < size and remaining > 0:
            import time

            start = time.monotonic()
            try:
                ready, _, _ = select.select([self._fd], [], [], remaining)
                if not ready:
                    break
                chunk = os.read(self._fd, size - len(buf))
                if not chunk:
                    break
                buf.extend(chunk)
            except OSError as e:
                if e.errno == errno.EAGAIN:
                    pass
                else:
                    raise SerialError(f"read error: {e}") from e
            elapsed = time.monotonic() - start
            remaining -= elapsed
        return bytes(buf)

    def _write(self, data: bytes) -> int:
        try:
            return os.write(self._fd, data)
        except OSError as e:
            raise SerialError(f"write error: {e}") from e

    def _flush(self) -> None:
        try:
            termios.tcdrain(self._fd)
        except termios.error as e:
            raise SerialError(f"flush error: {e}") from e

    def _in_waiting(self) -> int:
        try:
            buf = fcntl.ioctl(self._fd, termios.FIONREAD, b"\x00\x00\x00\x00")
            result: int = struct.unpack("i", buf)[0]
            return result
        except OSError as e:
            raise SerialError(f"in_waiting error: {e}") from e

    def _configure(self) -> None:
        try:
            attrs = termios.tcgetattr(self._fd)
        except termios.error as e:
            raise SerialError(f"failed to get terminal attributes: {e}") from e

        iflag, oflag, cflag, lflag, ispeed, ospeed, cc = attrs

        # Start with raw mode
        iflag &= ~(
            termios.IGNBRK
            | termios.BRKINT
            | termios.PARMRK
            | termios.ISTRIP
            | termios.INLCR
            | termios.IGNCR
            | termios.ICRNL
        )
        oflag &= ~termios.OPOST
        lflag &= ~(
            termios.ECHO
            | termios.ECHONL
            | termios.ICANON
            | termios.ISIG
            | termios.IEXTEN
        )
        cflag &= ~(termios.CSIZE | termios.PARENB)
        cflag |= termios.CLOCAL | termios.CREAD

        # Baudrate
        baud = self._get_baudrate()
        ispeed = baud
        ospeed = baud

        # Byte size
        cflag &= ~termios.CSIZE
        cflag |= self._BYTESIZE_MAP[self._config.bytesize]

        # Parity
        cflag = self._apply_parity(cflag, iflag)
        iflag = self._apply_parity_iflag(iflag)

        # Stop bits
        if self._config.stopbits == StopBits.TWO:
            cflag |= termios.CSTOPB
        else:
            cflag &= ~termios.CSTOPB

        # Flow control
        iflag, cflag = self._apply_flow_control(iflag, cflag)

        # VMIN / VTIME for read behavior
        cc[termios.VMIN] = 0 if self._config.timeout is not None else 1
        cc[termios.VTIME] = 0

        try:
            termios.tcsetattr(
                self._fd,
                termios.TCSANOW,
                [iflag, oflag, cflag, lflag, ispeed, ospeed, cc],
            )
        except termios.error as e:
            raise SerialError(f"failed to set terminal attributes: {e}") from e

    def _get_baudrate(self) -> int:
        baud = self._BAUDRATE_MAP.get(self._config.baudrate)
        if baud is None:
            raise ConfigError(
                f"unsupported baudrate: {self._config.baudrate}"
            )
        return baud

    def _apply_parity(self, cflag: int, iflag: int) -> int:
        match self._config.parity:
            case Parity.NONE:
                cflag &= ~(termios.PARENB | termios.PARODD)
            case Parity.EVEN:
                cflag |= termios.PARENB
                cflag &= ~termios.PARODD
            case Parity.ODD:
                cflag |= termios.PARENB | termios.PARODD
            case Parity.MARK:
                cflag |= termios.PARENB | termios.PARODD
                if hasattr(termios, "CMSPAR"):
                    cflag |= termios.CMSPAR
            case Parity.SPACE:
                cflag |= termios.PARENB
                cflag &= ~termios.PARODD
                if hasattr(termios, "CMSPAR"):
                    cflag |= termios.CMSPAR
        return cflag

    def _apply_parity_iflag(self, iflag: int) -> int:
        if self._config.parity == Parity.NONE:
            iflag &= ~(termios.INPCK | termios.ISTRIP)
        else:
            iflag |= termios.INPCK
        return iflag

    def _apply_flow_control(
        self, iflag: int, cflag: int
    ) -> tuple[int, int]:
        # XON/XOFF
        if self._config.xonxoff or self._config.flow_control == 2:
            iflag |= termios.IXON | termios.IXOFF
        else:
            iflag &= ~(termios.IXON | termios.IXOFF)

        # RTS/CTS
        if self._config.rtscts or self._config.flow_control == 1:
            cflag |= termios.CRTSCTS
        else:
            cflag &= ~termios.CRTSCTS

        return iflag, cflag
