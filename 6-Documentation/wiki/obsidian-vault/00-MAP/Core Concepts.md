# Core Concepts

## Fundamental Principles

### 🎯 **Single Source of Truth**
**Lean 4** is the authoritative source of truth for all formal claims. Every mathematical statement, algorithm, and system invariant must be expressible and verifiable in Lean 4.

### 🔢 **Fixed-Point Arithmetic**
All computation uses **Q16.16 fixed-point arithmetic** with Q0.64 scalars as the universal interface. This ensures deterministic behavior across all computational substrates.

### 📊 **Receipt-Bounded Transformations**
Every transformation must generate a **receipt** that proves:
- What changed
- What survived
- What was lost
- What it cost
- At what scale
- What receipt proves it

## System Architecture

### 🏗️ **Layer Model (USTSM)**
The **Universal Substrate Topological State Machine** consists of 7 layers:

| Layer | Name | Domain | Status |
|-------|------|--------|--------|
| **L0** | Primordial | Pure math, fixed-point arithmetic | ✅ Implemented |
| **L1** | Geometric | Shape-aware topology | 🟡 Partial |
| **L2** | Biological | Genetic codes, spiking neurons | 🟡 Speculative |
| **L3** | Thermodynamic | Energy-aware quality | 🟡 Speculative |
| **L4** | Security | Attack-aware gating | 🟡 Partial |
| **L5** | Semantic | Meaning-aware filtering | 🟡 Partial |
| **L6** | Meta | Self-aware adaptation | 🟡 Partial |

### 🔄 **Transformation Pipeline**
```
Lean Formal Proof → Receipt Generation → Hardware Extraction → Validation
```

## Key Components

### 📐 **Mathematical Foundations**
- [[Q16.16 Fixed-Point Arithmetic]] - Core number system
- [[Braid Fields]] - Topological data structures
- [[PIST/DIAT Shell]] - Computational framework
- [[SSMS_nD]] - n-dimensional state machine

### 🔐 **Security & Safety**
- [[AngrySphinx]] - Exponential proof of work
- [[FAMM]] - Frustration-avoiding memory management
- [[ASIC Topology]] - Attack-aware system design

### 🧬 **Biological Computing**
- [[Genetic Code Tables]] - 30+ genetic code implementations
- [[Spiking Dynamics]] - Izhikevich neuron models
- [[Genomic Compression]] - DNA-based data compression

### ⚡ **Hardware Extraction**
- [[FPGA Implementation]] - Field-programmable gate arrays
- [[ASIC Design]] - Application-specific integrated circuits
- [[Hardware Receipts]] - Physical validation receipts

## Research Methodology

### 🎯 **Attack Plans**
Structured research initiatives that follow the pattern:
1. **Assessment** - Current state analysis
2. **Implementation** - Formal proof development
3. **Verification** - Receipt generation and validation

### 📊 **Milestones**
Time-bound objectives with clear success criteria:
- [[Burgers 4-Theorem Attack Plan]] - Active milestone
- [[Eigensolid Convergence]] - Core compression theorem
- [[Receipt Invertibility]] - Bijective encoding theorem

### 🔍 **Conjectures**
Research hypotheses requiring formal proof:
- [[Sidon Field Conjectures]] - Combinatorial optimization
- [[Mass Number Admissibility]] - Number theory constraints
- [[Hyperfluid Density Profiles]] - Physical modeling

## Quality Assurance

### ✅ **Formal Verification**
- **Lean Compilation** - All code must compile without errors
- **Proof Checking** - All theorems must have valid proofs
- **Type Safety** - Strong typing prevents runtime errors

### 🧾 **Receipt Validation**
- **Schema Compliance** - Receipts must follow defined schemas
- **Hash Verification** - Cryptographic integrity checks
- **Reproducibility** - Results must be reproducible

### 🔬 **Experimental Validation**
- **Numerical Testing** - Computational experiments
- **Hardware Testing** - Physical implementation validation
- **Cross-Validation** - Multiple verification methods

## Terminology

### 📚 **Glossary**
- **Sidon Label** - Address from a set with unique pairwise sums
- **BraidStorm** - 8-strand braid topology for compression
- **Eigensolid** - Converged, stable state of braid crossing loop
- **Yang-Baxter** - Braid relation defining order invariance
- **GCL** - Genetic Code Language
- **AVM** - Adaptive Virtual Machine
- **TSM** - Topological S3C Manifold

### 🏷️ **Tag System**
- `#layer-L0` through `#layer-L6` - Layer classification
- `#formal-proof` - Lean formal proofs
- `#receipt` - Receipt documents
- `#attack-plan` - Research attack plans
- `#milestone` - Project milestones
- `#conjecture` - Research conjectures

## Related Concepts

### 🔗 **Cross-References**
- [[Formal Methods]] - Mathematical verification techniques
- [[Topology]] - Mathematical study of shapes and spaces
- [[Information Theory]] - Quantitative information analysis
- [[Quantum Computing]] - Quantum mechanical computation
- [[Neural Networks]] - Machine learning architectures

### 📖 **External Resources**
- [Lean 4 Documentation](https://lean-lang.org/)
- [Formal Methods Wiki](https://en.wikipedia.org/wiki/Formal_methods)
- [Topology Wiki](https://en.wikipedia.org/wiki/Topology)

---

#core-concepts #research-stack #formal-methods