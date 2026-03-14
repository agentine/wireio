# wireio

Modern Python serial port library — a drop-in replacement for [pyserial](https://github.com/pyserial/pyserial).

- **Python 3.10+** with full type annotations (PEP 561)
- **Zero dependencies** — stdlib only
- **Cross-platform** — Linux, macOS, Windows
- **Built-in async** — `AsyncSerial` with native asyncio support
- **Port discovery** — `list_ports()` enumerates available serial devices
- **CLI tools** — `wireio-miniterm` and `wireio-list-ports`

## Installation

```bash
pip install wireio
```

## Quick Start

### Synchronous

```python
from wireio import Serial

with Serial("/dev/ttyUSB0", baudrate=115200) as port:
    port.write(b"AT\r\n")
    response = port.read_until(b"\r\n")
    print(response)
```

### Asynchronous

```python
import asyncio
from wireio import AsyncSerial

async def main():
    async with AsyncSerial("/dev/ttyUSB0", baudrate=9600) as port:
        await port.write(b"hello")
        data = await port.read(100)
        print(data)

asyncio.run(main())
```

### Port Discovery

```python
from wireio import list_ports

for port in list_ports():
    print(f"{port.device} — {port.description}")
```

### Dataclass Config

```python
from wireio import Serial, SerialConfig, Parity, StopBits

config = SerialConfig(
    baudrate=115200,
    parity=Parity.EVEN,
    stopbits=StopBits.TWO,
    timeout=1.0,
)
with Serial("/dev/ttyS0", config=config) as port:
    port.write(b"data")
```

## API Reference

### `Serial(port, baudrate=9600, **kwargs)`

Main serial port class. Platform-specific backend is selected automatically.

**Constructor parameters:**
- `port` — device path (`/dev/ttyUSB0`, `COM3`)
- `baudrate` — baud rate (default: 9600)
- `bytesize` — `ByteSize.FIVE` through `ByteSize.EIGHT` (default: `EIGHT`)
- `parity` — `Parity.NONE`, `EVEN`, `ODD`, `MARK`, `SPACE`
- `stopbits` — `StopBits.ONE`, `ONE_POINT_FIVE`, `TWO`
- `timeout` — read timeout in seconds (`None` = blocking, `0` = non-blocking)
- `write_timeout` — write timeout in seconds
- `flow_control` — `FlowControl.NONE`, `HARDWARE`, `SOFTWARE`
- `xonxoff` — enable XON/XOFF flow control
- `rtscts` — enable RTS/CTS flow control
- `dsrdtr` — enable DSR/DTR flow control
- `inter_byte_timeout` — timeout between consecutive bytes in seconds (`None` = disabled)
- `config` — `SerialConfig` object (overrides individual params)

**Methods:**
- `open()` / `close()` — open or close the port
- `read(size)` — read up to `size` bytes
- `write(data)` — write bytes, returns count written
- `flush()` — wait until all data transmitted
- `read_until(delimiter, size=0)` — read until delimiter found
- `read_line()` — read until `\n`
- `read_exactly(size)` — read exactly `size` bytes
- `configure(config)` — apply new `SerialConfig` to an open port

**Properties:**
- `is_open` — whether the port is open
- `in_waiting` — bytes available in input buffer
- `port`, `baudrate`, `bytesize`, `parity`, `stopbits`, `timeout`, `config`

### `AsyncSerial(port, baudrate=9600, **kwargs)`

Async wrapper around `Serial`. Same constructor parameters. All I/O methods are `async`.

```python
async with AsyncSerial("/dev/ttyUSB0", baudrate=9600) as port:
    await port.write(b"hello")
    data = await port.read(100)
```

### `list_ports() -> list[PortInfo]`

Enumerate available serial ports. Returns `PortInfo` objects with:
- `device` — device path
- `name`, `description`, `hwid`
- `vid`, `pid` — USB vendor/product IDs
- `serial_number`, `manufacturer`, `product`

### Enums

- `Parity` — `NONE`, `EVEN`, `ODD`, `MARK`, `SPACE`
- `StopBits` — `ONE`, `ONE_POINT_FIVE`, `TWO`
- `ByteSize` — `FIVE`, `SIX`, `SEVEN`, `EIGHT`
- `FlowControl` — `NONE`, `HARDWARE`, `SOFTWARE`

### Exceptions

- `SerialError` — base exception
- `PortNotFoundError` — port not found or permission denied
- `ConfigError` — invalid configuration
- `SerialTimeoutError` — operation timed out

## CLI Tools

```bash
# List serial ports
wireio-list-ports
python -m wireio.tools.list_ports

# Interactive terminal
wireio-miniterm /dev/ttyUSB0 115200
python -m wireio.tools.miniterm /dev/ttyUSB0 115200 --echo --eol crlf
```

## Migration from pyserial

wireio is designed as a drop-in replacement for pyserial. Key differences:

| pyserial | wireio |
|---|---|
| `import serial` | `from wireio import Serial` |
| `serial.Serial(...)` | `Serial(...)` |
| `serial.tools.list_ports.comports()` | `wireio.list_ports()` |
| `serial.SerialException` | `wireio.SerialError` |
| `serial.serialutil.SerialTimeoutException` | `wireio.SerialTimeoutError` |
| Separate `pyserial-asyncio` package | Built-in `AsyncSerial` |
| No type hints | Full PEP 561 type hints |
| Python 2.7+ | Python 3.10+ |

### Common patterns

```python
# pyserial
import serial
ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
ser.write(b'hello')
data = ser.read(100)
ser.close()

# wireio (same pattern works)
from wireio import Serial
ser = Serial('/dev/ttyUSB0', 9600, timeout=1)
ser.open()
ser.write(b'hello')
data = ser.read(100)
ser.close()

# wireio (preferred — context manager)
with Serial('/dev/ttyUSB0', baudrate=9600, timeout=1) as ser:
    ser.write(b'hello')
    data = ser.read(100)
```

## License

MIT
