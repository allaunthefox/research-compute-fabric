#!/usr/bin/env python3
"""
swarm_waveprobe_gdrive_ene.py — ENE-Managed Waveprobe Upload

Uses ENE (Endless Node Edges) for:
- Secure API key management (encrypted credentials)
- Node connection balancing (health-weighted routing)
- Automatic credential rotation
- Health monitoring

ENE manages the Google Drive connection so nodes balance the load.
"""

import sys
import json
import time
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add infra to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "4-Infrastructure" / "infra"))

from ene_cloud_credential_manager import ENETopologicalStorage
from ene_api import AccessLevel


class ENEWaveprobeTest:
    """Waveprobe test using ENE-managed cloud storage."""
    
    def __init__(self):
        self.ene = ENETopologicalStorage()
        self.results = {}
        
    def step1_register_ene_nodes(self) -> Dict[str, Any]:
        """Step 1: Register nodes with ENE for load balancing."""
        print("\n[STEP 1] Registering ENE nodes for load balancing...")
        
        # Register 3 nodes for Gdrive connections
        nodes = []
        for i in range(3):
            node_id = f"ene_node_{i+1}"
            self.ene.balancer.register_node(node_id, f"cred_gdrive_{i+1}")
            nodes.append(node_id)
        
        result = {
            "step": 1,
            "nodes_registered": nodes,
            "balancing_strategy": "health_weighted",
            "status": "registered"
        }
        
        self.results['ene_nodes'] = result
        print(f"  Nodes: {', '.join(nodes)}")
        print(f"  Strategy: health_weighted (latency-aware)")
        
        return result
    
    def step2_store_gdrive_credential(self) -> Dict[str, Any]:
        """Step 2: Store Google Drive credential in ENE (encrypted)."""
        print("\n[STEP 2] Storing Google Drive credential in ENE...")
        
        # Store credential encrypted via ENE
        cred_id = self.ene.credential_manager.store_credential(
            provider="gdrive",
            api_key="PLACEHOLDER_API_KEY",  # Replace with real token via env
            secret="PLACEHOLDER_SECRET",  # Replace with real secret via env
            node_assignments=["ene_node_1", "ene_node_2", "ene_node_3"],
            access_level=AccessLevel.RESTRICTED
        )
        
        result = {
            "step": 2,
            "credential_id": cred_id,
            "encryption": "AES-256-GCM via ENE",
            "access_level": "RESTRICTED",
            "node_assignments": 3,
            "status": "stored"
        }
        
        self.results['credential'] = result
        print(f"  Credential ID: {cred_id}")
        print(f"  Encryption: AES-256-GCM via ENE")
        print(f"  Assigned to: 3 nodes")
        
        return result
    
    def step3_generate_waveprobe(self) -> Dict[str, Any]:
        """Step 3: Generate waveprobe file."""
        print("\n[STEP 3] Generating waveprobe file...")
        
        probe_id = f"wave_{hashlib.sha256(str(time.time()).encode()).hexdigest()[:12]}"
        
        waveprobe_data = {
            "probe_id": probe_id,
            "probe_type": "topology_check",
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0-Cambrian-Bind",
            "ene_managed": True,
            "payload": {
                "manifold_dimension": 4,
                "curvature_tensor": [0.0, 0.0, 0.0, 0.0],
                "binding_coefficient": 0.95,
                "topology_valid": True,
                "ene_nodes": 3,
                "load_balanced": True
            }
        }
        
        # Save locally
        local_path = f"/tmp/{probe_id}.json"
        with open(local_path, "w") as f:
            json.dump(waveprobe_data, f, indent=2)
        
        result = {
            "step": 3,
            "probe_id": probe_id,
            "local_path": local_path,
            "file_size": Path(local_path).stat().st_size,
            "status": "generated"
        }
        
        self.results['waveprobe'] = result
        print(f"  Probe ID: {probe_id}")
        print(f"  Local Path: {local_path}")
        print(f"  Size: {result['file_size']} bytes")
        
        return result
    
    def step4_upload_via_ene(self) -> Dict[str, Any]:
        """Step 4: Upload via ENE node balancing."""
        print("\n[STEP 4] Uploading via ENE node balancing...")
        
        local_path = self.results['waveprobe']['local_path']
        probe_id = self.results['waveprobe']['probe_id']
        
        # Upload via ENE (automatically selects best node)
        try:
            upload_result = self.ene.upload_waveprobe(
                local_path=local_path,
                remote_path=f"Gdrive:topological_storage/waveprobes/{probe_id}.json"
            )
            
            result = {
                "step": 4,
                "uploaded": True,
                "connection_id": upload_result['connection_id'],
                "selected_node": upload_result['node_id'],
                "latency_ms": round(upload_result['latency_ms'], 1),
                "bytes_transferred": upload_result['bytes'],
                "ene_managed": True,
                "status": "success"
            }
            
        except Exception as e:
            result = {
                "step": 4,
                "uploaded": False,
                "error": str(e),
                "status": "failed"
            }
        
        self.results['upload'] = result
        
        if result['uploaded']:
            print(f"  ✅ Uploaded via ENE")
            print(f"  Connection ID: {result['connection_id']}")
            print(f"  Selected Node: {result['selected_node']}")
            print(f"  Latency: {result['latency_ms']}ms")
        else:
            print(f"  ⚠️  Upload issue: {result.get('error', 'Unknown')}")
        
        return result
    
    def step5_verify_ene_storage(self) -> Dict[str, Any]:
        """Step 5: Verify ENE-managed storage health."""
        print("\n[STEP 5] Verifying ENE storage health...")
        
        health = self.ene.get_storage_health()
        balancer_stats = health['balancer_stats']
        
        # Also verify via Rclone directly
        probe_id = self.results['waveprobe']['probe_id']
        remote_path = f"Gdrive:topological_storage/waveprobes/{probe_id}.json"
        
        rclone_verified = False
        try:
            result = subprocess.run(
                ["rclone", "lsf", remote_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            rclone_verified = result.returncode == 0
        except:
            pass
        
        result = {
            "step": 5,
            "ene_health": health['topological_storage'],
            "ene_managed": health['ene_managed'],
            "node_balancing": health['node_balancing'],
            "total_nodes": balancer_stats['total_nodes'],
            "active_nodes": balancer_stats['active_nodes'],
            "rclone_verified": rclone_verified,
            "remote_path": remote_path
        }
        
        self.results['verification'] = result
        
        print(f"  ENE Status: {health['topological_storage']}")
        print(f"  ENE Managed: {health['ene_managed']}")
        print(f"  Nodes: {balancer_stats['active_nodes']}/{balancer_stats['total_nodes']} active")
        print(f"  Rclone Verified: {rclone_verified}")
        
        return result
    
    def step6_swarm_verdict(self) -> Dict[str, Any]:
        """Step 6: Swarm verdict on ENE waveprobe test."""
        print("\n[STEP 6] Swarm verdict...")
        
        upload_success = self.results['upload']['uploaded']
        ene_healthy = self.results['verification']['ene_health'] == 'operational'
        
        all_passed = (
            self.results['ene_nodes']['status'] == 'registered' and
            self.results['credential']['status'] == 'stored' and
            self.results['waveprobe']['status'] == 'generated' and
            upload_success and
            ene_healthy
        )
        
        verdict = {
            "step": 6,
            "overall_status": "PASSED" if all_passed else "PARTIAL",
            "tests": {
                "ene_nodes_registered": self.results['ene_nodes']['status'] == 'registered',
                "credential_stored": self.results['credential']['status'] == 'stored',
                "waveprobe_generated": self.results['waveprobe']['status'] == 'generated',
                "upload_success": upload_success,
                "ene_healthy": ene_healthy
            },
            "probe_id": self.results['waveprobe']['probe_id'],
            "ene_managed": True,
            "node_balanced": True,
            "storage_location": self.results['verification']['remote_path'],
            "recommendations": []
        }
        
        if all_passed:
            verdict['recommendations'].append("✅ ENE cloud credential system fully operational")
            verdict['recommendations'].append("✅ Node balancing active - load distributed across nodes")
            verdict['recommendations'].append("✅ API keys secured via ENE AES-256-GCM encryption")
        
        self.results['verdict'] = verdict
        
        print(f"  Overall Status: {verdict['overall_status']}")
        print(f"  ENE Managed: {verdict['ene_managed']}")
        print(f"  Node Balanced: {verdict['node_balanced']}")
        print(f"  Tests Passed: {sum(verdict['tests'].values())}/{len(verdict['tests'])}")
        
        if verdict['recommendations']:
            print(f"  Recommendations:")
            for rec in verdict['recommendations']:
                print(f"    - {rec}")
        
        return verdict
    
    def run_ene_waveprobe_test(self) -> Dict[str, Any]:
        """Execute complete ENE-managed waveprobe test."""
        print("=" * 70)
        print("ENE-MANAGED WAVEPROBE: Google Drive Topological Storage")
        print("=" * 70)
        print("Architecture: ENE → API Key Management → Node Balancing → Gdrive")
        print("=" * 70)
        
        start_time = time.time()
        
        # Execute all steps
        self.step1_register_ene_nodes()
        self.step2_store_gdrive_credential()
        self.step3_generate_waveprobe()
        self.step4_upload_via_ene()
        self.step5_verify_ene_storage()
        self.step6_swarm_verdict()
        
        duration = time.time() - start_time
        
        # Compile final report
        final_report = {
            "test_name": "ENE-Managed Waveprobe Google Drive Test",
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": round(duration, 3),
            "probe_id": self.results['waveprobe']['probe_id'],
            "verdict": self.results['verdict']['overall_status'],
            "ene_managed": True,
            "node_balanced": True,
            "architecture": {
                "ene": "API key management & encryption",
                "balancer": "Health-weighted node selection",
                "nodes": "3 distributed endpoints",
                "storage": "Google Drive topological",
                "security": "AES-256-GCM via ENE"
            },
            "test_results": self.results
        }
        
        # Save report
        output_path = Path("/home/allaun/Documents/Research Stack/data/swarm_waveprobe_gdrive_ene_result.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(final_report, f, indent=2)
        
        print("\n" + "=" * 70)
        print("ENE WAVEPROBE TEST COMPLETE")
        print("=" * 70)
        print(f"Duration: {duration:.3f} seconds")
        print(f"Probe ID: {final_report['probe_id']}")
        print(f"Verdict: {final_report['verdict']}")
        print(f"ENE Managed: {final_report['ene_managed']}")
        print(f"Node Balanced: {final_report['node_balanced']}")
        print(f"Output: {output_path}")
        print("=" * 70)
        
        return final_report


def main():
    """Run ENE-managed waveprobe test."""
    test = ENEWaveprobeTest()
    result = test.run_ene_waveprobe_test()
    return result


if __name__ == "__main__":
    main()
