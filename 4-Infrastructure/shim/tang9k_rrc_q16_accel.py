#!/usr/bin/env python3
"""Host harness for the Tang Nano 9K Rainbow Raccoon Q16.16 surface."""

from __future__ import annotations

import argparse
import json
import struct
import time
from pathlib import Path
from typing import Iterable

MAGIC_IN = 0xA5
MAGIC_OUT = 0xA6
VERSION = 0x02

OP_SHIFT_DIV = 0x20
OP_WEIGHTED = 0x21
OP_MONOTONE = 0x22


def xor_crc(values: Iterable[int]) -> int:
    crc = 0
    for value in values:
        crc ^= value & 0xFF
    return crc


def i32(value: int) -> bytes:
    if not -(1 << 31) <= value < (1 << 31):
        raise ValueError(f"int32 out of range: {value}")
    return struct.pack(">i", value)


def from_i32(data: bytes) -> int:
    return struct.unpack(">i", data)[0]


def build_frame(seq: int, opcode: int, payload: bytes) -> bytes:
    if len(payload) > 16:
        raise ValueError("FPGA payload is limited to 16 bytes")
    frame = bytearray([MAGIC_IN, VERSION, seq & 0xFF, opcode & 0xFF, len(payload)])
    frame.extend(payload)
    frame.append(xor_crc(frame))
    return bytes(frame)


def parse_receipt(frame: bytes) -> dict:
    if len(frame) < 7:
        raise ValueError(f"short receipt frame: {frame.hex()}")
    if frame[0] != MAGIC_OUT or frame[1] != VERSION:
        raise ValueError(f"invalid receipt header: {frame.hex()}")
    payload_len = frame[4]
    expected_len = 6 + payload_len
    if len(frame) != expected_len:
        raise ValueError(f"receipt length mismatch: got {len(frame)}, expected {expected_len}")
    if xor_crc(frame[:-1]) != frame[-1]:
        raise ValueError(f"receipt checksum mismatch: {frame.hex()}")
    payload = frame[5:-1]
    opcode = payload[0] if payload else None
    result = {
        "seq": frame[2],
        "status": frame[3],
        "payload_len": payload_len,
        "opcode": opcode,
        "payload_hex": payload.hex(),
        "crc": frame[-1],
    }
    if payload_len == 6:
        result["result0"] = from_i32(payload[1:5])
        result["pass"] = bool(payload[5])
    elif payload_len == 10:
        result["result0"] = from_i32(payload[1:5])
        result["result1"] = from_i32(payload[5:9])
        result["pass"] = bool(payload[9])
    return result


def _read_receipt_candidate(ser, timeout_s: float = 1.0) -> bytes:
    deadline = time.monotonic() + timeout_s
    buf = bytearray()
    while time.monotonic() < deadline:
        chunk = ser.read(1)
        if not chunk:
            continue
        buf.extend(chunk)
        while buf and buf[0] != MAGIC_OUT:
            del buf[0]
        if len(buf) >= 5:
            need = 6 + buf[4]
            if len(buf) >= need:
                return bytes(buf[:need])
    return bytes(buf)


def send_serial(port: str, baud: int, frame: bytes, retries: int = 5) -> bytes:
    try:
        import serial  # type: ignore
    except ImportError as exc:
        raise SystemExit("pyserial is required for --port mode") from exc

    with serial.Serial(port, baudrate=baud, timeout=2) as ser:
        time.sleep(0.08)
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        last = b""
        for _ in range(max(1, retries)):
            ser.reset_input_buffer()
            ser.write(b"\x00" * 32)
            ser.flush()
            time.sleep(0.02)
            ser.reset_input_buffer()
            ser.write(frame)
            ser.flush()
            raw = _read_receipt_candidate(ser)
            last = raw
            try:
                parsed = parse_receipt(raw)
                if parsed["status"] == 0:
                    return raw
            except ValueError:
                pass
            time.sleep(0.05)
        return last


def make_case(args) -> tuple[str, int, bytes, dict]:
    if args.op == "shift":
        payload = i32(args.x)
        expected = {
            "op": "shift",
            "opcode": OP_SHIFT_DIV,
            "x": args.x,
            "result0": args.x >> 16,
            "pass": True,
            "lean_lemma": "shiftRightEqDiv",
        }
        return args.op, OP_SHIFT_DIV, payload, expected
    if args.op == "weighted":
        payload = i32(args.energy) + i32(args.alpha)
        weighted = (args.energy * args.alpha) >> 16
        passes = (
            args.energy >= 0
            and args.alpha >= 0
            and args.alpha <= 65536
            and weighted <= args.energy
        )
        expected = {
            "op": "weighted",
            "opcode": OP_WEIGHTED,
            "energy": args.energy,
            "alpha": args.alpha,
            "result0": weighted,
            "pass": passes,
            "lean_lemma": "weightedTermBounded",
        }
        return args.op, OP_WEIGHTED, payload, expected
    payload = i32(args.a) + i32(args.b)
    a_shift = args.a >> 16
    b_shift = args.b >> 16
    expected = {
        "op": "monotone",
        "opcode": OP_MONOTONE,
        "a": args.a,
        "b": args.b,
        "result0": a_shift,
        "result1": b_shift,
        "pass": args.a <= args.b and a_shift <= b_shift,
        "lean_lemma": "shiftRightMonotone",
    }
    return args.op, OP_MONOTONE, payload, expected


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--op", choices=["shift", "weighted", "monotone"], default="weighted")
    parser.add_argument("--x", type=lambda v: int(v, 0), default=0x00038000)
    parser.add_argument("--energy", type=lambda v: int(v, 0), default=0x000A0000)
    parser.add_argument("--alpha", type=lambda v: int(v, 0), default=0x00008000)
    parser.add_argument("--a", type=lambda v: int(v, 0), default=0x00010000)
    parser.add_argument("--b", type=lambda v: int(v, 0), default=0x00030000)
    parser.add_argument("--seq", type=lambda v: int(v, 0), default=1)
    parser.add_argument("--port", help="optional USB serial port, e.g. /dev/ttyUSB1")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--retries", type=int, default=5)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    _, opcode, payload, expected = make_case(args)
    frame = build_frame(args.seq, opcode, payload)
    receipt = {
        "schema": "tang9k_rrc_q16_accel_receipt_v1",
        "claim_boundary": "FPGA accelerates deterministic Q16.16 witness arithmetic only; Lean and host admit proofs.",
        "frame_hex": frame.hex(),
        "expected": expected,
        "hardware": None,
        "match": None,
    }

    if args.port:
        raw = send_serial(args.port, args.baud, frame, args.retries)
        receipt["hardware_raw_hex"] = raw.hex()
        try:
            hardware = parse_receipt(raw)
            receipt["hardware"] = hardware
            keys = ["opcode", "result0", "pass"]
            if "result1" in expected:
                keys.append("result1")
            receipt["match"] = hardware["status"] == 0 and all(
                hardware.get(key) == expected.get(key) for key in keys
            )
        except ValueError as exc:
            receipt["hardware_error"] = str(exc)
            receipt["match"] = False
    else:
        receipt["software_only"] = True
        receipt["match"] = True

    output = json.dumps(receipt, indent=2, sort_keys=True)
    if args.out:
        args.out.write_text(output + "\n", encoding="utf-8")
    print(output)
    return 0 if receipt["match"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
