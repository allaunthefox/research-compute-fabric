#!/usr/bin/env python3
"""IPC bridge for GPU/codec producers and the Tang9K symbol surface.

The file in /dev/shm is a fixed-record ring:

  producer: GPU/codec/logogram process writes glyph payload records
  consumer: FPGA worker reads pending records and writes receipt fields

This does not grant the USB-attached Tang direct VRAM access. It creates a
host-mediated topological projection of a GPU work surface into a hardware
symbol-substitution witness lane.

The layout follows the older Research Stack cache-line IPC trick:
64-byte header, 64-byte records, monotonic read/write indices. Python cannot
provide Rust-style atomics, but the ABI is cache-line shaped so a Rust/C worker
can later use acquire/release loads without changing the on-disk ring format.
"""

from __future__ import annotations

import argparse
import json
import mmap
import os
import struct
import time
from pathlib import Path

import tang9k_hutter_symbol_surface as tang

DEFAULT_RING = Path("/dev/shm/tang9k_gpu_fpga_symbol_surface.ring")
MAGIC = b"T9IP"
VERSION = 1
SLOTS = 256
# 64-byte cache-line shaped structures. Keep these sizes stable.
HEADER = struct.Struct("<4sIIII44x")
RECORD = struct.Struct("<BBH16sHHBBBBQ28x")

STATUS_EMPTY = 0
STATUS_PENDING = 1
STATUS_DONE = 2
STATUS_ERROR = 3

MODE_SOFTWARE = 0
MODE_SERIAL = 1


def ring_size(slots: int = SLOTS) -> int:
    return HEADER.size + (RECORD.size * slots)


def open_ring(path: Path, create: bool = False, slots: int = SLOTS) -> mmap.mmap:
    if create:
        fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
        os.ftruncate(fd, ring_size(slots))
    else:
        fd = os.open(path, os.O_RDWR)
    return mmap.mmap(fd, 0)


def write_header(mm: mmap.mmap, slots: int = SLOTS) -> None:
    mm.seek(0)
    mm.write(HEADER.pack(MAGIC, VERSION, slots, 0, 0))


def read_header(mm: mmap.mmap) -> dict:
    mm.seek(0)
    magic, version, slots, write_index, read_index = HEADER.unpack(mm.read(HEADER.size))
    if magic != MAGIC:
        raise ValueError("not a Tang9K IPC symbol surface ring")
    return {
        "version": version,
        "slots": slots,
        "write_index": write_index,
        "read_index": read_index,
    }


def update_indices(mm: mmap.mmap, write_index: int, read_index: int) -> None:
    header = read_header(mm)
    mm.seek(0)
    mm.write(HEADER.pack(MAGIC, header["version"], header["slots"], write_index, read_index))


def record_offset(slot: int) -> int:
    return HEADER.size + (slot * RECORD.size)


def read_record(mm: mmap.mmap, slot: int) -> dict:
    mm.seek(record_offset(slot))
    (
        status,
        mode,
        seq,
        payload,
        expected_hash,
        receipt_hash,
        mapped,
        literal,
        hw_status,
        payload_len,
        timestamp_ns,
    ) = RECORD.unpack(mm.read(RECORD.size))
    return {
        "status": status,
        "mode": mode,
        "seq": seq,
        "payload": payload[:payload_len],
        "payload_hex": payload[:payload_len].hex(),
        "payload_len": payload_len,
        "expected_hash": expected_hash,
        "receipt_hash": receipt_hash,
        "mapped": mapped,
        "literal": literal,
        "hw_status": hw_status,
        "timestamp_ns": timestamp_ns,
    }


def write_record(
    mm: mmap.mmap,
    slot: int,
    *,
    status: int,
    mode: int,
    seq: int,
    payload: bytes,
    expected_hash: int,
    receipt_hash: int = 0,
    mapped: int = 0,
    literal: int = 0,
    hw_status: int = 0,
) -> None:
    if len(payload) > 16:
        raise ValueError("payload exceeds 16-byte Surface-0 record")
    padded = payload.ljust(16, b"\x00")
    mm.seek(record_offset(slot))
    mm.write(
        RECORD.pack(
            status,
            mode,
            seq & 0xFFFF,
            padded,
            expected_hash & 0xFFFF,
            receipt_hash & 0xFFFF,
            mapped & 0xFF,
            literal & 0xFF,
            hw_status & 0xFF,
            len(payload),
            time.time_ns(),
        )
    )


def payload_from_args(args: argparse.Namespace) -> tuple[bytes, str, object]:
    if args.glyph_ids:
        glyph_ids = tang.parse_glyph_ids(args.glyph_ids)
        return (
            tang.glyph_ids_to_surface_bytes(glyph_ids),
            "glyphbook_bank_ids",
            [f"0x{glyph_id:x}" for glyph_id in glyph_ids],
        )
    return args.text.encode("ascii"), "ascii_metaprobe_token", args.text


def cmd_init(args: argparse.Namespace) -> dict:
    mm = open_ring(args.ring, create=True, slots=args.slots)
    write_header(mm, args.slots)
    mm.flush()
    return {
        "schema": "gpu_fpga_ipc_symbol_surface_init_v1",
        "ring": str(args.ring),
        "slots": args.slots,
        "bytes": ring_size(args.slots),
    }


def cmd_produce(args: argparse.Namespace) -> dict:
    payload, input_kind, input_value = payload_from_args(args)
    expected = tang.receipt_for_payload(payload)
    mm = open_ring(args.ring)
    header = read_header(mm)
    slot = header["write_index"] % header["slots"]
    current = read_record(mm, slot)
    if current["status"] == STATUS_PENDING:
        raise SystemExit(f"slot {slot} is still pending")
    write_record(
        mm,
        slot,
        status=STATUS_PENDING,
        mode=MODE_SERIAL if args.serial else MODE_SOFTWARE,
        seq=args.seq,
        payload=payload,
        expected_hash=expected["hash16"],
    )
    update_indices(mm, header["write_index"] + 1, header["read_index"])
    mm.flush()
    return {
        "schema": "gpu_fpga_ipc_symbol_surface_produce_v1",
        "ring": str(args.ring),
        "slot": slot,
        "seq": args.seq,
        "input_kind": input_kind,
        "input": input_value,
        "payload_hex": payload.hex(),
        "expected": expected,
    }


def consume_one(mm: mmap.mmap, port: str | None, baud: int, retries: int = 5) -> dict | None:
    header = read_header(mm)
    for idx in range(header["slots"]):
        slot = (header["read_index"] + idx) % header["slots"]
        record = read_record(mm, slot)
        if record["status"] != STATUS_PENDING:
            continue

        payload = record["payload"]
        expected = tang.receipt_for_payload(payload)
        hw_status = 0
        note = ""
        receipt_hash = expected["hash16"]
        mapped = expected["mapped_count"]
        literal = expected["literal_count"]

        if record["mode"] == MODE_SERIAL and port:
            frame = tang.build_frame(record["seq"], payload)
            raw = tang.send_serial(port, baud, frame, retries=retries)
            try:
                parsed = tang.parse_receipt(raw)
                hw_status = parsed["status"]
                receipt_hash = parsed["hash16"]
                mapped = parsed["mapped_count"]
                literal = parsed["literal_count"]
            except ValueError as exc:
                hw_status = 0xEE
                note = f"non-surface UART response: {exc}"

        status = STATUS_DONE if receipt_hash == record["expected_hash"] and hw_status == 0 else STATUS_ERROR
        write_record(
            mm,
            slot,
            status=status,
            mode=record["mode"],
            seq=record["seq"],
            payload=payload,
            expected_hash=record["expected_hash"],
            receipt_hash=receipt_hash,
            mapped=mapped,
            literal=literal,
            hw_status=hw_status,
        )
        update_indices(mm, header["write_index"], slot + 1)
        mm.flush()
        return {
            "slot": slot,
            "seq": record["seq"],
            "mode": "serial" if record["mode"] == MODE_SERIAL else "software",
            "status": "done" if status == STATUS_DONE else "error",
            "payload_hex": payload.hex(),
            "expected_hash": record["expected_hash"],
            "receipt_hash": receipt_hash,
            "mapped_count": mapped,
            "literal_count": literal,
            "hardware_status": hw_status,
            "note": note,
        }
    return None


def cmd_consume(args: argparse.Namespace) -> dict:
    mm = open_ring(args.ring)
    receipts = []
    for _ in range(args.max_records):
        receipt = consume_one(mm, args.port, args.baud, retries=args.retries)
        if receipt is None:
            break
        receipts.append(receipt)
    return {
        "schema": "gpu_fpga_ipc_symbol_surface_consume_v1",
        "ring": str(args.ring),
        "receipt_count": len(receipts),
        "receipts": receipts,
    }


def cmd_status(args: argparse.Namespace) -> dict:
    mm = open_ring(args.ring)
    header = read_header(mm)
    counts = {str(STATUS_EMPTY): 0, str(STATUS_PENDING): 0, str(STATUS_DONE): 0, str(STATUS_ERROR): 0}
    for slot in range(header["slots"]):
        status = read_record(mm, slot)["status"]
        counts[str(status)] = counts.get(str(status), 0) + 1
    return {
        "schema": "gpu_fpga_ipc_symbol_surface_status_v1",
        "ring": str(args.ring),
        "header": header,
        "status_counts": counts,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ring", type=Path, default=DEFAULT_RING)
    sub = parser.add_subparsers(dest="cmd", required=True)

    init = sub.add_parser("init")
    init.add_argument("--slots", type=int, default=SLOTS)

    produce = sub.add_parser("produce")
    produce.add_argument("--text", default="D0A37FEED")
    produce.add_argument("--glyph-ids")
    produce.add_argument("--seq", type=lambda x: int(x, 0), default=1)
    produce.add_argument("--serial", action="store_true")

    consume = sub.add_parser("consume")
    consume.add_argument("--port")
    consume.add_argument("--baud", type=int, default=115200)
    consume.add_argument("--retries", type=int, default=5)
    consume.add_argument("--max-records", type=int, default=1)

    sub.add_parser("status")

    args = parser.parse_args()
    if args.cmd == "init":
        result = cmd_init(args)
    elif args.cmd == "produce":
        result = cmd_produce(args)
    elif args.cmd == "consume":
        result = cmd_consume(args)
    else:
        result = cmd_status(args)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
