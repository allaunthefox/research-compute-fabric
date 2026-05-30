#!/usr/bin/env python3
"""
Ivshmem Client — Zero-copy VM-to-VM communication via shared memory.

Implements the ivshmem (Inter-VM Shared Memory) protocol for QEMU:
  1. IvshmemClient  — mmap /dev/shm/ivshmem_bar0 for shared memory access
  2. IvshmemRing    — doorbell ring for peer notification
  3. IvshmemTransform — encode data as shared memory write + notify peer
  4. IvshmemReceipt — machine-readable receipt for shared memory operations

This is NOT a full ivshmem driver. It is a computation substrate that uses
QEMU's ivshmem device as a zero-copy shared memory mailbox. The peer VM
reads data from the same physical memory region without copying.

Shim boundary: I/O only. No decision logic. All computation routing
decisions belong in Lean (future MeshRouting or SharedMemory modules).

Reference: QEMU docs/interop/ivshmem-spec.txt, Linux ivshmem-client library

Usage:
    python3 ivshmem_client.py --example
    python3 ivshmem_client.py --analyze <payload.bin>
    python3 ivshmem_client.py write <payload.bin> [--offset <N>] [--slot <N>]
    python3 ivshmem_client.py read --offset <N> --length <N>
    python3 ivshmem_client.py ring --doorbell <N>
    python3 ivshmem_client.py receipt <result.json>
    python3 ivshmem_client.py --test-devshm
"""

from __future__ import annotations

import hashlib
import json
import mmap
import os
import struct
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ── Ivshmem Constants ──────────────────────────────────────────────────────

# Default BAR0 size (64 MiB shared memory region)
IVSHMEM_BAR0_DEFAULT_SIZE: int = 64 * 1024 * 1024

# Doorbell register offset within BAR0 (QEMU ivshmem-spec)
IVSHMEM_BAR0_DOORBELL_OFFSET: int = 0x00

# Maximum payload size per write (1 MiB, to avoid single-write bottlenecks)
IVSHMEM_MAX_PAYLOAD_SIZE: int = 1 * 1024 * 1024

# Slot header size: 8 bytes (uint32 length + uint32 sequence)
IVSHMEM_SLOT_HEADER_SIZE: int = 8

# Default slot count in shared memory region
IVSHMEM_DEFAULT_SLOT_COUNT: int = 64

# Slot size: payload region per slot (1 MiB)
IVSHMEM_SLOT_SIZE: int = IVSHMEM_MAX_PAYLOAD_SIZE

# Total region layout:
#   [0x0000_0000 - 0x0000_FFFF]  BAR0 registers (doorbell, interrupt mask)
#   [0x0001_0000 - 0x0001_FFFF]  Slot metadata (sequence numbers, flags)
#   [0x0002_0000 - ...]           Slot data regions
IVSHMEM_REGISTER_REGION_SIZE: int = 0x10000
IVSHMEM_METADATA_REGION_OFFSET: int = 0x10000
IVSHMEM_DATA_REGION_OFFSET: int = 0x20000

# ── Data Classes ───────────────────────────────────────────────────────────


@dataclass
class IvshmemSlotHeader:
    """Header for a single shared memory slot (8 bytes)."""
    length: int = 0          # uint32: payload length in bytes
    sequence: int = 0        # uint32: monotonically increasing sequence number

    def pack(self) -> bytes:
        return struct.pack("!II", self.length, self.sequence)

    @staticmethod
    def unpack(data: bytes) -> "IvshmemSlotHeader":
        length, sequence = struct.unpack("!II", data[:IVSHMEM_SLOT_HEADER_SIZE])
        return IvshmemSlotHeader(length=length, sequence=sequence)

    def sizeof(self) -> int:
        return IVSHMEM_SLOT_HEADER_SIZE


@dataclass
class IvshmemMetadata:
    """Metadata for one slot in the metadata region (16 bytes)."""
    sequence: int = 0        # uint32: last written sequence
    length: int = 0          # uint32: last written length
    flags: int = 0           # uint32: status flags (bit 0 = valid, bit 1 = read)
    timestamp_lo: int = 0    # uint32: low 32 bits of write timestamp

    FLAG_VALID: int = 1
    FLAG_READ: int = 2

    def pack(self) -> bytes:
        return struct.pack("!IIII", self.sequence, self.length, self.flags, self.timestamp_lo)

    @staticmethod
    def unpack(data: bytes) -> "IvshmemMetadata":
        seq, length, flags, ts = struct.unpack("!IIII", data[:16])
        return IvshmemMetadata(sequence=seq, length=length, flags=flags, timestamp_lo=ts)

    def sizeof(self) -> int:
        return 16


@dataclass
class IvshmemState:
    """State snapshot of the shared memory region. Used for receipts."""
    bar0_size: int = IVSHMEM_BAR0_DEFAULT_SIZE
    slot_count: int = IVSHMEM_DEFAULT_SLOT_COUNT
    slot_size: int = IVSHMEM_SLOT_SIZE
    active_slot: int = 0
    sequence_counter: int = 0
    bytes_written: int = 0
    doorbell_rang: bool = False


@dataclass
class IvshmemReceipt:
    """Machine-readable receipt for a shared memory operation."""
    schema: str = "ivshmem_receipt_v1"
    transform_type: str = "shared_memory"
    offset: int = 0
    length: int = 0
    slot: int = 0
    sequence: int = 0
    doorbell: bool = False
    witness_hash: str = ""
    bar0_size: int = 0
    slot_count: int = 0
    payload_crc32: str = ""
    peer_notified: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": self.schema,
            "transform_type": self.transform_type,
            "offset": self.offset,
            "length": self.length,
            "slot": self.slot,
            "sequence": self.sequence,
            "doorbell": self.doorbell,
            "witness_hash": self.witness_hash,
            "bar0_size": self.bar0_size,
            "slot_count": self.slot_count,
            "payload_crc32": self.payload_crc32,
            "peer_notified": self.peer_notified,
        }


# ── IvshmemClient ──────────────────────────────────────────────────────────


class IvshmemClient:
    """Client for QEMU ivshmem shared memory BAR0.

    Maps /dev/shm/ivshmem_bar0 (or a fallback file) into process memory.
    Provides read/write access to the shared memory region without copying
    data through kernel buffers — true zero-copy between VMs on the same host.

    If the ivshmem device is not available, falls back to a memory-mapped
    file in /dev/shm for testing.
    """

    def __init__(
        self,
        device_path: str = "/dev/shm/ivshmem_bar0",
        bar0_size: int = IVSHMEM_BAR0_DEFAULT_SIZE,
        slot_count: int = IVSHMEM_DEFAULT_SLOT_COUNT,
        fallback_to_devshm: bool = True,
    ):
        self.device_path = device_path
        self.bar0_size = bar0_size
        self.slot_count = slot_count
        self.state = IvshmemState(
            bar0_size=bar0_size,
            slot_count=slot_count,
            slot_size=IVSHMEM_SLOT_SIZE,
        )
        self._mm: Optional[mmap.mmap] = None
        self._fd: Optional[int] = None
        self._fallback_path: Optional[str] = None
        self._is_fallback = False

    def open(self) -> None:
        """Open and memory-map the ivshmem BAR0 region."""
        if os.path.exists(self.device_path):
            self._fd = os.open(self.device_path, os.O_RDWR | os.O_CREAT)
            self._mm = mmap.mmap(self._fd, self.bar0_size)
            self._is_fallback = False
        elif self.device_path.startswith("/dev/shm/"):
            # Fallback: create a shared memory file for testing
            if not self.device_path.startswith("/dev/shm/"):
                raise FileNotFoundError(
                    f"ivshmem device not found: {self.device_path}"
                )
            self._fallback_path = self.device_path
            self._fd = os.open(
                self._fallback_path, os.O_RDWR | os.O_CREAT, 0o666
            )
            os.ftruncate(self._fd, self.bar0_size)
            self._mm = mmap.mmap(self._fd, self.bar0_size)
            self._is_fallback = True
        else:
            raise FileNotFoundError(
                f"ivshmem device not found: {self.device_path}"
            )

    def close(self) -> None:
        """Unmap and close the shared memory region."""
        if self._mm is not None:
            self._mm.close()
            self._mm = None
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None

    def __enter__(self) -> "IvshmemClient":
        self.open()
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    @property
    def is_open(self) -> bool:
        return self._mm is not None

    @property
    def is_fallback(self) -> bool:
        return self._is_fallback

    def read_region(self, offset: int, length: int) -> bytes:
        """Read bytes from the shared memory region at offset."""
        if self._mm is None:
            raise RuntimeError("IvshmemClient not opened")
        if offset + length > self.bar0_size:
            raise ValueError(
                f"Read beyond BAR0: offset={offset} length={length} "
                f"bar0_size={self.bar0_size}"
            )
        self._mm.seek(offset)
        return self._mm.read(length)

    def write_region(self, offset: int, data: bytes) -> None:
        """Write bytes to the shared memory region at offset."""
        if self._mm is None:
            raise RuntimeError("IvshmemClient not opened")
        if offset + len(data) > self.bar0_size:
            raise ValueError(
                f"Write beyond BAR0: offset={offset} length={len(data)} "
                f"bar0_size={self.bar0_size}"
            )
        self._mm.seek(offset)
        self._mm.write(data)

    def read_slot_header(self, slot: int) -> IvshmemSlotHeader:
        """Read the header for a given slot."""
        offset = IVSHMEM_DATA_REGION_OFFSET + slot * IVSHMEM_SLOT_SIZE
        header_bytes = self.read_region(offset, IVSHMEM_SLOT_HEADER_SIZE)
        return IvshmemSlotHeader.unpack(header_bytes)

    def write_slot_header(self, slot: int, header: IvshmemSlotHeader) -> None:
        """Write the header for a given slot."""
        offset = IVSHMEM_DATA_REGION_OFFSET + slot * IVSHMEM_SLOT_SIZE
        self.write_region(offset, header.pack())

    def read_slot_payload(self, slot: int, length: int) -> bytes:
        """Read payload from a slot (after the header)."""
        offset = (
            IVSHMEM_DATA_REGION_OFFSET
            + slot * IVSHMEM_SLOT_SIZE
            + IVSHMEM_SLOT_HEADER_SIZE
        )
        return self.read_region(offset, length)

    def write_slot_payload(self, slot: int, data: bytes) -> None:
        """Write payload to a slot (after the header)."""
        offset = (
            IVSHMEM_DATA_REGION_OFFSET
            + slot * IVSHMEM_SLOT_SIZE
            + IVSHMEM_SLOT_HEADER_SIZE
        )
        self.write_region(offset, data)

    def read_metadata(self, slot: int) -> IvshmemMetadata:
        """Read metadata for a slot from the metadata region."""
        offset = IVSHMEM_METADATA_REGION_OFFSET + slot * IvshmemMetadata().sizeof()
        data = self.read_region(offset, IvshmemMetadata().sizeof())
        return IvshmemMetadata.unpack(data)

    def write_metadata(self, slot: int, meta: IvshmemMetadata) -> None:
        """Write metadata for a slot to the metadata region."""
        offset = IVSHMEM_METADATA_REGION_OFFSET + slot * meta.sizeof()
        self.write_region(offset, meta.pack())

    def ring_doorbell(self, peer_id: int = 0) -> None:
        """Ring the doorbell register to notify the peer VM.

        In a real ivshmem setup, writing to BAR0 offset 0 triggers an
        interrupt on the peer VM. In fallback mode, this is a no-op
        (the peer reads from the same mmap).
        """
        if self._mm is None:
            raise RuntimeError("IvshmemClient not opened")
        # Write peer_id to doorbell register (4 bytes at offset 0)
        self._mm.seek(IVSHMEM_BAR0_DOORBELL_OFFSET)
        self._mm.write(struct.pack("!I", peer_id))
        self.state.doorbell_rang = True

    def get_state(self) -> IvshmemState:
        """Return a snapshot of the current client state."""
        return IvshmemState(
            bar0_size=self.state.bar0_size,
            slot_count=self.state.slot_count,
            slot_size=self.state.slot_size,
            active_slot=self.state.active_slot,
            sequence_counter=self.state.sequence_counter,
            bytes_written=self.state.bytes_written,
            doorbell_rang=self.state.doorbell_rang,
        )


# ── IvshmemRing ────────────────────────────────────────────────────────────


class IvshmemRing:
    """Doorbell ring abstraction for ivshmem notification.

    Wraps the doorbell write primitive into a ring buffer pattern.
    Each ring increments a sequence counter and writes to the doorbell
    register, allowing the peer to track notification order.
    """

    def __init__(self, client: IvshmemClient, peer_id: int = 0):
        self.client = client
        self.peer_id = peer_id
        self.ring_count: int = 0

    def ring(self, slot: int = 0) -> int:
        """Ring the doorbell and return the ring sequence number.

        Args:
            slot: Which slot the peer should read from.

        Returns:
            The ring sequence number (monotonically increasing).
        """
        self.ring_count += 1
        self.client.ring_doorbell(self.peer_id)
        return self.ring_count

    def ring_with_payload_length(self, slot: int, length: int) -> int:
        """Ring the doorbell with metadata about the payload.

        Before ringing, writes the payload length to the slot header
        so the peer knows how many bytes to read.

        Returns:
            The ring sequence number.
        """
        header = IvshmemSlotHeader(length=length, sequence=self.ring_count + 1)
        self.client.write_slot_header(slot, header)
        return self.ring(slot)


# ── IvshmemTransform ───────────────────────────────────────────────────────


class IvshmemTransform:
    """Encode data as a shared memory write and notify the peer.

    This is the primary transform primitive for ivshmem computation:
      1. Write payload to a shared memory slot
      2. Write metadata (length, sequence, flags)
      3. Ring doorbell to notify peer
      4. Generate a receipt

    The peer reads from the same slot offset — zero copy.
    """

    def __init__(
        self,
        client: IvshmemClient,
        ring: Optional[IvshmemRing] = None,
    ):
        self.client = client
        self.ring = ring or IvshmemRing(client)
        self._sequence: int = 0

    def transform(
        self,
        data: bytes,
        slot: Optional[int] = None,
        notify: bool = True,
    ) -> Tuple[int, IvshmemReceipt]:
        """Write data to shared memory and optionally notify the peer.

        Args:
            data: Payload bytes to write.
            slot: Slot index (auto-selected if None).
            notify: Whether to ring the doorbell after writing.

        Returns:
            (offset, receipt) where offset is the byte offset of the payload.
        """
        if len(data) > IVSHMEM_MAX_PAYLOAD_SIZE:
            raise ValueError(
                f"Payload too large: {len(data)} > {IVSHMEM_MAX_PAYLOAD_SIZE}"
            )

        # Auto-select slot
        if slot is None:
            slot = self.client.state.active_slot
            self.client.state.active_slot = (slot + 1) % self.client.state.slot_count

        self._sequence += 1

        # Write payload to slot
        payload_offset = (
            IVSHMEM_DATA_REGION_OFFSET
            + slot * IVSHMEM_SLOT_SIZE
            + IVSHMEM_SLOT_HEADER_SIZE
        )
        self.client.write_slot_payload(slot, data)

        # Write slot header
        header = IvshmemSlotHeader(length=len(data), sequence=self._sequence)
        self.client.write_slot_header(slot, header)

        # Write metadata
        import time
        ts_lo = int(time.time() * 1000) & 0xFFFFFFFF
        meta = IvshmemMetadata(
            sequence=self._sequence,
            length=len(data),
            flags=IvshmemMetadata.FLAG_VALID,
            timestamp_lo=ts_lo,
        )
        self.client.write_metadata(slot, meta)

        # Ring doorbell
        peer_notified = False
        if notify:
            self.ring.ring(slot)
            peer_notified = True

        # Update state
        self.client.state.sequence_counter = self._sequence
        self.client.state.bytes_written += len(data)

        # Generate receipt
        witness = self._compute_witness(data, slot, self._sequence)
        receipt = IvshmemReceipt(
            offset=payload_offset,
            length=len(data),
            slot=slot,
            sequence=self._sequence,
            doorbell=notify,
            witness_hash=witness,
            bar0_size=self.client.state.bar0_size,
            slot_count=self.client.state.slot_count,
            payload_crc32=f"{_crc32(data):08x}",
            peer_notified=peer_notified,
        )

        return payload_offset, receipt

    def read_from_slot(self, slot: int) -> Tuple[bytes, IvshmemSlotHeader]:
        """Read payload and header from a slot (peer-side operation)."""
        header = self.client.read_slot_header(slot)
        if header.length == 0:
            return b"", header
        payload = self.client.read_slot_payload(slot, header.length)
        return payload, header

    def _compute_witness(self, data: bytes, slot: int, sequence: int) -> str:
        """Compute a witness hash over the transform inputs."""
        h = hashlib.sha256()
        h.update(data)
        h.update(struct.pack("!II", slot, sequence))
        return h.hexdigest()[:16]


# ── Utility Functions ──────────────────────────────────────────────────────


def _crc32(data: bytes) -> int:
    """Compute CRC32 of data."""
    import zlib
    return zlib.crc32(data) & 0xFFFFFFFF


# ── CLI ────────────────────────────────────────────────────────────────────


def main() -> None:
    args = sys.argv[1:]

    if not args or args[0] == "--example":
        print("=== Ivshmem Client — Zero-Copy VM-to-VM Communication ===")
        print()
        print("Three primitives for shared-memory computation:")
        print()
        print("1. IvshmemClient (BAR0 mmap):")
        print("   Maps /dev/shm/ivshmem_bar0 into process memory")
        print("   Read/write at arbitrary offsets, zero kernel copies")
        print()
        print("2. IvshmemRing (doorbell):")
        print("   Write to BAR0 doorbell register → triggers peer interrupt")
        print("   Sequence-numbered notifications for ordering")
        print()
        print("3. IvshmemTransform (write + notify):")
        print("   payload → slot write → metadata → doorbell → peer reads")
        print("   Receipt: {schema, transform_type: 'shared_memory', offset, length, witness_hash}")
        print()
        print("=== Memory Layout ===")
        print(f"  BAR0 registers:   0x{0:08X} - 0x{IVSHMEM_REGISTER_REGION_SIZE - 1:08X}")
        print(f"  Slot metadata:    0x{IVSHMEM_METADATA_REGION_OFFSET:08X} - "
              f"0x{IVSHMEM_METADATA_REGION_OFFSET + IVSHMEM_DEFAULT_SLOT_COUNT * 16 - 1:08X}")
        print(f"  Slot data:        0x{IVSHMEM_DATA_REGION_OFFSET:08X} - ...")
        print(f"  Slot count:       {IVSHMEM_DEFAULT_SLOT_COUNT}")
        print(f"  Slot size:        {IVSHMEM_SLOT_SIZE} bytes (header + payload)")
        print()
        print("=== Demo ===")

        test_payload = b"\\xde\\xad\\xbe\\xef" * 16
        print(f"Payload ({len(test_payload)} bytes): {test_payload[:16].hex()}...")
        print()

        # Create client with fallback
        devshm_path = "/dev/shm/ivshmem_test_bar0"
        print(f"Creating IvshmemClient (fallback: {devshm_path})...")
        with IvshmemClient(device_path=devshm_path, bar0_size=IVSHMEM_BAR0_DEFAULT_SIZE) as client:
            transform = IvshmemTransform(client)
            offset, receipt = transform.transform(test_payload, slot=0, notify=True)
            print(f"Write offset: 0x{offset:08X}")
            print(f"Receipt: {json.dumps(receipt.to_dict(), indent=2)}")
            print()

            # Read back
            data, header = transform.read_from_slot(slot=0)
            print(f"Read back: {data[:16].hex()}... ({len(data)} bytes)")
            print(f"Header: length={header.length}, sequence={header.sequence}")
            print()

            # Ring-only
            ring = IvshmemRing(client, peer_id=1)
            seq = ring.ring(slot=0)
            print(f"Doorbell ring #{seq} to peer 1")
            print()

        # Cleanup
        if os.path.exists(devshm_path):
            os.unlink(devshm_path)
        return

    if args[0] == "--test-devshm":
        print("Testing with /dev/shm fallback...")
        test_path = "/dev/shm/ivshmem_test"
        try:
            with IvshmemClient(device_path=test_path) as client:
                print(f"  Opened: {test_path} (fallback={client.is_fallback})")
                print(f"  BAR0 size: {client.bar0_size} bytes")

                transform = IvshmemTransform(client)
                payload = b"Hello, ivshmem!" + b"\\x00" * 48
                offset, receipt = transform.transform(payload, slot=0, notify=False)
                print(f"  Wrote {len(payload)} bytes at offset 0x{offset:08X}")
                print(f"  Receipt: {json.dumps(receipt.to_dict(), indent=2)}")

                data, header = transform.read_from_slot(slot=0)
                assert data[:len(payload.rstrip(b'\\x00'))] == payload.rstrip(b'\\x00'), \
                    "Read-back mismatch!"
                print(f"  Read-back verified: {len(data)} bytes")
                print("  PASS")
        finally:
            if os.path.exists(test_path):
                os.unlink(test_path)
        return

    if args[0] == "--analyze":
        if len(args) < 2:
            print("Usage: ivshmem_client.py --analyze <payload.bin>", file=sys.stderr)
            sys.exit(1)
        payload = Path(args[1]).read_bytes()
        print(f"=== {args[1]} ===")
        print(f"  Size: {len(payload)} bytes")
        print(f"  CRC32: {_crc32(payload):08x}")
        print(f"  SHA256: {hashlib.sha256(payload).hexdigest()[:16]}")
        print(f"  Fits in 1 slot: {len(payload) <= IVSHMEM_MAX_PAYLOAD_SIZE}")
        print(f"  Slots needed: {-(-len(payload) // IVSHMEM_MAX_PAYLOAD_SIZE)}")
        print(f"  Max slot payload: {IVSHMEM_MAX_PAYLOAD_SIZE} bytes")
        return

    if args[0] == "write":
        if len(args) < 2:
            print("Usage: ivshmem_client.py write <payload.bin> [--offset <N>] [--slot <N>]", file=sys.stderr)
            sys.exit(1)
        payload_path = args[1]
        payload = Path(payload_path).read_bytes()
        offset_arg = None
        slot_arg = None
        if "--offset" in args:
            oi = args.index("--offset")
            offset_arg = int(args[oi + 1])
        if "--slot" in args:
            si = args.index("--slot")
            slot_arg = int(args[si + 1])

        devshm_path = "/dev/shm/ivshmem_bar0"
        with IvshmemClient(device_path=devshm_path) as client:
            transform = IvshmemTransform(client)
            if slot_arg is not None:
                offset, receipt = transform.transform(payload, slot=slot_arg, notify=True)
            else:
                offset, receipt = transform.transform(payload, notify=True)
            print(json.dumps(receipt.to_dict(), indent=2))
        return

    if args[0] == "read":
        offset_arg = 0
        length_arg = 64
        if "--offset" in args:
            oi = args.index("--offset")
            offset_arg = int(args[oi + 1])
        if "--length" in args:
            li = args.index("--length")
            length_arg = int(args[li + 1])
        if "--slot" in args:
            si = args.index("--slot")
            slot = int(args[si + 1])
            devshm_path = "/dev/shm/ivshmem_bar0"
            with IvshmemClient(device_path=devshm_path) as client:
                transform = IvshmemTransform(client)
                data, header = transform.read_from_slot(slot)
                result = {
                    "slot": slot,
                    "length": header.length,
                    "sequence": header.sequence,
                    "data_hex": data[:min(64, header.length)].hex(),
                }
                print(json.dumps(result, indent=2))
        else:
            devshm_path = "/dev/shm/ivshmem_bar0"
            with IvshmemClient(device_path=devshm_path) as client:
                data = client.read_region(offset_arg, length_arg)
                result = {
                    "offset": offset_arg,
                    "length": length_arg,
                    "data_hex": data.hex(),
                }
                print(json.dumps(result, indent=2))
        return

    if args[0] == "ring":
        doorbell_peer = 0
        if "--doorbell" in args:
            di = args.index("--doorbell")
            doorbell_peer = int(args[di + 1])
        devshm_path = "/dev/shm/ivshmem_bar0"
        with IvshmemClient(device_path=devshm_path) as client:
            ring = IvshmemRing(client, peer_id=doorbell_peer)
            seq = ring.ring(slot=0)
            print(json.dumps({"peer_id": doorbell_peer, "sequence": seq}, indent=2))
        return

    if args[0] == "receipt":
        if len(args) < 2:
            print("Usage: ivshmem_client.py receipt <result.json>", file=sys.stderr)
            sys.exit(1)
        data = json.loads(Path(args[1]).read_text())
        print(json.dumps(data, indent=2))
        return

    print("Usage: ivshmem_client.py <command> [args]", file=sys.stderr)
    print("Commands: --example, --test-devshm, --analyze, write, read, ring, receipt", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
