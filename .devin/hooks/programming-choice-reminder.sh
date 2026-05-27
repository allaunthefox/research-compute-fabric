#!/usr/bin/env bash
# Programming choice flow reminder — injected before every user message.
# Full contract lives in AGENTS.md §Post-Interaction Workflow §5.

cat <<'EOF'
{
  "add_context": "PROGRAMMING CHOICE FLOW (check before writing any new code):\n\n1. Admissibility / gating / routing / alignment decision? → Lean only. No Python equivalent.\n2. Minting a receipt or emitting top-level JSON? → Semantics.AVMIsa.Emit ONLY (sole output boundary).\n3. Classifying rows / computing alignment scores? → Lean (Semantics.RRC.Emit or new Semantics.RRC.* module).\n4. Supplying raw input features (equation text, IDs, weak_axes)? → Python shim OK, but: (a) no admissibility logic, (b) regenerable from source, (c) TODO(lean-port) if portable.\n5. Float arithmetic in a compute path? → STOP. Use Q16_16.ofNat / Q16_16.ofRatio instead.\n6. Advancing promotion status in shim space? → STOP. Always not_promoted until a Lean gate passes.\n7. Pure I/O (read/write JSON, call subprocess, format output)? → Python shim fine; receipt output must route through AVMIsa.Emit.\n\nSummary rule: Lean owns all decisions. Python owns all I/O.\n\nPOST-INTERACTION CHECKLIST (before claiming session complete):\n1. Update nearest AGENTS.md for every touched subtree\n2. lake build Compiler (+ full lake build if Lean files touched)\n3. Commit with explicit file list — never git add .\n4. git status --branch --short --untracked-files=all"
}
EOF
