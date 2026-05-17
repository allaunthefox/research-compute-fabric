#!/usr/bin/env python3
"""PTY-backed virtual serial probe for the Tang Nano 9K Q16 host protocol.

This creates a local pseudo-terminal, runs a small responder that speaks the
same framed Q16 receipt protocol as the FPGA surface, then drives the existing
host harness through the PTY path. It proves host serial framing and parsing,
not live FPGA fabric behavior.
"""

from __future__ import annotations

import argparse
import json
import os
import pty
import select
import struct
import subprocess
import threading
import time
import tty
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tang9k_rrc_q16_accel import (
    MAGIC_IN,
    MAGIC_OUT,
    OP_MONOTONE,
    OP_SHIFT_DIV,
    OP_WEIGHTED,
    VERSION,
    xor_crc,
)


REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "shared-data" / "data" / "stack_solidification" / "tang9k_rrc_q16_virtual_serial_probe.json"
DOC = REPO / "6-Documentation" / "docs" / "tang9k_rrc_q16_virtual_serial_probe_2026-05-09.md"


def i32(value: int) -> bytes:
    return struct.pack(">i", value)


def from_i32(data: bytes) -> int:
    return struct.unpack(">i", data)[0]


def response_frame(seq: int, status: int, payload: bytes) -> bytes:
    frame = bytearray([MAGIC_OUT, VERSION, seq & 0xFF, status & 0xFF, len(payload)])
    frame.extend(payload)
    frame.append(xor_crc(frame))
    return bytes(frame)


def emulate_frame(frame: bytes) -> bytes:
    if len(frame) < 6 or frame[0] != MAGIC_IN or frame[1] != VERSION:
        return response_frame(0, 0xE1, b"\x00")
    seq = frame[2]
    opcode = frame[3]
    payload_len = frame[4]
    payload = frame[5 : 5 + payload_len]
    crc = frame[5 + payload_len] if len(frame) > 5 + payload_len else None
    if len(payload) != payload_len or crc is None or xor_crc(frame[:-1]) != crc:
        return response_frame(seq, 0xE2, bytes([opcode]))

    if opcode == OP_SHIFT_DIV and payload_len == 4:
        x = from_i32(payload)
        result0 = x >> 16
        return response_frame(seq, 0, bytes([opcode]) + i32(result0) + b"\x01")
    if opcode == OP_WEIGHTED and payload_len == 8:
        energy = from_i32(payload[:4])
        alpha = from_i32(payload[4:])
        result0 = (energy * alpha) >> 16
        passed = energy >= 0 and alpha >= 0 and alpha <= 65536 and result0 <= energy
        return response_frame(seq, 0, bytes([opcode]) + i32(result0) + bytes([1 if passed else 0]))
    if opcode == OP_MONOTONE and payload_len == 8:
        a = from_i32(payload[:4])
        b = from_i32(payload[4:])
        result0 = a >> 16
        result1 = b >> 16
        passed = a <= b and result0 <= result1
        return response_frame(seq, 0, bytes([opcode]) + i32(result0) + i32(result1) + bytes([1 if passed else 0]))
    return response_frame(seq, 0xE3, bytes([opcode]))


class VirtualResponder:
    def __init__(self, master_fd: int) -> None:
        self.master_fd = master_fd
        self.stop = threading.Event()
        self.frames_seen: list[dict[str, Any]] = []
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self.thread.start()

    def close(self) -> None:
        self.stop.set()
        self.thread.join(timeout=1.0)

    def _read_exactish(self, size: int, timeout_s: float = 1.0) -> bytes:
        deadline = time.monotonic() + timeout_s
        data = bytearray()
        while len(data) < size and time.monotonic() < deadline and not self.stop.is_set():
            ready, _, _ = select.select([self.master_fd], [], [], 0.05)
            if not ready:
                continue
            chunk = os.read(self.master_fd, size - len(data))
            if chunk:
                data.extend(chunk)
        return bytes(data)

    def _run(self) -> None:
        buf = bytearray()
        while not self.stop.is_set():
            ready, _, _ = select.select([self.master_fd], [], [], 0.05)
            if not ready:
                continue
            chunk = os.read(self.master_fd, 256)
            if not chunk:
                continue
            buf.extend(chunk)
            while buf:
                while buf and buf[0] != MAGIC_IN:
                    del buf[0]
                if len(buf) < 5:
                    break
                need = 6 + buf[4]
                if len(buf) < need:
                    break
                frame = bytes(buf[:need])
                del buf[:need]
                reply = emulate_frame(frame)
                os.write(self.master_fd, reply)
                self.frames_seen.append({"request_hex": frame.hex(), "response_hex": reply.hex()})


def run_case(port: str, name: str, args: list[str]) -> dict[str, Any]:
    out_path = REPO / "4-Infrastructure" / "shim" / f"tang9k_rrc_q16_virtual_{name}_receipt.json"
    cmd = [
        "python3",
        "4-Infrastructure/shim/tang9k_rrc_q16_accel.py",
        *args,
        "--port",
        port,
        "--retries",
        "1",
        "--out",
        str(out_path.relative_to(REPO)),
    ]
    proc = subprocess.run(
        cmd,
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )
    receipt = json.loads(out_path.read_text(encoding="utf-8")) if out_path.exists() else {}
    return {
        "case": name,
        "command": cmd,
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
        "receipt": str(out_path.relative_to(REPO)),
        "match": receipt.get("match"),
        "hardware": receipt.get("hardware"),
    }


def build_doc(receipt: dict[str, Any]) -> str:
    lines = [
        "# Tang Nano 9K Q16 Virtual Serial Probe",
        "",
        "**Date:** 2026-05-09",
        "",
        receipt["claim_boundary"],
        "",
        "## Status",
        "",
        f"- Status: `{receipt['summary']['status']}`",
        f"- Cases: `{receipt['summary']['case_count']}`",
        f"- Matches: `{receipt['summary']['match_count']}`",
        "",
        "## Cases",
        "",
    ]
    for case in receipt["cases"]:
        lines.append(f"- `{case['case']}`: match `{case['match']}`, receipt `{case['receipt']}`")
    lines.extend(["", "## Machine Receipt", "", f"- `{OUT.relative_to(REPO)}`"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()

    master_fd, slave_fd = pty.openpty()
    tty.setraw(master_fd)
    tty.setraw(slave_fd)
    slave_path = os.ttyname(slave_fd)
    responder = VirtualResponder(master_fd)
    responder.start()
    try:
        cases = [
            run_case(slave_path, "shift", ["--op", "shift", "--x", "0x00038000"]),
            run_case(slave_path, "weighted", ["--op", "weighted", "--energy", "0x000a0000", "--alpha", "0x00008000"]),
            run_case(slave_path, "monotone", ["--op", "monotone", "--a", "0x00010000", "--b", "0x00030000"]),
        ]
    finally:
        responder.close()
        os.close(master_fd)
        os.close(slave_fd)

    match_count = sum(1 for case in cases if case.get("match") is True)
    receipt = {
        "schema": "tang9k_rrc_q16_virtual_serial_probe_v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "claim_boundary": (
            "Virtual serial probe only. This validates the host Q16 UART framing, "
            "receipt parser, and opcode semantics over a PTY-backed serial device; "
            "it does not validate live FPGA fabric or the Tang Nano UART route."
        ),
        "virtual_port": slave_path,
        "summary": {
            "status": "PASS_VIRTUAL_SERIAL" if match_count == len(cases) else "FAIL",
            "case_count": len(cases),
            "match_count": match_count,
            "frames_seen": len(responder.frames_seen),
        },
        "cases": cases,
        "virtual_frames": responder.frames_seen,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    DOC.write_text(build_doc(receipt), encoding="utf-8")
    print(json.dumps({"receipt": str(args.out.relative_to(REPO)), "doc": str(DOC.relative_to(REPO)), "status": receipt["summary"]["status"]}, indent=2))
    return 0 if receipt["summary"]["status"] == "PASS_VIRTUAL_SERIAL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
