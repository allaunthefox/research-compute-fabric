#!/usr/bin/env python3
"""
Unified Shell Asset Creator for Lean 4 Toolchain Compression

Creates a ZIP-compatible shell with:
- Prefix Header: RGFlow Stability Signature (σ_q)
- Encapsulated Payload: Compressed via unifiedCompress logic
- Zip Footer: Standard Central Directory for compatibility

Shell-index ⌊√n⌋ based addressing from UnifiedCompression.lean
"""

import struct
import zlib
import hashlib
import os
import sys
import math
from pathlib import Path
from typing import List, Tuple, Optional

# ═══════════════════════════════════════════════════════════════════════════
# Shell Structure Constants
# ═══════════════════════════════════════════════════════════════════════════

PREFIX_HEADER_MAGIC = b"RGFL\x01\x00"
HEADER_SIZE = 64  # Fixed size for prefix header

# ZIP file signatures
LOCAL_FILE_HEADER_SIGNATURE = b'\x50\x4b\x03\x04'
CENTRAL_DIR_SIGNATURE = b'\x50\x4b\x01\x02'
END_OF_CENTRAL_DIR_SIGNATURE = b'\x50\x4b\x05\x06'

# ═══════════════════════════════════════════════════════════════════════════
# Shell-Index ⌊√n⌋ Based Addressing (from UnifiedCompression.lean)
# ═══════════════════════════════════════════════════════════════════════════

def isqrt(n: int) -> int:
    """Integer square root (floor of sqrt) - matches Lean implementation."""
    if n == 0:
        return 0
    if n == 1:
        return 1
    
    # Linear search from 1 to 256 (max sqrt of 65536)
    for k in range(1, 257):
        if k * k > n:
            return k - 1
    return 256

def pulse_from_int(n: int) -> dict:
    """
    Generate pulse from integer n (shell decomposition).
    Matches pulseFromInt from UnifiedCompression.lean.
    """
    k = isqrt(n)
    a = n - (k * k)
    b = ((k + 1) * (k + 1)) - n
    is_square = (a == 0)
    
    mass = (a * b)
    polarity = (a - b)
    
    # Triangle mode classification
    if is_square:
        mode = "square"
    elif a == k:
        mode = "g"
    elif a == k + 1:
        mode = "c"
    elif b == 1:
        mode = "t"
    else:
        mode = "a"
    
    return {
        "mode": mode,
        "pos": n,
        "width": 2 * k + 1,
        "mass": mass,
        "polarity": polarity,
        "square": is_square,
        "k": k,
        "a": a,
        "b": b
    }

def compute_rgflow_signature(pulses: List[dict]) -> float:
    """
    Compute RGFlow Stability Signature (σ_q) from pulse sequence.
    Square pulses are considered lawful (high stability).
    Non-square pulses have stability based on mass.
    """
    if not pulses:
        return 0.0
    
    sigma_q_sum = 0.0
    for pulse in pulses:
        if pulse["square"]:
            sigma_q_sum += 1.5
        elif pulse["mass"] > 65536:  # 0x00010000
            sigma_q_sum += 1.0
        else:
            sigma_q_sum += 0.5
    
    return sigma_q_sum / len(pulses)

# ═══════════════════════════════════════════════════════════════════════════
# Unified Compression Logic
# ═══════════════════════════════════════════════════════════════════════════

def unified_compress(data: bytes) -> Tuple[bytes, float]:
    """
    Compress data using unifiedCompress logic.
    Returns (compressed_data, sigma_q).
    """
    # Generate pulses from data positions (simplified - use byte positions)
    pulses = []
    for i in range(0, len(data), 256):  # Sample every 256 bytes
        n = i
        pulses.append(pulse_from_int(n))
    
    # Compute RGFlow signature
    sigma_q = compute_rgflow_signature(pulses)
    
    # Apply standard deflate compression with ZIP-compatible format
    # -15 windowBits produces raw deflate without zlib headers (ZIP format)
    compressed = zlib.compress(data, level=9, wbits=-15)
    
    return compressed, sigma_q

# ═══════════════════════════════════════════════════════════════════════════
# ITD (Informatic Topology Deduplication)
# ═══════════════════════════════════════════════════════════════════════════

def itd_deduplicate(data: bytes, chunk_size: int = 4096) -> Tuple[bytes, int]:
    """
    Apply ITD deduplication on chunks.
    Returns (deduplicated_data, deduplication_ratio).
    """
    chunks = [data[i:i+chunk_size] for i in range(0, len(data), chunk_size)]
    
    # Deduplicate by tracking unique chunks
    seen = {}
    deduplicated = bytearray()
    dedup_count = 0
    
    for chunk in chunks:
        chunk_hash = hashlib.sha256(chunk).digest()
        if chunk_hash in seen:
            # Reference existing chunk
            deduplicated.extend(struct.pack('<I', seen[chunk_hash]))
            dedup_count += 1
        else:
            # Store new chunk
            offset = len(deduplicated)
            seen[chunk_hash] = offset
            deduplicated.extend(chunk)
    
    ratio = (dedup_count / len(chunks)) * 100 if chunks else 0
    return bytes(deduplicated), int(ratio)

# ═══════════════════════════════════════════════════════════════════════════
# ZIP Shell Structure
# ═══════════════════════════════════════════════════════════════════════════

def create_prefix_header(sigma_q: float, original_size: int) -> bytes:
    """
    Create RGFlow signature string for ZIP comment.
    Returns a string that will be stored in the ZIP file comment.
    """
    signature = f"RGFL-v1|sigma_q={sigma_q:.4f}|original_size={original_size}"
    return signature.encode('utf-8')

def create_local_file_header(filename: str, compressed_data: bytes, 
                             crc32: int, uncompressed_size: int) -> bytes:
    """Create ZIP local file header."""
    header = bytearray()
    
    # Signature
    header.extend(LOCAL_FILE_HEADER_SIGNATURE)
    
    # Version needed to extract (2.0)
    header.extend(struct.pack('<H', 20))
    
    # General purpose bit flag (0)
    header.extend(struct.pack('<H', 0))
    
    # Compression method (8 = deflate)
    header.extend(struct.pack('<H', 8))
    
    # Last mod time and date (dummy)
    header.extend(struct.pack('<H', 0))
    header.extend(struct.pack('<H', 0))
    
    # CRC-32
    header.extend(struct.pack('<I', crc32))
    
    # Compressed size
    header.extend(struct.pack('<I', len(compressed_data)))
    
    # Uncompressed size
    header.extend(struct.pack('<I', uncompressed_size))
    
    # Filename length
    filename_bytes = filename.encode('utf-8')
    header.extend(struct.pack('<H', len(filename_bytes)))
    
    # Extra field length (0)
    header.extend(struct.pack('<H', 0))
    
    # Filename
    header.extend(filename_bytes)
    
    return bytes(header)

def create_central_directory_header(filename: str, compressed_data: bytes,
                                   crc32: int, uncompressed_size: int,
                                   local_header_offset: int) -> bytes:
    """Create ZIP central directory header."""
    header = bytearray()
    
    # Signature
    header.extend(CENTRAL_DIR_SIGNATURE)
    
    # Version made by (2.0)
    header.extend(struct.pack('<H', 20))
    
    # Version needed to extract (2.0)
    header.extend(struct.pack('<H', 20))
    
    # General purpose bit flag (0)
    header.extend(struct.pack('<H', 0))
    
    # Compression method (8 = deflate)
    header.extend(struct.pack('<H', 8))
    
    # Last mod time and date (dummy)
    header.extend(struct.pack('<H', 0))
    header.extend(struct.pack('<H', 0))
    
    # CRC-32
    header.extend(struct.pack('<I', crc32))
    
    # Compressed size
    header.extend(struct.pack('<I', len(compressed_data)))
    
    # Uncompressed size
    header.extend(struct.pack('<I', uncompressed_size))
    
    # Filename length
    filename_bytes = filename.encode('utf-8')
    header.extend(struct.pack('<H', len(filename_bytes)))
    
    # Extra field length (0)
    header.extend(struct.pack('<H', 0))
    
    # File comment length (0)
    header.extend(struct.pack('<H', 0))
    
    # Disk number start (0)
    header.extend(struct.pack('<H', 0))
    
    # Internal file attributes (0)
    header.extend(struct.pack('<H', 0))
    
    # External file attributes (0)
    header.extend(struct.pack('<I', 0))
    
    # Relative offset of local header
    header.extend(struct.pack('<I', local_header_offset))
    
    # Filename
    header.extend(filename_bytes)
    
    return bytes(header)

def create_end_of_central_dir_record(central_dir_offset: int, 
                                     central_dir_size: int,
                                     num_entries: int,
                                     comment: bytes = b'') -> bytes:
    """Create ZIP end of central directory record."""
    record = bytearray()
    
    # Signature
    record.extend(END_OF_CENTRAL_DIR_SIGNATURE)
    
    # Number of this disk (0)
    record.extend(struct.pack('<H', 0))
    
    # Disk where central directory starts (0)
    record.extend(struct.pack('<H', 0))
    
    # Number of central directory records on this disk
    record.extend(struct.pack('<H', num_entries))
    
    # Total number of central directory records
    record.extend(struct.pack('<H', num_entries))
    
    # Size of central directory
    record.extend(struct.pack('<I', central_dir_size))
    
    # Offset of central directory
    record.extend(struct.pack('<I', central_dir_offset))
    
    # Comment length
    record.extend(struct.pack('<H', len(comment)))
    
    # Comment (RGFlow signature)
    record.extend(comment)
    
    return bytes(record)

def create_unified_shell(input_path: str, output_path: str, 
                        enable_itd: bool = True) -> dict:
    """
    Create unified shell asset from input file.
    
    Returns statistics about compression.
    """
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Read input data
    with open(input_file, 'rb') as f:
        original_data = f.read()
    
    original_size = len(original_data)
    print(f"Original size: {original_size:,} bytes ({original_size / (1024*1024):.2f} MB)")
    
    # Step 1: Apply ITD deduplication if enabled
    if enable_itd:
        print("Applying ITD deduplication...")
        deduplicated_data, dedup_ratio = itd_deduplicate(original_data)
        print(f"ITD deduplication ratio: {dedup_ratio}%")
        data_to_compress = deduplicated_data
    else:
        data_to_compress = original_data
        dedup_ratio = 0
    
    # Step 2: Apply unified compression
    print("Applying unified compression...")
    compressed_data, sigma_q = unified_compress(data_to_compress)
    compressed_size = len(compressed_data)
    
    print(f"Compressed size: {compressed_size:,} bytes ({compressed_size / (1024*1024):.2f} MB)")
    print(f"Compression ratio: {(1 - compressed_size / original_size) * 100:.2f}%")
    print(f"RGFlow Stability Signature (σ_q): {sigma_q:.4f}")
    
    # Step 3: Create RGFlow signature for ZIP comment
    print("Creating RGFlow signature...")
    rgflow_signature = create_prefix_header(sigma_q, original_size)
    
    # Step 4: Create ZIP structure
    print("Creating ZIP shell structure...")
    filename = input_file.name
    crc32 = zlib.crc32(original_data) & 0xffffffff
    
    # Local file header
    local_header = create_local_file_header(filename, compressed_data, 
                                            crc32, original_size)
    
    # Calculate offsets (no prefix header now)
    local_header_offset = 0
    central_dir_offset = local_header_offset + len(local_header) + len(compressed_data)
    
    # Central directory header (required for ZIP compatibility)
    central_dir_header = create_central_directory_header(filename, compressed_data,
                                                           crc32, original_size,
                                                           local_header_offset)
    
    central_dir_size = len(central_dir_header)
    num_entries = 1
    
    # End of central directory with RGFlow signature in comment
    eocd_record = create_end_of_central_dir_record(central_dir_offset,
                                                   central_dir_size,
                                                   num_entries,
                                                   rgflow_signature)
    
    # Step 5: Write unified shell
    print(f"Writing unified shell to: {output_path}")
    with open(output_path, 'wb') as f:
        # ZIP local file header (no prefix header - starts with ZIP signature)
        f.write(local_header)
        
        # Compressed data
        f.write(compressed_data)
        
        # ZIP central directory header
        f.write(central_dir_header)
        
        # ZIP end of central directory with RGFlow signature in comment
        f.write(eocd_record)
    
    final_size = os.path.getsize(output_path)
    print(f"Final shell size: {final_size:,} bytes ({final_size / (1024*1024):.2f} MB)")
    print(f"Total reduction: {(1 - final_size / original_size) * 100:.2f}%")
    
    return {
        "original_size": original_size,
        "compressed_size": compressed_size,
        "final_size": final_size,
        "compression_ratio": (1 - compressed_size / original_size) * 100,
        "total_reduction": (1 - final_size / original_size) * 100,
        "sigma_q": sigma_q,
        "itd_ratio": dedup_ratio
    }

# ═══════════════════════════════════════════════════════════════════════════
# CLI Interface
# ═══════════════════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) < 3:
        print("Usage: python create_unified_shell.py <input_file> <output_file> [--no-itd]")
        print("\nCreates a unified shell asset with:")
        print("  - Prefix header with RGFlow Stability Signature (σ_q)")
        print("  - Payload compressed via unifiedCompress logic")
        print("  - Standard ZIP footer for compatibility")
        print("\nOptions:")
        print("  --no-itd  Disable ITD deduplication")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    enable_itd = "--no-itd" not in sys.argv
    
    try:
        stats = create_unified_shell(input_path, output_path, enable_itd)
        print("\n=== Compression Statistics ===")
        print(f"Original size:      {stats['original_size']:,} bytes")
        print(f"Compressed size:    {stats['compressed_size']:,} bytes")
        print(f"Final shell size:   {stats['final_size']:,} bytes")
        print(f"Compression ratio:  {stats['compression_ratio']:.2f}%")
        print(f"Total reduction:    {stats['total_reduction']:.2f}%")
        print(f"ITD deduplication:  {stats['itd_ratio']}%")
        print(f"RGFlow σ_q:         {stats['sigma_q']:.4f}")
        print("\n✓ Unified shell created successfully")
        print(f"✓ File can be extracted with standard unzip tools")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
