#!/usr/bin/env python3
"""
Radical adaptations finder — the most extreme biological solutions to physical problems.
Covers convergent evolution, novel biochemistry, and extinct engineering.
Adds to the 'Extremophile Bounds' domain and creates a new 'Radical Adaptations' domain.
"""

import sqlite3
import urllib.request
import urllib.parse
import json
import time
import os

DB = "/home/allaun/physics_equations.db"

conn = sqlite3.connect(DB)
cur = conn.cursor()

# --- Create new domain ---
cur.execute("SELECT MAX(id) FROM domains")
new_did = cur.fetchone()[0] + 1
cur.execute("INSERT INTO domains VALUES (?, 'Radical Adaptations', 'The most extreme biological innovations — convergent engineering across phyla, novel biochemistry, physical hacks that seem to violate constraints', NULL)", (new_did,))

# --- Equation injector ---
cur.execute("SELECT MAX(id) FROM equations"); eid = cur.fetchone()[0]
cur.execute("SELECT MAX(eq_number) FROM equations"); enum = cur.fetchone()[0]
def add_eq(title, sig, prec, year="various"):
    global eid, enum; eid += 1; enum += 1
    cur.execute("INSERT INTO equations VALUES (?,?,?,?,?,?,?,?)",
        (eid, enum, title, new_did, year, "Proven", sig, prec))
    return eid

# ================================================================
# LIVING SPECIES — RADICAL ADAPTATIONS
# ================================================================

eq_ids = {}

eq_ids['crypto'] = add_eq(
    "Cryptobiosis (Complete Metabolic Suspension) — Tardigrades, Rotifers, Brine Shrimp, Nematodes",
    "Organisms that can lose 95-99% of body water, shut down all detectable metabolism for decades, and revive within hours of rehydration. Tardigrades survive -272°C (liquid helium), 150°C, 6000 atm pressure, hard vacuum + cosmic rays (10 days in LEO). The mechanism: replace intracellular water with trehalose glass (vitrification) that preserves macromolecular structure. The universe's ultimate backup system — if you can pause entropy, you can wait out anything.",
    "Trehalose vitrification: replaces water's hydrogen bonds. Glass transition temp Tg of trehalose-water ~ −30°C, preserving protein/DNA conformation")
eq_ids['tardigrade'] = eq_ids['crypto']

eq_ids['cryo'] = add_eq(
    "Freeze Tolerance (Solid Ice Survival) — Wood Frogs, Arctic Beetles, Springtails, Antarctic Midge",
    "Rana sylvatica (wood frog) freezes solid each winter: 65% of body water turns to ice. Heart stops. Breathing stops. Brain activity zero. Glucose acts as cryoprotectant — blood sugar rises 100x (from 5 mM to 500 mM), preventing ice crystal formation inside cells while permitting it in extracellular spaces. Spring thaw: heart restarts before the brain, frog hops away within hours. Antarctic midge Belgica antarctica survives −20°C with 70% body water frozen — and can survive losing 40% of total body water.",
    "Ice-nucleating proteins in extracellular fluid; glycerol + glucose as intracellular cryoprotectants. Freeze concentration of solutes must not exceed osmotic tolerance.")
eq_ids['woodfrog'] = eq_ids['cryo']

eq_ids['immortal'] = add_eq(
    "Biological Immortality via Cellular Transdifferentiation — Turritopsis dohrnii (Immortal Jellyfish), Hydra",
    "Turritopsis dohrnii reverts from adult medusa stage back to polyp when stressed, effectively restarting its life cycle — indefinitely. This is not just regeneration; it's complete cellular reprogramming of differentiated cells back to stem cells, then redifferentiation into a different body plan. Hydra never senesces — its stem cells continuously replace all body cells with zero age-related decline. These organisms have decoupled aging from chronological time.",
    "Transdifferentiation: differentiated somatic cells revert to pluripotent state. Hydra: FoxO gene regulates continuous stem cell proliferation without tumor formation.")
eq_ids['jellyfish'] = eq_ids['immortal']

eq_ids['quantum_bio'] = add_eq(
    "Quantum Biology — Magnetoreception via Radical Pair Mechanism (Birds), Photosynthetic Coherence (Plants/Bacteria), Olfaction via Vibrational Tunneling",
    "European robins and other migratory birds can detect Earth's magnetic field (~50 μT) with their eyes. The leading mechanism involves cryptochrome proteins where photon absorption creates a radical pair whose spin dynamics are influenced by the magnetic field — a room-temperature quantum sensor in a biological system. Photosynthetic reaction centers achieve >95% quantum efficiency via coherent energy transfer through chromophore networks. Proposed: olfactory receptors may detect molecular vibrational frequencies via inelastic electron tunneling.",
    "Radical pair: electron spin correlation sensitive to ~50 μT. Coherence time in FMO complex ~300 fs at 77K, ~100 fs at RT. Controversial but accumulating evidence.")
eq_ids['bird_mag'] = eq_ids['quantum_bio']

eq_ids['photon'] = add_eq(
    "Single-Photon Detection in Biological Photoreceptors — Human Rod Cells, Amphibian Green Rods",
    "Human rod photoreceptor cells can detect individual photons. A rod cell responds to a single photon with a ~1 pA current change. Behavioral experiments: humans can reliably report a flash of ~5-7 photons delivered to the retina (only ~10% reach rods due to optical losses in the eye), meaning the perceptual threshold is ~1 photon per rod. This is a room-temperature single-photon detector made of rhodopsin protein — the quantum noise floor of vision.",
    "Rhodopsin quantum efficiency ~0.67. Thermal isomerization rate ~10⁻¹¹/s at 37°C (one spontaneous event per 160 years per molecule) — the ultimate dark noise floor.")
eq_ids['human_eye'] = eq_ids['photon']

eq_ids['electric'] = add_eq(
    "Bioelectrogenesis — Electric Eels (860 V), Torpedo Rays (220 V), Elephantnose Fish (active electrolocation)",
    "Electrophorus electricus generates 860 volts / 1 ampere pulses — enough to kill a horse — using specialized electrocytes derived from muscle cells, stacked in series (5,000-6,000 cells). The discharge is DC, not AC. Torpedo rays produce 220 V using a different evolutionary invention (modified gill arch musculature). Elephantnose fish (Gnathonemus) use weak electric fields (<1 V) for active electrolocation in murky waters — imaging their world through distortions in their self-generated field.",
    "Electrocyte: modified muscle cell, 0.15 V each, stacked in series.  Sodium channels clustered on posterior face, acetylcholine-activated. Discharge: all-or-nothing, ~500 Hz maximum rate.")
eq_ids['eel'] = eq_ids['electric']

eq_ids['cavitation'] = add_eq(
    "Biological Cavitation / Sonoluminescence — Pistol Shrimp, Mantis Shrimp",
    "Alpheidae (pistol/snapping shrimp) close their specialized claw at 100 km/h, creating a cavitation bubble that collapses with a 218 dB sound (loudest marine animal), a flash of light (sonoluminescence reaching ~4,700°C momentarily), and a shockwave that stuns prey. The flash is 10,000x too brief for human vision. This is a macroscopic quantum-ish phenomenon — cavitation collapse — generated by a living organism.",
    "Cavitation bubble collapse temperature ~4700 K (sun's surface). Pressure at collapse ~80 MPa. Sonoluminescence flash duration ~10⁻¹⁰ s. Claw closure time ~300 μs, acceleration ~100,000 m/s².")
eq_ids['shrimp'] = eq_ids['cavitation']

eq_ids['camouflage'] = add_eq(
    "Distributed Neural Camouflage — Cephalopod Chromatophore/Iridophore/Leucophore System, Cutaneous Light Sensing",
    "Octopus, cuttlefish, and squid can match color, pattern, texture, and brightness of any substrate — in 200-700 ms — without centralized processing. Their skin contains chromatophores (pigment sacs controlled by radial muscles), iridophores (Bragg-stack reflectors that produce structural color), and leucophores (diffuse white scatterers). Critically: cephalopod skin expresses opsin photoproteins identical to those in their eyes — their skin sees the environment directly, enabling distributed control without routing through the brain.",
    "Chromatophore expansion: radial muscle contraction in ~100 ms, controlled by motor neurons from chromatophore lobes. Iridophore: protein plates with tunable spacing (reflectin proteins) — active structural color. Papillae: hydrostatic muscles for 3D texture. Skin opsins: rhodopsin/r-opsin in chromatophore organs.")
eq_ids['octopus'] = eq_ids['camouflage']

eq_ids['endosymbiosis'] = add_eq(
    "Primary Endosymbiosis — Mitochondrial and Plastid Acquisition, the Singular Evolutionary Event",
    "The two most important events in the history of complex life: (1) an archaeon engulfed an α-proteobacterium ~1.5-2 billion years ago, creating the mitochondrion — the energy factory that enabled eukaryotic complexity; (2) a eukaryote engulfed a cyanobacterium ~1-1.5 billion years ago, creating the plastid — enabling photosynthesis in plants and algae. Both events happened exactly once each (with rare secondary/tertiary endosymbioses in some lineages). These aren't adaptations — they're the foundational architectural decisions of complex life. The mitochondrial inner membrane surface area per cell is ~14,000 m² in humans. Mitochondria still have their own DNA (37 genes in humans, 16,569 bp).",
    "Mitochondrial genome: 16.6 kb circular DNA, 37 genes (13 proteins, 22 tRNAs, 2 rRNAs). Plastid genome: 120-200 kb, ~100 genes. ~99% of original bacterial genes transferred to nucleus. Electron transport chain: Complex I-V, 93 protein subunits (13 mtDNA-coded). Proton gradient: ~180 mV across inner membrane.")
eq_ids['mito'] = eq_ids['endosymbiosis']

eq_ids['silk'] = add_eq(
    "Spider Silk — Tensile Strength Exceeding Steel, Toughness Exceeding Kevlar, Molecular Engineering",
    "Dragline silk from Nephila clavipes (golden orb-weaver): tensile strength ~1.1 GPa (vs steel ~0.4-1.5 GPa), but toughness (energy to break) ~160 MJ/m³ — 3x tougher than Kevlar and 5x tougher than steel by weight. The secret: a nanocomposite of crystalline β-sheet nanocrystals (~2-5 nm) embedded in an amorphous semi-liquid matrix, with sacrificial hydrogen bonds that break and reform under stress. Spiders extrude this from aqueous solution at room temperature and ambient pressure — no toxic solvents, no high heat. Plus: Darwin's bark spider (Caerostris darwini) produces silk spanning 25m rivers. Some spiders use silk for ballooning — electrostatic repulsion + wind lift carrying them to 5 km altitude and across oceans.",
    "β-sheet nanocrystals: poly(Ala) and poly(Gly-Ala) blocks; size ~2-5 nm; act as crosslinkers. Hydrogen bond clusters yield before breaking — sacrificial bond mechanism. Shear-thinning during spinning aligns polymer chains. dope → fiber transition: pH drop from 7.5 to 5.5 + ion exchange (Na⁺→K⁺) in spinning duct.")
eq_ids['spider'] = eq_ids['silk']

eq_ids['kleptoplasty'] = add_eq(
    "Kleptoplasty (Organelle Theft) — Elysia chlorotica (Photosynthetic Sea Slug), Hatena, Paulinella",
    "Elysia chlorotica eats the alga Vaucheria litorea, digests everything except the chloroplasts, and keeps them functional inside its own gut cells for 9-12 months — photosynthesizing and living off sugar for most of its adult life. The slug's genome contains algal nuclear genes (including photosystem proteins) acquired via horizontal gene transfer. Even wilder: Paulinella chromatophora independently 'domesticated' a cyanobacterium as a permanent endosymbiont — a primary plastid acquisition in progress, separate from the plant lineage. Hatena arenicola: steals a Nephroselmis chloroplast and permanently transforms its body plan to accommodate it.",
    "Slug acquires algal psbO (photosystem II stability protein) and fcp (light-harvesting complex) genes. Horizontal gene transfer from alga → slug nucleus confirmed. Paulinella chromatophore genome: ~1 Mb, ~870 genes — still larger than plant plastid genomes. Chromatophore division synchronized with host.")
eq_ids['slug'] = eq_ids['kleptoplasty']

eq_ids['echolocation'] = add_eq(
    "Biological Sonar — Echolocation Convergent Evolution in Bats and Toothed Whales (with Molecular Convergence)",
    "Echolocation evolved independently in bats and toothed whales (dolphins/porpoises/sperm whales), involving ~200 convergent amino acid substitutions — particularly in the prestin gene (outer hair cell motor protein in the cochlea). Bats emit 100+ dB ultrasonic pulses at 20-200 kHz and detect echoes from objects as fine as 0.05 mm. Dolphins can detect a 2.5 cm sphere at 100m distance. The physics: the matched-filter problem — correlating transmitted signal with returning echo — is solved by auditory cortex neurons tuned to specific frequency-modulated sweeps.",
    "Prestin gene: SLC26A5, 14 convergent amino acid substitutions between bat and dolphin lineages. Bat call frequencies: 20-200 kHz (most 20-80 kHz). Resolution: ~0.05 mm (moth scales). Dolphin: peak frequency 40-130 kHz, click duration 50-100 μs.  Cuvier's beaked whale dive: 137 min breathing-hold — echolocating at 3 km depth.")
eq_ids['bat'] = eq_ids['echolocation']

eq_ids['chem_defense'] = add_eq(
    "Explosive Biochemistry — Bombardier Beetle, Skunk Spray, Venom Systems (Cone Snail, Box Jellyfish, Blue-Ringed Octopus)",
    "Bombardier beetle (Brachinus) stores hydroquinone and hydrogen peroxide in separate abdominal chambers. When threatened, it mixes them in a reaction chamber containing catalase and peroxidase enzymes — the mixture reaches 100°C and explodes from a rotatable nozzle at the attacker. The beetle pulses the spray 500+ times/second to avoid cooking itself. Cone snails (Conus) produce 100-200 distinct peptide toxins per species, each targeting a specific ion channel subtype — the most sophisticated pharmacological arsenal in nature. Box jellyfish venom causes cardiovascular collapse in 2-5 minutes — the fastest-acting venom known. Blue-ringed octopus: tetrodotoxin (same as pufferfish, but produced by symbiotic bacteria).",
    "Bombardier beetle reaction: C₆H₄(OH)₂ + H₂O₂ → C₆H₄O₂ + 2H₂O (catalyzed), exothermic to ~100°C. Pressure in reaction chamber: pulsed release at 500 Hz to prevent thermal runaway. Tetrodotoxin: blocks voltage-gated Na⁺ channels, K_d ~1-10 nM. LD₅₀ ~10 μg/kg (human) — one octopus carries enough for 26 adults.")
eq_ids['beetle'] = eq_ids['chem_defense']

eq_ids['regeneration'] = add_eq(
    "Full Organ/Body-Plan Regeneration — Axolotl, Planaria, Zebrafish, Spiny Mouse (with Dedifferentiation vs Stem Cell Pools)",
    "Axolotl (Ambystoma mexicanum) regenerates entire limbs (bone, muscle, nerves, skin), spinal cord, heart ventricle, jaw, tail, and portions of brain — without scarring. The mechanism: differentiated cells at the wound site dedifferentiate into a blastema (pluripotent-like mass), which re-executes the developmental program. Planaria (flatworms) can regenerate from a fragment containing just 1/279th of the original body — the entire body plan is reconstructed, including brain and eyes, from a tiny piece, thanks to abundant pluripotent neoblasts (30% of all cells). Acoels (basal bilaterians) have the same neoblast system, suggesting whole-body regeneration is ancestral.",
    "Blastema formation: dedifferentiation signals (Wnt, FGF, BMP, Shh). Macrophage-dependent: without macrophages, scar forms. Planarian neoblasts: Piwi+ / bruno-like+ / EGFR signaling. Positional control genes (Wnt/β-catenin gradient for anterior-posterior axis).")
eq_ids['axolotl'] = eq_ids['regeneration']

eq_ids['social_farm'] = add_eq(
    "Agriculture by Non-Humans (Convergent Evolution ×3) — Leaf-Cutter Ants, Termites, Ambrosia Beetles (all farming fungus for 25-60 MYA)",
    "Leaf-cutter ants (Atta, Acromyrmex) don't eat the leaves they cut; they use them as substrate for a domesticated fungus (Leucoagaricus gongylophorus) that produces swollen hyphal tips (gongylidia) rich in lipids and carbohydrates. The ant-fungus mutualism is 50-60 million years old. The ants carry antibiotic-producing bacteria (Pseudonocardia) on their cuticle to suppress parasitic Escovopsis mold. Termites farm Termitomyces fungus in climate-controlled mounds with passive ventilation — fungal gardens maintained at exactly 30°C regardless of external temperature. Ambrosia beetles bore galleries in trees and inoculate them with spores of their specific fungus carried in mycangia (specialized body pockets). Each lineage has co-evolved with its specific fungus for 25-60 million years — the mutualism is obligate for both partners.",
    "Atta colony: 5-8 million workers, fungus garden ~2-3 m³. Pseudonocardia on ant cuticle: produces dentigerumycin, candicidin. Termite mound: solar-powered convection ventilation; core T=30±0.5°C. Termitomyces: 30+ described species, each specific to termite genus. Ambrosia beetle: evolved at least 12 independent times across Scolytinae + Platypodinae.")
eq_ids['ant_farm'] = eq_ids['social_farm']

eq_ids['mole_rat'] = add_eq(
    "Cancer Resistance + Extended Longevity — Naked Mole Rat (Heterocephalus glaber), Blind Mole Rat (Spalax), Brandt's Bat",
    "Naked mole rats: maximum lifespan >37 years (vs ~4 years for similar-size mice — 10×), and have NEVER been observed to develop spontaneous cancer in thousands of necropsies. The mechanism: their fibroblasts secrete extremely high-molecular-weight hyaluronan (~6-12 MDa vs ~0.5-2 MDa in humans) that fills extracellular space and prevents cell-to-cell contact needed for tumor formation. Additionally, they have hyper-sensitive contact inhibition (early-stage growth arrest at much lower cell density than other mammals). Blind mole rats use a different mechanism: concerted necrotic cell death via interferon-β release at hyperplasia onset. Brandt's bat (Myotis brandtii): ~41 year lifespan for a 7g animal — weight-specific longevity record for mammals.",
    "HAS2 gene: duplicated in naked mole rat, producing HMM-HA (6-12 MDa). Contact inhibition triggered at ~50% confluence (vs ~90% in mouse). p16^{INK4a} and p27^{Kip1}: early induction. INK4 locus: additional p15^{INK4b}-p16^{INK4a} fusion gene. Blind mole rat: IFN-β → p53/pRb activation → concerted necrosis.")
eq_ids['molerat'] = eq_ids['mole_rat']

eq_ids['biolum'] = add_eq(
    "Bioluminescence — 40+ Independent Evolutionary Origins, Bacterial Symbiosis, Counterillumination, Lure Predation",
    "Bioluminescence has evolved independently at least 40 times, using the same chemical reaction: luciferin + O₂ → oxyluciferin + light (catalyzed by luciferase). The convergence is so strong that unrelated organisms (fireflies, click beetles, railroad worms) use the same luciferin molecule. Deep-sea anglerfish: symbiotic bioluminescent bacteria in a lure (esca); the fish feeds the bacteria, and the bacteria produce light that attracts prey to the fish. 76% of deep-pelagic organisms are bioluminescent. Midwater squid use counterillumination — photophores on their ventral surface match downwelling light exactly, eliminating their silhouette against the sky. Dinoflagellates: mechanical stimulation (boat wake, swimming fish) triggers a flash — the original 'burglar alarm' hypothesis.",
    "Firefly luciferin: C₁₁H₈N₂O₃S₂. Quantum yield: 0.41-0.88 (firefly luciferase — one of the most efficient chemiluminescent reactions). ATP-dependent: requires Mg-ATP. Coelenterazine: used by 9+ phyla of marine organisms. Bacterial lux operon: luxCDABEG, quorum sensing (autoinducer / LuxI-LuxR). Deep-sea: 76% of organisms in mesopelagic zone are bioluminescent.")
eq_ids['firefly'] = eq_ids['biolum']

eq_ids['mimicry'] = add_eq(
    "Molecular & Morphological Mimicry — Batesian, Müllerian, Aggressive; Orchid Sexual Deception, Myrmecomorphy (Ant Mimicry in 20+ Orders)",
    "Ophrys orchids produce flowers that precisely mimic the shape, color, texture, and pheromonal blend of female bees/wasps — males attempt copulation, fail, and pollinate the orchid. The chemical mimicry is so precise that it reproduces the exact (Z)-9-alkene cuticular hydrocarbons of the target species' females. In myrmecomorphy, spiders, mantids, beetles, hemipterans, and over 2000 species in 20+ arthropod orders have convergently evolved to mimic the morphology, movement, and even chemical signatures of ants — many to prey on the ants they resemble. Dead-leaf butterflies (Kallima): the wing underside has evolved 'leaf damage' patterns, fake midribs, and fake fungal spots. Walking stick insects (Phasmatodea): eggs mimic seeds (with a lipid-rich capitulum) that ants carry underground — the eggs get protected from parasitoids.",
    "Ophrys: alkene positional isomers match target Andrena/Megachile bee sex pheromone blends with <5% variation. Dead-leaf mimic: Kallima inachus ventral wing pattern matches local host plant leaf damage + fungal spot patterns. Myrmecomorph: body elongation + petiolate waist + antennal illusion (1st leg pair moved forward as 'antennae'). Phasmid egg capitulum: elaiosome lipid, ~2% of egg mass — ant-dispersed.")
eq_ids['orchid'] = eq_ids['mimicry']

# ================================================================
# EXTINCT SPECIES — PHYSICAL EXTREMES
# ================================================================

eq_ids['sauropod'] = add_eq(
    "Sauropod Hemodynamics — Pumping Blood 8-10m Vertically Against Gravity, the Largest Terrestrial Organisms Ever (Argentinosaurus ~70-100 tonnes)",
    "How did sauropods pump blood 8-10 meters vertically to a brain without the giraffe's problem of cerebral edema? The physics: blood pressure at heart level must overcome ρ·g·h for every meter of neck. For a 9m vertical neck (Sauroposeidon), ρ_blood·g·9m ≈ 700 mmHg at the heart — roughly 6× human systolic pressure. But this would burst capillaries. Hypotheses: (1) siphon effect — carotid/jugular loop with counter-current, head-toe pressure difference could be as low as venous return pressure; (2) multiple hearts; (3) horizontal neck posture (diplodocids likely kept necks lower; brachiosaurids had vertical). The heart alone of Barosaurus may have weighed ~1.5 tonnes. Additionally: pneumatic invasion of cervical vertebrae by the respiratory system reduced neck mass — vertebrae were up to 75% air. The engineering problem of large body mass: Argentinosaurus may have massed 70-100 tonnes, with column-like limbs (graviportal posture), digitigrade manus, and a respiratory system extending into the skeleton (pneumaticity) to reduce weight. Limb bone cross-sectional area scales as M^{0.75} — elephants are near the maximum for mammalian-style limbs; sauropods solved it differently.",
    "Blood pressure at heart = ρ·g·h + P_brain + venous resistance loss. ρ=1060 kg/m³, g=9.81, h=9m → ΔP≈700 mmHg above brain perfusion pressure. Giraffe (2m neck): systolic ~250 mmHg. Barosaurus reconstruction: estimated heart mass ~1.5 tonnes, wall thickness ~15-20 cm. Pneumaticity: sauropod cervical vertebrae up to 75% air by volume — air sac system invaded bone. This is the universe's largest terrestrial self-supporting structure ever.")
eq_ids['dino_neck'] = eq_ids['sauropod']

eq_ids['meganeura'] = add_eq(
    "Giant Carboniferous Arthropods — Meganeura (70cm Dragonfly), Arthropleura (2.5m Millipede), Pulmonoscorpius (70cm Scorpion) — Oxygen Enables Insect Gigantism",
    "The Carboniferous (~300 MYA) had atmospheric O₂ at ~35% (vs 21% today). Insects breathe through a passive tracheal system — oxygen diffuses through spiracles and tubules, not actively pumped. The diffusion limit for O₂ in a blind-ended tracheal system imposes a maximum body diameter of ~2-3 cm at modern O₂ levels. At 35% O₂, the effective diffusion gradient doubles, allowing proportionally larger insects. The Dragonfly Meganeura monyi achieved 70 cm wingspan — the tracheal tubes in its thorax would have had ~2× the oxygen partial pressure gradient of modern dragonflies. Arthropleura, at 2.5m length and ~50 cm width, would be utterly unable to oxygenate its tissues at modern O₂ levels. When O₂ fell to ~15% at the Permian-Triassic boundary, giant insects went extinct — not from climate but from asphyxiation. This is a hard limit set by passive diffusion: any organism using passive gas exchange is directly bounded by atmospheric partial pressure of oxygen.",
    "Tracheal O₂ diffusion: J = D·ΔP/dx. For cylindrical body of radius r, maximum radius scales as √(pO₂). At 35% O₂, r_max increases by √(0.35/0.21) ≈ 1.29×. But tracheal branching + spiracles can't fully exploit this — the empirical bound seems to be ~3-4× modern insect sizes, suggesting other limits (mechanical, predation, developmental) also apply.  Arthropleura at 2.5m: tracheal diffusion limit predicts ~50 cm max diameter at 35% O₂ — consistent with the widest Arthropleura specimens.")
eq_ids['giant_bug'] = eq_ids['meganeura']

eq_ids['pterosaur'] = add_eq(
    "Pterosaur Giant Flight — Quetzalcoatlus 11m Wingspan, Estimated 200-250 kg, Largest Flying Organism Ever",
    "How does a 250 kg animal fly? Modern birds max out at ~20 kg (bustards, swans). The physics: lift L = ½ρv²SC_L, drag D = ½ρv²SC_D. For a 250 kg pterosaur, wing loading W/S = mg/S ≈ 250kg × 9.81 / 10m² ≈ 245 N/m² ≈ 25 kg/m² — comparable to a hang-glider. But the launch problem: birds jump with legs; pterosaurs launched quadrupedally using explosive forelimb power — their giant wings WERE the launch mechanism. Pterosaur bones were pneumatized (air-filled) with wall thickness ~0.1-1.0 mm — like modern birds but at much larger scale. The wing membrane (patagium) contained structural fibers (aktinofibrils) that stiffened it aerodynamically — unlike bat wings which are muscular/elastic, pterosaur wings were stiff airfoils with individual fiber-controlled camber. Quetzalcoatlus stood 5-6 m tall on the ground — the height of a giraffe, but capable of powered flight.",
    "Wing loading ~25 kg/m² (Quetzalcoatlus, estimated). Modern albatross: ~8 kg/m². Launch: quadrupedal vault — forelimbs provide 90% of launch impulse, peaking at ~2-3g. Bone pneumaticity: humeral wall thickness ~0.5 mm in Quetzalcoatlus (vs 1-2 mm in a 10 kg bird). Wing fibers (aktinofibrils): keratin-like, ~0.1-0.5 mm diameter, spaced ~0.2 mm apart — structural reinforcement of skin membrane.")
eq_ids['quetz'] = eq_ids['pterosaur']

eq_ids['megalodon'] = add_eq(
    "Megalodon Bite Force — 108,000-182,000 N (~11-19 tonnes-force), Largest Bite Force of Any Organism Ever",
    "Otodus megalodon (15-18m, ~50 tonnes) had an estimated anterior bite force of 108,000-182,000 Newtons — equivalent to the bite of a T. rex (~35,000 N) multiplied by 3-5×. This is a mechanical engineering limit: megalodon teeth are triangular, serrated, and up to 18 cm slant height — designed for shearing through whale blubber and bone. The jaw adductor muscle mass in megalodon would have been ~10-15% of total body mass (~5-7 tonnes of jaw muscle). By comparison: great white shark (Carcharodon) bite force ~18,000 N, saltwater crocodile ~16,000 N. The limit isn't muscle strength — it's the compressive strength of the tooth material (enameloid fluoroapatite, ~400 MPa compressive). Megalodon teeth occasionally show tip fractures indicating they approached the material limit of their own dentition.",
    "Bite force estimated from 3D FEA of fossil vertebrae + jaw reconstruction + scaling from Carcharodon. Compressive strength of shark enameloid ~350-450 MPa. Tooth tip stress concentration: F/(πr²_tip) must remain below enameloid fracture stress. For r_tip ~0.5 mm, maximum tip load ~300 N → megalodon teeth distributed load across 200+ teeth contacting simultaneously, reducing per-tooth stress. Tooth serrations: reduce initiation fracture toughness by ~30% via stress concentration at serration tips — the self-sharpening mechanism.")
eq_ids['meg'] = eq_ids['megalodon']

eq_ids['ichthyosaur'] = add_eq(
    "Ichthyosaur Eyes — 25-26 cm Diameter, Largest Eyes of Any Vertebrate Ever (Temnodontosaurus, Ophthalmosaurus)",
    "Temnodontosaurus and Ophthalmosaurus had eyes up to 25-26 cm in diameter — larger than a dinner plate. For comparison: the largest modern animal eye is the colossal squid (~30 cm), and the blue whale's eye is only ~15 cm. But these ichthyosaurs achieved this eye size in a 6-9m body (not 30m like a blue whale). The sclerotic ring (a bony ring supporting the eye in many vertebrates) is preserved in fossils and directly gives eye diameter. Why? Probably for hunting in the mesopelagic zone (200-1000m) — at these depths, the only light is bioluminescent prey. Larger pupil area (∝ D²) collects more photons. At 25 cm diameter and an estimated pupil size of ~15 cm, the light-gathering area is ~175 cm² — vs ~0.4 cm² for human dark-adapted pupil, a factor of ~440×. This allowed ichthyosaurs to see bioluminescent prey at extreme depths.",
    "Eye aperture ∝ D²: ~26 cm diameter → collection area ~530 cm² total, pupil ~175 cm². f-number of vertebrate eye ~2-4 in water → long focal length ~50 cm. Retina area ~50-100 cm² with high ganglion cell density (estimated from sclerotic ring diameter vs skull/brain cavity ratio). For comparison: giant squid eye 27-30 cm (largest modern), Mesonychoteuthis.")
eq_ids['ichthy_eye'] = eq_ids['ichthyosaur']

eq_ids['cambrian'] = add_eq(
    "Cambrian Body Plan Explosion — Opabinia (5 Eyes + Trunk Claw), Anomalocaris (Meter-Long Compound-Eyed Predator), Hallucigenia (Reconstructed Upside Down), Wiwaxia (Scale Armor), Odontogriphus (Radula Scraper)",
    "The Cambrian (~540-485 MYA) produced body plans so alien that paleontologists initially reconstructed many backwards or upside down. Hallucigenia was originally interpreted as walking on rigid spines with tentacles as dorsal feeding appendages — the correct reconstruction inverted it. Opabinia: 5 mushroom-shaped compound eyes on stalks + a flexible frontal proboscis ending in a grasping claw + segmented body with lateral lobes — a body plan that fits no modern phylum. Anomalocaris: meter-long apex predator with a circular mouth of overlapping plates (like a pineapple slice) surrounded by grasping appendages, with true compound eyes (>16,000 ommatidia). The Burgess Shale fauna challenges the assumption that complex life converges on familiar forms — many Cambrian body plans represent 'failed experiments' that had no evolutionary descendants. This is the universe showing you that carbon-based life has far more morphological degrees of freedom than what survived to the present.",
    "Anomalocaris: compound eyes with >16,000 ommatidia (rivaling modern dragonflies). Body length 0.3-1.0 m. Oral cone: 32 overlapping plates, tri-radial symmetry (yes, 3-fold — rare in animal body plans). Opabinia: 5 eyes, segmented but no known phylum affinity — possibly stem-group arthropod. Hallucigenia: now confidently placed as stem-group onychophoran (velvet worms) — the spines were dorsal defense, the 'tentacles' were lobopod walking legs. These are the weirdest legitimate scientific body plans in the fossil record.")
eq_ids['hallucigenia'] = eq_ids['cambrian']

# ================================================================
# API FETCHERS
# ================================================================
def s2_fetch(q, lim=5):
    out = []
    try:
        u = "https://api.semanticscholar.org/graph/v1/paper/search?" + urllib.parse.urlencode({
            "query": q, "limit": lim, "fields": "title,year,externalIds,journal,citationCount"})
        r = urllib.request.Request(u, headers={"User-Agent": "RadAdapt/1.0"})
        with urllib.request.urlopen(r, timeout=20) as res:
            d = json.loads(res.read().decode())
        for p in d.get("data",[]):
            e = p.get("externalIds",{}) or {}
            j = p.get("journal",{}) or {}
            out.append({"title":p.get("title","")[:250],"year":p.get("year")or 0,
                       "doi":e.get("DOI",""),"journal":j.get("name",""),"src":"S2"})
    except: pass
    return out

def crossref_fetch(q, lim=5):
    out = []
    try:
        u = "https://api.crossref.org/works?" + urllib.parse.urlencode({
            "query": q, "rows": lim, "sort": "relevance", "filter": "type:journal-article"})
        r = urllib.request.Request(u, headers={"User-Agent": "RadAdapt/1.0 (mailto:r@x.com)"})
        with urllib.request.urlopen(r, timeout=20) as res:
            d = json.loads(res.read().decode())
        for i in d.get("message",{}).get("items",[]):
            t = (i.get("title",[""]) or [""])[0]
            y = i.get("created",{}).get("date-parts",[[0]])[0][0]
            d2 = i.get("DOI","")
            j2 = (i.get("container-title",[""]) or [""])[0]
            if t: out.append({"title":t[:250],"year":y,"doi":d2,"journal":j2,"src":"Crossref"})
    except: pass
    return out

def openalex_fetch(q, lim=5):
    out = []
    try:
        u = "https://api.openalex.org/works?" + urllib.parse.urlencode({
            "search": q, "per_page": lim, "sort": "cited_by_count:desc"})
        r = urllib.request.Request(u, headers={"User-Agent": "mailto:r@x.com"})
        with urllib.request.urlopen(r, timeout=20) as res:
            d = json.loads(res.read().decode())
        for i in d.get("results",[]):
            t = i.get("title","")
            y = i.get("publication_year")or 0
            d2 = i.get("doi","")
            j2 = ""
            if i.get("primary_location") and i["primary_location"].get("source"):
                j2 = i["primary_location"]["source"].get("display_name","")
            if t: out.append({"title":t[:250],"year":y,"doi":d2,"journal":j2,"src":"OpenAlex"})
    except: pass
    return out

# Research queries
QUERIES = [
    ("tardigrade cryptobiosis trehalose glass vitrification survival mechanism", "crypto"),
    ("wood frog Rana sylvatica freeze tolerance glucose cryoprotectant", "cryo"),
    ("Turritopsis dohrnii immortal jellyfish transdifferentiation rejuvenation", "immortal"),
    ("cryptochrome magnetoreception radical pair mechanism bird navigation quantum biology", "quantum_bio"),
    ("human rod photoreceptor single photon detection threshold", "photon"),
    ("electric eel electrophorus electrocyte voltage generation sodium channel", "electric"),
    ("pistol shrimp snapping cavitation sonoluminescence bubble collapse", "cavitation"),
    ("cuttlefish octopus chromatophore iridophore camouflage body pattern", "camouflage"),
    ("mitochondrial origin endosymbiosis alpha proteobacterium eukaryogenesis", "endosymbiosis"),
    ("spider silk beta sheet nanocrystal toughness tensile molecular dynamics dragline", "silk"),
    ("Elysia chlorotica kleptoplasty chloroplast horizontal gene transfer photosynthesis", "kleptoplasty"),
    ("echolocation prestin molecular convergence bats dolphins toothed whales", "echolocation"),
    ("bombardier beetle hydroquinone hydrogen peroxide explosive biochemistry catalase", "chem_defense"),
    ("axolotl regeneration blastema dedifferentiation limb spinal cord mechanism", "regeneration"),
    ("leaf cutter ant fungus mutualism atta acromyrmex Leucoagaricus coevolution", "social_farm"),
    ("naked mole rat cancer resistance hyaluronan high molecular weight longevity", "mole_rat"),
    ("bioluminescence firefly luciferin luciferase convergent evolution independent origins", "biolum"),
    ("Ophrys orchid sexual deception insect pheromone mimicry chemical convergence", "mimicry"),
    ("sauropod neck posture blood pressure cardiovascular physiology Barosaurus", "sauropod"),
    ("Carboniferous Meganeura Arthropleura gigantism oxygen pulse tracheal diffusion insect", "meganeura"),
    ("Quetzalcoatlus pterosaur giant flight wing loading pneumatic bone quadrupedal launch", "pterosaur"),
    ("megalodon bite force tooth enameloid compressive strength finite element analysis", "megalodon"),
    ("ichthyosaur Ophthalmosaurus sclerotic ring eye diameter mesopelagic vision", "ichthyosaur"),
    ("Burgess Shale Cambrian Anomalocaris Hallucigenia Opabinia body plan disparity", "cambrian"),
]

# API rotation
print(f"Searching {len(QUERIES)} adaptation queries across Crossref + OpenAlex + S2...\n")
total = 0
rows = []
start = time.time()
apis = [(crossref_fetch,1.5), (openalex_fetch,1.5), (s2_fetch,2.0), (crossref_fetch,1.5), (openalex_fetch,1.5), (s2_fetch,2.0)]

for i, (q, tag) in enumerate(QUERIES):
    fn, delay = apis[i % len(apis)]
    papers = fn(q, 5)
    this_eq = eq_ids.get(tag, list(eq_ids.values())[i % len(eq_ids)])
    for j, p in enumerate(papers):
        rows.append((this_eq, p['title'],
            f"{p['src']}: {p.get('journal','')}" if p.get('journal') else p['src'],
            p['year'], p.get('doi', p['src']), "Radical adaptation ref."))
        total += 1
    short = q[:60]
    print(f"  {'✓' if papers else '○'} [{papers[0]['src'] if papers else '---':10s}] {short:60s} → {len(papers):2d}p | {total:3d} total | {time.time()-start:.0f}s", flush=True)
    time.sleep(delay)

cur.executemany("INSERT INTO verifications (equation_id, test_name, experiment, year, precision_level, status) VALUES (?,?,?,?,?,?)", rows)
conn.commit()

cur.execute("SELECT COUNT(*) FROM verifications WHERE status='Radical adaptation ref.'")
c1 = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM equations WHERE domain_id=?", (new_did,))
c2 = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM verifications")
c3 = cur.fetchone()[0]
print(f"\n═══ RADICAL ADAPTATIONS ═══")
print(f"  {c2} adaptation equations ({len(QUERIES)} queries)")
print(f"  {c1} paper references")
print(f"  DB total: {c3} verifications")
conn.close()
print(f"  {DB}")
