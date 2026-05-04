import sys
import os
import json
import logging

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from infra.lean_unified_shim import LeanUnifiedShim

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("EnhancedIntegratedSwarm")

class EnhancedIntegratedSwarm:
    """
    Enhanced Integrated Swarm for deep codebase analysis.
    Proper shim: calls Lean bindserver for all logic, no Python logic.
    """
    
    def __init__(self, lean_path="0-Core-Formalism/lean/Semantics"):
        self.shim = LeanUnifiedShim(lean_path)
        
    def perform_deep_analysis(self) -> Dict[str, Any]:
        """
        Perform deep codebase analysis via Lean bindserver.
        All logic is in Lean, this is just a shim for JSON serialization/subprocess.
        """
        logger.info("Enhanced Integrated Swarm: Initiating deep codebase analysis via Lean bindserver...")
        
        result = self.shim.swarm_manifold_analysis()
        
        if "error" in result:
            logger.error(f"Swarm analysis failed: {result['error']}")
            return {"error": result['error']}
        
        logger.info("Swarm analysis complete. Parsing results from Lean...")
        
        try:
            # Parse the JSON result from Lean
            if isinstance(result, str):
                analysis = json.loads(result)
            else:
                analysis = result
            
            logger.info(f"Analysis complete: {len(analysis.get('domains', []))} domains, {len(analysis.get('subdomains', []))} subdomains, {len(analysis.get('tensor_types', []))} tensor types, manifold with {len(analysis.get('manifold', {}).get('nodes', []))} nodes")
            return analysis
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse swarm analysis result: {e}")
            return {"error": f"JSON parse error: {e}"}
    
    def print_analysis(self, analysis: Dict[str, Any]):
        """Print formatted analysis results."""
        if "error" in analysis:
            print(f"ERROR: {analysis['error']}")
            return
        
        print("\n" + "=" * 60)
        print("ENHANCED INTEGRATED SWARM - DEEP CODEBASE ANALYSIS")
        print("=" * 60)
        
        metadata = analysis.get("metadata", {})
        print(f"\nTotal Domains: {metadata.get('total_domains', 'N/A')}")
        print(f"Total Subdomains: {metadata.get('total_subdomains', 'N/A')}")
        print(f"Total Tensor Types: {metadata.get('total_tensor_types', 'N/A')}")
        print(f"Manifold Nodes: {metadata.get('manifold_nodes', 'N/A')}")
        print(f"Manifold Edges: {metadata.get('manifold_edges', 'N/A')}")
        print(f"Manifold Dimension: {metadata.get('manifold_dimension', 'N/A')}")
        print(f"Analysis Timestamp: {metadata.get('analysis_timestamp', 'N/A')}")
        
        print("\n" + "-" * 60)
        print("DOMAINS")
        print("-" * 60)
        for domain in analysis.get("domains", []):
            dim = domain.get("dimensionality", "N/A")
            print(f"  {domain['name']}: {dim}-dim")
            print(f"    {domain['description']}")
        
        print("\n" + "-" * 60)
        print("SUBDOMAINS")
        print("-" * 60)
        for subdomain in analysis.get("subdomains", []):
            print(f"  {subdomain['name']}:")
            categories = subdomain.get("categories", [])
            for cat in categories:
                print(f"    - {cat}")
        
        print("\n" + "-" * 60)
        print("TENSOR TYPES")
        print("-" * 60)
        for tensor in analysis.get("tensor_types", []):
            print(f"  {tensor['name']}: {tensor['description']}")
        
        print("\n" + "-" * 60)
        print("MANIFOLD STRUCTURE")
        print("-" * 60)
        manifold = analysis.get("manifold", {})
        topology = manifold.get("topology", {})
        print(f"  Dimension: {topology.get('dimension', 'N/A')}")
        print(f"  Nodes: {len(manifold.get('nodes', []))}")
        print(f"  Edges: {len(manifold.get('edges', []))}")
        print(f"  Connected Components: {topology.get('connectedComponents', 'N/A')}")
        print(f"  Euler Characteristic: {topology.get('eulerCharacteristic', 'N/A')}")
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    swarm = EnhancedIntegratedSwarm()
    analysis = swarm.perform_deep_analysis()
    swarm.print_analysis(analysis)
