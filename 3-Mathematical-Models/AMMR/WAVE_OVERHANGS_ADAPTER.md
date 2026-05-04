# Wave Overhangs Adapter

## Purpose

This repository is treated as the wavefront toolpath-planning branch of the pressure / cavitation / vibration / diffusion catalog.

The adapter couples three layers:

```text
wavefront path planning
    -> heat-2D thermal residue simulation
    -> calibrated warp-risk envelope
```

Core role:

```text
unsupported overhang region
    -> wavefront / level-set path planning
    -> FDM deposition path
    -> thermal residue field
    -> warping or stable overhang
```

This file is a technical integration contract, not a claim that the slicer alone solves polymer mechanics.

---

## 1. Native objects

Let:

| Symbol | Meaning |
|---|---|
| `Omega_o` | unsupported overhang region to fill |
| `partial Omega_s` | supported / perimeter seed boundary |
| `M(x,y)` | printable geometry mask |
| `T(x,y)` | wavefront arrival / distance field |
| `lambda` | line spacing / wavelength |
| `Gamma_k` | kth generated wave track |
| `x_nozzle(t)` | time-parametrized nozzle trajectory |
| `u(x,y,t)` | thermal residue / cooling field |
| `alpha(x,y)` | effective diffusivity field |
| `f(x,y,t)` | deposition, reheat, and cooling source term |

---

## 2. Wavefront generation layer

A wavefront arrival field can be approximated by an Eikonal equation:

```math
|\nabla T(x,y)| = \frac{1}{c(x,y)}
```

where `c(x,y)` is a geometry-dependent propagation weight.

Boundary condition:

```math
T|_{\partial\Omega_s}=0
```

Blocked/outside region:

```math
(x,y)\notin\Omega_o \Rightarrow M(x,y)=0
```

Wave tracks are level sets:

```math
\Gamma_k = \{(x,y): T(x,y)=k\lambda\}\cap\Omega_o
```

A narrow-neck pruning gate should prevent fragile branches:

```math
w_{neck}(x,y)<w_{min}\Rightarrow M(x,y)=0
```

where `w_min` corresponds to the slicer `Minimum wave width` setting.

---

## 3. Toolpath ordering layer

The same level-set geometry can be emitted under different ordering policies:

| Policy | Model interpretation | Expected thermal effect |
|---|---|---|
| `Monotonic` | one consistent direction per line | longer cooling interval between neighbors |
| `Zig Zag` | connected depth-first back-and-forth path | lower travel, higher local heat buildup risk |
| `Smart` | start from better-supported end | lower unsupported-start and anchor-risk penalty |

Define an ordering functional:

```math
\pi: \{\Gamma_k\}\rightarrow x_{nozzle}(t)
```

where `pi` maps unordered wavefront curves into a nozzle-time trajectory.

---

## 4. Heat-2D coupling layer

A generated wave toolpath is treated as a moving thermal/material source:

```math
f_{nozzle}(x,y,t)=Q_n\exp\left(-\frac{\|\mathbf{x}-\mathbf{x}_{nozzle}(t)\|^2}{2\sigma_n^2}\right)
```

Then solve the heat-2D compatible equation:

```math
\partial_t u = \nabla\cdot(\alpha(x,y)\nabla u)+f_{nozzle}+f_{reheat}+f_{cool}
```

Cooling sink approximation:

```math
f_{cool}(x,y,t)=-h_f(u-u_{air})
```

Reheat source from subsequent layers:

```math
f_{reheat}(x,y,t)=\sum_{\ell=1}^{N}Q_{\ell}\exp\left(-\frac{\|\mathbf{x}-\mathbf{x}_{\ell}(t)\|^2}{2\sigma_{\ell}^{2}}\right)
```

---

## 5. Slicer parameter bridge

| WaveOverhangs setting | Adapter parameter | Effect |
|---|---|---|
| line spacing | `lambda` | wavefront interval / thermal line spacing |
| line width | `sigma_n`, bead width | source radius and material overlap |
| flow ratio | `Q_n` | deposited material and heat amplitude |
| print speed | `|dx_nozzle/dt|` | dwell time, cooling interval, bonding |
| fan speed | `h_f` | cooling sink strength |
| perimeter overlap | `A_anchor`, boundary coupling | anchor conduction and edge attachment |
| minimum wave width | `w_min` | branch pruning threshold |
| monotonic / zig-zag / smart | `pi` | path-ordering and reheat pattern |

---

## 6. Warp-risk observables

### 6.1 Thermal-gradient proxy

```math
G_T(x,y,t)=\|\nabla u(x,y,t)\|
```

Large gradients imply differential contraction risk.

### 6.2 Hot-time exposure

```math
t_{hot}(x,y)=\int \mathbf{1}_{u(x,y,t)>T_g}\,dt
```

where `T_g` is the glass-transition / mobility threshold proxy.

### 6.3 Reheat activation proxy

```math
R_{reheat}(x,y)=\max_t \mathbf{1}_{u(x,y,t)>T_g}
```

This estimates where earlier strands may re-enter a mobile polymer state.

### 6.4 Anchor distance penalty

```math
A_{anchor}(x,y)=\exp\left(-\frac{d(x,y,\partial\Omega_s)}{\ell_a}\right)
```

where `ell_a` is an anchor coupling length.

### 6.5 Span-size proxy

```math
C_{span}\propto L_{unsupported}^{2}
```

Large unsupported spans should be considered high-risk until calibrated print data says otherwise.

### 6.6 Curl-risk score

```math
C_{curl}=w_1\max G_T+w_2\max R_{reheat}+w_3\max t_{hot}+w_4C_{span}-w_5\max A_{anchor}
```

Interpretation:

```text
higher C_curl -> higher predicted warp/failure risk
lower C_curl  -> better candidate for unsupported wave overhang
```

---

## 7. Calibration receipts

Each print test should log:

| Receipt | Required data |
|---|---|
| geometry receipt | STL/model name, overhang area, unsupported span, holes/concavity flags |
| slicer receipt | line spacing, width, flow ratio, pattern, speed, fan, overlap, min width |
| material receipt | polymer, filler, nozzle temp, bed temp, chamber temp, cooling duct |
| simulation receipt | grid size, timestep, alpha field, source amplitude, boundary conditions |
| outcome receipt | pass/fail, max curl, detachment, bead break, surface roughness, photo/hash |

Minimum calibration target:

```math
C_{curl}\uparrow \Rightarrow P(failure)\uparrow
```

Do not promote the score beyond `CALIBRATED_ENGINEERING_DELTA` until this monotonic relationship is measured over multiple geometries and materials.

---

## 8. Test cases

### Test A: single wave stripe

Purpose: validate moving-source thermal trail.

Expected behavior:

- smooth trail behind nozzle,
- peak temperature decays after source passes,
- stronger fan coefficient shortens hot lifetime.

### Test B: adjacent wave lines

Purpose: test line spacing / width / flow-ratio coupling.

Expected behavior:

- tighter spacing increases overlap,
- higher flow ratio increases heat accumulation,
- slower print speed increases dwell and bonding but may reheat earlier lines.

### Test C: monotonic vs zig-zag ordering

Purpose: compare ordering policies.

Expected behavior:

- monotonic gives neighboring lines more cooling time,
- zig-zag lowers travel but can increase local heat accumulation,
- smart ordering should reduce unsupported-start risk.

### Test D: large unsupported span

Purpose: detect when the wave strategy should fall back to support.

Expected behavior:

- larger spans increase curl-risk proxy,
- two-sided cooling reduces vertical-gradient risk if modeled in a layered extension,
- fiber-filled material proxy should use higher conductivity, lower expansion risk, and higher stiffness in downstream mechanical model.

---

## 9. Failure gates

| Gate | Trigger | Action |
|---|---|---|
| thermal-gradient gate | `max G_T > theta_G` | slow print / raise fan / change path order |
| hot-time gate | `max t_hot > theta_t` | increase line interval cooling time |
| span gate | `L_unsupported > theta_L` | fall back to support / bridge / hybrid support |
| anchor gate | `A_anchor < theta_A` at line start | use smart start or add perimeter overlap |
| branch gate | `w_neck < w_min` | split/prune branch before propagation |

---

## 10. Scope warning

This adapter does not claim wave overhangs are fully solved by heat diffusion.

Pure heat diffusion does not model:

- bead sag,
- nozzle pressure deformation,
- shape-memory polymer behavior,
- viscoelastic stress relaxation,
- crystallization,
- full 3D strand mechanics.

Correct role:

```text
wavefront toolpath geometry -> thermal afterimage -> calibrated warping-risk proxy
```

Downstream mechanical models should consume this field instead of being hidden inside the diffusion solver.

---

## 11. Catalog placement

This branch belongs beside:

```text
pressure / cavitation / vibration / diffusion
    -> heat-2D residue model
    -> passive fluidic geometry
    -> rocket cooling geometry
    -> wavefront toolpath geometry
```

The shared abstraction is:

```text
geometry + source + diffusion/propagation law -> residual field -> failure envelope
```
