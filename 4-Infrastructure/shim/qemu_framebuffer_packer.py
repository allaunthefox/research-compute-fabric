#!/usr/bin/env python3
"""
QEMU Framebuffer Packer — Use virtual graphics framebuffer (/dev/fb0) as a DMA computation backplane.

Packs Q16_16 fixed-point matrices directly into framebuffer pixel words:
  - ARGB8888 (32-bit): 1 pixel = 1 Q16_16 scalar (100% density mapping)
  - RGB24 (24-bit): 1 pixel = 3 bytes of raw payload data

Enforces the core principles of the Research Stack:
  - NO FLOATS in compute paths. Fixed-point Q16_16 only.
  - Zero-copy mapping via mmap on /dev/fb0.
  - Machine-readable receipt generation.
"""

from __future__ import annotations

import os
import sys
import mmap
import json
import struct
import argparse
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Tuple, List, Dict, Any

# Framebuffer constants
SIGNATURE_HEADER = b"RDMAVCN\0"
SIGNATURE_SIZE = 24


@dataclass
class FramebufferReceipt:
    """Receipt for a framebuffer DMA computation packet."""
    schema: str = "qemu_framebuffer_receipt_v1"
    width: int = 1920
    height: int = 1080
    format: str = "ARGB8888"
    payload_bytes: int = 0
    pixel_count: int = 0
    seq: int = 0
    version: int = 1
    witness_hash: str = ""


def _crc32(data: bytes) -> int:
    import zlib
    return zlib.crc32(data) & 0xFFFFFFFF


def pack_q16_to_argb32(values: List[int]) -> bytes:
    """Pack Q16_16 raw integers directly into ARGB32 bytes.

    Each 32-bit value maps exactly to 1 ARGB pixel word (4 bytes).
    Little-endian representation:
      - Byte 0: Blue (lowest 8 bits of Q16_16)
      - Byte 1: Green
      - Byte 2: Red
      - Byte 3: Alpha (highest 8 bits of Q16_16)
    """
    # Pack values in little-endian format
    return struct.pack(f"<{len(values)}I", *values)


def unpack_argb32_to_q16(data: bytes) -> List[int]:
    """Unpack ARGB32 pixel bytes back to Q16_16 raw integers."""
    count = len(data) // 4
    return list(struct.unpack(f"<{count}I", data[:count * 4]))


def pack_bytes_to_rgb24(data: bytes) -> bytes:
    """Pack raw bytes directly into RGB24 format (3 bytes per pixel)."""
    # RGB24 is already raw bytes, so just return or verify length
    return data


def unpack_rgb24_to_bytes(data: bytes) -> bytes:
    """Unpack RGB24 pixel bytes back to raw computation bytes."""
    return data


def write_to_framebuffer(
    device_path: str,
    data: bytes,
    seq: int,
    width: int = 1920,
    height: int = 1080,
    pix_format: str = "ARGB8888"
) -> FramebufferReceipt:
    """Write compute payload directly to /dev/fb0 using zero-copy mmap.

    Layout:
      - Bytes 0-23: Signature header (RDMAVCN\0 + version + seq + length + format_tag)
      - Bytes 24+: Raw data packed into pixels
    """
    version = 1
    length = len(data)

    # Encode format tag
    # 0 = ARGB8888, 1 = RGB24
    format_tag = 0 if pix_format == "ARGB8888" else 1

    # Header structure: Signature(8B) + Version(4B) + Seq(4B) + Length(4B) + FormatTag(4B)
    header = SIGNATURE_HEADER + struct.pack("<IIII", version, seq, length, format_tag)

    total_bytes_needed = SIGNATURE_SIZE + length

    # 1. Prepare raw frame array
    frame_buf = bytearray(total_bytes_needed)
    frame_buf[:SIGNATURE_SIZE] = header
    frame_buf[SIGNATURE_SIZE:] = data

    # 2. Open framebuffer device
    fb_fd = os.open(device_path, os.O_RDWR)
    try:
        # Map framebuffer to memory
        # Framebuffer size = width * height * (4 for 32-bit, 3 for 24-bit)
        bpp = 4 if pix_format == "ARGB8888" else 3
        fb_size = width * height * bpp

        # If data size exceeds framebuffer capacity, raise error
        if len(frame_buf) > fb_size:
            raise ValueError(f"Payload size ({len(frame_buf)} bytes) exceeds framebuffer capacity ({fb_size} bytes)")

        fb_map = mmap.mmap(fb_fd, fb_size, mmap.MAP_SHARED, mmap.PROT_WRITE)
        try:
            # Zero-copy write to framebuffer memory
            fb_map[:len(frame_buf)] = frame_buf
            # Flush changes to display hardware
            fb_map.flush()
        finally:
            fb_map.close()
    finally:
        os.close(fb_fd)

    receipt = FramebufferReceipt(
        width=width,
        height=height,
        format=pix_format,
        payload_bytes=length,
        pixel_count=length // bpp,
        seq=seq,
        version=version,
        witness_hash=f"{_crc32(frame_buf):08x}"
    )
    return receipt


def read_from_framebuffer(
    device_path: str,
    width: int = 1920,
    height: int = 1080,
    pix_format: str = "ARGB8888"
) -> Tuple[bytes, FramebufferReceipt]:
    """Read compute payload directly from /dev/fb0 using mmap."""
    bpp = 4 if pix_format == "ARGB8888" else 3
    fb_size = width * height * bpp

    fb_fd = os.open(device_path, os.O_RDONLY)
    try:
        fb_map = mmap.mmap(fb_fd, fb_size, mmap.MAP_SHARED, mmap.PROT_READ)
        try:
            # Read signature header
            header = fb_map[:SIGNATURE_SIZE]
            signature, version, seq, length, format_tag = struct.unpack("<8sIIII", header)

            if signature != SIGNATURE_HEADER:
                raise ValueError(f"Invalid framebuffer signature: {signature}")

            # Read payload
            payload = fb_map[SIGNATURE_SIZE:SIGNATURE_SIZE + length]
            frame_buf = header + payload

            receipt = FramebufferReceipt(
                width=width,
                height=height,
                format="ARGB8888" if format_tag == 0 else "RGB24",
                payload_bytes=length,
                pixel_count=length // bpp,
                seq=seq,
                version=version,
                witness_hash=f"{_crc32(frame_buf):08x}"
            )
            return payload, receipt
        finally:
            fb_map.close()
    finally:
        os.close(fb_fd)


def main():
    parser = argparse.ArgumentParser(description="QEMU Framebuffer Packing tool")
    subparsers = parser.add_subparsers(dest="command")

    # pack command
    pack_parser = subparsers.add_parser("pack")
    pack_parser.add_argument("input", type=str, help="Input raw Q16_16 binary file")
    pack_parser.add_argument("output", type=str, help="Output packed framebuffer file")
    pack_parser.add_argument("--format", type=str, default="ARGB8888", choices=["ARGB8888", "RGB24"])

    # unpack command
    unpack_parser = subparsers.add_parser("unpack")
    unpack_parser.add_argument("input", type=str, help="Input packed framebuffer file")
    unpack_parser.add_argument("output", type=str, help="Output raw Q16_16 binary file")
    unpack_parser.add_argument("--format", type=str, default="ARGB8888", choices=["ARGB8888", "RGB24"])

    # write-fb command
    write_parser = subparsers.add_parser("write-fb")
    write_parser.add_argument("input", type=str, help="Input raw Q16_16 binary file")
    write_parser.add_argument("--device", type=str, default="/dev/fb0", help="Framebuffer device path")
    write_parser.add_argument("--format", type=str, default="ARGB8888", choices=["ARGB8888", "RGB24"])
    write_parser.add_argument("--seq", type=int, default=0, help="Frame sequence number")

    # read-fb command
    read_parser = subparsers.add_parser("read-fb")
    read_parser.add_argument("output", type=str, help="Output file to save extracted payload")
    read_parser.add_argument("--device", type=str, default="/dev/fb0", help="Framebuffer device path")
    read_parser.add_argument("--format", type=str, default="ARGB8888", choices=["ARGB8888", "RGB24"])

    # example / demo command
    subparsers.add_parser("example")

    args = parser.parse_args()

    if args.command == "example":
        print("=== QEMU Framebuffer Packing Demo ===")
        # Generate 16 sample Q16_16 values (1.0, 2.0, 3.5, etc.)
        sample_values = [0x00010000 * i for i in range(1, 17)]
        print(f"Sample Q16_16 values (len={len(sample_values)}): {[v / 65536.0 for v in sample_values]}")

        # Pack to ARGB
        packed_bytes = pack_q16_to_argb32(sample_values)
        print(f"Packed ARGB32 bytes (len={len(packed_bytes)}): {packed_bytes.hex()}")

        # Unpack back
        unpacked_values = unpack_argb32_to_q16(packed_bytes)
        print(f"Unpacked Q16_16 values: {[v / 65536.0 for v in unpacked_values]}")
        assert sample_values == unpacked_values, "Error: roundtrip packing verification failed!"
        print("Roundtrip validation: SUCCESS")
        return

    if args.command == "pack":
        data = Path(args.input).read_bytes()
        if args.format == "ARGB8888":
            # Convert raw bytes to uint32 values (little-endian)
            count = len(data) // 4
            values = list(struct.unpack(f"<{count}I", data[:count * 4]))
            packed = pack_q16_to_argb32(values)
        else:
            packed = pack_bytes_to_rgb24(data)
        Path(args.output).write_bytes(packed)
        print(f"Packed {len(data)} bytes to {args.output} using format {args.format}")
        return

    if args.command == "unpack":
        data = Path(args.input).read_bytes()
        if args.format == "ARGB8888":
            values = unpack_argb32_to_q16(data)
            unpacked = struct.pack(f"<{len(values)}I", *values)
        else:
            unpacked = unpack_rgb24_to_bytes(data)
        Path(args.output).write_bytes(unpacked)
        print(f"Unpacked {len(data)} bytes to {args.output} using format {args.format}")
        return

    if args.command == "write-fb":
        data = Path(args.input).read_bytes()
        try:
            receipt = write_to_framebuffer(
                device_path=args.device,
                data=data,
                seq=args.seq,
                pix_format=args.format
            )
            print(json.dumps(asdict(receipt), indent=2))
        except (PermissionError, FileNotFoundError) as e:
            print(f"Error accessing framebuffer device {args.device}: {e}", file=sys.stderr)
            print("To run on local framebuffer, verify device permissions or run as root.", file=sys.stderr)
            sys.exit(1)
        return

    if args.command == "read-fb":
        try:
            payload, receipt = read_from_framebuffer(
                device_path=args.device,
                pix_format=args.format
            )
            Path(args.output).write_bytes(payload)
            print(json.dumps(asdict(receipt), indent=2))
        except (PermissionError, FileNotFoundError) as e:
            print(f"Error accessing framebuffer device {args.device}: {e}", file=sys.stderr)
            sys.exit(1)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
