#!/usr/bin/env python3
import argparse
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


def configure(fd: int, baud: int) -> list[int]:
    old = termios.tcgetattr(fd)
    tty.setraw(fd)
    attrs = termios.tcgetattr(fd)
    baud_flag = BAUD_FLAGS[baud]
    attrs[4] = baud_flag
    attrs[5] = baud_flag
    attrs[2] |= termios.CLOCAL | termios.CREAD
    attrs[2] &= ~termios.CSTOPB
    attrs[2] &= ~termios.PARENB
    attrs[2] &= ~termios.CSIZE
    attrs[2] |= termios.CS8
    attrs[6][termios.VMIN] = 0
    attrs[6][termios.VTIME] = 0
    termios.tcsetattr(fd, termios.TCSANOW, attrs)
    return old


def decode(byte: int) -> str:
    tag = byte >> 4
    payload = byte & 0x0F
    if tag == 0x5:
        return f"0x{byte:02x}  tag=state state={payload}"
    if tag == 0x6:
        audio_mode = (payload >> 3) & 1
        emit = (payload >> 2) & 1
        handle_k = payload & 0x03
        return f"0x{byte:02x}  tag=meta mode={'audio' if audio_mode else 'manual'} emit={bool(emit)} handleK={handle_k}"
    return f"0x{byte:02x}  tag=0x{tag:x} low=0x{payload:x}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Monitor Tang Nano 9K Sparkle Phi/S3C UART telemetry.")
    parser.add_argument("port", nargs="?", default="/dev/ttyUSB1")
    parser.add_argument("--baud", type=int, default=115200, choices=sorted(BAUD_FLAGS))
    parser.add_argument("--seconds", type=float, default=0.0, help="Stop after N seconds; 0 means run forever.")
    parser.add_argument("--expect-state-tag", action="store_true", help="Fail unless state-tagged 0x5N frames arrive.")
    parser.add_argument("--min-frames", type=int, default=1, help="Minimum expected frames when checking telemetry.")
    args = parser.parse_args()

    fd = os.open(args.port, os.O_RDONLY | os.O_NOCTTY | os.O_NONBLOCK)
    old_attrs = configure(fd, args.baud)
    deadline = None if args.seconds <= 0 else time.monotonic() + args.seconds
    matched = 0
    print(f"listening on {args.port} at {args.baud} baud; press the FPGA user button")
    try:
        while deadline is None or time.monotonic() < deadline:
            ready, _, _ = select.select([fd], [], [], 0.25)
            if not ready:
                continue
            data = os.read(fd, 256)
            for byte in data:
                if byte >> 4 == 0x5:
                    matched += 1
                print(decode(byte), flush=True)
    finally:
        termios.tcsetattr(fd, termios.TCSANOW, old_attrs)
        os.close(fd)
    if args.expect_state_tag and matched < args.min_frames:
        print(f"expected at least {args.min_frames} state-tag frame(s), saw {matched}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
