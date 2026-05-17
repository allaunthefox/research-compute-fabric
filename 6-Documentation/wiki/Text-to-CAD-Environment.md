# Text-to-CAD Environment

> **Source:** [[Home|Wiki Home]] · [[Build-System]] · `5-Applications/text-to-cad/README.md` · `5-Applications/text-to-cad/AGENTS.md`

The Text-to-CAD harness (`5-Applications/text-to-cad/`) drives agentic 3D
modeling by exposing `build123d` and `OCP` (OpenCascade) bindings to coding
agents like Codex and Claude Code. The canonical VSCode task and npm script
matrix lives in [[Build-System]]. This page stays focused on the CAD-specific
environment shape, sequencing, and agent constraints.

For the agent contract (file-targeted skills, viewer handoff rules, prompt-ref
grammar), see `5-Applications/text-to-cad/AGENTS.md`.

---

## CAD Environment Setup

The Text-to-CAD harness uses a repo-local virtual environment at
`5-Applications/text-to-cad/.venv` that is created from the pinned Python
interpreter described in [[Build-System#Python Environment Management]].

### Bootstrap order

```bash
# 1. From the repository root
npm run install-python       # uv python install 3.11.15
npm run setup-cad-env        # creates 5-Applications/text-to-cad/.venv
npm run verify-cad           # prints "CAD dependencies OK" on success
```

The `Setup CAD Environment` task is idempotent — re-running it against an
existing `.venv` will reuse it and only update pinned packages. To force a
clean rebuild, remove `5-Applications/text-to-cad/.venv` first.

For the exact VSCode task labels, npm script definitions, and command bodies,
use [[Build-System]]. Do not duplicate that matrix here; when a task or script
changes, update [[Build-System]] and keep this page limited to the CAD workflow
that consumes those commands.

### Agent contract

The harness's `AGENTS.md` requires all CAD tooling to be invoked through
`./.venv/bin/python` from `5-Applications/text-to-cad/`. The `Verify CAD
Dependencies` task is the canonical preflight check before running any of the
skill scripts (`gen_step_part`, `gen_step_assembly`, `gen_urdf`, `cadref`,
`snapshot`). If the verification fails, agents are expected to re-run the
`Setup CAD Environment` task before attempting CAD generation.

---

## Related

- [[Build-System]] — Python version pinning, uv integration, VSCode interpreter
  configuration that this environment builds on.
- `5-Applications/text-to-cad/README.md` — user-facing quick start, feature
  list, and bundled skill catalog.
- `5-Applications/text-to-cad/AGENTS.md` — agent contract, viewer handoff
  rules, and common harness commands.
- `5-Applications/text-to-cad/requirements-cad.txt` — pinned CAD dependency
  set installed into `.venv`.
