import csv
import math

class DAGBuilder:
    def __init__(self):
        self.nodes = {}
        self.edges = []
        self.counter = 0

    def add_node(self, label, description=""):
        node_id = f"N{self.counter}"
        self.nodes[node_id] = f"{label}<br/><i>{description}</i>"
        self.counter += 1
        return node_id

    def add_edge(self, from_id, to_id, label=""):
        self.edges.append((from_id, to_id, label))

    def to_mermaid(self):
        lines = ["graph TD"]
        for nid, label in self.nodes.items():
            lines.append(f"    {nid}[\"{label}\"]")
        for frm, to, lbl in self.edges:
            if lbl:
                lines.append(f"    {frm} -- \"{lbl}\" --> {to}")
            else:
                lines.append(f"    {frm} --> {to}")
        return "\n".join(lines)

def load_atomic_weights(dag):
    node_load = dag.add_node("Load IUPAC Standard", "Read shared-data/data/atomic_weights.csv")
    weights = {}
    with open('shared-data/data/atomic_weights.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_w = row['AtomicWeight'].strip()
            if not raw_w: continue
            
            # 1. Handle Intervals [min, max] by taking the midpoint
            if raw_w.startswith('['):
                parts = raw_w.strip('[]').split(',')
                w = (float(parts[0].strip()) + float(parts[1].strip())) / 2.0
            else:
                # 2. Handle Uncertainty (x) or Mass Number (n) like (98) or 4.002602(2)
                # Strategy: strip parentheses and any non-numeric/non-decimal characters
                # but keep the content inside if it's just a number
                clean_w = raw_w.replace('(', '').replace(')', '').strip()
                # If uncertainty was 4.002602(2), clean_w is 4.0026022 - WRONG.
                # Correct Strategy: split at '(' only if there is something BEFORE it.
                if '(' in raw_w:
                    prefix = raw_w.split('(')[0].strip()
                    if prefix:
                        w = float(prefix)
                    else:
                        # Case like (98)
                        w = float(raw_w.strip('()'))
                else:
                    w = float(raw_w)
                
            weights[row['Symbol']] = w
    
    node_h = dag.add_node("Extract H", f"Mean Weight: {weights['H']:.5f}")
    node_c = dag.add_node("Extract C", f"Mean Weight: {weights['C']:.5f}")
    node_o = dag.add_node("Extract O", f"Mean Weight: {weights['O']:.5f}")
    node_n = dag.add_node("Extract N", f"Mean Weight: {weights['N']:.5f}")
    node_p = dag.add_node("Extract P", f"Mean Weight: {weights['P']:.5f}")
    
    dag.add_edge(node_load, node_h)
    dag.add_edge(node_load, node_c)
    dag.add_edge(node_load, node_o)
    dag.add_edge(node_load, node_n)
    dag.add_edge(node_load, node_p)
    
    return weights, {"H": node_h, "C": node_c, "O": node_o, "N": node_n, "P": node_p}

def verify_h2o(dag, weight_nodes):
    root = dag.add_node("H2O Composition Schema", "Intent: First-Principles Water")
    dag.add_edge(weight_nodes['H'], root)
    dag.add_edge(weight_nodes['O'], root)
    node_geom = dag.add_node("Proposed Geometry Search", "Conceptual Sweep Angle 90-120")
    dag.add_edge(root, node_geom)
    node_coulomb = dag.add_node("Coulombic Term (Assumption)", "q=0.41, r_HH")
    node_vdw = dag.add_node("Pauli/VdW Term (Assumption)", "1/r^12")
    node_ammr = dag.add_node("AMMR Phase-Gate (Constraint)", "Golden Ratio scaling")
    dag.add_edge(node_geom, node_coulomb)
    dag.add_edge(node_geom, node_vdw)
    dag.add_edge(node_geom, node_ammr)
    node_energy = dag.add_node("Theoretical Manifold Energy", "Target Functional Sum")
    dag.add_edge(node_coulomb, node_energy)
    dag.add_edge(node_vdw, node_energy)
    dag.add_edge(node_ammr, node_energy)
    node_opt = dag.add_node("Optimization Logic (Pending)", "Minimization via AMMR")
    dag.add_edge(node_energy, node_opt)
    node_result = dag.add_node("Expected Result: H2O", "Reference Angle: 104.5 degrees")
    dag.add_edge(node_opt, node_result)

def verify_co2(dag, weight_nodes):
    root = dag.add_node("CO2 Composition Schema", "Intent: First-Principles Carbon Dioxide")
    dag.add_edge(weight_nodes['C'], root)
    dag.add_edge(weight_nodes['O'], root)
    node_geom = dag.add_node("Proposed Geometry Search", "Conceptual Sweep Angle 100-180")
    dag.add_edge(root, node_geom)
    node_coulomb = dag.add_node("Coulombic Term (Assumption)", "O-O Repulsion")
    node_ammr = dag.add_node("AMMR sp Hybridization", "Linear phase-lock")
    dag.add_edge(node_geom, node_coulomb)
    dag.add_edge(node_geom, node_ammr)
    node_energy = dag.add_node("Theoretical Manifold Energy", "Target Functional Sum")
    dag.add_edge(node_coulomb, node_energy)
    dag.add_edge(node_ammr, node_energy)
    node_opt = dag.add_node("Optimization Logic (Pending)", "Minimization via AMMR")
    dag.add_edge(node_energy, node_opt)
    node_result = dag.add_node("Expected Result: CO2", "Reference Angle: 180.00 degrees")
    dag.add_edge(node_opt, node_result)

def verify_ch4(dag, weight_nodes):
    root = dag.add_node("CH4 Composition Schema", "Intent: First-Principles Methane")
    dag.add_edge(weight_nodes['C'], root)
    dag.add_edge(weight_nodes['H'], root)
    node_geom = dag.add_node("Proposed Geometry Search", "Conceptual Tetrahedral sweep")
    dag.add_edge(root, node_geom)
    node_coulomb = dag.add_node("Coulombic Term (Assumption)", "H-H Repulsion")
    node_ammr = dag.add_node("AMMR sp3 Hybridization", "Phi-neutral symmetry")
    dag.add_edge(node_geom, node_coulomb)
    dag.add_edge(node_geom, node_ammr)
    node_energy = dag.add_node("Theoretical Manifold Energy", "Target Functional Sum")
    dag.add_edge(node_coulomb, node_energy)
    dag.add_edge(node_ammr, node_energy)
    node_opt = dag.add_node("Optimization Logic (Pending)", "Minimization via AMMR")
    dag.add_edge(node_energy, node_opt)
    node_result = dag.add_node("Expected Result: CH4", "Reference Angle: 109.47 degrees")
    dag.add_edge(node_opt, node_result)

def verify_dna(dag, weight_nodes):
    root = dag.add_node("DNA Strand Schema", "Intent: B-DNA Assembly")
    dag.add_edge(weight_nodes['P'], root)
    dag.add_edge(weight_nodes['O'], root)
    dag.add_edge(weight_nodes['C'], root)
    dag.add_edge(weight_nodes['N'], root)
    dag.add_edge(weight_nodes['H'], root)
    node_bases = dag.add_node("Nucleotide Bases (Proposed)", "A, T, C, G resonance")
    dag.add_edge(root, node_bases)
    node_pairing = dag.add_node("Watson-Crick Pairing (Proposed)", "Hydrogen Bond resonance")
    dag.add_edge(node_bases, node_pairing)
    node_backbone = dag.add_node("Backbone Model (Proposed)", "Sugar-Phosphate chain")
    dag.add_edge(root, node_backbone)
    node_pitch = dag.add_node("Helical Torsion (Proposed)", "3.4nm pitch model")
    node_phi = dag.add_node("Phi-Manifold (Proposed Constraint)", "Golden Ratio groove ratio")
    dag.add_edge(node_pairing, node_pitch)
    dag.add_edge(node_backbone, node_pitch)
    dag.add_edge(node_pitch, node_phi)
    node_energy = dag.add_node("Theoretical Manifold Stability", "Target Functional Sum")
    dag.add_edge(node_phi, node_energy)
    node_opt = dag.add_node("Optimization Logic (Pending)", "Global minimum search")
    dag.add_edge(node_energy, node_opt)
    node_result = dag.add_node("Expected Result: B-DNA", "Reference: 10.5 bp/turn")
    dag.add_edge(node_opt, node_result)

def main():
    dag = DAGBuilder()
    weights, weight_nodes = load_atomic_weights(dag)
    verify_h2o(dag, weight_nodes)
    verify_co2(dag, weight_nodes)
    verify_ch4(dag, weight_nodes)
    verify_dna(dag, weight_nodes)
    with open('6-Documentation/docs/FIRST_PRINCIPLES_DAG.md', 'w') as f:
        f.write("# First Principles Molecular Derivation: Architectural Intent Map\n\n")
        f.write("**Status:** CONCEPTUAL — This DAG maps the intended first-principles derivation path. It identifies the provenance of atomic weights and the required manifold constraints. It does NOT yet execute these calculations.\n\n")
        f.write("```mermaid\n")
        f.write(dag.to_mermaid())
        f.write("\n```\n")

if __name__ == '__main__':
    main()
