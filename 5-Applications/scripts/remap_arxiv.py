#!/usr/bin/env python3
"""
Re-map arXiv findings using precise category-based heuristics.
Reads arxiv_findings_500.md and rewrites it with corrected mappings.
"""

import re
import sys
from dataclasses import dataclass


@dataclass
class Entry:
    number: int
    title: str
    url: str
    year: str
    summary: str
    mapping: dict


def classify(title: str, summary: str) -> dict:
    """Precise classifier using regex patterns on title+summary."""
    text = (title + " " + summary).lower()

    # Physics — Quantum
    if any(p in text for p in [
        "wavefunction", "eigenstate", "hamiltonian", "schrodinger", "heisenberg",
        "superposition", "entanglement", "decoherence", "bell inequality", "quantum field",
        "qubit", "quantum information", "quantum computing", "quantum error",
        "density matrix", "hilbert space", "path integral", "renormalization"
    ]):
        return {
            "Ω": "measured eigenvalue / quantum state probability",
            "Ψ": "unitary evolution / measurement collapse operator",
            "B": "Hilbert space basis / quantum state vector",
            "C": "Hamiltonian / measurement apparatus / initial condition",
            "Δ": "decoherence / quantum uncertainty / vacuum fluctuations",
        }

    # Physics — GR / Cosmology
    if any(p in text for p in [
        "spacetime", "metric tensor", "einstein", "curvature", "ricci", "riemann",
        "gravitational wave", "ligo", "black hole", "event horizon", "singularity",
        "cosmological", "inflation", "big bang", "dark energy", "dark matter",
        "hubble", "friedmann", "penrose", "hawking"
    ]):
        return {
            "Ω": "gravitational signal / metric perturbation / cosmic expansion",
            "Ψ": "Einstein field equations / geometric operator",
            "B": "spacetime manifold / metric tensor",
            "C": "mass-energy distribution / observer frame / cosmological parameters",
            "Δ": "quantum foam / backreaction / measurement uncertainty",
        }

    # Physics — Particle / High Energy
    if any(p in text for p in [
        "standard model", "higgs", "gauge", "symmetry breaking", "supersymmetry",
        "qcd", "electroweak", "neutrino", "quark", "gluon", "lepton", "boson",
        "collider", "lhc", "cms", "atlas", "parton", "hadron", "jet"
    ]):
        return {
            "Ω": "cross-section / particle yield / decay rate",
            "Ψ": "S-matrix / Feynman diagram / gauge interaction",
            "B": "Standard Model Lagrangian / particle spectrum",
            "C": "collision energy / beam luminosity / detector acceptance",
            "Δ": "systematic error / pileup / theoretical uncertainty",
        }

    # Physics — Condensed Matter / Materials
    if any(p in text for p in [
        "graphene", "superconductor", "superconductivity", "topological insulator",
        "moiré", "twist angle", "van der waals", "phonon", "plasmon", "exciton",
        "band structure", "fermi surface", "landau level", "quantum hall",
        "dirac point", "weyl", " Majorana", "spin liquid", "charge density wave"
    ]):
        return {
            "Ω": "conductivity / critical temperature / band gap",
            "Ψ": "Bloch Hamiltonian / Bogoliubov operator / topological invariant",
            "B": "crystal lattice / atomic orbital basis",
            "C": "doping / strain / twist angle / magnetic field / temperature",
            "Δ": "disorder / defects / thermal fluctuations / phonon scattering",
        }

    # Physics — Thermodynamics / Stat Mech
    if any(p in text for p in [
        "entropy", "free energy", "partition function", "boltzmann", "gibbs",
        "thermodynamic", "statistical mechanics", "ising", "percolation",
        "phase transition", "critical exponent", "renormalization group",
        "non-equilibrium", "fluctuation theorem", "landauer"
    ]):
        return {
            "Ω": "entropy / free energy / heat capacity / probability distribution",
            "Ψ": "ensemble average / MaxEnt / renormalization group operator",
            "B": "microstate basis / configuration space",
            "C": "temperature / pressure / chemical potential / external field",
            "Δ": "thermal fluctuation / finite-size effect / sampling error",
        }

    # Physics — Optics / Photonics
    if any(p in text for p in [
        "laser", "photon", "optical", "cavity", "resonator", "interferometer",
        "squeezed state", "nonlinear optics", "frequency comb", "meta surface"
    ]):
        return {
            "Ω": "intensity / phase / optical signal",
            "Ψ": "Maxwell equations / quantum optical master equation",
            "B": "electromagnetic mode / photon number state",
            "C": "pump power / cavity geometry / detuning",
            "Δ": "shot noise / thermal noise / loss",
        }

    # Physics — Plasma / Fusion
    if any(p in text for p in [
        "plasma", "tokamak", "stellarator", "magnetic confinement", "fusion",
        "iter", "runaway electron", "alpha particle", "guiding center"
    ]):
        return {
            "Ω": "confinement time / plasma beta / fusion gain Q",
            "Ψ": "Vlasov-Maxwell / guiding center / MHD operator",
            "B": "magnetic coil geometry / flux surface",
            "C": "plasma pressure / current profile / heating power",
            "Δ": "instability / turbulence / field ripple / perturbation",
        }

    # Mathematics
    if any(p in text for p in [
        "theorem", "proof", "lemma", "conjecture", "category", "homotopy",
        "cohomology", "manifold", "bundle", "sheaf", "scheme", "variety",
        "group theory", "representation", "algebraic", "number theory",
        "differential geometry", "symplectic", "riemannian"
    ]):
        return {
            "Ω": "theorem / invariant / computed quantity",
            "Ψ": "proof / functor / operator / morphism",
            "B": "axiom / basis / generating set / fundamental group",
            "C": "parameter space / module / sheaf section",
            "Δ": "approximation / truncation / undecidability",
        }

    # Biology — Genetics / Genomics
    if any(p in text for p in [
        "genome", "gene", "dna", "rna", "transcriptome", "epigenetic",
        "mutation", "variant", "allele", "snp", "genotype", "phenotype",
        "crispr", "expression", "promoter", "enhancer", "methylation",
        "chromatin", "histone", "genome-wide", "gwas"
    ]):
        return {
            "Ω": "phenotype / trait / disease risk / expression level",
            "Ψ": "gene regulation / evolutionary selection / developmental program",
            "B": "DNA sequence / gene / regulatory element",
            "C": "environment / cell type / developmental stage / diet",
            "Δ": "mutation / epigenetic noise / genetic drift / measurement error",
        }

    # Biology — Evolution / Paleo
    if any(p in text for p in [
        "evolution", "natural selection", "phylogenetic", "ancestral",
        "speciation", "adaptation", "fossil", "paleontology", "extinction",
        "homologous", "convergent evolution", "molecular clock"
    ]):
        return {
            "Ω": "trait / fitness / divergence time / lineage",
            "Ψ": "selection / drift / migration operator",
            "B": "genome / morphological trait / protein sequence",
            "C": "environment / population size / geographic barrier",
            "Δ": "contamination / decay / sampling bias / neutral drift",
        }

    # Biology — Neuroscience
    if any(p in text for p in [
        "neuron", "synapse", "brain", "cortex", "hippocampus",
        "memory", "learning", "cognitive", "consciousness", "neural circuit",
        "fmri", "eeg", "connectome", "action potential", "neurotransmitter"
    ]):
        return {
            "Ω": "behavior / cognition / neural firing rate / BOLD signal",
            "Ψ": "network dynamics / synaptic plasticity / information integration",
            "B": "neural population / synaptic weight / receptor type",
            "C": "stimulus / task / attention / arousal state",
            "Δ": "neural noise / individual variation / artifact",
        }

    # Biology — Cell / Molecular
    if any(p in text for p in [
        "cell", "protein folding", "signaling pathway", "metabolism",
        "mitochondria", "ribosome", "autophagy", "apoptosis",
        "kinase", "phosphorylation", "transcription factor"
    ]):
        return {
            "Ω": "cellular response / growth rate / metabolite concentration",
            "Ψ": "signaling cascade / metabolic flux / gene regulatory network",
            "B": "protein / enzyme / metabolite / organelle",
            "C": "nutrient / hormone / stress / drug concentration",
            "Δ": "stochastic expression / cell-to-cell variability / measurement noise",
        }

    # CS / AI — Machine Learning
    if any(p in text for p in [
        "neural network", "deep learning", "transformer", "attention",
        "backpropagation", "gradient descent", "generalization",
        "overfitting", "regularization", "latent space", "embedding",
        "contrastive learning", "self-supervised", "fine-tuning",
        "generative model", "diffusion model", "gan", "vae"
    ]):
        return {
            "Ω": "model output / prediction / generated sample / loss",
            "Ψ": "optimization / backpropagation / inference / sampling operator",
            "B": "network weights / training data distribution / latent basis",
            "C": "input / prompt / hyperparameter / task specification",
            "Δ": "generalization gap / mode collapse / adversarial vulnerability / bias",
        }

    # CS / AI — Reinforcement Learning / Game Theory
    if any(p in text for p in [
        "reinforcement learning", "q-learning", "policy gradient",
        "multi-agent", "game theory", "nash equilibrium", "mechanism design",
        "bandit", "exploration", "exploitation", "reward shaping"
    ]):
        return {
            "Ω": "cumulative reward / policy / equilibrium strategy",
            "Ψ": "Bellman operator / policy gradient / best-response dynamics",
            "B": "state space / action space / reward function",
            "C": "environment dynamics / opponent strategy / discount factor",
            "Δ": "exploration noise / sample inefficiency / non-stationarity",
        }

    # CS — Algorithms / Theory
    if any(p in text for p in [
        "algorithm", "complexity", "np-complete", "approximation",
        "graph", "combinatorial", "optimization", "linear programming",
        "randomized", "deterministic", "online algorithm", "streaming"
    ]):
        return {
            "Ω": "solution quality / running time / approximation ratio",
            "Ψ": "algorithm / recursive procedure / iterative operator",
            "B": "input instance / graph / constraint set",
            "C": "parameter / resource bound / adversarial input",
            "Δ": "approximation error / slack / worst-case gap",
        }

    # CS — Information Theory / Compression
    if any(p in text for p in [
        "information theory", "entropy", "channel capacity", "coding",
        "compression", "kullback-leibler", "mutual information", "rate distortion"
    ]):
        return {
            "Ω": "compressed size / rate / distortion / channel capacity",
            "Ψ": "encoder / decoder / channel operator",
            "B": "source alphabet / codebook / basis distribution",
            "C": "source statistics / channel noise / rate constraint",
            "Δ": "redundancy / loss / decoding error / gap to Shannon limit",
        }

    # Chemistry
    if any(p in text for p in [
        "catalyst", "reaction mechanism", "molecular dynamics", "density functional",
        "electronic structure", "spectroscopy", "chromatography",
        "organic synthesis", "polymer", "nanoparticle", "surface chemistry"
    ]):
        return {
            "Ω": "yield / selectivity / spectrum / binding energy",
            "Ψ": "reaction pathway / Hamiltonian / kinetic operator",
            "B": "molecular orbital / active site / monomer",
            "C": "temperature / pressure / solvent / concentration",
            "Δ": "side reaction / impurity / thermal broadening",
        }

    # Climate / Ecology
    if any(p in text for p in [
        "climate", "carbon cycle", "ecosystem", "biodiversity", "species",
        "population dynamics", "predator-prey", "food web", "biogeochemical",
        "remote sensing", "land use", "deforestation"
    ]):
        return {
            "Ω": "CO₂ flux / species count / temperature anomaly / biomass",
            "Ψ": "ecosystem model / nutrient cycle / population dynamics operator",
            "B": "species pool / microbial community / carbon reservoir",
            "C": "temperature / precipitation / human activity / disturbance",
            "Δ": "stochastic variation / model bias / measurement uncertainty",
        }

    # Energy / Engineering
    if any(p in text for p in [
        "battery", "lithium", "electrolyte", "solar cell", "photovoltaic",
        "fuel cell", "supercapacitor", "energy storage", "power grid",
        "turbine", "heat exchanger", "combustion"
    ]):
        return {
            "Ω": "capacity / efficiency / power density / lifetime",
            "Ψ": "ion transport / charge transfer / thermodynamic cycle operator",
            "B": "electrode material / semiconductor / electrolyte",
            "C": "temperature / voltage / current / cycling rate",
            "Δ": "degradation / resistance / thermal loss / manufacturing defect",
        }

    # Default — catch-all
    return {
        "Ω": "observed phenomenon / measured quantity",
        "Ψ": "underlying theoretical mechanism / operator",
        "B": "conserved basis / fundamental reusable component",
        "C": "dynamic context / adaptive parameter / external condition",
        "Δ": "residual error / noise / uncertainty / irreducible limit",
    }


def parse_entries(text: str):
    """Parse markdown file into Entry objects."""
    entries = []
    pattern = re.compile(
        r"## (\d+)\. (.+?)\n\n"
        r"\*\*Source:\*\* \[([^\]]+)\]\([^)]+\)\s+\((\d{4})\)\n\n"
        r"\*\*Summary:\*\* (.+?)\n\n"
        r"\| Symbol \| Mapping \|\n\|--------\|---------\|\n"
        r"\| Ω \| (.+?) \|\n"
        r"\| Ψ \| (.+?) \|\n"
        r"\| B \| (.+?) \|\n"
        r"\| C \| (.+?) \|\n"
        r"\| Δ \| (.+?) \|\n",
        re.DOTALL
    )
    for m in pattern.finditer(text):
        entries.append(Entry(
            number=int(m.group(1)),
            title=m.group(2).strip(),
            url=m.group(3).strip(),
            year=m.group(4).strip(),
            summary=m.group(5).strip(),
            mapping={"Ω": m.group(6).strip(), "Ψ": m.group(7).strip(),
                     "B": m.group(8).strip(), "C": m.group(9).strip(), "Δ": m.group(10).strip()}
        ))
    return entries


def render_entry(e: Entry) -> str:
    m = e.mapping
    return (
        f"## {e.number}. {e.title}\n\n"
        f"**Source:** [{e.url}]({e.url})  ({e.year})\n\n"
        f"**Summary:** {e.summary[:500]}\n\n"
        f"| Symbol | Mapping |\n"
        f"|--------|---------|\n"
        f"| Ω | {m['Ω']} |\n"
        f"| Ψ | {m['Ψ']} |\n"
        f"| B | {m['B']} |\n"
        f"| C | {m['C']} |\n"
        f"| Δ | {m['Δ']} |\n\n"
        f"---\n\n"
    )


def main():
    input_path = "/home/allaun/Documents/Research Stack/3-Mathematical-Models/arxiv_findings_500.md"
    output_path = "/home/allaun/Documents/Research Stack/3-Mathematical-Models/arxiv_findings_500_remapped.md"

    with open(input_path, "r", encoding="utf-8") as f:
        text = f.read()

    entries = parse_entries(text)
    print(f"Parsed {len(entries)} entries")

    improved = 0
    for e in entries:
        old = e.mapping["B"]
        new_map = classify(e.title, e.summary)
        if new_map["B"] != old:
            improved += 1
        e.mapping = new_map

    print(f"Improved mappings: {improved}/{len(entries)}")

    lines = [
        "# ArXiv Findings — Re-Mapped to Unified Equation (LLM-Assisted Heuristic)",
        "",
        f"**Papers:** {len(entries)}",
        f"**Equation:** Ω = Ψ [ B(θ) ⊗ C(n, α) ] ⊕ Δ(n, θ, α)",
        "",
        "---",
        "",
    ]

    for e in entries:
        lines.append(render_entry(e))

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
