# Acoustic Black Hole (Analogue Gravity) — Complete Equations

> Also known as "dumb holes." First proposed by Unruh (1981). Experimentally
> realized in Bose–Einstein condensates (Steinhauer, 2014–2019) and water tanks
> (Weinfurtner et al., 2011; Torres et al., 2017).

---

## 1. Fluid Dynamics Foundation

Continuity equation and Euler equation for an inviscid, irrotational, barotropic fluid:

$$ \partial_t \rho + \nabla \cdot (\rho \mathbf{v}) = 0 $$

$$ \rho \left[ \partial_t \mathbf{v} + (\mathbf{v} \cdot \nabla) \mathbf{v} \right] = -\nabla p $$

Irrotational flow means the velocity field is the gradient of a velocity potential:

$$ \mathbf{v} = -\nabla \psi $$

**Ref:** Unruh, W.G. (1981). "Experimental black-hole evaporation?" *Phys. Rev. Lett.* **46**, 1351–1353.

---

## 2. Acoustic Metric (Unruh Metric)

Linearized perturbations of the velocity potential $\psi_1$ obey the massless Klein–Gordon equation in a curved spacetime:

$$ \frac{1}{\sqrt{-g}} \partial_\mu (\sqrt{-g} g^{\mu\nu} \partial_\nu \psi_1) = 0 $$

The acoustic metric in $(3+1)$ form (up to conformal factor $\rho/c$):

$$ g_{\mu\nu} = \frac{\rho}{c} \begin{pmatrix} -(c^2 - v^2) & -v^j \\ -v^i & \delta_{ij} \end{pmatrix} $$

Line element:

$$ ds^2 = \frac{\rho}{c} \left[ -(c^2 - v^2) dt^2 - 2 v_i dx^i dt + \delta_{ij} dx^i dx^j \right] $$

**Ref:** Unruh (1981); Visser, M. (1998). *Class. Quantum Grav.* **15**, 1767 [arXiv:gr-qc/9712010].

---

## 3. Wave Equation for Phonons in a Flowing Fluid

The velocity potential perturbation $\phi \equiv \psi_1$ satisfies:

$$ \partial_t \left( \frac{\rho}{c^2} (\partial_t \phi + \mathbf{v} \cdot \nabla \phi) \right) + \nabla \cdot \left( \frac{\rho}{c^2} (\partial_t \phi + \mathbf{v} \cdot \nabla \phi) \mathbf{v} - \rho \nabla \phi \right) = 0 $$

Compact form:

$$ \square_g \phi = \frac{1}{\sqrt{-g}} \partial_\mu (\sqrt{-g} g^{\mu\nu} \partial_\nu \phi) = 0 $$

**Ref:** Barcelo, C., Liberati, S., & Visser, M. (2005). *Living Rev. Relativity* **8**, 12 [arXiv:gr-qc/0505065].

---

## 4. Dispersion Relations

### Homogeneous fluid (linear)
$$ \omega = c k $$

### Bose–Einstein condensate (Bogoliubov)
$$ \omega^2 = c^2 k^2 + \frac{\hbar^2 k^4}{4m^2} $$

or equivalently:

$$ \omega^2 = c^2 k^2 \left(1 + \frac{\xi^2 k^2}{4}\right) $$

where $\xi = \hbar / (mc)$ is the **healing length** and $c = \sqrt{g n/m}$ is the speed of sound.

### Doppler-shifted (flowing fluid)
$$ (\omega - \mathbf{v} \cdot \mathbf{k})^2 = c^2 k^2 $$

### Doppler-shifted in BEC
$$ (\omega - \mathbf{v} \cdot \mathbf{k})^2 = c^2 k^2 + \frac{\hbar^2 k^4}{4m^2} $$

### Group velocity in BEC
$$ v_g = \frac{d\omega}{dk} = \frac{c^2 k + \frac{\hbar^2 k^3}{2m^2}}{\sqrt{c^2 k^2 + \frac{\hbar^2 k^4}{4m^2}}} $$

At $k\xi \ll 1$: $v_g \approx c$ (relativistic). At $k\xi \gg 1$: $v_g \approx \hbar k / m$ (free particle).

**Ref:** Garay et al. (2000) *PRL* **85**, 4643; Recati et al. (2009) *PRA* **80**, 043603.

---

## 5. Horizon Condition

An acoustic horizon forms where the fluid speed equals the local speed of sound:

$$ |\mathbf{v}(x_H)| = c(x_H) $$

In 1D (flow in $x$-direction, upstream against sound propagation):

$$ v(x_H) = -c(x_H) $$

The horizon separates the subsonic ($|v| < c$) from the supersonic ($|v| > c$) region.

**Ref:** Unruh (1981); Visser (1998).

---

## 6. Surface Gravity

General form:

$$ \kappa = \left. \frac{d}{dx}(c - |v|) \right|_{x=x_H} $$

For 1D stationary flow ($v = -c$ at horizon):

$$ \kappa_H = \left. \frac{d(c - v)}{dx} \right|_{x_H} $$

For a draining bathtub (rotating):

$$ \kappa = \left.\frac{1}{2} \frac{d(c^2 - v_r^2)}{dr}\right|_{r_H} $$

where $v_r$ is the radial flow velocity.

**Ref:** Visser (1998) [gr-qc/9712010]; Barcelo, Liberati, Visser (2005).

---

## 7. Hawking Temperature

$$ T_H = \frac{\hbar \kappa}{2\pi k_B} $$

In terms of the flow gradient at the horizon:

$$ T_H = \frac{\hbar}{2\pi k_B} \left. \frac{d(c - v)}{dx} \right|_{x_H} $$

Typical BEC scale: $c \sim \text{mm/s}$, $L \sim 10\ \mu\text{m}$ $\Rightarrow$ $T_H \sim \text{nK}$.

Steinhauer (2014) experimental value: $T_H \approx 0.45\ \text{nK}$ for $\kappa \approx 0.23\ \text{mm/s/}\mu\text{m}$.

**Ref:** Unruh (1981); Visser (1998); Steinhauer (2014) *Nature Phys.* **10**, 864 [arXiv:1409.6550].

---

## 8. Bogoliubov Transformation (In/Out Mode Mixing)

Annihilation operators of upstream (in) and downstream (out) modes:

$$ \hat{a}_{\omega}^{\text{out}} = \alpha_{\omega} \hat{a}_{\omega}^{\text{in}} + \beta_{\omega} \hat{b}_{\omega}^{\text{in}\dagger} $$

$$ \hat{b}_{\omega}^{\text{out}} = \bar{\alpha}_{\omega} \hat{b}_{\omega}^{\text{in}} + \bar{\beta}_{\omega} \hat{a}_{\omega}^{\text{in}\dagger} $$

Normalization:

$$ |\alpha_{\omega}|^2 - |\beta_{\omega}|^2 = 1 $$

Mean Hawking particle number in mode $\omega$:

$$ n_{\omega} = \langle \hat{a}_{\omega}^{\text{out}\dagger} \hat{a}_{\omega}^{\text{out}} \rangle = |\beta_{\omega}|^2 $$

For a black hole horizon:

$$ \alpha_{\omega} = e^{\pi \omega / \kappa}, \quad \beta_{\omega} = e^{-\pi \omega / \kappa} $$

Resulting Planck spectrum:

$$ |\beta_{\omega}|^2 = \frac{1}{e^{2\pi \omega / \kappa} - 1} = \frac{1}{e^{\hbar \omega / k_B T_H} - 1} $$

**Ref:** Hawking (1975) *Comm. Math. Phys.* **43**, 199; Macher & Parentani (2009) *PRA* **80**, 043601.

---

## 9. Density-Density Correlation (Hawking Pair Signature)

$$ G^{(2)}(x, x') = \langle \hat{n}(x) \hat{n}(x') \rangle - \langle \hat{n}(x) \rangle \langle \hat{n}(x') \rangle $$

Theoretical expression:

$$ G^{(2)}(x, x') = -\frac{\hbar}{4\pi c(x) c(x')} \left[ \frac{1}{(x - x')^2} + \frac{\coth(\pi \omega_0 / \kappa) \cos[\omega_0 (t - t')]}{|x - x'|^2} \right] $$

Equal-time form (tortoise coordinate):

$$ G^{(2)}(x, x') \propto -\frac{\kappa^2}{\sinh^2[\kappa \eta(x, x')/c]} $$

The hallmark: a negative correlation peak connecting partners across the horizon, along the line:

$$ t + \frac{x}{c_{\infty}} = t' - \frac{x'}{c_{\infty}} $$

Experimental measured quantity:

$$ g^{(2)}(z, z') = \frac{\langle \hat{n}(z) \hat{n}(z') \rangle}{\langle \hat{n}(z) \rangle \langle \hat{n}(z') \rangle} - 1 $$

**Ref:** Balbinot et al. (2008) *PRA* **78**, 021603; Steinhauer (2014, 2016).

---

## 10. Painlevé–Gullstrand Form of the Acoustic Metric

For a spherically symmetric draining flow:

$$ ds^2 = \frac{\rho}{c} \left[ -(c^2 - v_r^2) dt^2 - 2 v_r dr dt + dr^2 + r^2 d\Omega^2 \right] $$

For a rotating (draining bathtub) geometry ($v_r = -A/r$, $v_\phi = B/r$):

$$ ds^2 = \frac{\rho}{c} \left[ -\left(c^2 - v_r^2 - \frac{v_\phi^2}{r^2}\right) dt^2 - 2 v_r dr dt - 2 r v_\phi d\phi dt + dr^2 + r^2 d\Omega^2 \right] $$

Compare to the Schwarzschild metric in PG coordinates:

$$ ds^2 = - \left(1 - \frac{2GM}{r}\right) dt^2 + 2\sqrt{\frac{2GM}{r}} dt dr + dr^2 + r^2 d\Omega^2 $$

**Ref:** Visser (1998) [gr-qc/9712010]; Painlevé (1921); Gullstrand (1922).

---

## 11. Black Hole Laser Condition (Corley & Jacobson)

With both a black and white hole horizon (a cavity between them), the lasing condition:

$$ \oint k(x, \omega) \, dx = 2\pi n, \quad n \in \mathbb{Z} $$

where $k(x,\omega)$ satisfies the local BEC dispersion:

$$ (\omega - v(x) k)^2 = c(x)^2 k^2 + \frac{\hbar^2 k^4}{4m^2} $$

Exponential growth of the cavity mode:

$$ \phi_{\text{mode}} \propto e^{\Gamma t}, \quad \Gamma = \frac{2\pi \omega}{\kappa} - \text{(boundary losses)} $$

Steinhauer's output power: $P_{\text{laser}} = \hbar \omega_0 \Gamma N_0$

Steinhauer's growth rate (with BEC correction):

$$ \Gamma = \frac{2\pi \omega_0}{\kappa} \frac{1}{1 + (4m c_0^2 / \hbar \kappa)} $$

**Ref:** Corley & Jacobson (1999) *PRD* **59**, 124011; Steinhauer (2014) [arXiv:1409.6550].

---

## 12. Superradiance (Weinfurtner et al.)

Amplification factor for waves scattering off a rotating acoustic black hole:

$$ |R|^2 = |T|^2 \left( \frac{\omega - m\Omega_H}{\omega} \right) $$

Superradiance condition ($|R|^2 > 1$):

$$ \omega < m\Omega_H $$

where $m$ is the azimuthal quantum number and $\Omega_H = v_\phi/r_H$ is the angular velocity at the horizon.

Scattering cross-section for surface water waves:

$$ \sigma(\omega) = \frac{2\pi}{k} \sum_{m=-\infty}^{\infty} |\beta_m(\omega)|^2 $$

Stimulated Hawking emission:

$$ N_{\text{out}} = N_{\text{in}} \times e^{2\pi (\omega - m\Omega_H)/\kappa} $$

**Ref:** Weinfurtner et al. (2011) *PRL* **106**, 021302; Torres et al. (2017) *Nature Phys.* **13**, 833.

---

## 13. Gross–Pitaevskii Equation (BEC Background)

$$ i\hbar \partial_t \Psi_0 = \left( -\frac{\hbar^2}{2m} \nabla^2 + V_{\text{ext}} + g |\Psi_0|^2 \right) \Psi_0 $$

Speed of sound:

$$ c = \sqrt{\frac{g n}{m}} = \sqrt{\frac{4\pi \hbar^2 a_s n}{m^2}} $$

where $g = 4\pi\hbar^2 a_s/m$ and $a_s$ is the s-wave scattering length.

**Ref:** Barcelo, Liberati, Visser (2001) [gr-qc/0011026]; Garay et al. (2000).

---

## Key Experiments

| Experiment | What was observed | Year |
|---|---|---|
| Steinhauer (Technion) | Black hole laser (self-amplifying Hawking radiation) | 2014 |
| Steinhauer (Technion) | Quantum Hawking radiation + entangled pairs | 2016 |
| Muñoz de Nova et al. (Technion) | Thermal Hawking spectrum with measured temperature | 2019 |
| Weinfurtner et al. (UBC) | Stimulated Hawking emission in water tank | 2011 |
| Torres et al. (Nottingham) | Superradiance in vortex flow | 2017 |
