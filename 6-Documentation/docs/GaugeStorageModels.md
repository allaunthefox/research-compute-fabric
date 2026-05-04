# Gauge Storage Models

**Purpose:** Document storage models for lattice gauge field simulations

**Status:** Draft for Review  
**Date:** 2026-04-29

---

## Storage Models

### 1. 8-Real/Site Model (Toy Model)

**Description:**
- Stores 8 real numbers per lattice site
- Simplified representation of SU(3) gauge field
- Suitable for small lattice experiments and toy simulations

**Storage Calculation:**
```
S = N × 8 × bytesPerReal
where N = L⁴ (lattice sites)
```

**Example:**
- L = 8 (8⁴ lattice)
- bytesPerReal = 4 (Q16_16 fixed-point)
- Storage: 8⁴ × 8 × 4 = 16,384 bytes = 16 KB

**Advantages:**
- Simple storage model
- Easy to implement
- Suitable for toy experiments

**Limitations:**
- Does not capture full SU(3) structure
- Not suitable for production Yang-Mills simulations
- Loss of gauge invariance information

### 2. SU(3) Link Model (Full Model)

**Description:**
- Stores 4 complex numbers per lattice site (link variables)
- Full SU(3) gauge field representation
- Captures gauge invariance structure

**Storage Calculation:**
```
S = N × 4 × 2 × bytesPerReal
where N = L⁴ (lattice sites)
4 complex numbers × 2 (real/imag) = 8 reals per site
```

**Example:**
- L = 8 (8⁴ lattice)
- bytesPerReal = 8 (Float64)
- Storage: 8⁴ × 4 × 2 × 8 = 32,768 bytes = 32 KB

**Advantages:**
- Full SU(3) structure
- Preserves gauge invariance
- Suitable for accurate simulations

**Limitations:**
- Higher storage requirements
- More complex implementation
- Still not suitable for 64⁴ production on small VPS

---

## Feasibility Analysis

### Small Lattice Experiments (L = 4-16)

**8-Real/Site Model:**
- L = 4: 4⁴ × 8 × 4 = 2,048 bytes = 2 KB (Q16_16)
- L = 8: 8⁴ × 8 × 4 = 16,384 bytes = 16 KB (Q16_16)
- L = 16: 16⁴ × 8 × 4 = 262,144 bytes = 256 KB (Q16_16)

**SU(3) Link Model:**
- L = 4: 4⁴ × 4 × 2 × 8 = 4,096 bytes = 4 KB (Float64)
- L = 8: 8⁴ × 4 × 2 × 8 = 32,768 bytes = 32 KB (Float64)
- L = 16: 16⁴ × 4 × 2 × 8 = 524,288 bytes = 512 KB (Float64)

### Production Lattice (L = 64)

**8-Real/Site Model:**
- L = 64: 64⁴ × 8 × 4 = 67,108,864 bytes = 64 MB (Q16_16)

**SU(3) Link Model:**
- L = 64: 64⁴ × 4 × 2 × 8 = 134,217,728 bytes = 128 MB (Float64)
- With Float64: 64⁴ × 4 × 2 × 8 = 1,073,741,824 bytes = 1,024 MB

---

## Conclusion

**Feasible on Small VPS:**
- L = 4-16 lattice experiments
- 8-real/site toy model
- SU(3) link model for small lattices

**NOT Feasible on Small VPS:**
- L = 64 production lattice
- Full Yang-Mills simulations
- Millennium Prize proof work

**Recommendation:**
- Use small lattice experiments (L = 4-16) for sandbox
- Document storage model clearly in all experiments
- Do not claim 64⁴ feasibility without proper hardware
