# Pending (Lean Unification)

This folder quarantines files that violate the repo's Lean-first direction:

- Lean defines **surfaces** (tool lists, schemas, semantics).
- Non-Lean languages (Rust/Python/etc.) may only implement **thin shims** that:
	- execute Lean-owned decisions, or
	- provide transport/runtime plumbing, without inventing new surface semantics.

Anything here should be treated as *not canonical* and is pending port/removal.
