# Wave Overhangs + Heat-2D Integration

## Why this belongs here

`PrusaSlicer-WaveOverhangs` introduces wave-generated toolpaths for unsupported FDM overhangs. The slicer fills unsupported bottom-surface regions with recursively generated wave paths instead of ordinary support material. The algorithm is described as wave-propagation inspired: waves continue until they fill available space and can diffract around corners and holes.

This makes it a natural companion to `heat-2D`:

```text
wavefront toolpath geometry
    -> deposited polymer strand
    -> cooling / reheating / contraction
    -> warping or stable overhang
```

`heat-2D` should not try to reproduce the slicer. Its role is narrower:

```text
Given a wave-overhang toolpath source pattern, estimate the thermal residue field and failure-risk envelope.
```

---

## Core PDE

The native `heat-2D` equation is:

```math
\partial_t u = \nabla\cdot(\alpha\nabla u)+f
```

For wave overhangs:

| Term | Interpretation |
|---|---|
| `u(x,y,t)` | local thermal state / cooling residue of the overhang layer |
| `alpha(x,y)` | effective thermal diffusivity of polymer, air gap, perimeter anchor, or fiber-filled material |
| `f(x,y,t)` | moving deposition source from nozzle path |
| boundary conditions | cooling from air/fan, anchor conduction into perimeter, or imposed bed/chamber temperature |

---

## Toolpath-as-source model

Represent the wave path as a moving heat source:

```math
f(x,y,t)=Q_n\exp\left(-\frac{\|\mathbf{x}-\mathbf{x}_{nozzle}(t)\|^2}{2\sigma_n^2}\right)
```

where:

| Symbol | Meaning |
|---|---|
| `Q_n` | deposited thermal source strength |
| `x_nozzle(t)` | time-parametrized wave toolpath |
| `sigma_n` | effective bead/nozzle heat radius |

Cooling sink:

```math
f_{cool}(x,y,t)=-h_f(u-u_{air})
```

Combined:

```math
\partial_t u=\nabla\cdot(\alpha\nabla u)+f_{nozzle}+f_{reheat}+f_{cool}
```

---

## Warping risk proxies

WaveOverhangs documentation identifies warping as a coupled thermal, mechanical, and process-control problem. This adapter only models the thermal part directly, but it can output risk proxies.

### 1. Temperature-gradient stress proxy

```math
G_T=\|\nabla u\|
```

Higher local thermal gradients imply higher differential contraction risk.

### 2. Reheat activation proxy

```math
R_{reheat}(x,y)=\max_t \mathbf{1}_{u(x,y,t)>T_g}
```

This estimates where previous strands may re-enter a mobile polymer state.

### 3. Curl-risk proxy

```math
C_{curl}=w_1\|\nabla u\|+w_2R_{reheat}+w_3t_{hot}-w_4A_{anchor}
```

where `A_anchor` measures proximity/connection to perimeter or previously stabilized strand.

### 4. Span-size risk

```math
C_{span}\propto L_{unsupported}^2
```

Large unsupported spans amplify nozzle-pressure and contraction risks.

---

## Parameter bridge to slicer settings

| WaveOverhangs setting | Heat-2D proxy |
|---|---|
| line spacing | source-path spacing / wavelength |
| line width | source radius and deposited amount |
| flow ratio | source amplitude `Q_n` |
| print speed | source dwell time |
| fan speed | cooling coefficient `h_f` |
| perimeter overlap | anchor conduction / boundary coupling |
| minimum wave width | geometry mask pruning threshold |
| monotonic / zig-zag / smart | source ordering and local reheat history |

---

## Test cases

### Test A: single wave stripe

Goal: validate moving-source thermal trail.

Expected:

- smooth trail behind nozzle,
- peak temperature decays after source passes,
- stronger fan coefficient reduces hot lifetime.

### Test B: adjacent wave lines

Goal: test line spacing / line width / flow ratio coupling.

Expected:

- tighter spacing increases overlap,
- higher flow ratio increases heat accumulation,
- slower print speed increases local dwell and bonding but may reheat earlier lines.

### Test C: monotonic vs zig-zag ordering

Goal: quantify local heat buildup from path ordering.

Expected:

- monotonic gives neighboring lines more cooling time,
- zig-zag lowers travel but can increase local heat accumulation,
- smart ordering should reduce unsupported-start risk, though geometry support is outside pure heat diffusion.

### Test D: large unsupported span

Goal: identify when thermal gradients and hot lifetime become too large.

Expected:

- larger spans increase curl-risk proxy,
- uniform two-sided cooling reduces vertical-gradient proxy if modeled with layered extension,
- fiber-filled material proxy should use higher conductivity, lower expansion risk, and higher stiffness in downstream mechanical model.

---

## Scope warning

This is not a full FDM mechanics model. Pure `heat-2D` does not solve:

- bead sag,
- viscoelastic shape memory,
- nozzle pressure deformation,
- polymer crystallization,
- 3D strand geometry,
- mechanical stress equilibrium.

Correct use:

```text
thermal afterimage and risk proxy generator for wave-overhang toolpaths
```

Downstream mechanical models should consume the heat-field output rather than be hidden inside this solver.
