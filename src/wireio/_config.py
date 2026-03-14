"""Serial port configuration."""

from __future__ import annotations

from dataclasses import dataclass, field

from wireio._types import ByteSize, FlowControl, Parity, StopBits


@dataclass(slots=True)
class SerialConfig:
    """Configuration for a serial port connection.

    Attributes:
        baudrate: Baud rate (e.g. 9600, 115200).
        bytesize: Number of data bits.
        parity: Parity checking mode.
        stopbits: Number of stop bits.
        timeout: Read timeout in seconds. None = blocking, 0 = non-blocking.
        write_timeout: Write timeout in seconds. None = blocking.
        flow_control: Flow control mode.
        xonxoff: Enable software flow control (XON/XOFF).
        rtscts: Enable hardware flow control (RTS/CTS).
        dsrdtr: Enable hardware flow control (DSR/DTR).
        inter_byte_timeout: Inter-byte timeout in seconds. None = disabled.
    """

    baudrate: int = 9600
    bytesize: ByteSize = ByteSize.EIGHT
    parity: Parity = Parity.NONE
    stopbits: StopBits = StopBits.ONE
    timeout: float | None = None
    write_timeout: float | None = None
    flow_control: FlowControl = FlowControl.NONE
    xonxoff: bool = False
    rtscts: bool = False
    dsrdtr: bool = False
    inter_byte_timeout: float | None = None

    _STANDARD_BAUDRATES: frozenset[int] = field(
        default=frozenset({
            50, 75, 110, 134, 150, 200, 300, 600, 1200, 1800, 2400, 4800,
            9600, 19200, 38400, 57600, 115200, 230400, 460800, 500000, 576000,
            921600, 1000000, 1152000, 1500000, 2000000, 2500000, 3000000,
            3500000, 4000000,
        }),
        init=False,
        repr=False,
    )

    def validate(self) -> None:
        """Validate configuration values.

        Raises:
            ConfigError: If any value is invalid.
        """
        from wireio._exceptions import ConfigError

        if self.baudrate <= 0:
            raise ConfigError(f"baudrate must be positive, got {self.baudrate}")
        if self.timeout is not None and self.timeout < 0:
            raise ConfigError(f"timeout must be non-negative, got {self.timeout}")
        if self.write_timeout is not None and self.write_timeout < 0:
            raise ConfigError(
                f"write_timeout must be non-negative, got {self.write_timeout}"
            )
        if self.inter_byte_timeout is not None and self.inter_byte_timeout < 0:
            raise ConfigError(
                f"inter_byte_timeout must be non-negative, got {self.inter_byte_timeout}"
            )
