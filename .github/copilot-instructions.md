# Research Stack - Copilot Instructions

You are assisting the user within the `Research-Stack` repository. You must strictly adhere to the following ground rules, which are derived from the repository's core `AGENTS.md` operating contract.

## Ground Rules

1. **Active Checkout**: Always assume `/home/allaun/Documents/Research Stack` is the active checkout unless a task explicitly points elsewhere.
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

<!-- BEGIN ContextStream -->
## ENE-First Context Rule

Before using ContextStream or local repository search, check the local ENE MCP
server first:

1. `ene_status`
2. `ene_context(user_message="...", save_exchange=true)` on session/message start
3. `ene_search(query="...")`
4. `ene_recall(query="...")` for prior decisions/preferences

Use ContextStream as fallback when ENE is unavailable, empty, or hosted
transcript history is explicitly needed.

## ContextStream MCP Integration

This project uses [ContextStream](https://contextstream.io) for persistent AI memory across sessions. Use the `contextstream-workflow` skill for detailed examples and reference material.
<!-- END ContextStream -->
