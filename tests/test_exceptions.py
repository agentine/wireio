"""Tests for exception hierarchy."""

from wireio import ConfigError, PortNotFoundError, SerialError
from wireio._exceptions import SerialTimeoutError


def test_hierarchy() -> None:
    assert issubclass(PortNotFoundError, SerialError)
    assert issubclass(ConfigError, SerialError)
    assert issubclass(SerialTimeoutError, SerialError)
    assert issubclass(SerialError, Exception)


def test_serial_error_message() -> None:
    err = SerialError("test message")
    assert str(err) == "test message"


def test_port_not_found_message() -> None:
    err = PortNotFoundError("/dev/nonexistent")
    assert "/dev/nonexistent" in str(err)


def test_config_error_message() -> None:
    err = ConfigError("bad baudrate")
    assert "bad baudrate" in str(err)
