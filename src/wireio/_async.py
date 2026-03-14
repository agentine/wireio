"""Async serial port wrapper using asyncio."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from wireio._base import SerialBase
from wireio._config import SerialConfig
from wireio._types import ByteSize, FlowControl, Parity, StopBits

if TYPE_CHECKING:
    from types import TracebackType


class AsyncSerial:
    """Async serial port using asyncio with run_in_executor for I/O.

    Usage::

        async with AsyncSerial("/dev/ttyUSB0", baudrate=9600) as port:
            await port.write(b"hello")
            data = await port.read(100)
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
        loop: asyncio.AbstractEventLoop | None = None,
    ) -> None:
        # Lazy import to get the right platform class
        from wireio import Serial

        self._serial: SerialBase = Serial(
            port,
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
            config=config,
        )
        self._loop = loop

    def _get_loop(self) -> asyncio.AbstractEventLoop:
        if self._loop is not None:
            return self._loop
        return asyncio.get_running_loop()

    @property
    def port(self) -> str:
        return self._serial.port

    @property
    def is_open(self) -> bool:
        return self._serial.is_open

    @property
    def baudrate(self) -> int:
        return self._serial.baudrate

    @property
    def config(self) -> SerialConfig:
        return self._serial.config

    async def open(self) -> None:
        """Open the serial port."""
        loop = self._get_loop()
        await loop.run_in_executor(None, self._serial.open)

    async def close(self) -> None:
        """Close the serial port."""
        loop = self._get_loop()
        await loop.run_in_executor(None, self._serial.close)

    async def read(self, size: int = 1) -> bytes:
        """Read up to *size* bytes."""
        loop = self._get_loop()
        return await loop.run_in_executor(None, self._serial.read, size)

    async def write(self, data: bytes | bytearray) -> int:
        """Write *data* to the port."""
        loop = self._get_loop()
        return await loop.run_in_executor(None, self._serial.write, data)

    async def flush(self) -> None:
        """Wait until all written data has been transmitted."""
        loop = self._get_loop()
        await loop.run_in_executor(None, self._serial.flush)

    async def read_until(self, delimiter: bytes = b"\n", size: int = 0) -> bytes:
        """Read until *delimiter* is found or *size* bytes have been read."""
        loop = self._get_loop()
        return await loop.run_in_executor(
            None, self._serial.read_until, delimiter, size
        )

    async def read_line(self) -> bytes:
        """Read a single line (ending with ``\\n``)."""
        loop = self._get_loop()
        return await loop.run_in_executor(None, self._serial.read_line)

    async def read_exactly(self, size: int) -> bytes:
        """Read exactly *size* bytes."""
        loop = self._get_loop()
        return await loop.run_in_executor(None, self._serial.read_exactly, size)

    async def configure(self, config: SerialConfig) -> None:
        """Apply a new configuration."""
        loop = self._get_loop()
        await loop.run_in_executor(None, self._serial.configure, config)

    async def __aenter__(self) -> AsyncSerial:
        await self.open()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()

    def __repr__(self) -> str:
        return f"AsyncSerial({self._serial!r})"
