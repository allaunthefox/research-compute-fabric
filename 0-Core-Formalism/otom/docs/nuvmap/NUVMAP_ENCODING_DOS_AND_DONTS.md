# NUVMAP Encoding Do's and Don'ts

**Canonical term:** NUVMAP — Non-Uniform Virtual Memory Address Projection  
**Purpose:** Encoding discipline for addressable projection of spectral, graph, memory, manifold, AVM, and witness state.  
**Status:** Initial encoding spec  
**Claim level:** Projection and routing discipline; not proof, certification, or domain validation by itself.

## 0. Core rule

A NUVMAP encoding must preserve enough provenance that a projected point can be traced back to:

```text
source object
  -> encoder
  -> address rule
  -> coordinate rule
  -> field/intensity rule
  -> receipt
  -> claim boundary
```

If the projection cannot be traced back to the source and encoder, it is a visualization only and must not be used as evidence.

## 1. Do encode addressable state

Do encode objects that can be represented as structured state with explicit provenance.

Allowed examples:

```text
AVM stack traces
Q16.16 scalar kernel outputs
spectral mode amplitudes
photonic witness distributions
process graph features
S3C codons
DIAT / mass-number shell coordinates
Delta residual vectors
MetaProbe failure surfaces
GCL lawful/forbidden regions
AngrySphinx route-pressure fields
hardware loopback trace locations
benchmark receipts
```

A NUVMAP point should answer:

```text
what is this?
where did it come from?
which encoder placed it here?
what address does it occupy?
what field value does it carry?
what claim does it support?
what claim does it not support?
```

## 2. Don't encode vibes as facts

Do not encode intuition, aesthetic resemblance, or narrative convenience as if it were measured or computed data.

Forbidden examples:

```text
"this looks similar"
"this feels turbulent"
"this resembles mass"
"this probably maps to mode 3"
"the projection proves the systems are equivalent"
"the pretty cluster means the theory is true"
```

If a field is heuristic, label it as heuristic.

If a field is measured, include measurement provenance.

If a field is computed, include the exact computation rule.

## 3. Do separate address, coordinate, and value

Every encoded NUVMAP record should separate these concepts:

```text
address:
  virtual memory / shell / graph / trace identity

coordinate:
  plotted or projected position

value:
  scalar, intensity, probability, score, pressure, or residual carried by the coordinate
```

Do not collapse them into one ambiguous number.

Bad:

```json
{"u": 0.7, "v": 2, "meaning": "complexity"}
```

Better:

```json
{
  "address": {
    "kind": "spectral_mode",
    "mode_index": 2,
    "source_id": "burgers_witness_3mode"
  },
  "coordinate": {
    "u": 0.3,
    "v": 2
  },
  "value": {
    "field": "omega_contribution",
    "q16_16": 5898,
    "debug_float": 0.09
  },
  "encoder": "nuvmap.burgers_witness.v1"
}
```

## 4. Do prefer deterministic encoders

A NUVMAP encoder should be deterministic unless explicitly marked stochastic.

Required for deterministic encoders:

```text
same input
same encoder version
same parameters
same output address/projection
```

For stochastic/sampling encoders, record:

```text
random seed when available
shot count
sampler/backend
confidence interval
statistical error model
whether values are empirical estimates or analytical values
```

## 5. Don't hide units or numeric representation

Every numeric value must declare its representation.

Allowed numeric forms:

```text
Q16.16 fixed-point hot-path value
integer count
rational value
probability in [0,1]
dimensionless score
SI quantity with explicit unit
float debug value marked non-authoritative
```

Do not use floats as hidden authority in hot-path encodings.

Bad:

```json
{"omega": 0.725}
```

Better:

```json
{
  "omega": {
    "representation": "Q16_16",
    "q16_16": 47514,
    "debug_float": 0.725,
    "debug_float_authoritative": false
  }
}
```

## 6. Do encode claim boundaries with every receipt

Every NUVMAP receipt should include allowed claims and non-claims.

Minimum receipt fields:

```json
{
  "nuvmap_version": "v0.1",
  "encoder": "encoder.name.version",
  "source_artifact": "path-or-id",
  "projection_kind": "spectral|graph|avm_trace|hardware_trace|process|metaprobe|gcl|angrysphinx",
  "numeric_policy": "Q16_16_hot_path_float_debug_only",
  "allowed_claims": [],
  "non_claims": []
}
```

Non-claims must be explicit when the projection is connected to ambitious work.

Common non-claims:

```text
not a PDE proof
not a global boundedness proof
not a proof of domain equivalence
not a hardware certification unless loopback passed
not a quantum advantage claim
not a theorem unless Lean proves it
not a market prediction oracle
```

## 7. Don't let visualization become validation

A NUVMAP plot is an inspection surface, not proof.

Allowed wording:

```text
The projection visualizes mode dominance.
The projection localizes the witness contribution.
The projection shows the encoded data under encoder X.
```

Forbidden wording:

```text
The plot proves the PDE claim.
The projection validates the theorem.
The cluster proves equivalence.
The colorbar proves causality.
```

## 8. Do keep source and encoder versioned

Every NUVMAP encoding must include:

```text
source artifact path or hash
encoder name
encoder version
parameter version
timestamp or commit hash when available
numeric policy
```

If the source cannot be found later, the NUVMAP record is degraded to non-evidence.

## 9. Don't mix analytical, empirical, and heuristic values without labels

Use separate fields.

Example:

```json
{
  "omega": {
    "analytical_q16_16": 47514,
    "empirical_q16_16": 47369,
    "heuristic_q16_16": null,
    "shots": 100000,
    "sigma_deviation": 0.904
  }
}
```

Do not overwrite analytical values with empirical estimates or vice versa.

## 10. Do encode non-uniformity explicitly

NUVMAP is non-uniform. The reason for non-uniform density or resolution should be recorded.

Examples:

```text
high witness probability
high turbulence
high route pressure
high uncertainty
hardware failure boundary
proof gap boundary
negative-control cluster
AngrySphinx escalation zone
```

Suggested field:

```json
{
  "non_uniformity": {
    "reason": "high_witness_probability",
    "resolution_multiplier_q16_16": 131072,
    "routing_priority": "high"
  }
}
```

## 11. Don't overload U and V without a legend

The U-axis and V-axis are projection coordinates, not universal constants.

Every plot or receipt must define:

```text
U means what in this projection?
V means what in this projection?
What does marker size mean?
What does marker color mean?
What does opacity mean, if used?
```

For example:

```text
Burgers witness projection:
  U-axis = projected process/time/address coordinate
  V-axis = spectral mode index
  marker size = omega contribution
  marker color = witness intensity
```

## 12. Do make failed encodings useful

A failed encoding should become a structured artifact.

Failure output should include:

```text
source
encoder
failure mode
failed invariant
fallback address
whether AngrySphinx should scar/throttle/quarantine
whether MetaProbe should generate a harder test
```

Do not silently drop failed points.

## 13. Don't encode unsafe or unauthorized material

Do not encode:

```text
private credentials
secrets
auth tokens
personal identifying data without a legitimate need
malware payloads
unauthorized target information
retaliatory instructions
doxxing material
unvalidated medical claims as conclusions
```

If security or safety information must be represented, encode only abstract, non-operational features needed for defensive analysis.

## 14. Do use NUVMAP as a routing surface

NUVMAP may route evidence and compute pressure.

Examples:

```text
high Delta residual -> MetaProbe target
AVM trace mismatch -> hardware loopback retest
photonic mismatch -> harder witness family
GCL violation -> quarantine/fail_closed
AngrySphinx overload -> throttle or scar
Lean proof gap -> formal target queue
```

Routing decisions must be logged.

## 15. Don't let NUVMAP mutate source truth

NUVMAP is a projection layer. It must not alter the source artifact.

Allowed:

```text
add receipt
add projection
add derived coordinate
add route recommendation
```

Forbidden:

```text
rewrite original trace to fit the projection
change source data to improve visual clustering
delete negative controls
hide failed witness points
```

## 16. Recommended NUVMAP record schema

```json
{
  "id": "nuvmap-point-id",
  "nuvmap_version": "v0.1",
  "encoder": {
    "name": "encoder.name",
    "version": "v1",
    "commit": "optional-git-sha"
  },
  "source": {
    "kind": "avm_trace|photonic_witness|process_graph|lean_target|hardware_loopback",
    "artifact": "path-or-url",
    "sha256": "optional-hash"
  },
  "address": {
    "kind": "virtual|spectral|shell|graph|trace|hardware",
    "value": "address-value"
  },
  "coordinate": {
    "u": {"representation": "Q16_16", "value": 0},
    "v": {"representation": "Q16_16", "value": 0}
  },
  "fields": {
    "omega": {"representation": "Q16_16", "value": 0, "debug_float": 0.0},
    "binding": {"representation": "Q16_16", "value": 0},
    "turbulence": {"representation": "Q16_16", "value": 0},
    "route_pressure": {"representation": "Q16_16", "value": 0}
  },
  "non_uniformity": {
    "reason": "none|witness_probability|uncertainty|route_pressure|proof_gap|failure_boundary",
    "routing_priority": "low|normal|high|quarantine"
  },
  "claim_boundary": {
    "allowed_claims": [],
    "non_claims": []
  }
}
```

## 17. Final encoding discipline

Use NUVMAP when it makes state addressable, comparable, inspectable, and routable.

Do not use NUVMAP to launder intuition into evidence.

Short rule:

```text
No source, no encoder, no claim boundary = not a NUVMAP evidence artifact.
```
