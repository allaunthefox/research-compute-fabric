# Meta-Antitropic Angle-Forced Interlock Audit

## Purpose

This note records the next refinement of the flexure / metastable-material layer:

two local material points may be treated as **meta-antitropic** when their ordinary atomic or lattice interaction resists co-alignment, but an imposed approach angle, shock front, flexure geometry, or contact constraint forces them into a metastable interlocked state.

This is a mechanism-layer hypothesis. It supports the engineering analogy for forced alignment, contact lock, and metastable relaxation. It does not prove the Sidon construction or compact density result.

## Core Statement

```text
normally opposed atomic/lattice states
-> oblique forced contact angle
-> geometric frustration
-> metastable interlock
-> charge/contact symmetry during lock
-> dissipation or release after energy decays
```

## Terminology

`Meta-antitropic` is used here as a project term:

```text
meta-antitropic = locally opposed under ordinary alignment, but capable of forced interlock under angle, shock, or constrained contact
```

It should not be treated as a standard materials-science term unless later mapped onto a standard mechanism such as:

```text
lattice mismatch
coincident-site lattice interface
grain-boundary locking
mechanical interlocking
cold-welded clean metallic contact
stress-induced phase transformation
frictional adhesion / fretting adhesion
snap-through bistability
```

## Mechanism Map

```text
Opposed atomic preference     -> repulsive / orthogonal pre-contact state
Approach angle                -> geometric forcing parameter
Flexure or snap point         -> local compliance that imposes the angle
Shock front                   -> transient energy source that overcomes the barrier
Interlock                     -> metastable contact-locked state
Symmetric charge phase        -> temporary discharge-conserving propagation state
Dissipation                   -> loss of phonon/stored energy
Relaxation                    -> return toward anisotropic or separated state
```

## Minimal State Model

Let two points be represented by local orientation states `o₁`, `o₂`, charges `q₁`, `q₂`, and a forced contact angle `θ`.

The unconstrained state resists alignment:

```text
o₁ ⟂ o₂ or interaction_energy(o₁,o₂) > alignment_barrier
```

The constrained oblique contact supplies a forcing term:

```text
F_angle(θ) + F_shock + F_flexure >= E_barrier
```

When the threshold is crossed, the points enter a metastable interlock:

```text
Interlocked(p₁,p₂,θ) = true
```

During interlock, the charge channel becomes approximately symmetric enough to propagate a discharge:

```text
q₁ + q₂ is conserved during the local transfer step
```

After dissipation, the interlock is released or relaxes into a lower-energy basin:

```text
phonon_load -> 0
contact_lock -> released or stabilized
```

## Engineering Interpretation

The useful part of the conjecture is not that the points naturally agree. They do not. The useful part is that the geometry can force a narrow contact configuration where opposition becomes a lock.

This gives a stronger mechanical reading of the flexure:

```text
flexure = controlled misalignment operator
forced angle = interlock gate
metastability = temporary stored state
shock/Burgers front = transport clock
hysteresis = energy drainage receipt
```

## Candidate Physical Analogues

### 1. Coincident-site / commensurate interface

Two lattices may be mismatched globally but share low-energy registry at special angles or coincidence sites. This is a good analogy for angle-specific interlocking.

### 2. Grain-boundary locking

Neighboring crystals can resist ordinary alignment but become mechanically locked along boundary planes or defect structures.

### 3. Clean metallic contact / cold welding

In vacuum or oxide-free contact, surfaces that normally remain separated by contamination or oxide barriers can adhere when fretting/contact exposes clean metal and supplies pressure.

### 4. Stress-induced transformation in metastable alloys

Metastable β-Ti or metastable HEA phases can transform under stress, giving a physical anchor for shock-forced state change.

### 5. Snap-through metamaterial cell

A bistable or multistable cell can resist displacement until a threshold is crossed, then collapse into a second stable or metastable state.

## Audit Classification

```text
Receipt: MetaAntitropicAngleForcedInterlock
Status: MECHANISM_PLAUSIBLE
Gate: U_scope
Reason: the mechanism is physically interpretable through known interface/contact/metastability phenomena, but requires material-specific data, geometry, FEA, and prototype evidence before promotion.
```

## Required Receipts

```text
AntitropicInteractionReceipt
AngleForcingReceipt
InterlockThresholdReceipt
MetastableContactReceipt
DissipationRelaxationReceipt
MaterialAnchorReceipt
FEASimulationReceipt
PrototypeMeasurementReceipt
```

## Boundary

This mechanism should be used only as the mechanical contact layer:

```text
Meta-antitropic angle-forced interlock
  -> supports forced alignment / contact-lock plausibility
ShockBurgersCoupling
  -> models transport and dissipation timing
BurgersRuzsaDecoupling
  -> separates selector from arithmetic lock
NonseparableEncodingReceipt
  -> required for global Sidon pair-sum injectivity
CompactDensityReceipt
  -> required for sigma = 1
```

The interlock is not the theorem. It is the physical receipt candidate for why locally opposed cells can temporarily become aligned under shock and angle constraints.
