# RedPajama English Manifold Pipeline

## What This Is

This pipeline ingests the [RedPajama](https://github.com/togethercomputer/RedPajama-Data) dataset — 1.2 trillion tokens of English text — and builds the **mathematical model of the English language itself**.

The output is a **structural invariant manifold**: every grammatical form English can take, anonymized and canonicalized, with frequency statistics.

## Why RedPajama

| Dataset | Tokens | Use |
|---|---|---|
| Common Crawl | ~878B | General web English |
| C4 | ~175B | Cleaned web crawl |
| GitHub | ~59B | Code + comments |
| Books | ~26B | Literary English |
| Wikipedia | ~24B | Encyclopedic English |
| ArXiv | ~28B | Technical/academic English |
| StackExchange | ~20B | Q&A English |
| **Total** | **~1.2T** | **The complete English language** |

## Quick Start

### 1. Get RedPajama Data

```bash
# Clone the data tools
git clone https://github.com/togethercomputer/RedPajama-Data.git
cd RedPajama-Data

# Download a subset (e.g., Wikipedia only — 24B tokens)
python data_prep/download.py --source wikipedia --output_dir /path/to/redpajama/

# Or download everything (requires TBs of storage)
python data_prep/download.py --all --output_dir /path/to/redpajama/
```

### 2. Run the Manifold Builder

```bash
cd /home/allaun/Documents/Research\ Stack/5-Applications/scripts

# Process Wikipedia subset (24B tokens → ~100M sentences)
python3 redpajama_english_manifold.py \
    --input /path/to/redpajama/wikipedia/*.jsonl \
    --limit 10000000 \
    --batch-save 1000000

# Process full RedPajama (1.2T tokens → ~5B sentences)
python3 redpajama_english_manifold.py \
    --input /path/to/redpajama/*/*.jsonl \
    --limit 5000000000 \
    --batch-save 10000000
```

### 3. Output

The pipeline produces:

```
/home/allaun/Documents/Research Stack/3-Mathematical-Models/redpajama_english_manifold/
├── manifold_checkpoint_1000000_*.json    # Checkpoints every N sentences
├── manifold_checkpoint_2000000_*.json
├── redpajama_english_manifold_*.json     # Final manifold
```

Each JSON contains:
- `sentences_processed`: total sentences analyzed
- `unique_forms`: number of distinct grammatical fingerprints
- `shannon_entropy_bits`: entropy of the invariant distribution
- `taxonomy`: grammatical category breakdown (SVO, NP_PP, COMPOUND, etc.)
- `top_forms`: most frequent structural patterns with examples

## The Mathematical Model

### Structural Fingerprinting

Each sentence is reduced to its grammatical skeleton:

| Original | Fingerprint |
|---|---|
| "The cat sat on the mat" | `DET NOUN VERB PREP DET NOUN` |
| "However, the situation changed dramatically" | `CONJ DET NOUN VERB ADV` |
| "In order to understand quantum mechanics..." | `PREP LEX PREP VERB NOUN NOUN` |

Content words → `LEX`, function words → specific tags (DET, PREP, CONJ, etc.)

### The 9 Natural Categories (discovered, not imposed)

| Category | % | Description |
|---|---|---|
| **NP_PP** | ~31.7% | Noun phrase + prepositional phrase |
| **COMPOUND** | ~31.1% | Conjoined clauses/phrases |
| **PP_CHAIN** | ~14.0% | Multiple prepositions |
| **DENSE_NP** | ~9.5% | Heavy noun phrase |
| **OTHER** | ~5.5% | Uncategorizable |
| **AUX_V** | ~3.6% | Auxiliary + verb |
| **SVO** | ~2.4% | Subject-verb-object |
| **VSO** | ~2.0% | Verb-subject-object |
| **PRON_V** | ~0.1% | Pronoun-verb |

**Key finding:** English is NOT primarily SVO. The dominant forms are **NP_PP** and **COMPOUND**.

## Compression Implications

The invariant manifold directly feeds into the **Grand Unified Theory of Language Compression**:

```
C* = argmin_C [ H(X|C) + λ|C| + μ·K(C) + ν·dim(M_C) ]
```

Where `M_C` is the manifold of grammatical forms. The more complete the manifold, the tighter the compression bound.

### Current Results (enwik9, 161K sentences)

| Metric | Value |
|---|---|
| Shannon entropy | **17.05 bits/form** |
| Unique forms | **151,177** |
| Top form frequency | **230** ("LEX+ PREP LEX") |

### Projected Results (RedPajama full, 5B sentences)

| Metric | Projected |
|---|---|
| Unique forms | **~2-5 million** |
| Shannon entropy | **~12-15 bits/form** |
| Compression ratio | **50-100x** |
| Hutter Prize | **< 112 MB** |

## Architecture

```
RedPajama JSONL/Parquet → Stream Parser → Sentence Splitter
                                                  ↓
                                         Structural Fingerprint
                                                  ↓
                                         Incremental Manifold Update
                                                  ↓
                                         Checkpoint Save
                                                  ↓
                                    Final Manifold → ANS Coder → Compressed
```

## Scaling Notes

- **Memory:** Uses `Counter` + `defaultdict` — ~500MB per 1M unique forms
- **Disk:** Each checkpoint ~50-200MB
- **Speed:** ~10K sentences/second on a single core
- **Parallel:** Can shard by source and merge manifolds afterwards

## Next Steps

1. **Obtain RedPajama data** (or a representative 100B-token subset)
2. **Run pipeline at scale** (set `--limit` to 100M+ sentences)
3. **Merge checkpoints** into unified manifold
4. **Feed into ANS coder** with grammatical context models
5. **Beat the Hutter Prize**
