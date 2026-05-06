# Next Steps Plan — PIST Extended Encoding

## Completed This Session

### Track B: C Decoder — Steps 1-4 [DONE]
**Result**: Working self-contained binary, tested on synthetic data.

- [x] Fix EMIT logic in `hutter_pist_decoder.c` — replaced register machine with predict+residual model
- [x] Test roundtrip on 1KB, 1MB, 10MB synthetic data — **all pass**
- [x] Verify binary size: **16,864 bytes** (< 20KB target)
- [x] Speed: **0.84 MB/s** (~20 min for 1GB, well within 50h limit)

**Files created**:
- `5-Applications/scripts/hutter_pist_decoder.c` — C decoder
- `5-Applications/scripts/hutter_pist_decoder` — compiled binary
- `5-Applications/scripts/test_pist_decoder.py` — Python test harness

**Note**: Compression ratio is currently ~1.0x (no real compression) because prediction model is trivial. Real compression requires better prediction + arithmetic coding.

### Track A: Lean Proofs — Steps 1-3 [PENDING]
**Goal**: Prove the trivial invariants first.

1. [ ] Prove Theorem 1 (PIST Reconstruction): `(pistK n)² + (pistT n) = n`
2. [ ] Prove Theorem 5 (Address Reconstruction): `n = k² + t` from `(k, t)`
3. [ ] Prove Theorem 2 (Tree Determinism): `tree_address(n, d)` always same path

## Now: Multilingual Corpus Collection (Track D)

**Goal**: Test framework on non-English data to measure generalization.

### Why this matters

- enwik9 contains non-English sections (interwiki links, foreign names, multilingual headers)
- Basis selection may generalize poorly to non-Latin scripts
- PIST coordinates are script-agnostic (position-based), but basis vectors are frequency-based
- Testing on multilingual data reveals whether the architecture is truly substrate-independent
- More diverse training data → better basis vectors → better prediction → better compression

### Corpora to Acquire

| Corpus | Languages | Size | Source | Download Method |
|--------|-----------|------|--------|----------------|
| **Europarl** | 21 EU languages | ~2GB | https://www.statmt.org/europarl/ | wget + extract |
| **Wikipedia dumps** | 300+ languages | TB scale | https://dumps.wikimedia.org/ | `wget -r` or torrent |
| **Common Crawl** | 100+ languages | PB scale | https://commoncrawl.org/ | S3 / AWS |
| **Project Gutenberg** | 60+ languages | ~100GB | https://www.gutenberg.org/ | rsync / FTP |
| **UN Corpus** | 6 official languages | ~1GB | https://conferences.unite.un.org/UNCorpus | registration |
| **OPUS** | 100+ languages | TB scale | https://opus.nlpl.eu/ | wget per language |
| **Leipzig Corpora** | 250+ languages | ~50GB | https://wortschatz.uni-leipzig.de/en/download | per-language download |
| **OSCAR** | 150+ languages | TB scale | https://oscar-project.org/ | torrent / HuggingFace |
| **C4 (Multilingual)** | 101 languages | ~6TB | https://huggingface.co/datasets/allenai/c4 | HuggingFace datasets |
| **mC4** | 101 languages | ~6.3TB | https://huggingface.co/datasets/allenai/c4 | HuggingFace datasets |

### Immediate Download Commands

```bash
# Create corpus directory
mkdir -p "/home/allaun/Documents/Research Stack/data/corpora"
cd "/home/allaun/Documents/Research Stack/data/corpora"

# Europarl (parallel corpus, good for cross-lingual testing)
wget -r -np -nH --cut-dirs=2 -R "index.html*" \
  https://www.statmt.org/europarl/v7/

# Leipzig Corpora (news text, many languages)
# Example: German 2023
wget https://downloads.wortschatz-leipzig.de/corpus/deu_news_2023_1M.tar.gz

# OPUS (Open Parallel Corpus)
# Example: Wikipedia in Spanish
wget https://object.pouta.csc.fi/OPUS-wikipedia/v1.0/moses/es-en.txt.zip

# Project Gutenberg (multilingual)
rsync -av --progress ftp@ftp.ibiblio.org::gutenberg-epub \
  ./gutenberg/

# OSCAR (web-scale, via HuggingFace)
pip install datasets
python3 -c "from datasets import load_dataset; ds = load_dataset('oscar', 'unshuffled_deduplicated_en'); ds.save_to_disk('./oscar_en')"
```

### What to Measure

For each language corpus:
1. **Byte-frequency histogram** — are top-16 basis bytes language-specific?
2. **Prediction accuracy** — does the PIST prediction model match the data?
3. **Residual entropy** — how random are the residuals after prediction?
4. **Compression ratio** — how well does the framework compress vs gzip/lzma?
5. **Script independence** — do non-Latin scripts (Cyrillic, Arabic, CJK) behave differently?

### Why More Data Helps the Hutter Prize

enwik9 is English Wikipedia + XML markup. But it contains:
- Foreign article names
- Interwiki links (`[[de:Berlin]]`, `[[fr:Paris]]`)
- Multilingual disambiguation pages
- Unicode characters outside ASCII

If the basis is trained only on English, it misses patterns in these non-English sections. A multilingual basis captures more structure → better prediction → smaller residuals → better compression.

## Track E: Basin-Stability Certificate (NEW SEED)

**Goal**: Promote `mass number` from "semantic ratio" to "semantic ratio + admissible basin behavior + residual-risk witness."

**Seed doc**: [BASIN_STABILITY_CERTIFICATE.md](BASIN_STABILITY_CERTIFICATE.md)
**Template paper**: Linares & Cadenas, *Dynamics of the Modified Chebyshev's Method to Multiple Roots*, arXiv:2601.10751v1 (2026-01-19).

### Why this matters

The lawfulness filter currently certifies invariant survival at the bridge point. That is local. It cannot tell whether the operator about to act on a structure converges to a lawful attractor, a strange attractor, or fails to converge. Without that distinction, a mass number can pass local checks and still license a drifting compression regime.

### Steps

1. [ ] Pick one operator family already in the stack (candidate: an `AdaptiveBlock` update rule) and identify its canonical conjugate operator.
2. [ ] Enumerate its fixed points; mark lawful vs strange.
3. [ ] Define a finite set of critical probes (analogue of `C_1`, `C_2`, `C_3` in the Chebyshev paper).
4. [ ] Run the parameter-space iteration; produce the first basin map for an operator in this stack.
5. [ ] Use the result to issue or refuse a basin-stability certificate for that operator's mass number.
6. [ ] Define the certificate schema (the seven fields in §3 of the seed doc) as a typed object the lawfulness filter can consume.

### Connection to existing tracks

- Slots between the lawfulness check (`INCOMPATIBLE_MANIFOLDS_AND_LAWFUL_LOSS.md`) and the coding-cost accounting (`CodingCost`).
- Becomes a precondition for trusting `AdaptiveBlock` update rules under iteration.
- Catches strange-attractor capture, boundary drift, imaginary-axis failure, residual hiding (see §5 of the seed doc).

### Independence

Track E is independent of Tracks A–D. It can run in parallel and does not block Hutter submission prep.

## Deferred

- Track B steps 5-6: enwik8 testing, compressor prototype
- Track A steps 1-3: Lean proofs (can be done in parallel)
- Track A steps 4-7: harder proofs (density, determinism, roundtrip)
- Hutter Prize actual submission prep
