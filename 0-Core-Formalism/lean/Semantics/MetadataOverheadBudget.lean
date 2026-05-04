/-!
# Metadata Overhead Budget for 1,250× Neural Compression

**Context:** From MinimumNeuralCompression.lean:
- Uncompressed: 1,000,000 GB (1 PB)
- Target compressed: 800 GB
- Required ratio: 1,250×

**Question:** What does 1,250× imply for per-value metadata overhead
in formats like Python objects, JSON, HDF5, or protobuf?

This file is standalone: zero imports.
-/

def uncompressedBytes : Nat := 1000000000000000  -- 1 PB = 10¹⁵ bytes

def compressedBytes : Nat := 800000000000        -- 800 GB = 8×10¹¹ bytes

def requiredRatio : Nat := uncompressedBytes / compressedBytes

-- ═══════════════════════════════════════════════════════════════════════════
-- §1  Bytes Per Original Byte (The Brutal Ceiling)
-- ═══════════════════════════════════════════════════════════════════════════

def compressedBytesPerOriginalMegabyte : Nat :=
  compressedBytes / (uncompressedBytes / 1000000)

-- A single original megabyte must compress to, on average, 800 bytes.
-- That is: 1 MB → ~0.8 KB in the compressed representation.

-- ═══════════════════════════════════════════════════════════════════════════
-- §2  Python Object Overhead (The Budget Violation)
-- ═══════════════════════════════════════════════════════════════════════════

def pythonFloatRaw : Nat := 8          -- C double (IEEE 754)
def pythonObjectHeader : Nat := 16     -- PyObject_HEAD (ob_refcnt + ob_type)
def pythonFloatOverhead : Nat := 24    -- PyFloatObject total size

def pythonDictEntryOverhead : Nat := 72  -- key string + hash + value ptr + probe
-- Conservative estimate: 72 bytes per key-value pair in a CPython dict

def pythonTotalPerValue : Nat := pythonFloatOverhead + pythonDictEntryOverhead

-- Python overhead ratio: what multiplier does Python add per scalar?
def pythonOverheadRatio : Nat :=
  (pythonTotalPerValue * 1000) / pythonFloatRaw

-- ═══════════════════════════════════════════════════════════════════════════
-- §3  JSON Overhead
-- ═══════════════════════════════════════════════════════════════════════════

def jsonFloatCharacters : Nat := 8     -- e.g., "0.123456" (avg for float)
def jsonKeyOverhead : Nat := 20       -- "\"voltage\": " (key + quotes + colon + space)
def jsonDelimiter : Nat := 2          -- comma + space or bracket

def jsonTotalPerValue : Nat := jsonKeyOverhead + jsonFloatCharacters + jsonDelimiter

def jsonOverheadRatio : Nat :=
  (jsonTotalPerValue * 1000) / pythonFloatRaw

-- ═══════════════════════════════════════════════════════════════════════════
-- §4  Flat Binary (Zero Metadata Per Value)
-- ═══════════════════════════════════════════════════════════════════════════

def flatBinaryPerValue : Nat := pythonFloatRaw

def flatBinaryOverheadRatio : Nat :=
  (flatBinaryPerValue * 1000) / pythonFloatRaw

-- ═══════════════════════════════════════════════════════════════════════════
-- §5  Amortized Metadata (Block Header, No Per-Value Cost)
-- ═══════════════════════════════════════════════════════════════════════════

def blockSizeValues : Nat := 1000000   -- 1M values per block
def blockHeaderBytes : Nat := 64       -- shape, dtype, checksum, timestamp

def amortizedMetadataPerValue : Nat :=
  (blockHeaderBytes * 1000) / blockSizeValues  -- scaled

def amortizedOverheadRatio : Nat :=
  ((flatBinaryPerValue * 1000) + amortizedMetadataPerValue) / pythonFloatRaw

-- ═══════════════════════════════════════════════════════════════════════════
-- §6  Verification
-- ═══════════════════════════════════════════════════════════════════════════

#eval requiredRatio              -- 1250
#eval compressedBytesPerOriginalMegabyte  -- 800 (800 bytes compressed per 1 MB original)
#eval pythonTotalPerValue         -- 96
#eval pythonOverheadRatio         -- 12000 (12,000× overhead per float)
#eval jsonTotalPerValue           -- 30
#eval jsonOverheadRatio           -- 3750 (3.75× overhead per float)
#eval flatBinaryOverheadRatio     -- 1000 (1.0×, zero overhead)
#eval amortizedMetadataPerValue   -- 0  (64 / 1M ≈ 0, integer division)
#eval amortizedOverheadRatio      -- 1000
