# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [0.1.0] — 2026-03-14

### Added
- `Serial` class with synchronous serial port I/O (POSIX backend via termios/fcntl)
- `AsyncSerial` class wrapping `Serial` with asyncio (`run_in_executor`)
- `SerialConfig` dataclass for structured port configuration
- Enums: `Parity`, `StopBits`, `ByteSize`, `FlowControl`
- Exception hierarchy: `SerialError`, `PortNotFoundError`, `ConfigError`, `SerialTimeoutError`
- Buffered read helpers: `read_until(delimiter)`, `read_line()`, `read_exactly(size)`
- `list_ports()` for platform-specific serial port enumeration (Linux sysfs, macOS IOKit, Windows SetupAPI)
- Windows backend via ctypes (`Win32Serial`)
- Context manager support: `with Serial(...) as port:` and `async with AsyncSerial(...) as port:`
- `wireio-list-ports` CLI tool to enumerate serial devices
- `wireio-miniterm` interactive terminal CLI with `--encoding`, `--echo`, `--eol` options
- Full PEP 561 type annotations (`py.typed` marker)
- Python 3.10–3.13+ support with zero dependencies
