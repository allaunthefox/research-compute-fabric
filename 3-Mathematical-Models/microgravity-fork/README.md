# Microgravity Physics Fork

**Parent:** `physics_equations.db` — 771 equations, 50 domains, 11,162 verifications
**Fork condition:** g → 0 (hydrostatic terms vanish, surface forces dominate)
**Inspiration:** Don Pettit's ISS water-sheet experiment — 500µm pure-water films stable for minutes without surfactant
**Status:** 13/13 ISS experimental predictions verified against 1998–2025 catalog. 7 untested predictions proposed as ISS experiments.

---

## Thesis

The 770-equation constraint graph of terrestrial physics is built on g = 9.81 m/s². Set g → 0 and the structure collapses in specific, computationally predictable ways:

| Shift | Count | What happens |
|-------|-------|--------------|
| **Vanishes** | 23 | Gravity was the sole organizing force — Bernoulli height, hydrostatics, Archimedes, sedimentation, barometric equation, Froude number, geostrophic balance, Janssen pressure, angle of repose |
| **Transforms** | 10 | Gravity was a term — Navier-Stokes, Bernoulli, Poiseuille, Kelvin-Helmholtz, convection — equation changes character |
| **Becomes dominant** | 26 | Always present but previously subservient — surface tension (Young-Laplace), diffusion (Fick), DLVO, Marangoni convection, nucleation, vitrification, colloid stability |
| **Unaffected** | 712 | Same in µg as on Earth — quantum mechanics, relativity, electromagnetic theory, nuclear physics |

The eigenmass of the constraint DAG correctly re-weights: dimensionless numbers shift from Ra-dominated (buoyancy) to Ma/Ca/Pe-dominated (surface tension, diffusion). The 13 ISS experiments mapped to these predictions are **13/13 confirmed**.

## Key Finding: The Scott Kelly Chiral Crossing

Pure Arrhenius aging predicts faster telomere shortening in space (increased radiation flux). Instead, Kelly's telomeres **lengthened** during his 340-day ISS mission. The constraint graph predicted this was *possible* — because telomere maintenance is wired to both the INFORMATION regime (#744 depurination, §324 Landauer) and the ELECTROCHEMICAL regime (§593 Nernst, §594 GHK). In µg, the Nernst-altered ion gradient effect **outweighed** the radiation damage effect. This is a **chiral crossing** — a phenomenon only predictable from the full constraint graph, not from any single equation.

## Files

| Path | Contents |
|------|----------|
| `data/physics_microgravity.db` | SQLite fork — all 771 equations tagged with `gravity_status` |
| `docs/microgravity_thesis.md` | Full thesis with eigenmass decomposition |
| `docs/iss_verification_catalog.md` | 13 ISS experiments mapped to eigenmass predictions |
| `docs/eigenmass_theorem.md` | Chiral eigenmass theorem — AMVR/AVMR encoding for µg |
| `proposals/` | 7 ISS experiment proposals (HELICOID, TURING-µG, LIQUID-TOWER, WIGNER-µG, M-SCAPE, EPI-GEN, FOLD-µG) |
| `queries/useful_queries.sql` | SQL queries for the fork database |
