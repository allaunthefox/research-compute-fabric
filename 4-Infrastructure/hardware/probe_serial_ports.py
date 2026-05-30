#!/usr/bin/env python3
"""Probe all serial ports simultaneously for Tang Nano 9K UART output.

Targets the 0xAA test byte from the uart_test design.
Handles both BL702 and FT2232H board variants by scanning every
available /dev/ttyUSB* and /dev/ttyACM* device.

Usage:
    python3 probe_serial_ports.py              # auto-detect all ports
    python3 probe_serial_ports.py --baud 9600  # override baud rate
    python3 probe_serial_ports.py --ports /dev/ttyUSB0 /dev/ttyUSB1
"""

import argparse
import glob
import os
import select
import sys
import termios
import time
import tty

BAUD_FLAGS = {
    9600: termios.B9600,
    19200: termios.B19200,
    38400: termios.B38400,
    57600: termios.B57600,
    115200: termios.B115200,
}

# ANSI colours for terminal output
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
CYAN = "\033[36m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


def discover_ports() -> list[str]:
    """Find all candidate serial device nodes."""
    patterns = ["/dev/ttyUSB*", "/dev/ttyACM*"]
    ports = []
    for pat in patterns:
        ports.extend(sorted(glob.glob(pat)))
    return ports


def configure_raw(fd: int, baud: int) -> list[int]:
    """Set fd to raw 8N1 at the given baud rate. Returns old attrs."""
    old = termios.tcgetattr(fd)
    tty.setraw(fd)
    attrs = termios.tcgetattr(fd)
    baud_flag = BAUD_FLAGS[baud]
    attrs[4] = baud_flag  # ispeed
    attrs[5] = baud_flag  # ospeed
    attrs[2] |= termios.CLOCAL | termios.CREAD
    attrs[2] &= ~termios.CSTOPB
    attrs[2] &= ~termios.PARENB
    attrs[2] &= ~termios.CSIZE
    attrs[2] |= termios.CS8
    attrs[6][termios.VMIN] = 0
    attrs[6][termios.VTIME] = 0
    termios.tcsetattr(fd, termios.TCSANOW, attrs)
    return old


def decode_byte(b: int) -> str:
    """Human-readable decode of one byte in context of the UART test."""
    if b == 0xAA:
        return f"{GREEN}0xAA ✓ UART test byte{RESET}"
    if b == 0x55:
        return f"{YELLOW}0x55 (complement — TX/RX might be swapped){RESET}"
    if b == 0x00:
        return f"{DIM}0x00 (break / noise){RESET}"
    if b == 0xFF:
        return f"{DIM}0xFF (idle line / noise){RESET}"
    return f"0x{b:02X}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Probe all serial ports for Tang Nano 9K UART test output (0xAA)."
    )
    parser.add_argument(
        "--ports",
        nargs="*",
        help="Explicit port list; default: auto-discover /dev/ttyUSB* /dev/ttyACM*",
    )
    parser.add_argument(
        "--baud",
        type=int,
        default=115200,
        choices=sorted(BAUD_FLAGS),
        help="Baud rate (default: 115200)",
    )
    parser.add_argument(
        "--seconds",
        type=float,
        default=10.0,
        help="How long to listen (default: 10s)",
    )
    parser.add_argument(
        "--all-bauds",
        action="store_true",
        help="Cycle through all supported baud rates (9600, 19200, 38400, 57600, 115200)",
    )
    args = parser.parse_args()

    ports = args.ports or discover_ports()
    if not ports:
        print(f"{RED}No serial ports found.{RESET}")
        print("Check: ls -la /dev/ttyUSB* /dev/ttyACM*")
        print("Check: dmesg | grep -i 'tty\\|usb.*serial'")
        return 1

    baud_rates = sorted(BAUD_FLAGS) if args.all_bauds else [args.baud]

    # Header
    print(f"{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}Tang Nano 9K UART Serial Port Probe{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")
    print(f"  Ports:      {', '.join(ports)}")
    print(f"  Baud rates: {', '.join(str(b) for b in baud_rates)}")
    print(f"  Duration:   {args.seconds}s per baud rate")
    print(f"  Looking for: 0xAA (the UART test byte)")
    print(f"{BOLD}{'='*60}{RESET}")
    print()

    found_port = None
    found_baud = None

    for baud in baud_rates:
        print(f"{CYAN}── Probing at {baud} baud ──{RESET}")

        # Open all ports
        open_fds: dict[str, tuple[int, list[int]]] = {}
        for port in ports:
            try:
                fd = os.open(port, os.O_RDONLY | os.O_NOCTTY | os.O_NONBLOCK)
                old_attrs = configure_raw(fd, baud)
                open_fds[port] = (fd, old_attrs)
                print(f"  {GREEN}✓{RESET} Opened {port}")
            except OSError as e:
                print(f"  {RED}✗{RESET} Cannot open {port}: {e}")

        if not open_fds:
            print(f"  {RED}No ports could be opened at {baud} baud.{RESET}")
            continue

        # Flush any stale data
        time.sleep(0.1)
        for port, (fd, _) in open_fds.items():
            try:
                while os.read(fd, 4096):
                    pass
            except BlockingIOError:
                pass

        print(f"  Listening for {args.seconds}s ...")
        deadline = time.monotonic() + args.seconds
        port_stats: dict[str, dict] = {
            port: {"total": 0, "aa_count": 0, "bytes": bytearray()}
            for port in open_fds
        }

        try:
            while time.monotonic() < deadline:
                fds = [fd for fd, _ in open_fds.values()]
                ready, _, _ = select.select(fds, [], [], 0.25)
                if not ready:
                    continue
                for port, (fd, _) in open_fds.items():
                    if fd not in ready:
                        continue
                    try:
                        data = os.read(fd, 256)
                    except BlockingIOError:
                        continue
                    if not data:
                        continue
                    stats = port_stats[port]
                    stats["total"] += len(data)
                    stats["bytes"].extend(data)
                    for byte in data:
                        if byte == 0xAA:
                            stats["aa_count"] += 1
                        ts = time.strftime("%H:%M:%S")
                        print(
                            f"  [{ts}] {BOLD}{port}{RESET}: {decode_byte(byte)}"
                        )
        finally:
            for port, (fd, old_attrs) in open_fds.items():
                try:
                    termios.tcsetattr(fd, termios.TCSANOW, old_attrs)
                except Exception:
                    pass
                os.close(fd)

        # Summary for this baud rate
        print()
        print(f"  {BOLD}Summary at {baud} baud:{RESET}")
        for port, stats in port_stats.items():
            total = stats["total"]
            aa = stats["aa_count"]
            if total == 0:
                print(f"    {port}: {DIM}no data received{RESET}")
            else:
                raw_hex = " ".join(f"{b:02X}" for b in stats["bytes"][:32])
                if len(stats["bytes"]) > 32:
                    raw_hex += " ..."
                status = f"{GREEN}✓ MATCH{RESET}" if aa > 0 else f"{YELLOW}no 0xAA{RESET}"
                print(f"    {port}: {total} bytes, {aa} × 0xAA {status}")
                print(f"      raw: {raw_hex}")
                if aa > 0 and found_port is None:
                    found_port = port
                    found_baud = baud
        print()

    # Final verdict
    print(f"{BOLD}{'='*60}{RESET}")
    if found_port:
        print(f"{GREEN}{BOLD}UART FOUND!{RESET}")
        print(f"  Port: {found_port}")
        print(f"  Baud: {found_baud}")
        print()
        print(f"  To monitor continuously:")
        print(f"    python3 monitor_uart.py {found_port} --baud {found_baud}")
        print(f"  Or with pyserial:")
        print(f"    python3 -m serial.tools.miniterm {found_port} {found_baud}")
    else:
        print(f"{RED}{BOLD}No UART data detected on any port.{RESET}")
        print()
        print(f"  Troubleshooting checklist:")
        print(f"  1. Is the bitstream flashed?  (check LEDs toggling)")
        print(f"  2. Is uart_tx mapped to pin 17?  (check uart_test.cst)")
        print(f"  3. Try --all-bauds to scan all baud rates")
        print(f"  4. Check dmesg for USB device enumeration:")
        print(f"     dmesg | grep -i 'tty\\|usb.*serial\\|bl702'")
        print(f"  5. On BL702 boards, the UART may need the BL702")
        print(f"     firmware to be in passthrough mode")
    print(f"{BOLD}{'='*60}{RESET}")

    return 0 if found_port else 2


if __name__ == "__main__":
    sys.exit(main())
