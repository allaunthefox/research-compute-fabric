#!/usr/bin/env python3
"""Dynamic Omnitoken LUT slot selector for workload-shaped tiny tokens."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class WorkloadProfile:
    name: str
    slot: int
    default_domain: int
    default_scalar: int
    expected_cost: int
    mountain_range: str
    angry_depth: int
    description: str


@dataclass(frozen=True)
class OmniToken:
    shell: str
    workload: str
    mountain_range: str
    slot: int
    domain: int
    scalar: int
    avmr_signal: int
    s3c_emit: bool
    s3c_score: int
    ammr_safe: bool

    def bytes3(self) -> bytes:
        return bytes([self.slot, self.domain, self.scalar])


PROFILES: dict[str, WorkloadProfile] = {
    "recovery": WorkloadProfile(
        "recovery", 0x01, 0x0D, 0x01, 1, "root_mountain", 1, "minimal recovery pulse"
    ),
    "angry_sphinx": WorkloadProfile(
        "angry_sphinx",
        0x02,
        0x0F,
        0x01,
        21,
        "frustration_range",
        8,
        "default proof-of-defense challenge/quarantine gate",
    ),
    "standards_registry": WorkloadProfile(
        "standards_registry",
        0x20,
        0x10,
        0x01,
        8,
        "public_basis_range",
        3,
        "ISO/RFC/IANA/W3C registry intake",
    ),
    "crypto_mev_research": WorkloadProfile(
        "crypto_mev_research",
        0x30,
        0x31,
        0x01,
        13,
        "adversarial_flow_range",
        6,
        "mempool/token-layer research classifier",
    ),
    "ibmii_ethernet": WorkloadProfile(
        "ibmii_ethernet",
        0x40,
        0x0D,
        0x01,
        3,
        "legacy_shell_range",
        2,
        "software Ethernet shell on IBM-II-class target",
    ),
    "iso_prepass": WorkloadProfile(
        "iso_prepass",
        0x50,
        0x51,
        0x01,
        5,
        "symbol_basis_range",
        2,
        "shared public symbol-basis compression pass",
    ),
}

LUTS: dict[tuple[int, int, int], str] = {
    (0x01, 0x0D, 0x01): "recover",
    (0x02, 0x0F, 0x01): "angry_sphinx_challenge",
    (0x20, 0x10, 0x01): "index_standard_surface",
    (0x20, 0x10, 0x02): "refresh_registry_pointer",
    (0x30, 0x31, 0x01): "classify_mempool_surface",
    (0x30, 0x31, 0x02): "route_mev_research_candidate",
    (0x40, 0x0D, 0x01): "recover_from_ethernet_shell",
    (0x50, 0x51, 0x01): "apply_iso_symbol_basis",
}


def select_profile(workload: str, pressure: int) -> WorkloadProfile:
    profile = PROFILES.get(workload)
    if profile is None:
        return PROFILES["angry_sphinx"]
    if pressure >= 90 and workload != "recovery":
        return PROFILES["recovery"]
    return profile


def avmr_signal(shell: str, workload: str, pressure: int) -> int:
    """Tiny AVMR-like spectral audit: returns a bounded 0..255 mountain signal."""
    text = f"{shell}:{workload}".encode("utf-8")
    # This is intentionally cheap: structured names produce stable signal without
    # carrying the registry table. The real AVMR layer can replace this function.
    shell_mass = sum((idx + 1) * byte for idx, byte in enumerate(text)) & 0xFF
    pressure_penalty = min(pressure * 2, 200)
    return max(0, min(255, shell_mass - pressure_penalty + 64))


def s3c_partial_gate(slot: int, domain: int, scalar: int, budget: int) -> tuple[bool, int]:
    """Partial S3C gate: shell handles agree before full LUT expansion."""
    n = ((slot & 0xFF) << 8) | ((domain & 0xFF) << 4) | (scalar & 0x0F)
    k = int(n**0.5)
    a = n - k * k
    b = (k + 1) * (k + 1) - n
    mass = a * b
    width = max(1, a + b + 1)
    echo = ((slot ^ domain) + scalar) & 0xFF
    contact_a = (a + echo) % 3 != 0
    contact_c = (b + echo) % 5 != 0
    score = (mass % 256) + budget - width
    return contact_a and contact_c and score > 0, max(0, min(255, score))


def ammr_allows(profile: WorkloadProfile, signal: int, pressure: int, s3c_emit: bool) -> bool:
    """Tiny AMMR gate: finite safety decision before LUT expansion."""
    if profile.name == "angry_sphinx":
        return True
    if profile.name == "recovery":
        return True
    if pressure >= 90:
        return False
    return signal >= 24 and s3c_emit


def make_token(
    shell: str,
    workload: str,
    pressure: int,
    scalar: int | None = None,
    partial_budget: int = 32,
) -> OmniToken:
    profile = select_profile(workload, pressure)
    signal = avmr_signal(shell, profile.name, pressure)
    candidate_scalar = profile.default_scalar if scalar is None else scalar
    s3c_emit, s3c_score = s3c_partial_gate(
        profile.slot, profile.default_domain, candidate_scalar, partial_budget
    )
    safe = ammr_allows(profile, signal, pressure, s3c_emit)
    if not safe and profile.name != "recovery":
        profile = PROFILES["recovery"] if pressure >= 90 else PROFILES["angry_sphinx"]
        signal = avmr_signal(shell, profile.name, pressure)
        candidate_scalar = profile.default_scalar if scalar is None else scalar
        s3c_emit, s3c_score = s3c_partial_gate(
            profile.slot, profile.default_domain, candidate_scalar, partial_budget
        )
        safe = ammr_allows(profile, signal, pressure, s3c_emit)
    return OmniToken(
        shell=shell,
        workload=profile.name,
        mountain_range=profile.mountain_range,
        slot=profile.slot,
        domain=profile.default_domain,
        scalar=candidate_scalar,
        avmr_signal=signal,
        s3c_emit=s3c_emit,
        s3c_score=s3c_score,
        ammr_safe=safe,
    )


def admit(token: OmniToken) -> str:
    return LUTS.get((token.slot, token.domain, token.scalar), "refuse")


def event(token: OmniToken, action: str) -> dict[str, object]:
    return {
        "v": "hs-jsonl-0.1",
        "id": f"omni-lut:{token.workload}:0x{token.slot:02X}:0x{token.scalar:02X}",
        "op": "recover" if action.startswith("recover") else "route",
        "surface": {
            "class": "node",
            "kind": "omnisurface.dynamic_lut",
            "caps": ["recover", "route", "attest"],
        },
        "gcl": {
            "admission": "admitted" if action != "refuse" else "refused",
            "capability_tier": "T1_8kb",
            "invariant": "workload_slot_before_lut_expansion",
            "refusal_code": "none" if action != "refuse" else "op_not_supported",
        },
        "omni": {
            "shell": token.shell,
            "workload_profile": token.workload,
            "mountain_range": token.mountain_range,
            "lut_slot": f"0x{token.slot:02X}",
            "domain": f"0x{token.domain:02X}",
            "scalar": f"0x{token.scalar:02X}",
            "avmr_signal": token.avmr_signal,
            "s3c_emit": token.s3c_emit,
            "s3c_score": token.s3c_score,
            "ammr_safe": token.ammr_safe,
            "angry_sphinx_default": token.workload == "angry_sphinx",
            "action": action,
        },
        "privacy": {
            "tier": "internal",
            "retention": "cache",
            "export": "deny",
            "redaction": "none",
        },
    }


def run_cases(cases: Iterable[tuple[str, str, int, int | None]], emit_jsonl: bool) -> int:
    refused = 0
    for shell, workload, pressure, scalar in cases:
        token = make_token(shell, workload, pressure, scalar)
        action = admit(token)
        refused += int(action == "refuse")
        if emit_jsonl:
            print(json.dumps(event(token, action), separators=(",", ":")))
        else:
            raw = token.bytes3().hex()
            print(
                f"shell={token.shell} workload={token.workload} "
                f"mountain={token.mountain_range} signal={token.avmr_signal} "
                f"s3c_emit={int(token.s3c_emit)} s3c_score={token.s3c_score} "
                f"ammr_safe={int(token.ammr_safe)} "
                f"slot=0x{token.slot:02X} domain=0x{token.domain:02X} "
                f"scalar=0x{token.scalar:02X} bytes={raw} action={action}"
            )
    return 1 if refused else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shell", default="ethernet")
    parser.add_argument("--workload", default="angry_sphinx", choices=sorted(PROFILES) + ["unknown"])
    parser.add_argument("--pressure", type=int, default=10)
    parser.add_argument("--partial-budget", type=int, default=32)
    parser.add_argument("--scalar", type=lambda value: int(value, 0), default=None)
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--jsonl", action="store_true")
    args = parser.parse_args()
    if not 0 <= args.pressure <= 100:
        parser.error("--pressure must be 0..100")
    if args.scalar is not None and not 0 <= args.scalar <= 0xFF:
        parser.error("--scalar must fit in one byte")
    if not 0 <= args.partial_budget <= 255:
        parser.error("--partial-budget must fit in one byte")
    if args.demo:
        cases = [
            ("unknown-shell", "unknown", 10, None),
            ("ethernet", "ibmii_ethernet", 20, None),
            ("ipv923u", "standards_registry", 25, None),
            ("onion", "crypto_mev_research", 40, None),
            ("serial", "iso_prepass", 15, None),
            ("tcp", "crypto_mev_research", 95, None),
        ]
        return run_cases(cases, args.jsonl)
    token = make_token(args.shell, args.workload, args.pressure, args.scalar, args.partial_budget)
    action = admit(token)
    if args.jsonl:
        print(json.dumps(event(token, action), separators=(",", ":")))
    else:
        raw = token.bytes3().hex()
        print(
            f"shell={token.shell} workload={token.workload} "
            f"mountain={token.mountain_range} signal={token.avmr_signal} "
            f"s3c_emit={int(token.s3c_emit)} s3c_score={token.s3c_score} "
            f"ammr_safe={int(token.ammr_safe)} "
            f"slot=0x{token.slot:02X} domain=0x{token.domain:02X} "
            f"scalar=0x{token.scalar:02X} bytes={raw} action={action}"
        )
    return 1 if action == "refuse" else 0


if __name__ == "__main__":
    raise SystemExit(main())
