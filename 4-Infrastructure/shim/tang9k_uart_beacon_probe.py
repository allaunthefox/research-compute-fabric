#!/usr/bin/env python3
"""Probe a Tang Nano 9K TX-only UART beacon on one or more serial ports."""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import serial


DEFAULT_EXPECTED = "a6425131360a"


def read_port(port: str, baud: int, duration_s: float, expected: bytes) -> dict[str, object]:
    entry: dict[str, object] = {"port": port, "baud": baud, "duration_s": duration_s}
    try:
        with serial.Serial(port, baud, timeout=0.05) as ser:
            ser.reset_input_buffer()
            start = time.monotonic()
            data = bytearray()
            while time.monotonic() - start < duration_s:
                chunk = ser.read(256)
                if chunk:
                    data.extend(chunk)
            payload = bytes(data)
            entry.update(
                {
                    "byte_count": len(payload),
                    "hex_prefix": payload[:128].hex(),
                    "ascii_prefix": payload[:128].decode("ascii", "replace"),
                    "contains_expected": expected in payload,
                    "contains_q16_ascii": b"Q16" in payload,
                }
            )
    except Exception as exc:  # pragma: no cover - hardware diagnostic path
        entry.update(
            {
                "byte_count": 0,
                "hex_prefix": "",
                "ascii_prefix": "",
                "contains_expected": False,
                "contains_q16_ascii": False,
                "error": repr(exc),
            }
        )
    return entry


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", action="append", dest="ports", help="serial port to probe; repeatable")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--duration", type=float, default=2.0)
    parser.add_argument("--expected-hex", default=DEFAULT_EXPECTED)
    parser.add_argument("--constraints", default="")
    parser.add_argument("--bitstream", default="4-Infrastructure/hardware/tangnano9k_uart_beacon.fs")
    parser.add_argument("--bitstream-sha256", default="")
    parser.add_argument("--out", default="4-Infrastructure/shim/tang9k_uart_beacon_probe_receipt.json")
    args = parser.parse_args()

    ports = args.ports or ["/dev/ttyUSB0", "/dev/ttyUSB1"]
    expected = bytes.fromhex(args.expected_hex)
    results = [read_port(port, args.baud, args.duration, expected) for port in ports]
    receipt = {
        "schema": "tangnano9k_uart_beacon_probe_v3",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "Probe TX-only UART beacon bytes on host-visible serial ports.",
        "bitstream": args.bitstream,
        "bitstream_sha256": args.bitstream_sha256,
        "constraints": args.constraints,
        "expected_payload_hex": expected.hex(),
        "results": results,
        "conclusion": "PASS" if any(item.get("contains_expected") for item in results) else "FAIL_NO_BEACON_ON_SERIAL_PORTS",
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["conclusion"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
