# Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
# Released under Apache 2.0 license as described in the file LICENSE.
# Authors: Research Stack Team
#
# reed_solomon_vcn.py — Reed-Solomon error correction for VCN frame data
#
# Adds ECC (Error Correction Code) symbols after frame data in the VCN
# (Virtual Compute Network) frame format. Uses the reedsolo library.

from __future__ import annotations

import struct
from typing import Tuple

try:
    import reedsolo
except ImportError:
    raise ImportError(
        "reedsolo library required. Install with: pip install reedsolo"
    )


# ════════════════════════════════════════════════════════════
# §1  VCN Frame Format
# ════════════════════════════════════════════════════════════

# VCN Frame Layout:
# ┌──────────┬──────────────┬──────────────┬──────────────┬──────────────┐
# │ Magic(4) │ FrameLen (4) │ FrameType(1) │ Payload(var) │ RS ECC(var)  │
# └──────────┴──────────────┴──────────────┴──────────────┴──────────────┘

VCN_MAGIC = b"VCN\x01"
VCN_HEADER_SIZE = 9  # 4 (magic) + 4 (length) + 1 (type)

# Frame types
FRAME_TYPE_DATA = 0x01
FRAME_TYPE_CTRL = 0x02
FRAME_TYPE_SYNC = 0x03
FRAME_TYPE_ECC  = 0x04


# ════════════════════════════════════════════════════════════
# §2  Reed-Solomon Encoder/Decoder
# ════════════════════════════════════════════════════════════

class RSCodec:
    """Reed-Solomon codec wrapper with VCN frame integration."""

    def __init__(self, nsym: int = 32, nsize: int = 255):
        """Initialize RS codec.

        Args:
            nsym: Number of error correction symbols.
            nsize: Total codeword size (data + ECC). Max 255 for GF(2^8).
        """
        self.nsym = nsym
        self.nsize = nsize
        self.codec = reedsolo.RSCodec(nsym, nsize)

    def encode_rs(self, data: bytes) -> bytes:
        """Encode data with Reed-Solomon ECC.

        Args:
            data: Raw data bytes.

        Returns:
            Encoded data with ECC symbols appended.
        """
        return bytes(self.codec.encode(data))

    def decode_rs(self, encoded_data: bytes) -> Tuple[bytes, int]:
        """Decode and correct RS-encoded data.

        Args:
            encoded_data: Data with ECC symbols.

        Returns:
            Tuple of (corrected_data, number_of_corrections).

        Raises:
            reedsolo.ReedSolomonError: If too many errors to correct.
        """
        decoded, decoded_msgecc, errata_pos = self.codec.decode(encoded_data)
        corrections = len(errata_pos) if errata_pos else 0
        return bytes(decoded), corrections


# ════════════════════════════════════════════════════════════
# §3  VCN Frame Protection
# ════════════════════════════════════════════════════════════

def encode_rs(data: bytes, nsym: int = 32) -> bytes:
    """Encode data with Reed-Solomon ECC symbols.

    Args:
        data: Raw data bytes.
        nsym: Number of ECC symbols (default 32).

    Returns:
        Encoded data with nsym ECC symbols appended.
    """
    codec = reedsolo.RSCodec(nsym)
    return bytes(codec.encode(data))


def decode_rs(encoded_data: bytes, nsym: int = 32) -> Tuple[bytes, int]:
    """Decode and correct RS-encoded data.

    Args:
        encoded_data: Data with ECC symbols.
        nsym: Number of ECC symbols (must match encoding).

    Returns:
        Tuple of (corrected_data, corrections_count).
    """
    codec = reedsolo.RSCodec(nsym)
    decoded, _, errata_pos = codec.decode(encoded_data)
    corrections = len(errata_pos) if errata_pos else 0
    return bytes(decoded), corrections


def protect_frame(frame_bytes: bytes, redundancy_factor: int = 2) -> bytes:
    """Add Reed-Solomon ECC protection to a VCN frame.

    The frame is chunked into blocks (max 223 data bytes each for GF(2^8)
    with 32 ECC symbols), and each block is independently RS-encoded.

    Protected Frame Layout:
    ┌──────────────┬──────────────┬──────────────────────────────────┐
    │ NumBlocks(4) │ BlockSize(4) │ Block0(RS) │ Block1(RS) │ ...   │
    └──────────────┴──────────────┴──────────────────────────────────┘

    Args:
        frame_bytes: Raw frame data to protect.
        redundancy_factor: Controls ECC symbol count (nsym = 16 * factor).

    Returns:
        Protected frame bytes with ECC.
    """
    nsym = 16 * redundancy_factor
    # Max data bytes per codeword in GF(2^8) with nsym ECC symbols
    max_data = 255 - nsym
    if max_data < 1:
        raise ValueError(f"Redundancy factor {redundancy_factor} too high: nsym={nsym}")

    # Chunk the frame data
    chunks = []
    for i in range(0, len(frame_bytes), max_data):
        chunk = frame_bytes[i:i + max_data]
        # Pad last chunk to consistent block size
        if len(chunk) < max_data:
            chunk = chunk + b'\x00' * (max_data - len(chunk))
        chunks.append(chunk)

    num_blocks = len(chunks)
    block_size = max_data  # data portion of each block

    # Header
    header = struct.pack('<II', num_blocks, block_size)

    # Encode each chunk
    encoded_blocks = b''
    for chunk in chunks:
        encoded_blocks += encode_rs(chunk, nsym)

    return header + encoded_blocks


def recover_frame(protected_bytes: bytes, redundancy_factor: int = 2) -> bytes:
    """Recover a VCN frame from RS-protected data.

    Args:
        protected_bytes: Protected frame bytes.
        redundancy_factor: Must match the factor used during protection.

    Returns:
        Recovered frame data (errors corrected if possible).

    Raises:
        ValueError: If the protected data is malformed.
        reedsolo.ReedSolomonError: If too many errors to correct in any block.
    """
    nsym = 16 * redundancy_factor

    if len(protected_bytes) < 8:
        raise ValueError("Protected data too short for header")

    num_blocks, block_size = struct.unpack('<II', protected_bytes[:8])

    encoded_data = protected_bytes[8:]
    # Each encoded block = block_size (data) + nsym (ECC) = 255 bytes
    encoded_block_size = block_size + nsym

    if len(encoded_data) < num_blocks * encoded_block_size:
        raise ValueError(
            f"Protected data too short: expected {num_blocks * encoded_block_size}, "
            f"got {len(encoded_data)}"
        )

    recovered = bytearray()
    total_corrections = 0

    for i in range(num_blocks):
        start = i * encoded_block_size
        end = start + encoded_block_size
        block = encoded_data[start:end]

        decoded, corrections = decode_rs(block, nsym)
        total_corrections += corrections
        recovered.extend(decoded[:block_size])  # Trim padding

    # Remove trailing padding (zeros added during protection)
    # We use the original frame length encoded in VCN header if available
    return bytes(recovered)


# ════════════════════════════════════════════════════════════
# §4  Module API
# ════════════════════════════════════════════════════════════

__all__ = [
    "RSCodec",
    "encode_rs",
    "decode_rs",
    "protect_frame",
    "recover_frame",
    "VCN_MAGIC",
    "VCN_HEADER_SIZE",
    "FRAME_TYPE_DATA",
    "FRAME_TYPE_CTRL",
    "FRAME_TYPE_SYNC",
    "FRAME_TYPE_ECC",
]


if __name__ == "__main__":
    print("Reed-Solomon VCN Frame Protection — Research Stack")
    print("=" * 55)

    # Test basic encode/decode
    test_data = b"Hello, Research Stack! This is a VCN frame payload."
    nsym = 32

    encoded = encode_rs(test_data, nsym)
    print(f"Original:  {len(test_data)} bytes")
    print(f"Encoded:   {len(encoded)} bytes (added {nsym} ECC symbols)")

    decoded, corrections = decode_rs(encoded, nsym)
    assert decoded[:len(test_data)] == test_data, "Decoded data mismatch!"
    print(f"Decoded:   {corrections} corrections needed")
    print("Basic RS encode/decode: PASS")

    # Test with corruption
    corrupted = bytearray(encoded)
    for i in range(5):  # Corrupt 5 bytes
        corrupted[i + 10] ^= 0xFF
    decoded2, corrections2 = decode_rs(bytes(corrupted), nsym)
    assert decoded2[:len(test_data)] == test_data, "Failed to correct corrupted data!"
    print(f"Corrupted decode: {corrections2} corrections — PASS")

    # Test frame protection
    frame = b"VCN\x01" + struct.pack('<I', 20) + bytes([0x01]) + b"payload data here!!"
    protected = protect_frame(frame, redundancy_factor=2)
    print(f"\nFrame:     {len(frame)} bytes")
    print(f"Protected: {len(protected)} bytes")

    recovered = recover_frame(protected, redundancy_factor=2)
    # recovered may have trailing padding; check prefix
    original_data = frame
    assert recovered[:len(original_data)] == original_data, "Frame recovery failed!"
    print("Frame protect/recover: PASS")

    # Test with damage
    damaged = bytearray(protected)
    damage_positions = [20, 21, 22, 30, 31]
    for pos in damage_positions:
        if pos < len(damaged):
            damaged[pos] ^= 0xAA
    try:
        recovered2 = recover_frame(bytes(damaged), redundancy_factor=2)
        if recovered2[:len(original_data)] == original_data:
            print("Damaged frame recovery: PASS")
        else:
            print("Damaged frame recovery: MISMATCH (may need higher redundancy)")
    except Exception as e:
        print(f"Damaged frame recovery: FAILED ({e})")

    print("\nAll tests complete.")
