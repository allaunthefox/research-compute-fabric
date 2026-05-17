#!/usr/bin/env python3
"""Probe the virtual-only EE stress-test toolchain.

This script intentionally does not run device programming commands. It records
tool presence, versions, Python package imports, and the hardware-safety boundary.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "4-Infrastructure" / "hardware" / "ee_virtual_stress_probe_receipt.json"

COMMANDS = {
    "verilator": ["verilator", "--version"],
    "ngspice": ["ngspice", "--version"],
    "yosys": ["yosys", "-V"],
    "iverilog": ["iverilog", "-V"],
    "vvp": ["vvp", "-V"],
    "gtkwave": ["gtkwave", "--version"],
    "abc": ["abc", "-h"],
    "z3": ["z3", "--version"],
    "yices": ["yices", "--version"],
    "vpr": ["vpr", "--version"],
    "odin_ii": ["odin_II", "--version"],
    "tinyprog": ["tinyprog", "--help"],
    "openfpgaloader": ["openFPGALoader", "--version"],
}

PY_MODULES = [
    "cocotb",
    "cocotb_bus",
    "amaranth",
    "vcd",
    "vunit",
    "edalize",
    "fusesoc",
    "PySpice",
    "numpy",
    "scipy",
]

HARDWARE_FORBIDDEN = [
    "openFPGALoader <bitstream>",
    "tinyprog --program",
    "esptool.py write_flash",
    "dfu-util -D",
    "iceprog",
    "ujprog",
    "JTAG/SWD/serial flashing",
]


def run_version(argv: list[str]) -> dict:
    exe = shutil.which(argv[0])
    if not exe:
        return {"present": False}
    try:
        proc = subprocess.run(argv, text=True, capture_output=True, timeout=8)
        text = (proc.stdout or proc.stderr).strip()
        return {
            "present": True,
            "path": exe,
            "returncode": proc.returncode,
            "version_head": text.splitlines()[:6],
        }
    except Exception as exc:  # noqa: BLE001
        return {"present": True, "path": exe, "error": str(exc)}


def probe_module(name: str) -> dict:
    try:
        mod = importlib.import_module(name)
        return {
            "present": True,
            "version": getattr(mod, "__version__", None),
            "file": getattr(mod, "__file__", None),
        }
    except Exception as exc:  # noqa: BLE001
        return {"present": False, "error": str(exc)}


def main() -> None:
    receipt = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "lawful": True,
        "mode": "virtual_only",
        "claim_boundary": (
            "Simulation/lint/formal/synthesis/probe only. No programmer, flasher, "
            "JTAG, serial, USB, or board-write command is run by this probe."
        ),
        "hardware_forbidden": HARDWARE_FORBIDDEN,
        "commands": {name: run_version(argv) for name, argv in COMMANDS.items()},
        "python_modules": {name: probe_module(name) for name in PY_MODULES},
    }
    encoded = json.dumps(receipt, indent=2, sort_keys=True).encode("utf-8")
    receipt["receipt_hash_preimage_sha256"] = hashlib.sha256(encoded).hexdigest()
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
