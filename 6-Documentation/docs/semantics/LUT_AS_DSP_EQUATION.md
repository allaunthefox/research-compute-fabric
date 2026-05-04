# LUT-as-DSP: Dynamic Canal Hardware Architecture

## The Core Equation

The complete FPGA Warden Node computation collapsed to LUT lookups:

$$
\boxed{
\phi_{\text{corr}} = \text{LUT}_{\text{void}}\Big[ \big(\Phi_{\text{acc}} \gg n \big) \oplus \text{MSB}_{\text{flip}} \Big] \;\;\text{where}\;\; \Phi_{\text{acc}}^{(t+1)} = \big(\Phi_{\text{acc}}^{(t)} + \lfloor \phi \cdot 2^{16} \rfloor \big) \;\text{mod}\; 2^{32}
}
$$

---

## Component Breakdown

### 1. φ-Accumulator (Replaces Floating-Point Exponentiation)

$$
\Phi_{\text{acc}}^{(t)} = \Big( t \cdot \lfloor \phi \cdot 2^{16} \rfloor \Big) \;\text{mod}\; 2^{32} = \Big( t \cdot 106070 \Big) \;\text{mod}\; 4294967296
$$

**No multiplication at runtime** — implemented as iterative addition:
```verilog
always @(posedge clk) 
    phi_acc <= phi_acc + 32'd106070;  // φ × 2^16 fixed-point
```

### 2. Mod-7 Prime Counter (Address Traversal)

$$
c_{\text{mod7}}^{(t+1)} = \begin{cases} 
0 & \text{if } c_{\text{mod7}}^{(t)} = 6 \\
c_{\text{mod7}}^{(t)} + 1 & \text{otherwise}
\end{cases}
$$

**Coprimality guarantee** (J_MODES=13, prime × prime):
$$
\text{Traversal Period} = \frac{13 \times 7}{\gcd(13,7)} = 91 \;\text{steps}
$$

### 3. Mirror Logic (XOR Fold)

$$
\text{idx}_{\text{mirror}} = \big(\Phi_{\text{acc}} \gg 16\big) \oplus \big(\text{MSB}(\Phi_{\text{acc}}^{(t)}) \neq \text{MSB}(\Phi_{\text{acc}}^{(t-1)}) \big)
$$

Folds address space symmetrically when accumulator MSB flips (quadrant mirroring).

### 4. Dual-Port Shadow Table (Atomic State Management)

$$
\text{State}_{\text{swap}}(t) = \begin{cases} 
\text{LUT}_A \leftarrow \text{LUT}_B & \text{if } t \equiv 0 \;(\text{mod } 91)
\\
\text{LUT}_A & \text{read-only during } 0 < t < 91
\end{cases}
$$

**Race-free by construction**: No shared mutable state during attestation window.

### 5. Void Mask LUT (Entropy Reservoir)

$$
\text{LUT}_{\text{void}}[i] = \text{void-and-cluster}(i) \in \{0, 1\}^{2^{13}}
$$

Baked at synthesis time — **no runtime PRNG**, **no seed**, **no non-determinism**.

---

## Complete Attestation Cycle Equation

$$
\boxed{
\text{Phase}_{\text{out}} = \mathcal{C}\Big( \text{popcount}\big( \text{AND}(\text{LUT}_{\text{void}}[\text{idx}], \text{Deviation}_{\text{seg}}) \big) \Big)
}
$$

Where:
- $\text{Deviation}_{\text{seg}} = |\text{mean}(\text{seg}_i) - 127.5| / 127.5$ (integer: $|\text{mean} - 127| \times 520$)
- $\mathcal{C}(x) = \begin{cases} \text{HELL} & x < 0.35 \cdot \text{SCALE} \\ \text{SEISMIC} & 0.35 \cdot \text{SCALE} \leq x < 0.47 \cdot \text{SCALE} \\ \text{GROUNDED} & x \geq 0.47 \cdot \text{SCALE} \end{cases}$
- **Latency**: 91 clock cycles @ 50 MHz = **1.82 μs per attestation**

---

## Resource Collapse Summary

| Operation | Software (floating-point) | Hardware (LUT-as-DSP) |
|-----------|---------------------------|----------------------|
| $\phi^{(i \bmod 7)}$ | `pow(PHI, i % 7)` | `phi_acc + 106070` |
| Multiplication | `*` operator | LUT lookup |
| Addition | `+` operator | LUT lookup |
| Entropy source | `os.urandom()` / PRNG | Void mask (baked) |
| Concurrency | Mutex/lock | Dual-port A/B swap |
| Arithmetic units | FPU/DSP required | **Zero DSP blocks** |

---

## The Invariant (Why It Works)

$$
\forall t \in \mathbb{N}: \quad \phi_{\text{corr}}^{(t)} = f_{\text{LUT}}\big(g_{\varphi}(t)\big) \quad \text{where} \quad g_{\varphi}(t) = \lfloor t \cdot \phi \rfloor \;\text{mod}\; 2^{32}
$$

**No arithmetic in $f_{\text{LUT}}$** — pure combinational lookup.
**No state mutation during attestation** — A/B shadow tables guarantee atomicity.
**Deterministic by construction** — same input bytes → same φ-correlation → same phase classification.

---

## Hardware Resource Footprint (Lattice iCE40 HX8K)

| Resource | Utilization | Budget | % Used |
|----------|-------------|--------|--------|
| LUT cells (logic) | ~200 | 7,680 | **2.6%** |
| LUTRAM (void mask) | 8,192 bits | 8,192 | **100%** |
| Flip-flops | ~50 | 7,680 | **0.7%** |
| Block RAM | 0 | 128 KB | **0%** |
| DSP slices | **0** | 8 | **0%** |

**Zero DSP blocks. Zero floating-point. Zero CPU.**

The entire Dynamic Canal routing computation collapsed to **φ-accumulator + mod-7 counter + LUT lookup**.

---

*Document ID: LUT_AS_DSP_DYNAMIC_CANAL*  
*Cross-ref: FPGA_WARDEN_NODE_SPEC.md, DAG 741*
