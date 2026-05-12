# Merkle-Attested 3D Printing With Equihash-Style Load Scheduling

## Claim Boundary

This note refines the earlier "Merkle tree + Zcash load distribution" equation.
The important correction is:

```text
hashes and XOR predicates are not mechanical forces
```

The mechanical layer must remain dimensionally mechanical. Merkle roots,
Equihash-style puzzles, and Zcash-like memory-hard checks belong in the
verification / scheduling / attestation layer.

So the safe architecture is:

```text
mechanical equilibrium
  + layer/state commitment
  + bounded load-schedule witness
  + verification receipt
  -> accept, repair, replan, or reject print stage
```

It is not:

```text
mechanical force = hash(layer) XOR load
```

## Source Anchors

Invariant mechanics prior:

```text
"Invariant dual mechanics of tensegrity and origami"
PNAS, 2026.
DOI: 10.1073/pnas.2519138123
https://www.pnas.org/doi/10.1073/pnas.2519138123
```

Useful extraction:

```text
tensegrity self-stress
  is dual to
origami infinitesimal mechanism

linear / projective transformations can preserve the relevant
mechanical class when their invariant conditions hold
```

Equihash prior:

```text
"Equihash: Asymmetric Proof-of-Work Based on the Generalized Birthday Problem"
IACR ePrint 2015/946 / NDSS 2016.
https://eprint.iacr.org/2015/946
```

Useful extraction:

```text
memory-hard puzzle
  + comparatively cheap verification
  + generalized birthday / Wagner-style collision structure
  -> anti-spoofing or work-budget witness
```

Merkle prior:

```text
Merkle tree / Merkle mountain range
  -> logarithmic membership proof
  -> tamper-evident commitment to layer records
```

## Corrected Layer Model

For print layer `i`, keep three separate records:

```text
MechanicalLayer_i =
  (
    geometry_i,
    material_i,
    boundary_condition_i,
    load_i,
    stiffness_i,
    displacement_i
  )
```

```text
CommitmentLayer_i =
  (
    layer_index_i,
    geometry_hash_i,
    material_batch_hash_i,
    sensor_digest_i,
    load_schedule_digest_i,
    mechanical_receipt_hash_i
  )
```

```text
ScheduleWitness_i =
  (
    load_bucket_i,
    printer_head_state_i,
    thermal_window_i,
    memory_hard_nonce_i,
    merkle_path_i,
    verification_status_i
  )
```

The Merkle leaf should commit to the record, not replace the record:

```text
leaf_i =
  H(
    encode(CommitmentLayer_i)
  )
```

The Merkle root is:

```text
M_root =
  MerkleRoot(
    leaf_1,
    leaf_2,
    ...,
    leaf_N
  )
```

The root gives a tamper-evident commitment to the print plan / observed print
state. It does not prove that the print is mechanically safe.

## Mechanical Core

Keep the mechanical equilibrium equation separate:

```text
K(q_i) * u_i = f_i
```

where:

```text
K(q_i)  stiffness / compatibility-derived operator for layer or component i
u_i     displacement / infinitesimal motion state
f_i     applied load vector
q_i     geometry + material + boundary state
```

For the invariant dual mechanics prior, represent the self-stress and mechanism
compatibility as paired constraints:

```text
A_i * omega_i = B_i * delta_i
```

A transform `T` is admissible only when it preserves the mechanical class:

```text
admissible(T, i) iff
  rank_class(T * A_i) == rank_class(A_i)
  and closure_class(T * B_i) == closure_class(B_i)
  and stability_guard(T, i) == pass
```

Then the mechanical residual is:

```text
R_mech_i =
  T_i * A_i * omega_i
  - T_i * B_i * delta_i
```

The stage is mechanically acceptable only if:

```text
||R_mech_i|| <= epsilon_mech_i
```

or if the planner emits a bounded repair / replan packet.

## Merkle Commitment Layer

Merkle verification answers:

```text
is this layer record included in the committed print plan / print log?
```

It does not answer:

```text
is this load mechanically valid?
```

Define:

```text
MerkleOK_i =
  VerifyMerklePath(
    leaf_i,
    path_i,
    M_root
  )
```

The commitment receipt is:

```text
Receipt_commit_i =
  H(
    M_root,
    layer_index_i,
    leaf_i,
    path_i,
    sensor_digest_i
  )
```

## Equihash-Style Load Schedule Witness

Equihash should not be described as directly "optimizing" load distribution.
The safer extraction is:

```text
memory-hard work witness
  -> makes schedule spoofing / cheap replanning harder
  -> can rate-limit or attest load-bucket assignment
  -> verification is cheaper than generation
```

For load scheduling, define a bounded bucket assignment:

```text
bucket_i =
  Bucket(
    load_i,
    material_i,
    thermal_window_i,
    printer_head_state_i
  )
```

Then use a memory-hard witness as an optional admission guard:

```text
EquihashOK_i =
  VerifyEquihashStyleWitness(
    challenge = H(M_root, layer_index_i, bucket_i),
    nonce_i,
    parameters
  )
```

The load balance objective remains ordinary engineering optimization:

```text
minimize over schedule s:
  max_i utilization_i(s)
  + alpha * thermal_risk_i(s)
  + beta  * mechanical_residual_i(s)
  + gamma * replan_cost_i(s)
```

subject to:

```text
MerkleOK_i == true
EquihashOK_i == true when memory_hard_guard_enabled
||R_mech_i|| <= epsilon_mech_i
printer_constraints_i == satisfied
```

## Corrected Combined Gate

The combined acceptance gate is a conjunction, not a force sum:

```text
AcceptLayer_i iff
  MechanicalOK_i
  and MerkleOK_i
  and ScheduleOK_i
  and WitnessOK_i
  and SensorOK_i
```

where:

```text
MechanicalOK_i =
  (||R_mech_i|| <= epsilon_mech_i)
```

```text
ScheduleOK_i =
  load_i in allowed_load_region_i
  and thermal_window_i in allowed_thermal_region_i
  and replan_cost_i <= replan_budget_i
```

```text
SensorOK_i =
  H(sensor_observation_i) == sensor_digest_i
  or bounded_repair_packet_i exists
```

```text
WitnessOK_i =
  true, if memory_hard_guard_enabled == false
  EquihashOK_i, otherwise
```

The print-stage gate is:

```text
AcceptStage_t iff
  forall i in active_layers(Stage_t):
    AcceptLayer_i
```

The print-job gate is:

```text
AcceptPrint iff
  M_root matches committed plan
  and every required layer has AcceptLayer_i
  and final_geometry_hash == expected_geometry_hash
  and final_mechanical_test_status == pass
```

## Parallel Domain Interpretation

This file now matches the DD stage refinement:

```text
Stage_t =
  {
    D_t^mechanical,
    D_t^geometry,
    D_t^material,
    D_t^load,
    D_t^merkle,
    D_t^equihash_witness,
    D_t^sensor,
    D_t^repair,
    D_t^closure
  }
```

Each domain advances in parallel:

```text
Stage_{t+1} =
  parallel_map(
    f_domain,
    D_t^domain
  )
```

but all domains must synchronize at the claim barrier:

```text
barrier_ok iff
  MechanicalOK
  and MerkleOK
  and ScheduleOK
  and WitnessOK
  and SensorOK
  and closure_status != NaN0
```

## Practical Receipt Schema

A useful implementation receipt should look like:

```json
{
  "schema": "merkle_attested_3d_print_load_schedule_v1",
  "layer_id": "layer_000123",
  "merkle_root": "hex...",
  "leaf_hash": "hex...",
  "mechanical_model_hash": "hex...",
  "geometry_hash": "hex...",
  "material_batch_hash": "hex...",
  "load_vector_hash": "hex...",
  "sensor_digest": "hex...",
  "mechanical_residual_norm": 0.0,
  "mechanical_tolerance": 0.0,
  "mechanical_ok": true,
  "schedule_ok": true,
  "merkle_ok": true,
  "memory_hard_guard_enabled": false,
  "equihash_style_witness_ok": null,
  "repair_packet_id": null,
  "closure_status": "closed"
}
```

## What Changed From the Earlier Equation

Removed / corrected:

```text
T * A * omega = T * B * delta + lambda * Sum(H(layer_i) XOR load_i)
```

Reason:

```text
left side is mechanical
right-side hash/XOR term is cryptographic / integer-domain metadata
the equation is dimensionally invalid as a mechanics equation
```

Replacement:

```text
MechanicalOK_i =
  ||T_i * A_i * omega_i - T_i * B_i * delta_i|| <= epsilon_i
```

plus:

```text
VerificationOK_i =
  MerkleOK_i
  and ScheduleOK_i
  and WitnessOK_i
  and SensorOK_i
```

and:

```text
AcceptLayer_i =
  MechanicalOK_i
  and VerificationOK_i
```

## Implementation Considerations

1. Keep force, displacement, stiffness, and stress in a numerical mechanics
   model with units.
2. Keep Merkle hashes in a commitment model with byte strings.
3. Keep Equihash-style checks as optional memory-hard schedule witnesses,
   not as load solvers.
4. Keep optimization in a real load scheduler / finite-element / structural
   evaluator.
5. Treat failed Merkle, sensor, schedule, or mechanical checks as separate
   failure codes so the printer knows whether to re-hash, re-sense, replan,
   repair, or abort.

## Final Compact Form

```text
AcceptPrint =
  MechanicalClosure
  and CommitmentClosure
  and ScheduleClosure
  and WitnessClosure
  and SensorClosure
  and RepairClosure
```

with:

```text
MechanicalClosure:
  forall i, ||T_i * A_i * omega_i - T_i * B_i * delta_i|| <= epsilon_i

CommitmentClosure:
  forall i, VerifyMerklePath(leaf_i, path_i, M_root)

ScheduleClosure:
  forall i, load_i and thermal_i satisfy planner constraints

WitnessClosure:
  optional memory-hard witness verifies for guarded schedule updates

RepairClosure:
  every failed local check either has a bounded repair packet or aborts
```

This preserves the useful idea:

```text
mechanics gives lawful structure
Merkle gives tamper-evident layer commitments
Equihash-style work gives optional anti-spoofing / schedule-admission cost
receipts give inspection and replay
```

without pretending that a cryptographic predicate is a physical force.

## Synthetic Load Equation Harness

Durable runner:

```text
4-Infrastructure/shim/merkle_tensegrity_load_equation_generator.py
```

Receipt:

```text
4-Infrastructure/shim/merkle_tensegrity_load_equation_receipt.json
```

Curriculum sidecar:

```text
4-Infrastructure/shim/merkle_tensegrity_load_equation_curriculum.jsonl
```

Receipt hash:

```text
848d10552a5da1b7dde5543eaa853ee4444006662da3c28b616765b887e4b62d
```

Merkle root:

```text
4756b85d22ea7c66751d446130a26f85c218b15d5d765747d438baa7460e91ed
```

The harness generates a synthetic braced cube lattice:

```text
node_count     8
edge_count     24
support_count  4
```

The important correction from the quick sketch is that a free or unbraced cube
cannot generally balance gravity plus lateral disturbance with internal
self-stress alone. The harness therefore includes:

```text
support reactions on bottom nodes
face diagonals as shear/load paths
```

Mechanical equation:

```text
sum_{j in adj(i)} q_ij * (x_i - x_j) + p_i + r_i = 0
```

Matrix form:

```text
[B_edges B_support] * [q r]^T = -p
```

Least-squares solve:

```text
argmin_{q,r}
  ||[B_edges B_support][q r]^T + p||_2
```

Shielded / bounded print-density command:

```text
rho_e =
  1 / (1 + exp(-alpha * (abs(q_e) - q_mid)))
```

For the default deterministic run:

```text
seed                  2519138123
alpha                 sqrt(2)
q_mid                 0.25
gravity               -9.81
mass_per_node          0.1
lateral_noise_sigma    0.05
epsilon_mech           1e-8
```

Result:

```text
residual_norm_l2       8.765376456850576e-15
mechanically_ok        true
density_min            0.4322915948268626
density_max            0.5521950895667369
```

The axis-only cube was intentionally checked and rejected:

```text
edge_count             12
residual_norm_l2       0.0799708974681604
mechanically_ok        false
```

This is a useful signal: the Merkle commitment can preserve the failed record,
but it cannot make an unbraced geometry mechanically valid.

Failure rules:

```text
Merkle root treated as mechanical proof                 -> invalid
sigmoid density treated as solved equilibrium           -> invalid
unbraced lattice cannot carry lateral loads             -> invalid residual or add diagonals
unsupported free-body gravity case without reactions    -> invalid residual
residual_norm_l2 > epsilon_mech                         -> replan or repair
density command used without slicer/material calibration -> unsafe
```

## Four-Force Probe Interpretation

The braced Merkle-tensegrity cube can be used as a typed probe geometry for
separating force roles:

```text
gravity
  direct external load in the harness

electromagnetism
  next required extension: material stiffness, thermal state, bonding,
  extrusion, sensing, and actuation

strong interaction
  material binding baseline only at this scale

weak interaction
  radiation / transmutation safety guard only at this scale
```

Durable prior:

```text
4-Infrastructure/shim/four_force_geometry_probe_prior.py
4-Infrastructure/shim/four_force_geometry_probe_prior_receipt.json
```

Receipt hash:

```text
f3dfe47c8367501a10ad4e4aae9f14dc2cb4e8947396810bedffe5f7f6c31090
```

The useful 16D lift is:

```text
(x, y, z,
 mass_density,
 gravity_load_z,
 lateral_load_x,
 lateral_load_y,
 edge_force_density_q,
 support_reaction,
 print_density_rho,
 em_stiffness_or_thermal_state,
 material_binding_baseline,
 radiation_decay_guard,
 equilibrium_residual,
 merkle_phase_commitment,
 closure_margin)
```

This is a typed state vector, not a claim of sixteen physical spatial
dimensions.

## CAD Force Probe Experiment Matrix

This is the current most directly testable frame besides biological DNA work:
the geometry can be modeled as CAD, printed, loaded with known forces, measured
with a fixture, and committed as a Merkle-verifiable experiment record.

Durable matrix:

```text
4-Infrastructure/shim/cad_force_probe_experiment_matrix.py
4-Infrastructure/shim/cad_force_probe_experiment_matrix_receipt.json
4-Infrastructure/shim/cad_force_probe_experiment_matrix_curriculum.jsonl
```

Receipt hash:

```text
95f8243b44c5e3f715f54e619f8fa7bc6408c84bcfb4c3b3ad9a20b99293040d
```

Simulated scenario sweep:

```text
G0_braced_static_gravity
  residual_norm_l2   8.765376456850576e-15
  mechanically_ok    true

G1_gravity_only_braced
  residual_norm_l2   8.903690591538473e-15
  mechanically_ok    true

G2_lateral_sweep_braced_0p20
  residual_norm_l2   8.74437471591242e-15
  mechanically_ok    true

G3_mass_sweep_braced_0p20kg
  residual_norm_l2   1.0604488334316642e-14
  mechanically_ok    true

NC1_unbraced_lateral_negative_control
  residual_norm_l2   0.0799708974681604
  mechanically_ok    false
```

Bench equations:

```text
e_F = ||B q + R + p||_2
e_u = ||u_observed - u_predicted||_2
K_proxy = F_applied / max(delta_observed, epsilon_delta)
G_brace = K_proxy(braced) / K_proxy(unbraced)
```

Bench tests:

```text
BENCH_G0       gravity mass sweep
BENCH_G1       lateral force sweep on braced cube
BENCH_NC1      unbraced negative control
BENCH_EM1      material / thermal / stiffness sweep
BENCH_COMMIT1  Merkle mutation check
```

Claim boundary:

```text
CAD force probe matrix       yes
direct load measurement      yes
negative control             yes
unified-force proof          no
structural safety cert       no
replacement for FEA/slicer   no
```
