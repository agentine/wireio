"""Abstract base class for serial port backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from wireio._config import SerialConfig
from wireio._exceptions import ConfigError, SerialError
from wireio._types import ByteSize, FlowControl, Parity, StopBits

if TYPE_CHECKING:
    from types import TracebackType


class SerialBase(ABC):
    """Abstract base class for serial port implementations.

    Subclasses must implement: _open, _close, _read, _write, _flush,
    _in_waiting, _configure.
    """

    def __init__(
        self,
        port: str,
        baudrate: int = 9600,
        bytesize: ByteSize = ByteSize.EIGHT,
        parity: Parity = Parity.NONE,
        stopbits: StopBits = StopBits.ONE,
        timeout: float | None = None,
        write_timeout: float | None = None,
        flow_control: FlowControl = FlowControl.NONE,
        xonxoff: bool = False,
        rtscts: bool = False,
        dsrdtr: bool = False,
        inter_byte_timeout: float | None = None,
        config: SerialConfig | None = None,
    ) -> None:
        self._port = port
        self._is_open = False

        if config is not None:
            self._config = config
        else:
            self._config = SerialConfig(
                baudrate=baudrate,
                bytesize=bytesize,
                parity=parity,
                stopbits=stopbits,
                timeout=timeout,
                write_timeout=write_timeout,
                flow_control=flow_control,
                xonxoff=xonxoff,
                rtscts=rtscts,
                dsrdtr=dsrdtr,
                inter_byte_timeout=inter_byte_timeout,
            )
        self._config.validate()

    @property
    def port(self) -> str:
        """The serial port device path."""
        return self._port

    @property
    def is_open(self) -> bool:
        """Whether the port is currently open."""
        return self._is_open

    @property
    def config(self) -> SerialConfig:
        """Current serial port configuration."""
        return self._config

    @property
    def baudrate(self) -> int:
        return self._config.baudrate

    @property
    def bytesize(self) -> ByteSize:
        return self._config.bytesize

    @property
    def parity(self) -> Parity:
        return self._config.parity

    @property
    def stopbits(self) -> StopBits:
        return self._config.stopbits

    @property
    def timeout(self) -> float | None:
        return self._config.timeout

    @property
    def in_waiting(self) -> int:
        """Number of bytes in the input buffer."""
        self._check_open()
        return self._in_waiting()

    def open(self) -> None:
        """Open the serial port."""
        if self._is_open:
            raise SerialError(f"port {self._port} is already open")
        self._open()
        self._is_open = True

    def close(self) -> None:
        """Close the serial port."""
        if self._is_open:
            self._close()
            self._is_open = False

    def read(self, size: int = 1) -> bytes:
        """Read up to *size* bytes from the port.

        Returns fewer bytes if timeout expires before *size* bytes are available.
        """
        self._check_open()
        if size < 0:
            raise ConfigError("read size must be non-negative")
        if size == 0:
            return b""
        return self._read(size)

    def write(self, data: bytes | bytearray) -> int:
        """Write *data* to the port. Returns number of bytes written."""
        self._check_open()
        return self._write(bytes(data))

    def flush(self) -> None:
        """Wait until all written data has been transmitted."""
        self._check_open()
        self._flush()

    def read_until(self, delimiter: bytes = b"\n", size: int = 0) -> bytes:
        """Read until *delimiter* is found or *size* bytes have been read.

        A *size* of 0 means no limit.
        """
        self._check_open()
        buf = bytearray()
        while True:
            if size > 0 and len(buf) >= size:
                break
            chunk = self._read(1)
            if not chunk:
                break
            buf.extend(chunk)
            if buf.endswith(delimiter):
                break
        return bytes(buf)

    def read_line(self) -> bytes:
        """Read a single line (ending with ``\\n``)."""
        return self.read_until(b"\n")

    def read_exactly(self, size: int) -> bytes:
        """Read exactly *size* bytes, blocking until all are received."""
        self._check_open()
        buf = bytearray()
        while len(buf) < size:
            chunk = self._read(size - len(buf))
            if not chunk:
                break
            buf.extend(chunk)
        return bytes(buf)

    def configure(self, config: SerialConfig) -> None:
        """Apply a new configuration to an open port."""
        config.validate()
        self._config = config
        if self._is_open:
            self._configure()

    def __enter__(self) -> SerialBase:
        self.open()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()

    def __repr__(self) -> str:
        state = "open" if self._is_open else "closed"
        return (
            f"{self.__class__.__name__}(port={self._port!r}, "
            f"baudrate={self._config.baudrate}, state={state})"
        )

    def _check_open(self) -> None:
        if not self._is_open:
            raise SerialError("port is not open")

    # --- Abstract methods for backends ---

    @abstractmethod
    def _open(self) -> None: ...

    @abstractmethod
    def _close(self) -> None: ...

    @abstractmethod
    def _read(self, size: int) -> bytes: ...

    @abstractmethod
    def _write(self, data: bytes) -> int: ...

    @abstractmethod
    def _flush(self) -> None: ...

    @abstractmethod
    def _in_waiting(self) -> int: ...

    @abstractmethod
    def _configure(self) -> None: ...
