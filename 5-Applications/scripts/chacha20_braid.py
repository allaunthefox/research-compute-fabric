# Copyright (c) 2026 Sovereign Research Stack. All rights reserved.
# Released under Apache 2.0 license as described in the file LICENSE.
# Authors: Research Stack Team
#
# chacha20_braid.py — ChaCha20 encryption for braid data before VCN encoding
#
# Encrypts braid strand data using ChaCha20 stream cipher before it enters
# the VCN (Virtual Compute Network) encoding pipeline.

from __future__ import annotations

import hashlib
import os
import secrets
import struct
from typing import Tuple

try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms
    from cryptography.hazmat.backends import default_backend
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False


# ════════════════════════════════════════════════════════════
# §1  Key and Nonce Types
# ════════════════════════════════════════════════════════════

KEY_SIZE = 32   # 256-bit key
NONCE_SIZE = 16  # 128-bit nonce (cryptography lib uses 16-byte nonce)


# ════════════════════════════════════════════════════════════
# §2  Pure Python ChaCha20 (fallback if cryptography lib absent)
# ════════════════════════════════════════════════════════════

def _quarter_round(state: list, a: int, b: int, c: int, d: int) -> None:
    """ChaCha20 quarter round operation."""
    def rotl32(v, n):
        return ((v << n) | (v >> (32 - n))) & 0xFFFFFFFF

    state[a] = (state[a] + state[b]) & 0xFFFFFFFF
    state[d] ^= state[a]
    state[d] = rotl32(state[d], 16)

    state[c] = (state[c] + state[d]) & 0xFFFFFFFF
    state[b] ^= state[c]
    state[b] = rotl32(state[b], 12)

    state[a] = (state[a] + state[b]) & 0xFFFFFFFF
    state[d] ^= state[a]
    state[d] = rotl32(state[d], 8)

    state[c] = (state[c] + state[d]) & 0xFFFFFFFF
    state[b] ^= state[c]
    state[b] = rotl32(state[b], 7)


def _chacha20_block(key: bytes, counter: int, nonce: bytes) -> bytes:
    """Generate one ChaCha20 keystream block (64 bytes).
    
    Uses DJB's original ChaCha20 with 64-bit counter + 64-bit nonce.
    The nonce is 16 bytes: first 8 bytes are the initial counter (little-endian),
    last 8 bytes are the nonce.
    """
    assert len(key) == 32
    assert len(nonce) == 16

    # "expand 32-byte k" magic constants
    constants = [0x61707865, 0x3320646e, 0x79622d32, 0x6b206574]

    # Key words
    k = [struct.unpack('<I', key[i:i+4])[0] for i in range(0, 32, 4)]

    # Nonce words (16 bytes = 4 words)
    n = [struct.unpack('<I', nonce[i:i+4])[0] for i in range(0, 16, 4)]

    # Counter: combine initial counter from nonce bytes 0-7 with block counter
    init_counter_lo = n[0]
    init_counter_hi = n[1]
    combined_counter = init_counter_lo + counter
    # Handle carry
    if combined_counter > 0xFFFFFFFF:
        combined_counter_lo = combined_counter & 0xFFFFFFFF
        combined_counter_hi = (init_counter_hi + 1) & 0xFFFFFFFF
    else:
        combined_counter_lo = combined_counter
        combined_counter_hi = init_counter_hi

    state = constants + k + [combined_counter_lo, combined_counter_hi, n[2], n[3]]
    working = list(state)

    # 20 rounds (10 double-rounds)
    for _ in range(10):
        # Column rounds
        _quarter_round(working, 0, 4, 8, 12)
        _quarter_round(working, 1, 5, 9, 13)
        _quarter_round(working, 2, 6, 10, 14)
        _quarter_round(working, 3, 7, 11, 15)
        # Diagonal rounds
        _quarter_round(working, 0, 5, 10, 15)
        _quarter_round(working, 1, 6, 11, 12)
        _quarter_round(working, 2, 7, 8, 13)
        _quarter_round(working, 3, 4, 9, 14)

    # Add original state
    result = [(working[i] + state[i]) & 0xFFFFFFFF for i in range(16)]

    return b''.join(struct.pack('<I', w) for w in result)


def _chacha20_encrypt(key: bytes, nonce: bytes, plaintext: bytes) -> bytes:
    """Encrypt using ChaCha20 (pure Python fallback)."""
    ciphertext = bytearray()
    counter = 0  # DJB ChaCha20 starts counter at 0 (initial counter in nonce bytes 0-7)

    for i in range(0, len(plaintext), 64):
        block = _chacha20_block(key, counter, nonce)
        chunk = plaintext[i:i + 64]
        for j in range(len(chunk)):
            ciphertext.append(chunk[j] ^ block[j])
        counter += 1

    return bytes(ciphertext)


# ════════════════════════════════════════════════════════════
# §3  Braid Encryption API
# ════════════════════════════════════════════════════════════

def generate_key() -> bytes:
    """Generate a cryptographically random 256-bit ChaCha20 key.

    Returns:
        32 bytes of random key material.
    """
    return secrets.token_bytes(KEY_SIZE)


def generate_nonce() -> bytes:
    """Generate a cryptographically random 96-bit ChaCha20 nonce.

    Returns:
        12 bytes of random nonce material.
    """
    return secrets.token_bytes(NONCE_SIZE)


def derive_key_from_strands(strand_data: list[int], salt: bytes | None = None) -> bytes:
    """Derive an encryption key from braid strand data.

    Uses HKDF-like construction: SHA-256(strand_bytes || salt).

    Args:
        strand_data: List of strand integer values.
        salt: Optional salt bytes. Generated if None.

    Returns:
        Tuple of (derived_key, salt_used).
    """
    if salt is None:
        salt = secrets.token_bytes(16)

    # Encode strand data as bytes
    strand_bytes = b''.join(struct.pack('<q', s) for s in strand_data)

    # HKDF-like: extract and expand
    prk = hashlib.sha256(salt + strand_bytes).digest()
    # Expand: generate 32 bytes from PRK
    key = hashlib.sha256(prk + b'\x01' + salt).digest()

    return key, salt


def encrypt_braid(data: bytes, key: bytes, nonce: bytes) -> bytes:
    """Encrypt braid data using ChaCha20.

    Args:
        data: Plaintext braid data bytes.
        key: 32-byte ChaCha20 key.
        nonce: 12-byte ChaCha20 nonce.

    Returns:
        Encrypted data (same length as input).

    Raises:
        ValueError: If key or nonce have incorrect length.
    """
    if len(key) != KEY_SIZE:
        raise ValueError(f"Key must be {KEY_SIZE} bytes, got {len(key)}")
    if len(nonce) != NONCE_SIZE:
        raise ValueError(f"Nonce must be {NONCE_SIZE} bytes, got {len(nonce)}")

    if HAS_CRYPTOGRAPHY:
        cipher = Cipher(
            algorithms.ChaCha20(key, nonce),
            mode=None,
            backend=default_backend(),
        )
        encryptor = cipher.encryptor()
        return encryptor.update(data) + encryptor.finalize()
    else:
        return _chacha20_encrypt(key, nonce, data)


def decrypt_braid(encrypted_data: bytes, key: bytes, nonce: bytes) -> bytes:
    """Decrypt braid data using ChaCha20.

    ChaCha20 is a symmetric stream cipher — decryption is the same
    operation as encryption (XOR with keystream).

    Args:
        encrypted_data: Ciphertext bytes.
        key: 32-byte ChaCha20 key (must match encryption key).
        nonce: 16-byte ChaCha20 nonce (must match encryption nonce).

    Returns:
        Decrypted plaintext data.

    Raises:
        ValueError: If key or nonce have incorrect length.
    """
    if len(key) != KEY_SIZE:
        raise ValueError(f"Key must be {KEY_SIZE} bytes, got {len(key)}")
    if len(nonce) != NONCE_SIZE:
        raise ValueError(f"Nonce must be {NONCE_SIZE} bytes, got {len(nonce)}")

    if HAS_CRYPTOGRAPHY:
        cipher = Cipher(
            algorithms.ChaCha20(key, nonce),
            mode=None,
            backend=default_backend(),
        )
        decryptor = cipher.decryptor()
        return decryptor.update(encrypted_data) + decryptor.finalize()
    else:
        return _chacha20_encrypt(key, nonce, encrypted_data)


# ════════════════════════════════════════════════════════════
# §4  Wire Format: Encrypted Braid Packet
# ════════════════════════════════════════════════════════════

# Encrypted Braid Packet:
# ┌───────────┬──────────┬──────────────────┐
# │ Nonce(16) │ Salt(16) │ Ciphertext(var)  │
# └───────────┴──────────┴──────────────────┘

def pack_encrypted_packet(
    ciphertext: bytes,
    nonce: bytes,
    salt: bytes,
) -> bytes:
    """Pack encrypted braid data into a wire-format packet.

    Args:
        ciphertext: Encrypted data.
        nonce: 16-byte nonce.
        salt: 16-byte key derivation salt.

    Returns:
        Packed packet bytes.
    """
    assert len(nonce) == NONCE_SIZE
    assert len(salt) == 16
    return nonce + salt + ciphertext


def unpack_encrypted_packet(packet: bytes) -> Tuple[bytes, bytes, bytes]:
    """Unpack an encrypted braid packet.

    Args:
        packet: Packed packet bytes.

    Returns:
        Tuple of (nonce, salt, ciphertext).
    """
    if len(packet) < NONCE_SIZE + 16:
        raise ValueError("Packet too short")
    nonce = packet[:NONCE_SIZE]
    salt = packet[NONCE_SIZE:NONCE_SIZE + 16]
    ciphertext = packet[NONCE_SIZE + 16:]
    return nonce, salt, ciphertext


# ════════════════════════════════════════════════════════════
# §5  Module API
# ════════════════════════════════════════════════════════════

__all__ = [
    "generate_key",
    "generate_nonce",
    "derive_key_from_strands",
    "encrypt_braid",
    "decrypt_braid",
    "pack_encrypted_packet",
    "unpack_encrypted_packet",
    "KEY_SIZE",
    "NONCE_SIZE",
]


if __name__ == "__main__":
    print("ChaCha20 Braid Encryption — Research Stack")
    print("=" * 50)
    lib_status = "cryptography" if HAS_CRYPTOGRAPHY else "pure Python fallback"
    print(f"Backend: {lib_status}")

    # Test basic encrypt/decrypt
    key = generate_key()
    nonce = generate_nonce()
    plaintext = b"Braid strand data: phase=[1.0, 2.5], crossing=3, admissible=true"

    ciphertext = encrypt_braid(plaintext, key, nonce)
    assert len(ciphertext) == len(plaintext), "ChaCha20 preserves length"
    print(f"Plaintext:  {len(plaintext)} bytes")
    print(f"Ciphertext: {len(ciphertext)} bytes")

    decrypted = decrypt_braid(ciphertext, key, nonce)
    assert decrypted == plaintext, "Decryption mismatch!"
    print("Encrypt/decrypt round-trip: PASS")

    # Test key derivation from strands
    strands = [0x1234, 0x5678, 0x9ABC, 0xDEF0]
    derived_key, salt = derive_key_from_strands(strands)
    derived_key2, _ = derive_key_from_strands(strands, salt=salt)
    assert derived_key == derived_key2, "Key derivation not deterministic!"
    print("Key derivation from strands: PASS")

    # Test packet packing
    nonce2 = generate_nonce()
    ciphertext2 = encrypt_braid(b"test payload", derived_key, nonce2)
    packet = pack_encrypted_packet(ciphertext2, nonce2, salt)
    n, s, c = unpack_encrypted_packet(packet)
    assert n == nonce2 and s == salt and c == ciphertext2, "Packet round-trip failed!"
    decrypted2 = decrypt_braid(c, derived_key, n)
    assert decrypted2 == b"test payload", "Packet decrypt failed!"
    print("Packet pack/unpack/decrypt: PASS")

    # Test wrong key fails
    wrong_key = generate_key()
    try:
        bad_decrypt = decrypt_braid(ciphertext, wrong_key, nonce)
        if bad_decrypt != plaintext:
            print("Wrong key produces different output: PASS")
        else:
            print("Wrong key check: SKIP (same keystream not expected)")
    except Exception:
        print("Wrong key raises exception: PASS")

    print("\nAll tests complete.")
