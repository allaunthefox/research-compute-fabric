# Gemini CLI Instructions for Research Stack

You are working in the **Research Stack** project. This project is a formally verified, formally grounded, and hardware-native stack. You MUST adhere to the strict operating rules defined in the `AGENTS.md` files.

## Primary Mandate
**Lean is the source of truth.** All core logic belongs in `0-Core-Formalism/lean/Semantics/`. Python, Rust, and Verilog are shims/extraction targets only.

## Key Constraints (from AGENTS.md)
- **NO FLOATS:** Use `Q0_16` (pure fraction) or `Q16_16` (mixed) fixed-point. Floats are BANNED in core logic.
- **NO NEW DEPENDENCIES:** Do not add libraries without explicit human approval.
- **NO BROAD REFACTORING:** Only change code that is broken, violates invariants, or cannot be extracted.
- **STATISTICAL RIGOR:** All statistical claims must hit **6.5σ** (preferred) or **6σ** (acceptable). **5σ** is the absolute floor.
- **GIT HYGIENE:** Never use `git add .`. Always use explicit file lists.
- **RECOVER LEGACY INFORMATION:** Use this exact trigger to revive archived info from cornfield branches.
- **SI UNITS:** All physical and compression claims must use SI base units.
- **WOLFRAM ALPHA:** Verify all mathematical formulas with Wolfram Alpha when possible.

## Verification Workflow
1. **Plan:** Outline the Lean implementation and the required theorems/#eval witnesses.
2. **Act:** Implement in Lean first. Update shims only as extraction targets.
3. **Validate:** Run `lake build` in `0-Core-Formalism/lean/Semantics/`.
4. **Receipts:** All infrastructure or storage changes must produce a machine-readable receipt.

## Terminology
- Use **Sidon labels**, **BraidStorm**, **eigensolid**, **scar**, **receipt**.
- Refer to `AGENTS.md` for the full glossary.

## Sub-Agents & Tools
- Use `storage_agent.py` for restic/Garage/rclone operations.
- Use `gen_step_part` etc. for CAD work in `5-Applications/text-to-cad/`.
- Use `podman exec research-stack` for container-bound tasks (Lean builds, WGSL).

## References
- Root Contract: `AGENTS.md`
- Documentation/Lean Strict Rules: `6-Documentation/docs/AGENTS.md`
- Infrastructure: `4-Infrastructure/AGENTS.md`
- CAD: `5-Applications/text-to-cad/AGENTS.md`

<!-- BEGIN ContextStream -->
## 🚨 CRITICAL RULE #1 - CONTEXTSTREAM SEARCH FIRST 🚨

**BEFORE using Glob, Grep, Search, Read (for discovery), Explore, Task(Explore), EnterPlanMode, or ANY local file scanning:**
```
STOP → Call search(mode="auto", query="...") FIRST
```

**Note:** PreToolUse hooks block these tools when ContextStream is available.
**Claude Code users:** Your tool names are `mcp__contextstream__search`, `mcp__contextstream__init`, etc.

❌ **NEVER DO THIS:**
- `Glob("**/*.ts")` → Use `search(mode="pattern", query="*.ts")` instead
- `Grep("functionName")` → Use `search(mode="keyword", query="functionName")` instead
- `Read(file)` for discovery → Use `search(mode="auto", query="...")` instead
- `Explore` or `Task(subagent_type="Explore")` → Use `search(mode="auto")` instead
- `EnterPlanMode` for discovery → Use `search(mode="auto", output_format="paths")` instead

✅ **ALWAYS DO THIS:**
1. `search(mode="auto", query="what you're looking for")`
2. Only use local tools (Glob/Grep/Read) after stale/not-indexed refresh grace window elapses (~20s) or ContextStream still returns **0 results** after retry
3. Use Read ONLY for exact file edits after you know the file path

This applies to **EVERY search** throughout the **ENTIRE conversation**, not just the first message.

---
<!-- END ContextStream -->
