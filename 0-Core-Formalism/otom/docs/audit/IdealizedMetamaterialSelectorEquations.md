# Idealized Metamaterial Selector Equations

## Purpose

This note extracts a common idealized equation stack from the literature-backed material families:

- multistable auxetic metamaterials;
- snap-through mechanical metamaterials;
- tunable / modular multistable lattices;
- snap-fit and interlocking metamaterials;
- magnetoelastic metamaterials;
- phononic-bandgap and local-resonance lattices;
- layered van der Waals / graphene-like interlocks.

The goal is not to claim these equations prove the Sidon construction. The goal is to define the physical selector layer that can generate an active-cell set before the algebraic Ruzsa/Bose-Chowla encoding supplies the global Sidon lock.

## Common Abstraction

Each cell `i` has a state vector:

```text
z_i(t) = (x_i, v_i, s_i, q_i, p_i, theta_i, h_i)
```

where:

```text
x_i       = displacement / local snap coordinate
v_i       = velocity
s_i       = discrete stable well or phase state
q_i       = quasi-charge / contact activation proxy
p_i       = phonon load / localized vibrational energy
theta_i   = forced angle, twist, or local registry parameter
h_i       = hysteresis / internal-memory variable
```

The active selector is:

```text
chi_N(i,t) = BurgersGradientGate_N(i,t)
             AND SnapThroughGate_N(i,t)
             AND BandGapPhononGate_N(i,t)
             AND InterlockGate_N(i,t)
```

Density target for the selector:

```text
|{ i <= N : chi_N(i,t_N) = true }| ~ sqrt(N)
```

This remains an active-cell-counting receipt, not an arithmetic Sidon receipt.

## 1. Burgers Shock / Alignment Kernel

Use the viscous Burgers equation as a solved shock-transport kernel:

```text
u_t + u u_x = nu u_xx
```

Traveling shock solution:

```text
u(x,t) = s - (Delta u / 2) tanh((Delta u / (4 nu)) (x - s t - x_0))
```

with:

```text
Delta u = u_L - u_R
s = (u_L + u_R) / 2
shock_thickness ~ 4 nu / Delta u
```

Alignment gate:

```text
B_i(t) = 1 iff |partial_x u(i,t;nu_N)| >= theta_A(N)
```

Smooth gate:

```text
B_i(t) = 1 / (1 + exp[-beta_A (|partial_x u(i,t;nu_N)| - theta_A(N))])
```

Interpretation:

```text
Burgers shock gradient -> local alignment pressure / transport clock
```

## 2. Snap-Through / Multistability Potential

A minimal bistable cell can be modeled by a double-well potential:

```text
V_i(x_i; a_i,b_i) = a_i x_i^4 - b_i x_i^2 - f_i(t) x_i
```

Force law:

```text
m_i x_i'' + c_i x_i' + dV_i/dx_i = F_i(t)
```

Expanded:

```text
m_i x_i'' + c_i x_i' + 4 a_i x_i^3 - 2 b_i x_i = F_i(t) + f_i(t)
```

Snap gate:

```text
S_i(t) = 1 iff V_i(x_barrier) - V_i(x_i) <= W_shock(i,t)
```

or force threshold form:

```text
S_i(t) = 1 iff |F_i(t)| >= F_snap,i
```

Interpretation:

```text
snap-through unit cell -> discrete regime transition and hysteretic energy storage
```

## 3. Hysteretic Energy Dissipation

Energy dissipated over one loading/unloading cycle:

```text
E_diss,i = integral_cycle F_i dx_i
```

State update with internal memory:

```text
h_i' = gamma_i |x_i'| - lambda_i h_i
```

Effective damping:

```text
c_eff,i = c_0,i + c_h,i h_i
```

Dissipation gate:

```text
D_i(t) = 1 iff E_diss,i(t0:t1) >= theta_D(N)
```

Interpretation:

```text
hysteresis area -> measured energy drainage receipt
```

## 4. Phonon Load / Band-Gap Dump Gate

Treat localized vibrational energy as a phonon-load variable:

```text
p_i' = alpha_i |partial_x u(i,t)|^2 + eta_i E_gap,i(t) - lambda_p,i p_i
```

Bandgap mismatch / attenuation condition:

```text
G_i(t) = 1 iff omega_shock(i,t) in [omega_-,i(theta_i), omega_+,i(theta_i)]
```

Phonon dump gate:

```text
P_i(t) = 1 iff G_i(t) = 1 and p_i(t) >= theta_P(N)
```

Interpretation:

```text
bandgap blocks or localizes propagation -> excess wave energy dumps into phonon modes
```

## 5. Local Resonance / Phononic Crystal Approximation

A simple locally resonant lattice has host displacement `x_i` and resonator displacement `y_i`:

```text
m x_i'' = K (x_{i+1} - 2 x_i + x_{i-1}) + k_r (y_i - x_i)
```

```text
m_r y_i'' = -k_r (y_i - x_i)
```

Local resonance frequency:

```text
omega_r = sqrt(k_r / m_r)
```

Bandgap forms near the resonance window where the effective dynamic mass changes sign:

```text
m_eff(omega) = m + (m_r omega_r^2) / (omega_r^2 - omega^2)
```

Bandgap selector:

```text
G_i(t) = 1 iff m_eff(omega_shock) < 0 or k_eff(omega_shock) < 0
```

Interpretation:

```text
local resonance -> vibration mitigation and selective wave attenuation
```

## 6. Interlock / Atomic Tensegrity Interface

Use an angle-dependent interface potential:

```text
U_int(theta_i, r_i) = U_0,i exp[-r_i / ell_i] [1 - A_i cos(n_i theta_i - phi_i)]
```

Residual separating stress:

```text
sigma_sep,i = - partial U_int / partial r_i
```

Angular locking torque:

```text
tau_theta,i = - partial U_int / partial theta_i
```

Interlock gate:

```text
L_i(t) = 1 iff U_barrier,i(theta_i) <= W_shock(i,t) + W_pressure(i,t)
```

Near-threshold condition:

```text
0 < U_release,i - E_i(t) <= epsilon_crit
```

Interpretation:

```text
opposed lattice points + forced angle + pressure/deposition path -> metastable layered interlock
```

## 7. Magnetoelastic / Quasi-Charge Analogue

For magnetoelastic cells or charge-like contact activation:

```text
E_mag,ij = - mu_0/(4 pi r_ij^3) [3 (m_i dot r_hat)(m_j dot r_hat) - m_i dot m_j]
```

Coupled elastic energy:

```text
E_total = sum_i V_i(x_i) + sum_<ij> K_ij/2 (x_i - x_j)^2 + sum_<ij> E_mag,ij
```

Quasi-charge/contact activation:

```text
q_i(t) = sigma(beta_q (E_contact,i - theta_q))
```

Interpretation:

```text
magnetoelastic or contact field -> switchable state, hysteresis, and configuration-dependent bandgap
```

## 8. Emergent-Lattice / Continuum Limit

For a coarse-grained displacement field `w(x,t)`:

```text
rho w_tt + c w_t = div(sigma(w, grad w, h)) + f_shock(x,t)
```

Nonlinear constitutive relation:

```text
sigma = C grad w + alpha |grad w|^2 grad w + sigma_contact(w,theta)
```

Energy functional:

```text
E[w] = integral_Omega [ 1/2 rho |w_t|^2 + Psi(grad w) + V_snap(w) + U_int(theta,w) ] dx
```

Dissipation inequality:

```text
dE/dt <= - integral_Omega [ c |w_t|^2 + lambda_p p + lambda_h h ] dx + Power_in
```

Interpretation:

```text
metamaterial lattice -> near-critical continuum with snap, contact, bandgap, and dissipation channels
```

## 9. Unified Selector Equation

Define the combined gate:

```text
chi_N(i,t) = 1 iff
  |partial_x u(i,t;nu_N)| >= theta_A(N)
  and |F_i(t)| >= F_snap,i(N)
  and omega_shock(i,t) in BandGap_i(theta_i,N)
  and p_i(t) >= theta_P(N)
  and Interlock_i(theta_i,r_i,t) = true
```

Smooth version:

```text
chi_N(i,t) = sigma_A sigma_S sigma_G sigma_P sigma_L
```

where each `sigma_*` is a logistic gate in `[0,1]`.

Active-cell counting receipt:

```text
A_active(N,t_N) = sum_{i=1}^N chi_N(i,t_N)
```

Required density target:

```text
A_active(N,t_N) / sqrt(N) -> 1 in limsup
```

## 10. Handoff to Algebraic Sidon Layer

The selector produces active indices:

```text
I_active(N) = { i <= N : chi_N(i,t_N) = 1 }
```

The arithmetic layer then applies a non-separable encoding:

```text
A_N = { Phi(i) : i in I_active(N) }
```

Sidon/B2 condition:

```text
Phi(a) + Phi(b) = Phi(c) + Phi(d) -> {a,b} = {c,d}
```

Boundary:

```text
The material equations can justify I_active.
They do not by themselves justify PairSumInjective(Phi).
```

## Receipt Status

```text
Receipt: IdealizedMetamaterialSelectorEquations
Status: FORMAL_MECHANISM_DRAFT
Gate: U_scope
Reason: equations are physically standard abstractions for the selector layer, but require parameter identification, simulation, and active-cell counting proof before promotion.
```

## Required Receipts

```text
MaterialParameterReceipt
GeometryParameterReceipt
ShockSpectrumReceipt
BandGapReceipt
PhononDissipationReceipt
InterlockThresholdReceipt
ActiveCellCountingReceipt
ScaleTuningReceipt
SimulationReceipt
PrototypeMeasurementReceipt
```

## Non-Receipts

This note does not supply:

```text
NonseparableEncodingReceipt
GlobalSidonReceipt
CompactDensityReceipt
```

Those remain obligations of the arithmetic layer.
