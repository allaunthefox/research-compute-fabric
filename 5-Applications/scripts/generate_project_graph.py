import csv
import xml.etree.ElementTree as ET
import sys

def generate_graphs(tsv_path):
    nodes = {}
    edges = []
    
    with open(tsv_path, 'r', encoding='utf-8') as f:
        # Skip potential comment lines at start
        lines = f.readlines()
        start_idx = 0
        for i, line in enumerate(lines):
            if line.startswith('1\t') or line.startswith('#\t'):
                start_idx = i
                break
        
        reader = csv.DictReader(lines[start_idx:], delimiter='\t')
        
        # Normalize field names (sometimes they have # or leading/trailing space)
        fieldnames = [fn.strip().replace('#', 'ID') for fn in reader.fieldnames]
        
        for row in reader:
            # Re-map row to clean keys
            clean_row = {fn.strip().replace('#', 'ID'): v for fn, v in zip(reader.fieldnames, row.values())}
            
            node_id = clean_row.get('ID')
            if not node_id: continue
            
            name = clean_row.get('Model_Name', f"Model_{node_id}")
            family = clean_row.get('Family', 'Uncategorized')
            domain = clean_row.get('Domain_Type', 'Default')
            
            nodes[node_id] = {
                'name': name,
                'family': family,
                'domain': domain,
                'equation': clean_row.get('Equation', ''),
                'status': clean_row.get('Status', '')
            }
            
            cross_refs = clean_row.get('Cross_Refs', '')
            if cross_refs and cross_refs != '-':
                refs = [r.strip() for r in cross_refs.split(',') if r.strip().isdigit()]
                for ref in refs:
                    edges.append((node_id, ref))

    # 1. Generate Mermaid
    mermaid_content = "graph TD\n"
    # Group by domain
    domains = {}
    for nid, data in nodes.items():
        dom = data['domain']
        if dom not in domains: domains[dom] = []
        domains[dom].append(nid)
    
    for dom, nids in domains.items():
        if dom == 'Default': continue
        mermaid_content += f"  subgraph {dom.replace('_', ' ')}\n"
        for nid in nids:
            # Clean label for mermaid
            label = nodes[nid]['name'].replace(' ', '_').replace('(', '').replace(')', '')
            mermaid_content += f"    N{nid}[{label}]\n"
        mermaid_content += "  end\n"
    
    for src, dst in edges:
        if src in nodes and dst in nodes:
            mermaid_content += f"  N{src} --> N{dst}\n"
            
    with open('research_graph.mermaid', 'w') as f:
        f.write(mermaid_content)

    # 2. Generate GraphML
    graphml = ET.Element('graphml', {
        'xmlns': "http://graphml.graphdrawing.org/xmlns",
        'xmlns:xsi': "http://www.w3.org/2001/XMLSchema-instance",
        'xsi:schemaLocation': "http://graphml.graphdrawing.org/xmlns http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd"
    })
    
    # Define keys
    key_name = ET.SubElement(graphml, 'key', {'id': 'd0', 'for': 'node', 'attr.name': 'name', 'attr.type': 'string'})
    key_family = ET.SubElement(graphml, 'key', {'id': 'd1', 'for': 'node', 'attr.name': 'family', 'attr.type': 'string'})
    key_domain = ET.SubElement(graphml, 'key', {'id': 'd2', 'for': 'node', 'attr.name': 'domain', 'attr.type': 'string'})
    
    graph = ET.SubElement(graphml, 'graph', {'id': 'G', 'edgedefault': 'directed'})
    
    for nid, data in nodes.items():
        node = ET.SubElement(graph, 'node', {'id': f"n{nid}"})
        ET.SubElement(node, 'data', {'key': 'd0'}).text = data['name']
        ET.SubElement(node, 'data', {'key': 'd1'}).text = data['family']
        ET.SubElement(node, 'data', {'key': 'd2'}).text = data['domain']
        
    for i, (src, dst) in enumerate(edges):
        if src in nodes and dst in nodes:
            ET.SubElement(graph, 'edge', {
                'id': f"e{i}",
                'source': f"n{src}",
                'target': f"n{dst}"
            })
            
    tree = ET.ElementTree(graphml)
    tree.write('research_graph.graphml', encoding='utf-8', xml_declaration=True)

    # 3. Generate simplified Mermaid (Top nodes by degree)
    # Count connections
    degree = {nid: 0 for nid in nodes}
    for src, dst in edges:
        if src in degree: degree[src] += 1
        if dst in degree: degree[dst] += 1
    
    top_nodes = sorted(degree.items(), key=lambda x: x[1], reverse=True)[:50]
    top_ids = [nid for nid, deg in top_nodes]
    
    simp_mermaid = "graph TD\n"
    for nid in top_ids:
        label = nodes[nid]['name'].replace(' ', '_')
        simp_mermaid += f"  N{nid}[{label}]\n"
    
    for src, dst in edges:
        if src in top_ids and dst in top_ids:
            simp_mermaid += f"  N{src} --> N{dst}\n"
            
    with open('research_graph_summary.mermaid', 'w') as f:
        f.write(simp_mermaid)

    print(f"✅ Generated graphs for {len(nodes)} nodes and {len(edges)} edges.")

if __name__ == "__main__":
    import os
    base_path = "/home/allaun/Documents/Research Stack"
    tsv_path = os.path.join(base_path, "3-Mathematical-Models", "MATH_MODEL_MAP.tsv")
    generate_graphs(tsv_path)
