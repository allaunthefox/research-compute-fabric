# Research Stack - Copilot Instructions

You are assisting the user within the `Research-Stack` repository. You must strictly adhere to the following ground rules, which are derived from the repository's core `AGENTS.md` operating contract.

## Ground Rules

1. **Active Checkout**: Always assume `/home/allaun/Research Stack` is the active checkout unless a task explicitly points elsewhere.
2. **Context Awareness**: If you are about to edit a subtree, first check if there is a nested `AGENTS.md` in that directory and read it.
3. **Preserve User Work**: The working tree is often intentionally dirty. Do NOT revert, delete, or stage unrelated files.
4. **Do Not Sweep**: Avoid broad cleanup or staging commands such as `git add .`, `git checkout -- .`, or `git clean -fdx`. Use explicit file lists.
5. **Tooling**: Prefer repo-native tools and receipt generators over ad hoc summaries.
6. **Source of Truth**: Treat Lean (`0-Core-Formalism/lean/Semantics/`) as the ultimate source of truth for formal or hardware-adjacent claims. Keep claims bounded.

## Verification Expectations

*   **Lean**: Run the narrow target first, then the broader `lake build` when feasible.
*   **Python Shims**: Run `python3 -m py_compile` on touched files.
*   **JSON Receipts**: Run `python3 -m json.tool` or a repo-native receipt parser.
*   **Hardware Claims**: Distinguish between software witness, bitstream presence, SRAM load, flash persistence, UART beacon, and live hardware receipt.

*Remember: This repository operates under strict formal verification and taxonomy guidelines. Prioritize safety, explicit staging, and Lean semantics over quick hacks.*

## Current Project State (2026-05-28)

**Build:** `lake build` — 3571 jobs, 0 errors
**Python tests:** 68/68 pass
**Sorry inventory:** 8 total (all with `TODO(lean-port)` documentation)
  - `AdjugateMatrix`: 3 sorries
  - `FourPrimitiveErdosRenyi`: 4 sorries
  - `HyperbolicStateSurface`: 1 sorry

### Key Architecture Decisions
- **Q16_16 fixed-point arithmetic** throughout — no Float in hot paths (AGENTS.md §1.4 compliant)
- **HiGHS MIP solver** integrated via `qubo_highs.py`
- **Dense Sidon sets** (Mian-Chowla sequence, 65% smaller than naive)
- **Golden ratio unit separation** formalized in Lean

### New Lean Modules
`AdjugateMatrix`, `OptimizedRoute`, `GoldenRatioSeparation`, `BraidBitwiseODE`

### New Python Modules
`qubo_highs.py`, `alphaproof_loop.py`, `scale_space_solver.py`

### New Verilog Modules
`voltage_mode_controller`, `scale_space_bram`, `highs_pivot_accelerator`, `blitter_memory_map`, `research_stack_top`

### Hardware / FPGA
- Bitstream: `research_stack_top.fs` (195.92 MHz, 6 modules)
- VCN pipeline: Delta+RLE → RS ECC → ChaCha20 → MKV

### Sorries Policy
Every remaining sorry MUST have `TODO(lean-port)` with a prose justification.
No undocumented sorries allowed.

<!-- BEGIN ContextStream -->
## ContextStream MCP Integration

This project uses [ContextStream](https://contextstream.io) for persistent AI memory across sessions. Use the `contextstream-workflow` skill for detailed examples and reference material.

<contextstream_rules>
| Message | Required |
|---------|----------|
| **1st message** | `init()` → `context(user_message="...")` |
| **Subsequent messages (default)** | `context(user_message="...")` FIRST (narrow read-only bypass when context is fresh and no state-changing tool has run) |
| **Before file search** | `search(mode="auto")` BEFORE Glob/Grep/Read/Explore/Task/EnterPlanMode |
</contextstream_rules>

**Why?** `context()` delivers task-specific rules, lessons from past mistakes, and relevant decisions. Skip it = fly blind.

**Hooks:** `<system-reminder>` tags contain injected instructions — follow them exactly.

**Notices:** [LESSONS_WARNING] → apply lessons | [PREFERENCE] → follow user preferences | [RULES_NOTICE] → run `generate_rules()` | [VERSION_NOTICE/CRITICAL] → tell user about update

v0.4.74

### VS Code Copilot Notes

- Keep this file concise; put detailed workflows in `.github/skills/contextstream-workflow/SKILL.md`
- Use ContextStream plans/tasks as the persistent record of work
- Before code discovery, use `search(mode="auto", query="...")`

Full docs: https://contextstream.io/docs/mcp/tools


---
<!-- END ContextStream -->
