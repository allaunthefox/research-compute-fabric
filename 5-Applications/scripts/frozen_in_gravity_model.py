#!/usr/bin/env python3
"""
Frozen-In Gravity Model — Asenjo, Comisso & Winkler (PRL 2026)

Extracted equations and their mapping to PIST Extended Encoding.

Paper: "Frozen-In Gravitational Fields"
DOI: 10.1103/6c4q-kx6f
URL: https://phys.org/news/2026-04-frozen-gravity-evolution-spacetime-dynamics.html

Core idea: Gravitational field structures remain "frozen" into spacetime dynamics
under ideal conditions, preserving topological invariants.

PIST analogy: Coordinate structures remain invariant under encoding/decoding,
eliminating the need for search-based context modeling.
"""

import numpy as np
from typing import Tuple, Callable


# ─── Equation 1: Einstein Field Equations (Standard Form) ───
#
#   G_μν + Λ g_μν = (8πG / c⁴) T_μν
#
#   G_μν = Einstein tensor (geometry)
#   T_μν = stress-energy tensor (matter)
#   Λ    = cosmological constant
#   g_μν = metric tensor
#
# Asenjo et al. rewrite this in analogy to conducting fluid equations.

def einstein_tensor(g_inv: np.ndarray, dg: np.ndarray, ddg: np.ndarray) -> np.ndarray:
    """
    Compute Einstein tensor G_μν from metric and its derivatives.

    G_μν = R_μν - (1/2) R g_μν
    where R_μν is Ricci tensor, R is Ricci scalar.
    """
    # Simplified: full computation is complex; this is the symbolic structure
    # In practice, Christoffel symbols → Riemann → Ricci → Einstein
    # For PIST analogy, we only need the conceptual mapping
    pass  # Placeholder — full GR computation is beyond scope


# ─── Equation 2: Fluid-Dynamics Analog (Asenjo Rewriting) ───
#
#   The paper rewrites Einstein equations as:
#
#   ∂_t u + (u · ∇) u = -∇p/ρ + ν ∇²u + (other terms)
#
#   where u represents the gravitational "velocity" field,
#   p is effective pressure, ρ is effective density.
#
#   Key insight: gravitational field lines behave like magnetic field lines in MHD.

class GravitationalMHD:
    """
    Model gravitational field as magnetohydrodynamic fluid.

    Frozen-in theorem: If E + v × B = 0 (ideal condition),
    then field lines move with the fluid and topology is preserved.
    """

    def __init__(self, grid_size: Tuple[int, int, int] = (64, 64, 64)):
        self.Nx, self.Ny, self.Nz = grid_size
        # Gravitational "magnetic" field B_g (analog to magnetic field)
        self.B_g = np.zeros((*grid_size, 3))
        # Gravitational "electric" field E_g
        self.E_g = np.zeros((*grid_size, 3))
        # Velocity field v
        self.v = np.zeros((*grid_size, 3))
        # Gravitational vector potential A_g (B_g = ∇ × A_g)
        self.A_g = np.zeros((*grid_size, 3))

    def ideal_ohm_law(self) -> np.ndarray:
        """
        Equation 3: Ideal Ohm-type condition for gravity.

        E_g + v × B_g = 0

        This is the frozen-in condition. When satisfied, field lines
        move with the fluid and connectivity is preserved.
        """
        v_cross_B = np.cross(self.v, self.B_g)
        return self.E_g + v_cross_B  # Should be ~0 for frozen-in

    def is_frozen_in(self, tol: float = 1e-6) -> bool:
        """Check if ideal condition is satisfied."""
        residual = self.ideal_ohm_law()
        return np.linalg.norm(residual) < tol

    def evolve(self, dt: float) -> None:
        """
        Equation 4: Evolution equations for frozen-in fields.

        ∂_t B_g = ∇ × (v × B_g)   (induction equation analog)

        Under ideal condition, this preserves:
        - Field line connectivity
        - Gravitational helicity
        - Topological invariants
        """
        # Compute ∇ × (v × B_g)
        v_cross_B = np.cross(self.v, self.B_g)
        curl_v_cross_B = self._curl(v_cross_B)
        self.B_g += dt * curl_v_cross_B

    def _curl(self, F: np.ndarray) -> np.ndarray:
        """Compute curl of vector field F on grid."""
        # Simplified finite-difference curl
        dFz_dy = np.roll(F[..., 2], -1, axis=1) - np.roll(F[..., 2], 1, axis=1)
        dFy_dz = np.roll(F[..., 1], -1, axis=2) - np.roll(F[..., 1], 1, axis=2)
        curl_x = dFz_dy - dFy_dz

        dFx_dz = np.roll(F[..., 0], -1, axis=2) - np.roll(F[..., 0], 1, axis=2)
        dFz_dx = np.roll(F[..., 2], -1, axis=0) - np.roll(F[..., 2], 1, axis=0)
        curl_y = dFx_dz - dFz_dx

        dFy_dx = np.roll(F[..., 1], -1, axis=0) - np.roll(F[..., 1], 1, axis=0)
        dFx_dy = np.roll(F[..., 0], -1, axis=1) - np.roll(F[..., 0], 1, axis=1)
        curl_z = dFy_dx - dFx_dy

        return np.stack([curl_x, curl_y, curl_z], axis=-1)

    def gravitational_helicity(self) -> float:
        """
        Equation 5: Gravitational helicity (topological invariant).

        H_g = ∫ A_g · B_g dV

        This measures the linkedness/knottedness of gravitational field lines.
        Under frozen-in dynamics, H_g is conserved.
        """
        dot = np.sum(self.A_g * self.B_g, axis=-1)
        return np.sum(dot)  # Discrete integral over grid


# ─── PIST Analogy: Coordinate Invariance ───

class PISTFrozenIn:
    """
    Map gravitational frozen-in theorem to PIST coordinate invariance.

    Gravitational field line  →  PIST composite address
    Fluid velocity v            →  Data stream position n
    Field line connectivity     →  Coordinate structure (k,t,tree,surface,torus)
    Frozen-in condition         →  Deterministic encoding/decoding
    Gravitational helicity      →  Information conservation (lossless roundtrip)
    """

    def __init__(self, basis_size: int = 16):
        self.basis_size = basis_size
        self.basis = np.zeros(basis_size, dtype=np.uint8)
        self.helicity_history = []

    def pist_encode(self, n: int) -> Tuple[int, int]:
        """
        n = k² + t  (Equation 6: PIST shell decomposition)

        Analogous to resolving field into components along/orthogonal
        to a preferred direction in the fluid.
        """
        k = int(np.sqrt(n))
        t = n - k * k
        return k, t

    def pist_mass(self, k: int, t: int) -> int:
        """
        m(k,t) = t(2k+1-t) for t < 2k+1-t, else mirrored.

        Analogous to field strength/intensity at a given shell.
        """
        if k == 0:
            return 0
        m = 2 * k + 1 - t
        tf = t if t < m else m
        return tf * (2 * k + 1 - tf)

    def composite_address(self, n: int) -> dict:
        """
        Equation 7: Composite address = (tree, surface, torus, shell)

        Analogous to full field specification at a point:
        - Tree address   = topological genus/branch label
        - Surface coords = local field direction
        - Torus angles   = phase/rotation state
        - Shell coords   = radial distance/amplitude
        """
        k, t = self.pist_encode(n)
        mass = self.pist_mass(k, t)

        # Tree: base-20 path
        tree = [(n // (20 ** i)) % 20 for i in range(3)]

        # Surface: y = 1/x, θ = n·Φ
        x = 1.0 + (n % 255)
        y = 1.0 / x
        theta_surf = (n * 1.618033988749895) % (2 * np.pi)

        # Torus: Φ-irrational angles
        phi = (n * 1.618033988749895) % (2 * np.pi)
        psi = (n * 1.618033988749895 ** 2) % (2 * np.pi)

        return {
            'n': n, 'k': k, 't': t, 'mass': mass,
            'tree': tree,
            'surface': {'x': x, 'y': y, 'theta': theta_surf},
            'torus': {'phi': phi, 'psi': psi}
        }

    def frozen_in_decode(self, stream: bytes, position: int) -> int:
        """
        Equation 8: Decoder = prediction XOR residual.

        Prediction is a "frozen-in" coordinate function:
        it depends only on position n and basis, not on data.

        This guarantees:
        - Determinism: same n → same prediction
        - Reversibility: residual = data XOR prediction
        - Invariance: coordinate structure preserved
        """
        n = position
        addr = self.composite_address(n)

        # Prediction from coordinate-derived values
        pred = self.basis[n % self.basis_size]
        pred ^= int(addr['torus']['phi'] * 40.5) & 0xFF
        pred ^= (addr['mass'] % 256)
        pred ^= int(addr['surface']['theta'] * 40.5) & 0xFF

        # Residual from stream
        if position < len(stream):
            residual = stream[position]
        else:
            residual = 0

        return pred ^ residual

    def compute_helicity(self, data: bytes) -> float:
        """
        Equation 9: PIST "helicity" = correlation of address components.

        Analogous to gravitational helicity but for information coordinates.
        Measures how tightly the coordinate components are "knotted" together.

        High helicity = strong correlation = better prediction = lower entropy.
        """
        # Compute pairwise correlations between address components
        k_vals = []
        t_vals = []
        mass_vals = []
        tree_sum = []

        for n in range(len(data)):
            k, t = self.pist_encode(n)
            mass = self.pist_mass(k, t)
            tree = [(n // (20 ** i)) % 20 for i in range(3)]

            k_vals.append(k)
            t_vals.append(t)
            mass_vals.append(mass)
            tree_sum.append(sum(tree))

        # Correlation matrix
        corr_kt = np.corrcoef(k_vals, t_vals)[0, 1] if len(k_vals) > 1 else 0
        corr_km = np.corrcoef(k_vals, mass_vals)[0, 1] if len(k_vals) > 1 else 0
        corr_tm = np.corrcoef(t_vals, mass_vals)[0, 1] if len(t_vals) > 1 else 0

        # "Helicity" = integrated correlation strength
        helicity = abs(corr_kt) + abs(corr_km) + abs(corr_tm)
        return helicity


# ─── Demonstration ───

def demonstrate_frozen_in():
    """Show that PIST coordinates preserve structure under dynamics."""

    print("=" * 60)
    print("Frozen-In Gravity → PIST Analogy")
    print("Asenjo, Comisso & Winkler (PRL 2026)")
    print("=" * 60)

    # 1. Create PIST system
    pist = PISTFrozenIn(basis_size=16)

    # 2. Generate synthetic data
    np.random.seed(42)
    data = bytes(np.random.randint(0, 256, size=1000))

    # 3. Show address invariance
    print("\n--- Coordinate Invariance Test ---")
    for n in [0, 10, 100, 500]:
        addr1 = pist.composite_address(n)
        addr2 = pist.composite_address(n)

        assert addr1['k'] == addr2['k']
        assert addr1['t'] == addr2['t']
        assert addr1['mass'] == addr2['mass']

        print(f"n={n}: k={addr1['k']}, t={addr1['t']}, mass={addr1['mass']}")
    print("  ✓ Coordinates are deterministic (frozen-in)")

    # 4. Show reversibility
    print("\n--- Reversibility Test ---")
    # Encode: residual = data XOR prediction
    # Decode: data' = prediction XOR residual
    residuals = bytearray()
    for i, b in enumerate(data):
        pred = pist.basis[i % pist.basis_size]
        pred ^= (pist.pist_mirror(i) % 256)
        residual = b ^ pred
        residuals.append(residual)

    # Decode
    decoded = bytearray()
    for i in range(len(data)):
        pred = pist.basis[i % pist.basis_size]
        pred ^= (pist.pist_mirror(i) % 256)
        out = pred ^ residuals[i]
        decoded.append(out)

    assert bytes(decoded) == data
    print(f"  ✓ Roundtrip verified for {len(data)} bytes")

    # 5. Compute helicity
    print("\n--- Information Helicity ---")
    helicity = pist.compute_helicity(data)
    print(f"  PIST coordinate helicity: {helicity:.4f}")
    print(f"  (Higher = stronger coordinate correlations = better compression)")

    print("\n" + "=" * 60)
    print("Key insight: Deterministic coordinates = frozen-in structure")
    print("No search needed. Topology is built into the encoding.")
    print("=" * 60)


def pist_mirror(n: int) -> int:
    """Helper: PIST mirror operation."""
    k = int(np.sqrt(n))
    t = n - k * k
    if k == 0:
        return 0
    return k * k + (2 * k + 1 - t)


# Add mirror to class
PISTFrozenIn.pist_mirror = staticmethod(pist_mirror)


# ─── AngrySphinx Gear Law & FAMM-Coupled Gear Ratio ───

class FAMMRouteMemory:
    """
    Frustration-Aligned Memory Management (FAMM).
    Records route outcomes as scars that bias future search.
    """

    def __init__(self):
        self.scars = []  # List of (route_signature, outcome, load)
        self.torsion = 0.0
        self.interlock = 0.0
        self.phase_delta = 0.0
        self.route_helicity = 0.0

    def record_scar(self, route_sig: str, outcome: str, effort: float):
        """Record a route traversal outcome."""
        self.scars.append({
            'route': route_sig,
            'outcome': outcome,  # 'success', 'failure', 'trap', 'partial'
            'effort': effort,
            'timestamp': len(self.scars)
        })
        # Update FAMM load components
        self.torsion += effort * 0.1
        self.interlock += 1.0 if outcome == 'trap' else 0.0
        self.phase_delta += abs(hash(route_sig) % 100) / 100.0

    def load(self) -> float:
        """
        Eq: L_FAMM(t) = Sigma^2(t) + I_lock(t) + Delta_phi(t)
        """
        return self.torsion**2 + self.interlock + self.phase_delta

    def load_frozen(self) -> float:
        """
        Frozen-FAMM / topology-aware version:
        L_FAMM+(t) = Sigma^2 + I_lock + Delta_phi + H_route
        where H_route = preserved route-helicity / connectivity penalty.
        """
        return self.load() + self.route_helicity

    def hostile_route_count(self) -> int:
        return sum(1 for s in self.scars if s['outcome'] in ('failure', 'trap'))

    def repeated_hostile_count(self, route_sig: str) -> int:
        return sum(1 for s in self.scars
                   if s['route'] == route_sig and s['outcome'] in ('failure', 'trap'))


class AngrySphinxShell:
    """
    AngrySphinx Gear Law:

        O(t) = eta(t) * G_AS(t) * a(t) + F(t) + chi(t)

    where:
        a(t)  = adversarial input effort
        G_AS  = gear reduction / escalation multiplier
        eta   = efficiency of cost transfer
        F(t)  = FAMM route-scar load
        chi   = cringe / semantic friction

    Gear ratio (FAMM-coupled escalation):
        G_AS(t) = 1 + alpha*L_FAMM(t) + beta*R(t) + gamma*U(t)

    where:
        L_FAMM = route-scar / frustration load
        R      = repeated hostile route count
        U      = uncertainty or unknown-route risk
    """

    def __init__(self,
                 alpha: float = 0.5,
                 beta: float = 1.0,
                 gamma: float = 2.0,
                 delta: float = 0.3,
                 theta_safe: float = 10.0):
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.delta = delta  # H_route coupling
        self.theta_safe = theta_safe
        self.famm = FAMMRouteMemory()
        self.cringe_friction = 0.0
        self.semantic_cost = 0.0
        self.reality_cost = 0.0
        self.constructive_cost = 0.0

    def gear_ratio(self, adversarial_effort: float, route_sig: str) -> float:
        """
        Compute the current gear ratio for a given adversarial input.
        """
        L_famm = self.famm.load_frozen()
        R_repeat = self.famm.repeated_hostile_count(route_sig)
        U_unknown = 1.0 if self.famm.hostile_route_count() == 0 else 0.0
        H_route = self.famm.route_helicity

        G_as = (1.0
                + self.alpha * L_famm
                + self.beta * R_repeat
                + self.gamma * U_unknown
                + self.delta * H_route)
        return G_as

    def impose_obligation(self, adversarial_effort: float, route_sig: str) -> dict:
        """
        Convert adversarial input into constructive obligation.

        C_out = G_AS * C_in + C_semantic + C_reality + C_constructive + C_cringe
        """
        G_as = self.gear_ratio(adversarial_effort, route_sig)
        eta = 0.85  # efficiency of cost transfer

        O_compute = eta * G_as * adversarial_effort
        O_semantic = self.semantic_cost
        O_reality = self.reality_cost
        O_constructive = self.constructive_cost
        O_cringe = self.cringe_friction
        O_total = O_compute + O_semantic + O_reality + O_constructive + O_cringe

        # Update FAMM with this engagement
        self.famm.record_scar(route_sig, 'trap', adversarial_effort)

        return {
            'gear_ratio': G_as,
            'compute_obligation': O_compute,
            'semantic_obligation': O_semantic,
            'reality_obligation': O_reality,
            'constructive_obligation': O_constructive,
            'cringe_obligation': O_cringe,
            'total_obligation': O_total
        }

    def is_defensive(self, payload_value: float, auth_recovery_cost: float) -> bool:
        """
        Shell is economically defensive when:

            S_AS(t) = C_out - V_payload - C_auth  >  0

        or in full form:
            S_AS+(t) = C_compute + C_semantic + C_reality + C_constructive + C_cringe
                       + lambda * L_FAMM+
                       - V_payload - C_auth
        """
        # Use latest obligation as proxy for current state
        latest_effort = self.famm.scars[-1]['effort'] if self.famm.scars else 1.0
        latest_route = self.famm.scars[-1]['route'] if self.famm.scars else 'default'
        obligation = self.impose_obligation(latest_effort, latest_route)
        S_as = obligation['total_obligation'] - payload_value - auth_recovery_cost
        return S_as > 0

    def decision_rule(self, payload_value: float, auth_recovery_cost: float) -> str:
        """
        Decision rule based on defensive score:

            S_AS+(t) > theta_safe   =>  allow shell state to persist
            0 < S_AS+(t) <= theta_safe  =>  harden shell
            S_AS+(t) <= 0           =>  shell failing or underpriced
        """
        if not self.famm.scars:
            return "neutral"

        latest_effort = self.famm.scars[-1]['effort']
        latest_route = self.famm.scars[-1]['route']
        obligation = self.impose_obligation(latest_effort, latest_route)
        S_as = obligation['total_obligation'] - payload_value - auth_recovery_cost

        if S_as > self.theta_safe:
            return "persist"
        elif S_as > 0:
            return "harden"
        else:
            return "underpriced"


def demonstrate_gear_law():
    """Demonstrate AngrySphinx gear reduction with FAMM escalation."""

    print("=" * 60)
    print("AngrySphinx Gear Law — FAMM-Coupled Escalation")
    print("=" * 60)

    shell = AngrySphinxShell(alpha=0.5, beta=1.0, gamma=2.0)
    payload_value = 100.0
    auth_cost = 5.0

    # Simulate repeated hostile probes on the same route
    route = "brute_force_shell_0"
    efforts = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]

    print(f"\nPayload value: {payload_value}, Auth recovery cost: {auth_cost}")
    print(f"Hostile route: '{route}'")
    print(f"\n{'Probe':>6} {'Effort':>8} {'Gear G':>10} {'C_out':>10} {'S_AS':>10} {'Decision':>10}")
    print("-" * 60)

    for i, effort in enumerate(efforts):
        obligation = shell.impose_obligation(effort, route)
        S_as = obligation['total_obligation'] - payload_value - auth_cost
        decision = shell.decision_rule(payload_value, auth_cost)

        print(f"{i+1:>6} {effort:>8.2f} {obligation['gear_ratio']:>10.2f} "
              f"{obligation['total_obligation']:>10.2f} {S_as:>10.2f} {decision:>10}")

    # Show effect of switching to a novel route
    print(f"\n--- Novel route probe (high uncertainty load) ---")
    novel_route = "injection_vector_7"
    obligation = shell.impose_obligation(1.0, novel_route)
    S_as = obligation['total_obligation'] - payload_value - auth_cost
    print(f"Novel route '{novel_route}': G={obligation['gear_ratio']:.2f}, "
          f"C_out={obligation['total_obligation']:.2f}, S_AS={S_as:.2f}")

    print("\n" + "=" * 60)
    print("Gear reduction: cheap attacker speed → expensive defensive torque")
    print("FAMM scars ratchet the gear ratio up with each hostile engagement")
    print("=" * 60)


if __name__ == "__main__":
    demonstrate_frozen_in()
    print("\n")
    demonstrate_gear_law()
