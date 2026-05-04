#!/usr/bin/env python3
"""Apply calibrated SNN/FAMM failure-contract fixes in-place.

Run from repo root after copying the harness files:
  python 5-Applications/scripts/snn/apply_snn_calibration_fixes.py
"""
from __future__ import annotations
import json
from pathlib import Path

root = Path.cwd()
cfgp = root / "5-Applications/scripts/snn/snn_test_config.json"
refp = root / "5-Applications/scripts/snn/snn_nii_reference.py"
if not cfgp.exists() or not refp.exists():
    raise SystemExit("Expected 5-Applications/scripts/snn/snn_test_config.json and 5-Applications/scripts/snn/snn_nii_reference.py")

cfg = json.loads(cfgp.read_text())
cfg["version"] = "SNN_NII_TEST_V1_CALIBRATED"
cfg.setdefault("rgflow", {})["threshold"] = 650
cfg["rgflow"]["near_miss_band"] = 160
cfg["rgflow"]["failure_weight"] = 2
cfg.setdefault("famm", {})["decay_frustration"] = 6
cfg["famm"]["decay_torsion"] = 4
cfg["famm"]["decay_basin"] = 2
cfg["famm"]["saturation_warn_at"] = 240
cfgp.write_text(json.dumps(cfg, indent=2) + "\n")

text = refp.read_text()
start = text.index("def famm_update(")
end = text.index("\n\ndef run(", start)
new_block = '''def famm_update(famm: FAMMState, rg: Dict[str, int | str | bool], cfg: dict) -> Dict[str, bool | int]:
    """Update FAMM and expose decay/saturation as first-class signals."""
    f = cfg["famm"]
    before = {"frustration": famm.frustration, "basin": famm.basin, "torsion": famm.torsion}

    famm.frustration = clamp(famm.frustration - int(f.get("decay_frustration", 0)), 0, f["max_frustration"])
    famm.torsion = clamp(famm.torsion - int(f.get("decay_torsion", 0)), 0, 255)
    famm.basin = clamp(famm.basin - int(f.get("decay_basin", 0)), 0, f["max_basin"])

    if rg["verdict"] == "lawful":
        famm.basin = clamp(famm.basin + f["basin_increment"], 0, f["max_basin"])
        famm.frustration = clamp(famm.frustration - 1, 0, f["max_frustration"])
    elif rg["verdict"] == "near_miss":
        famm.basin = clamp(famm.basin + f["near_miss_increment"], 0, f["max_basin"])
        famm.frustration = clamp(famm.frustration + int(rg["reject_pressure"]) // 16, 0, f["max_frustration"])
        famm.torsion = clamp(famm.torsion + int(rg["torsion_delta"]) // 32, 0, 255)
    else:
        famm.frustration = clamp(famm.frustration + int(rg["reject_pressure"]) // 12, 0, f["max_frustration"])
        famm.torsion = clamp(famm.torsion + int(rg["torsion_delta"]) // 24, 0, 255)

    warn = int(f.get("saturation_warn_at", 240))
    saturated_frustration = famm.frustration >= warn
    saturated_basin = famm.basin >= warn
    saturated_torsion = famm.torsion >= warn
    after = {"frustration": famm.frustration, "basin": famm.basin, "torsion": famm.torsion}
    return {
        "changed": before != after,
        "decay_applied": any(int(f.get(k, 0)) > 0 for k in ["decay_frustration", "decay_torsion", "decay_basin"]),
        "saturated_frustration": saturated_frustration,
        "saturated_basin": saturated_basin,
        "saturated_torsion": saturated_torsion,
        "any_saturated": saturated_frustration or saturated_basin or saturated_torsion,
    }
'''
text = text[:start] + new_block + text[end:]
text = text.replace(
    "            rg = rgflow_step(surprise, msnn_out, event, famm, cfg)\n            famm_update(famm, rg, cfg)\n            record = {",
    "            rg = rgflow_step(surprise, msnn_out, event, famm, cfg)\n            famm_flags = famm_update(famm, rg, cfg)\n            record = {",
)
text = text.replace(
    '                "rgflow": rg,\n                "famm": {"frustration": famm.frustration, "basin": famm.basin, "torsion": famm.torsion}\n            }',
    '                "rgflow": rg,\n                "famm": {"frustration": famm.frustration, "basin": famm.basin, "torsion": famm.torsion},\n                "famm_flags": famm_flags\n            }',
)
refp.write_text(text)
print("Applied SNN calibration fixes.")
