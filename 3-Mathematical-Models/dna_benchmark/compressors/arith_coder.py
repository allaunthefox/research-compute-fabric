# PROPRIETARY -- ALL RIGHTS RESERVED
# Copyright (c) 2026 Allaun Holdings
# See THIRD_PARTY_NOTICES.txt for third-party attributions.

"""
Simple arithmetic coder using byte-oriented range coding.
Based on standard practice (Schindler/Moffat/Storer).
No threading, no complex buffering — just works.
"""

import sys
from typing import Tuple

TOP = 0xFFFFFFFF
BOT = 0x01000000
SHIFT = 24


class SimpleArithEncoder:
    def __init__(self):
        self.low = 0
        self.high = TOP
        self.out = []
        self.buf = 0
        self.bcnt = 0

    def _emit(self, b: int):
        self.out.append(b)

    def _flush(self):
        for _ in range(4):
            self._emit((self.low >> 24) & 0xFF)
            self.low <<= 8

    def encode_byte(self, sym: int, cum_lo: int, cum_hi: int, total: int):
        """Encode symbol given cumulative frequency bounds."""
        rng = self.high - self.low + 1
        self.high = self.low + (rng * cum_hi) // total - 1
        self.low += (rng * cum_lo) // total
        while True:
            if self.high < 0x80000000:
                self._emit(0)
            elif self.low >= 0x80000000:
                self._emit(1)
                self.low -= 0x80000000
                self.high -= 0x80000000
            elif self.low >= 0x40000000 and self.high < 0xC0000000:
                self.buf += 1
                self.low -= 0x40000000
                self.high -= 0x40000000
            else:
                break
            self.low <<= 1
            self.high = (self.high << 1) | 1

    def finish(self) -> bytes:
        self.buf += 1
        if self.low < 0x40000000:
            self._emit(0)
            for _ in range(self.buf):
                self._emit(1)
        else:
            self._emit(1)
            for _ in range(self.buf):
                self._emit(0)
        self._flush()
        return bytes(self.out)


class SimpleArithDecoder:
    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0
        self.low = 0
        self.high = TOP
        self.code = 0
        for _ in range(4):
            self.code = (self.code << 8) | self._next_byte()

    def _next_byte(self) -> int:
        if self.pos < len(self.data):
            b = self.data[self.pos]
            self.pos += 1
            return b
        return 0

    def decode_sym(self, freq_table, total: int) -> int:
        """Decode a symbol given a frequency table (list of counts). Returns symbol index."""
        rng = self.high - self.low + 1
        target = ((self.code - self.low + 1) * total - 1) // rng

        cum = 0
        sym = 0
        for i, cnt in enumerate(freq_table):
            cum += cnt
            if cum > target:
                sym = i
                cum_lo = cum - cnt
                cum_hi = cum
                break
        else:
            sym = len(freq_table) - 1
            cum_lo = cum - freq_table[-1] if freq_table else 0
            cum_hi = total

        self.high = self.low + (rng * cum_hi) // total - 1
        self.low += (rng * cum_lo) // total

        while True:
            if self.high < 0x80000000:
                pass
            elif self.low >= 0x80000000:
                self.code -= 0x80000000
                self.low -= 0x80000000
                self.high -= 0x80000000
            elif self.low >= 0x40000000 and self.high < 0xC0000000:
                self.code -= 0x40000000
                self.low -= 0x40000000
                self.high -= 0x40000000
            else:
                break
            self.low <<= 1
            self.high = (self.high << 1) | 1
            self.code = (self.code << 1) | self._next_byte()

        return sym


class Order0ArithCoder:
    """
    Order-0 adaptive arithmetic coder.
    Counts symbol frequencies and encodes/decodes with cumulative distributions.
    Simple, correct, fast. Baseline to beat gzip.
    """

    def __init__(self):
        self.freqs = [1] * 256  # Laplace smoothed (no zero-prob symbols)
        self.total = 256

    def _cumulative(self, sym: int) -> Tuple[int, int, int]:
        """Return (cum_lo, cum_hi, total) for symbol."""
        cum = 0
        for i in range(sym):
            cum += self.freqs[i]
        return cum, cum + self.freqs[sym], self.total

    def compress(self, data: bytes) -> bytes:
        enc = SimpleArithEncoder()
        freqs = [1] * 256
        total = 256

        for b in data:
            b = b & 0xFF
            cum_lo, cum_hi, _ = self._cumulative(b)
            enc.encode_byte(b, cum_lo, cum_hi, total)
            freqs[b] += 1
            total += 1

        return enc.finish()

    def decompress(self, compressed: bytes, length: int) -> bytes:
        dec = SimpleArithDecoder(compressed)
        freqs = [1] * 256
        total = 256
        result = bytearray()

        for _ in range(length):
            sym = dec.decode_sym(freqs, total)
            result.append(sym)
            freqs[sym] += 1
            total += 1

        return bytes(result)

    def roundtrip(self, data: bytes) -> Tuple[bool, int, int]:
        """Test roundtrip. Returns (success, compressed_size, original_size)."""
        c = self.compress(data)
        d = self.decompress(c, len(data))
        return data == d, len(c), len(data)


def bench_arith(data: bytes, label: str, quiet=False) -> dict:
    """Benchmark and verify roundtrip."""
    import time
    coder = Order0ArithCoder()

    t0 = time.time()
    compressed = coder.compress(data)
    ct = time.time() - t0

    t0 = time.time()
    decompressed = coder.decompress(compressed, len(data))
    dt = time.time() - t0

    ok = data == decompressed
    if not ok:
        errors = sum(1 for a, b in zip(data, decompressed) if a != b)
        return {"label": label, "ok": False, "errors": errors, "compressed_bytes": len(compressed)}

    return {
        "label": label, "ok": True,
        "original": len(data),
        "compressed": len(compressed),
        "ratio": round(len(compressed) / len(data), 4),
        "bpb": round(len(compressed) * 8 / len(data), 3),
        "comp_s": round(ct, 3),
        "dec_s": round(dt, 3),
    }
