"""Tests for SerialConfig."""

import pytest

from wireio import ByteSize, ConfigError, FlowControl, Parity, SerialConfig, StopBits


def test_default_config() -> None:
    cfg = SerialConfig()
    assert cfg.baudrate == 9600
    assert cfg.bytesize == ByteSize.EIGHT
    assert cfg.parity == Parity.NONE
    assert cfg.stopbits == StopBits.ONE
    assert cfg.timeout is None
    assert cfg.write_timeout is None
    assert cfg.flow_control == FlowControl.NONE
    assert cfg.xonxoff is False
    assert cfg.rtscts is False
    assert cfg.dsrdtr is False
    assert cfg.inter_byte_timeout is None


def test_custom_config() -> None:
    cfg = SerialConfig(
        baudrate=115200,
        bytesize=ByteSize.SEVEN,
        parity=Parity.EVEN,
        stopbits=StopBits.TWO,
        timeout=1.0,
        rtscts=True,
    )
    assert cfg.baudrate == 115200
    assert cfg.bytesize == ByteSize.SEVEN
    assert cfg.parity == Parity.EVEN
    assert cfg.stopbits == StopBits.TWO
    assert cfg.timeout == 1.0
    assert cfg.rtscts is True


def test_validate_negative_baudrate() -> None:
    cfg = SerialConfig(baudrate=-1)
    with pytest.raises(ConfigError, match="baudrate must be positive"):
        cfg.validate()


def test_validate_zero_baudrate() -> None:
    cfg = SerialConfig(baudrate=0)
    with pytest.raises(ConfigError, match="baudrate must be positive"):
        cfg.validate()


def test_validate_negative_timeout() -> None:
    cfg = SerialConfig(timeout=-1.0)
    with pytest.raises(ConfigError, match="timeout must be non-negative"):
        cfg.validate()


def test_validate_negative_write_timeout() -> None:
    cfg = SerialConfig(write_timeout=-1.0)
    with pytest.raises(ConfigError, match="write_timeout must be non-negative"):
        cfg.validate()


def test_validate_negative_inter_byte_timeout() -> None:
    cfg = SerialConfig(inter_byte_timeout=-0.5)
    with pytest.raises(ConfigError, match="inter_byte_timeout must be non-negative"):
        cfg.validate()


def test_validate_ok() -> None:
    cfg = SerialConfig(baudrate=115200, timeout=0, write_timeout=5.0)
    cfg.validate()  # Should not raise
