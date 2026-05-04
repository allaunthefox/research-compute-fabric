import json
import os
import networkx as nx
from collections import defaultdict

def build_genome_graph():
    G = nx.Graph()
    
    jsonl_path = "/home/allaun/Documents/Research Stack/data/equations_forest_genome18.jsonl"
    
    # Track addresses and their equations
    address_to_equations = defaultdict(list)
    bin_to_addresses = defaultdict(list)
    
    equations = []
    with open(jsonl_path, 'r') as f:
        for line in f:
            if not line.strip():
                continue
            data = json.loads(line)
            name = data.get("model_name")
            address = data.get("genome18_address")
            bins = data.get("genome18_bins", {})
            
            equations.append(data)
            
            if name and address is not None:
                address_to_equations[address].append(name)
                
                # Add Equation node
                G.add_node(name, type="equation", address=address, **bins)
                
                # Add Address node
                address_node = f"Addr_{address}"
                if not G.has_node(address_node):
                    G.add_node(address_node, type="address_hub", address=address, **bins)
                    
                # Link Equation to Address
                G.add_edge(name, address_node, type="encoded_at")

    # Connect addresses that are 'adjacent' (only 1 bin differs by 1)
    addresses = list(address_to_equations.keys())
    addr_to_bins = {}
    for eq in equations:
        addr = eq.get("genome18_address")
        if addr not in addr_to_bins:
            addr_to_bins[addr] = eq.get("genome18_bins", {})

    for i in range(len(addresses)):
        for j in range(i + 1, len(addresses)):
            addr1 = addresses[i]
            addr2 = addresses[j]
            b1 = addr_to_bins[addr1]
            b2 = addr_to_bins[addr2]
            
            # Calculate distance
            diff = 0
            for k in ["muBin", "rhoBin", "cBin", "mBin", "neBin", "sigmaBin"]:
                diff += abs(b1.get(k, 0) - b2.get(k, 0))
            
            # If distance is exactly 1, link them
            if diff == 1:
                G.add_edge(f"Addr_{addr1}", f"Addr_{addr2}", type="topological_adjacent")

    # Save GraphML
    output_dir = "/home/allaun/Documents/Research Stack/artifacts"
    os.makedirs(output_dir, exist_ok=True)
    graphml_path = os.path.join(output_dir, "genome18_complete.graphml")
    nx.write_graphml(G, graphml_path)
    print(f"Saved complete GraphML to {graphml_path} ({G.number_of_nodes()} nodes, {G.number_of_edges()} edges)")
    
    # Generate Hubs Mermaid Chart
    # Find addresses with the most equations
    sorted_addresses = sorted(address_to_equations.items(), key=lambda x: len(x[1]), reverse=True)
    top_addresses = sorted_addresses[:15] # Top 15 hubs
    
    mermaid_lines = ["graph TD", "  %% Sovereign Research Stack - Genomic Hubs"]
    
    for addr, eq_list in top_addresses:
        addr_node = f"Addr_{addr}"
        mermaid_lines.append(f"  {addr_node}((Address {addr}))")
        
        # Add up to 5 equations for this hub to avoid clutter
        for eq in eq_list[:5]:
            safe_eq = eq.replace(' ', '_').replace('-', '_').replace('+', '_')
            mermaid_lines.append(f"  {safe_eq}[{eq}] --> {addr_node}")
            
        if len(eq_list) > 5:
            mermaid_lines.append(f"  {addr_node}_more(>...and {len(eq_list)-5} more) -.-> {addr_node}")

    # Add "Tree Fiddy" and "PIST" specifically if they aren't in the top 15
    special_equations = ["Tree Fiddy", "PIST_Neural_Topology", "Bridge_PIST_Surface"]
    for eq_data in equations:
        name = eq_data.get("model_name")
        if name and any(s in name for s in special_equations):
            addr = eq_data.get("genome18_address")
            addr_node = f"Addr_{addr}"
            safe_name = name.replace(' ', '_').replace('-', '_').replace('+', '_')
            mermaid_lines.append(f"  {safe_name}[{name}] --> {addr_node}")
            mermaid_lines.append(f"  style {safe_name} fill:#f9f,stroke:#333,stroke-width:4px")
            
    mermaid_path = os.path.join(output_dir, "genome18_hubs.mermaid")
    with open(mermaid_path, "w") as f:
        f.write("\n".join(mermaid_lines))
        
    print(f"Saved hubs Mermaid chart to {mermaid_path}")

if __name__ == "__main__":
    build_genome_graph()
