# Hairy Ball FFT Topological Filter

## Purpose

This note refines the spectral-void diagnostic by adding a topological constraint inspired by the hairy ball theorem.

The idea is to use FFT/GFT/Hodge/Dirac-style filtering to extract information from spectral fields while using unavoidable topological singularities as markers of voids, defects, phase slips, or active-cell boundaries.

This is a diagnostic and selector layer. It does not prove Sidon pair-sum injectivity by itself.

## Core Statement

```text
spectral field on a curved / closed topology
-> no globally smooth nonvanishing tangent vector field is possible on even spheres
-> unavoidable defects / singularities mark topological obstruction points
-> FFT/GFT filters expose spectral voids and mode concentrations
-> topological defects become candidate active-cell anchors
-> finite set still requires difference/sum-set audit and nonseparable encoding
```

## Hairy Ball Translation

The classical hairy ball theorem says that every continuous tangent vector field on an even-dimensional sphere has at least one zero.

Project translation:

```text
If the virtual Sidon fabric is modeled as a closed curved admissibility surface,
then a globally consistent flow/phase/orientation field cannot avoid singularities.
```

Those singularities can be interpreted as:

```text
void centers
phase-slip nodes
unrecoverable throat points
bandwidth collapse points
local shatter/recovery anchors
topological defects in the spectral field
```

## FFT Filter Layer

Given a finite signal:

```text
f[n] = measured spectral amplitude / phase / transmission over finite window
```

apply FFT:

```text
F[k] = FFT(f[n])
```

Define a filter:

```text
F_filtered[k] = H[k] F[k]
```

where `H[k]` may be:

```text
band-stop filter for known noise
band-pass filter around candidate phonon modes
notch filter around destructive voids
sparsifying threshold for strong modes
phase-coherence filter
```

Inverse transform:

```text
f_filtered[n] = IFFT(F_filtered[k])
```

Candidate voids:

```text
Void = { n : f_filtered[n] <= -Theta or Gamma[n] <= Gamma_min }
```

## Topological Filter Layer

If the signal is not on a line but on a graph, manifold, or cell complex, replace FFT with:

```text
Graph Fourier Transform
Hodge Laplacian filter
Dirac operator filter
simplicial / cell-complex topological signal processing
```

For a graph/cell complex:

```text
L = graph Laplacian or Hodge Laplacian
L phi_k = lambda_k phi_k
f_hat[k] = <f, phi_k>
f_filtered = sum_k h(lambda_k) f_hat[k] phi_k
```

For higher-order signals, use Hodge/Dirac decomposition:

```text
signal = gradient component + curl component + harmonic component
```

Interpretation:

```text
gradient component -> transport / alignment flow
curl component     -> torsion / circulation / mode mixing
harmonic component -> topology-protected residual / hole witness
```

## Hairy-Ball Defect Receipt

Define a local orientation/phase vector field over the admissibility fabric:

```text
V(p) = normalized local spectral-gradient / phase-flow / transport vector
```

Defect candidates are:

```text
Defect_epsilon = { p : ||V(p)|| <= epsilon }
```

On a closed even-sphere-like topology, at least one zero is expected by topology. More generally, the sum of defect indices should match the Euler characteristic:

```text
sum_p index_p(V) = chi(M)
```

This is the Poincare-Hopf version and is often more useful than the informal hairy-ball statement.

## Combined Selector

The active selector becomes:

```text
chi_topo_fft(i,t) = 1 iff
  FFTVoidGate_i(t)=1
  and TopologicalDefectGate_i(t)=1
  and ModeOverlap_i(t) >= eta_min(N)
  and Repair_i(T_N) >= R_min(N)
  and ThroatLoss_i(t) <= L_max(N)
```

Candidate active set:

```text
I_candidate(N) = { i <= N : exists t in T_emit(N), chi_topo_fft(i,t)=1 }
```

Then perform:

```text
DifferenceSetReceipt
SumSetReceipt
NonseparableEncodingReceipt
CompactDensityReceipt
```

## Why This Helps

FFT alone finds frequency structure but can miss geometric/topological defects.

Hairy-ball / Poincare-Hopf logic adds a structural rule:

```text
closed admissibility fabrics force defect points;
those defects are not random noise;
they are topologically required discontinuities or zeros.
```

So the pipeline becomes:

```text
FFT finds void spectrum
GFT/Hodge/Dirac localizes voids on irregular geometry
Poincare-Hopf checks whether defect count/index is topologically consistent
Sidon audit checks arithmetic uniqueness of selected indices
```

## Boundary

Do not claim:

```text
hairy ball theorem proves Sidon
FFT filtering proves B2 uniqueness
spectral voids automatically equal forbidden sums
```

Allowed claim:

```text
Hairy-ball/Poincare-Hopf constraints can turn spectral voids into topological defect candidates, while FFT/GFT/Hodge filters extract the finite recoverable information used to propose active cells.
```

## Literature Anchors

Topological signal processing over simplicial and cell complexes, graph Fourier transforms, Hodge/Dirac signal processing, and graph signal processing on uncertain topology support the signal-processing side of this selector.

## Audit Classification

```text
Receipt: HairyBallFFTTopologicalFilter
Status: DIAGNOSTIC_SELECTOR_DRAFT
Gate: U_scope
Reason: coherent as a topological-spectral filter for finite active-cell candidates, but requires explicit topology, finite samples, defect-index calculation, void-fit score, and sum/difference-set audits.
```

## Required Receipts

```text
FiniteSignalReceipt
FFTFilterReceipt
GraphOrManifoldTopologyReceipt
VectorFieldReceipt
DefectIndexReceipt
VoidExtractionReceipt
VoidFitReceipt
DifferenceSetReceipt
SumSetReceipt
NonseparableEncodingReceipt
CompactDensityReceipt
```
