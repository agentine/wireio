"""Tests for port discovery."""

from __future__ import annotations

import sys

import pytest

from wireio import PortInfo, list_ports


def test_port_info_defaults() -> None:
    info = PortInfo(device="/dev/ttyUSB0")
    assert info.device == "/dev/ttyUSB0"
    assert info.name == ""
    assert info.description == ""
    assert info.hwid == ""
    assert info.vid is None
    assert info.pid is None
    assert info.serial_number == ""
    assert info.manufacturer == ""
    assert info.product == ""


def test_port_info_with_usb_info() -> None:
    info = PortInfo(
        device="/dev/ttyUSB0",
        name="ttyUSB0",
        vid=0x1234,
        pid=0x5678,
        manufacturer="FTDI",
        product="FT232R",
        serial_number="A12345",
    )
    assert info.vid == 0x1234
    assert info.pid == 0x5678
    assert info.manufacturer == "FTDI"


def test_list_ports_returns_list() -> None:
    result = list_ports()
    assert isinstance(result, list)


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS only")
def test_list_ports_macos() -> None:
    from wireio._ports import _list_ports_macos

    ports = _list_ports_macos()
    assert isinstance(ports, list)
    for port in ports:
        assert isinstance(port, PortInfo)
        assert port.device.startswith("/dev/")


@pytest.mark.skipif(sys.platform != "linux", reason="Linux only")
def test_list_ports_linux() -> None:
    from wireio._ports import _list_ports_linux

    ports = _list_ports_linux()
    assert isinstance(ports, list)
    for port in ports:
        assert isinstance(port, PortInfo)
        assert port.device.startswith("/dev/")
