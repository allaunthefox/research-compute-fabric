#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def default_compartments() -> List[Dict[str, object]]:
    return [
        {
            "name": "mail_submission",
            "purpose": "SMTP sending only",
            "blast_radius": "medium",
            "allowed_dependencies": ["dns", "smtp_gateway"],
            "token_ttl_days": 14,
        },
        {
            "name": "mail_fetch",
            "purpose": "IMAP/Bridge receive only",
            "blast_radius": "medium",
            "allowed_dependencies": ["imap_gateway"],
            "token_ttl_days": 30,
        },
        {
            "name": "auth_recovery",
            "purpose": "account recovery channel",
            "blast_radius": "high",
            "allowed_dependencies": ["offline_backup"],
            "token_ttl_days": 90,
        },
        {
            "name": "evidence_snapshot",
            "purpose": "passive evidence and handoff only",
            "blast_radius": "low",
            "allowed_dependencies": ["local_storage"],
            "token_ttl_days": 180,
        },
        {
            "name": "service_restoration",
            "purpose": "diagnostics and connectivity checks",
            "blast_radius": "low",
            "allowed_dependencies": ["dns", "routing", "http"],
            "token_ttl_days": 7,
        },
    ]


def write_json(path: Path, payload: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_rotation_policy(path: Path, compartments: List[Dict[str, object]]) -> None:
    lines: List[str] = []
    lines.append("# Everywhere-Nowhere Rotation Policy")
    lines.append("")
    lines.append("generated_utc: " + utc_now_iso())
    lines.append("policy_version: 1")
    lines.append("principles:")
    lines.append("  - redundancy_everywhere")
    lines.append("  - identity_coupling_nowhere")
    lines.append("  - passive_evidence_only")
    lines.append("  - no_attribution_claims")
    lines.append("compartments:")
    for item in compartments:
        lines.append(f"  - name: {item['name']}")
        lines.append(f"    purpose: {item['purpose']}")
        lines.append(f"    blast_radius: {item['blast_radius']}")
        lines.append(f"    token_ttl_days: {item['token_ttl_days']}")
        lines.append("    allowed_dependencies:")
        for dep in item["allowed_dependencies"]:
            lines.append(f"      - {dep}")
        lines.append("    controls:")
        lines.append("      - least_privilege")
        lines.append("      - independent_recovery_channel")
        lines.append("      - per-compartment_token")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_compartment_map(path: Path, compartments: List[Dict[str, object]]) -> None:
    lines: List[str] = []
    lines.append("# Everywhere-Nowhere Compartment Map")
    lines.append("")
    lines.append("This map separates roles so each channel is replaceable and isolated.")
    lines.append("")
    for item in compartments:
        lines.append(f"## {item['name']}")
        lines.append("")
        lines.append(f"- Purpose: {item['purpose']}")
        lines.append(f"- Blast radius: {item['blast_radius']}")
        deps = ", ".join(item["allowed_dependencies"])
        lines.append(f"- Allowed dependencies: {deps}")
        lines.append(f"- Token TTL (days): {item['token_ttl_days']}")
        lines.append("- Boundaries: no cross-use of credentials with other compartments")
        lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_recovery_matrix(path: Path, compartments: List[Dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "compartment",
                "primary_channel",
                "backup_channel",
                "rotate_if_compromised_within_hours",
                "owner_role",
            ],
        )
        writer.writeheader()
        for item in compartments:
            writer.writerow(
                {
                    "compartment": item["name"],
                    "primary_channel": "designated_primary",
                    "backup_channel": "designated_backup",
                    "rotate_if_compromised_within_hours": 4 if item["blast_radius"] == "high" else 12,
                    "owner_role": "operator",
                }
            )


def write_runbook(path: Path) -> None:
    lines = [
        "# Everywhere-Nowhere Runbook",
        "",
        "1. Keep channels redundant and isolated.",
        "2. Rotate only the affected compartment token on incidents.",
        "3. Preserve passive evidence snapshots for handoff.",
        "4. Use neutral wording and avoid attribution language.",
        "5. Prioritize service restoration over investigation.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate_profile(out_dir: Path, profile_name: str) -> Dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    compartments = default_compartments()

    profile_json = out_dir / f"{profile_name}.json"
    rotation_policy = out_dir / "rotation_policy.yaml"
    compartment_map = out_dir / "compartment_map.md"
    recovery_matrix = out_dir / "recovery_matrix.csv"
    runbook = out_dir / "runbook.md"

    payload = {
        "schema": "everywhere-nowhere/v1",
        "profile": profile_name,
        "generated_utc": utc_now_iso(),
        "compartments": compartments,
    }

    write_json(profile_json, payload)
    write_rotation_policy(rotation_policy, compartments)
    write_compartment_map(compartment_map, compartments)
    write_recovery_matrix(recovery_matrix, compartments)
    write_runbook(runbook)

    return {
        "profile": str(profile_json),
        "rotation_policy": str(rotation_policy),
        "compartment_map": str(compartment_map),
        "recovery_matrix": str(recovery_matrix),
        "runbook": str(runbook),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate everywhere-nowhere operational profile artifacts.")
    parser.add_argument("--out-dir", default=str(PROJECT_ROOT / "out" / "everywhere_nowhere"), help="Output directory.")
    parser.add_argument("--profile-name", default="everywhere_nowhere_profile", help="Profile basename.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    outputs = generate_profile(Path(args.out_dir), args.profile_name)
    print(json.dumps(outputs, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
