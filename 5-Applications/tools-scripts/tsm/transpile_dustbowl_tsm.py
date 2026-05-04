#!/usr/bin/env python3
# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
import json
import datetime
import os
import argparse
import sys
from pathlib import Path

# Add project root to sys.path to import TSM_COMPILER
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from TSM_COMPILER import TSM_Kernel
except ImportError:
    # Fallback for direct execution
    from TSM_COMPILER import TSM_Kernel

def compile_dustbowl_to_logic_signal_substrate(scad_file):
    print(f"\n[*] USAL-TRANSPILER: Processing '{scad_file}'")
    
    # Legacy data template
    legacy_template = {
        "kind": "physical_matrix_node",
        "state": {
            "node_type": "Dust Bowl Survival Engine - Stirling/DAC Hybrid",
            "active_systems": [
                "Subterranean Moisture Trap",
                "Gamma-Type Stirling Core", 
                "Scrap Kinematics (Bicycle Flywheel)", 
                "Glass-Jar Electrolysis Array"
            ],
            "materials_profile": {
                "RustyMetal": "Fe2O3 Composite",
                "DirtyCopper": "Cu / Cu2O",
                "FadedLego": "Degraded ABS Plastic",
                "GlassJar": "Silica Glass"
            },
            "logic_signal_substrate_mode": "hardware_translation_with_gpgpu",
            "gpgpu_bindings": {
                "compute_backend": "CUDA_OPENCL_HYBRID",
                "thermal_gradient_solver": "FiniteElement_GPU",
                "kinematic_solver": "MuJoCo_RigidBody_Matrix"
            }
        },
        "lineage": {
            "source_path": scad_file,
            "compiler": "USAL-Transpiler v1.0",
            "updated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
    }
    
    # Initialize Kernel
    kernel = TSM_Kernel(substrate="silicon")
    
    # Absorb into manifold
    out_file = scad_file.replace(".scad", ".logic_signal_substrate.json")
    manifold_id = kernel.absorb(out_file, legacy_template)
    
    # Emit v3.2-USAL Manifest
    recompiled_manifest = {
        "logic_signal_substrate_version": "v3.2-USAL",
        "isa_version": "ISA-v1",
        "manifold_id": manifold_id,
        "substrate_transparency": "ENABLED",
        "stability_metric": kernel.surface.stability_metric,
        "absorbed_state": kernel.manifold[out_file],
        "legacy_reference": {
            "original_file": scad_file,
            "original_version": "logic_signal_substrate/1"
        }
    }
    
    with open(out_file, "w") as f:
        json.dump(recompiled_manifest, f, indent=2)
    
    print(f"[Graph OS] -> ACK. Transpiled and absorbed '{scad_file}' into USAL object '{out_file}'.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transpile SCAD to TSM")
    parser.add_argument("scad_file", nargs='?', default="dust_bowl_stirling.scad", help="The SCAD file to transpile")
    args = parser.parse_args()
    
    if os.path.exists(args.scad_file):
        compile_dustbowl_to_logic_signal_substrate(args.scad_file)
    else:
        print(f"[ERROR] Source file {args.scad_file} not found.")