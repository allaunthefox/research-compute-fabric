# Calculator-Plain Math: The Entire Research Stack

Every equation in this project reducible to `+ - * / ^ log`.
No calculus. No linear algebra. Just arithmetic.

---

## 1. Nibble Switch (GCCL Core)

**What it is:** A 4-bit transition atom.

**Calculator steps:**

Given `control` (0-3) and `domain` (0-3):

```
nibble = control * 4 + domain

Example: control=1 (ACCEPT), domain=2 (M_TENSION)
nibble = 1 * 4 + 2 = 6
```

**Unpack:**
```
control = floor(nibble / 4)
domain  = nibble mod 4

Example: nibble = 6
control = floor(6 / 4) = 1
domain  = 6 mod 4 = 2
```

**That's it. No algebra. Just `* / mod`.**

---

## 2. Manifold State Point

**What it is:** A point on the machine's map.

**Calculator steps:**

```
new_locus = old_locus + delta

delta depends on domain:
  K_AXIS    → delta = +1
  C_WINDING → delta = +256
  M_TENSION → delta = +65536
  Y_BREAK   → delta = -1

If polarity is negative, flip the sign.

Example: locus = 100, domain = K_AXIS, polarity = positive
new_locus = 100 + 1 = 101
```

**Curvature update (exponential moving average):**
```
new_curvature = 0.7 * old_curvature + 0.3 * target

target = 1.0 if control == ACCEPT
         0.0 otherwise

Example: curvature = 0.5, control = ACCEPT
new_curvature = 0.7 * 0.5 + 0.3 * 1.0
              = 0.35 + 0.30
              = 0.65
```

**Register:**
```
new_register = nibble (the packed value, 0-15)
```

---

## 3. English Invariant Fingerprint

**What it is:** Reduce a sentence to its grammatical skeleton.

**Calculator steps (per word):**

1. Check if word is in a lookup table (DET, PRON, PREP, etc.)
2. If not, check suffix:
   - ends with "ing" → VBG
   - ends with "ed" → VBN
   - ends with "ly" → ADV
   - ends with "tion" → NOUN
   - ends with "able" → ADJ
3. If no match and length ≤ 3 → SHORT
4. Otherwise → LEX

**Example:**
```
"The cat sat on the mat"
The  → DET
cat  → LEX (not in tables, no special suffix)
sat  → SHORT (3 letters) or VBN (ends with 't', not 'ed')
on   → PREP (in table)
the  → DET
mat  → SHORT (3 letters)

Fingerprint: DET LEX SHORT PREP DET SHORT
```

**No math. Just string matching.**

---

## 4. Shannon Entropy

**What it is:** How unpredictable the language is.

**Calculator steps:**

Given a list of counts (how many times each form appears):

```
Step 1: total = sum of all counts

Step 2: For each count:
  p = count / total
  contribution = -p * log2(p)

Step 3: entropy = sum of all contributions
```

**Example:**
```
Forms: A=100, B=50, C=50
total = 100 + 50 + 50 = 200

For A: p = 100/200 = 0.5
       -0.5 * log2(0.5) = -0.5 * (-1) = 0.5

For B: p = 50/200 = 0.25
       -0.25 * log2(0.25) = -0.25 * (-2) = 0.5

For C: p = 50/200 = 0.25
       -0.25 * log2(0.25) = 0.5

entropy = 0.5 + 0.5 + 0.5 = 1.5 bits
```

**You need: `+ / * log2`. That's it.**

---

## 5. Power-Law (Zipf) Fit

**What it is:** Word frequency follows `count * rank ≈ constant`.

**Calculator steps:**

Given ranks (1, 2, 3, ...) and counts sorted descending:

```
alpha = 1 + N / sum(log(rank/count) for each item)
```

**Example:**
```
rank 1: count = 200 → log(1/200) = log(0.005) = -7.64
rank 2: count = 100 → log(2/100) = log(0.02) = -5.52
rank 3: count = 50  → log(3/50) = log(0.06) = -4.12

sum = -7.64 + (-5.52) + (-4.12) = -17.28
N = 3

alpha = 1 + 3 / (-17.28) = 1 - 0.174 = 0.826
```

**You need: `log + /`.**

---

## 6. Hutter Prize Score

**What it is:** How good the compression is.

**Calculator steps:**

```
C = (0.4 * C_comp + 0.35 * C_phys + 0.25 * C_geom) * (S / (G + F))
```

**Each component:**
```
C_comp = original_size / compressed_size  (compression ratio)
C_phys = log2(number_of_unique_words + 1)
C_geom = (top_form_count) / (total_forms)
S = spatial_locality (constant, e.g. 0.95)
G = decoder_size_in_MB
F = replay_overhead (constant, e.g. 0.4)
```

**Example:**
```
original = 1000 bytes
compressed = 100 bytes
decoder = 10 MB

C_comp = 1000 / 100 = 10.0
C_phys = log2(5000 + 1) = log2(5001) = 12.29
C_geom = 44679 / 152158 = 0.293
S = 0.95
G = 10
F = 0.4

C = (0.4 * 10.0 + 0.35 * 12.29 + 0.25 * 0.293) * (0.95 / (10 + 0.4))
  = (4.0 + 4.30 + 0.073) * (0.95 / 10.4)
  = 8.373 * 0.0913
  = 0.764
```

**You need: `+ * / log2`.**

---

## 7. Grand Compression Equation

**What it is:** The optimal compressor minimizes this.

**Calculator steps:**

```
Score = H + λ*|C| + μ*K + ν*dim

H  = Shannon entropy (from §4)
|C| = size of the compressor in bytes
K   = log2(|C| + 1)  (simplified Kolmogorov)
dim = number of unique forms / total sentences
```

**Example:**
```
H = 17.05 bits/form
|C| = 10000 bytes
K = log2(10001) = 13.29
dim = 151232 / 180189 = 0.839
λ = 0.001, μ = 0.01, ν = 1.0

Score = 17.05 + 0.001*10000 + 0.01*13.29 + 1.0*0.839
      = 17.05 + 10.0 + 0.133 + 0.839
      = 28.022
```

**You need: `+ * / log2`.**

---

## 8. Betti Numbers (Topological Invariants)

**What it is:** Count holes in the state trajectory.

**Calculator steps:**

```
β₀ = number of connected parts = 1 (always 1 for single trajectory)

β₁ = number of loops
     A loop = trajectory revisits a previous point

χ (Euler) = V - E + F
  V = number of unique points
  E = number of edges (transitions) = len(trajectory) - 1
  F = β₁ (simplified)
```

**Example:**
```
trajectory: A → B → C → B → D
V = 4 (A, B, C, D)
E = 4 (AB, BC, CB, BD)
β₁ = 1 (B visited twice, forming loop B→C→B)

χ = 4 - 4 + 1 = 1
```

**You need: `+ -` only.**

---

## 9. Unified Hardware Surface

**What it is:** Add up all compute units.

**Calculator steps:**

```
total_compute = CPU_cores + (if has_GPU then 1024 else 0)

memory_tiers:
  RAM_max  = available_RAM * 0.5
  VRAM_max = available_VRAM * 0.7
```

**Example (this machine):**
```
CPU = 12 cores
GPU = yes (RTX 4070 SUPER)
total = 12 + 1024 = 1036 compute units

RAM = 17.2 GB available → 8.6 GB managed
VRAM = 11.8 GB → 8.3 GB managed
```

**You need: `+ *`.**

---

## 10. Cache Statistics

**What it is:** Hit rate and size.

**Calculator steps:**

```
hit_rate = hits / (hits + misses) * 100

Example:
hits = 161,154
misses = 3,523
hit_rate = 161154 / (161154 + 3523) * 100
         = 161154 / 164677 * 100
         = 97.9%
```

**You need: `+ / *`.**

---

## Summary Table

| Concept | Operations Needed | Difficulty |
|---|---|---|
| Nibble Switch | `* + mod /` | Elementary |
| Manifold Point | `+ *` | Elementary |
| Fingerprint | String lookup | Elementary |
| Shannon Entropy | `+ / * log` | High school |
| Power-Law Fit | `+ / log` | High school |
| Hutter Score | `+ * / log` | High school |
| Grand Equation | `+ * / log` | High school |
| Betti Numbers | `+ -` | Elementary |
| Hardware Surface | `+ *` | Elementary |
| Cache Stats | `+ / *` | Elementary |

**Every equation in this project uses only `+ - * / ^ log`.**
**No calculus required. No matrices. Just arithmetic.**

A high school student with a scientific calculator could verify every number.
