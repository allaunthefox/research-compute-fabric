import mmap
import os
import struct
import numpy as np

SHM_PATH = "/dev/shm/sovereign_signal_buffer"
SHM_SIZE = 1024 * 1024  # 1MB buffer
RAW_DATA_OFFSET = 128 * 1024
TELEMETRY_TAIL_SIZE = 1024

class SovereignSHMBridge:
    """
    Python interface for the PCIe-simulated Shared Memory bridge.
    Used to transfer raw data to the Rust/WGPU engine for E/B mode gating.
    """
    def __init__(self, path=SHM_PATH, size=SHM_SIZE):
        self.path = path
        self.size = size
        self._ensure_shm_exists()
        
    def _ensure_shm_exists(self):
        """Creates the shared memory file if it doesn't exist."""
        if not os.path.exists(self.path):
            with open(self.path, "wb") as f:
                f.write(b'\x00' * self.size)

    def write_dataset_chunk(self, data: bytes):
        """Write a raw text/byte chunk to the start of the buffer."""
        length = min(len(data), self.size - 8)
        with open(self.path, "r+b") as f:
            mm = mmap.mmap(f.fileno(), self.size)
            # Prefix with 4-byte length header
            mm[0:4] = struct.pack("<I", length)
            mm[4:4+length] = data
            mm.close()

    def read_signal_map(self) -> np.ndarray:
        """
        Read the E-mode (Convergence) map processed by the Rust engine.
        Assumes the map starts after the raw data offset.
        """
        # Schema: [4B Length][Offset=128KB][E-Mode Map (float32)]
        with open(self.path, "r+b") as f:
            mm = mmap.mmap(f.fileno(), self.size)
            # Read after raw data offset
            map_data = mm[RAW_DATA_OFFSET:self.size - TELEMETRY_TAIL_SIZE]
            signal_map = np.frombuffer(map_data, dtype=np.float32)
            mm.close()
            return signal_map

    def get_telemetry_tail(self) -> bytes:
        """Read the 1KB telemetry tail from the end of the buffer."""
        with open(self.path, "r+b") as f:
            mm = mmap.mmap(f.fileno(), self.size)
            tail = mm[self.size - TELEMETRY_TAIL_SIZE:self.size]
            mm.close()
            return tail
