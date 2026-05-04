# MS3C-RG: Matroska S3C Nested Reduction Gear

**Version:** 0.2  
**Status:** Route-prior geometry spec  
**Claim boundary:** This is not a proved brane-physics model. It is a signed
nested-shell reduction and routing system built from S3C shell coordinates,
Matroska nesting, GCL admission, and FAMM failure memory.
**GCL revision anchor:** `docs/specs/GCL_TOPOLOGY_REVISION_SPEC.md`

---

## Safe Core

The defensible reduction is:

```text
Matroska/S3C = signed nested-shell route-prior geometry
```

Under the GCL topology revision, MS3C is a route-prior source. It may improve
search, compression, visualization, and route ranking, but it cannot authorize
execution. Its output must pass the canonical GCL gate before becoming state.

not:

```text
proved brane physics
```

The useful mathematical spine from the dataset is:

```text
Quaternion, qmul, qconj, qnormsq, qinv
shellQuaternion(k,a,b)
contraRotation
shearQuaternion
MatroskaCodon
discoveryAtBoundary
nested shell projection
RGFlow + FAMM
GCL admissibility
```

The risky spine is every theorem-like Float claim, physical brane claim,
cosmology claim, or unsupported extraction claim. Those remain sketches until
retyped with exact algebra and proved in Lean.

---

## Revised Core Object

```text
Matroska-S3C Nested Reduction Gear =
  nested shell reducer
  + S3C root-shell codec
  + contra-rotation gear
  + shear-boundary detector
  + codon-style shell descriptor
  + GCL admissibility wrapper
  + FAMM failure-memory compression
```

Short name:

```text
MS3C-RG
```

---

## Gear Stack

### Gear 0: Raw Coordinate Shell

Purpose: accept unbounded coordinates and route them into compressed shell
coordinates.

```text
X_raw -> (rho, theta, phi)
```

Where:

```text
rho   = log shell radius
theta = phase / angular channel
phi   = shell phase
```

This is the unbounded-forest rule from the dataset:

```text
raw huge coordinate -> log/projective chart -> shell coordinate -> route
```

### Gear 1: S3C Shell Decomposition

Use the corrected S3C split:

```text
n = k^2 + a
k = floor(sqrt(n))
a = n - k^2
b0 = (k+1)^2 - 1 - n
b_plus = (k+1)^2 - n
```

Identities:

```text
a + b0 = 2k
a + b_plus = 2k + 1
b_plus = b0 + 1
```

Interpretation:

```text
b0      = closed-shell complement
b_plus  = next-shell tension
mass    = a * b0
delta   = a - b0
```

This makes S3C a root-shell coordinate atlas, not only a codec.

### Gear 2: Matroska Nesting

One shell becomes a nested route state:

```text
S_k contains S_{k-1} contains ... contains S_0
```

Interpretation:

```text
outer shell = high-level route context
inner shell = compressed local route state
```

The hardware-adjacent dataset already gives the useful implementation shape:

```text
contract: x' = x >> 2
expand:   x' = x << 2, saturating on overflow
```

The scale factor is a route/chart factor. It is not a physical constant claim.

### Gear 3: Contra-Rotation

Purpose: detect whether adjacent shells route against each other.

```text
contraRotation(S_k, S_{k-1}) -> signed route pressure
```

Use this as route stress, not literal angular momentum physics.

```text
q_parent = rotationQuaternion(S_k, t)
q_child  = qinv(q_parent)
q_shear  = q_parent * qinv(q_child)
```

The Float theorem claims in the Kimi bundle are useful design targets, but not
accepted as proofs.

### Gear 4: Shear Boundary

Purpose: detect shell interface stress.

Inputs:

```text
a
b0
b_plus
mass = a * b0
mirror_delta = a - b0
contra_rotation
```

Route score:

```text
shear_boundary_score =
  w_m * normalized(mass)
+ w_d * normalized(abs(mirror_delta))
+ w_t * normalized(b_plus)
+ w_c * normalized(abs(contra_rotation))
```

High shear means candidate boundary, transition, or routing pressure. It does
not authorize a claim.

### Gear 5: Matroska Codon

Purpose: compress shell state into a finite route descriptor.

```json
{
  "matroska_codon": {
    "k": "shell_index",
    "a": "lower_offset",
    "b0": "closed_shell_complement",
    "b_plus": "next_shell_gap",
    "mass": "a * b0",
    "mirror_delta": "a - b0",
    "parity": "n mod 2",
    "shell_phase": "phi",
    "contra_rotation": "signed_route_pressure",
    "shear": "boundary_pressure"
  }
}
```

This descriptor is the reduction gear tooth.

### Gear 6: GCL Admissibility Wrap

Route-prior geometry cannot authorize itself.

Every MS3C-RG output is wrapped:

```text
OBSERVE
-> BIND
-> ROUTE
-> SIGMA_CHECK
-> POLICY_CHECK
-> DAG_CHECK
-> VERIFY
-> RECEIPT
```

Failure paths:

```text
REFUSE
RENORMALIZE
HOLD_REVIEW
```

### Gear 7: FAMM Compression

Failed shell routes become memory, not noise.

```text
failed route
-> coarse-grain shell region
-> mark FAMM scar
-> skip or down-rank similar shell regions
-> keep receipt
```

Buildable spine:

```text
RGFlow verdict
reject pressure
torsion delta
FAMM frustration
FAMM basin
FAMM torsion
receipt hash
```

---

## Revised Combinations

### A. S3C Root Gear

```text
S3C root shell
+ b0 closed complement
+ b_plus next-shell tension
+ mass throat
```

Use when clean integer/root-shell placement is required.

Output:

```text
root_throat_marker
```

### B. Matroska Contra Gear

```text
nested shell
+ contra-rotation
+ shear boundary
```

Use when neighboring shells route against each other.

Output:

```text
counter_rotating_shell_boundary
```

### C. Codec Gear

```text
S3C shell descriptor
+ Matroska codon
+ GCL metadata sequence
```

Use when shell state must be compressed into route metadata.

Output:

```text
shell_codon
```

### D. Lawful Decoupling Gear

```text
Matroska shell
+ n-TDC domain-space split
+ Lawful Decoupling Primitive
```

Use when two properties look human-incompatible but may belong to different law
spaces.

Example:

```text
positive charge response
+ negative effective refraction
```

Output:

```text
split_sign_relic
```

### E. Photonic Gradient Gear

```text
S3C shell
+ photonic gradient field
+ phase shell
+ mode trap
+ Casimir question marker
```

Use when geometry and material response shape allowed modes.

Outputs:

```text
phase_shell
mode_pressure_boundary
caustic_bloom
```

Claim gate:

```text
question marker only; no extractable energy claim
```

### F. Cross-Polymer GCL Gear

```text
DNA / Hachimoji / XNA scaffold
+ GCL route context
+ Matroska shell codon
```

Use when molecular information spaces need lawful route indexing.

Output:

```text
cross_chain_shell_codon
```

Hard gate:

```text
nonliving scaffold only
no replication
no coding function
no cellular deployment
```

### G. Forest Minimap Gear

```text
Matroska nested shell
+ S3C throat/mass field
+ torsion rivers
+ interestingness primitives
```

Use when a human operator needs to see why a manifold region is interesting.

Output:

```text
3D manifold minimap object
```

Primitive stack:

```text
terrain substrate
+ nested shell mesh
+ torsion rivers
+ throat rings
+ shear boundaries
+ lawful decoupling objects
```

---

## Revised JSON Schema

```json
{
  "matroska_s3c_reduction_gear": {
    "id": "MS3C_RG_v2",
    "claim_status": "route_prior_geometry_not_physical_brane_claim",
    "input": {
      "raw_coordinate": "X_raw",
      "integer_or_shell_seed": "n",
      "domain_context": "nTDC"
    },
    "s3c": {
      "k": "floor(sqrt(n))",
      "a": "n - k^2",
      "b0": "(k+1)^2 - 1 - n",
      "b_plus": "(k+1)^2 - n",
      "mass": "a * b0",
      "mirror_delta": "a - b0",
      "identities": [
        "a + b0 = 2k",
        "a + b_plus = 2k + 1",
        "b_plus = b0 + 1"
      ]
    },
    "matroska": {
      "nesting": "S_k contains S_{k-1} ... contains S_0",
      "contra_rotation": "signed route pressure",
      "shear_boundary": "shell interface stress",
      "codon": "compressed shell descriptor"
    },
    "gcl_wrap": [
      "OBSERVE",
      "BIND",
      "ROUTE",
      "SIGMA_CHECK",
      "POLICY_CHECK",
      "DAG_CHECK",
      "VERIFY",
      "RECEIPT"
    ],
    "famm_memory": {
      "failed_route": "coarse_grain_ban_region",
      "successful_route": "reinforce_route_prior",
      "ambiguous_route": "hold_review"
    },
    "output_primitives": [
      "root_throat_marker",
      "counter_rotating_shell_boundary",
      "shell_codon",
      "phase_shell",
      "mode_pressure_boundary",
      "split_sign_relic",
      "torsion_river"
    ]
  }
}
```

---

## Revised Reduction Rule

```text
Raw manifold region
-> S3C root-shell coordinates
-> Matroska nested shell state
-> contra-rotation / shear test
-> codon compression
-> n-TDC domain-space lens
-> Lawful Decoupling check
-> GCL admissibility gate
-> FAMM memory update
-> receipt
```

---

## GCL Field-Equation Integration

MS3C-RG is a motif surface in the GCL field-equation system:

```text
payload surface = S3C/Matroska codon
motif surface   = ms3c_reduction_gear
witness surface = informaton_bind or informaton_genome
```

Triple bind:

```text
bind(ms3c_payload, ms3c_reduction_gear, informaton_witness)
```

Admit only if:

```text
RGFlow persistent
and GCL invariant preserved
and policy permits the domain lens
and FAMM does not mark the region as saturated failure
```

---

## What Changed

Old version:

```text
Matroska branes imply exotic layered physics
```

Revised version:

```text
Matroska shells provide nested route-prior geometry
that can compress, compare, and gate manifold search regions.
```

Old version:

```text
S3C = codec only
```

Revised version:

```text
S3C = root-shell coordinate atlas
+ throat/mass field
+ codon compressor
+ minimap geometry generator
```

Old version:

```text
reduction gear compresses everything
```

Revised version:

```text
reduction gear compresses only after:
  shell identity
  complement identity
  shear state
  domain lens
  admissibility gate
  receipt path
```

---

## Keeper Law

```text
Matroska gives nesting.
S3C gives shell coordinates.
GCL gives admissibility.
FAMM remembers failed teeth.
n-TDC decides which law spaces are being geared together.
```

Sharper form:

```text
The reduction gear does not prove the brane.
It turns the brane-shaped intuition into a lawful route machine.
```
