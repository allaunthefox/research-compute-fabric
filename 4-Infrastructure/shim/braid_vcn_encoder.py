#!/usr/bin/env python3
"""
Braid VCN Encoder Pipeline

End-to-end pipeline:
  braid data → Delta+RLE compression → Q16_16 encoding → Reed-Solomon ECC →
  ChaCha20 encryption → VCN YUV420 frame → hardware encode (MKV)

Functions:
  encode_braid_strand(strand_dict, resolution) -> bytes (MKV)
  encode_braid_crossing(bracket_a, bracket_b) -> bytes (MKV)
  encode_pist_field(pist_dict, resolution) -> bytes (MKV)
  decode_braid_frame(mkv_bytes) -> dict
"""

from __future__ import annotations

import struct
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
from vcn_compute_substrate import (
    VCNComputeFrameSpec, VCN_RESOLUTIONS, SIGNATURE_HEADER, SIGNATURE_SIZE,
    compute_frame_size, create_frame_dynamic, encode_frames_hardware,
    BRAID_STRAND_BYTES, BRAID_BRACKET_BYTES,
    _q16_to_bytes, _u32_to_bytes, _bool_to_byte,
)

# Third-party (lazy imports so py_compile works without them installed)
try:
    import reedsolo
except ImportError:
    reedsolo = None  # type: ignore

try:
    from cryptography.hazmat.primitives.ciphers import Cipher as _Cipher
    from cryptography.hazmat.primitives.ciphers import algorithms as _alg
    _CHA20_AVAILABLE = True
except ImportError:
    _CHA20_AVAILABLE = False


# ── Configuration ────────────────────────────────────────────────────────────

RS_NSYM = 32                # Reed-Solomon parity symbols (corrects 16 symbol errors)
CHACHA_KEY_SIZE = 32        # 256-bit key
CHACHA_NONCE_SIZE = 16      # 128-bit nonce (cryptography ChaCha20 requires 16)

# Pipeline stage tags (1 byte each, used to identify frame contents)
TAG_STRAND   = 0x01
TAG_CROSSING = 0x02
TAG_PIST     = 0x03


# ── Delta + RLE compression ─────────────────────────────────────────────────

def delta_rle_encode(data: bytes) -> bytes:
    """Compress *data* using delta encoding followed by run-length encoding.

    Layout:
        [4 bytes: original length][1 byte: delta flag (0x01)]
        [delta-encoded + RLE stream]

    RLE scheme: if a byte repeats ≥3 times, emit [0xFE, byte, count].
    0xFE in the literal stream is escaped as [0xFE, 0xFE].
    """
    if not data:
        return struct.pack("<I", 0) + b"\x01"

    # Delta encoding (byte-level deltas)
    deltas = bytearray(len(data))
    deltas[0] = data[0]
    for i in range(1, len(data)):
        deltas[i] = (data[i] - data[i - 1]) & 0xFF

    # RLE pass
    out = bytearray()
    i = 0
    while i < len(deltas):
        if i + 2 < len(deltas) and deltas[i] == deltas[i + 1] == deltas[i + 2]:
            # Run of identical bytes
            run_byte = deltas[i]
            run_len = 0
            while i + run_len < len(deltas) and deltas[i + run_len] == run_byte and run_len < 255:
                run_len += 1
            out.append(0xFE)
            out.append(run_byte)
            out.append(run_len)
            i += run_len
        else:
            b = deltas[i]
            if b == 0xFE:
                out.append(0xFE)
                out.append(0xFE)
            else:
                out.append(b)
            i += 1

    header = struct.pack("<I", len(data)) + b"\x01"
    return header + bytes(out)


def delta_rle_decode(stream: bytes) -> bytes:
    """Decompress a delta-RLE stream back to original bytes."""
    orig_len = struct.unpack("<I", stream[:4])[0]
    if orig_len == 0:
        return b""
    _flag = stream[4]
    payload = stream[5:]

    # Undo RLE
    expanded = bytearray()
    i = 0
    while i < len(payload):
        if payload[i] == 0xFE:
            if i + 1 < len(payload) and payload[i + 1] == 0xFE:
                expanded.append(0xFE)
                i += 2
            elif i + 2 < len(payload):
                run_byte = payload[i + 1]
                run_len = payload[i + 2]
                expanded.extend([run_byte] * run_len)
                i += 3
            else:
                expanded.append(payload[i])
                i += 1
        else:
            expanded.append(payload[i])
            i += 1

    # Undo delta encoding
    out = bytearray(orig_len)
    if orig_len > 0:
        out[0] = expanded[0]
        for j in range(1, orig_len):
            out[j] = (expanded[j] + out[j - 1]) & 0xFF

    return bytes(out)


# ── Reed-Solomon error correction ───────────────────────────────────────────

def rs_encode(data: bytes, nsym: int = RS_NSYM) -> bytes:
    """Append Reed-Solomon parity symbols to *data*."""
    if reedsolo is None:
        raise ImportError("reedsolo is required for Reed-Solomon ECC. pip install reedsolo")
    rs = reedsolo.RSCodec(nsym)
    return rs.encode(data)


def rs_decode(data: bytes, nsym: int = RS_NSYM) -> bytes:
    """Decode (and correct errors in) a Reed-Solomon encoded message."""
    if reedsolo is None:
        raise ImportError("reedsolo is required for Reed-Solomon ECC. pip install reedsolo")
    rs = reedsolo.RSCodec(nsym)
    decoded = rs.decode(data)
    # reedsolo returns (decoded_msg, decoded_msg_with_ecc, ...) — take first element
    if isinstance(decoded, tuple):
        return bytes(decoded[0])
    return bytes(decoded)


# ── ChaCha20 encryption ─────────────────────────────────────────────────────

def _get_chacha_key(key: Optional[bytes] = None) -> bytes:
    """Return a 32-byte ChaCha20 key, generating one if not supplied."""
    if key is not None:
        if len(key) != CHACHA_KEY_SIZE:
            raise ValueError(f"Key must be {CHACHA_KEY_SIZE} bytes")
        return key
    return os.urandom(CHACHA_KEY_SIZE)


def chacha_encrypt(plaintext: bytes, key: bytes, nonce: Optional[bytes] = None) -> Tuple[bytes, bytes]:
    """Encrypt *plaintext* with ChaCha20. Returns (ciphertext, nonce)."""
    if not _CHA20_AVAILABLE:
        raise ImportError("cryptography is required for ChaCha20. pip install cryptography")
    if nonce is None:
        nonce = os.urandom(CHACHA_NONCE_SIZE)
    encryptor = _Cipher(_alg.ChaCha20(key, nonce), mode=None).encryptor()
    ct = encryptor.update(plaintext) + encryptor.finalize()
    return ct, nonce


def chacha_decrypt(ciphertext: bytes, key: bytes, nonce: bytes) -> bytes:
    """Decrypt *ciphertext* with ChaCha20."""
    if not _CHA20_AVAILABLE:
        raise ImportError("cryptography is required for ChaCha20. pip install cryptography")
    decryptor = _Cipher(_alg.ChaCha20(key, nonce), mode=None).decryptor()
    return decryptor.update(ciphertext) + decryptor.finalize()


# ── Braid serialization (matches vcn_compute_substrate layouts) ─────────────

def _serialize_bracket(bracket: dict) -> bytes:
    """Encode a BraidBracket dict to 21 bytes."""
    data = b""
    for key in ("lower", "upper", "gap", "kappa", "phi"):
        data += _q16_to_bytes(bracket[key])
    data += _bool_to_byte(bracket["admissible"])
    return data


def _deserialize_bracket(raw: bytes) -> dict:
    """Decode 21 bytes into a BraidBracket dict."""
    keys = ("lower", "upper", "gap", "kappa", "phi")
    bracket = {}
    for i, key in enumerate(keys):
        bracket[key] = struct.unpack("<I", raw[i * 4:(i + 1) * 4])[0]
    bracket["admissible"] = raw[20] != 0
    return bracket


def _serialize_strand(strand: dict) -> bytes:
    """Encode a BraidStrand dict to 42 bytes."""
    data = b""
    data += _q16_to_bytes(strand["phaseAcc"]["x"])
    data += _q16_to_bytes(strand["phaseAcc"]["y"])
    data += _bool_to_byte(strand["parity"])
    data += _u32_to_bytes(strand["slot"])
    data += _q16_to_bytes(strand["residue"])
    data += _q16_to_bytes(strand["jitter"])
    data += _serialize_bracket(strand["bracket"])
    assert len(data) == BRAID_STRAND_BYTES
    return data


def _deserialize_strand(raw: bytes) -> dict:
    """Decode 42 bytes into a BraidStrand dict."""
    return {
        "phaseAcc": {
            "x": struct.unpack("<I", raw[0:4])[0],
            "y": struct.unpack("<I", raw[4:8])[0],
        },
        "parity": raw[8] != 0,
        "slot": struct.unpack("<I", raw[9:13])[0],
        "residue": struct.unpack("<I", raw[13:17])[0],
        "jitter": struct.unpack("<I", raw[17:21])[0],
        "bracket": _deserialize_bracket(raw[21:42]),
    }


# ── Full pipeline: encode ───────────────────────────────────────────────────

def _build_frame_payload(tag: int, serialized: bytes,
                         key: Optional[bytes],
                         compress: bool = True) -> bytes:
    """Apply Delta+RLE → RS → ChaCha20 → return frame-ready payload.

    Layout: [1B tag][1B flags][nonce?][RS-encoded, encrypted blob]
    """
    flags = 0x00
    if compress:
        flags |= 0x01

    blob = serialized
    if compress:
        blob = delta_rle_encode(blob)

    blob = rs_encode(blob)

    nonce = b""
    if key is not None:
        blob, nonce = chacha_encrypt(blob, key)
        flags |= 0x02  # encrypted flag

    return struct.pack("<BB", tag, flags) + nonce + blob


def encode_braid_strand(strand_dict: dict, resolution: str = "1080p",
                        key: Optional[bytes] = None,
                        compress: bool = True) -> bytes:
    """Encode a BraidStrand → Delta+RLE → RS → ChaCha20 → VCN frame → MKV bytes.

    Returns the raw MKV file bytes.
    """
    serialized = _serialize_strand(strand_dict)
    payload = _build_frame_payload(TAG_STRAND, serialized, key, compress)

    w, h = VCN_RESOLUTIONS.get(resolution, VCN_RESOLUTIONS["1080p"])
    spec = VCNComputeFrameSpec(
        width=w, height=h,
        bytes_per_frame=compute_frame_size(w, h, "yuv420p"),
        encoder="libx264",
    )
    frame = create_frame_dynamic(payload, seq=0, spec=spec)

    with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        result = encode_frames_hardware([frame], tmp_path, spec)
        if result.returncode != 0:
            raise RuntimeError(f"VCN encode failed: {result.stderr}")
        mkv_bytes = tmp_path.read_bytes()
    finally:
        tmp_path.unlink(missing_ok=True)

    return mkv_bytes


def encode_braid_crossing(bracket_a: dict, bracket_b: dict,
                          resolution: str = "1080p",
                          key: Optional[bytes] = None,
                          compress: bool = True) -> bytes:
    """Encode two BraidBrackets (crossing) → full pipeline → MKV bytes."""
    serialized = _serialize_bracket(bracket_a) + _serialize_bracket(bracket_b)
    payload = _build_frame_payload(TAG_CROSSING, serialized, key, compress)

    w, h = VCN_RESOLUTIONS.get(resolution, VCN_RESOLUTIONS["1080p"])
    spec = VCNComputeFrameSpec(
        width=w, height=h,
        bytes_per_frame=compute_frame_size(w, h, "yuv420p"),
        encoder="libx264",
    )
    frame = create_frame_dynamic(payload, seq=0, spec=spec)

    with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        result = encode_frames_hardware([frame], tmp_path, spec)
        if result.returncode != 0:
            raise RuntimeError(f"VCN encode failed: {result.stderr}")
        mkv_bytes = tmp_path.read_bytes()
    finally:
        tmp_path.unlink(missing_ok=True)

    return mkv_bytes


def encode_pist_field(pist_dict: dict, resolution: str = "1080p",
                      key: Optional[bytes] = None,
                      compress: bool = True) -> bytes:
    """Encode a PIST field dict → full pipeline → MKV bytes.

    pist_dict is serialized as JSON bytes (arbitrary key/value pairs).
    """
    serialized = json.dumps(pist_dict, separators=(",", ":")).encode("utf-8")
    payload = _build_frame_payload(TAG_PIST, serialized, key, compress)

    w, h = VCN_RESOLUTIONS.get(resolution, VCN_RESOLUTIONS["1080p"])
    spec = VCNComputeFrameSpec(
        width=w, height=h,
        bytes_per_frame=compute_frame_size(w, h, "yuv420p"),
        encoder="libx264",
    )
    frame = create_frame_dynamic(payload, seq=0, spec=spec)

    with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        result = encode_frames_hardware([frame], tmp_path, spec)
        if result.returncode != 0:
            raise RuntimeError(f"VCN encode failed: {result.stderr}")
        mkv_bytes = tmp_path.read_bytes()
    finally:
        tmp_path.unlink(missing_ok=True)

    return mkv_bytes


# ── Full pipeline: decode ────────────────────────────────────────────────────

def decode_braid_frame(frame_payload: bytes,
                       key: Optional[bytes] = None) -> dict:
    """Decode a frame payload (after extracting from MKV / YUV420 frame).

    Reverses: ChaCha20 decrypt → RS decode → Delta+RLE decompress → deserialize.

    Args:
        frame_payload: raw payload bytes (after stripping VCN signature header).
        key: ChaCha20 key (required if the frame was encrypted).

    Returns:
        {
            "tag": int,
            "tag_name": str,
            "flags": int,
            "decrypted": bool,
            "data": dict | bytes,  # deserialized braid structure
        }
    """
    tag, flags = struct.unpack("<BB", frame_payload[:2])
    encrypted = bool(flags & 0x02)
    compressed = bool(flags & 0x01)
    offset = 2

    nonce = b""
    if encrypted:
        nonce = frame_payload[offset:offset + CHACHA_NONCE_SIZE]
        offset += CHACHA_NONCE_SIZE

    blob = frame_payload[offset:]

    # Reverse pipeline
    if encrypted:
        if key is None:
            raise ValueError("Frame is encrypted but no key provided")
        blob = chacha_decrypt(blob, key, nonce)

    blob = rs_decode(blob)

    if compressed:
        blob = delta_rle_decode(blob)

    # Deserialize based on tag
    tag_names = {TAG_STRAND: "strand", TAG_CROSSING: "crossing", TAG_PIST: "pist"}
    result: dict = {
        "tag": tag,
        "tag_name": tag_names.get(tag, "unknown"),
        "flags": flags,
        "decrypted": encrypted,
    }

    if tag == TAG_STRAND:
        result["data"] = _deserialize_strand(blob)
    elif tag == TAG_CROSSING:
        result["data"] = {
            "bracket_a": _deserialize_bracket(blob[:BRAID_BRACKET_BYTES]),
            "bracket_b": _deserialize_bracket(blob[BRAID_BRACKET_BYTES:]),
        }
    elif tag == TAG_PIST:
        result["data"] = json.loads(blob.decode("utf-8"))
    else:
        result["data"] = blob

    return result


def decode_braid_mkv(mkv_bytes: bytes, key: Optional[bytes] = None) -> dict:
    """Decode an MKV file produced by the braid encoder pipeline.

    Writes the MKV to a temp file, extracts the raw YUV420 frame via ffmpeg,
    strips the VCN header, then runs decode_braid_frame.
    """
    with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as mkv_f:
        mkv_f.write(mkv_bytes)
        mkv_path = Path(mkv_f.name)

    yuv_path = mkv_path.with_suffix(".yuv")

    try:
        # Decode MKV → raw YUV420
        cmd = [
            "ffmpeg", "-y", "-i", str(mkv_path),
            "-c:v", "rawvideo", "-f", "rawvideo",
            "-pix_fmt", "yuv420p", str(yuv_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg decode failed: {result.stderr}")

        raw = yuv_path.read_bytes()

        # Find frame size by reading the signature header
        if raw[:8] != SIGNATURE_HEADER:
            raise ValueError("Invalid VCN frame: bad signature")

        _, _, _, payload_len, _ = struct.unpack("<8sIIII", raw[:SIGNATURE_SIZE])
        payload = raw[SIGNATURE_SIZE:SIGNATURE_SIZE + payload_len]

        return decode_braid_frame(payload, key)
    finally:
        mkv_path.unlink(missing_ok=True)
        yuv_path.unlink(missing_ok=True)


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    import sys
    print("braid_vcn_encoder.py — Braid VCN Encoder Pipeline")
    print("  encode_braid_strand(strand_dict, resolution) -> MKV bytes")
    print("  encode_braid_crossing(bracket_a, bracket_b)  -> MKV bytes")
    print("  encode_pist_field(pist_dict, resolution)     -> MKV bytes")
    print("  decode_braid_frame(frame_payload, key)       -> dict")
    print("  decode_braid_mkv(mkv_bytes, key)             -> dict")


if __name__ == "__main__":
    main()
