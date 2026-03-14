"""CLI tool to list available serial ports.

Usage::

    python -m wireio.tools.list_ports
"""

from __future__ import annotations

from wireio._ports import list_ports


def main() -> None:
    """Print a table of available serial ports."""
    ports = list_ports()
    if not ports:
        print("No serial ports found.")
        return

    # Calculate column widths
    dev_width = max(len(p.device) for p in ports)
    desc_width = max((len(p.description) for p in ports), default=0)
    dev_width = max(dev_width, 6)
    desc_width = max(desc_width, 11)

    header = f"{'DEVICE':<{dev_width}}  {'DESCRIPTION':<{desc_width}}  HWID"
    print(header)
    print("-" * len(header))

    for port in ports:
        print(
            f"{port.device:<{dev_width}}  "
            f"{port.description:<{desc_width}}  "
            f"{port.hwid}"
        )


if __name__ == "__main__":
    main()
