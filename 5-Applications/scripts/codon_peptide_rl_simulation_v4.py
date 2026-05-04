from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

# =========================================================
# OTOM V4 Python Simulator (clean step-by-step version)
# Step layering:
# 0. Base codon->peptide score
# 1. Cotranslational visible prefix
# 2. Pause field + dwell time
# 3. Exposed tail window
# 4. Contact kinetics
# 5. Transient codon structural bias (optional ablation)
# =========================================================

# -----------------------------
# Shared toy biology definitions
# -----------------------------
CODON_TABLE = {
    "GCU": "A", "GCC": "A", "GCA": "A", "GCG": "A",
    "UUU": "F", "UUC": "F",
    "GGU": "G", "GGC": "G", "GGA": "G", "GGG": "G",
}

AA_TO_IDX = {"A": 0, "F": 1, "G": 2}

AA_TO_CODONS = {}
for c, aa in CODON_TABLE.items():
    AA_TO_CODONS.setdefault(aa, []).append(c)
for aa in AA_TO_CODONS:
    AA_TO_CODONS[aa] = sorted(AA_TO_CODONS[aa])

DEGENERACY = {c: sum(1 for x in CODON_TABLE.values() if x == aa) for c, aa in CODON_TABLE.items()}

TRIPLET_STABILITY = {
    "GCU": 0.90, "GCC": 0.95, "GCA": 0.82, "GCG": 0.88,
    "UUU": 0.76, "UUC": 0.81,
    "GGU": 0.72, "GGC": 0.86, "GGA": 0.67, "GGG": 0.61,
}

CONSERVATION = {
    "GCU": 0.72, "GCC": 0.80, "GCA": 0.58, "GCG": 0.64,
    "UUU": 0.75, "UUC": 0.83,
    "GGU": 0.60, "GGC": 0.79, "GGA": 0.55, "GGG": 0.48,
}

TRANSLATION_EFF = {
    "GCU": 0.78, "GCC": 0.90, "GCA": 0.64, "GCG": 0.70,
    "UUU": 0.73, "UUC": 0.85,
    "GGU": 0.66, "GGC": 0.88, "GGA": 0.52, "GGG": 0.45,
}

LOCAL_ENTROPY = {
    "GCU": 0.36, "GCC": 0.28, "GCA": 0.44, "GCG": 0.39,
    "UUU": 0.41, "UUC": 0.30,
    "GGU": 0.48, "GGC": 0.31, "GGA": 0.53, "GGG": 0.58,
}

MUTATION_PENALTY = {
    "GCU": 0.20, "GCC": 0.12, "GCA": 0.30, "GCG": 0.24,
    "UUU": 0.22, "UUC": 0.15,
    "GGU": 0.33, "GGC": 0.18, "GGA": 0.37, "GGG": 0.42,
}

TRANSLATION_SPEED = {
    "GCU": 0.82, "GCC": 1.05, "GCA": 0.68, "GCG": 0.76,
    "UUU": 0.72, "UUC": 0.95,
    "GGU": 0.66, "GGC": 0.98, "GGA": 0.58, "GGG": 0.50,
}

CODON_BIAS = {
    "GCU": np.array([ 0.03,  0.00, -0.01]),
    "GCC": np.array([ 0.07, -0.01, -0.02]),
    "GCA": np.array([-0.02,  0.01,  0.03]),
    "GCG": np.array([ 0.01,  0.00,  0.01]),
    "UUU": np.array([-0.01,  0.05, -0.01]),
    "UUC": np.array([ 0.00,  0.07, -0.02]),
    "GGU": np.array([-0.02, -0.01,  0.05]),
    "GGC": np.array([-0.01,  0.00,  0.06]),
    "GGA": np.array([-0.03, -0.01,  0.04]),
    "GGG": np.array([-0.03,  0.00,  0.03]),
}

# -----------------------------
# Model parameters
# -----------------------------
w_rho, w_q, w_tau, w_H, w_eps = 1.0, 0.8, 0.9, 0.7, 0.75
lambda_deg, C0_codon = 0.35, 1.5
speed_cost_mu = 0.45
dt = 0.04
noise_scale = 0.04
alpha_rl = 0.55
temperature = 1.0
C0_peptide = 8.0

# expert basins
mu_helix = np.array([-1.0, -0.7])
mu_sheet = np.array([-2.2,  2.2])
mu_loop  = np.array([ 0.8,  0.8])

# -----------------------------
# Helper functions
# -----------------------------
def softmax(z):
    z = np.asarray(z, dtype=float)
    z = z - np.max(z)
    e = np.exp(z)
    return e / e.sum()

def wrap_angle(x):
    return (x + np.pi) % (2 * np.pi) - np.pi

def angular_delta(a, b):
    return wrap_angle(a - b)

def expert_potential(theta, mu, alpha):
    d = angular_delta(theta, mu)
    return 0.5 * alpha * np.dot(d, d)

def expert_gradient(theta, mu, alpha):
    return alpha * angular_delta(theta, mu)

def torsion_energy(theta):
    return 0.16 * (2 - np.cos(theta[0]) - np.cos(theta[1]))

def conformational_entropy(theta):
    return np.log1p(1.8 + 0.9 * np.exp(-0.5 * np.dot(theta - mu_loop, theta - mu_loop)))

def peptide_expert_energies(theta):
    return np.array([
        expert_potential(theta, mu_helix, 1.35),
        expert_potential(theta, mu_sheet, 1.20),
        expert_potential(theta, mu_loop,  0.75),
    ])

def peptide_expert_gradients(theta):
    return np.vstack([
        expert_gradient(theta, mu_helix, 1.35),
        expert_gradient(theta, mu_sheet, 1.20),
        expert_gradient(theta, mu_loop,  0.75),
    ])

def structural_coherence(theta):
    d_helix = np.linalg.norm(angular_delta(theta, mu_helix))
    d_sheet = np.linalg.norm(angular_delta(theta, mu_sheet))
    return 1.0 / (1.0 + min(d_helix, d_sheet))

def phi_codon(codon: str) -> float:
    num = (
        w_rho * TRIPLET_STABILITY[codon] +
        w_q * CONSERVATION[codon] +
        w_tau * TRANSLATION_EFF[codon] -
        w_H * LOCAL_ENTROPY[codon] -
        w_eps * MUTATION_PENALTY[codon]
    )
    denom = (
        np.log(64.0) +
        lambda_deg * np.log(float(DEGENERACY[codon])) +
        speed_cost_mu / TRANSLATION_SPEED[codon] +
        C0_codon
    )
    return num / denom

def visible_prefix(codons, translated_count):
    return codons[:translated_count]

def exposed_tail(codons, translated_count, Lexp=2):
    vp = visible_prefix(codons, translated_count)
    return vp[-Lexp:]

def pause_intensity(codon):
    rarity = 1.0 - TRANSLATION_EFF[codon]
    return 0.5 / TRANSLATION_SPEED[codon] + 0.25 * rarity

def transient_bias(recent_codons, age_weights, use_bias):
    if not use_bias or len(recent_codons) == 0:
        return np.zeros(3)
    accum = np.zeros(3)
    for c, w in zip(recent_codons, age_weights):
        accum += w * CODON_BIAS[c]
    return accum

def contact_prob(theta, exposed_codons, pause):
    if len(exposed_codons) < 2:
        return 0.0
    # toy contact proxy: more probable near structured basins and during pause
    d1 = np.linalg.norm(angular_delta(theta, mu_helix))
    d2 = np.linalg.norm(angular_delta(theta, mu_sheet))
    geom = np.exp(-(min(d1, d2) ** 2) / 1.2)
    access = (1 - np.exp(-0.8 * pause))
    return float(geom * access)

def phi_peptide_v4(theta, codons, translated_count, use_bias=False, Lexp=2):
    vp = visible_prefix(codons, translated_count)
    et = exposed_tail(codons, translated_count, Lexp=Lexp)
    aas = [CODON_TABLE[c] for c in vp]  # visible prefix

    # weighted by recency
    weights = np.linspace(0.35, 1.0, len(aas))
    weights = weights / weights.sum()
    target = np.zeros(3)
    for aa, w in zip(aas, weights):
        target[AA_TO_IDX[aa]] += w

    # active codon
    active = vp[-1]
    pause = pause_intensity(active)

    # delay bias from pausing
    delay_bias = np.array([-0.35 * pause, -0.18 * pause, 0.52 * pause])

    # transient codon bias only on exposed recent tail
    ages = np.linspace(1.0, 0.45, len(et)) if len(et) > 0 else np.array([])
    codon_bias = transient_bias(et, ages, use_bias=use_bias)

    E_ex = peptide_expert_energies(theta)
    gates = softmax(target + delay_bias + codon_bias - 0.5 * E_ex)
    contact = contact_prob(theta, et, pause)

    free_energy = (
        np.dot(gates, E_ex) +
        torsion_energy(theta) -
        0.8 * contact +
        temperature * conformational_entropy(theta)
    )

    coh = (
        0.6 * structural_coherence(theta) +
        0.25 * (1.0 - (-np.sum(gates*np.log(gates+1e-12))/np.log(3))) +
        0.15 * contact
    )

    return coh / (free_energy + C0_peptide), gates, pause, delay_bias, codon_bias, contact, free_energy

def phi_cds_v4(theta, codons, translated_count, use_bias=False, Lexp=2):
    vp = visible_prefix(codons, translated_count)
    codon_avg = np.mean([phi_codon(c) for c in vp]) if len(vp) else 0.0
    pep, gates, pause, delay_bias, codon_bias, contact, free_energy = phi_peptide_v4(
        theta, codons, translated_count, use_bias=use_bias, Lexp=Lexp
    )
    score = 0.50 * codon_avg + 0.40 * pep + 0.10 * contact
    return score, gates, pause, delay_bias, codon_bias, contact, free_energy

# -----------------------------
# Stage runner
# -----------------------------
def run_v4(use_bias=False, seed=7, T=360, Lexp=2):
    rng = np.random.default_rng(seed)
    aa_sequence = ["A", "F", "G"]
    codons = ["GCA", "UUU", "GGG"]  # initial
    logits = {i: np.zeros(len(AA_TO_CODONS[aa_sequence[i]])) for i in range(3)}
    theta = np.array([2.25, -2.05], dtype=float)

    history = {
        "phi": [],
        "theta": [],
        "translated": [],
        "pause": [],
        "contact": [],
        "free_energy": [],
        "delay_bias": [],
        "codon_bias": [],
        "visible": [],
        "policy": {0: [], 1: [], 2: []},
        "gates": [],
    }

    translated_count = 1
    phi_prev, *_ = phi_cds_v4(theta, codons, translated_count, use_bias=use_bias, Lexp=Lexp)

    cycles_per_codon = T // 3
    for t in range(T):
        translated_count = min(3, 1 + t // cycles_per_codon)
        active_pos = translated_count - 1
        aa = aa_sequence[active_pos]
        choices = AA_TO_CODONS[aa]
        probs = softmax(logits[active_pos])
        chosen_idx = rng.choice(len(choices), p=probs)
        codons[active_pos] = choices[chosen_idx]

        score, gates, pause, delay_bias, codon_bias, contact, free_energy = phi_cds_v4(
            theta, codons, translated_count, use_bias=use_bias, Lexp=Lexp
        )

        grads = peptide_expert_gradients(theta)
        drift = np.einsum("k,kj->j", gates, grads)

        # active codon controls effective dwell time
        dt_eff = dt / TRANSLATION_SPEED[codons[active_pos]]
        theta = wrap_angle(
            theta - dt_eff * drift + np.sqrt(dt_eff) * noise_scale * rng.normal(size=2)
        )

        phi_new, *_ = phi_cds_v4(theta, codons, translated_count, use_bias=use_bias, Lexp=Lexp)
        reward = phi_new - phi_prev

        # synonymous RL update at active position
        usefulness = np.array([phi_codon(c) - np.mean([phi_codon(x) for x in choices]) for c in choices])
        logits[active_pos] = logits[active_pos] + alpha_rl * reward * usefulness

        history["phi"].append(phi_new)
        history["theta"].append(theta.copy())
        history["translated"].append(translated_count)
        history["pause"].append(pause)
        history["contact"].append(contact)
        history["free_energy"].append(free_energy)
        history["delay_bias"].append(delay_bias.copy())
        history["codon_bias"].append(codon_bias.copy())
        history["visible"].append(tuple(visible_prefix(codons, translated_count)))
        history["gates"].append(gates.copy())
        for i in range(3):
            history["policy"][i].append(softmax(logits[i]))

        phi_prev = phi_new

    for k, v in history.items():
        if k in ("policy", "visible"):
            continue
        history[k] = np.array(v)

    history["final_codons"] = tuple(codons)
    history["final_phi"] = float(history["phi"][-1])
    history["best_phi"] = float(np.max(history["phi"]))

    return history

def main():
    base = run_v4(use_bias=False, seed=7)
    abl = run_v4(use_bias=True, seed=7)

    out_dir = Path(".")

    fig1, axes = plt.subplots(3, 1, figsize=(10, 10), sharex=True)
    axes[0].plot(base["phi"], label="Base v4")
    axes[0].plot(abl["phi"], label="Bias ablation v4")
    axes[0].set_ylabel("Phi_CDS")
    axes[0].set_title("V4 cotranslational score")
    axes[0].legend()

    axes[1].plot(base["translated"], label="Translated count")
    axes[1].set_ylabel("Visible codons")
    axes[1].legend()

    axes[2].plot(base["contact"], label="Base contact")
    axes[2].plot(abl["contact"], label="Bias contact")
    axes[2].set_ylabel("Contact")
    axes[2].set_xlabel("Step")
    axes[2].legend()

    fig1.tight_layout()

    fig2, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    axes[0].plot(base["pause"], label="Pause intensity")
    axes[0].plot(base["free_energy"], label="Free energy")
    axes[0].set_title("Pause and free energy")
    axes[0].legend()

    axes[1].plot(base["delay_bias"][:,0], label="helix delay bias")
    axes[1].plot(base["delay_bias"][:,1], label="sheet delay bias")
    axes[1].plot(base["delay_bias"][:,2], label="loop delay bias")
    axes[1].plot(abl["codon_bias"][:,0], "--", label="helix codon bias")
    axes[1].plot(abl["codon_bias"][:,1], "--", label="sheet codon bias")
    axes[1].plot(abl["codon_bias"][:,2], "--", label="loop codon bias")
    axes[1].set_title("Delay bias vs transient codon bias")
    axes[1].set_xlabel("Step")
    axes[1].legend(ncol=2)

    fig2.tight_layout()

    fig3 = plt.figure(figsize=(8, 6))
    ax = fig3.add_subplot(1, 1, 1)
    ax.plot(base["theta"][:,0], base["theta"][:,1], label="Base")
    ax.plot(abl["theta"][:,0], abl["theta"][:,1], label="Bias ablation")
    ax.scatter([mu_helix[0], mu_sheet[0], mu_loop[0]],
               [mu_helix[1], mu_sheet[1], mu_loop[1]], marker="x", s=100)
    ax.set_title(r"V4 trajectory in $(\phi,\psi)$ space")
    ax.set_xlabel(r"$\phi$")
    ax.set_ylabel(r"$\psi$")
    ax.legend()
    fig3.tight_layout()

    fig1.savefig(out_dir / "codon_peptide_v4_score.png", dpi=180, bbox_inches="tight")
    fig2.savefig(out_dir / "codon_peptide_v4_bias_and_pause.png", dpi=180, bbox_inches="tight")
    fig3.savefig(out_dir / "codon_peptide_v4_trajectory.png", dpi=180, bbox_inches="tight")
    plt.close(fig1); plt.close(fig2); plt.close(fig3)

    summary = f"""V4 cotranslational codon->peptide summary
Base model final codons: {base['final_codons']}
Base final Phi_CDS: {base['final_phi']:.6f}
Base best Phi_CDS: {base['best_phi']:.6f}

Bias ablation final codons: {abl['final_codons']}
Bias final Phi_CDS: {abl['final_phi']:.6f}
Bias best Phi_CDS: {abl['best_phi']:.6f}

Delta final score (bias - base): {abl['final_phi'] - base['final_phi']:.6f}
Delta best score (bias - base): {abl['best_phi'] - base['best_phi']:.6f}
"""
    (out_dir / "codon_peptide_v4_summary.txt").write_text(summary)
    print(summary)

if __name__ == "__main__":
    main()
