#!/usr/bin/env python3
"""Host harness for Tang9K Hutter/metaprobe symbol surface.

This harness frames short compressed text tokens for the FPGA and computes the
same substitution receipt in software. If --port is supplied and pyserial is
installed, it also sends the frame over USB UART.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Iterable

MAGIC_IN = 0xA5
MAGIC_OUT = 0xA6
VERSION = 0x01
OP_SUBSTITUTE = 0x10


def substitute(byte: int) -> tuple[int, bool]:
    table = {
        ord(" "): 0x0,
        ord("e"): 0x1,
        ord("E"): 0x1,
        ord("t"): 0x2,
        ord("T"): 0x2,
        ord("a"): 0x3,
        ord("A"): 0x3,
        ord("o"): 0x4,
        ord("O"): 0x4,
        ord("i"): 0x5,
        ord("I"): 0x5,
        ord("n"): 0x6,
        ord("N"): 0x6,
        ord("s"): 0x7,
        ord("S"): 0x7,
        ord("r"): 0x8,
        ord("R"): 0x8,
        ord("h"): 0x9,
        ord("H"): 0x9,
        ord("l"): 0xA,
        ord("L"): 0xA,
        ord("d"): 0xB,
        ord("c"): 0xC,
        ord("C"): 0xC,
        ord("u"): 0xD,
        ord("U"): 0xD,
        ord("F"): 0xE,
        ord("D"): 0xF,
    }
    if byte in table:
        return table[byte], True
    return byte & 0xF, False


def xor_crc(values: Iterable[int]) -> int:
    crc = 0
    for value in values:
        crc ^= value & 0xFF
    return crc


def receipt_for_payload(payload: bytes) -> dict:
    rolling_hash = 0xACE1
    mapped = 0
    literal = 0
    codes = []
    for byte in payload:
        code, hit = substitute(byte)
        codes.append({"byte": byte, "char": chr(byte), "code": code, "hit": hit})
        rolling_hash = (((rolling_hash << 1) & 0xFFFF) | (rolling_hash >> 15)) ^ (
            (0x10 if hit else 0x00) | code
        )
        if hit:
            mapped += 1
        else:
            literal += 1
    return {
        "hash16": rolling_hash,
        "mapped_count": mapped,
        "literal_count": literal,
        "codes": codes,
    }


def pbacs_cmyk_state_for_payload(payload: bytes) -> int:
    error_acc = 0
    stress_acc = 0
    mapped_count = 0
    literal_count = 0
    for byte in payload:
        code, hit = substitute(byte)
        value_q16 = ((1 if hit else 0) << 15) | (code << 11)
        candidate = value_q16 + error_acc
        bit_out = 1 if candidate > 0x8000 else 0
        error_acc = candidate - (0x10000 if bit_out else 0)
        abs_error = abs(error_acc)
        residual_term = (abs_error >> 4) & 0x3FFF
        mismatch_term = ((literal_count & 0x0F) << 4) | (mapped_count & 0x0F)
        mask_term = (1 if hit else 0) << 4
        stress_acc = max(
            0,
            min(
                0xFFFF,
                stress_acc - (stress_acc >> 6) + residual_term + mismatch_term + mask_term,
            ),
        )
        if hit:
            mapped_count += 1
        else:
            literal_count += 1
    return (stress_acc >> 14) & 0x03


def led_reservoir_address(route_state: int, mapped_count: int) -> dict:
    logical = ((route_state & 0x03) << 4) | (mapped_count & 0x0F)
    physical_active_low = logical ^ 0x3F
    return {
        "schema": "tang9k_led_reservoir_address_v1",
        "logical_bits": f"{logical:06b}",
        "logical_hex": f"0x{logical:02x}",
        "route_state": (logical >> 4) & 0x03,
        "mapped_bucket": logical & 0x0F,
        "physical_active_low_bits": f"{physical_active_low:06b}",
        "physical_active_low_hex": f"0x{physical_active_low:02x}",
        "meaning": "logical LED reservoir address is {PBACS/CMYK route_state[1:0], mapped_count[3:0]}; board LEDs are active low",
    }


def build_frame(seq: int, payload: bytes) -> bytes:
    if len(payload) > 16:
        raise ValueError("Surface-0 payload is limited to 16 bytes per frame")
    frame = bytearray([MAGIC_IN, VERSION, seq & 0xFF, OP_SUBSTITUTE, len(payload)])
    frame.extend(payload)
    frame.append(xor_crc(frame))
    return bytes(frame)


def parse_glyph_ids(value: str) -> list[int]:
    glyph_ids = []
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        glyph_ids.append(int(part, 0))
    return glyph_ids


def glyph_ids_to_surface_bytes(glyph_ids: list[int]) -> bytes:
    if len(glyph_ids) > 16:
        raise ValueError("Surface-0 accepts at most 16 glyph IDs per frame")
    # Surface-0 works on bank-local glyph IDs. The host GlyphBook maps full
    # Unicode/PUA/custom logograms to these low-byte hot-path banks.
    return bytes(glyph_id & 0xFF for glyph_id in glyph_ids)


def parse_receipt(frame: bytes) -> dict:
    if len(frame) != 11 or frame[0] != MAGIC_OUT or frame[1] != VERSION:
        raise ValueError(f"invalid receipt frame: {frame.hex()}")
    if xor_crc(frame[:-1]) != frame[-1]:
        raise ValueError("receipt checksum mismatch")
    return {
        "seq": frame[2],
        "status": frame[3],
        "payload_len": frame[4],
        "opcode": frame[5],
        "hash16": (frame[6] << 8) | frame[7],
        "mapped_count": frame[8],
        "literal_count": frame[9],
        "crc": frame[10],
    }


def _read_receipt_candidate(ser, timeout_s: float = 0.75) -> bytes:
    deadline = time.monotonic() + timeout_s
    buf = bytearray()
    while time.monotonic() < deadline:
        chunk = ser.read(1)
        if not chunk:
            continue
        buf.extend(chunk)
        while buf and buf[0] != MAGIC_OUT:
            del buf[0]
        if len(buf) >= 11:
            return bytes(buf[:11])
    return bytes(buf)


def send_serial(port: str, baud: int, frame: bytes, retries: int = 5, resync: bool = True) -> bytes:
    try:
        import serial  # type: ignore
    except ImportError as exc:
        raise SystemExit("pyserial is required for --port mode") from exc

    with serial.Serial(port, baudrate=baud, timeout=2) as ser:
        time.sleep(0.05)
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        last = b""
        for _ in range(max(1, retries)):
            ser.reset_input_buffer()
            if resync:
                # If the FPGA UART parser is stranded in payload/CRC state,
                # enough non-magic bytes complete the partial frame and return
                # it to RX_WAIT_MAGIC. In wait state, these bytes are ignored.
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", default="D0A37FEED", help="compressed token text")
    parser.add_argument(
        "--glyph-ids",
        help="comma-separated logogram/GlyphBook IDs; e.g. 0xe101,0xe10f,0x42",
    )
    parser.add_argument("--seq", type=lambda x: int(x, 0), default=1)
    parser.add_argument("--port", help="optional USB serial port, e.g. /dev/ttyUSB1")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--retries", type=int, default=5)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    glyph_ids = parse_glyph_ids(args.glyph_ids) if args.glyph_ids else []
    if glyph_ids:
        payload = glyph_ids_to_surface_bytes(glyph_ids)
        input_kind = "glyphbook_bank_ids"
        input_value = [f"0x{glyph_id:x}" for glyph_id in glyph_ids]
    else:
        payload = args.text.encode("ascii")
        input_kind = "ascii_metaprobe_token"
        input_value = args.text
    frame = build_frame(args.seq, payload)
    expected = receipt_for_payload(payload)
    result = {
        "schema": "tang9k_hutter_symbol_surface_receipt_v1",
        "claim_boundary": "FPGA accelerates substitution witness only; host owns full codec/decodec",
        "input_kind": input_kind,
        "input": input_value,
        "surface_payload_hex": payload.hex(),
        "frame_hex": frame.hex(),
        "expected": expected,
        "expected_led_reservoir": led_reservoir_address(
            pbacs_cmyk_state_for_payload(payload), expected["mapped_count"]
        ),
    }

    if args.port:
        raw_receipt = send_serial(args.port, args.baud, frame, retries=args.retries)
        result["hardware_receipt_hex"] = raw_receipt.hex()
        if raw_receipt:
            try:
                parsed = parse_receipt(raw_receipt)
                result["hardware_receipt"] = parsed
                result["hardware_led_reservoir"] = led_reservoir_address(
                    pbacs_cmyk_state_for_payload(payload), parsed["mapped_count"]
                )
                result["hardware_matches_expected"] = (
                    parsed["status"] == 0
                    and parsed["hash16"] == expected["hash16"]
                    and parsed["mapped_count"] == expected["mapped_count"]
                    and parsed["literal_count"] == expected["literal_count"]
                )
            except ValueError as exc:
                result["hardware_receipt"] = None
                result["hardware_matches_expected"] = False
                result["hardware_note"] = f"non-surface UART response: {exc}"
        else:
            result["hardware_receipt"] = None
            result["hardware_matches_expected"] = False
            result["hardware_note"] = "no UART receipt received; topology is present but expected bitstream may not be loaded"

    text = json.dumps(result, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
