# Equation Forest Index v0.1 — Canonical Layer

## 12 Foundation Kernels (Exact Solver Basis Vectors)

| ID | Equation | Domain |
|----|----------|--------|
| F01 | Shannon_Entropy_Calculation | Entropy/Compression |
| F02 | Information_Content_Measurement | Entropy/Compression |
| F03 | Hierarchical_Entropy_Decomposition | Entropy/Compression |
| F04 | Thermodynamic_Efficiency_Limit | Thermodynamic |
| F05 | Computation_Energy_Bound | Thermodynamic |
| F06 | Energy_Balance_Threshold | Thermodynamic |
| F07 | Maxwell_Demon_Recovery | Thermodynamic |
| F08 | Riemannian_Distance_Calculation | Geometry |
| F09 | Geodesic_Connection_Coefficients | Geometry |
| F10 | Single_Step_Geodesic_Integration | Geometry |
| F11 | Aggregate_Load_Combination | Cognitive/Routing |
| F12 | Intrinsic_to_Total_Ratio | Cognitive/Routing |

## 5 Core Streets (Graph Collapse)

1. **Entropy/Compression** (F01-F03) — Shannon entropy → hierarchical decomposition
2. **Thermodynamic Admissibility** (F04-F07) — Carnot/Landauer → energy balance
3. **Geometric Motion** (F08-F10) — Metric → connection → geodesics
4. **Cognitive/Routing Load** (F11-F12) — Aggregate load → routing efficiency
5. **DIAT/AVMR/S3C Bridge** — Shell → vector → witness → surface

## 8 Bridge Nodes

| Bridge | Connection |
|--------|------------|
| B1 | Entropy ↔ Load |
| B2 | Entropy ↔ Landauer |
| B3 | Energy ↔ Routing |
| B4 | Geometry ↔ Routing |
| B5 | DIAT ↔ Geometry |
| B6 | AVMR ↔ Entropy |
| B7 | S3C ↔ Codec |
| B8 | PIST ↔ Surface |

## 18-Bit Semantic Micro-ISA (Hardware Bridge)

**Genome18 Structure:**
- muBin: mutation/drift (routing load)
- rhoBin: verification pressure (routing efficiency)
- cBin: connectance (geometry/route neighborhood)
- mBin: compression residue (entropy)
- neBin: effective sample (entropy)
- sigmaBin: fitness proxy (entropy)

6 bins × 3 bits = 18 bits (262,144 states)

**Address Calculation:**
```
addr = muBin * 32768 + rhoBin * 4096 + cBin * 512 + mBin * 64 + neBin * 8 + sigmaBin
```

**Kernel to Bin Mapping:**
- F01-F03 → mBin, neBin, sigmaBin
- F04-F07 → cost/failure mask
- F08-F10 → cBin
- F11-F12 → muBin, rhoBin
- DIAT/AVMR/S3C/PIST → transition surface

## Pipeline Architecture

```
raw equation
→ F01-F12 kernel signature
→ street / bridge assignment
→ six 3-bit Genome18 bins
→ 18-bit ISA/LUT address
→ FPGA route expansion
→ PIST/witness audit
→ Lean/proof/executable check
```

## Best Street Through System

Shannon entropy → hierarchical entropy decomposition → DIAT shell reduction → AVMR vector roll-up → S3C codec → cognitive load minimization → Riemannian/geodesic routing → Landauer/Carnot admissibility → PIST witness surface

## Key Insight

Shell structure = coordinate system (not predictor). 18-bit ISA = routing state class (not full math object). Value = structural organization for measuring constraint, compression, geometry, routing together (not magical prediction).

## Graph Compression

Raw: hundreds of equations
→ After kernel signature: ~30-45 supernodes
→ After Genome18 encoding: 262,144 LUT addresses
→ Exact TSP becomes plausible

## Files

- `data/equations_forest.jsonl` — Full equation forest with signatures
- `data/equations_forest_genome18.jsonl` — Genome18 encoded equations
- `0-Core-Formalism/lean/Semantics/Semantics/Genome18.lean` — Lean formalization with theorems
- `scripts/equation_forest_genome18_encoder.py` — Kernel to bin mapping
- `MATH_MODEL_MAP.tsv` — Equation registry (source of truth, obeys this index)
- `AGENTS.md` — Full specification (sections 9.1-9.12)

## Minimap Visualization (Complex Roots Approach)

**Inspiration:** Parametric complex roots visualization (@lbarqueira.bsky.social, inspired by @sconradi.bsky.social)

**Concept:** Adapt complex roots visualization technique to create a 3D minimap of the Genome18 address space

**Mapping:**
- **Parameter domain:** Genome18 18-bit address space (262,144 states) instead of unit circle
- **Roots being tracked:** Equation signatures as they traverse parameter space
- **Color dimension:** Kernel signatures (F01-F12) instead of Im(t₂)
- **Trajectory paths:** Street/bridge transitions through the space

**Implementation approach:**
- Use polynomial root finding to visualize how equation clusters shift as Genome18 bins vary
- 6 bins × 3 bits = 18 parameters → traverse high-dimensional parameter space
- Color by street assignment (Entropy/Compression, Thermodynamic, Geometric, Cognitive/Routing, DIAT/AVMR/S3C)
- Show bridge transitions as trajectory lines between clusters

**Benefits:**
- Visual navigation system for 262,144-state Genome18 space
- Identify equation family clustering patterns
- Show parametric stability regions (bifurcation analysis)
- Debug kernel-to-bin mapping by visualizing signature drift

**Navigation/Positioning (Planet Beacon Concept):**
- Dynamic positioning: show current Genome18 address as "you are here" beacon
- Trajectory visualization: highlight paths to nearby states in the forest
- Bridge transitions: animate movement across street/bridge connections
- Relative positioning: understand your location within the full geometric space
- Real-time feedback: see how kernel signature changes affect position
- Exploration guidance: suggest optimal paths through equation space based on constraints

**Visual Aesthetic (Liquid Metal Inspiration):**
- Topographical feel: fluid, organic lines that swirl and cluster in dense areas
- Depth/3D effect: some areas bulge forward (active states), others recede (inactive)
- Warm metallic tones: champagne, rose gold, soft bronze mapping to street assignments
- Dark shadows: coffee-colored shadows defining depth between equation families
- Iridescent surface: high-sheen effect creating continuous motion despite static image
- Pearlescent quality: natural seashell-like patterning for bridge transitions
- Smooth, hypnotic flow: emphasizes continuous traversal through Genome18 space

**Reference Implementation (Scale Space):**
- Game: Scale Space by setz (itch.io, Steam coming)
- Multi-scale navigation: quantum/microscopic/classical/cosmic scales
- Physics controls: Equilibrium, Coherence, Viscosity, Mass for parameter space traversal
- Mathematical shapes: vortices, Lissajous figures, knots
- Emergent ecosystems: life competing for resources, dividing, playing, hunting
- Zen-like experience: calming navigation through infinite parameter space
- Tech stack: Unreal Engine Blueprints, WebGL, Three.js, Antigravity
- Mapping to Equation Forest:
  - Physics controls → Kernel signature parameters (F01-F12)
  - Multi-scale → 5 street assignments (Entropy/Compression, Thermodynamic, Geometric, Cognitive/Routing, DIAT/AVMR/S3C)
  - Mathematical shapes → Equation signature clusters and bridge transitions
  - Emergent ecosystems → Equation families competing for representation
  - Parameter space traversal → Genome18 262,144-state navigation

**Foundational Concepts (Scale Space Science):**
- Scale-Space Theory: structures emerge at the right scale (applies to Genome18 address space)
- Wavelet Transform: structure emerges from coherence and frequency (kernel signature coherence)
- Renormalization Group: behaviors evolve consistently across scales (street assignment invariance)
- Fractals & Scale-Invariance: recursive patterns across scales (equation family clustering)
- Emergence & Complexity: complex structures from simple interactions (F01-F12 kernel interactions)
- Cellular Automata: complexity from simple deterministic rules (Genome18 bin encoding)
- Information & Entropy: measuring and guiding emergence (entropy/compression kernels F01-F03)
- Thermodynamics: irreversible processes, phase transitions (thermodynamic kernels F04-F07)
- Quantum theories: entanglement, Hilbert space (geometric kernels F08-F10)
- Network Theory: graph topology, small-world networks (cognitive/routing kernels F11-F12)
- Cymatics & Resonance: standing waves, Fourier transform (bridge transition resonance)
- Swarm Intelligence: decentralized interactions producing global behavior (equation forest as CAS)
- Twistor Theory: emergent dimensionality from relationships (Genome18 as emergent coordinate system)
- Visualization: Unreal Engine Niagara particle systems (potential rendering backend)
