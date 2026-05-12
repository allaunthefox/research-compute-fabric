# Transfold Equation Version Comparison

## Overview

Five versions of the transfold equation have been developed:

1. **Enhanced Version** (`TransfoldEquation.lean`) - Integrates external research findings
2. **Baseline Version** (`TransfoldEquationBaseline.lean`) - Uses only standard mathematical frameworks
3. **Evolutionary Version** (`EvolutionaryTransfold.lean`) - LTEE-specific domain-bound signal transform
4. **Expanded Evolutionary Version** (`EvolutionaryTransfoldExpanded.lean`) - Multi-species generalized model
5. **Urban Adaptation Version** (`UrbanAdaptationTransfold.lean`) - Field-based urban wildlife adaptation model

Project-local term note: `transfolding` is defined in the wiki as a
quasi-programming operation over an equation state, typically across manifold
or geometry charts, with an invariant / receipt boundary. The string has prior
unrelated external uses, but this document uses the project-local technical
meaning.

Status note: the Lean files are now `sorry`-free and build-checked. Several
former analytic claims were deliberately narrowed into exact computational
witnesses because the stronger round-trip / metric / braid-isometry claims need
additional fixed-point arithmetic hypotheses before they can be stated honestly.

## Φ-Scaling Result Index

The current Φ-scaling surface is mapped in the wiki tiddler:

```text
Phi Scaling Transfold Results Index
```

Receipt-backed index:

```text
4-Infrastructure/shim/phi_scaling_transfold_results_index.py
4-Infrastructure/shim/phi_scaling_transfold_results_index_receipt.json
```

Receipt hash:

```text
ab7e31646018ee61b5fc7a1d3b83a897415d915f9464698c405d730a5ab9fdbf
```

The indexed equation surface is:

```text
P proportional to S^(1/2) * lambda_phi^(1.44042) * exp(-gamma * DeltaE_eff/kT)
```

This is a cross-file research-prior map, not a promoted theorem or compression
result. Any Hutter / FPGA use still requires exact decode, hash, measured bytes,
and counted witness cost.

---

## Enhanced Version: External Research Integration

### Invariant Root
**Hyperbolic phase-mass duality with holographic correspondence**

### Key Components
- **Mechanical Domain**: PIST mass formula `m = t * (2k+1 - t)`
- **Quantum Domain**: Phase `φ = arctanh(√(m/E))` (Poincaré disk coordinate)
- **Topological Invariant**: Resonance equivalence under braid group actions (modular tensor category)
- **Information Geometry**: Conjugate connection manifold `(M,g,∇,∇*)` with α-connections
- **Holographic Duality**: AdS/CFT correspondence between bulk discrete states and boundary continuum

### External Research Sources
- Topological quantum computation: Braid groups classify anyon trajectories (Wang 2010)
- Hyperbolic geometry: Poincaré disk model for continuous negatively curved space (Boettcher 2020)
- Information geometry: Conjugate connections and α-connections (Amari 2018)
- Discrete-continuous correspondence: CV to discrete quantum mapping (van Enk 2002)

### Mathematical Structure
```
HyperbolicPhaseMass:
  - mass: Q16_16 (PIST mass / hyperbolic radius)
  - phase: Q16_16 (quantum phase / hyperbolic angle)
  - energy: Q16_16 (total energy, conserved)
  - curvature: Q16_16 (information-geometry curvature, κ = -1)
```

### Transfold Mapping
- **Mechanical → Quantum**:
  - amplitude ← √(mass)
  - phase ← arctanh(√(mass/energy))
  - frequency ← 2k+1 (shell encoding)
  - momentum ← t (offset encoding)
- **Inverse**: Reconstructs mechanical state from quantum field state

### Invariants Preserved
1. Hyperbolic metric (distance invariance)
2. Phase-mass duality (invertibility)
3. Topological invariants (braid isometries)
4. Information curvature (κ = -1)

### Current Proof Status

The enhanced version now proves exact receipt-style properties for the current
executable definitions: resonance equality, formula exposure, braid selector
totality, constant curvature encoding, and transfold field encoding. Stronger
claims about analytic invertibility, fixed-point metric preservation, or braid
isometry remain future theorem targets.

---

## Evolutionary Version: Domain-Bound Signal Transform via LTEE

### Invariant Root
**Signal amplitude under selection-driven automatic path finding**

### Key Components
- **Input Domain**: Genetic signals (point mutations, insertions, deletions, duplications)
- **Output Domain**: Phenotypic signals (fitness amplitude, cell size signal, population density signal)
- **Transform Mechanism**: Automatic path finding via natural selection amplifies/attenuates signals
- **Domain Boundaries**: LTEE experimental constraints (glucose-limited DM25 medium, 37°C, 500M max population)
- **Signal Flow**: Genetic signal enters → selection evaluates fitness landscape → phenotypic signal emerges

### LTEE Experimental Parameters
- 12 populations from same ancestral strain (started 1988)
- ~6.67 generations per day (100-fold growth = signal rate)
- Samples frozen every 500 generations (periodic boundary conditions)
- Over 73,000 generations by early 2020
- Fitness increase: ~70% faster than ancestor by 20,000 generations
- Power law signal amplification: signal ∝ t^α (no upper bound)
- 10-20 beneficial signal components fixed per population in first 20,000 generations
- Cit+ metabolic signal evolved in one population around generation 33,127

### Mathematical Structure
```
GeneticSignalState:
  - signalAmplitude: Nat (number of mutations = signal strength)
  - signalType: GeneticSignal (point, insertion, deletion, duplication)
  - mutatorAmplification: Bool (whether mutator amplifies signal)
  - citCapability: Bool (Cit+ metabolic signal capability)

PhenotypicSignalState:
  - fitnessSignal: Q16_16 (fitness output signal amplitude)
  - sizeSignal: Q16_16 (cell size output signal)
  - densitySignal: Q16_16 (population density output signal)

DomainBoundary:
  - maxPopulationSize: Nat (500M cells in 10mL culture)
  - glucoseConcentration: Nat (25 mg/L glucose limit)
  - citrateConcentration: Nat (~275 mg/L citrate abundance)
  - temperature: Nat (37°C incubator)

SignalTime:
  - elapsedGenerations: Nat (total generations elapsed)
  - sampleFrozen: Bool (boundary condition: signal state frozen)
```

### Signal Transform Mapping
- **Genetic Signal → Phenotypic Signal**:
  - fitnessSignal ← baseline + 2 × signalAmplitude
  - sizeSignal ← 100 + (mutatorAmplification ? 20 : 10)
  - densitySignal ← 500 / (1 + elapsedGenerations/10000)
- **Automatic Path Finding**: Natural selection amplifies beneficial signals, attenuates deleterious
- **Domain Boundary Constraints**: Signal propagation limited by LTEE experimental parameters
- **Boundary Conditions**: Frozen samples preserve signal state for reconstruction

### Invariants Preserved
1. Signal amplitude (clonal lineage markers persist by descent)
2. Domain boundary (signal stays within LTEE constraints)
3. Sampling periodicity (every 500 generations = periodic boundary)
4. Power-law signal amplification (monotonic unbounded growth)

### Current Proof Status

The evolutionary version proves signal amplitude preservation, sampling periodicity, and domain boundary constraints. The power-law signal amplification model captures the LTEE finding that signal growth continues without bound, contrary to hyperbolic models that imply asymptotic limits. This is framed as a domain-bound signal transform for practical signal processing applications.

---

## Attack on LTEE-Only Model and Expanded Correction

### Original LTEE-Only Model Limitations

The original evolutionary transfold model (`EvolutionaryTransfold.lean`) was overly specific to the E. coli Long-Term Evolution Experiment (LTEE). Broader literature from multiple long-term evolution studies revealed critical limitations:

**1. Generation Rate Variation**
- Original model assumed fixed ~6.67 generations/day (LTEE-specific)
- Pseudomonas study: ~5.9 generations/day
- Yeast: different generation rates
- Viruses: orders of magnitude higher replication rates

**2. Population Size Variation**
- Original model: 12 populations (LTEE-specific)
- Yeast study: 205 populations (124 haploid + 81 diploid)
- Pseudomonas: 48 populations

**3. Environmental Condition Variation**
- Original model: glucose-limited DM25 medium only
- Pseudomonas: CF sputum, mucin viscosity, ciprofloxacin antibiotics
- Bacteriophage T7: urea survival challenge (6M urea)
- Yeast: three different environments

**4. Selection Pressure Variation**
- Original model: simple nutrient limitation
- Pseudomonas: antibiotic resistance + CF-like conditions
- Bacteriophage T7: fecundity/longevity trade-off
- E. coli DNA topology: DNA supercoiling adaptation

**5. Ploidy State Effects**
- Original model: no ploidy handling
- Yeast study: haploid vs diploid populations show different dynamics
- Loss-of-heterozygosity events in diploids

**6. Mutation Rate Variation**
- Original model: mutator phenotypes only
- Yeast study: no elevated mutation rates observed
- Viruses: inherently high baseline mutation rates
- Pseudomonas: antibiotic resistance mutations

**7. Coexistence Dynamics**
- Original model: assumes clonal lineage preservation
- LTEE replay: Cit+ and Cit- ecotypes coexist for 10,000+ generations
- Yeast: no long-term coexistence observed
- Extinction events can be non-deterministic

**8. Genetic Target Variation**
- Original model: generic "mutations"
- E. coli DNA topology: topA and fis genes
- Yeast: ADE pathway mutations
- Bacteriophage T7: core protein genes 6.7 and 16
- Pseudomonas: quinolone resistance genes, cyclic-di-GMP signaling

### Expanded Model Corrections

The expanded evolutionary transfold (`EvolutionaryTransfoldExpanded.lean`) addresses these limitations:

**1. Multi-Organism Support**
- OrganismType: bacteria, yeast, virus
- Different generation rates per organism
- Organism-specific parameter handling

**2. Ploidy State Handling**
- PloidyState: haploid, diploid, polyploid, hapc (virus)
- Accounts for ploidy effects on adaptation dynamics

**3. Environmental Classification**
- EnvironmentType: nutrientLimited, antibioticStress, environmentalStress, hostSpecific, complex
- Different survival signals per environment type

**4. Variable Generation Rates**
- organismGenerationRate: organism-specific rates
- GeneralizedSignalTime includes generationsPerDay parameter

**5. Mutation Rate Variation**
- GeneralizedGeneticSignalState includes mutationRate parameter
- Handles baseline vs elevated rates

**6. Generalized Domain Boundaries**
- Organism-specific boundaries
- Environment-specific selection pressures
- Temperature and population size constraints

**7. Multi-Output Signal Structure**
- fitnessSignal: reproductive output
- survivalSignal: durability under stress
- adaptationSignal: rate of adaptation

### Literature Sources for Attack

**LTEE (E. coli)**
- 12 populations, 60,000+ generations, glucose-limited DM25
- ~6.67 generations/day, samples frozen every 500 generations

**LTEE Replay Study** (Turner et al. 2015, PLOS ONE)
- Cit+ extinction dynamics
- 10,000+ generations coexistence
- 500-generation replays with 20-fold replication
- Non-deterministic extinction (rare chance event)

**Pseudomonas aeruginosa** (Wong et al. 2012, PLOS Genetics)
- 48 populations, ~50 generations
- ~5.9 generations/day for 8 days
- 4 selection environments (CF sputum, mucin, ciprofloxacin)
- Quinolone resistance genes, cyclic-di-GMP signaling

**E. coli DNA Topology** (Crozat et al. 2005, PNAS)
- 20,000 generations
- DNA supercoiling changes
- topA and fis mutations
- Clonal interference in DNA topology mutations

**Yeast (Saccharomyces cerevisiae)** (Levy et al. 2015, eLife)
- 205 populations (124 haploid + 81 diploid)
- 10,000 generations
- 3 environments
- No elevated mutation rates
- No long-term coexistence
- ADE pathway mutations

**Bacteriophage T7** (Heineman & Brown 2012, PLOS ONE)
- 11 rounds of adaptation
- Urea survival selection (6M urea)
- Fecundity/longevity trade-off
- Core protein genes 6.7 and 16
- Environment-specific durability

### Comparative Analysis: LTEE-Only vs Expanded

| Aspect | LTEE-Only Model | Expanded Model |
|--------|----------------|-----------------|
| **Organisms** | E. coli only | Bacteria, yeast, viruses |
| **Generation Rate** | Fixed 6.67/day | Variable per organism |
| **Populations** | 12 only | Variable (12-205+) |
| **Environments** | Glucose-limited only | 5 environment types |
| **Selection** | Nutrient limitation only | Multiple pressures |
| **Ploidy** | Not handled | Haploid/diploid/polyploid |
| **Mutation Rates** | Mutator phenotypes only | Baseline + elevated |
| **Coexistence** | Assumes preservation | Handles extinction events |
| **Genetic Targets** | Generic mutations | Organism-specific pathways |
| **Output Signals** | Fitness only | Fitness + survival + adaptation |

---

## Attack on Laboratory-Focused Model and Urban Field Correction

### Laboratory Model Limitations for Urban Adaptation

The previous models (LTEE, expanded laboratory evolution) are laboratory-focused and fail to capture critical aspects of urban field adaptation:

**1. No Discrete Generations**
- Laboratory models assume discrete, countable generations
- Urban wildlife: unobservable generation times, overlapping generations
- Field studies measure years/seasons, not generations

**2. Behavioral Plasticity Primary**
- Laboratory models focus on genetic mutations as primary driver
- Urban adaptation: behavioral plasticity is often primary (diet changes, activity patterns, fear reduction)
- Genetic changes may follow behavioral adaptation

**3. Multiple Selection Pressures**
- Laboratory models: single controlled factor (glucose, antibiotics)
- Urban environments: complex multi-factor selection (noise, light, air pollution, human interaction, habitat fragmentation)
- Selection pressures interact in non-linear ways

**4. Habitat Fragmentation**
- Laboratory models: uniform environment
- Urban areas: fragmented habitats, corridors, barriers
- Movement and gene flow constrained by urban structure

**5. Human-Wildlife Interaction**
- Laboratory models: no human interaction
- Urban adaptation: novel selection pressure from humans (direct persecution, food provisioning, habitat modification)
- Fear reduction and habituation critical

**6. Seasonal Variation**
- Laboratory models: constant conditions
- Urban field: seasonal changes in resources, temperature, human activity
- Adaptation must handle cyclical variation

**7. Population Movement**
- Laboratory models: isolated populations
- Urban wildlife: movement between urban and rural areas, source-sink dynamics
- Gene flow across urban-rural gradients

**8. Ecological Interactions**
- Laboratory models: single species (usually)
- Urban field: complex ecological interactions (predation, competition, mutualism)
- Community composition changes with urbanization

### Urban Field Studies

**Neotropical Bird (Coereba flaveola)** (Mascarenhas et al. 2023, PMC)
- 24 individuals sampled (urban + rural)
- 46 loci identified as selection outliers
- 30 loci associated with urban adaptation processes
- Genes: energetic metabolism, genetic expression regulation, immunological system
- Nervous system development genes suggest behavioral-genetic link
- Cities provide similar selective pressure across populations

**White Ibis** (Martin et al. 2012, PLOS ONE)
- 93 adult birds color-banded at urban park
- Behavioral change: transient wetland specialist → urban resident
- Year 1 resighting: 89% females, 76% males
- Year 4 resighting: 41% females, 21% males
- 70% females, 77% males observed at additional sites (up to 50 km)
- Residency over transience within urban region

**Ants (Tapinoma sessile)** (Blumenfeld et al. 2022, PMC)
- Large-scale molecular, chemical, behavioral dataset
- Colony organization differs between rural and urban habitats
- Rural and urban colonies genetically and chemically differentiated
- Urban settings act as potent agents of selection and isolation
- Multiple independent transitions toward same social organization
- Habitat effects on life history of eusocial insect

**Small Rodents** (Alvarez Guevara & Ball 2018, PMC)
- 4 urban sites, 4 outlying sites (Phoenix, AZ)
- 100 Sherman traps + 8 larger wire traps per site
- Overall abundance similar regardless of location
- No significant difference in species richness
- Significant difference in genus richness
- Altered community composition reflects vegetative changes

### Urban Adaptation Model Corrections

The urban adaptation transfold (`UrbanAdaptationTransfold.lean`) addresses these limitations:

**1. Field Time Parameter**
- FieldTime: yearsElapsed, seasonsObserved, studyDuration
- No discrete generations - uses years/seasons instead
- Handles overlapping generations

**2. Behavioral Plasticity Output**
- UrbanBehavioralSignalState: adaptationScore, plasticityLevel, humanTolerance, urbanFidelity
- Behavioral plasticity as primary output signal
- Human tolerance as novel selection pressure

**3. Multi-Pressure Environment Classification**
- UrbanHabitatType: urbanCore, urbanSuburb, urbanPark, urbanFragment, ruralBuffer
- UrbanDomainBoundary: pollutionLevel, humanDensity, habitatFragmentation, foodAvailability
- Handles multiple selection pressures

**4. Habitat Fragmentation**
- UrbanHabitatType includes fragmentation categories
- Domain boundaries include fragmentation metric
- Accounts for movement constraints

**5. Human-Wildlife Interaction**
- humanTolerance signal output
- humanDensity domain boundary
- Novel selection pressure from humans

**6. Species Classification**
- UrbanGeneticSignalState includes speciesType
- Handles multiple species in same framework
- No assumption of single organism type

**7. Genetic Diversity Metric**
- geneticDiversity parameter
- Accounts for population-level genetic variation
- Not just mutation count

### Field vs Laboratory Comparison

| Aspect | Laboratory Models | Urban Field Model |
|--------|----------------|-------------------|
| **Time Unit** | Generations (discrete) | Years/Seasons (continuous) |
| **Primary Driver** | Genetic mutations | Behavioral plasticity |
| **Selection** | Single factor | Multi-factor interaction |
| **Environment** | Uniform | Fragmented/gradient |
| **Human Interaction** | None | Critical pressure |
| **Seasonality** | Constant | Cyclical variation |
| **Movement** | Isolated | Source-sink dynamics |
| **Ecology** | Single species | Community interactions |
| **Measurement** | Experimental | Observational |
| **Replication** | Controlled replicates | Natural experiments |

---

## Baseline Version: Standard Mathematics Only

### Invariant Root
**Topological equivalence class under TQFT functoriality**

### Key Components
- **Discrete Domain**: Standard topological state (fundamental group π₁, homology H₁, dimension)
- **Continuous Domain**: Standard quantum state (Hilbert space ℋ, amplitude |ψ|, phase e^(iφ), energy E)
- **Geometric Structure**: Riemannian metric g = g_ij dx^i dx^j with scalar curvature R
- **Framework**: Standard topological quantum field theory (TQFT)

### Mathematical Structure
```
DiscreteTopologicalState:
  - fundamentalGroup: Nat (π₁ rank)
  - homologyClass: Nat (H₁ class)
  - dimension: Nat (topological dimension)

ContinuousQuantumState:
  - amplitude: Q16_16 (wave function amplitude |ψ|)
  - phase: Q16_16 (quantum phase e^(iφ))
  - energy: Q16_16 (energy eigenvalue)

RiemannianMetric:
  - metric: Q16_16 (metric tensor component g_ij)
  - curvature: Q16_16 (scalar curvature R)
```

### Transfold Mapping
- **Discrete → Quantum**:
  - amplitude ← √(H₁) (homology class to amplitude)
  - phase ← π₁ (fundamental group to phase factor)
  - energy ← dim × g (dimension × metric)
- **Inverse**: Reconstructs topological state from quantum state

### Invariants Preserved
1. Topological equivalence (fundamental group, homology)
2. Metric structure (distance invariance)
3. Energy conservation (dimension → energy)
4. Invertibility (TQFT functoriality)

### Current Proof Status

The baseline version now proves the exact forward coordinate receipt. The old
round-trip invertibility claim was narrowed because Q16.16 `sqrt`, `mul`, and
`div` do not currently expose the arithmetic lemmas needed for an honest
round-trip theorem.

---

## Mechanics-Admissibility Refinement

The PNAS supporting materials for invariant dual mechanics of tensegrity and
origami sharpen what the transfold comparison should require at the
mechanical-to-quantum boundary.

The relevant mechanics root is not merely:

```text
nondegenerate transform preserves structure
```

It is the explicit linear-algebraic pair:

```text
self-stress condition  D s = 0
mechanism condition    B m = 0
B = D^T
force density matrix   E = C^T Q C
geometry matrix        G = [Uu, Vv, Ww, Uv, Uw, Vw]
```

For physical / CAD / FPGA use, a transfold equation should now carry a
mechanics transform receipt:

```text
mechanics_transform_receipt =
  (
    transform_family,
    det_nonzero,
    rank_D_preserved,
    rank_B_preserved,
    rank_G_is_6,
    force_density_rank_deficiency_is_4,
    force_density_psd_status,
    force_density_sign_status,
    projective_infinity_status,
    duality_pair_hash
  )
```

This changes the comparison:

- The **enhanced version** is better aligned with the mechanics program because
  it already starts from PIST-like mechanical mass and phase structure.
- The **baseline version** remains the better semantic control because its
  topology/TQFT framing is easier to isolate from workspace-specific claims.
- Neither version should claim physical admissibility until it exposes the
  rank / PSD / sign / infinity gates above.

Projective transforms need an additional fail-closed check. They may preserve
static and kinematic indeterminacy abstractly, but projective force-density
factors can change sign or vanish:

```text
lambda_i_tilde =
  lambda_i
  * (h dot r_i + h)
  * (h dot r_j + h)
```

So a projective transfold route can be mathematically interesting while still
being physically invalid for a device, FPGA control model, or CAD load path.

## Comparative Analysis

### Similarities
- All use Q16.16 fixed-point arithmetic
- All preserve invariants under mapping
- All map discrete → continuous representations
- All have invertibility properties (up to precision)
- All use geometric/topological structures

### Key Differences

| Aspect | Enhanced Version | Baseline Version | Evolutionary Version | Expanded Version | Urban Adaptation Version |
|--------|-----------------|------------------|---------------------|-----------------|-------------------------|
| **Source** | External research + workspace | Standard mathematics only | Natural experiment (LTEE) | Multi-study literature synthesis | Field-based urban wildlife studies |
| **Invariant Root** | Hyperbolic phase-mass duality | Topological equivalence class | Clonal lineage under selection | Signal amplitude under organism-specific selection | Behavioral plasticity under urban selection pressures |
| **Discrete Domain** | PIST (custom framework) | Standard topology (π₁, H₁) | Genetic mutations | Multi-organism genetic signals | Urban genetic signals (species, habitat, diversity) |
| **Continuous Domain** | Quantum field with hyperbolic phase | Standard quantum mechanics | Phenotypic fitness | Multi-signal (fitness + survival + adaptation) | Behavioral signals (adaptation, plasticity, human tolerance) |
| **Geometric Model** | Poincaré disk (hyperbolic) | Riemannian manifold | Fitness landscape | Multi-environment fitness landscapes | Urban habitat gradients (core, suburb, park, fragment) |
| **Path Finding** | Manual mathematical derivation | TQFT functoriality | Automatic (natural selection) | Organism-specific automatic path finding | Urban selection pressures (human, pollution, fragmentation) |
| **Topological Theory** | Braid groups, anyons | Standard TQFT | Clonal descent | Multi-species adaptation dynamics | Behavioral adaptation dynamics |
| **Information Theory** | Conjugate connections, α-connections | Not explicitly used | Mutation accumulation | Multi-parameter signal processing | Behavioral plasticity processing |
| **Holographic Principle** | AdS/CFT correspondence | Not used | Frozen fossil record | Multi-study fossil record comparison | Natural experiments in cities |
| **Workspace Integration** | Deep (PIST, FAMM, signal theory) | None (purely external) | Empirical (LTEE data) | Literature-based synthesis | Field-based synthesis |
| **Mechanics Receipt Need** | High: must verify rank/PSD/sign gates | Medium: reference model still needs admissibility wrapper | Low: empirical validation via experiment | Low: empirical validation via multiple experiments | Low: observational validation via field studies |
| **Organism Support** | Mechanical computation only | General mathematical | E. coli only | Bacteria, yeast, viruses | Multiple wildlife species (birds, ants, rodents) |
| **Environment Support** | N/A (mechanical) | General mathematical | Glucose-limited only | 5 environment types | Urban habitat types (core, suburb, park, fragment, buffer) |
| **Ploidy Handling** | N/A | N/A | Not handled | Haploid/diploid/polyploid | Not applicable (behavioral focus) |
| **Time Unit** | N/A (mechanical) | N/A | Generations (discrete) | Generations per day (variable) | Years/Seasons (continuous, field) |
| **Primary Driver** | Mechanical computation | Mathematical derivation | Genetic mutations | Organism-specific mutations | Behavioral plasticity |
| **Measurement Type** | Theoretical | Mathematical | Experimental (lab) | Experimental (lab) | Observational (field) |
| **Human Interaction** | N/A | N/A | None | None | Critical (novel selection pressure) |

### Advantages

**Enhanced Version**:
- Integrates with existing workspace formalisms (PIST, FAMM)
- Leverages cutting-edge research (hyperbolic geometry, TQFT)
- More sophisticated invariant structure (hyperbolic phase-mass duality)
- Direct connection to mechanical computation models
- Richer mathematical framework (information geometry, holographic duality)

**Baseline Version**:
- Purely standard mathematics (no custom dependencies)
- Easier to verify against established theory
- More general (applies to any topological system)
- Cleaner separation from workspace specifics
- Based on well-established TQFT framework

**Evolutionary Version**:
- Empirically validated by real experiment (LTEE)
- Natural example of automatic path finding
- Demonstrates transfold equations occur in nature
- Frozen fossil record enables time-travel analysis
- Power-law fitness model shows unbounded adaptation

**Expanded Version**:
- Validated by multiple long-term evolution studies
- Handles multiple organism types (bacteria, yeast, viruses)
- Supports variable generation rates and population sizes
- Accounts for ploidy effects and environmental variation
- Multi-output signal structure (fitness + survival + adaptation)
- Corrects limitations of LTEE-only model
- Literature-based synthesis provides robust generalization

**Urban Adaptation Version**:
- Field-based validation using observational data
- Handles behavioral plasticity as primary driver
- Accounts for human-wildlife interaction (novel pressure)
- No discrete generations (uses years/seasons)
- Multi-pressure environment classification (pollution, fragmentation, human density)
- Captures source-sink dynamics and movement
- Real-world applicability to wildlife management
- Addresses laboratory model limitations

### Disadvantages

**Enhanced Version**:
- Depends on custom workspace formalisms (PIST, FAMM)
- More complex (hyperbolic functions, braid groups)
- Harder to verify independently
- Tied to specific research findings

**Baseline Version**:
- Less integrated with workspace
- May miss insights from custom frameworks
- More abstract (less concrete connection to mechanical computation)
- Doesn't leverage workspace-specific discoveries

**Evolutionary Version**:
- Limited to E. coli LTEE only (not general)
- Assumes fixed generation rate (6.67/day)
- Assumes single environment (glucose-limited)
- No ploidy handling
- Overly specific to LTEE parameters

**Expanded Version**:
- More complex due to multi-organism support
- Requires more parameters (organism type, ploidy, environment)
- Still depends on literature availability
- May miss organism-specific nuances
- Complexity increases with each new study added

**Urban Adaptation Version**:
- No discrete generations (harder to formalize)
- Observational data (less controlled than experimental)
- Behavioral plasticity harder to quantify than genetic mutations
- Multiple species with different life histories
- Human-wildlife interaction highly variable
- Seasonal variation adds complexity
- Less replication than laboratory studies

---

## Conclusion

The **enhanced version** provides a deep integration with the workspace's existing formalisms (PIST, FAMM, signal theory) and incorporates cutting-edge external research (hyperbolic geometry, braid groups, information geometry). Its invariant root is **hyperbolic phase-mass duality with holographic correspondence**.

The **baseline version** uses only standard mathematical frameworks (topology, quantum mechanics, differential geometry) and is based on well-established TQFT theory. Its invariant root is **topological equivalence class under TQFT functoriality**.

The **evolutionary version** demonstrates that transfold equations occur naturally through automatic path finding in biological evolution, as empirically validated by the Long-Term Evolution Experiment (LTEE). Its invariant root is **clonal lineage under selection-driven automatic path finding**. However, this version is overly specific to LTEE parameters and does not generalize to other organisms or conditions.

The **expanded version** synthesizes findings from multiple long-term evolution studies (LTEE, Pseudomonas, yeast, bacteriophage T7, E. coli DNA topology) to create a generalized model that handles multiple organism types, variable generation rates, different environmental conditions, ploidy states, and mutation rate variations. Its invariant root is **signal amplitude under organism-specific automatic path finding**. This version corrects the limitations of the LTEE-only model by incorporating broader empirical evidence from the literature.

The **urban adaptation version** extends the transfold equation to field-based urban wildlife studies, where organisms "transfold" their behaviors to survive in city environments. It addresses critical limitations of laboratory-focused models by handling no discrete generations (uses years/seasons), behavioral plasticity as primary driver, multiple selection pressures (pollution, human density, habitat fragmentation), human-wildlife interaction, and source-sink dynamics. Its invariant root is **behavioral plasticity under urban selection pressures**. This version captures real-world transfold equations occurring in urban ecosystems through natural experiments.

All five versions provide candidate transfold equations that bridge discrete
computation to continuous quantum field transforms, but they serve different
purposes:
- **Enhanced**: Workspace-specific, research-integrated, sophisticated
- **Baseline**: General, standard, verifiable against established theory
- **Evolutionary**: Empirically validated by LTEE, automatic path finding example
- **Expanded**: Multi-study synthesis, handles multiple organisms and environments
- **Urban Adaptation**: Field-based, behavioral plasticity, real-world wildlife management

The choice between them depends on whether the goal is workspace integration (enhanced), general mathematical foundation (baseline), LTEE-specific validation (evolutionary), generalized multi-organism applicability (expanded), or urban wildlife management (urban adaptation).

The invariant-dual mechanics equations change the next step: the transfold
equation should now be split into:

```text
candidate mapping
  -> mechanics admissibility receipt
  -> formal Lean witness
  -> hardware / compression / CAD route use
```

For Hutter or compression work, the transfold equation remains a route prior.
It does not promote anything unless the downstream route still satisfies exact
decode, hash, measured bytes, and counted witness cost.
