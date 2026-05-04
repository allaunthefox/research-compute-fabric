# Compression Benchmark Plan

**Purpose:** Require empirical comparisons between compression methods

**Status:** Draft for Review  
**Date:** 2026-04-29

---

## Benchmark Requirements

### 1. Baseline Comparisons

**Required Baselines:**
- **zstd:** Industry-standard lossless compression
- **ndzip:** Domain-specific compression (if applicable)
- **Delta GCL:** Our custom compression
- **gzip/zlib:** Legacy compression for reference

**Metric Requirements:**
- Original size (bytes)
- Compressed size (bytes)
- Compression ratio (original/compressed)
- Compression time (seconds)
- Decompression time (seconds)
- Memory usage (MB)

### 2. Corpus Requirements

**Test Corpora:**
- **Toy lattice data:** Small SU(2)/SU(3) lattice configurations (L = 4-16)
- **Metadata:** Similar to Lean metadata (for comparison with existing achievements)
- **Structured data:** Swarm component metadata (for comparison with existing achievements)
- **Field data:** Actual gauge field configurations (for realistic assessment)

**Corpus Provenance:**
- Document source of each test corpus
- Document generation method (if synthetic)
- Document size and characteristics

### 3. Experimental Protocol

**Compression Test:**
1. Load original data
2. Measure original size
3. Compress with each method
4. Measure compressed size, time, memory
5. Decompress with each method
6. Verify exact reconstruction (for lossless)
7. Measure decompression time, memory

**Statistical Requirements:**
- Minimum 10 runs per method
- Report mean ± standard deviation
- Use SI standard compression ratio (original/compressed)

### 4. Acceptance Criteria

**Delta GCL Requirements:**
- Must outperform zstd on metadata by ≥ 10%
- Must outperform gzip on structured data by ≥ 20%
- Must achieve ≥ 2× compression on field data (conservative)
- Must have reasonable compression time (< 2× baseline)

**Claims Without Benchmarks:**
- 60-135× compression on field data: **REQUIRES BENCHMARK**
- 99.9% compression on field data: **REQUIRES BENCHMARK**
- "Massive" compression without comparison: **REQUIRES BENCHMARK**

### 5. Reporting Format

**Required Fields:**
```
Method: <name>
Corpus: <name>
Original Size: <bytes>
Compressed Size: <bytes>
Compression Ratio: <ratio>
Compression Time: <seconds>
Decompression Time: <seconds>
Memory Usage: <MB>
```

**Comparison Table:**
| Method | Corpus | Original | Compressed | Ratio | Time | Memory |
|--------|--------|----------|------------|-------|------|--------|
| zstd | toy lattice | 1MB | 800KB | 1.25× | 0.1s | 10MB |
| Delta GCL | toy lattice | 1MB | 500KB | 2.0× | 0.2s | 15MB |

---

## Implementation Plan

**Phase 1: Corpus Generation (1-2 weeks)**
- Generate toy lattice data (L = 4-16)
- Collect metadata samples
- Collect structured data samples

**Phase 2: Baseline Implementation (1 week)**
- Implement zstd compression
- Implement gzip compression
- Implement ndzip (if applicable)

**Phase 3: Delta GCL Integration (1 week)**
- Integrate Delta GCL with benchmark framework
- Ensure fair comparison

**Phase 4: Benchmark Execution (1 week)**
- Run all benchmarks
- Collect metrics
- Generate comparison tables

**Phase 5: Analysis (1 week)**
- Analyze results
- Document findings
- Update claims based on evidence

---

## Success Criteria

**Benchmark Success:**
- All baselines implemented and tested
- Delta GCL compared against industry standards
- Claims backed by empirical evidence
- SI standard compression ratios used

**Failure Criteria:**
- Claims made without benchmarks
- Only metadata used as evidence
- No comparison to industry standards
- Non-SI compression ratios reported
