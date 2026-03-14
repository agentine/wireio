"""Interactive serial terminal emulator.

Usage::

    python -m wireio.tools.miniterm /dev/ttyUSB0 115200
"""

from __future__ import annotations

import argparse
import sys
import threading

from wireio import Serial, SerialError


def main() -> None:
    """Run the miniterm interactive terminal."""
    parser = argparse.ArgumentParser(
        description="wireio miniterm — interactive serial terminal"
    )
    parser.add_argument("port", help="Serial port device")
    parser.add_argument(
        "baudrate", nargs="?", type=int, default=9600, help="Baud rate"
    )
    parser.add_argument(
        "--encoding", default="utf-8", help="Character encoding"
    )
    parser.add_argument(
        "--echo", action="store_true", help="Enable local echo"
    )
    parser.add_argument(
        "--eol",
        choices=["cr", "lf", "crlf"],
        default="crlf",
        help="Line ending for transmitted data",
    )
    args = parser.parse_args()

    eol_map = {"cr": "\r", "lf": "\n", "crlf": "\r\n"}
    eol = eol_map[args.eol]

    try:
        with Serial(args.port, baudrate=args.baudrate, timeout=0.1) as port:
            print(
                f"--- wireio miniterm on {args.port} "
                f"@ {args.baudrate} baud ---"
            )
            print("--- Ctrl+C to exit ---")

            stop_event = threading.Event()

            def reader() -> None:
                while not stop_event.is_set():
                    try:
                        data = port.read(256)
                        if data:
                            text = data.decode(args.encoding, errors="replace")
                            sys.stdout.write(text)
                            sys.stdout.flush()
                    except SerialError:
                        if not stop_event.is_set():
                            break

            reader_thread = threading.Thread(target=reader, daemon=True)
            reader_thread.start()

            try:
                while True:
                    line = input()
                    if args.echo:
                        print(line)
                    port.write((line + eol).encode(args.encoding))
            except (KeyboardInterrupt, EOFError):
                pass
            finally:
                stop_event.set()
                print("\n--- exit ---")

    except SerialError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
