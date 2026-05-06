# Hutter Prize Submission Strategy for PIST Extended Encoding

## Exact Corpus Identity

**enwik9** = first 10⁹ bytes of `enwiki-20060303-pages-articles.xml`

This is a fixed historical XML dump. It is not "any Wikipedia dump" — it is exactly this 2006 snapshot. The first gigabyte includes:
- XML markup (`<page>`, `<revision>`, `<text>`, etc.)
- English Wikipedia article templates
- Cross-references, infoboxes, tables
- Multi-language section headers
- MediaWiki syntax (`[[link]]`, `{{template}}`, `'''bold'''`, etc.)

Source: http://mattmahoney.net/dc/textdata.html

## Current Record

| Metric | Value |
|--------|-------|
| **Record holder** | fx2-cmix (Kaido Orav and Byron Knoll, 2024) |
| **Current record L** | 110,793,128 bytes (~105.6 MiB) |
| **Prize-eligible target** | S ≤ floor(0.99 × L) = **109,685,196 bytes** |
| **Any record target** | S < 110,793,128 bytes |
| **Prize fund Z** | 500,000€ (not depleted after awards) |
| **Prize formula** | **Award = 500,000€ × (1 − S/L)** = 500,000€ × (L − S) / L |
| **Minimum payout** | 5,000€ (at exactly 1% improvement) |
| **enwik9 uncompressed** | 1,000,000,000 bytes |
| **Current compression ratio** | 11.08% |

### Prize Scenarios (Corrected)

| Improvement (L−S)/L | S (bytes) | Prize (€) |
|----------------------|-----------|-----------|
| 1% (minimum) | 109,685,196 | 5,000 |
| 2% | 108,577,266 | 10,000 |
| 5% | 105,253,472 | 25,000 |
| 10% | 99,713,815 | 50,000 |

The formula is **linear in improvement**, not exponential. A 2% improvement pays ~2× the 1% prize.

## Scoring Formula: S = S1 + S2

The official rule counts **both** the compressor and the archive:

- **S1** = size of `comp9.exe` (or zipped source) — the compressor
- **S2** = size of `archive9.exe` — the self-extracting archive (decompressor + compressed data)
- **S = S1 + S2** must be < L

**Important nuance**: The compressor may be counted as a zipped package, not just raw executable size. The exact packaging rule depends on submission format.

### Size Budget (1% Prize)

| Component | Typical Size | Notes |
|-----------|-------------|-------|
| Decompressor binary | ~10-20KB | C code compiled with `-O3 -s` |
| Compressed data | ~109,650KB | The program stream + residuals |
| **S2 (archive9.exe)** | **~109,665KB** | Binary + embedded data |
| Compressor (S1) | Variable | Counted as submitted (executable or zip) |
| **Total S target** | **< 109,685,196 bytes** | **Very tight margin** |

**This means S2 alone must be < 109.7MB. The decompressor gets ~20KB of headroom.**

The current PAQ record compresses to ~110.8MB total. To win even 1%, PIST must beat PAQ by ~1.1MB. This requires PAQ-level or better compression.

## Hardware and Resource Constraints

Both **compression** and **decompression** are constrained:

| Resource | Limit | Notes |
|----------|-------|-------|
| CPU | 1 single core | No multi-threading, no SIMD reliance |
| GPU | 0 | No GPU acceleration |
| RAM | < 10GB | For both comp9 and archive9 |
| Temporary disk | < 100GB | HDD scratch space |
| Runtime | < 70,000 / T hours | T = test machine Geekbench 5 score |
| Practical runtime | ≲ 50 hours | Approximation; depends on T |

The test machine is specified at: http://browser.primatelabs.com/v4/cpu/145066

## Critical Blockers for PIST

### 1. Python Is Disqualified

| Problem | Why | Fix |
|---------|-----|-----|
| External dependency | Python interpreter not guaranteed on test machine | Rewrite decoder in C |
| Slow execution | Python ~100× slower than C for 1GB stream | C with `-O3` |
| Large footprint | Python + script >> 1MB | Static C binary ~10-20KB |

**Status**: `hutter_pist_decoder.c` skeleton created. Needs completion and testing.

### 2. Single-Core Deterministic Arithmetic

| Implication | Impact on PIST |
|-------------|---------------|
| No parallel basis search | Fine — PIST coordinates are O(1) arithmetic, no search |
| No SIMD | Fine — scalar `n = k² + t` is already fast |
| No GPU matrix ops | Fine — no neural networks in decoder |

**Advantage**: PIST decoder is pure register-machine arithmetic. It is naturally single-core optimal.

### 3. RAM Budget

| Operation | RAM | Safe? |
|-----------|-----|-------|
| Streaming decode (byte-at-a-time) | ~1KB | Yes |
| Bootstrap basis + stack | ~512B | Yes |
| Loading enwik9 (compressor only) | 1GB | Yes (9GB headroom) |
| Context mixing tables | ~2-4MB | Yes |
| Neural model weights | >1GB | No — do not use |

### 4. Runtime Budget

| Phase | Target | PIST Estimate |
|-------|--------|---------------|
| Decompression (archive9.exe) | < ~50h | ~2-4 hours for 1GB at 1μs/byte |
| Compression (comp9.exe) | < ~50h | Compressor can be slower; only runs once |
| Verification (committee) | Must pass | Deterministic output, easy to verify |

**Advantage**: PIST decompression is O(N) with ~20 arithmetic ops per byte. At 100ns/byte on a 3GHz core, 1GB = 100 seconds. Even at 1μs/byte = ~16 minutes.

## Model / Dictionary / LUT Accounting Rule

**Every piece of knowledge required for decompression must be counted in S.**

This explicitly includes:
- Grammar tables, semantic maps, tokenizers
- Mass-number fields, LUTs, transform recipes
- Article reorder lists, decoder-side priors
- Any pre-trained model weights
- Bootstrap basis vectors

**Implication for PIST**: The 16-byte bootstrap basis is tiny and easily counted. Any larger grammar or semantic table must either:
1. Be included in `archive9.exe` (counts in S2), or
2. Be reconstructed by the compressor and not needed by the decoder

The PIST architecture is well-suited to this: the decoder computes coordinates from `n` alone. No external tables needed. The bootstrap basis is the only decoder-side state.

## Self-Contained Binary Requirement

`archive9.exe` must:
- Be a single executable file (Windows or Linux x86, 32/64-bit)
- Run with **zero external inputs** — no network, no files, no DLLs, no environment variables
- Output exactly the 10⁹-byte enwik9 file, byte-for-byte
- Contain all compressed data embedded within itself

**Implementation**: Append compressed data after the compiled binary. The binary reads itself to locate the data offset (marked with a magic sequence).

## Path to Submission

### Phase 1: Minimal Viable C Decoder (Week 1-2)

Goal: `archive9.exe` compiles, runs, and outputs exactly 1GB on test data.

- [ ] Fix `hutter_pist_decoder.c` EMIT logic (currently placeholder)
- [ ] Implement proper instruction semantics (LOAD, XOR, FUSE, HALT)
- [ ] Add magic marker for self-reading data offset
- [ ] Test roundtrip on 1KB, 1MB synthetic data
- [ ] Optimize: `gcc -O3 -s -fno-stack-protector -fomit-frame-pointer`
- [ ] Verify binary size < 20KB

### Phase 2: Compressor Search Prototype (Week 3-6)

Goal: A Python script `comp9.py` that finds a program stream P where `decode(P) = enwik9`.

- [ ] Bootstrap basis optimization (find 16 bytes that minimize residuals)
- [ ] Instruction sequence search (simulated annealing / genetic algorithm)
- [ ] Residual encoding (arithmetic coding of prediction errors)
- [ ] Test on enwik8 (100MB) first — do not touch enwik9 until this works

### Phase 3: Enwik9-Specific Tuning (Week 7-10)

enwik9 is a 2006 Wikipedia XML dump with predictable structure:

- [ ] XML tag template detection (`<page>`, `<revision>`, `<text>`)
- [ ] MediaWiki syntax patterns (`[[`, `{{`, `'''`, `==`)
- [ ] Cross-reference link structure
- [ ] Infobox and table templates
- [ ] English n-gram frequency modeling

### Phase 4: Submission Verification (Week 11-12)

- [ ] Document all source code (required before payout)
- [ ] Choose OSI-approved license (e.g., GPL-3.0, MIT, Apache-2.0)
- [ ] Verify losslessness: `./archive9.exe | cmp - enwik9`
- [ ] Measure exact sizes: `wc -c comp9.zip archive9.exe`
- [ ] Profile peak RAM and temp disk usage
- [ ] Record wall-clock and CPU time on reference hardware
- [ ] Submit to Hutter Prize forum (30-day public comment period)
- [ ] If multiple authors: agree on prize split in writing

## Reproducibility Checklist

A submission must include all of the following:

1. **Exact source revision / git tag**
2. **Build instructions** — exact compiler flags and commands
3. **OSI-approved license** declared in repository
4. **Exact command to build and run comp9**
5. **Exact output filename** produced by archive9
6. **SHA-256 or bytewise verification** procedure against enwik9
7. **Peak RAM measurement** during both compression and decompression
8. **Peak temp disk measurement**
9. **Single-core enforcement notes** — how the code avoids multi-threading
10. **Wall-clock and CPU-time logs**
11. **Attestation**: no network, no external dictionary, no hidden files, no environment variables, no runtime downloads
12. **Contributor payout agreement** (if multiple authors)

## Size Budget (Detailed)

Target for 1% prize: **S < 109,685,196 bytes**

| Line Item | Bytes | Notes |
|-----------|-------|-------|
| C decoder binary | 12,000-18,000 | Stripped, optimized |
| Bootstrap basis | 16 | Embedded in binary |
| Magic marker + metadata | ~100 | Offset marker, version |
| Compressed program stream | ~109,660,000 | The actual data |
| **archive9.exe (S2)** | **~109,678,000** | |
| comp9 source zip (S1) | ~500,000 | Compressor + docs |
| **Total S** | **~110,178,000** | **Still above L — needs better compression** |

The margin is razor-thin. To win 1%, the compressed data must be ~1.1MB smaller than PAQ's. This requires either:
- Better prediction (lower entropy = shorter arithmetic-coded stream)
- Smaller decompressor (but C is already near minimum)
- Or both

## What PAQ/cmix Does That PIST Currently Lacks

| Feature | PAQ/cmix | PIST Status | Gap |
|---------|----------|-------------|-----|
| Context mixing (multiple models, weighted) | Yes | No | **High** |
| Adaptive weight learning (online gradient descent) | Yes | No | **High** |
| Bit-level arithmetic coding | Yes | Byte-level | Medium |
| Long-range string matching (LZP) | Yes | No | **High** |
| Pre-trained neural network (cmix) | Yes (LSTM) | No | **High** |
| enwik9-specific model tuning | Yes (years) | No | **High** |

## Realistic Assessment

| Milestone | Probability | Effort |
|-----------|-------------|--------|
| Functional C decoder | 95% | 2 weeks |
| Beats gzip (~270MB total) | 80% | 4 weeks |
| Beats bzip2 (~200MB total) | 60% | 8 weeks |
| Beats LZMA (~140MB total) | 30% | 16 weeks |
| Beats PAQ record (110.8MB) | 5% | 6+ months |
| Wins Hutter Prize 1% | 2% | 1+ year |

The Hutter Prize represents the state of the art in text compression. PAQ and cmix are the product of decades of research by multiple contributors. PIST is a novel architecture but is **not yet competitive** without:
1. Context mixing (multiple prediction models)
2. Adaptive weight learning
3. Bit-level arithmetic coding
4. Long-range pattern matching
5. Extensive enwik9-specific tuning

## Recommended Intermediate Goal

**Do not target enwik9 directly.**

Target the **Large Text Compression Benchmark** enwik8 (100MB) first:
- http://mattmahoney.net/dc/text.html
- Public leaderboard
- Faster iteration
- Proves architecture before scaling

A reasonable intermediate milestone: **beat bzip2 on enwik8**. This validates the approach without requiring PAQ-level sophistication.

## Immediate Action Items

1. [ ] Fix `hutter_pist_decoder.c` — complete EMIT, test roundtrip on small data
2. [ ] Write `comp9.py` — Python compressor prototype
3. [ ] Test on enwik8 first (download from Matt Mahoney's site)
4. [ ] Measure compression ratio vs gzip/bzip2/lzma baseline
5. [ ] If results are promising, add context mixing to decoder
6. [ ] Port compressor to C only if Python prototype shows competitive ratios
