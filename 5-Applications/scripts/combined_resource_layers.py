#!/usr/bin/env python3
"""
combined_resource_layers.py — Combined Base + Topological Resource Report

Combines physical/base layer resources with special/topological layers:
- Physical: CPU, RAM, Storage, GPU (36 cores, 72GB, 2.4TB, 1 GPU)
- Topological: Manifold state, BIND compression, semantic space, Triumvirate
- Compression: L3 rules, hyperbolic encoding, experience compression
"""

import json
import math
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any

# Import infrastructure
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "4-Infrastructure" / "infra"))

from ene_cloud_credential_manager import ENETopologicalStorage


@dataclass
class PhysicalLayer:
    """Physical/base layer resources (substrate)."""
    cpu_cores: int
    memory_gb: float
    storage_gb: float
    gpu_count: int
    nodes: int
    bandwidth_mbps: float


@dataclass
class TopologicalLayer:
    """Topological/special layer (compressed state)."""
    # BIND L3 compression
    bind_compression_ratio: float  # Typically 1.6x (from ExperienceCompression)
    l3_rule_count: int
    
    # Semantic space (hyperbolic manifold)
    semantic_dimensions: int  # Q16_16 encoding
    semantic_vectors: int
    
    # Triumvirate state
    builder_state_slots: int
    warden_proof_capacity: int
    judge_adjudication_queue: int
    
    # Manifold topology
    manifold_dimensions: int
    curvature_points: int
    binding_coefficient: float
    
    # ENE mesh state
    ene_nodes: int
    gossip_backlog: int
    credential_fragments: int
    consensus_votes: int
    
    # Compression totals
    effective_memory_gb: float  # Physical * compression
    effective_state_capacity: float  # Conceptual state size


class CombinedResourceCalculator:
    """Calculate combined base + topological resources."""
    
    def __init__(self):
        self.physical = self._calculate_physical()
        self.topological = self._calculate_topological()
        
    def _calculate_physical(self) -> PhysicalLayer:
        """Calculate physical layer from deployed mesh."""
        # From deploy_ene_full_mesh.py results
        return PhysicalLayer(
            cpu_cores=36,  # 16+8+4+2+4+2
            memory_gb=72.0,  # 32+16+8+4+8+4
            storage_gb=2400.0,  # 1000+500+200+100+500+100
            gpu_count=1,  # qfox only
            nodes=6,
            bandwidth_mbps=5000.0  # Aggregate across mesh
        )
    
    def _calculate_topological(self) -> TopologicalLayer:
        """Calculate topological layer (compressed state)."""
        physical = self.physical
        
        # BIND L3 compression (from ExperienceCompression.lean)
        # L3 rules achieve ~1.6x compression ratio
        bind_ratio = 1.6
        l3_rules = 1024  # Typical L3 rule set size
        
        # Semantic space (Q16_16 encoding, from Semantics modules)
        # Each semantic vector is 65536-dimensional in fixed-point
        semantic_dims = 7  # ρ, v, τ, σ, q, κ, ε (from Experience.lean)
        semantic_vecs = physical.nodes * 1000  # ~1000 vectors per node
        
        # Triumvirate state (from GenomicCompression.lean)
        # Builder: manifold_reg slots
        # Warden: stark_trace proof capacity
        # Judge: heatsink_halt queue
        builder_slots = physical.cpu_cores * 4  # 4 states per core
        warden_capacity = 1000  # Proof validation capacity
        judge_queue = 256  # Adjudication backlog
        
        # Manifold topology (from ManifoldFlow, NonEuclideanGeometry)
        manifold_dims = 4  # 4D manifold (from VoxelEncoding)
        curvature_pts = 10000  # Discrete curvature samples
        binding_coef = 0.95  # High binding coefficient
        
        # ENE mesh state
        ene_nodes = physical.nodes
        gossip_backlog = ene_nodes * 100  # ~100 messages per node
        cred_fragments = ene_nodes  # One fragment per node (Shamir)
        consensus_votes = 100  # Active consensus proposals
        
        # Calculate effective capacity
        # Physical memory * BIND compression = effective state capacity
        effective_mem = physical.memory_gb * bind_ratio
        
        # Conceptual state size (semantic vectors * dimensions)
        effective_state = (semantic_vecs * semantic_dims * 8) / (1024**3)  # GB
        
        return TopologicalLayer(
            bind_compression_ratio=bind_ratio,
            l3_rule_count=l3_rules,
            semantic_dimensions=semantic_dims,
            semantic_vectors=semantic_vecs,
            builder_state_slots=builder_slots,
            warden_proof_capacity=warden_capacity,
            judge_adjudication_queue=judge_queue,
            manifold_dimensions=manifold_dims,
            curvature_points=curvature_pts,
            binding_coefficient=binding_coef,
            ene_nodes=ene_nodes,
            gossip_backlog=gossip_backlog,
            credential_fragments=cred_fragments,
            consensus_votes=consensus_votes,
            effective_memory_gb=effective_mem,
            effective_state_capacity=effective_state
        )
    
    def calculate_combined_resources(self) -> Dict[str, Any]:
        """Calculate total combined resources."""
        phys = self.physical
        topo = self.topological
        
        # Combined compute (physical + parallel topological threads)
        total_compute_units = phys.cpu_cores + (topo.builder_state_slots // 4)
        
        # Combined memory (physical + effective compressed state)
        total_memory_gb = phys.memory_gb + topo.effective_memory_gb
        
        # Combined storage (physical + semantic space)
        total_storage_gb = phys.storage_gb + topo.effective_state_capacity
        
        # Combined state capacity (conceptual)
        # This is the theoretical maximum state the system can hold
        # considering compression and topological encoding
        theoretical_state_capacity = (
            phys.memory_gb * topo.bind_compression_ratio * 
            (topo.semantic_vectors / 1000) *  # Scale factor
            topo.binding_coefficient
        )
        
        return {
            "physical_layer": {
                "cpu_cores": phys.cpu_cores,
                "memory_gb": phys.memory_gb,
                "storage_gb": phys.storage_gb,
                "gpu_count": phys.gpu_count,
                "nodes": phys.nodes,
                "bandwidth_mbps": phys.bandwidth_mbps
            },
            "topological_layer": {
                "bind_compression_ratio": topo.bind_compression_ratio,
                "l3_rules": topo.l3_rule_count,
                "semantic_dimensions": topo.semantic_dimensions,
                "semantic_vectors": topo.semantic_vectors,
                "manifold_dimensions": topo.manifold_dimensions,
                "curvature_points": topo.curvature_points,
                "binding_coefficient": topo.binding_coefficient,
                "triumvirate": {
                    "builder_slots": topo.builder_state_slots,
                    "warden_capacity": topo.warden_proof_capacity,
                    "judge_queue": topo.judge_adjudication_queue
                },
                "ene_mesh": {
                    "nodes": topo.ene_nodes,
                    "gossip_backlog": topo.gossip_backlog,
                    "credential_fragments": topo.credential_fragments,
                    "consensus_votes": topo.consensus_votes
                }
            },
            "combined_totals": {
                "total_compute_units": total_compute_units,
                "total_memory_gb": round(total_memory_gb, 1),
                "total_storage_gb": round(total_storage_gb, 1),
                "effective_state_capacity_gb": round(theoretical_state_capacity, 1),
                "total_nodes": phys.nodes,
                "compression_multiplier": topo.bind_compression_ratio,
                "theoretical_expansion_factor": round(
                    theoretical_state_capacity / phys.memory_gb, 2
                )
            }
        }
    
    def print_resource_report(self):
        """Print formatted resource report."""
        resources = self.calculate_combined_resources()
        
        print("=" * 70)
        print("COMBINED RESOURCE LAYERS REPORT")
        print("Base (Physical) + Special (Topological) Layers")
        print("=" * 70)
        
        # Physical Layer
        print("\n📦 PHYSICAL LAYER (Substrate)")
        print("-" * 40)
        phys = resources["physical_layer"]
        print(f"  CPU Cores:        {phys['cpu_cores']}")
        print(f"  Memory:           {phys['memory_gb']:.1f} GB")
        print(f"  Storage:          {phys['storage_gb']:.1f} GB")
        print(f"  GPUs:             {phys['gpu_count']}")
        print(f"  Nodes:            {phys['nodes']}")
        print(f"  Bandwidth:        {phys['bandwidth_mbps']:.0f} Mbps")
        
        # Topological Layer
        print("\n🌀 TOPOLOGICAL LAYER (Compressed State)")
        print("-" * 40)
        topo = resources["topological_layer"]
        print(f"  BIND Compression: {topo['bind_compression_ratio']}x")
        print(f"  L3 Rules:         {topo['l3_rules']}")
        print(f"  Semantic Dims:    {topo['semantic_dimensions']}")
        print(f"  Semantic Vectors: {topo['semantic_vectors']:,}")
        print(f"  Manifold Dims:    {topo['manifold_dimensions']}D")
        print(f"  Curvature Points: {topo['curvature_points']:,}")
        print(f"  Binding Coeff:    {topo['binding_coefficient']}")
        
        # Triumvirate
        print("\n⚖️  TRIUMVIRATE STATE")
        print("-" * 40)
        tri = topo["triumvirate"]
        print(f"  Builder Slots:    {tri['builder_slots']}")
        print(f"  Warden Capacity:  {tri['warden_capacity']}")
        print(f"  Judge Queue:      {tri['judge_queue']}")
        
        # ENE Mesh
        print("\n🔗 ENE MESH STATE")
        print("-" * 40)
        ene = topo["ene_mesh"]
        print(f"  Nodes:            {ene['nodes']}")
        print(f"  Gossip Backlog:   {ene['gossip_backlog']}")
        print(f"  Cred Fragments:   {ene['credential_fragments']}")
        print(f"  Consensus Votes:  {ene['consensus_votes']}")
        
        # Combined Totals
        print("\n🌐 COMBINED TOTALS")
        print("=" * 40)
        total = resources["combined_totals"]
        print(f"  Compute Units:    {total['total_compute_units']}")
        print(f"  Total Memory:     {total['total_memory_gb']:.1f} GB")
        print(f"  Total Storage:    {total['total_storage_gb']:.1f} GB")
        print(f"  Effective State:  {total['effective_state_capacity_gb']:.1f} GB")
        print(f"  Expansion Factor: {total['theoretical_expansion_factor']}x")
        print(f"  Total Nodes:      {total['total_nodes']}")
        
        # Conceptual capacity
        print("\n💡 CONCEPTUAL CAPACITY")
        print("-" * 40)
        raw_state = topo['semantic_vectors'] * topo['semantic_dimensions']
        print(f"  Raw State Units:  {raw_state:,}")
        print(f"  Per-Node Average: {raw_state / phys['nodes']:,.0f} units")
        print(f"  With Compression: {raw_state * topo['bind_compression_ratio']:,.0f} units")
        
        print("\n" + "=" * 70)
        
        return resources


def main():
    """Generate combined resource report."""
    calc = CombinedResourceCalculator()
    resources = calc.print_resource_report()
    
    # Save to file
    output_path = Path("/home/allaun/Documents/Research Stack/data/combined_resource_layers.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(resources, f, indent=2)
    
    print(f"Report saved: {output_path}")
    
    return resources


if __name__ == "__main__":
    main()
