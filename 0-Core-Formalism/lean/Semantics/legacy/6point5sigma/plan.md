# Plan: Firm Up and Repair AnalysisFoundations

## Assessment
The uploaded file `AnalysisFoundations-delete.md` is a Lean 4 (Mathlib) formalization aiming to provide "Minimal Foundational Definitions for Hamiltonian Mechanics." It currently covers:
- Continuity (ε-δ definitions + basic proofs)
- Differentiability (ε-δ definition + basic proofs)
- Smoothness (inductive C^k and C^∞ definitions)
- Convexity (definition + proof for x²)
- A severely weakened "ODE Theory" section with a trivial stationary-equilibrium certificate mislabeled as Picard-Lindelöf

## Issues Identified
1. **Misleading ODE section**: `ODESolution` definition is pathologically restrictive (forces `f(solution t) = 0` and constancy simultaneously). The `picard_lindelof` theorem is trivial and does not reflect the actual Picard-Lindelöf existence/uniqueness theorem.
2. **No Hamiltonian content**: Despite the title, there are no definitions of phase space, symplectic form, Hamiltonian vector fields, Poisson brackets, Hamilton's equations, or conservation laws.
3. **No multivariable calculus**: Hamiltonian mechanics requires at least gradients/differentials in n dimensions. Currently only ℝ → ℝ functions are handled.
4. **Mathematical gaps**: No derivative value extracted from `DifferentiableAt`, no chain rule, no inverse function theorem, no flow of vector fields.
5. **Inconsistent depth**: Some basic proofs are fully spelled out (continuity of x²) but the ODE section is essentially a tautology with a grandiose name.

## Staged Workflow

### Stage 1 — Structural Design & Repair Strategy
Design the target architecture for the firmed-up file. Decide what a *minimal but honest* foundation for Hamiltonian mechanics in Lean 4 looks like, staying within a single file and without importing heavy ODE machinery from Mathlib.

### Stage 2 — Parallel Writing (by section)
Break the new file into independent sections and delegate to Lean-specialist subagents:
- **Subagent A**: Real Analysis Core (Continuity, Differentiability, Derivative extraction, Chain rule, Product rule, Gradient in n-dim)
- **Subagent B**: Smoothness & Convexity (C^k/C^∞, convex functions, Legendre-Fenchel transform definition)
- **Subagent C**: ODE Foundations (Proper ODESolution definition, existence/uniqueness statement as `sorry`/axiom if too heavy, Flow definition, Gronwall-like estimate)
- **Subagent D**: Hamiltonian Mechanics Core (Phase space, Canonical symplectic form, Hamiltonian vector field, Hamilton's equations, Energy conservation, Poisson bracket)

### Stage 3 — Integration & Consistency
Merge all sections into a single coherent Lean 4 file. Ensure:
- Consistent naming conventions
- No duplicate definitions
- Proper namespace usage
- Honest comments (clearly mark what's proven vs what's postulated)
- All imports are correct and sufficient

### Stage 4 — Lean Syntax Check (heuristic)
Review all Lean code for probable compilation issues (lemma names, import coverage, tactic availability in current Mathlib).

## Output
A single repaired and firmed-up `.md` file containing valid Lean 4 code with proper mathematical foundations for Hamiltonian mechanics.
