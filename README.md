# wireio

[![PyPI](https://img.shields.io/pypi/v/wireio)](https://pypi.org/project/wireio/)
[![Python](https://img.shields.io/pypi/pyversions/wireio)](https://pypi.org/project/wireio/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Modern Python serial port library — a drop-in replacement for [pyserial](https://github.com/pyserial/pyserial).

- **Python 3.10+** with full type annotations (PEP 561)
- **Zero dependencies** — stdlib only
- **Cross-platform** — Linux, macOS, Windows
- **Built-in async** — `AsyncSerial` with native asyncio support
- **Port discovery** — `list_ports()` enumerates available serial devices
- **CLI tools** — `wireio-miniterm` and `wireio-list-ports`

## Why wireio?

[pyserial](https://github.com/pyserial/pyserial) is used by 100,000+ projects but has had no release since November 2020. The single maintainer is unreachable, 275+ issues are open, and the library has no type hints, no async support, and still targets Python 2.7.

wireio is a modern replacement:

| | pyserial | wireio |
|---|---|---|
| Last release | Nov 2020 | Active |
| Dependencies | None | **None** |
| Python support | 2.7, 3.4–3.8 | **3.10+ (including 3.13+)** |
| Type hints | No | **Full PEP 561** |
| Async support | Separate package | **Built-in `AsyncSerial`** |
| API style | Old-style class | **Dataclass config + enums** |

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

Main serial port class. Platform-specific backend is selected automatically (POSIX on Linux/macOS, Win32 on Windows).

**Constructor parameters:**
- `port` — device path (`/dev/ttyUSB0`, `COM3`)
- `baudrate` — baud rate (default: `9600`)
- `bytesize` — `ByteSize.FIVE` through `ByteSize.EIGHT` (default: `EIGHT`)
- `parity` — `Parity.NONE`, `EVEN`, `ODD`, `MARK`, `SPACE` (default: `NONE`)
- `stopbits` — `StopBits.ONE`, `ONE_POINT_FIVE`, `TWO` (default: `ONE`)
- `timeout` — read timeout in seconds (`None` = blocking, `0` = non-blocking, default: `None`)
- `write_timeout` — write timeout in seconds (`None` = blocking, default: `None`)
- `flow_control` — `FlowControl.NONE`, `HARDWARE`, `SOFTWARE` (default: `NONE`)
- `xonxoff` — enable XON/XOFF software flow control (default: `False`)
- `rtscts` — enable RTS/CTS hardware flow control (default: `False`)
- `dsrdtr` — enable DSR/DTR hardware flow control (default: `False`)
- `inter_byte_timeout` — timeout between consecutive bytes in seconds (`None` = disabled, default: `None`)
- `config` — `SerialConfig` object (overrides individual params when provided)

**Methods:**
- `open()` / `close()` — open or close the port
- `read(size=1) -> bytes` — read up to `size` bytes; returns fewer if timeout expires
- `write(data) -> int` — write bytes, returns count written
- `flush()` — wait until all data transmitted
- `read_until(delimiter=b"\n", size=0) -> bytes` — read until delimiter found; `size=0` means no limit
- `read_line() -> bytes` — read until `\n`
- `read_exactly(size) -> bytes` — read exactly `size` bytes, blocking until all received
- `configure(config)` — apply new `SerialConfig` to an open port

**Properties:**
- `is_open` — whether the port is open
- `in_waiting` — bytes available in input buffer
- `port`, `baudrate`, `bytesize`, `parity`, `stopbits`, `timeout`, `config`

Supports the context manager protocol (`with Serial(...) as port:`).

### `AsyncSerial(port, baudrate=9600, **kwargs)`

Async wrapper around `Serial`. Runs blocking I/O in a thread executor via `asyncio.run_in_executor`. Same constructor parameters as `Serial`, plus:

- `loop` (`asyncio.AbstractEventLoop | None`) — event loop to use (default: current running loop)

All I/O methods are `async` and mirror the `Serial` interface:

```python
async with AsyncSerial("/dev/ttyUSB0", baudrate=9600) as port:
    await port.write(b"hello")
    data = await port.read(100)
    line = await port.read_line()
    exact = await port.read_exactly(4)
    until = await port.read_until(b"\r\n")
    await port.flush()
    await port.configure(SerialConfig(baudrate=115200))
```

**Async methods:** `open`, `close`, `read`, `write`, `flush`, `read_until`, `read_line`, `read_exactly`, `configure`

**Properties (sync):** `port`, `is_open`, `baudrate`, `config`

Supports the async context manager protocol (`async with AsyncSerial(...) as port:`).

### `SerialConfig`

Dataclass holding all serial port settings. Pass as the `config=` argument to `Serial` or `AsyncSerial`, or use `port.configure(config)` to reconfigure an open port.

```python
from wireio import SerialConfig, Parity, StopBits, ByteSize, FlowControl

config = SerialConfig(
    baudrate=115200,
    bytesize=ByteSize.EIGHT,
    parity=Parity.NONE,
    stopbits=StopBits.ONE,
    timeout=1.0,
    write_timeout=None,
    flow_control=FlowControl.NONE,
    inter_byte_timeout=None,
)
```

**Fields** (all optional, defaults match `Serial` constructor):
- `baudrate: int` — default `9600`
- `bytesize: ByteSize` — default `ByteSize.EIGHT`
- `parity: Parity` — default `Parity.NONE`
- `stopbits: StopBits` — default `StopBits.ONE`
- `timeout: float | None` — default `None`
- `write_timeout: float | None` — default `None`
- `flow_control: FlowControl` — default `FlowControl.NONE`
- `xonxoff: bool` — default `False`
- `rtscts: bool` — default `False`
- `dsrdtr: bool` — default `False`
- `inter_byte_timeout: float | None` — default `None`

`SerialConfig.validate()` raises `ConfigError` for invalid values (negative baudrate, negative timeouts, etc.).

### `list_ports() -> list[PortInfo]`

Enumerate available serial ports. Returns `PortInfo` objects with:
- `device` — device path (e.g. `/dev/ttyUSB0`, `COM3`)
- `name` — short port name
- `description` — human-readable description
- `hwid` — hardware ID string
- `vid`, `pid` — USB vendor/product IDs (or `None`)
- `serial_number`, `manufacturer`, `product` — USB metadata (or `None`)

### Enums

- `Parity` — `NONE`, `EVEN`, `ODD`, `MARK`, `SPACE`
- `StopBits` — `ONE`, `ONE_POINT_FIVE`, `TWO`
- `ByteSize` — `FIVE`, `SIX`, `SEVEN`, `EIGHT`
- `FlowControl` — `NONE`, `HARDWARE`, `SOFTWARE`

### Exceptions

All exceptions inherit from `SerialError`:

- `SerialError` — base exception for all serial port errors
- `PortNotFoundError` — port not found or permission denied
- `ConfigError` — invalid configuration value
- `SerialTimeoutError` — operation timed out

## CLI Tools

### `wireio-list-ports`

Print a table of available serial ports:

```bash
wireio-list-ports
# or
python -m wireio.tools.list_ports
```

Output example:
```
DEVICE        DESCRIPTION          HWID
-------------------------------------------------
/dev/ttyUSB0  USB Serial Device    USB VID:PID=0403:6001
/dev/ttyS0    ttyS0                n/a
```

### `wireio-miniterm`

Interactive serial terminal:

```bash
wireio-miniterm /dev/ttyUSB0 115200
# or
python -m wireio.tools.miniterm /dev/ttyUSB0 115200 --echo --eol crlf
```

**Options:**
- `port` — serial port device path (required)
- `baudrate` — baud rate (default: `9600`)
- `--encoding` — character encoding for display and input (default: `utf-8`)
- `--echo` — enable local echo of typed input
- `--eol {cr,lf,crlf}` — line ending appended to transmitted lines (default: `crlf`)

Press `Ctrl+C` to exit.

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
