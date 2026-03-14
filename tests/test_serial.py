"""Tests for Serial using PTY pairs."""

from __future__ import annotations

import os
import sys
import time

import pytest

from wireio import (
    ByteSize,
    ConfigError,
    Parity,
    Serial,
    SerialConfig,
    SerialError,
    StopBits,
)

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


class TestSerialOpen:
    def test_open_close(self, pty_port: str) -> None:
        port = Serial(pty_port, baudrate=9600, timeout=0.1)
        assert not port.is_open
        port.open()
        assert port.is_open
        port.close()
        assert not port.is_open

    def test_context_manager(self, pty_port: str) -> None:
        with Serial(pty_port, baudrate=9600, timeout=0.1) as port:
            assert port.is_open
        assert not port.is_open

    def test_double_open_raises(self, pty_port: str) -> None:
        port = Serial(pty_port, baudrate=9600, timeout=0.1)
        port.open()
        with pytest.raises(SerialError, match="already open"):
            port.open()
        port.close()

    def test_open_nonexistent_port(self) -> None:
        with pytest.raises(SerialError):
            with Serial("/dev/nonexistent_serial_port_xyz", timeout=0.1) as _:
                pass

    def test_close_idempotent(self, pty_port: str) -> None:
        port = Serial(pty_port, baudrate=9600, timeout=0.1)
        port.open()
        port.close()
        port.close()  # Should not raise

    def test_repr(self, pty_port: str) -> None:
        port = Serial(pty_port, baudrate=115200, timeout=0.1)
        assert "115200" in repr(port)
        assert "closed" in repr(port)
        port.open()
        assert "open" in repr(port)
        port.close()


class TestSerialConfig:
    def test_config_object(self, pty_port: str) -> None:
        cfg = SerialConfig(baudrate=115200, parity=Parity.EVEN)
        with Serial(pty_port, config=cfg, timeout=0.1) as port:
            assert port.baudrate == 115200
            assert port.parity == Parity.EVEN

    def test_baudrate_property(self, pty_port: str) -> None:
        with Serial(pty_port, baudrate=19200, timeout=0.1) as port:
            assert port.baudrate == 19200

    def test_bytesize_property(self, pty_port: str) -> None:
        with Serial(
            pty_port, baudrate=9600, bytesize=ByteSize.SEVEN, timeout=0.1
        ) as port:
            assert port.bytesize == ByteSize.SEVEN

    def test_parity_property(self, pty_port: str) -> None:
        with Serial(pty_port, baudrate=9600, parity=Parity.ODD, timeout=0.1) as port:
            assert port.parity == Parity.ODD

    def test_stopbits_property(self, pty_port: str) -> None:
        with Serial(
            pty_port, baudrate=9600, stopbits=StopBits.TWO, timeout=0.1
        ) as port:
            assert port.stopbits == StopBits.TWO

    def test_invalid_baudrate_rejected(self) -> None:
        with pytest.raises(ConfigError):
            SerialConfig(baudrate=-1).validate()

    def test_reconfigure(self, pty_port: str) -> None:
        with Serial(pty_port, baudrate=9600, timeout=0.1) as port:
            new_cfg = SerialConfig(baudrate=19200, timeout=0.1)
            port.configure(new_cfg)
            assert port.baudrate == 19200


class TestSerialReadWrite:
    def test_write_read(self, pty_pair: tuple[int, int]) -> None:
        master, slave = pty_pair
        port_path = os.ttyname(slave)
        with Serial(port_path, baudrate=9600, timeout=1.0) as port:
            # Write through port, read from master
            port.write(b"hello")
            time.sleep(0.05)
            data = os.read(master, 100)
            assert data == b"hello"

    def test_read_from_master(self, pty_pair: tuple[int, int]) -> None:
        master, slave = pty_pair
        port_path = os.ttyname(slave)
        with Serial(port_path, baudrate=9600, timeout=1.0) as port:
            # Write to master, read from port
            os.write(master, b"world")
            data = port.read(5)
            assert data == b"world"

    def test_read_timeout(self, pty_port: str) -> None:
        with Serial(pty_port, baudrate=9600, timeout=0.1) as port:
            start = time.monotonic()
            data = port.read(10)
            elapsed = time.monotonic() - start
            assert data == b""
            assert elapsed < 1.0

    def test_read_zero_bytes(self, pty_port: str) -> None:
        with Serial(pty_port, baudrate=9600, timeout=0.1) as port:
            data = port.read(0)
            assert data == b""

    def test_write_returns_count(self, pty_pair: tuple[int, int]) -> None:
        master, slave = pty_pair
        port_path = os.ttyname(slave)
        with Serial(port_path, baudrate=9600, timeout=0.1) as port:
            n = port.write(b"test")
            assert n == 4
            os.read(master, 100)  # drain

    def test_read_negative_raises(self, pty_port: str) -> None:
        with Serial(pty_port, baudrate=9600, timeout=0.1) as port:
            with pytest.raises(ConfigError, match="non-negative"):
                port.read(-1)

    def test_nonblocking_read(self, pty_port: str) -> None:
        with Serial(pty_port, baudrate=9600, timeout=0) as port:
            data = port.read(10)
            assert data == b""

    def test_write_bytearray(self, pty_pair: tuple[int, int]) -> None:
        master, slave = pty_pair
        port_path = os.ttyname(slave)
        with Serial(port_path, baudrate=9600, timeout=0.1) as port:
            port.write(bytearray(b"abc"))
            time.sleep(0.05)
            data = os.read(master, 100)
            assert data == b"abc"


class TestSerialReadUntil:
    def test_read_until_newline(self, pty_pair: tuple[int, int]) -> None:
        master, slave = pty_pair
        port_path = os.ttyname(slave)
        with Serial(port_path, baudrate=9600, timeout=1.0) as port:
            os.write(master, b"hello\nworld\n")
            line = port.read_until(b"\n")
            assert line == b"hello\n"

    def test_read_line(self, pty_pair: tuple[int, int]) -> None:
        master, slave = pty_pair
        port_path = os.ttyname(slave)
        with Serial(port_path, baudrate=9600, timeout=1.0) as port:
            os.write(master, b"line1\nline2\n")
            line = port.read_line()
            assert line == b"line1\n"

    def test_read_until_custom_delimiter(
        self, pty_pair: tuple[int, int]
    ) -> None:
        master, slave = pty_pair
        port_path = os.ttyname(slave)
        with Serial(port_path, baudrate=9600, timeout=1.0) as port:
            os.write(master, b"AT+OK\r\n")
            data = port.read_until(b"\r\n")
            assert data == b"AT+OK\r\n"

    def test_read_until_size_limit(self, pty_pair: tuple[int, int]) -> None:
        master, slave = pty_pair
        port_path = os.ttyname(slave)
        with Serial(port_path, baudrate=9600, timeout=1.0) as port:
            os.write(master, b"abcdefghij\n")
            data = port.read_until(b"\n", size=5)
            assert len(data) == 5

    def test_read_exactly(self, pty_pair: tuple[int, int]) -> None:
        master, slave = pty_pair
        port_path = os.ttyname(slave)
        with Serial(port_path, baudrate=9600, timeout=1.0) as port:
            os.write(master, b"0123456789")
            data = port.read_exactly(10)
            assert data == b"0123456789"


class TestSerialState:
    def test_read_when_closed_raises(self, pty_port: str) -> None:
        port = Serial(pty_port, baudrate=9600, timeout=0.1)
        with pytest.raises(SerialError, match="not open"):
            port.read(1)

    def test_write_when_closed_raises(self, pty_port: str) -> None:
        port = Serial(pty_port, baudrate=9600, timeout=0.1)
        with pytest.raises(SerialError, match="not open"):
            port.write(b"test")

    def test_flush_when_closed_raises(self, pty_port: str) -> None:
        port = Serial(pty_port, baudrate=9600, timeout=0.1)
        with pytest.raises(SerialError, match="not open"):
            port.flush()

    def test_in_waiting_when_closed_raises(self, pty_port: str) -> None:
        port = Serial(pty_port, baudrate=9600, timeout=0.1)
        with pytest.raises(SerialError, match="not open"):
            _ = port.in_waiting

    def test_in_waiting(self, pty_pair: tuple[int, int]) -> None:
        master, slave = pty_pair
        port_path = os.ttyname(slave)
        with Serial(port_path, baudrate=9600, timeout=0.1) as port:
            os.write(master, b"data")
            time.sleep(0.05)
            assert port.in_waiting >= 4

    def test_port_property(self, pty_port: str) -> None:
        port = Serial(pty_port, baudrate=9600, timeout=0.1)
        assert port.port == pty_port

    def test_timeout_property(self, pty_port: str) -> None:
        port = Serial(pty_port, baudrate=9600, timeout=2.5)
        assert port.timeout == 2.5

    def test_config_property(self, pty_port: str) -> None:
        cfg = SerialConfig(baudrate=38400, timeout=0.1)
        port = Serial(pty_port, config=cfg)
        assert port.config is cfg


class TestBaudrates:
    @pytest.mark.parametrize(
        "baud", [9600, 19200, 38400, 57600, 115200]
    )
    def test_standard_baudrates(self, pty_port: str, baud: int) -> None:
        with Serial(pty_port, baudrate=baud, timeout=0.1) as port:
            assert port.baudrate == baud
