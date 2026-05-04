# First Principles Molecular Derivation: Architectural Intent Map

**Status:** CONCEPTUAL — This DAG maps the intended first-principles derivation path. It identifies the provenance of atomic weights and the required manifold constraints. It does NOT yet execute these calculations.

```mermaid
graph TD
    N0["Load IUPAC Standard<br/><i>Read data/atomic_weights.csv</i>"]
    N1["Extract H<br/><i>Mean Weight: 1.00798</i>"]
    N2["Extract C<br/><i>Mean Weight: 12.01060</i>"]
    N3["Extract O<br/><i>Mean Weight: 15.99940</i>"]
    N4["Extract N<br/><i>Mean Weight: 14.00685</i>"]
    N5["Extract P<br/><i>Mean Weight: 30.97376</i>"]
    N6["H2O Composition Schema<br/><i>Intent: First-Principles Water</i>"]
    N7["Proposed Geometry Search<br/><i>Conceptual Sweep Angle 90-120</i>"]
    N8["Coulombic Term (Assumption)<br/><i>q=0.41, r_HH</i>"]
    N9["Pauli/VdW Term (Assumption)<br/><i>1/r^12</i>"]
    N10["AMMR Phase-Gate (Constraint)<br/><i>Golden Ratio scaling</i>"]
    N11["Theoretical Manifold Energy<br/><i>Target Functional Sum</i>"]
    N12["Optimization Logic (Pending)<br/><i>Minimization via AMMR</i>"]
    N13["Expected Result: H2O<br/><i>Reference Angle: 104.5 degrees</i>"]
    N14["CO2 Composition Schema<br/><i>Intent: First-Principles Carbon Dioxide</i>"]
    N15["Proposed Geometry Search<br/><i>Conceptual Sweep Angle 100-180</i>"]
    N16["Coulombic Term (Assumption)<br/><i>O-O Repulsion</i>"]
    N17["AMMR sp Hybridization<br/><i>Linear phase-lock</i>"]
    N18["Theoretical Manifold Energy<br/><i>Target Functional Sum</i>"]
    N19["Optimization Logic (Pending)<br/><i>Minimization via AMMR</i>"]
    N20["Expected Result: CO2<br/><i>Reference Angle: 180.00 degrees</i>"]
    N21["CH4 Composition Schema<br/><i>Intent: First-Principles Methane</i>"]
    N22["Proposed Geometry Search<br/><i>Conceptual Tetrahedral sweep</i>"]
    N23["Coulombic Term (Assumption)<br/><i>H-H Repulsion</i>"]
    N24["AMMR sp3 Hybridization<br/><i>Phi-neutral symmetry</i>"]
    N25["Theoretical Manifold Energy<br/><i>Target Functional Sum</i>"]
    N26["Optimization Logic (Pending)<br/><i>Minimization via AMMR</i>"]
    N27["Expected Result: CH4<br/><i>Reference Angle: 109.47 degrees</i>"]
    N28["DNA Strand Schema<br/><i>Intent: B-DNA Assembly</i>"]
    N29["Nucleotide Bases (Proposed)<br/><i>A, T, C, G resonance</i>"]
    N30["Watson-Crick Pairing (Proposed)<br/><i>Hydrogen Bond resonance</i>"]
    N31["Backbone Model (Proposed)<br/><i>Sugar-Phosphate chain</i>"]
    N32["Helical Torsion (Proposed)<br/><i>3.4nm pitch model</i>"]
    N33["Phi-Manifold (Proposed Constraint)<br/><i>Golden Ratio groove ratio</i>"]
    N34["Theoretical Manifold Stability<br/><i>Target Functional Sum</i>"]
    N35["Optimization Logic (Pending)<br/><i>Global minimum search</i>"]
    N36["Expected Result: B-DNA<br/><i>Reference: 10.5 bp/turn</i>"]
    N0 --> N1
    N0 --> N2
    N0 --> N3
    N0 --> N4
    N0 --> N5
    N1 --> N6
    N3 --> N6
    N6 --> N7
    N7 --> N8
    N7 --> N9
    N7 --> N10
    N8 --> N11
    N9 --> N11
    N10 --> N11
    N11 --> N12
    N12 --> N13
    N2 --> N14
    N3 --> N14
    N14 --> N15
    N15 --> N16
    N15 --> N17
    N16 --> N18
    N17 --> N18
    N18 --> N19
    N19 --> N20
    N2 --> N21
    N1 --> N21
    N21 --> N22
    N22 --> N23
    N22 --> N24
    N23 --> N25
    N24 --> N25
    N25 --> N26
    N26 --> N27
    N5 --> N28
    N3 --> N28
    N2 --> N28
    N4 --> N28
    N1 --> N28
    N28 --> N29
    N29 --> N30
    N28 --> N31
    N30 --> N32
    N31 --> N32
    N32 --> N33
    N33 --> N34
    N34 --> N35
    N35 --> N36
```
