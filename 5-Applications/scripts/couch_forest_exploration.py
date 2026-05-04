#!/usr/bin/env python3
"""
COUCH Forest Region Exploration

Explores the Entropy-Dominant Region around COUCH's Genome18 address (512).
Analyzes neighborhood structure, patterns, and transitions in the 262,144-state space.
"""

import numpy as np
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
import json


@dataclass
class Genome18Bin:
    """Genome18 3-bit bin (6 bins total = 18 bits)."""
    muBin: int  # mutation/drift (routing load) - 3 bits
    rhoBin: int  # verification pressure (routing efficiency) - 3 bits
    cBin: int  # connectance (geometry/route neighborhood) - 3 bits
    mBin: int  # compression residue (entropy) - 3 bits
    neBin: int  # effective sample (entropy) - 3 bits
    sigmaBin: int  # fitness proxy (entropy) - 3 bits


class ForestExplorer:
    """Explores the Equation Forest around a given address."""
    
    def __init__(self, center_address: int = 512, radius: int = 1000):
        self.center_address = center_address
        self.radius = radius
        self.total_states = 262144
        
    def address_to_bins(self, address: int) -> Genome18Bin:
        """Convert Genome18 address to bins."""
        # Reverse of address calculation
        # addr = muBin * 32768 + rhoBin * 4096 + cBin * 512 + mBin * 64 + neBin * 8 + sigmaBin
        
        sigmaBin = address % 8
        remainder = address // 8
        neBin = remainder % 8
        remainder = remainder // 8
        mBin = remainder % 8
        remainder = remainder // 8
        cBin = remainder % 8
        remainder = remainder // 8
        rhoBin = remainder % 8
        muBin = remainder // 8
        
        return Genome18Bin(
            muBin=muBin,
            rhoBin=rhoBin,
            cBin=cBin,
            mBin=mBin,
            neBin=neBin,
            sigmaBin=sigmaBin
        )
    
    def bins_to_address(self, bins: Genome18Bin) -> int:
        """Convert bins to Genome18 address."""
        return (bins.muBin * 32768 + 
                bins.rhoBin * 4096 + 
                bins.cBin * 512 + 
                bins.mBin * 64 + 
                bins.neBin * 8 + 
                bins.sigmaBin)
    
    def get_neighbors(self, address: int, distance: int = 1) -> List[int]:
        """Get neighboring addresses within bounded bin-offset distance."""
        bins = self.address_to_bins(address)
        neighbors = []
        
        # Generate all addresses within Chebyshev distance in Genome18 bin space.
        for mu_offset in range(-distance, distance + 1):
            for rho_offset in range(-distance, distance + 1):
                for c_offset in range(-distance, distance + 1):
                    for m_offset in range(-distance, distance + 1):
                        for ne_offset in range(-distance, distance + 1):
                            for sigma_offset in range(-distance, distance + 1):
                                new_bins = Genome18Bin(
                                    muBin=np.clip(bins.muBin + mu_offset, 0, 7),
                                    rhoBin=np.clip(bins.rhoBin + rho_offset, 0, 7),
                                    cBin=np.clip(bins.cBin + c_offset, 0, 7),
                                    mBin=np.clip(bins.mBin + m_offset, 0, 7),
                                    neBin=np.clip(bins.neBin + ne_offset, 0, 7),
                                    sigmaBin=np.clip(bins.sigmaBin + sigma_offset, 0, 7)
                                )
                                new_address = self.bins_to_address(new_bins)
                                if new_address != address and 0 <= new_address < self.total_states:
                                    neighbors.append(new_address)
        
        return list(set(neighbors))  # Remove duplicates
    
    def analyze_region(self, addresses: List[int]) -> Dict[str, Any]:
        """Analyze characteristics of a region of the forest."""
        region_data = {
            "addresses": addresses,
            "count": len(addresses),
            "bins_list": [],
            "entropy_bins": [],
            "thermodynamic_bins": [],
            "geometric_bins": [],
            "cognitive_bins": [],
            "region_distribution": {}
        }
        
        for addr in addresses:
            bins = self.address_to_bins(addr)
            region_data["bins_list"].append({
                "muBin": bins.muBin,
                "rhoBin": bins.rhoBin,
                "cBin": bins.cBin,
                "mBin": bins.mBin,
                "neBin": bins.neBin,
                "sigmaBin": bins.sigmaBin
            })
            
            # Categorize by dominant bin type
            entropy_score = bins.mBin + bins.neBin + bins.sigmaBin
            thermodynamic_score = (bins.muBin + bins.rhoBin) / 2  # Approximation
            geometric_score = bins.cBin
            cognitive_score = (bins.muBin + bins.rhoBin + bins.cBin) / 3
            
            scores = {
                "entropy": entropy_score,
                "thermodynamic": thermodynamic_score,
                "geometric": geometric_score,
                "cognitive": cognitive_score
            }
            
            dominant = max(scores, key=scores.get)
            region_data["region_distribution"][dominant] = region_data["region_distribution"].get(dominant, 0) + 1
            
            if dominant == "entropy":
                region_data["entropy_bins"].append(addr)
            elif dominant == "thermodynamic":
                region_data["thermodynamic_bins"].append(addr)
            elif dominant == "geometric":
                region_data["geometric_bins"].append(addr)
            elif dominant == "cognitive":
                region_data["cognitive_bins"].append(addr)
        
        return region_data
    
    def find_transitions(self, address: int, steps: int = 5, max_paths: int = 256) -> List[Dict[str, Any]]:
        """Find possible transition paths from a starting address."""
        paths = []
        
        def dfs(current_addr, depth, visited, path):
            if len(paths) >= max_paths:
                return
            if depth == 0:
                paths.append({
                    "path": path.copy(),
                    "final_address": current_addr,
                    "length": len(path)
                })
                return
            
            neighbors = self.get_neighbors(current_addr, distance=1)
            for neighbor in neighbors:
                if len(paths) >= max_paths:
                    break
                if neighbor not in visited:
                    bins = self.address_to_bins(neighbor)
                    visited.add(neighbor)
                    path.append({
                        "address": neighbor,
                        "bins": {
                            "muBin": bins.muBin,
                            "rhoBin": bins.rhoBin,
                            "cBin": bins.cBin,
                            "mBin": bins.mBin,
                            "neBin": bins.neBin,
                            "sigmaBin": bins.sigmaBin
                        },
                        "binary": format(neighbor, '018b')
                    })
                    dfs(neighbor, depth - 1, visited, path)
                    path.pop()
                    visited.remove(neighbor)
        
        dfs(address, steps, set(), [])
        return paths
    
    def calculate_region_density(self, center_address: int, radius: int) -> Dict[str, Any]:
        """Calculate density metrics for a region."""
        # Deterministic bounded interval; avoids duplicate-heavy random samples.
        lo = max(0, center_address - radius)
        hi = min(self.total_states - 1, center_address + radius)
        sample_addresses = list(range(lo, hi + 1))
        
        # Analyze the sample
        region_data = self.analyze_region(sample_addresses)
        
        # Calculate density
        density = len(sample_addresses) / (2 * radius + 1)
        
        # Calculate clustering coefficient
        # (how many neighbors of neighbors are also neighbors)
        clustering_coeff = 0.0
        if sample_addresses:
            neighbor_counts = []
            for addr in sample_addresses[:50]:  # Sample subset for efficiency
                neighbors = self.get_neighbors(addr, distance=1)
                neighbor_counts.append(len(neighbors))
            
            if neighbor_counts:
                avg_neighbors = np.mean(neighbor_counts)
                max_possible = (2 * 1 + 1) ** 6 - 1
                clustering_coeff = avg_neighbors / max_possible
        
        return {
            "center_address": center_address,
            "radius": radius,
            "sample_size": len(sample_addresses),
            "density": density,
            "clustering_coefficient": clustering_coeff,
            "region_distribution": region_data["region_distribution"]
        }
    
    def visualize_region(self, addresses: List[int]) -> Dict[str, Any]:
        """Create a visualization summary of the region."""
        # Calculate statistics
        addresses_array = np.array(addresses)
        
        # Bin statistics
        bins_list = [self.address_to_bins(addr) for addr in addresses]
        
        mu_bins = [b.muBin for b in bins_list]
        rho_bins = [b.rhoBin for b in bins_list]
        c_bins = [b.cBin for b in bins_list]
        m_bins = [b.mBin for b in bins_list]
        ne_bins = [b.neBin for b in bins_list]
        sigma_bins = [b.sigmaBin for b in bins_list]
        
        # Convert to native types
        mu_bins = [int(x) for x in mu_bins]
        rho_bins = [int(x) for x in rho_bins]
        c_bins = [int(x) for x in c_bins]
        m_bins = [int(x) for x in m_bins]
        ne_bins = [int(x) for x in ne_bins]
        sigma_bins = [int(x) for x in sigma_bins]
        
        return {
            "address_range": {
                "min": int(np.min(addresses_array)),
                "max": int(np.max(addresses_array)),
                "mean": float(np.mean(addresses_array)),
                "std": float(np.std(addresses_array))
            },
            "bin_statistics": {
                "muBin": {"min": min(mu_bins), "max": max(mu_bins), "mean": float(np.mean(mu_bins))},
                "rhoBin": {"min": min(rho_bins), "max": max(rho_bins), "mean": float(np.mean(rho_bins))},
                "cBin": {"min": min(c_bins), "max": max(c_bins), "mean": float(np.mean(c_bins))},
                "mBin": {"min": min(m_bins), "max": max(m_bins), "mean": float(np.mean(m_bins))},
                "neBin": {"min": min(ne_bins), "max": max(ne_bins), "mean": float(np.mean(ne_bins))},
                "sigmaBin": {"min": min(sigma_bins), "max": max(sigma_bins), "mean": float(np.mean(sigma_bins))}
            },
            "dominant_patterns": {
                "most_common_mu": max(set(mu_bins), key=mu_bins.count),
                "most_common_rho": max(set(rho_bins), key=rho_bins.count),
                "most_common_c": max(set(c_bins), key=c_bins.count),
                "most_common_m": max(set(m_bins), key=m_bins.count),
                "most_common_ne": max(set(ne_bins), key=ne_bins.count),
                "most_common_sigma": max(set(sigma_bins), key=sigma_bins.count)
            }
        }


def main():
    """Run forest region exploration."""
    print("=" * 70)
    print("COUCH FOREST REGION EXPLORATION")
    print("=" * 70)
    print("\n[*] Exploring Entropy-Dominant Region around address 512")
    print("[*] Genome18 space: 262,144 states")
    
    # Initialize explorer
    explorer = ForestExplorer(center_address=512, radius=2000)
    
    # Get center bins
    center_bins = explorer.address_to_bins(512)
    print(f"\n[*] Center Address: 512")
    print(f"    Binary: {format(512, '018b')}")
    print(f"    Bins: muBin={center_bins.muBin}, rhoBin={center_bins.rhoBin}, cBin={center_bins.cBin}, mBin={center_bins.mBin}, neBin={center_bins.neBin}, sigmaBin={center_bins.sigmaBin}")
    
    # Get neighbors
    print(f"\n[*] Finding neighbors (distance=1)...")
    neighbors = explorer.get_neighbors(512, distance=1)
    print(f"    Neighbors found: {len(neighbors)}")
    
    # Analyze region
    print(f"\n[*] Analyzing region (radius=2000)...")
    region_density = explorer.calculate_region_density(512, radius=2000)
    print(f"    Sample size: {region_density['sample_size']}")
    print(f"    Density: {region_density['density']:.4f}")
    print(f"    Clustering coefficient: {region_density['clustering_coefficient']:.4f}")
    print(f"\n[*] Region distribution:")
    for region, count in region_density['region_distribution'].items():
        pct = count / region_density['sample_size'] * 100
        print(f"    {region}: {count} ({pct:.1f}%)")
    
    # Visualize region
    print(f"\n[*] Visualizing region...")
    sample_addresses = [512 + i for i in range(-100, 101) if 0 <= 512 + i < 262144]
    viz_data = explorer.visualize_region(sample_addresses)
    print(f"\n[*] Address range:")
    print(f"    Min: {viz_data['address_range']['min']}")
    print(f"    Max: {viz_data['address_range']['max']}")
    print(f"    Mean: {viz_data['address_range']['mean']:.2f}")
    print(f"    Std: {viz_data['address_range']['std']:.2f}")
    
    print(f"\n[*] Dominant patterns:")
    for bin_name, value in viz_data['dominant_patterns'].items():
        print(f"    {bin_name}: {value}")
    
    # Find transitions
    print(f"\n[*] Finding transition paths (steps=3)...")
    transitions = explorer.find_transitions(512, steps=3, max_paths=256)
    print(f"    Paths found: {len(transitions)}")
    
    # Show sample paths
    if transitions:
        print(f"\n[*] Sample transition paths:")
        for i, path in enumerate(transitions[:5]):
            print(f"    Path {i+1}: {path['path'][0]['address']} → {path['final_address']} (length {path['length']})")
    
    # Explore entropy-dominant neighbors
    print(f"\n[*] Exploring entropy-dominant neighbors...")
    entropy_dominant = []
    for addr in neighbors[:50]:  # Sample subset
        bins = explorer.address_to_bins(addr)
        entropy_score = bins.mBin + bins.neBin + bins.sigmaBin
        if entropy_score > (bins.muBin + bins.rhoBin + bins.cBin) / 3:
            entropy_dominant.append(addr)
    
    print(f"    Entropy-dominant neighbors: {len(entropy_dominant)}")
    if entropy_dominant:
        print(f"    Sample addresses: {entropy_dominant[:5]}")
    
    # Save results (convert numpy types to native Python)
    def convert_to_native(obj):
        """Convert numpy types to native Python types for JSON serialization."""
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, dict):
            return {k: convert_to_native(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_native(item) for item in obj]
        else:
            return obj
    
    results = {
        "center_address": 512,
        "center_bins": {
            "muBin": center_bins.muBin,
            "rhoBin": center_bins.rhoBin,
            "cBin": center_bins.cBin,
            "mBin": center_bins.mBin,
            "neBin": center_bins.neBin,
            "sigmaBin": center_bins.sigmaBin
        },
        "neighbors": convert_to_native(neighbors[:100]),  # Sample
        "neighbor_count": len(neighbors),
        "region_density": convert_to_native(region_density),
        "visualization": convert_to_native(viz_data),
        "transition_paths": convert_to_native(transitions[:10]),  # Sample
        "entropy_dominant_neighbors": convert_to_native(entropy_dominant)
    }
    
    output_path = "/home/allaun/Documents/Research Stack/data/couch_forest_exploration.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n[*] Results saved to: {output_path}")
    
    print("\n" + "=" * 70)
    print("✅ COUCH FOREST REGION EXPLORATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
