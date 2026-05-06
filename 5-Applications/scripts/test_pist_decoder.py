#!/usr/bin/env python3
"""
Test harness for PIST C decoder.
Creates a compressed stream, embeds it into the decoder binary, and verifies roundtrip.
"""

import os
import subprocess
import struct
import tempfile
import sys

# ─── PIST Primitives (must match C decoder exactly) ───
PHI = (1 + 5**0.5) / 2
TWO_PI = 2 * 3.141592653589793
BASIS_SIZE = 16
BOOTSTRAP_SIZE = 16

def isqrt(n):
    x = n
    y = (x + 1) >> 1
    while y < x:
        x = y
        y = (x + n // x) >> 1
    return x

def pist_encode(n):
    k = isqrt(n)
    t = n - k * k
    return k, t

def pist_mass(k, t):
    if k == 0:
        return 0
    m = 2 * k + 1 - t
    tf = t if t < m else m
    return tf * (2 * k + 1 - tf)

def pist_mirror(n):
    k = isqrt(n)
    t = n - k * k
    if k == 0:
        return 0
    return k * k + (2 * k + 1 - t)

def torus_angles(n):
    nd = float(n)
    theta = (nd * PHI) % TWO_PI
    phi = (nd * PHI * PHI) % TWO_PI
    psi = (nd * PHI * PHI * PHI) % TWO_PI
    return theta, phi, psi

def keystream_value(n):
    t, p, s = torus_angles(n)
    mod = (t % TWO_PI) + (p % TWO_PI) + (s % TWO_PI)
    # Map [0, 6π] to [0, 255] — simplified to match C:
    # C does: sin(t) + cos(p) + sin(s), maps [-3,3] to [0,255]
    import math
    mod = math.sin(t) + math.cos(p) + math.sin(s)
    return int((mod + 3.0) * 42.5) & 0xFF

def predict(n, basis):
    b = basis[n % BASIS_SIZE]
    b ^= keystream_value(n)
    b ^= (n & 0xFF)
    b ^= (pist_mirror(n) % 256)
    return b & 0xFF

# ─── Compressor ───

def compress(data: bytes) -> bytes:
    """Compress data using PIST prediction + residuals."""
    # Compute optimal bootstrap basis
    freq = [0] * 256
    for b in data:
        freq[b] += 1
    # Top-16 most frequent bytes
    top = sorted(range(256), key=lambda i: freq[i], reverse=True)[:BASIS_SIZE]
    basis = bytes(top)

    # Compute residuals
    residuals = bytearray()
    for n, byte in enumerate(data):
        p = predict(n, basis)
        residual = byte ^ p
        residuals.append(residual)

    return basis + bytes(residuals)

# ─── Test ───

def test_roundtrip(data: bytes, decoder_path: str):
    """Test roundtrip: data -> compress -> C decoder -> verify."""
    compressed = compress(data)

    # Write compressed data to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.bin') as f:
        f.write(compressed)
        compressed_path = f.name

    # Embed into decoder binary: cat decoder + marker + compressed data
    marker = b'\xDE\xAD\xBE\xEFPIST'

    with open(decoder_path, 'rb') as f:
        decoder_bin = f.read()

    archive_path = compressed_path + '_archive.exe'
    with open(archive_path, 'wb') as f:
        f.write(decoder_bin)
        f.write(marker)
        f.write(compressed)
    os.chmod(archive_path, 0o755)

    # Run decoder
    result = subprocess.run([archive_path], capture_output=True)
    if result.returncode != 0:
        print(f"Decoder failed: {result.stderr.decode()}")
        return False

    output = result.stdout

    # Verify
    if output == data:
        print(f"  PASS: {len(data)} bytes roundtrip OK")
        print(f"  Compressed size: {len(compressed)} bytes (ratio: {len(compressed)/len(data):.3f})")
        return True
    else:
        print(f"  FAIL: output mismatch")
        print(f"  Expected: {len(data)} bytes, got: {len(output)} bytes")
        if len(output) > 0 and len(data) > 0:
            for i in range(min(20, len(output), len(data))):
                if output[i] != data[i]:
                    print(f"  First mismatch at byte {i}: expected {data[i]}, got {output[i]}")
                    break
        return False

def main():
    decoder_path = os.path.join(os.path.dirname(__file__), 'hutter_pist_decoder')

    # Check if decoder binary exists
    if not os.path.exists(decoder_path):
        print(f"Decoder binary not found: {decoder_path}")
        print("Build it first: gcc -O3 -o hutter_pist_decoder hutter_pist_decoder.c -lm")
        return 1

    print("=== PIST C Decoder Roundtrip Tests ===\n")

    # Test 1: All zeros (best case — residuals all same)
    print("Test 1: 1KB all zeros")
    data1 = bytes(1024)
    test_roundtrip(data1, decoder_path)

    # Test 2: Sequential bytes
    print("\nTest 2: 1KB sequential (0..255 repeat)")
    data2 = bytes(i % 256 for i in range(1024))
    test_roundtrip(data2, decoder_path)

    # Test 3: Random data (worst case — residuals random)
    import random
    print("\nTest 3: 1KB random")
    random.seed(42)
    data3 = bytes(random.randint(0, 255) for _ in range(1024))
    test_roundtrip(data3, decoder_path)

    # Test 4: 1MB mixed
    print("\nTest 4: 1MB mixed (50% zeros, 50% sequential)")
    data4 = bytearray()
    for i in range(1024 * 1024):
        if i % 2 == 0:
            data4.append(0)
        else:
            data4.append(i % 256)
    test_roundtrip(bytes(data4), decoder_path)

    # Test 5: 10MB zeros (measure speed)
    print("\nTest 5: 10MB all zeros (speed test)")
    import time
    data5 = bytes(10 * 1024 * 1024)
    t0 = time.time()
    ok = test_roundtrip(data5, decoder_path)
    t1 = time.time()
    if ok:
        mbps = len(data5) / (t1 - t0) / (1024 * 1024)
        print(f"  Speed: {mbps:.2f} MB/s")

    print("\n=== Done ===")
    return 0

if __name__ == '__main__':
    sys.exit(main())
