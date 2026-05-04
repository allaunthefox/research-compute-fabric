# GCL Field Equations Spec

**Version:** 0.1  
**Status:** Draft canonical extension  
**Scope:** Defines the field equations for GCL surface combination, compression,
adaptation, and admission across sequence substrates, GCL motifs, and informaton
surfaces.
**Revision anchor:** `docs/specs/GCL_TOPOLOGY_REVISION_SPEC.md`

---

## Thesis

GCL is not bound to one sequence, one motif table, or one carrier. It operates
over a possibility space of surfaces. The math should expose which combinations
are computationally useful, then GCL should compress and admit those surfaces
through finite LUTs.

The revised model is:

```text
candidate surface
  -> metaprobe signature
  -> field interaction
  -> RGFlow persistence
  -> LUT admission
  -> finite GCL codon
```

The topology revision makes this authority boundary explicit:

```text
route priors suggest; only the GCL gate admits or refuses
```

Builder, Warden, and Judge are topology phases in this model, not standalone
software roots. This spec defines the fields they observe; the gate contract is
defined in `GCL_TOPOLOGY_REVISION_SPEC.md`.

The decisive question is:

```text
What is the smallest lawful surface that preserves the useful structure?
```

---

## Objects

Let `x` be a candidate computational object. It may be:

- a biological or synthetic sequence surface: DNA, RNA, mRNA, Hachimoji, XNA;
- a GCL motif surface: control, admission, compression, route, manifest,
  attest, recovery, MS3C nested reduction gear;
- an informaton surface: genome address or bind witness;
- a synthetic finite lane discovered by the possibility-space probe.

Each candidate is represented as:

```text
x = (A, W, R, O, K)
```

Where:

| Symbol | Meaning |
| --- | --- |
| `A` | alphabet size or finite state cardinality |
| `W` | bits per symbol |
| `R` | role flags |
| `O` | operation flags |
| `K` | closure kind: complement, rgflow, codec_roundtrip, hash_chain, invariant_witness, etc. |

The current implementation maps these objects through:

```text
infra/embedded_surface/omni_lut/sequence_surface_lut.py
infra/embedded_surface/omni_lut/gcl_motif_lut.py
infra/embedded_surface/omni_lut/possibility_space_probe.py
infra/embedded_surface/omni_lut/matroska_s3c_reduction_gear.py
infra/embedded_surface/omni_lut/unified_compression_route.py
```

---

## Primary Fields

### 1. Surface Field

The surface field measures whether a candidate can carry structure with a small
local representation.

```text
S(x) = (log2(A) / W) * E_frame(x)
```

Where:

```text
E_frame(x) = 1 - ((N * W + H) / (N * 8))
```

`N` is the local symbol window and `H` is fixed frame overhead. `S(x)` is high
when the surface carries many distinguishable states with few bits and low
framing cost.

Implementation:

```text
frame_efficiency
combinatorial_capacity
bits_per_symbol
```

### 2. Closure Field

The closure field measures whether a candidate preserves structure under its
native lawful operation.

```text
C(x) =
  1.00  if complement-closed
  0.90  if closed by RGFlow, hash chain, codec roundtrip, manifest hash,
        last-good recovery, address conservation, or invariant witness
  0.80  if closed by finite codon or topology route
  0.65  if transient messenger execution closes by translation hint
  0.35  if only partial complement intent is present
  0.00  otherwise
```

This prevents the model from over-favoring one biological closure. DNA/RNA may
close by complement. mRNA may close by transient expression. GCL admission may
close by RGFlow. `informaton_bind` may close by invariant witness.

Implementation:

```text
closure_kind
complement_closed
operation flags
role flags
```

### 3. Motif Field

The motif field measures whether a surface has useful executable affordances.

```text
M(x) = popcount(O) / |O_max|
```

The field is intentionally finite. Operation names are not open strings inside
the decision layer.

Current operation families:

```text
complement
transcribe
translate_hint
mutate
route
control
admit
attest
```

Implementation:

```text
operation_density
```

### 4. Informaton Field

The informaton field measures whether a candidate can enter the GCL/JSON-L
manifold as addressable, attestable, invariant-bearing information.

```text
I(x) = w_g G(x) + w_b B(x) + w_a A_t(x)
```

Where:

| Term | Meaning |
| --- | --- |
| `G(x)` | can project to a 6D RGFlow genome/address |
| `B(x)` | can carry lawful/cost/invariant bind witness |
| `A_t(x)` | can participate in attestation or hash-chain provenance |

For tiny targets, this collapses to bit checks on finite role/op flags.

Implementation:

```text
informaton_genome
informaton_bind
gcl_attest
gcl_manifest
role_flags
op_flags
```

### 5. RGFlow Field

The RGFlow field measures persistence under coarse-graining.

Metaprobe first maps a candidate to a six-bin state:

```text
P(x) = (mu, rho, c, m, ne, sig) in Fin(8)^6
```

Current interpretation:

| Bin | Source |
| --- | --- |
| `mu` | mutation freedom / instability |
| `rho` | combinatorial capacity |
| `c` | operation complexity |
| `m` | frame efficiency |
| `ne` | role density / negentropy |
| `sig` | closure plus degeneracy signal |

Then RGFlow evolves:

```text
P_{t+1} = beta(P_t)
```

A candidate is persistent when:

```text
R_n(x) = and_{t=0..n} lawful(P_t)
```

Implementation:

```text
signature_to_rg_state
locally_lawful
coarse_step
rgflow
```

---

## Interaction Equations

### Pairwise Intersection

Two surfaces interact when their fields conserve useful structure across a
shared operation boundary.

```text
x ⋂ y = J(x, y)
```

with:

```text
J(x, y) =
  alpha_S min(S(x), S(y))
+ alpha_C C(x) C(y)
+ alpha_M overlap(O_x, O_y)
+ alpha_I I(x, y)
- alpha_D distance(K_x, K_y)
```

Where:

```text
overlap(O_x, O_y) = popcount(O_x & O_y) / popcount(O_x | O_y)
```

and `I(x, y)` is high when one surface can witness, address, route, or compress
the other.

Examples:

```text
mRNA ⋂ gcl_admission
  = transient executable surface + admission witness

DNA ⋂ gcl_manifest
  = archival sequence + hash-conserved manifest

Hachimoji ⋂ gcl_compression
  = expanded alphabet + codec roundtrip

gcl_route ⋂ informaton_genome
  = route decision + 6D addressable topology

gcl_recovery ⋂ informaton_bind
  = rollback/recovery + invariant witness

ms3c_reduction_gear ⋂ informaton_genome
  = nested shell route-prior geometry + 6D addressable topology
```

### Triple Bind

The core GCL bind is a triple intersection among payload surface, motif, and
informaton witness.

```text
bind(p, m, i) = (cost, witness, admitted)
```

Defined by:

```text
Phi_bind(p, m, i) =
  lambda_1 J(p, m)
+ lambda_2 J(m, i)
+ lambda_3 J(p, i)
+ lambda_4 R_n(p)
+ lambda_5 R_n(m)
+ lambda_6 R_n(i)
- lambda_7 Cost(p, m, i)
```

Admission rule:

```text
admitted = Phi_bind >= theta_admit
           and R_n(p)
           and R_n(m)
           and R_n(i)
           and invariant_preserved(p, m, i)
```

This is the revised meaning of GCL dispatch:

```text
payload does not execute because it exists;
payload executes because it binds to a motif and witness lawfully.
```

### Compression Potential

Compression is selected by minimizing the lawful surface cost.

```text
Compress(x) = argmin_s Cost_s(x)
              subject to R_n(s) and preserves(s, x)
```

For a candidate surface:

```text
Cost_s(x) = H_frame + N * W_s + verification_cost(s, x)
```

Domain-specific compression emerges because the chosen surface changes with the
payload:

| Payload | Likely surface |
| --- | --- |
| recovery pulse | binary lane or `gcl_recovery` |
| stable heredity | DNA/Hachimoji/XNA lane |
| transient execution | mRNA + `gcl_admission` |
| route/update event | `gcl_route` + `informaton_genome` |
| manifest payload | `gcl_manifest` + `gcl_attest` |
| semantic/admission event | `informaton_bind` + RGFlow |

### Adaptation Equation

Adaptation updates the active LUT bank by choosing the best lawful surface under
current pressure.

```text
L_{t+1} = select_top_k(
  { x in PossibilitySpace | R_n(x) and Phi_context(x, q_t) >= theta_context }
)
```

Where `q_t` is the local context:

```text
q_t = (memory_budget, carrier, pressure, trust, workload, recovery_state)
```

The context score is:

```text
Phi_context(x, q) =
  beta_1 S(x)
+ beta_2 C(x)
+ beta_3 M(x)
+ beta_4 I(x)
+ beta_5 R_n(x)
- beta_6 resource_cost(x, q)
- beta_7 risk(x, q)
```

This is the formal bridge from the possibility-space probe to runtime GCL
adaptation.

---

## Revised GCL Pipeline

The revised pipeline is:

```text
1. enumerate candidate surfaces
2. metaprobe candidate fields
3. compute pairwise intersections
4. test RGFlow persistence
5. choose active LUT bank
6. bind payload + motif + informaton witness
7. emit finite GCL codon or refuse
```

Minimal hosted implementation:

```text
python3 infra/embedded_surface/omni_lut/possibility_space_probe.py \
  --max-alphabet 16 \
  --window-symbols 256 \
  --steps 4 \
  --top 24 \
  --jsonl \
  --output out/sequence_surface_possibility_space.jsonl
```

Tiny node implementation:

```text
u8 domain
u8 scalar
u8 surface_id
u8 witness_id
```

Then:

```text
lut[domain][scalar] -> motif
surface_lut[surface_id] -> payload surface
witness_lut[witness_id] -> informaton witness
bind(payload, motif, witness) -> admit/refuse
```

---

## Implementation Requirements

### Python Shim

The Python layer MAY:

1. enumerate candidate surfaces;
2. compute finite metaprobe signatures;
3. generate JSONL candidate tables;
4. smoke-test packing, roundtrips, and closure labels.

The Python layer MUST NOT become final semantic authority for admission. It is
a generator and harness.

### Lean / Formal Layer

The Lean layer SHOULD own:

1. finite field definitions;
2. RGFlow lawfulness predicates;
3. bind preservation theorem;
4. compression preservation theorem;
5. refusal correctness theorem.

Target Lean shapes:

```lean
structure GCLSurface where
  alphabetSize : Nat
  bitsPerSymbol : Nat
  roleFlags : UInt8
  opFlags : UInt16
  closureKind : ClosureKind

structure FieldSignature where
  surface : UInt8
  closure : UInt8
  motif : UInt8
  informaton : UInt8
  rg : Genome6

def intersects : GCLSurface -> GCLSurface -> UInt16
def bind3 : GCLSurface -> GCLSurface -> GCLSurface -> BindResult
def rgPersistent : GCLSurface -> Nat -> Bool
```

Required theorem targets:

```lean
theorem admitted_preserves_invariant :
  bind3 p m i = admitted ->
  invariantPreserved p m i

theorem compression_preserves_surface :
  selectedCompressor x = s ->
  rgPersistent s n ->
  preserves s x
```

### Embedded / Nanokernel Layer

The nanokernel layer SHOULD receive precomputed tables:

```text
surface table
motif table
witness table
intersection table
rg verdict table
```

The runtime path should be bounded:

```text
decode token
lookup surface/motif/witness
lookup intersection score
lookup RG verdict
emit finite op or refuse
```

No dynamic allocation, JSON parsing, regex, network-specific parsing, or
floating point is required at Layer 0.

---

## Spec Delta For Omnitoken/GCL

The existing Omnitoken model remains valid:

```text
scale-invariant scalar -> compressed LUT -> lawful GCL codon
```

This spec revises the middle:

```text
scale-invariant scalar
  -> surface/motif/informaton field lookup
  -> RGFlow persistent intersection
  -> compressed LUT
  -> lawful GCL codon
```

Therefore, GCL no longer has a single flat LUT. It has a field-selected LUT:

```text
lut_bank = select(domain, surface_id, motif_id, witness_id, rg_verdict)
codon = lut_bank[scalar]
```

This enables domain-specific combination, compression, and adaptation while
preserving the finite-codon invariant.
