import csv
import json
import os
from pathlib import Path
import networkx as nx

def build_graph():
    G = nx.DiGraph()
    
    # Load equations from TSV
    tsv_path = Path(__file__).resolve().parent.parent.parent / "3-Mathematical-Models" / "MATH_MODEL_MAP.tsv"
    with open(tsv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            name = row.get("Model_Name", "")
            if not name:
                continue
            
            family = row.get("Family") or "Unknown"
            domain = row.get("Domain_Type") or "Unknown"
            bind = row.get("Bind_Class") or "Unknown"
            
            G.add_node(name, family=family, domain=domain, bind=bind, type="equation")
            
            # Create edges to family and domain
            G.add_edge(name, family, relation="BELONGS_TO_FAMILY")
            G.add_edge(name, domain, relation="BELONGS_TO_DOMAIN")
            G.add_edge(name, bind, relation="HAS_BIND_CLASS")
            
            # Handle Cross_Refs
            cross_refs = row.get("Cross_Refs", "")
            if cross_refs:
                # Assuming comma-separated or space-separated
                refs = [r.strip() for r in cross_refs.replace(',', ' ').split()]
                for ref in refs:
                    if ref:
                        G.add_edge(name, ref, relation="CROSS_REFERENCE")
                        
    # Save as GraphML
    output_dir = "/home/allaun/Documents/Research Stack/artifacts"
    os.makedirs(output_dir, exist_ok=True)
    graphml_path = os.path.join(output_dir, "master_equation_graph.graphml")
    nx.write_graphml(G, graphml_path)
    
    print(f"GraphML saved to {graphml_path} with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
    
    # Try to generate a Mermaid graph (only for major hubs to avoid rendering issues)
    hub_nodes = [n for n, d in G.out_degree() if d > 50] # Top families/domains
    # Let's write a python script to generate Mermaid for top 100 equations or something.
    
if __name__ == "__main__":
    build_graph()
