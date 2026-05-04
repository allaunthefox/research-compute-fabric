# Field-Native Witness Hierarchy

Status: READY_FOR_SPEC_MODULE

Core law: A noisy field is a compiled artifact. The witness hierarchy is the source code.

Canonical equation:

S(x) = sum_{k=1..K} a_k P_{v_k}(x, phi_k) + R(x)

Each witness is an executable tuple:

W_k = (basis, v_k, a_k, phi_k, action_k)

Reference toy field:

S(x) = sin(2x) + 0.5 sin(10x) + 0.25 sin(0.5x)

Expected witness grammar:

- v=2.0, a=1.0, role=carrier, action=ROUTE_CARRIER
- v=10.0, a=0.5, role=texture, action=APPLY_TEXTURE
- v=0.5, a=0.25, role=basin, action=ADJUST_BASIN

Operational loop:

R0 = S
v1 = argmax_v |<R0, P_v>|
R1 = R0 - a1 P_v1
Repeat until residual is routeable.

Claim boundaries:

- Finite grammar gives infinite evaluability, not infinite information.
- Reconstruction is valid only within the declared basis family and residual tolerance.
- Meshes are outputs, not origins.

Routing law: Extract the carrier, subtract it; extract the texture, subtract it; extract the basin, subtract it; route the residual only if it still matters.
