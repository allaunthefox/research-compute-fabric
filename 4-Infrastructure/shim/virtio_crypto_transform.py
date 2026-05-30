#!/usr/bin/env python3
"""
Virtio-Crypto Transform — Use virtio-crypto sessions as a hash computation pipeline.

Implements the HASH session primitive from the virtio-crypto spec:
  1. VirtioCryptoSession — create a HASH session (SHA-256, SHA-512, MD5)
  2. VirtioCryptoHashTransform — encode data as a HASH request, produce receipt
  3. VirtioCryptoTransformReceipt — machine-readable result with witness

This is NOT a crypto driver. It is a computation substrate that models the
virtio-crypto control queue and data queue protocol. The host QEMU backend
(gcrypt/AES-NI) processes hash requests without knowing it is being used
for general computation.

Shim boundary: I/O only. No decision logic. All computation mapping decisions
belong in Lean (future VirtioCrypto modules).

Reference: virtio/virtio_crypto.h (Linux kernel headers), RFC 6234 (SHA test vectors)

Usage:
    python3 virtio_crypto_transform.py --example
    python3 virtio_crypto_transform.py --analyze <payload.bin>
    python3 virtio_crypto_transform.py hash <payload.bin> [--algo sha256|sha512|md5]
    python3 virtio_crypto_transform.py session-info [--algo sha256]
    python3 virtio_crypto_transform.py receipt <result.json>
    python3 virtio_crypto_transform.py --test-vectors
"""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

# ── Virtio-Crypto Constants ──────────────────────────────────────────────────

# Opcodes (from linux/virtio_crypto.h)
VIRTIO_CRYPTO_OPCODE_HASH: int = 0x06
VIRTIO_CRYPTO_OPCODE_SYMCIPHER: int = 0x07
VIRTIO_CRYPTO_OPCODE_AKCIPHER: int = 0x08

# Session types
VIRTIO_CRYPTO_OP_SESSION_CREATE: int = 0x01
VIRTIO_CRYPTO_OP_SESSION_DESTROY: int = 0x02

# Hash algorithms (from linux/virtio_crypto.h)
VIRTIO_CRYPTO_HASH_SHA1: int = 0
VIRTIO_CRYPTO_HASH_SHA224: int = 1
VIRTIO_CRYPTO_HASH_SHA256: int = 2
VIRTIO_CRYPTO_HASH_SHA384: int = 3
VIRTIO_CRYPTO_HASH_SHA512: int = 4
VIRTIO_CRYPTO_HASH_MD5: int = 5
VIRTIO_CRYPTO_HASH_SHA3_224: int = 6
VIRTIO_CRYPTO_HASH_SHA3_256: int = 7
VIRTIO_CRYPTO_HASH_SHA3_384: int = 8
VIRTIO_CRYPTO_HASH_SHA3_512: int = 9

# Status codes
VIRTIO_CRYPTO_OK: int = 0
VIRTIO_CRYPTO_ERR: int = 1
VIRTIO_CRYPTO_BADMSG: int = 2
VIRTIO_CRYPTO_NOTSUPP: int = 3
VIRTIO_CRYPTO_INVSESS: int = 4

# Feature bits
VIRTIO_CRYPTO_F_CIPHER_STATELESS: int = 0
VIRTIO_CRYPTO_F_HASH_STATELESS: int = 1

# Algorithm name mapping
ALGO_MAP: Dict[str, int] = {
    "md5": VIRTIO_CRYPTO_HASH_MD5,
    "sha1": VIRTIO_CRYPTO_HASH_SHA1,
    "sha224": VIRTIO_CRYPTO_HASH_SHA224,
    "sha256": VIRTIO_CRYPTO_HASH_SHA256,
    "sha384": VIRTIO_CRYPTO_HASH_SHA384,
    "sha512": VIRTIO_CRYPTO_HASH_SHA512,
    "sha3_224": VIRTIO_CRYPTO_HASH_SHA3_224,
    "sha3_256": VIRTIO_CRYPTO_HASH_SHA3_256,
    "sha3_384": VIRTIO_CRYPTO_HASH_SHA3_384,
    "sha3_512": VIRTIO_CRYPTO_HASH_SHA3_512,
}

ALGO_DIGEST_SIZE: Dict[str, int] = {
    "md5": 16,
    "sha1": 20,
    "sha224": 28,
    "sha256": 32,
    "sha384": 48,
    "sha512": 64,
    "sha3_224": 28,
    "sha3_256": 32,
    "sha3_384": 48,
    "sha3_512": 64,
}

ALGO_VIRTIO_CODE: Dict[str, int] = {
    "md5": VIRTIO_CRYPTO_HASH_MD5,
    "sha1": VIRTIO_CRYPTO_HASH_SHA1,
    "sha256": VIRTIO_CRYPTO_HASH_SHA256,
    "sha384": VIRTIO_CRYPTO_HASH_SHA384,
    "sha512": VIRTIO_CRYPTO_HASH_SHA512,
}

# ── Virtio-Crypto Header Structures ─────────────────────────────────────────


@dataclass
class VirtioCryptoCtrlHdr:
    """struct virtio_crypto_ctrl_header — control queue header.

    Layout (from linux/virtio_crypto.h):
        __le32 opcode
        __le32 algo
        __le32 flag
        __le32 session_id
        __u8   padding[4]
    Total: 20 bytes
    """
    opcode: int = 0
    algo: int = 0
    flag: int = 0
    session_id: int = 0

    CTRL_SIZE: int = 20  # 4 + 4 + 4 + 4 + 4 padding

    def pack(self) -> bytes:
        return struct.pack(
            "!IIIII",
            self.opcode,
            self.algo,
            self.flag,
            self.session_id,
            0,  # padding
        )

    @staticmethod
    def unpack(data: bytes) -> "VirtioCryptoCtrlHdr":
        opcode, algo, flag, session_id, _ = struct.unpack("!IIIII", data[:20])
        return VirtioCryptoCtrlHdr(
            opcode=opcode,
            algo=algo,
            flag=flag,
            session_id=session_id,
        )


@dataclass
class VirtioCryptoSessionInput:
    """struct virtio_crypto_session_input — session creation result.

    Layout:
        __le32 session_id
        __le32 status
    Total: 8 bytes
    """
    session_id: int = 0
    status: int = VIRTIO_CRYPTO_OK

    def pack(self) -> bytes:
        return struct.pack("!II", self.session_id, self.status)

    @staticmethod
    def unpack(data: bytes) -> "VirtioCryptoSessionInput":
        session_id, status = struct.unpack("!II", data[:8])
        return VirtioCryptoSessionInput(session_id=session_id, status=status)


@dataclass
class VirtioCryptoHashSessionPara:
    """struct virtio_crypto_hash_session_para — hash session parameters.

    Layout:
        __le32 algo
        __le32 hash_result_len
    Total: 8 bytes
    """
    algo: int = VIRTIO_CRYPTO_HASH_SHA256
    hash_result_len: int = 32

    def pack(self) -> bytes:
        return struct.pack("!II", self.algo, self.hash_result_len)

    @staticmethod
    def unpack(data: bytes) -> "VirtioCryptoHashSessionPara":
        algo, hash_result_len = struct.unpack("!II", data[:8])
        return VirtioCryptoHashSessionPara(algo=algo, hash_result_len=hash_result_len)


@dataclass
class VirtioCryptoHashDataReq:
    """struct virtio_crypto_hash_data_req — data queue request for hash.

    Layout:
        struct virtio_crypto_ctrl_hdr header
        __le32 src_data_len
        __le32 dst_data_len
    Total: 28 bytes (20 + 4 + 4)
    """
    header: VirtioCryptoCtrlHdr = field(default_factory=VirtioCryptoCtrlHdr)
    src_data_len: int = 0
    dst_data_len: int = 0

    HASH_REQ_SIZE: int = 28

    def pack(self) -> bytes:
        return self.header.pack() + struct.pack(
            "!II", self.src_data_len, self.dst_data_len
        )

    @staticmethod
    def unpack(data: bytes) -> "VirtioCryptoHashDataReq":
        header = VirtioCryptoCtrlHdr.unpack(data[:20])
        src_data_len, dst_data_len = struct.unpack("!II", data[20:28])
        return VirtioCryptoHashDataReq(
            header=header,
            src_data_len=src_data_len,
            dst_data_len=dst_data_len,
        )


# ── Session and Transform ────────────────────────────────────────────────────


@dataclass
class VirtioCryptoSession:
    """A HASH session in virtio-crypto.

    Models the session creation handshake:
      Guest → control queue: VirtioCryptoCtrlHdr + VirtioCryptoHashSessionPara
      Host  → control queue: VirtioCryptoSessionInput (session_id, status)

    The session_id is then used for all subsequent hash requests on this session.
    """
    algo: str = "sha256"
    algo_code: int = VIRTIO_CRYPTO_HASH_SHA256
    digest_size: int = 32
    session_id: int = 0
    status: int = VIRTIO_CRYPTO_OK

    @staticmethod
    def create(algo: str = "sha256") -> "VirtioCryptoSession":
        """Create a new hash session for the given algorithm."""
        algo_lower = algo.lower()
        if algo_lower not in ALGO_MAP:
            raise ValueError(f"Unknown algorithm: {algo}. Supported: {list(ALGO_MAP.keys())}")
        algo_code = ALGO_MAP[algo_lower]
        digest_size = ALGO_DIGEST_SIZE[algo_lower]
        return VirtioCryptoSession(
            algo=algo_lower,
            algo_code=algo_code,
            digest_size=digest_size,
        )

    def session_create_request(self) -> bytes:
        """Encode the control queue session creation request."""
        ctrl = VirtioCryptoCtrlHdr(
            opcode=VIRTIO_CRYPTO_OP_SESSION_CREATE,
            algo=self.algo_code,
            flag=VIRTIO_CRYPTO_F_HASH_STATELESS,
            session_id=0,
        )
        para = VirtioCryptoHashSessionPara(
            algo=self.algo_code,
            hash_result_len=self.digest_size,
        )
        return ctrl.pack() + para.pack()

    def session_create_response(self) -> bytes:
        """Encode the host's session creation response."""
        resp = VirtioCryptoSessionInput(
            session_id=self.session_id,
            status=self.status,
        )
        return resp.pack()

    def destroy_request(self) -> bytes:
        """Encode the session destroy request."""
        ctrl = VirtioCryptoCtrlHdr(
            opcode=VIRTIO_CRYPTO_OP_SESSION_DESTROY,
            algo=self.algo_code,
            flag=0,
            session_id=self.session_id,
        )
        return ctrl.pack()


@dataclass
class VirtioCryptoTransformReceipt:
    """Machine-readable receipt for a virtio-crypto hash transform."""
    schema: str = "virtio_crypto_transform_receipt_v1"
    transform_type: str = "hash"
    algo: str = "sha256"
    algo_code: int = VIRTIO_CRYPTO_HASH_SHA256
    payload_bytes: int = 0
    result_hex: str = ""
    result_bytes: int = 0
    session_id: int = 0
    witness_hash: str = ""
    request_header_hex: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": self.schema,
            "transform_type": self.transform_type,
            "algo": self.algo,
            "algo_code": self.algo_code,
            "payload_bytes": self.payload_bytes,
            "result_hex": self.result_hex,
            "result_bytes": self.result_bytes,
            "session_id": self.session_id,
            "witness_hash": self.witness_hash,
            "request_header_hex": self.request_header_hex,
        }


def _compute_hash(algo: str, data: bytes) -> bytes:
    """Compute a hash using Python's hashlib (models QEMU's crypto backend)."""
    import hashlib
    h = hashlib.new(algo)
    h.update(data)
    return h.digest()


def _witness(data: bytes) -> str:
    """SHA-256 of the full request+result bundle for receipt verification."""
    import hashlib
    return hashlib.sha256(data).hexdigest()


# ── Transform Implementation ─────────────────────────────────────────────────


def transform_hash(
    payload: bytes,
    algo: str = "sha256",
    session_id: int = 1,
) -> Tuple[bytes, VirtioCryptoTransformReceipt]:
    """HASH transform: encode data as a virtio-crypto HASH request, compute hash.

    Protocol flow:
      1. Guest creates HASH session on control queue → session_id
      2. Guest posts VirtioCryptoHashDataReq + payload on data queue
      3. Host (QEMU crypto backend) computes hash
      4. Host writes hash result to dst buffer on data queue

    This function models the full round-trip. The hash is computed locally
    (matching what QEMU's gcrypt backend would produce).

    Returns (result_digest, receipt).
    """
    session = VirtioCryptoSession.create(algo)
    session.session_id = session_id

    # Encode the data queue request header
    data_req = VirtioCryptoHashDataReq(
        header=VirtioCryptoCtrlHdr(
            opcode=VIRTIO_CRYPTO_OPCODE_HASH,
            algo=session.algo_code,
            flag=VIRTIO_CRYPTO_F_HASH_STATELESS,
            session_id=session_id,
        ),
        src_data_len=len(payload),
        dst_data_len=session.digest_size,
    )

    # Compute hash (models QEMU crypto backend)
    digest = _compute_hash(algo, payload)

    # Build receipt
    request_bytes = data_req.pack() + payload
    receipt = VirtioCryptoTransformReceipt(
        transform_type="hash",
        algo=algo,
        algo_code=session.algo_code,
        payload_bytes=len(payload),
        result_hex=digest.hex(),
        result_bytes=len(digest),
        session_id=session_id,
        witness_hash=_witness(request_bytes + digest),
        request_header_hex=data_req.pack().hex(),
    )

    return digest, receipt


# ── RFC 6234 Test Vectors ────────────────────────────────────────────────────

SHA256_TEST_VECTORS: List[Tuple[str, str]] = [
    # (input, expected_sha256_hex)
    ("", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
    ("abc", "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"),
    ("abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq",
     "248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1"),
    ("abcdefghbcdefghicdefghijdefghijkefghijklfghijklmghijklmnhijklmnoijklmnopjklmnopqklmnopqrlmnopqrsmnopqrstnopqrstu",
     "cf5b16a778af8380036ce59e7b0492370b249b11e8f07a51afac45037afee9d1"),
]

SHA512_TEST_VECTORS: List[Tuple[str, str]] = [
    ("", "cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e"),
    ("abc", "ddaf35a193617abacc417349ae20413112e6fa4e89a97ea20a9eeee64b55d39a2192992a274fc1a836ba3c23a3feebbd454d4423643ce80e2a9ac94fa54ca49f"),
]

MD5_TEST_VECTORS: List[Tuple[str, str]] = [
    ("", "d41d8cd98f00b204e9800998ecf8427e"),
    ("abc", "900150983cd24fb0d6963f7d28e17f72"),
    ("message digest", "f96b697d7cb7938d525a2f31aaf161d0"),
    ("abcdefghijklmnopqrstuvwxyz", "c3fcd3d76192e4007dfb496cca67e13b"),
]


# ── CLI ──────────────────────────────────────────────────────────────────────


def main():
    args = sys.argv[1:]

    if not args or args[0] == "--example":
        print("=== Virtio-Crypto Transform ===")
        print()
        print("HASH computation via virtio-crypto sessions:")
        print()
        print("  payload → HASH session (SHA-256/SHA-512/MD5)")
        print("         → QEMU crypto backend computes hash")
        print("         → result digest + receipt")
        print()
        print("=== Protocol ===")
        print()
        print("  1. Control queue: CREATE_SESSION(algo) → session_id")
        print("  2. Data queue:    HASH_REQUEST(session_id, payload) → digest")
        print("  3. Control queue: DESTROY_SESSION(session_id)")
        print()
        print("=== Demo ===")
        print()

        # SHA-256
        payload = b"abc"
        digest, receipt = transform_hash(payload, algo="sha256")
        print(f"SHA-256({payload!r}):")
        print(f"  result: {digest.hex()}")
        print(f"  receipt: {json.dumps(receipt.to_dict(), indent=2)}")
        print()

        # SHA-512
        digest, receipt = transform_hash(payload, algo="sha512")
        print(f"SHA-512({payload!r}):")
        print(f"  result: {digest.hex()}")
        print()

        # MD5
        digest, receipt = transform_hash(payload, algo="md5")
        print(f"MD5({payload!r}):")
        print(f"  result: {digest.hex()}")
        print()

        # Session creation wire format
        session = VirtioCryptoSession.create("sha256")
        session.session_id = 1
        req = session.session_create_request()
        print(f"Session create request ({len(req)} bytes): {req.hex()}")
        resp = session.session_create_response()
        print(f"Session create response ({len(resp)} bytes): {resp.hex()}")
        print()

        # Data request wire format
        data_req = VirtioCryptoHashDataReq(
            header=VirtioCryptoCtrlHdr(
                opcode=VIRTIO_CRYPTO_OPCODE_HASH,
                algo=VIRTIO_CRYPTO_HASH_SHA256,
                flag=VIRTIO_CRYPTO_F_HASH_STATELESS,
                session_id=1,
            ),
            src_data_len=3,
            dst_data_len=32,
        )
        print(f"Data request header ({len(data_req.pack())} bytes): {data_req.pack().hex()}")
        return

    if args[0] == "--analyze":
        if len(args) < 2:
            print("Usage: virtio_crypto_transform.py --analyze <payload.bin>", file=sys.stderr)
            sys.exit(1)
        payload = Path(args[1]).read_bytes()
        print(f"=== {args[1]} ===")
        print(f"  Size: {len(payload)} bytes")
        print(f"  SHA-256: {hashlib.sha256(payload).hexdigest()}")
        print(f"  SHA-512: {hashlib.sha512(payload).hexdigest()}")
        print(f"  MD5:     {hashlib.md5(payload).hexdigest()}")
        print(f"  Digest sizes: sha256=32B, sha512=64B, md5=16B")
        return

    if args[0] == "--test-vectors":
        print("=== RFC 6234 Test Vector Verification ===")
        print()
        all_pass = True

        # SHA-256
        print("--- SHA-256 ---")
        for i, (inp, expected) in enumerate(SHA256_TEST_VECTORS):
            digest, receipt = transform_hash(inp.encode(), algo="sha256")
            actual = digest.hex()
            ok = actual == expected
            status = "PASS" if ok else "FAIL"
            print(f"  [{status}] vector {i}: input={inp[:40]!r}{'...' if len(inp) > 40 else ''}")
            if not ok:
                print(f"         expected: {expected}")
                print(f"         actual:   {actual}")
                all_pass = False
        print()

        # SHA-512
        print("--- SHA-512 ---")
        for i, (inp, expected) in enumerate(SHA512_TEST_VECTORS):
            digest, receipt = transform_hash(inp.encode(), algo="sha512")
            actual = digest.hex()
            ok = actual == expected
            status = "PASS" if ok else "FAIL"
            print(f"  [{status}] vector {i}: input={inp[:40]!r}{'...' if len(inp) > 40 else ''}")
            if not ok:
                print(f"         expected: {expected}")
                print(f"         actual:   {actual}")
                all_pass = False
        print()

        # MD5
        print("--- MD5 ---")
        for i, (inp, expected) in enumerate(MD5_TEST_VECTORS):
            digest, receipt = transform_hash(inp.encode(), algo="md5")
            actual = digest.hex()
            ok = actual == expected
            status = "PASS" if ok else "FAIL"
            print(f"  [{status}] vector {i}: input={inp[:40]!r}{'...' if len(inp) > 40 else ''}")
            if not ok:
                print(f"         expected: {expected}")
                print(f"         actual:   {actual}")
                all_pass = False
        print()

        # Receipt schema check
        print("--- Receipt Schema ---")
        _, receipt = transform_hash(b"abc", algo="sha256")
        d = receipt.to_dict()
        required_keys = {"schema", "transform_type", "algo", "payload_bytes",
                         "result_hex", "witness_hash"}
        missing = required_keys - set(d.keys())
        if missing:
            print(f"  [FAIL] Missing keys in receipt: {missing}")
            all_pass = False
        else:
            print(f"  [PASS] Receipt has all required keys: {sorted(required_keys)}")
        print(f"         schema={d['schema']}, transform_type={d['transform_type']}")
        print()

        if all_pass:
            print("ALL TEST VECTORS PASSED")
        else:
            print("SOME TESTS FAILED")
            sys.exit(1)
        return

    if args[0] == "hash":
        if len(args) < 2:
            print("Usage: virtio_crypto_transform.py hash <payload.bin> [--algo sha256|sha512|md5]", file=sys.stderr)
            sys.exit(1)
        payload = Path(args[1]).read_bytes()
        algo = "sha256"
        if "--algo" in args:
            ai = args.index("--algo")
            algo = args[ai + 1]
        digest, receipt = transform_hash(payload, algo=algo)
        print(json.dumps(receipt.to_dict(), indent=2))
        return

    if args[0] == "session-info":
        algo = "sha256"
        if "--algo" in args:
            ai = args.index("--algo")
            algo = args[ai + 1]
        session = VirtioCryptoSession.create(algo)
        info = {
            "algo": session.algo,
            "algo_code": session.algo_code,
            "digest_size": session.digest_size,
            "supported_algorithms": list(ALGO_MAP.keys()),
            "session_create_request_size": len(session.session_create_request()),
            "session_create_response_size": len(session.session_create_response()),
        }
        print(json.dumps(info, indent=2))
        return

    if args[0] == "receipt":
        if len(args) < 2:
            print("Usage: virtio_crypto_transform.py receipt <result.json>", file=sys.stderr)
            sys.exit(1)
        data = json.loads(Path(args[1]).read_text())
        print(json.dumps(data, indent=2))
        return

    print("Usage: virtio_crypto_transform.py <command> [args]", file=sys.stderr)
    print("Commands: --example, --analyze, --test-vectors, hash, session-info, receipt", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
