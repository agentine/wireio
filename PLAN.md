# wireio — Modern Python Serial Port Library

**Replaces:** [pyserial](https://github.com/pyserial/pyserial) (13M downloads/month, last release Nov 2020)
**Package name:** wireio (verified available on PyPI)
**Language:** Python 3.10+
**Dependencies:** Zero (stdlib only)

## Why Replace pyserial

- **Single maintainer** (Chris Liechti) — no visible activity since 2020
- **5+ years without a release** — last version 3.5 on Nov 23, 2020
- **275 open issues, 54 unmerged PRs** — no maintainer responses
- **Outdated Python support** — still lists Python 2.7 and 3.4-3.8
- **No type hints** — no PEP 561 compliance
- **No built-in async** — requires separate `pyserial-asyncio` package
- **Used by 101K projects** — massive bus factor risk
- **No active fork** has gained traction

## Scope

A modern, type-safe serial port communication library providing:

1. Synchronous and asynchronous serial port I/O
2. Cross-platform backends (POSIX via termios, Windows via ctypes/win32)
3. Port discovery and enumeration
4. Familiar API for easy migration from pyserial

## Architecture

```
wireio/
├── __init__.py          # Public API: Serial, list_ports, exceptions, enums
├── _types.py            # Enums: Parity, StopBits, ByteSize, FlowControl
├── _config.py           # SerialConfig dataclass
├── _base.py             # SerialBase abstract base class
├── _posix.py            # POSIX backend (termios, fcntl)
├── _win32.py            # Windows backend (ctypes + kernel32/setupapi)
├── _exceptions.py       # SerialError, PortNotFoundError, ConfigError
├── _ports.py            # Port discovery (platform-specific enumeration)
├── _async.py            # AsyncSerial class (asyncio native)
├── py.typed             # PEP 561 marker
└── tools/
    ├── __init__.py
    ├── miniterm.py      # Interactive terminal emulator
    └── list_ports.py    # CLI: python -m wireio.tools.list_ports
```

## Key Design Decisions

- **Python 3.10+** — use match/case, modern type unions, dataclasses with slots
- **Zero dependencies** — stdlib only (termios, ctypes, fcntl, asyncio)
- **Full type hints** — PEP 561 compliant, strict mypy
- **Dataclass config** — `SerialConfig` instead of scattered constructor params
- **Enum-based settings** — `Parity.NONE`, `StopBits.ONE`, `ByteSize.EIGHT`
- **Context manager** — `with Serial("/dev/ttyUSB0") as port:`
- **Built-in async** — `async with AsyncSerial(...) as port:` (no extra package)
- **Buffered reads** — `read_until(delimiter)`, `read_line()`, `read_exactly(n)`

## Module Breakdown

### Phase 1: Core (MVP)
- `_types.py` — Parity, StopBits, ByteSize, FlowControl enums
- `_config.py` — SerialConfig dataclass (baudrate, bytesize, parity, stopbits, timeout, flow control)
- `_exceptions.py` — Exception hierarchy
- `_base.py` — SerialBase ABC (open, close, read, write, configure, properties)
- `_posix.py` — PosixSerial implementation using termios/fcntl
- `__init__.py` — Public API, platform auto-detection

### Phase 2: Windows + Port Discovery
- `_win32.py` — Win32Serial using ctypes (CreateFile, SetCommState, etc.)
- `_ports.py` — Platform-specific port enumeration (sysfs on Linux, IOKit on macOS, SetupAPI on Windows)

### Phase 3: Async + Tools
- `_async.py` — AsyncSerial wrapping sync backend with asyncio
- `tools/miniterm.py` — Interactive terminal
- `tools/list_ports.py` — CLI tool

### Phase 4: Testing + Polish
- Virtual serial port tests using PTY pairs (os.openpty)
- Integration test harness
- Migration guide from pyserial
- Documentation

## Public API Surface

```python
from wireio import Serial, AsyncSerial, list_ports
from wireio import Parity, StopBits, ByteSize, FlowControl
from wireio import SerialConfig, SerialError

# Sync usage
with Serial("/dev/ttyUSB0", baudrate=115200) as port:
    port.write(b"AT\r\n")
    response = port.read_until(b"\r\n")

# Async usage
async with AsyncSerial("/dev/ttyUSB0", baudrate=9600) as port:
    await port.write(b"hello")
    data = await port.read(100)

# Port discovery
for port_info in list_ports():
    print(f"{port_info.device} — {port_info.description}")

# Dataclass config
config = SerialConfig(baudrate=115200, parity=Parity.EVEN, stopbits=StopBits.TWO)
port = Serial("/dev/ttyS0", config=config)
```

## Testing Strategy

- **Unit tests:** Mock termios/ctypes calls, test config validation, enum behavior
- **PTY tests:** Use `os.openpty()` to create virtual serial port pairs for read/write testing
- **Platform tests:** CI on Linux (primary), macOS (secondary); Windows via contributor testing
- **Compatibility tests:** Verify API parity with pyserial for migration scenarios
