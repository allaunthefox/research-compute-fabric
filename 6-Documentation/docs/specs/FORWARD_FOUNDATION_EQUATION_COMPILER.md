# Forward Foundation Equation Compiler

Status: Draft v0.1
Date: 2026-05-09
Scope: trust boundary for equation atoms, foundation kernels, derivation receipts, and theorem/logogram labels
Claim state: compiler contract and admission doctrine; not a theorem prover, benchmark result, or proof of external equations

## 1. Purpose

This document defines the forward foundation equation compiler.

The rule is:

```text
No backward trust chain. Only forward admissible generation.
```

Human theorem labels, expert names, citation chains, equation names, and
logogram names are routing hints only. They are not trust objects.

A trusted equation object must be generated forward from the foundation kernel,
closed under the declared transform, and accompanied by a receipt.

The human-origin doctrine is:

```text
Origin may inspire. Only closure admits.
```

The irreverent short form is:

```text
No vibes-to-axioms pipeline without a receipt.
```

This does not claim that unusual historical, cultural, personal, mystical,
countercultural, or altered-state origins invalidate an equation. It only says
origin stories are metadata, not authority.

Local generator:

```text
4-Infrastructure/shim/foundation_forward_equation_compiler.py
```

Current receipt:

```text
shared-data/data/foundation_forward_equation_compiler/foundation_forward_equation_compiler_receipt.json
```

Human summary:

```text
shared-data/data/foundation_forward_equation_compiler/foundation_forward_equation_compiler.md
```

## 2. Foundation Kernel

The foundation set is:

```text
F0 = {O4, SD, MN, gamma_star, H_dV, Omega, Lambda, A}
```

| Symbol | Role |
|---|---|
| `O4` | four primitives: field, shear, packet, spectral |
| `SD` | dimensional shell: projection, residual, closure |
| `MN` | Mass Number metric pressure |
| `gamma_star` | shortest lawful projection path |
| `H_dV` | information horizon / Underverse boundary |
| `Omega` | torsion, shear, and event correction |
| `Lambda` | logogram substitution / callable abstraction atom |
| `A` | admission gate: ACCEPT, HOLD, QUARANTINE |

The foundation kernel is not a citation bundle. It is the root object from
which equation atoms must compile.

## 3. Shell Equation

The no-infinity shell is:

```text
SD = L4(O4) + L3(Rg3) + chi0 + U4 + E_HD + U_under
```

Where:

| Term | Meaning |
|---|---|
| `SD` | source object in full domain dimension |
| `O4` | visible four-primitive projection |
| `Rg3` | genus-3 residual shadow |
| `chi0` | closure witness |
| `U4` | unseen but potentially promotable reserve |
| `E_HD` | high-dimensional projection energy tax |
| `U_under` | failed, forbidden, entropy-bound, or non-promotable residue |

If an equation cannot fit this shell, it is not promoted structure. It routes
to `HOLD`, `QUARANTINE`, `U_under`, or `NaN0`.

## 4. Forward Derivation

The compiler does not ask whether a theorem label has a prestigious citation
chain. It asks whether the object can be generated from `F0`:

```text
F0 -> E1 -> E2 -> E3 -> ...
```

Each equation atom is shaped as:

```text
E_next = Compile(E_prev, transform_rule, constraints, residual)
```

Promotion requires:

```text
Admit(E_next) = ACCEPT
```

Otherwise the result remains:

```text
HOLD | QUARANTINE | U_under | NaN0
```

## 5. Equation Atom Contract

Every generated equation atom carries:

```yaml
equation_atom:
  identity:
    equation_id:
    semantic_key:
    canonical_equation:
    equation_hash:
  foundation:
    source_kernel: F0_forward_foundation_kernel
    parent_equations:
    transform_rule:
    dependency_hash:
  projection:
    O4:
    Rg3:
    chi0:
    U4:
    E_HD:
    Underverse:
  admissibility:
    domain_laws:
    dimensional_scaling:
    energy_budget:
    information_budget:
    closure_status:
    residual_policy:
  receipt:
    source_hash:
    equation_hash:
    dependency_hash:
    receipt_hash:
    decision:
```

This mirrors the Omindirection rule:

```text
payload != glyph != rendered layout
```

For equations:

```text
equation object != theorem label != citation chain != rendered math
```

## 6. Admission Equation

A derived equation is accepted only when:

```text
ACCEPT(E) iff
  receipt_recomputes(E)
  and chi0(E) = 0
  and residual_declared(E)
  and B(E) < B_max
  and E_HD_paid(E)
```

The stack may propose candidate equations. The foundation compiler decides only
whether the object is closed, accounted, and receipted.

## 7. PASS / ADD / PAUSE / SUBTRACT

To avoid clock skew and hidden accounting drift, the compiler uses the same
four-gate deterministic loop as the reconstruction-core receipts:

```text
PASS -> ADD -> PAUSE -> SUBTRACT
```

| Gate | Function |
|---|---|
| `PASS` | verify exact replay or payload closure plus hashes |
| `ADD` | count deterministic costs: core, residual, receipt, protocol, dictionary, energy |
| `PAUSE` | zero-delta logical event fence; wall-clock time is metadata only |
| `SUBTRACT` | compute trust/compression deltas only after costs are sealed |

Timestamps may appear in human logs, but they are excluded from receipt hashes
and cannot affect admission.

## 8. Godel Gauntlet

`Godels_Gauntlet` is the promotion/quarantine gate:

```text
the stack may propose and defend,
but may not promote itself without receipts
```

It blocks the suspicious pattern:

```text
human label -> trusted theorem
```

and replaces it with:

```text
human label -> routing hint
F0 -> compiled atom -> receipt -> closure -> admission decision
```

## 9. Claim Boundary

This document does not claim that the foundation compiler proves external
mathematics. It defines the local trust boundary:

```text
trusted object = compiled, receipted, closed object
```

Everything else is a hint, fixture, negative control, or HOLD candidate.

## 10. Origin Metadata

Historical origin is retained as metadata:

```yaml
provenance:
  human_origin: metadata_only
  era_context: metadata_only
  institutional_prestige: metadata_only
  theorem_label: routing_hint_only
  aesthetic_elegance: routing_hint_only
  accepted_result: hold_until_forward_receipted
  formal_closure: admission_candidate
```

This distinguishes:

```text
historical origin != formal admissibility
```

The stack may record that an equation came from a strange era, private notebook,
philosophical program, dense internal notation, institutional seminar, or
beautiful intuition. None of those facts can promote it. They only help route
the candidate into the forward compiler.

The fair version is:

```text
Humans may discover; the compiler must admit.
```

## 11. Derived Fixture Example

The first small derived physics atom is:

```text
shared-data/data/buoyancy_added_mass_mobius/buoyancy_added_mass_mobius_receipt.json
```

It records `lambda_BAM`, a Mass-Number Mobius compression of the early-time
buoyancy added-mass equation:

```text
lambda_BAM(MN_rho, C) =
  g * alpha_C * MN_rho / (1 + kappa_C * MN_rho)
```

This fixture is accepted only as:

```text
ACCEPT_FIXTURE_WITH_BOUND_CORRECTION
```

It shows the intended pattern: an external equation can be a candidate, but the
accepted object is the normalized equation atom, exact equivalence checks,
inverse check, residual policy, and receipt. The fixture does not promote a new
fluid theorem or broad experimental claim.

## 12. Mass Number Transform Registry

The Mass Number transform registry is:

```text
4-Infrastructure/shim/mass_number_transform_registry.py
```

Current receipt:

```text
shared-data/data/mass_number_transform_registry/mass_number_transform_registry_receipt.json
```

Human summary:

```text
shared-data/data/mass_number_transform_registry/mass_number_transform_registry.md
```

Receipt hash:

```text
b215abe8cca08253dd62a2c2e84ff1f90fbd8e7eb5b2bb02d60dec39bbea2b9c
```

It records exact algebraic transform kernels that compile repeated pair
equations into:

```text
MN(a,b) = (a-b)/(a+b)
MN plus small transform opcode
```

Accepted exact-kernel opcodes:

```text
MN
MN_RATIO_INV
MN_MOBIUS_LOAD
MN_SPLIT
MN_REDUCED
MN_PAIR_PRODUCT
MN_BLEND
MN_REFLECT
MN_TRANSMIT_POWER
MN_BINARY_P
MN_ELASTIC_1D
```

`MN_BINARY_ENTROPY` is recorded only as `HOLD_ANALYTIC` until log base, numeric
precision, and approximation/error receipts are declared.

Decision:

```text
ACCEPT_REGISTRY_WITH_HOLD_ANALYTIC
```

This registry does not prove every domain equation named in its route surface.
It admits only the exact algebraic identities checked by the local receipt.
Domain-specific uses still need source equations, residual policy, and
forward-foundation admission.

## 13. Cross-Domain Kernel Adapters

The cross-domain kernel adapter registry is:

```text
4-Infrastructure/shim/cross_domain_kernel_adapter_registry.py
```

Current receipt:

```text
shared-data/data/cross_domain_kernel_adapters/cross_domain_kernel_adapter_registry_receipt.json
```

Human summary:

```text
shared-data/data/cross_domain_kernel_adapters/cross_domain_kernel_adapter_registry.md
```

Receipt hash:

```text
a66552526d5213a8122ce8f1efa56137f70c707d991ac7fdc90dc83d970ac081
```

The adapter equation is:

```text
X_d = A_d[K_j(theta)] + R_d + chi0
same shape does not imply same law
```

Decision:

```text
HOLD_CROSS_DOMAIN_WITH_ACCEPTED_KERNEL_ADAPTERS
```

This admits the doctrine, not broad domain truth. Reusing a Mass Number kernel
across fluid mechanics, impedance boundaries, routing probability, two-body
mechanics, expert blending, moving-sofa contact geometry, or seismic horizon
inference is lawful only when the adapter has its own source, replay, residual,
and closure receipts.

The moving-sofa route remains `HOLD_CONTACT_TOPOLOGY` until corridor geometry,
signed-distance convention, motion path replay, collision closure, and area
accounting exist. The seismic-horizon route remains `HOLD_BOUNDARY_WITNESS`
until boundary-wave data and material residual models are receipted.

## 14. Magnetic Derivative Kernels

The magnetic derivative kernel probe is:

```text
4-Infrastructure/shim/magnetic_derivative_kernel_probe.py
```

Current receipt:

```text
shared-data/data/magnetic_derivative_kernels/magnetic_derivative_kernel_receipt.json
```

Human summary:

```text
shared-data/data/magnetic_derivative_kernels/magnetic_derivative_kernel.md
```

Receipt hash:

```text
b4617a8ff31586250efafd13e3ed402535fcad5d564922599aaa3cb95134c7e3
```

Decision:

```text
HOLD_MAGNETIC_DOMAIN_WITH_ACCEPTED_FIXTURES
```

Accepted local fixtures:

```text
d/dB [B^2/(2*mu)] = B/mu
F_x = m*dB/dx
F_B = q*cross(v,B)
Gamma_mu = MN(mu2,mu1)
```

These are algebra/vector fixtures and adapter candidates only. Field equations
such as Faraday induction, Ampere-Maxwell routing, Alfven-speed routes,
susceptibility contrast, hysteresis, and material-response claims stay HOLD
until unit systems, gauge/sign conventions, boundary conditions, source data,
and residual policies are receipted.

## 15. Solids Physics Kernels

The solids physics kernel probe is:

```text
4-Infrastructure/shim/solids_physics_kernel_probe.py
```

Current receipt:

```text
shared-data/data/solids_physics_kernels/solids_physics_kernel_receipt.json
```

Human summary:

```text
shared-data/data/solids_physics_kernels/solids_physics_kernel.md
```

Receipt hash:

```text
98501df5a36ddd8a103ff40e6c8973f93e5271df325dd43ebdbebe59e896defb
```

Decision:

```text
HOLD_SOLIDS_DOMAIN_WITH_ACCEPTED_FIXTURES
```

Accepted local fixtures:

```text
sigma = E*epsilon
U = E*epsilon^2/2 = sigma^2/(2E)
dU/depsilon = sigma
G = E/(2*(1+nu))
K = E/(3*(1-2*nu))
E_eff = S/2*(1-MN(E1,E2)^2)
Gamma_Z = MN(Z2,Z1)
```

These are local algebra fixtures and adapter candidates only. Elastic wave
speed, plasticity, fracture, anisotropy, finite-element boundary value,
geometry, and material-model claims stay HOLD until units, conventions, source
data, boundary conditions, and residual policies are receipted.

## 16. Easy-Wins Route Map

The cross-domain easy-wins route map is:

```text
4-Infrastructure/shim/cross_domain_easy_wins_route_map.py
```

Current receipt:

```text
shared-data/data/cross_domain_easy_wins/cross_domain_easy_wins_route_map_receipt.json
```

Human summary:

```text
shared-data/data/cross_domain_easy_wins/cross_domain_easy_wins_route_map.md
```

Receipt hash:

```text
ac1fe2ca6ee469c046cdb5fc78cef9efca6a601aee2e5270ef4b8c5854bb1e2e
```

Decision:

```text
ADMIT_ROUTE_MAP_HOLD_FIRST
```

The ranked route queue is:

```text
circuits_impedance
thermal_diffusion
acoustics_waves
probability_routing
orbital_two_body
chemistry_equilibrium
optics_fresnel
statistics_effect_size
bio_expression_contrast
geometry_contact
```

This is a planning receipt only. It ranks low-cost probes where exact local
algebra can be checked before nonlinear, field, geometry, measurement, or
material-law claims are touched.
