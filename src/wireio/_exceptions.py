"""Serial port exception hierarchy."""

from __future__ import annotations


class SerialError(Exception):
    """Base exception for all serial port errors."""


class PortNotFoundError(SerialError):
    """Raised when the specified serial port cannot be found or opened."""


class ConfigError(SerialError):
    """Raised when serial port configuration is invalid."""


class SerialTimeoutError(SerialError):
    """Raised when a read or write operation times out."""
