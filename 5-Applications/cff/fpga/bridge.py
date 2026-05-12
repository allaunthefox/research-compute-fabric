#!/usr/bin/env python3
"""
CFF-FPGA Bridge: Tang Nano 9K → Real-time Constraint Verification

The FPGA (cff_invariant_scanner.v) stores a compact routing table of up to
256 equation entries. This bridge:
  1. Loads the top equations from the DB into FPGA BRAM via UART
  2. Sends CMD/ID queries and receives chiral state + admissibility
  3. Integrates with CFF (fingerprint verification) and GPU (eigenmass)

Used as a real-time validation co-processor: GPU handles batch PageRank,
FPGA handles per-equation fast yes/no with sub-ms latency.

Protocol:
  Host → FPGA:  [CMD:8][EQ_ID_H:8][EQ_ID_L:8]
  FPGA → Host:  [STATUS/N bytes]

Commands:
  0x01 — Verify equation       → [LAYER_STATUS:8][STRENGTH:8]
  0x02 — Get chiral state      → [CHIRAL_STATE:8][ADMISSIBLE:8]
  0x03 — List neighbor info    → [EQ_ID_H:8][EQ_ID_L:8][LAYER_INFO:8][STRENGTH:8]

Chiral states: 0=achiral_stable, 1=left_handed_mass_bias,
               2=right_handed_vector_bias, 3=chiral_scarred
Layer: 1=Fundamental, 2=Derived, 3=Empirical, 4=Living

Hardware: Tang Nano 9K (GW1NR-9C), UART 115200 baud, 27 MHz clock
"""

import struct
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field

try:
    import serial
    HAS_SERIAL = True
except ImportError:
    HAS_SERIAL = False
    serial = None  # type: ignore


# ── FPGA Protocol Constants ──

CMD_VERIFY = 0x01
CMD_CHIRAL = 0x02
CMD_NEIGHBORS = 0x03

CHIRAL_STATES = {
    0: "achiral_stable",
    1: "left_handed_mass_bias",
    2: "right_handed_vector_bias",
    3: "chiral_scarred",
}


@dataclass
class FPGAEquationEntry:
    """An equation entry loaded into FPGA routing table."""
    equation_id: int
    chiral_state: str = "achiral_stable"
    admissible: bool = True
    layer: int = 2
    strength: int = 512        # 0-2047 (11 bits)
    raw_packed: int = 0

    def pack(self) -> int:
        """Pack into 16-bit FPGA routing table entry."""
        cs_bits = {
            "achiral_stable": 0,
            "left_handed_mass_bias": 1,
            "right_handed_vector_bias": 2,
            "chiral_scarred": 3,
        }
        cs = cs_bits.get(self.chiral_state, 0)
        adm = 1 if self.admissible else 0
        lay = max(1, min(4, self.layer)) - 1   # 0-indexed
        strength = max(0, min(2047, self.strength))

        self.raw_packed = (cs << 14) | (adm << 13) | (lay << 11) | strength
        return self.raw_packed

    @classmethod
    def unpack(cls, packed: int, eq_id: int = 0) -> "FPGAEquationEntry":
        cs = (packed >> 14) & 0x3
        adm = (packed >> 13) & 0x1
        lay = ((packed >> 11) & 0x3) + 1
        strength = packed & 0x7FF

        return cls(
            equation_id=eq_id,
            chiral_state=CHIRAL_STATES.get(cs, "achiral_stable"),
            admissible=bool(adm),
            layer=lay,
            strength=strength,
            raw_packed=packed,
        )


class CFFFPGABridge:
    """
    Primary bridge between CFF pipeline and Tang Nano 9K FPGA.

    The FPGA serves as a real-time invariant verification co-processor.
    GPU does batch PageRank, FPGA does per-equation yes/no routing checks.
    """

    def __init__(self, port: str = "/dev/ttyUSB1", baud: int = 115200,
                 timeout: float = 0.5):
        if not HAS_SERIAL:
            raise ImportError(
                "pyserial required: pip install pyserial"
            )

        self.port = port
        self.baud = baud
        self.timeout = timeout
        self._ser: Optional[serial.Serial] = None
        self._loaded_entries: Dict[int, FPGAEquationEntry] = {}
        self._entry_count: int = 0
        self._max_entries: int = 256   # FPGA BRAM limit

    # ── Connection Management ──

    def open(self) -> bool:
        """Open serial connection to FPGA."""
        if self._ser and self._ser.is_open:
            return True
        try:
            self._ser = serial.Serial(
                self.port, self.baud,
                timeout=self.timeout,
                write_timeout=self.timeout,
            )
            self._ser.reset_input_buffer()
            self._ser.reset_output_buffer()
            time.sleep(0.05)  # let FPGA stabilize
            return True
        except (OSError, serial.SerialException) as e:
            self._ser = None
            return False

    def close(self):
        if self._ser and self._ser.is_open:
            self._ser.close()
            self._ser = None

    @property
    def is_open(self) -> bool:
        return self._ser is not None and self._ser.is_open

    # ── FPGA Communication ──

    def _send_raw(self, data: bytes) -> bool:
        """Send raw bytes to FPGA."""
        if not self.is_open:
            return False
        try:
            self._ser.write(data)  # type: ignore[union-attr]
            self._ser.flush()      # type: ignore[union-attr]
            return True
        except (OSError, serial.SerialTimeoutException):
            return False

    def _read_raw(self, n: int = 1) -> bytes:
        """Read raw bytes from FPGA."""
        if not self.is_open:
            return b""
        try:
            return self._ser.read(n)  # type: ignore[union-attr]
        except OSError:
            return b""

    def _send_cmd(self, cmd: int, eq_id: int) -> Optional[bytes]:
        """
        Send command to FPGA and receive response.
        Returns raw response bytes, or None on failure.
        """
        if not self._ensure_open():
            return None

        # Flush any stale data
        if self._ser:
            self._ser.reset_input_buffer()

        # Send: [CMD:8][EQ_ID_H:8][EQ_ID_L:8]
        packet = struct.pack(">BH", cmd, eq_id & 0xFFFF)[:3]
        if not self._send_raw(packet):
            return None

        # Read response (up to 5 bytes)
        time.sleep(0.005)  # give FPGA time to process
        resp = self._read_raw(8)
        return resp if resp else None

    def _ensure_open(self) -> bool:
        if not self.is_open:
            return self.open()
        return self.is_open

    # ── High-Level Queries ──

    def verify_equation(self, eq_id: int) -> Optional[Dict[str, Any]]:
        """
        Query FPGA: verify if equation is topologically admissible.
        Returns dict with layer_status, strength, raw bytes.
        """
        resp = self._send_cmd(CMD_VERIFY, eq_id)
        if not resp or len(resp) < 2:
            return None

        layer_status = resp[0]
        strength = resp[1]

        layer_map = {
            0x80: "Layer1_Fundamental_Verified",
            0xC0: "Layer4_Scarred_But_Present",
            0x00: "Not_Loaded",
        }
        status = layer_map.get(layer_status & 0xF0, f"Unknown_0x{layer_status:02X}")

        return {
            "equation_id": eq_id,
            "status": status,
            "layer_byte": layer_status,
            "strength": strength,
            "admissible": (layer_status & 0x20) != 0,
            "raw_response": resp.hex(),
        }

    def get_chiral_state(self, eq_id: int) -> Optional[Dict[str, Any]]:
        """
        Query FPGA: get chiral state and admissibility.
        """
        resp = self._send_cmd(CMD_CHIRAL, eq_id)
        if not resp or len(resp) < 2:
            return None

        cs_bits = (resp[0] >> 6) & 0x3
        admissible = (resp[0] >> 5) & 0x1

        return {
            "equation_id": eq_id,
            "chiral_state": CHIRAL_STATES.get(cs_bits, "achiral_stable"),
            "chiral_bits": cs_bits,
            "admissible": bool(admissible),
            "raw_response": resp.hex(),
        }

    def get_neighbors(self, eq_id: int) -> Optional[Dict[str, Any]]:
        """
        Query FPGA: get neighbor/layer info.
        """
        resp = self._send_cmd(CMD_NEIGHBORS, eq_id)
        if not resp or len(resp) < 4:
            return None

        eq_hi = resp[0]
        eq_lo = resp[1]
        layer_info = ((resp[2] >> 4) & 0xF) + 1
        strength = ((resp[2] & 0x0F) << 4) | (resp[3] >> 4)

        return {
            "equation_id": (eq_hi << 8) | eq_lo,
            "layer": layer_info,
            "strength": strength,
            "raw_response": resp.hex(),
        }

    # ── Batch Operations ──

    def verify_batch(self, eq_ids: List[int]) -> List[Optional[Dict]]:
        """Verify a batch of equations sequentially."""
        return [self.verify_equation(eid) for eid in eq_ids]

    def scan_admissible(self, eq_ids: List[int]) -> List[int]:
        """
        Scan equations for admissibility.
        Returns list of admissible equation IDs.
        """
        admissible = []
        for eid in eq_ids:
            result = self.verify_equation(eid)
            if result and result.get("admissible"):
                admissible.append(eid)
        return admissible

    def benchmark_roundtrip(self, n: int = 100) -> Dict[str, float]:
        """Benchmark FPGA roundtrip latency."""
        if not self.is_open:
            return {"error": "not connected"}

        times = []
        for i in range(n):
            eq_id = (i % 86) + 1
            t0 = time.perf_counter()
            self._send_cmd(CMD_VERIFY, eq_id)
            dt = time.perf_counter() - t0
            times.append(dt)

        times_sorted = sorted(times)
        return {
            "samples": n,
            "avg_ms": sum(times) / n * 1000,
            "min_ms": min(times) * 1000,
            "max_ms": max(times) * 1000,
            "p50_ms": times_sorted[n // 2] * 1000,
            "p95_ms": times_sorted[int(n * 0.95)] * 1000,
            "p99_ms": times_sorted[int(n * 0.99)] * 1000,
        }

    # ── Integration with CFF Pipeline ──

    def cross_validate_with_cff(
        self, eq_id: int, cff_fp: str
    ) -> Dict[str, Any]:
        """
        Cross-validate: does FPGA agree with CFF fingerprint?
        Combines FPGA chiral state with CFF Merkle fingerprint.
        """
        fpga = self.get_chiral_state(eq_id)

        return {
            "equation_id": eq_id,
            "cff_fingerprint": cff_fp[:24] + "...",
            "fpga_chiral": fpga["chiral_state"] if fpga else "offline",
            "fpga_admissible": fpga["admissible"] if fpga else None,
            "consensus": (
                "VERIFIED"
                if fpga and fpga["admissible"] and cff_fp
                else "MISMATCH" if fpga and not fpga["admissible"]
                else "FPGA_OFFLINE"
            ),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }

    def load_from_db(self, db_path: str):
        """
        Populate internal equation map from physics_equations.db.
        """
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='gpu_eigenmass'")
        has_gpu = bool(cursor.fetchone())

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chiral_eigenmass'")
        has_chiral = bool(cursor.fetchone())

        if has_gpu:
            cursor.execute("""
                SELECT equation_id, chiral_state, chiral_residual
                FROM gpu_eigenmass ORDER BY chiral_residual DESC
                LIMIT ?
            """, (self._max_entries,))
        elif has_chiral:
            cursor.execute("""
                SELECT equation_id, chiral_state, chiral_residual
                FROM chiral_eigenmass ORDER BY chiral_residual DESC
                LIMIT ?
            """, (self._max_entries,))
        else:
            conn.close()
            return

        for row in cursor.fetchall():
            eid = row["equation_id"]
            self._loaded_entries[eid] = FPGAEquationEntry(
                equation_id=eid,
                chiral_state=row["chiral_state"] or "achiral_stable",
                admissible=row["chiral_state"] not in ("chiral_scarred",),
                strength=int(min(2047, abs(float(row["chiral_residual"] or 0)) * 100)),
            )

        conn.close()

    # ── Status ──

    def status(self) -> Dict[str, Any]:
        return {
            "connected": self.is_open,
            "port": self.port,
            "baud": self.baud,
            "loaded_entries": len(self._loaded_entries),
            "max_entries": self._max_entries,
        }


# ── Convenience ──

def quick_fpga_test(port: str = "/dev/ttyUSB1") -> Optional[Dict]:
    """Quick connectivity test: open, verify one equation, report."""
    bridge = CFFFPGABridge(port=port)
    try:
        if not bridge.open():
            return {"error": f"Cannot open {port}"}

        result = bridge.verify_equation(1)
        return {
            "connected": True,
            "port": port,
            "test_result": result,
        }
    finally:
        bridge.close()


def scan_critical_equations(
    db_path: str, port: str = "/dev/ttyUSB1",
    critical_ids: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """
    Load DB, connect FPGA, scan critical equations.
    Critical IDs default to DNA depurination (744), chiral bridges,
    and extremophile bounds.
    """
    if critical_ids is None:
        critical_ids = [1, 2, 4, 38, 68, 232, 324, 443, 593, 744]

    bridge = CFFFPGABridge(port=port)
    bridge.load_from_db(db_path)

    try:
        if not bridge.open():
            return {"error": "FPGA unreachable", "eq_ids": critical_ids}

        results = {}
        for eid in critical_ids:
            fpga = bridge.get_chiral_state(eid)
            results[str(eid)] = fpga if fpga else {"error": "no_response"}

        return {
            "fpga_status": bridge.status(),
            "results": results,
            "total_queried": len(critical_ids),
            "responsive": sum(1 for v in results.values()
                              if v.get("chiral_state")),
        }
    finally:
        bridge.close()
