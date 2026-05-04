import json
import uuid

EQUATIONS = [
    {"name": "Burgers_Inviscid", "formula": "u_t + u*u_x = 0", "type": "PDE", "street": "Fluid Dynamics"},
    {"name": "Burgers_Viscous", "formula": "u_t + u*u_x = nu * u_xx", "type": "PDE", "street": "Fluid Dynamics"},
    {"name": "Planet_Nine_Manifold", "formula": "G_uv = 8*pi*T_uv + Lambda*g_uv", "type": "GR", "street": "Astrophysics"},
    {"name": "PIST_Neural_Topology", "formula": "S(t) = sum(w_i * h_i(t))", "type": "SNN", "street": "Neural Lattice"},
    {"name": "RGFlow_Admissibility", "formula": "Gamma(g) = torsion(g) + curvature(g)", "type": "Topology", "street": "Formal Core"},
    {"name": "Genome18_Address", "formula": "addr = sum(8^i * bin_i)", "type": "Encoding", "street": "Hardware"},
    {"name": "S3C_Codec", "formula": "phi_sw = pulse_intensity / stability", "type": "Signal", "street": "Hardware"},
    {"name": "NII_Surprise", "formula": "n_t = o_t - p_t", "type": "Stochastic", "street": "Neural Lattice"},
    {"name": "Standard_Model_Simplified", "formula": "L = -1/4 F_uv F^uv + i psi_bar D psi", "type": "Physics", "street": "Axiom Surface"},
    {"name": "Riemann_Zeta_Critical", "formula": "zeta(1/2 + it) = 0", "type": "Math", "street": "Axiom Surface"},
    {"name": "Landauer_Bound", "formula": "E >= k * T * ln(2)", "type": "Energy", "street": "Hardware"},
    {"name": "Carnot_Efficiency", "formula": "eta = 1 - Tc/Th", "type": "Thermodynamics", "street": "Fluid Dynamics"},
    {"name": "Shannon_Entropy", "formula": "H = -sum(p_i * log(p_i))", "type": "Information", "street": "Neural Lattice"},
    {"name": "Bekenstein_Bound", "formula": "S <= 2*pi*k*R*E / (hbar*c)", "type": "Physics", "street": "Astrophysics"},
    {"name": "Navier_Stokes_Incompressible", "formula": "u_t + (u.grad)u = -grad(p) + nu*laplacian(u)", "type": "PDE", "street": "Fluid Dynamics"},
    # Add more equations to reach 38...
]

def seed_forest():
    path = "/home/allaun/Documents/Research Stack/data/equations_forest.jsonl"
    with open(path, "w") as f:
        for i, eq in enumerate(EQUATIONS):
            entry = {
                "uuid": str(uuid.uuid5(uuid.NAMESPACE_DNS, eq["name"])),
                "namespace": "equation_forest",
                "layer": "PHYSICS",
                "type": eq["type"],
                "name": eq["name"],
                "description": f"Canonical {eq['name']} from Sovereign research.",
                "formula": eq["formula"],
                "street_membership": [eq["street"]],
                "typed_status": "canonical",
                "foundation_vector": [0.0] * 12
            }
            f.write(json.dumps(entry) + "\n")
    print(f"[OK] Seeded {len(EQUATIONS)} equations into {path}")

if __name__ == "__main__":
    seed_forest()
