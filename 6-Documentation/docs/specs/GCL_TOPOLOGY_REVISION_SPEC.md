# GCL Topology Revision Spec

**Version:** 0.2  
**Status:** Canonical revision layer  
**Scope:** Records the revised GCL model used by the nanokernel, metaprobe,
MS3C route-prior geometry, unified compression selector, and embedded node
surface.

---

## Revision Thesis

GCL is no longer modeled as a carrier-specific language or a stack of separate
software authorities. It is a topology contract:

```text
observed surface
-> bounded route prior
-> GCL admission
-> verified state transition
-> receipt
```

The three historical authority layers are now topology phases:

| Phase | Meaning |
| --- | --- |
| `builder` | constructive / forward route formation |
| `warden` | inhibitory / verification pressure |
| `judge` | adjudication / settlement |

They are not independent root authorities. A node may expose them as local
capabilities, but GCL treats them as phases inside one topological surface.

---

## Canonical Gate

Every route, compression, hardware synthesis, recovery, and topology update
passes through the same gate:

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

Nothing before `VERIFY` is authority. MS3C, metaprobe, Sparkle, MNN, and
compression selectors provide route-prior evidence only.

Failure outcomes:

| Outcome | Meaning |
| --- | --- |
| `refuse` | transition is not admissible |
| `renormalize` | coarsen or remap the route and retry |
| `remember_failure` | record a FAMM scar so similar routes are downranked |

---

## Route-Prior Sources

The revised GCL model admits multiple surface families:

1. Sequence surfaces: DNA, RNA, mRNA, Hachimoji, XNA.
2. GCL motif surfaces: control, admission, compression, route, manifest,
   attestation, recovery.
3. Informaton surfaces: genome address, bind witness, invariant receipt.
4. MS3C route-prior geometry: nested shell codons and shear scores.
5. Hardware surfaces: Sparkle Signal DSL circuits and generated Verilog
   candidates.
6. Node surfaces: RackNerd/Netcup appliance primitives.
7. Fractal fold surfaces: self-similar recursive manifests, GraphML concepts,
   golden-spiral navigation paths, and parent/child hash proofs.
8. Meta-autotype surfaces: contingent fields for payloads that have no defined
   ingestion surface yet.

All of these enter the same possibility space. The math chooses useful finite
intersections; GCL decides whether the transition may become state.

---

## Nanokernel Contract

The GCL nanokernel is the smallest carrier-independent executor for admitted
state transitions. Its job is not to host arbitrary workloads. Its job is:

```text
observe, bind, route, verify, receipt, recover
```

The node carrier may be Linux, LFS, NixOS, a unikernel, firmware, KVM, QEMU, or
a direct appliance loop. The carrier does not define GCL.

Required primitives:

```text
health
status
attest
admit
compress
route
plan_route
wiki
fractal_fold
meta_autotype
recover
receipt
```

Optional primitives:

```text
vector_filter
delta_batch
merkle_mmr
content_chunk
sparkle_synthesize
```

`plan_route` is explicitly pre-admission. It returns a route hint, not an
execution grant.

---

## MS3C Integration Rule

MS3C is a route-prior geometry source:

```text
Matroska/S3C = signed nested-shell route-prior geometry
```

It is not a proved physical brane claim.

The MS3C path is:

```text
raw coordinate
-> S3C root-shell split
-> Matroska nested shell codon
-> contra-rotation / shear score
-> metaprobe signature
-> GCL gate
-> FAMM update
-> receipt
```

High shear means "interesting route boundary", not "authorized action".

---

## Sparkle Integration Rule

Sparkle is a hardware surface for candidate circuits. It is not a replacement
for the GCL gate.

The current Semantics package imports Sparkle through:

```text
Semantics.SparkleBridge
```

Downstream hardware modules SHOULD import the bridge instead of raw Sparkle
internals. The bridge records the pinned Sparkle revision and narrows the
stable API used by Semantics.

Sparkle-generated Verilog enters GCL as:

```text
Signal DSL candidate
-> synthesis artifact
-> equivalence/proof evidence
-> GCL admission
-> receipt
```

---

## Implementation Anchors

Current repo anchors:

```text
docs/specs/GCL_FIELD_EQUATIONS_SPEC.md
docs/specs/MS3C_NESTED_REDUCTION_GEAR_SPEC.md
docs/specs/EMBEDDED_NODE_SURFACE_SPEC.md
docs/specs/OMNITOKEN_GCL_REDESIGN.md
infra/embedded_surface/omni_lut/unified_compression_route.py
infra/embedded_surface/omni_lut/matroska_s3c_reduction_gear.py
infra/embedded_surface/omni_lut/possibility_space_probe.py
infra/ene_wiki_layer.py
infra/ene_fractal_fold.py
infra/ene_meta_autotype.py
0-Core-Formalism/lean/Semantics/Semantics/GCLTopologyRevision.lean
0-Core-Formalism/lean/Semantics/Semantics/SparkleBridge.lean
```

Keeper law:

```text
Route priors suggest.
GCL admits or refuses.
FAMM remembers failures.
Receipts make state accountable.
```
