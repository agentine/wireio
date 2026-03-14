"""Tests for wireio type enums."""

from wireio import ByteSize, FlowControl, Parity, StopBits


def test_parity_values() -> None:
    assert Parity.NONE == 0
    assert Parity.EVEN == 1
    assert Parity.ODD == 2
    assert Parity.MARK == 3
    assert Parity.SPACE == 4


def test_stopbits_values() -> None:
    assert StopBits.ONE == 1
    assert StopBits.ONE_POINT_FIVE == 15
    assert StopBits.TWO == 2


def test_bytesize_values() -> None:
    assert ByteSize.FIVE == 5
    assert ByteSize.SIX == 6
    assert ByteSize.SEVEN == 7
    assert ByteSize.EIGHT == 8


def test_flow_control_values() -> None:
    assert FlowControl.NONE == 0
    assert FlowControl.HARDWARE == 1
    assert FlowControl.SOFTWARE == 2


def test_enums_are_intenum() -> None:
    assert isinstance(Parity.NONE, int)
    assert isinstance(StopBits.ONE, int)
    assert isinstance(ByteSize.EIGHT, int)
    assert isinstance(FlowControl.NONE, int)
