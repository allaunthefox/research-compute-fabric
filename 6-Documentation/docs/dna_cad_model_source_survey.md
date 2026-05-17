# DNA CAD / 3D-Printable Model Source Survey

Date: 2026-05-08

Purpose: identify downloadable DNA structure models that can feed the CAD force
probe work. This is a source survey, not an endorsement that any model is
already mechanically valid for load testing.

## Best Candidates

### NIH 3D: DNA Segment Based on 1BNA

Source:

```text
https://3d.nih.gov/entries/251
https://3d.nih.gov/entries/download/251/2
```

Why it matters:

```text
PDB-based DNA segment
based on 1BNA
NIH 3D output includes STL / GLB / WRL / X3D / PNG
good science-aligned starting point
```

Use:

```text
baseline scientific DNA segment
geometry extraction
comparison against generated 1BNA pipeline
```

Hold:

```text
likely fragile as a direct mechanical test object unless thickened or embedded
```

### NIH 3D: Triplex and Duplex DNA Flexible Model Kits

Source:

```text
https://3d.nih.gov/entries/22792/1
https://3d.nih.gov/entries/download/22792/1
```

Why it matters:

```text
flexible kit based on 1BWG and 1BNA
includes duplex and triplex components
files include STL plus visualization formats
explicitly designed as reconfigurable model parts
```

Use:

```text
best candidate for force-probe style bench tests
base-pair component load / snap-fit / connector behavior
duplex versus triplex geometry comparison
```

Hold:

```text
model page recommends sintered nylon for stacks
FDM may need rescaling and connector tolerance checks
```

### NIH 3D: DNA Playset

Source:

```text
https://3d.nih.gov/entries/259
```

Why it matters:

```text
35,000,000:1 scale DNA playset
four nucleotide parts snap together into arbitrary sequences
mechanically inspectable modular model
```

Use:

```text
sequence-dependent physical assembly tests
connector tolerance / load distribution in modular DNA
```

Hold:

```text
educational scale model, not atomistic force model
```

### NIH 3D: Folding DNA Model

Source:

```text
https://3d.nih.gov/entries/3DPX-001475
```

Why it matters:

```text
modular DNA model that can be extended
single strands can separate to illustrate base pairing
includes detailed assembly and FDM printing notes
```

Use:

```text
strong practical candidate for print-and-measure experiments
base-pair snap fit
strand separation
repeat-unit load path testing
```

Hold:

```text
pins may break if printed in weak orientation
model may need scaling and print orientation controls
```

### NIH 3D: Flexible ssDNA and ssRNA

Source:

```text
https://3d.nih.gov/entries/8880
```

Why it matters:

```text
teaching models of ssDNA / ssRNA in stick representation
uses PDB 1EHZ
successfully printed using laser sintering / elastomeric material per source
```

Use:

```text
single-strand flexibility comparison
material-dependent bend / torsion proxy
```

Hold:

```text
not a double-helix lattice by itself
```

## Secondary Candidates

### Sketchfab: DNA Stick and Ball Molecular Model

Source:

```text
https://sketchfab.com/3d-models/dna-stick-and-ball-molecular-model-a8d959ad7f6649a784ae9a874ade7826
```

Why it matters:

```text
downloadable 3D model
built in ChimeraX from PDB ID 1BNA
CC Attribution
good visual / atomistic reference mesh
```

Use:

```text
visual comparison
atomistic 1BNA reference
mesh inspection
```

Hold:

```text
NoAI restriction noted by source
high triangle count
may require repair / thickening for actual printing
```

### CGTrader: DNA Double Helix Free 3D Print Model

Source:

```text
https://www.cgtrader.com/free-3d-print-models/miniatures/other/dna-double-helix
```

Why it matters:

```text
free model
STL and Rhino 3DM formats
marked prepared for 3D printing
```

Use:

```text
decorative / gross double-helix geometry
possible CAD-editable Rhino route
```

Hold:

```text
not necessarily PDB-derived
license and no-AI terms need review before derivative use
```

### 3DCADBrowser: B-DNA

Source:

```text
https://www.3dcadbrowser.com/3d-model/b-dna
```

Why it matters:

```text
B-DNA model
formats include STL, OBJ, FBX, BLEND, DXF, DWG, and others
atom spheres identify oxygen, nitrogen, hydrogen, carbon, phosphorus
```

Use:

```text
format diversity
CAD import / conversion experiments
```

Hold:

```text
download terms may require account or credits
source has spelling/metadata roughness
verify license before reuse
```

### MakerWorld: DNA Double Helix

Source:

```text
https://makerworld.com/en/models/437066-dna-double-helix
```

Why it matters:

```text
free STL/CAD model
DNA model with support guidance
```

Use:

```text
quick print sanity check
decorative helix comparison
```

Hold:

```text
CC BY-NC-SA license
not scientific geometry
```

### Printables DNA Tag

Source:

```text
https://www.printables.com/tag/dna
```

Why it matters:

```text
aggregates many DNA tagged STL models
includes folding DNA model kit, double helix models, lamps, manipulatives
```

Use:

```text
candidate discovery
practical FDM variants
compare support-free versus supported helix forms
```

Hold:

```text
tag page contains mixed decorative, educational, and unrelated models
vet each license and geometry manually
```

## Generation Route

### RCSB PDB / PDB-101 + NIH 3D Workflow

Sources:

```text
https://pdb101.rcsb.org/learn/3d-printing
https://pdb101-west.rcsb.org/learn/3d-printing/pdb-structures-and-3d-printing
https://3d.nih.gov/submit
```

Why it matters:

```text
RCSB PDB provides scientific source structures
PDB-101 documents 3D printing workflows
NIH 3D can process PDB / CIF and mesh files
NIH 3D can export customized GLB or STL
```

Recommended structure IDs:

```text
1BNA  B-DNA dodecamer
1BWG  triplex DNA component in NIH flexible kit
1EHZ  ssDNA / ssRNA teaching model source
4UN4  Cas9 with target DNA, useful for protein-DNA complex context
```

Use:

```text
generate our own controlled source mesh from PDB data
hash PDB input
hash STL / GLB output
record conversion parameters
feed into CAD force-probe receipt
```

## Shortlist for the Force-Probe Path

Best practical order:

```text
1. NIH 3D Folding DNA Model
2. NIH 3D Triplex and Duplex DNA Flexible Model Kits
3. NIH 3D DNA Playset
4. NIH 3D DNA Segment Based on 1BNA
5. Self-generated 1BNA model through NIH 3D or ChimeraX
```

Rationale:

```text
modular and snap-fit models are better bench objects than fragile atomistic meshes
scientific 1BNA models are better for geometry truth but may need thickening
decorative helices are useful as print controls but weak as biological models
```

## Failure Rules

```text
decorative helix treated as scientific DNA geometry                 -> hold
PDB-derived mesh treated as mechanically printable without repair   -> hold
license omitted from candidate selection                            -> invalid source record
downloaded STL used without hash / provenance                       -> invalid receipt
atomistic visual mesh used as load-bearing model without thickening  -> unsafe / invalid
```
