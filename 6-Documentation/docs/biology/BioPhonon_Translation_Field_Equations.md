# BioPhonon Translation Field Equations

Status: EQUATION_UPDATE
Claim state: FORMAL_SCAFFOLD / ANALOGY_BOUNDED

This note defines the BioPhonon Translation Field: the class of evolved systems that convert mechanical wave propagation into actionable meaning. It includes percussive foragers, web/modal graph sensors, substrate vibration insects, seismic mammals, aquatic lateral-line systems, echolocators, and plant stress-ultrasound emission.

Boundary: this is not proof that plants have subjective experience or intentional speech. The plant-stress sound source is treated as an informative biomechanical emission term in a broader phonon-mediated translation equation.

---

## 1. Base BioPhonon field

Universal medium equation:

```math
\mathcal{M}\ddot{u}
+
\mathcal{C}\dot{u}
+
\mathcal{K}u
+
\mathcal{N}(u,\nabla u)
=
S_a(x,t)
+
S_w(x,t)
+
N(x,t)
```

Observation equation:

```math
y_i(t)
=
\mathcal{R}_i[u(x_i,t)]
+
\eta_i(t)
```

Translation equation:

```math
P(z\mid y_{1:n},a)
\propto
P(y_{1:n}\mid z,a)P(z)
```

Action policy:

```math
a^*
=
\arg\max_a
\frac{
I(z;y_{1:n}\mid a)
}{
E_{act}(a)+E_{move}(a)+C_{compute}(a)+C_{risk}(a)
}
```

---

## 2. Plant-stress ultrasonic emission term

The plant-stress source term adds an emitter that is not a moving animal sensor, but a biomechanical state-to-sound translator.

```math
S_w(x,t)
\rightarrow
S_{world}(x,t)
+
S_{plant}(x,t;\sigma_h,w,i,\chi)
```

where:

```text
σ_h = hydraulic / xylem tension stress
w   = water deficit / dehydration state
i   = injury or cutting state
χ   = species / tissue / morphology parameters
```

The plant emission source can be modeled as a sparse ultrasonic pulse train:

```math
S_{plant}(x,t)
=
\sum_k
A_k(\sigma_h,w,i,\chi)
\,g(t-t_k;f_k,Q_k)
\,\delta(x-x_{plant})
```

with event rate:

```math
\lambda_{plant}(t)
=
\lambda_0
+
\lambda_w\,\Phi_w(w(t))
+
\lambda_i\,\Phi_i(i(t))
+
\lambda_h\,\Phi_h(\sigma_h(t)).
```

Interpretation:

```text
Plant state -> ultrasonic event statistics -> receiver inference.
```

---

## 3. Cavitation-compatible source hypothesis

A conservative biomechanical source model treats plant sounds as cavitation-compatible xylem events rather than intentional vocalization:

```math
\sigma_h(t) > \sigma_{cav}
\Rightarrow
\Delta P_{xylem}(t)
\Rightarrow
S_{plant}(t).
```

One possible event kernel:

```math
g(t;f,Q)
=
H(t)e^{-\pi f t/Q}\sin(2\pi f t).
```

This keeps the plant term compatible with mechanical emission:

```text
hydraulic stress / injury -> elastic release / cavitation-like pulse -> airborne ultrasound.
```

---

## 4. Receiver inference: who listens?

For any receiver organism r:

```math
y_r(t)
=
\mathcal{H}_{air,plant\to r}[S_{plant}](t)+\eta_r(t)
```

and:

```math
P(z_{plant}\mid y_r)
\propto
P(y_r\mid z_{plant})P(z_{plant}).
```

Receiver action:

```math
a_r^*
=
\arg\max_{a_r}
\frac{
I(z_{plant};y_r\mid a_r)
}{
E_{move}(a_r)+C_{compute}(a_r)+C_{risk}(a_r)
}.
```

Examples:

```text
moth: avoid oviposition on stressed host plant
bat/mouse/insect: detect ultrasonic environmental state
neighbor plant: possible stress preconditioning route, currently research-bound
farmer sensor: irrigation / stress monitoring
```

---

## 5. Updated universal BioPhonon translation equation

With plant-stress ultrasound included:

```math
\boxed{
\mathcal{M}\ddot{u}
+
\mathcal{C}\dot{u}
+
\mathcal{K}u
+
\mathcal{N}(u,\nabla u)
=
S_{self}(x,t)
+
S_{prey}(x,t)
+
S_{mate}(x,t)
+
S_{predator}(x,t)
+
S_{plant}(x,t)
+
N_{env}(x,t)
}
```

Observation:

```math
\boxed{
y_i(t)
=
\mathcal{R}_i[u(x_i,t)]
+
\eta_i(t)
}
```

Translation:

```math
\boxed{
P(z\mid y_{1:n},a)
\propto
P(y_{1:n}\mid z,a)P(z)
}
```

Action:

```math
\boxed{
a^*
=
\arg\max_a
\frac{
I(z;y_{1:n}\mid a)
}{
E_{act}(a)+E_{move}(a)+C_{compute}(a)+C_{risk}(a)+L_{FAMM}(a)
}
}
```

---

## 6. Stack translation

Plant-stress ultrasound adds a new category: passive biomechanical source emission.

```text
not only: active probe -> response -> meaning
also: internal stress -> emitted phonon signature -> external listener inference
```

Compression analogy:

```text
internal state strain -> sparse acoustic/phonon events -> classifier route -> FAMM scar/update
```

So the compression/semantic equivalent is:

```math
route^*
=
\arg\max_{probe/listen}
\frac{
I(hidden\_state;response\mid probe/listen)
}{
C_{probe}+C_{listen}+C_{decode}+C_{interface}+C_{risk}+L_{FAMM}
}.
```

---

## 7. Warden boundary

Allowed:

```text
Use plant-stress sounds as a biomechanical ultrasonic source term.
Use the term to expand BioPhonon translation to include passive stress emissions.
Use classifier/inference framing for animal, plant, or engineered receivers.
```

Blocked:

```text
Do not claim plants intentionally scream.
Do not claim plant sentience or pain from ultrasonic emissions.
Do not claim plant-to-animal communication unless receiver behavior is empirically shown.
Do not promote BioPhonon claims outside the measured stress-sound/source-receiver boundary.
```

---

## 8. Source anchor

Primary source:

```text
Khait et al. 2023. Sounds emitted by plants under stress are airborne and informative. Cell 186(7):1328-1336.e10. DOI: 10.1016/j.cell.2023.03.009
```
