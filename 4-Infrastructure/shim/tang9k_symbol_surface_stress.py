#!/usr/bin/env python3
"""Stress the Tang9K symbol surface over direct UART and IPC serial modes.

This is the next evidence layer after the single full-gambit receipt: it sends
multiple short metaprobe/logogram payloads through the loaded FPGA bitstream and
records pass rate plus coarse host-observed transaction timing.
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path
from types import SimpleNamespace

import gpu_fpga_ipc_symbol_surface as ipc
import tang9k_hutter_symbol_surface as tang


DEFAULT_PAYLOADS = [
    ("ascii_metaprobe_token", "D0A37FEED"),
    ("ascii_metaprobe_token", "F00010203"),
    ("ascii_metaprobe_token", "TRACE"),
    ("ascii_metaprobe_token", "DELTA"),
    ("glyphbook_bank_ids", "0xe101,0xe10f,0x44,0x46"),
    ("glyphbook_bank_ids", "0xe144,0xe146,0xe145,0xe145"),
]


def payload_for(kind: str, value: str) -> tuple[bytes, object]:
    if kind == "glyphbook_bank_ids":
        ids = tang.parse_glyph_ids(value)
        return tang.glyph_ids_to_surface_bytes(ids), [f"0x{x:x}" for x in ids]
    return value.encode("ascii"), value


def summarize_attempts(schema: str, attempts: list[dict], started_ns: int, ended_ns: int) -> dict:
    durations = [item["duration_ms"] for item in attempts]
    passed = [item for item in attempts if item["passed"]]
    return {
        "schema": schema,
        "attempt_count": len(attempts),
        "pass_count": len(passed),
        "fail_count": len(attempts) - len(passed),
        "pass_rate": (len(passed) / len(attempts)) if attempts else 0.0,
        "elapsed_ms": (ended_ns - started_ns) / 1_000_000,
        "duration_ms": {
            "min": min(durations) if durations else 0.0,
            "max": max(durations) if durations else 0.0,
            "mean": statistics.fmean(durations) if durations else 0.0,
        },
        "attempts": attempts,
    }


def run_direct(args: argparse.Namespace) -> dict:
    attempts = []
    started = time.perf_counter_ns()
    for idx in range(args.count):
        kind, value = DEFAULT_PAYLOADS[idx % len(DEFAULT_PAYLOADS)]
        payload, input_value = payload_for(kind, value)
        seq = (args.seq_base + idx) & 0xFF
        frame = tang.build_frame(seq, payload)
        expected = tang.receipt_for_payload(payload)

        t0 = time.perf_counter_ns()
        raw = tang.send_serial(args.port, args.baud, frame, retries=args.retries)
        t1 = time.perf_counter_ns()

        parsed = None
        note = ""
        try:
            parsed = tang.parse_receipt(raw)
            passed = (
                parsed["status"] == 0
                and parsed["seq"] == seq
                and parsed["hash16"] == expected["hash16"]
                and parsed["mapped_count"] == expected["mapped_count"]
                and parsed["literal_count"] == expected["literal_count"]
            )
        except ValueError as exc:
            passed = False
            note = str(exc)

        attempts.append(
            {
                "index": idx,
                "seq": seq,
                "input_kind": kind,
                "input": input_value,
                "payload_hex": payload.hex(),
                "duration_ms": (t1 - t0) / 1_000_000,
                "passed": passed,
                "raw_receipt_hex": raw.hex(),
                "hardware_receipt": parsed,
                "expected_hash": expected["hash16"],
                "note": note,
            }
        )
    ended = time.perf_counter_ns()
    return summarize_attempts("tang9k_symbol_surface_direct_stress_v1", attempts, started, ended)


def run_ipc(args: argparse.Namespace) -> dict:
    ring = args.ring
    init_args = SimpleNamespace(ring=ring, slots=args.slots)
    ipc.cmd_init(init_args)

    attempts = []
    started = time.perf_counter_ns()
    for idx in range(args.count):
        kind, value = DEFAULT_PAYLOADS[idx % len(DEFAULT_PAYLOADS)]
        seq = (args.seq_base + 1000 + idx) & 0xFFFF
        produce_args = SimpleNamespace(
            ring=ring,
            text=value if kind == "ascii_metaprobe_token" else "",
            glyph_ids=value if kind == "glyphbook_bank_ids" else None,
            seq=seq,
            serial=True,
        )
        consume_args = SimpleNamespace(
            ring=ring,
            port=args.port,
            baud=args.baud,
            retries=args.retries,
            max_records=1,
        )

        t0 = time.perf_counter_ns()
        produced = ipc.cmd_produce(produce_args)
        consumed = ipc.cmd_consume(consume_args)
        t1 = time.perf_counter_ns()

        receipts = consumed.get("receipts", [])
        receipt = receipts[0] if receipts else {}
        passed = bool(
            receipt.get("status") == "done"
            and receipt.get("hardware_status") == 0
            and receipt.get("receipt_hash") == produced["expected"]["hash16"]
        )
        attempts.append(
            {
                "index": idx,
                "seq": seq,
                "input_kind": produced["input_kind"],
                "input": produced["input"],
                "payload_hex": produced["payload_hex"],
                "duration_ms": (t1 - t0) / 1_000_000,
                "passed": passed,
                "producer_slot": produced["slot"],
                "receipt": receipt,
            }
        )
    ended = time.perf_counter_ns()
    status = ipc.cmd_status(SimpleNamespace(ring=ring))
    result = summarize_attempts("tang9k_symbol_surface_ipc_stress_v1", attempts, started, ended)
    result["ring"] = str(ring)
    result["final_ring_status"] = status
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default="/dev/ttyUSB1")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--count", type=int, default=24)
    parser.add_argument("--retries", type=int, default=6)
    parser.add_argument("--seq-base", type=int, default=120)
    parser.add_argument("--slots", type=int, default=32)
    parser.add_argument("--ring", type=Path, default=Path("/dev/shm/tang9k_symbol_surface_stress.ring"))
    parser.add_argument("--mode", choices=["direct", "ipc", "both"], default="both")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    report = {
        "schema": "tang9k_symbol_surface_stress_report_v1",
        "port": args.port,
        "baud": args.baud,
        "count": args.count,
        "retries": args.retries,
        "claim_boundary": "Tang FPGA accelerates the substitution witness; host owns full codec/decodec and IPC staging.",
    }
    if args.mode in {"direct", "both"}:
        report["direct"] = run_direct(args)
    if args.mode in {"ipc", "both"}:
        report["ipc"] = run_ipc(args)

    text = json.dumps(report, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
