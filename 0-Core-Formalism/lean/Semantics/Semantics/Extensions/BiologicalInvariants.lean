namespace Semantics.Extensions.BiologicalInvariants

/-- 
  # Biological Invariants as Formal Operators
  
  This file defines fundamental biological laws as formal operators on 
  semantic manifolds. Each law represents a constraint or a flow on the 
  biological state space, verified through their canonical equations 
  and integrated into a differential geometric view of biology.
-/

-- ============================================================
-- 1. KLEIBER'S LAW (Metabolic Scaling)
-- ============================================================

/-- 
  Kleiber's Law: Metabolic rate (P) scales with mass (M) to the 3/4 power.
  Equation: P = P₀ * M^(3/4)

  MANIFOLD RATIONALE:
  The functional dimension of the metabolic manifold is effectively 4 (3 spatial + 1 fractal). 
  In this view, biological organisms are space-filling fractal networks that optimize 
  energy transport. The 3/4 exponent arises because the 'effective' volume scales 
  differently than Euclidean 3D volume, representing a fractal-to-volume ratio 
  invariant across the tree of life.
-/
structure KleiberScaling where
  p0 : Float    -- Normalization constant (species-specific metabolic intensity)
  mass : Float  -- Mass of the organism (M)
  rate : Float  -- Metabolic rate (P)
  deriving Repr

def kleiberLaw (s : KleiberScaling) : Prop :=
  s.rate = s.p0 * (s.mass ^ 0.75)


-- ============================================================
-- 2. LOTKA-VOLTERRA (Stability of Predator-Prey Manifolds)
-- ============================================================

/-- 
  Lotka-Volterra Equations: Stability of Predator-Prey Manifolds.
  Equations: 
    dx/dt = αx - βxy
    dy/dt = δxy - γy

  MANIFOLD RATIONALE:
  Predator-prey dynamics define a vector field on a 2D state-space manifold. 
  The trajectories are closed orbits (in the simplest case), representing 
  geodesic flow on a symplectic manifold. Stability is the topological 
  persistence of these orbits under perturbations of the interaction metric.
-/
structure LotkaVolterra where
  alpha : Float -- Prey growth rate
  beta  : Float -- Predation rate
  delta : Float -- Predator growth per prey consumed
  gamma : Float -- Predator death rate
  prey  : Float -- Current prey population (x)
  pred  : Float -- Current predator population (y)
  deriving Repr

/-- The vector field (flux) at the current point on the population manifold. -/
def lvFlow (s : LotkaVolterra) : (Float × Float) :=
  let dx := s.alpha * s.prey - s.beta * s.prey * s.pred
  let dy := s.delta * s.prey * s.pred - s.gamma * s.pred
  (dx, dy)


-- ============================================================
-- 3. MICHAELIS-MENTEN (Enzyme Substrate Saturation)
-- ============================================================

/-- 
  Michaelis-Menten: Enzyme Substrate Saturation.
  Equation: v = (Vmax * [S]) / (Km + [S])

  MANIFOLD RATIONALE:
  This represents a hyperbolic scaling of reaction rate on the enzyme-substrate 
  interaction manifold. The Km (Michaelis constant) defines the 'radius of 
  curvature' of the manifold where the linear transport regime transitions 
  into a saturation-limited regime.
-/
structure MichaelisMenten where
  vMax : Float -- Maximum reaction velocity
  kM   : Float -- Michaelis constant (substrate concentration at 1/2 Vmax)
  s    : Float -- Substrate concentration [S]
  v    : Float -- Current reaction velocity
  deriving Repr

def michaelisMentenLaw (m : MichaelisMenten) : Prop :=
  m.v = (m.vMax * m.s) / (m.kM + m.s)


-- ============================================================
-- 4. HODGKIN-HUXLEY (Neural Manifold Dynamics)
-- ============================================================

/-- 
  Hodgkin-Huxley: Neural Manifold Dynamics.
  Equation: I = Cₘ(dV/dt) + gₖn⁴(V - Vₖ) + gₙₐm³h(V - Vₙₐ) + gₗ(V - Vₗ)

  MANIFOLD RATIONALE:
  Neural activity is a trajectory on a 4D dynamical manifold (defined by 
  voltage V and gating variables m, n, h). Action potentials are 
  topological 'excursions' (limit cycles) that return the system to the 
  resting attractor. The gating variables act as the metric coefficients 
  for ionic flow.
-/
structure HodgkinHuxley where
  cm    : Float -- Membrane capacitance
  v     : Float -- Membrane potential
  vk    : Float -- Potassium equilibrium potential
  vna   : Float -- Sodium equilibrium potential
  vl    : Float -- Leak equilibrium potential
  gk    : Float -- Max potassium conductance
  gna   : Float -- Max sodium conductance
  gl    : Float -- Max leak conductance
  n     : Float -- K+ activation gating variable
  m     : Float -- Na+ activation gating variable
  h     : Float -- Na+ inactivation gating variable
  deriving Repr

def hhCurrent (s : HodgkinHuxley) (dvdt : Float) : Float :=
  let ik := s.gk * (s.n ^ 4) * (s.v - s.vk)
  let ina := s.gna * (s.m ^ 3) * s.h * (s.v - s.vna)
  let il := s.gl * (s.v - s.vl)
  s.cm * dvdt + ik + ina + il


-- ============================================================
-- 5. HARDY-WEINBERG EQUILIBRIUM (Genetic State Persistence)
-- ============================================================

/-- 
  Hardy-Weinberg Equilibrium: Genetic State Persistence.
  Equation: p² + 2pq + q² = 1

  MANIFOLD RATIONALE:
  This equation defines a stationary manifold (a surface of equilibrium) 
  within the simplex of allele frequencies. In the absence of evolutionary 
  'forces' (curvature), the population state persists on this flat 
  geometric surface. Deviation from this manifold measures the 
  evolutionary 'acceleration' acting on the gene pool.
-/
structure HardyWeinberg where
  p : Float -- Frequency of allele A
  q : Float -- Frequency of allele a
  deriving Repr

def hardyWeinbergInvariant (s : HardyWeinberg) : Prop :=
  s.p + s.q = 1.0 ∧ (s.p^2 + 2*s.p*s.q + s.q^2 = 1.0)


-- ============================================================
-- 6. ARRHENIUS EQUATION (Metabolic Rate Tensors)
-- ============================================================

/-- 
  Arrhenius Equation: Metabolic Rate Tensors.
  Equation: k = A * exp(-Eₐ / (R * T))

  MANIFOLD RATIONALE:
  The Arrhenius equation describes the 'escape rate' from a local potential 
  minimum on an energy manifold. The activation energy (Ea) is the height of 
  the saddle point between states. In a tensor view, k is the flow velocity 
  along the reaction coordinate, accelerated by the 'thermal metric' of 
  the system (T).
-/
structure ArrheniusRate where
  a    : Float -- Pre-exponential factor
  ea   : Float -- Activation energy
  r    : Float -- Gas constant
  temp : Float -- Absolute temperature (T)
  k    : Float -- Rate constant
  deriving Repr

def arrheniusLaw (s : ArrheniusRate) : Prop :=
  s.k = s.a * Float.exp (-s.ea / (s.r * s.temp))


-- ============================================================
-- 7. FICK'S LAWS (Information/Mass Diffusion)
-- ============================================================

/-- 
  Fick's Laws: Information/Mass Diffusion.
  Equations: 
    1. J = -D * ∇φ
    2. ∂φ/∂t = D * ∇²φ

  MANIFOLD RATIONALE:
  Diffusion is the gradient descent of concentration (or information) 
  toward maximum entropy on a manifold. The second law is the 
  heat equation on a manifold, where the Laplace-Beltrami operator (∇²) 
  governs the 'flattening' of gradients over time. The diffusion 
  coefficient (D) is the scalar component of the transport tensor.
-/
structure FickDiffusion where
  d     : Float -- Diffusion coefficient
  phi   : Float -- Concentration/Information density
  grad  : Float -- Local gradient (∇φ)
  lapl  : Float -- Local Laplacian (∇²φ)
  deriving Repr

def fickFirstLaw (s : FickDiffusion) : Float :=
  -s.d * s.grad

def fickSecondLaw (s : FickDiffusion) : Float :=
  s.d * s.lapl

end Semantics.Extensions.BiologicalInvariants
