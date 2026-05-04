#!/usr/bin/env python3
"""
Ask swarm to adapt OTOM v4 cotranslational simulator to waveprobe.

This script asks the swarm to analyze the codon_peptide_rl_simulation_v4.py
and propose waveprobe integration for testing and validation.
"""

import json
import uuid
from pathlib import Path
from datetime import datetime

# =========================================================
# Waveprobe Adaptation Request for OTOM v4 Simulator
# =========================================================

WAVEPROBE_REQUEST = {
    "probe_type": "adaptation_request",
    "target_system": "codon_peptide_rl_simulation_v4.py",
    "target_description": "OTOM v4 cotranslational codon-to-peptide simulator with RL policy, cotranslational dynamics, and bias ablation",
    "adaptation_goal": "waveprobe_compatibility",
    "waveprobe_requirements": {
        "probe_generation": {
            "description": "Generate waveprobe test cases for simulator validation",
            "required_interfaces": [
                "parameter_sweep_probes",
                "seed_variation_probes",
                "bias_ablation_probes",
                "convergence_validation_probes"
            ]
        },
        "execution_interface": {
            "description": "Standardized execution wrapper for waveprobe testing",
            "required_methods": [
                "execute_with_probe_config",
                "extract_metrics",
                "validate_convergence",
                "export_waveprobe_results"
            ]
        },
        "result_storage": {
            "description": "Store results in waveprobe-compatible format for topological storage",
            "required_fields": [
                "probe_id",
                "execution_timestamp",
                "simulator_config",
                "metrics",
                "convergence_status",
                "final_codons",
                "phi_trajectory",
                "theta_trajectory"
            ]
        }
    },
    "simulator_analysis": {
        "current_interface": {
            "entry_point": "run_v4(use_bias=False, seed=7, T=360, Lexp=2)",
            "outputs": {
                "history": {
                    "phi": "Phi_CDS trajectory",
                    "theta": "Torsion trajectory (phi, psi)",
                    "translated": "Visible codon count",
                    "pause": "Pause intensity",
                    "contact": "Contact probability",
                    "free_energy": "Free energy",
                    "delay_bias": "Delay bias vector",
                    "codon_bias": "Codon bias vector",
                    "visible": "Visible prefix",
                    "policy": "RL policy per position",
                    "gates": "Expert gate values",
                    "final_codons": "Final codon choices",
                    "final_phi": "Final Phi_CDS score",
                    "best_phi": "Best Phi_CDS score"
                }
            },
            "parameters": {
                "use_bias": "Boolean - enable transient codon structural bias",
                "seed": "Integer - random seed",
                "T": "Integer - total time steps",
                "Lexp": "Integer - exposed tail window size"
            }
        },
        "waveprobe_adaptation_points": [
            {
                "point": "parameter_sweep",
                "description": "Generate waveprobe probes that sweep key parameters",
                "parameters_to_sweep": ["use_bias", "seed", "T", "Lexp"],
                "probe_generation_strategy": "factorial_design"
            },
            {
                "point": "convergence_validation",
                "description": "Validate convergence across multiple seeds",
                "validation_criteria": {
                    "codon_convergence": "final codons should stabilize across seeds",
                    "phi_convergence": "final phi should converge within tolerance",
                    "delta_threshold": "delta between bias and base should be small (< 1e-4)"
                }
            },
            {
                "point": "metric_extraction",
                "description": "Extract standardized metrics for waveprobe comparison",
                "required_metrics": [
                    "final_phi",
                    "best_phi",
                    "phi_convergence_rate",
                    "codon_convergence_stability",
                    "contact_formation_rate",
                    "pause_intensity_profile"
                ]
            },
            {
                "point": "result_serialization",
                "description": "Serialize results in waveprobe-compatible JSON format",
                "serialization_format": "waveprobe_v2.0"
            }
        ]
    },
    "requested_deliverables": [
        {
            "deliverable": "waveprobe_adapter_class",
            "description": "Python class that wraps run_v4() with waveprobe interface",
            "methods": [
                "__init__(config)",
                "execute_probe(probe_config)",
                "extract_metrics(history)",
                "validate_convergence(metrics)",
                "serialize_results(metrics, probe_id)",
                "store_to_topological(results)"
            ]
        },
        {
            "deliverable": "probe_generator",
            "description": "Generate waveprobe test cases for v4 simulator",
            "probe_types": [
                "parameter_sweep_probe",
                "multi_seed_convergence_probe",
                "bias_ablation_comparison_probe",
                "convergence_stability_probe"
            ]
        },
        {
            "deliverable": "waveprobe_test_script",
            "description": "Script that executes waveprobe tests on v4 simulator",
            "features": [
                "probe_generation",
                "parallel_execution",
                "metric_extraction",
                "convergence_validation",
                "result_storage_to_gdrive"
            ]
        }
    ],
    "integration_points": {
        "ene_credential_manager": {
            "description": "Use ENE for Google Drive credential management",
            "integration_path": "4-Infrastructure/infra/ene_cloud_credential_manager.py"
        },
        "topological_storage": {
            "description": "Store waveprobe results in Google Drive topological storage",
            "storage_path": "gdrive:topological_storage/waveprobes/otom_v4/"
        },
        "swarm_integration": {
            "description": "Register v4 simulator as waveprobe-compatible component",
            "registration_endpoint": "swarm_api.py"
        }
    }
}

def generate_waveprobe_request():
    """Generate waveprobe adaptation request for swarm."""
    probe_id = f"wave_{uuid.uuid4().hex[:12]}"
    timestamp = datetime.now().isoformat()
    
    request = {
        "probe_id": probe_id,
        "timestamp": timestamp,
        "request_type": "waveprobe_adaptation",
        "payload": WAVEPROBE_REQUEST
    }
    
    return request

def save_request(request, output_path):
    """Save waveprobe request to file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(request, f, indent=2)
    
    print(f"Waveprobe adaptation request saved to: {output_path}")
    print(f"Probe ID: {request['probe_id']}")
    return output_path

def main():
    """Main entry point."""
    print("=" * 70)
    print("Waveprobe Adaptation Request for OTOM v4 Simulator")
    print("=" * 70)
    
    request = generate_waveprobe_request()
    output_path = Path("shared-data/data/swarm_requests") / f"waveprobe_adaptation_v4_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    saved_path = save_request(request, output_path)
    
    print("\n" + "=" * 70)
    print("Request Summary:")
    print("=" * 70)
    print(f"Target: {WAVEPROBE_REQUEST['target_system']}")
    print(f"Goal: {WAVEPROBE_REQUEST['adaptation_goal']}")
    print(f"Deliverables: {len(WAVEPROBE_REQUEST['requested_deliverables'])}")
    for d in WAVEPROBE_REQUEST['requested_deliverables']:
        print(f"  - {d['deliverable']}")
    print(f"Integration Points: {len(WAVEPROBE_REQUEST['integration_points'])}")
    for k in WAVEPROBE_REQUEST['integration_points'].keys():
        print(f"  - {k}")
    print("=" * 70)
    
    print("\nNext steps:")
    print("1. Submit this request to swarm for analysis")
    print("2. Swarm will generate waveprobe adapter code")
    print("3. Integrate adapter with codon_peptide_rl_simulation_v4.py")
    print("4. Execute waveprobe tests")
    print("5. Store results in topological storage via ENE")

if __name__ == "__main__":
    main()
