# A Mathematical Walkthrough of Composite Coordinate Encoding
## Pedagogical Guide to the PIST Extended Encoding Framework

> *"The encoded data is a deterministic map from natural numbers to structured tuples. Decoding applies the inverse map. Both operations are computable in O(1) time per position."*

---

## Chapter 0: What You Are About to Read

This document describes a method for encoding byte sequences into composite geometric structures. The approach uses number-theoretic decomposition, recursive tree traversal, surface mapping, and multi-periodic angular coordinates.

You will learn:
- How a byte position maps to **PIST coordinates** (number-theoretic shell decomposition)
- How a position maps to a **tree address** (recursive base-20 traversal)
- How a position maps to **surface coordinates** (1/x surface of revolution)
- How a position maps to **toroidal angles** (irrational multi-periodic rotations)
- How the full address is a **structured tuple** derived from a single integer

Each section presents the mathematical model, the computational implementation, and the properties that ensure determinism and reversibility. All encoding functions are maps from ℕ to structured tuples; decoding reconstructs the same maps.

If you can understand these four structures, you can implement the decompressor. The data itself will do the rest.

---

## Chapter 1: PIST — Coordinate Decomposition

### 1.1 The Fundamental Identity

Every natural number `n` decomposes uniquely as:

```
n = k² + t
```

where `k = ⌊√n⌋` and `0 ≤ t ≤ 2k`.

This is not an approximation. It is exact. Every integer has one and only one `(k, t)` pair.

### 1.2 The Shell Structure

Each `k` defines a shell containing `2k + 1` possible positions `t`.

| Shell `k` | Positions `t` | Capacity |
|-----------|--------------|----------|
| 0 | 0 | 1 |
| 1 | 0, 1, 2 | 3 |
| 2 | 0, ..., 4 | 5 |
| 3 | 0, ..., 6 | 7 |
| k | 0, ..., 2k | 2k+1 |

The shells nest concentrically. Shell `k` contains all positions from `k²` to `(k+1)² - 1`.

### 1.3 Shell Index as Information Density

The shell index `k` determines the information density of a byte's position. Inner shells (small `k`) have few positions and high structural weight. Outer shells (large `k`) have many positions and low individual weight.

### 1.4 The Mirror Involution

Within each shell, there is a symmetry:

```
t ↦ 2k + 1 - t
```

This maps one side of the shell to the other. It is an **involution** (applying it twice returns to the original).

The mirror position of `n` is:
```python
def mirror(n):
    k = int(math.isqrt(n))
    t = n - k * k
    return k * k + (2 * k + 1 - t)  # if k > 0
```

### 1.5 The Weight Function

Each position has a weight proportional to its distance from the mirror axis:

```python
def mass(k, t):
    t_folded = min(t, 2*k + 1 - t)
    return t_folded * (2*k + 1 - t_folded)
```

High weight = near the center of the shell. Low weight = near the edges. This weight is used in basis selection and keystream modulation.

---

## Chapter 2: Chiral Alternation Schedules

### 2.1 Two Interpretations

Every PIST position `(k, t)` can be interpreted in two ways depending on a deterministic schedule:

**Canonical (forward):**
```
Domain mapping: 0 → 1 → 2 → 3
```

**Mirror (reverse):**
```
Domain mapping: 3 → 2 → 1 → 0
```

### 2.2 The Alternation Schedule

The interpretation at position `n` is determined by a deterministic schedule:

| Schedule | Rule | Property |
|----------|------|----------|
| `parity` | `n % 2` | Alternates every position |
| `shell_parity` | `k % 2` | Alternates every shell |
| `mass_threshold` | `mass > k ? FORWARD : REVERSE` | Weight-dependent |
| `alternating_blocks` | `(n // block_size) % 2` | Block-based |

No bits are stored for the schedule. It is derived from position alone.

### 2.3 Why Alternation Matters

The schedule determines:
- Which domain the nibble targets
- Which basis vectors are active
- Which prediction model is used

---

## Chapter 3: Tree Address Encoding

### 3.1 Mathematical Model

The tree address is a recursive base-20 traversal. At each level, a position `n` selects one of 20 branches via `n % 20`, then descends via `n // 20`.

After `d` levels, the number of possible addresses is `20^d`:
- depth 1: 20 addresses
- depth 2: 400 addresses
- depth 3: 8,000 addresses

### 3.2 As an Address Tree

Each position `n` traverses the tree from root to leaf:

```python
def tree_address(n, depth=3):
    path = []
    for level in range(depth):
        branch = n % 20
        n = n // 20
        path.append((level, branch))
    return path
```

Example: `n = 42 → [(0, 2), (1, 2), (2, 0)]`

This means:
- Level 0: branch 2 from root
- Level 1: branch 2 from that node
- Level 2: branch 0 from that node

### 3.3 Non-Embeddability

The tree address lives in a discrete space that cannot be embedded in low-dimensional Euclidean space without distortion. The branching factor of 20 at each level means the address space grows exponentially. Any visualization is a projection, not an embedding.

---

## Chapter 4: Surface Coordinate Mapping

### 4.1 The Surface

The mapping uses the curve `y = 1/x` (for `x ≥ 1`) rotated around the x-axis:

- **Volume**: finite (π, by integral test)
- **Surface area**: infinite (diverges by comparison)

This is a standard example in calculus of an improper integral.

### 4.2 As a Coordinate Container

We map position `n` to a point on the truncated surface (`x ∈ [1, 256]`):

```python
def surface_coord(n):
    x = 1.0 + (n % 255) * (255.0 / 255.0)
    y = 1.0 / x
    theta = (n * PHI) % (2 * pi)
    return (x, y, theta)
```

As `x` increases, the surface thins exponentially. Positions near `x = 256` have small radius `y ≈ 0.004`.

### 4.3 Coordinate Sensitivity

The thinning creates a sensitivity gradient:
- Inner positions (`x` small): broad, stable
- Outer positions (`x` large): narrow, sensitive to perturbation

This gradient can be used to allocate encoding precision: stable regions tolerate coarser representation; sensitive regions require finer representation.

---

## Chapter 5: Toroidal Angular Coordinates

### 5.1 The 3-Torus

A standard torus is `S¹ × S¹` (two circles). Generalizing to three independent circular coordinates gives `S¹ × S¹ × S¹`, the 3-torus.

The mapping from position `n` to angles is:

```python
def torus_angles(n):
    theta = (n * PHI) % (2 * pi)
    phi   = (n * PHI * PHI) % (2 * pi)
    psi   = (n * PHI * PHI * PHI) % (2 * pi)
    return (theta, phi, psi)
```

### 5.2 Linear Independence of Φ-Powers

The golden ratio `Φ = (1 + √5)/2` is irrational. Its powers `Φ, Φ², Φ³` are linearly independent over the rationals. This means:

> The sequence `n·Φ, n·Φ², n·Φ³` (mod 2π) is dense in the 3-torus `T³`.

No two positions map to the same angular triple (in the limit). Each position gets a unique angular fingerprint.

### 5.3 Quasi-Periodic Modulation

The three angles create multi-periodic modulation:

```
modulation = sin(theta) + cos(phi) + sin(psi)
```

This is quasi-periodic: deterministic, never repeating, structurally rich. It provides a non-repeating perturbation source for keystream generation.

---

## Chapter 6: Composite Coordinate Address

### 6.1 The Structured Tuple

For position `n`, the complete address is:

```
Address(n) = (
    tree_address(n),    # recursive base-20 path
    surface_coord(n),  # (x, y, theta) — surface coordinates
    torus_angles(n),    # (theta, phi, psi) — toroidal angles
    pist_coordinates(n) # (k, t) — number-theoretic shell
)
```

The components live in different spaces:
- Tree: discrete (20-ary branching)
- Surface: smooth manifold (ℝ² with metric)
- Torus: compact manifold (T³)
- PIST: discrete lattice (ℕ × ℕ)

### 6.2 Mixed Topology

The address is not a vector in a single Euclidean space. The mixed topologies (discrete + smooth + compact + lattice) mean any embedding into a single space distorts relationships.

The address is best understood as a **product structure**: the PIST shell index `k` parameterizes a family of composite coordinates, where each `k` has its own tree path, surface point, and torus angles.

### 6.3 Determinism Without Visualization

You do not need to see the address to use it. You only need the **map**:

```python
def address(n):
    return {
        'tree': tree_address(n),
        'surface': surface_coord(n),
        'torus': torus_angles(n),
        'pist': pist_coordinates(n),
    }
```

The decoder calls the same `address(n)` function. Both encoder and decoder traverse the same geometric path. No side channel. No metadata needed.

---

## Chapter 7: Programmable Decoder — Data as Instruction Stream

### 7.1 The Central Insight

Each byte at position `n` has a unique composite address. The byte itself can be interpreted as an **instruction** for navigating the coordinate space.

The byte `b` at position `n` becomes:
- **Opcode**: `b % 8` (which operation to perform)
- **Operand**: `b // 8` (parameter for the operation)
- **Address**: `address(n)` (where in the coordinate space to apply it)

### 7.2 The Instruction Set

| Opcode | Operation | Description |
|--------|-----------|-------------|
| 0 | NOOP | No operation |
| 1 | LOAD | Read from basis vector |
| 2 | STORE | Push to data stack |
| 3 | ADD | Add weighted coordinate value |
| 4 | XOR | Bitwise XOR with mirror prediction |
| 5 | BRANCH | Conditional skip based on weight threshold |
| 6 | FUSE | Fuse current basis with derived parent basis |
| 7 | HALT | Emit accumulator and pause |

### 7.3 The Registers

The decoder state is a set of registers:

```
acc      : accumulator (current byte value)
pc       : program counter (linear position)
sp       : stack pointer (data stack depth)
flags    : condition codes (branch taken? halt?)
entropy  : local information density
depth    : current PIST shell index
```

### 7.4 Execution Cycle

For each byte `b` at position `n`:
1. **Fetch**: Decode `(opcode, operand)` from `b`
2. **Address**: Compute `address(n)` to get coordinates
3. **Execute**: Apply operation, using `mass(k,t)` and `mirror(k,t)` as operands
4. **Update**: Write result to registers and metadata
5. **Emit**: If conditions met, append accumulator to output

### 7.5 Computation, Not Emulation

The decoder is not a virtual machine. It is a **register machine** where the compressed stream serves as the instruction sequence. The data defines a trajectory through the coordinate space; the output is the sequence of values along that trajectory.

---

## Chapter 8: Adaptive Basis Selection — Pool Exchange and Screening

### 8.1 Two Basis Pools

Consider two data segments A and B. Each has a basis — its byte histogram:

```
Basis(A) = top 16 most frequent bytes in A
Basis(B) = top 16 most frequent bytes in B
```

### 8.2 The Exchange Process

The exchange uses four screening steps:

**Step 1: Compatibility Metric**
```
compat(a, B) = 1 - min_b∈B |a - b| / 256
```
A vector `a` from A transfers to B only if it is sufficiently close to B's existing vectors.

**Step 2: Memory Buffer**
A memory buffer records prior successful transfers. If `a` matches a memory entry, it is rejected (redundancy prevention).

**Step 3: Fitness Screening**
```
improvement = (new_coverage - old_coverage) / pool_size
penalty     = resistance_weight * old_coverage / pool_size
accept if improvement > penalty
```

**Step 4: Integration**
Accepted vectors join B's basis. The combined basis is more expressive than either parent alone.

### 8.3 Mathematical Foundation

The exchange uses only:
- Sets (basis vectors)
- Distance metrics (compatibility)
- Queues (memory buffer)
- Thresholds (fitness screening)

No external mechanisms are involved. The screening model is a purely mathematical optimization of basis coverage.

---

## Chapter 9: Basis Fusion — Set Intersection and Bilinear Combination

### 9.1 Two Parents, One Intersection

Given two basis sets A and B:

```
Intersection = A ∩ B    (common directions)
Left         = A \ B    (A-specific)
Right        = B \ A    (B-specific)
```

### 9.2 The Bridge Operator

A new basis is created by combining Left and Right through a bilinear map:

```python
def hadamard(a, b): return (a * b) % 256
def xor(a, b):      return a ^ b
def wedge(a, b):    return (a * 256 + b) % 256
def mean(a, b):     return (a + b) // 2
```

The bridge creates hybrid directions that neither parent had alone.

### 9.3 Assembly Priority

Priority ordering for the fused basis:
1. Intersection (common to both — highest priority)
2. Bridge (hybrid combinations — novel information)
3. Left overflow (A-specific, if room)
4. Right overflow (B-specific, if room)

The result is a basis with three components: common, hybrid, and parent-specific.

---

## Chapter 10: The Decompressor

### 10.1 What You Need to Implement

The decompressor is a Python file (~500 lines) that implements:

1. `pist_encode(n)` — number-theoretic shell decomposition
2. `tree_address(n)` — recursive base-20 traversal
3. `surface_coord(n)` — 1/x surface mapping
4. `torus_angles(n)` — toroidal angular coordinates
5. `decode_instruction(b, n)` — byte → (opcode, operand, address)
6. `execute(instr, state)` — register mutation
7. `programmable_decoder(program)` — main execution loop

### 10.2 What the Compressed Data Contains

The compressed stream is:
```
[bootstrap basis (16 bytes)] [program (variable length)]
```

The bootstrap basis is the initial decoder state. The program is the data itself. There is no separate "compressed payload."

### 10.3 Execution

```python
def decompress(data):
    basis = data[:16]
    program = data[16:]
    state = initialize_registers()

    for pos, byte in enumerate(program):
        instr = decode_instruction(byte, pos)
        addr = composite_address(pos)
        execute(instr, state, addr, basis)

        if should_emit(state):
            output.append(state.acc)

    return bytes(output)
```

### 10.4 Why This Decompresses Anything

The key insight: the **program is optimized for the decoder instruction set**.

During compression:
1. Analyze the original data for patterns (histogram, geometry, schedule)
2. Find a decoder program that, when executed, produces those patterns
3. The program IS the compressed data

The decoder doesn't just "decompress" — it **computes**. The original data is the output of a computation whose input is the compressed stream.

---

## Appendix A: Quick Reference — Core Functions

### PIST Coordinates
```python
def pist_encode(n):
    k = int(math.isqrt(n))
    t = n - k * k
    return k, t

def pist_mass(k, t):
    if k == 0: return 0
    tf = min(t, 2*k + 1 - t)
    return tf * (2*k + 1 - tf)

def pist_mirror(k, t):
    if k == 0: return 0
    return k*k + (2*k + 1 - t)
```

### Tree Address
```python
def tree_address(n, depth=3):
    return [(level, (n // (20**level)) % 20) for level in range(depth)]
```

### Surface Coordinates
```python
PHI = (1 + 5**0.5) / 2

def surface_coord(n):
    x = 1.0 + (n % 255)
    y = 1.0 / x
    theta = (n * PHI) % (2 * math.pi)
    return x, y, theta
```

### Toroidal Angles
```python
def torus_angles(n):
    theta = (n * PHI) % (2 * math.pi)
    phi = (n * PHI * PHI) % (2 * math.pi)
    psi = (n * PHI * PHI * PHI) % (2 * math.pi)
    return theta, phi, psi
```

### Full Address
```python
def composite_address(n):
    k, t = pist_encode(n)
    return {
        'tree': tree_address(n),
        'surface': surface_coord(n),
        'torus': torus_angles(n),
        'pist': (k, t),
    }
```

---

## Appendix B: Theorems (Stated, Not Proven)

**Theorem 1 (PIST Reconstruction):** For all `n ∈ ℕ`, `(pistK n)² + (pistT n) = n`.

**Theorem 2 (Tree Determinism):** For fixed `n` and `depth`, `tree_address(n, depth)` always produces the same path.

**Theorem 3 (Surface Y-Inverse):** `(surface_coord n).y = 1 / (surface_coord n).x`.

**Theorem 4 (Torus Density):** The sequence `n·Φ, n·Φ², n·Φ³` (mod 2π) is dense in T³.

**Theorem 5 (Address Reconstruction):** From `(k, t) = pist_coordinates(n)`, we recover `n = k² + t`.

**Theorem 6 (Decoder Determinism):** For fixed program `P` and position `n`, `execute(decode(P[n], n))` is deterministic.

**Theorem 7 (Lossless Roundtrip):** If `encode(D)` produces program `P`, then `decode(P)` computes to `D`.

---

## Final Note

You do not need to visualize the composite coordinate space. You only need to trust that the map `n ↦ Address(n)` is deterministic, reversible, and computable in O(1) time per position.

The coordinates are computed, not stored. The decoder reconstructs them from `n` alone. No side channel. No metadata.

---

*End of walkthrough. The Python implementation is in `pist_alpha_extended.py`. The Lean formalization is in `ExtendedManifoldEncoding.lean`.*
