"""Tests for AsyncSerial using PTY pairs."""

from __future__ import annotations

import asyncio
import os
import sys

import pytest

from wireio import AsyncSerial, SerialConfig, SerialError

pytestmark = pytest.mark.skipif(
    sys.platform == "win32", reason="PTY tests only run on POSIX"
)


@pytest.fixture()
def pty_pair() -> tuple[int, int]:
    """Create a PTY pair and return (master, slave) file descriptors."""
    master, slave = os.openpty()
    yield master, slave  # type: ignore[misc]
    for fd in (master, slave):
        try:
            os.close(fd)
        except OSError:
            pass


@pytest.fixture()
def pty_port(pty_pair: tuple[int, int]) -> str:
    """Return the slave PTY device path."""
    _, slave = pty_pair
    return os.ttyname(slave)


class TestAsyncSerialOpen:
    @pytest.mark.asyncio
    async def test_async_context_manager(self, pty_port: str) -> None:
        async with AsyncSerial(pty_port, baudrate=9600, timeout=0.1) as port:
            assert port.is_open
        assert not port.is_open

    @pytest.mark.asyncio
    async def test_async_open_close(self, pty_port: str) -> None:
        port = AsyncSerial(pty_port, baudrate=9600, timeout=0.1)
        assert not port.is_open
        await port.open()
        assert port.is_open
        await port.close()
        assert not port.is_open

    @pytest.mark.asyncio
    async def test_port_property(self, pty_port: str) -> None:
        port = AsyncSerial(pty_port, baudrate=9600, timeout=0.1)
        assert port.port == pty_port

    @pytest.mark.asyncio
    async def test_baudrate_property(self, pty_port: str) -> None:
        port = AsyncSerial(pty_port, baudrate=115200, timeout=0.1)
        assert port.baudrate == 115200

    @pytest.mark.asyncio
    async def test_config_property(self, pty_port: str) -> None:
        cfg = SerialConfig(baudrate=38400, timeout=0.1)
        port = AsyncSerial(pty_port, config=cfg)
        assert port.config is cfg

    @pytest.mark.asyncio
    async def test_repr(self, pty_port: str) -> None:
        port = AsyncSerial(pty_port, baudrate=9600, timeout=0.1)
        assert "AsyncSerial" in repr(port)


class TestAsyncSerialReadWrite:
    @pytest.mark.asyncio
    async def test_write_read(self, pty_pair: tuple[int, int]) -> None:
        master, slave = pty_pair
        port_path = os.ttyname(slave)
        async with AsyncSerial(port_path, baudrate=9600, timeout=1.0) as port:
            await port.write(b"hello")
            await asyncio.sleep(0.05)
            data = os.read(master, 100)
            assert data == b"hello"

    @pytest.mark.asyncio
    async def test_read_from_master(
        self, pty_pair: tuple[int, int]
    ) -> None:
        master, slave = pty_pair
        port_path = os.ttyname(slave)
        async with AsyncSerial(port_path, baudrate=9600, timeout=1.0) as port:
            os.write(master, b"world")
            data = await port.read(5)
            assert data == b"world"

    @pytest.mark.asyncio
    async def test_read_until(self, pty_pair: tuple[int, int]) -> None:
        master, slave = pty_pair
        port_path = os.ttyname(slave)
        async with AsyncSerial(port_path, baudrate=9600, timeout=1.0) as port:
            os.write(master, b"line1\nline2\n")
            data = await port.read_until(b"\n")
            assert data == b"line1\n"

    @pytest.mark.asyncio
    async def test_read_line(self, pty_pair: tuple[int, int]) -> None:
        master, slave = pty_pair
        port_path = os.ttyname(slave)
        async with AsyncSerial(port_path, baudrate=9600, timeout=1.0) as port:
            os.write(master, b"data\n")
            data = await port.read_line()
            assert data == b"data\n"

    @pytest.mark.asyncio
    async def test_read_exactly(self, pty_pair: tuple[int, int]) -> None:
        master, slave = pty_pair
        port_path = os.ttyname(slave)
        async with AsyncSerial(port_path, baudrate=9600, timeout=1.0) as port:
            os.write(master, b"0123456789")
            data = await port.read_exactly(10)
            assert data == b"0123456789"

    @pytest.mark.asyncio
    async def test_configure(self, pty_port: str) -> None:
        async with AsyncSerial(pty_port, baudrate=9600, timeout=0.1) as port:
            new_cfg = SerialConfig(baudrate=19200, timeout=0.1)
            await port.configure(new_cfg)
            assert port.baudrate == 19200
