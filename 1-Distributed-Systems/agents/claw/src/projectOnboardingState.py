from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ProjectOnboardingState:
    has_readme: bool
    has_tests: bool
    lean_first: bool = True  # Lean is always the source of truth; Python/Rust are extraction targets
