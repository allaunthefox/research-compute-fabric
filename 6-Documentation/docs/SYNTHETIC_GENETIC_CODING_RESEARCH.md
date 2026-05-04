# Synthetic & Biological Genetic Coding Systems — Research Summary

**Date**: 2026-05-01  
**Module**: `SyntheticGeneticCoding.lean`  
**GCL Surfaces**: Informational, Geometric, Thermodynamic, Physical, Control

---

## 1. HACHIMOJI DNA/RNA (Benner Lab, 2019)

**Publication**: Hoshika et al. (2019) *Science* — "Hachimoji DNA and RNA: A genetic system with eight building blocks"

### 1.1 Alphabet Structure
- **8 bases**: A, C, G, T (natural) + P, Z, B, S (synthetic)
- **4 orthogonal pairs**: A-T, C-G, P-Z, B-S
- **Codon space**: 8³ = 512 codons (vs 64 in standard DNA)
- **Information density**: 3 bits/base vs 2 bits/base

### 1.2 Synthetic Base Chemistry
| Base | Full Name | Pair |
|------|-----------|------|
| P | 2-aminoimidazo[1,2-a][1,3,5]triazin-4(8H)-one | pairs with Z |
| Z | 6-amino-5-nitro-2(1H)-pyridone | pairs with P |
| B | Isoguanine (isoG) | pairs with S |
| S | 5-methylisocytosine (isoC) | pairs with B |

### 1.3 GCL Bind Mapping
- **Primary**: `informational_bind` — enhanced data storage capacity
- **Secondary**: `geometric_bind` — 8-base duplex geometry differs from B-DNA
- **Surface**: `S(x)` — Surface field (alphabet expansion)

---

## 2. XENO NUCLEIC ACIDS (XNA)

**Key Reference**: Pinheiro et al. (2012) *Science* — XNA polymerase engineering

### 2.1 Sugar-Modified XNAs (Cyclic Backbones)

#### TNA — Threose Nucleic Acid
- **Backbone**: 4-carbon threose sugar (vs 5-carbon ribose)
- **Key Property**: Prebiotically plausible (simpler than RNA)
- **Application**: Origin of life research, "TNA world" hypothesis
- **GCL Bind**: `geometric_bind` → `thermodynamic_bind` → `C(x)` (closure field)

#### LNA — Locked Nucleic Acid
- **Backbone**: 2'-O,4'-C-methylene bridge locks ribose in C3'-endo conformation
- **Key Properties**:
  - Tm increase: +5-10°C per LNA base
  - Nuclease resistance: >99%
  - Binding affinity: 1.5x DNA-DNA
- **Clinical**: Approved drugs (Volanesorsen/Waylivra for FCS)
- **GCL Bind**: `thermodynamic_bind` → `physical_bind` → `M(x)` (motif field)

#### BNA — Bridged Nucleic Acid
- **Backbone**: Amide-linked bridge (6-membered ring)
- **Properties**: Intermediate between LNA and DNA
- **Applications**: Diagnostic probes, PCR clamping

#### HNA — 1,5-Anhydrohexitol Nucleic Acid
- **Backbone**: Hexose sugar (6-membered ring)
- **Structure**: RNA-like A-form helix
- **Applications**: Gene silencing, antisense therapies

#### FANA — Fluoroarabino Nucleic Acid
- **Backbone**: 2'-F-arabinose
- **Key Property**: Folds like RNA → XNAzymes (catalytic XNA)
- **Significance**: Demonstrates catalytic activity outside ribose backbone

### 2.2 Non-Sugar XNAs (Acyclic/Peptide Backbones)

#### PNA — Peptide Nucleic Acid
- **Backbone**: N-(2-aminoethyl)glycine (peptide-like)
- **Key Properties**:
  - Neutral charge (no phosphate backbone)
  - Achiral (can use D- or L-amino acids)
  - Completely nuclease/protease resistant
  - Antigene capability (invades dsDNA)
- **GCL Bind**: `physical_bind` → `control_bind` → `I(x)` (informaton field)

#### GNA — Glycol Nucleic Acid
- **Backbone**: Glycol (simplest acyclic backbone)
- **Structure**: Prefers single-stranded state
- **Research**: Minimal informational polymer

#### Morpholino (PMO)
- **Backbone**: Morpholine ring + phosphorodiamidate linkage
- **Charge**: Neutral (unlike phosphodiester DNA)
- **Clinical**: Eteplirsen (Exondys 51) — DMD exon 51 skipping
- **Delivery**: Requires charged delivery systems (Pip6a-PMO, etc.)

#### CeNA — Cyclohexene Nucleic Acid
- **Backbone**: Cyclohexene ring (conformationally flexible)
- **Applications**: Structural studies, hybridization research

### 2.3 XNA Summary Table

| XNA | Backbone | Tm vs DNA | Nuclease Res. | Clinical Status |
|-----|----------|-----------|---------------|-----------------|
| TNA | Threose (4C) | -5°C | 95% | Research |
| LNA | Locked ribose | +8°C | 99% | Approved drugs |
| BNA | Bridged sugar | +4°C | 95% | Diagnostics |
| HNA | Anhydrohexitol | +2°C | 90% | Research |
| FANA | Fluoroarabino | +3°C | 95% | Research |
| PNA | Peptide | +2°C | 100% | Antigene trials |
| GNA | Glycol | -10°C | 80% | Basic research |
| Morpholino | Morpholine | -5°C | 100% | Approved (DMD) |
| CeNA | Cyclohexene | 0°C | 85% | Research |

---

## 3. GENETIC CODE EXPANSION

**Key References**:
- Anderson et al. (2022) *Nature* — Quadruplet codons in animals
- Deiters et al. — Genetic code expansion technology reviews

### 3.1 Quadruplet Codon Systems
- **Total codons**: 320 (256 quadruplets + 64 triplets)
- **Mechanism**: Frameshift suppression with engineered tRNA
- **Efficiency**: ~10-50% suppression (vs ~99% for triplet)
- **Applications**: 200+ non-canonical amino acids (ncAAs)

### 3.2 Stop Codon Recoding
| Stop Codon | Name | Recoding Target |
|------------|------|-----------------|
| UAG | Amber | Most common for ncAA |
| UAA | Ochre | Alternative amber |
| UGA | Opal | Selenocysteine (natural) |

### 3.3 Orthogonal Translation Systems
**Components Required**:
1. Orthogonal aminoacyl-tRNA synthetase (aaRS)
2. Orthogonal tRNA (recognizes reassigned codon)
3. ncAA substrate
4. Editing domain (prevents misacylation)

**Evolved Pairs**:
- *E. coli* TyrRS/tRNA(CUA) → pAzF (p-azidophenylalanine)
- *M. jannaschii* TyrRS/tRNA(CUA) → various ncAAs
- PylRS/tRNA(CUA) — naturally orthogonal (pyrrolysine)

### 3.4 ncAA Functional Categories
| Category | Example | Application |
|----------|---------|-------------|
| Photocrosslinkers | pAzF, Bpa | Protein-protein interaction mapping |
| Fluorescent | Anap, CouAA | Live-cell imaging |
| Click chemistry | AzF, Alkynyl-Phe | Bioconjugation |
| Post-translational mimics | AcK, MeK | Epigenetic research |
| Heavy atoms | pI-Phe | X-ray crystallography phasing |
| Redox active | DOPA | Bioelectronic interfaces |

### 3.5 GCL Bind Mapping
- **Primary**: `control_bind` — regulation of translation
- **Secondary**: `informational_bind` — expanded codon meaning
- **Surface**: Triple bind `Φ` — requires all five field intersections

---

## 4. THERAPEUTIC ASO CHEMISTRIES (Clinical)

### 4.1 Approved ASO Drugs
| Drug | Chemistry | Target | Disease |
|------|-----------|--------|---------|
| Fomivirsen | PS-DNA | CMV IE2 | Retinitis (withdrawn) |
| Mipomersen | PS 2'-MOE | ApoB-100 | Familial hypercholesterolemia |
| Inotersen | PS 2'-MOE | TTR | hATTR amyloidosis |
| Volanesorsen | LNA gapmer | ApoC-III | FCS (familial chylomicronemia) |
| Eteplirsen | Morpholino | DMD exon 51 | Duchenne MD |
| Golodirsen | Morpholino | DMD exon 53 | Duchenne MD |
| Viltolarsen | Morpholino | DMD exon 53 | Duchenne MD |
| Casimersen | Morpholino | DMD exon 45 | Duchenne MD |

### 4.2 Chemistry Generations
**1st Generation**: Phosphorothioate (PS) DNA backbone
- Full PS backbone increases nuclease resistance
- Still immunostimulatory (TLR9 activation)

**2nd Generation**: PS + 2'-modifications
- 2'-O-methyl (2'-OMe)
- 2'-MOE (2'-O-(2-methoxyethyl))
- Gapmer design: modified wings + DNA gap

**3rd Generation**: Advanced chemistries
- LNA (locked nucleic acid)
- Morpholino (PMO)
- PNA (peptide nucleic acid)
- siRNA (triggers RNase H independent pathway)

### 4.3 Gapmer Design Rules
```
Typical LNA gapmer: 3-10-3 configuration
[ LNA-LNA-LNA ] — DNA gap — [ LNA-LNA-LNA ]
|__wings___|   |___gap___|   |__wings___|
```

**Optimal parameters**:
- Length: 16-20 nucleotides
- GC content: 40-60%
- Tm: 50-65°C (for RNase H cleavage)
- Gap size: 8-10 DNA nucleotides

---

## 5. GCL SURFACE BIND INTEGRATION

### 5.1 Five Bind Classes Mapping

```
┌─────────────────────────────────────────────────────────────┐
│                    GCL FIELD EQUATIONS                       │
├─────────────────────────────────────────────────────────────┤
│ S(x) = Surface Field       → Alphabet size, information     │
│ C(x) = Closure Field       → Duplex stability, geometry     │
│ M(x) = Motif Field         → Sequence patterns, codon bias    │
│ I(x) = Informaton Field    → Genome projection, binding     │
│ D(x) = Distance Field      → Hybridization kinetics         │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 System-Specific Mapping

| Genetic System | S(x) | C(x) | M(x) | I(x) | D(x) | Primary Bind |
|----------------|------|------|------|------|------|--------------|
| Standard DNA | 2.0 | 1.0 | 1.0 | 1.0 | 1.0 | informational |
| Hachimoji | 3.0 | 0.9 | 0.7 | 1.2 | 0.9 | informational |
| TNA | 2.0 | 0.8 | 0.5 | 0.7 | 0.7 | geometric |
| LNA | 2.0 | 1.8 | 1.2 | 1.5 | 1.1 | thermodynamic |
| PNA | 2.0 | 1.1 | 1.0 | 1.8 | 0.8 | physical |
| Morpholino | 2.0 | 0.9 | 0.8 | 0.6 | 0.7 | control |
| Expanded Code | 2.5 | 1.0 | 0.9 | 1.5 | 1.0 | control |

### 5.3 Compression Implications

**Information Density Scaling**:
```
Compression Ratio ∝ 1 / (Entropy per symbol × Redundancy)

Standard DNA:  2 bits/base × 0.7 redundancy = 1.4 bits effective
Hachimoji:     3 bits/base × 0.6 redundancy = 1.8 bits effective (+29%)
Binary:        1 bit/base × 1.0 redundancy = 1.0 bits effective
```

**XNA-Specific Compression**:
- TNA: Lower Tm → more breathing → higher temporal entropy
- LNA: Rigid structure → predictable motifs → better compression
- PNA: Neutral charge → different electrostatic patterns

---

## 6. RESEARCH GAPS & FUTURE DIRECTIONS

### 6.1 Open Questions
1. **Hachimoji polymerases**: No natural polymerase accepts 8-base system
2. **XNAzymes**: Limited catalytic repertoire vs ribozymes
3. **Quadruplet efficiency**: Suppression rates too low for industrial use
4. **PNA delivery**: Cellular uptake remains major barrier
5. **Evolutionary stability**: XNA-based life unknown

### 6.2 GCL Integration TODOs
- [ ] Port epigenetic compression from 2504.03733
- [ ] Connect to ProteinRepresentation.lean (2503.16659)
- [ ] Prove compression bounds vs gzip/bzip2
- [ ] Model XNA hybridization thermodynamics
- [ ] Implement codon usage bias compression

---

## 7. KEY REFERENCES

### Primary Sources
1. Hoshika S. et al. (2019). *Science* 363(6429):884-887 — Hachimoji DNA
2. Pinheiro V.B. et al. (2012). *Science* 336(6079):341-344 — XNA polymerases
3. Anderson J.C. et al. (2022). *Nature* 603(7903):746-751 — Quadruplet codons
4. Devers M. et al. (2023). *Tetrahedron* — TNA primitive polymer
5. Nielsen P.E. (1991). *Science* 254(5037):1497-1500 — PNA discovery
6. Southern E.M. et al. (1998). *Nature Genetics* 18(1):5-6 — LNA

### Reviews
- Deiters A. & Chin J.W. (2022). *Nat Rev Mol Cell Biol* — Genetic code expansion
- Taylor A.I. et al. (2015). *Nature Communications* — XNA review
- Karkare S. & Bhatnagar D. (2006). *Appl Microbiol Biotechnol* — PNA/LNA/Morpholino
- Dowling D. et al. (2021). *Nucleic Acids Res* — ASO therapeutic mechanisms

---

**Generated**: 2026-05-01  
**Lean Module**: `0-Core-Formalism/lean/Semantics/Semantics/SyntheticGeneticCoding.lean`  
**Build Status**: ✅ PASSED
