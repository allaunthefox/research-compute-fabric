"""
Merkle Jack - A 3D tree structure based on the semi_jack geometry search.

This model represents a Merkle tree structure with nodes and struts
in 3D space, optimized for uniform stress distribution.

Based on: /home/allaun/Documents/Research Stack/scratch/exploit_recovery/5-Applications/tools-scripts/semi_jack/
"""

import build123d as bd
import trimesh
import numpy as np
import math
from typing import List, Tuple, Optional

# Geometry parameters from semi_jack search
DEPTH = 4
BRANCHING_FACTOR = 2
BRANCH_ANGLES = [30.0, 25.0, 20.0, 15.0]  # degrees from vertical
AZ_OFFSETS = [0.0, 45.0, 90.0, 135.0]     # azimuthal rotation
TUBULE_RADIUS = 1.5  # mm
HEIGHT_PER_LEVEL = 6.0  # mm

class GNode:
    def __init__(self, id: int, x: float, y: float, z: float, load_frac: float, parent: Optional[int] = None, depth: int = 0):
        self.id = id
        self.x = x
        self.y = y
        self.z = z
        self.load_frac = load_frac
        self.parent = parent
        self.depth = depth

def generate_tree(
    depth: int,
    branch_angles: List[float],
    az_offsets: List[float],
    branching_factor: int,
    height_per_level: float = 6.0,
) -> Tuple[List[GNode], List[Tuple[int, int]]]:
    """Build a rooted tree in 3D using scaled integer matrices to avoid fractional accumulation."""
    # Scale factor for integer math
    Q_SCALE = 65536
    
    nodes = [GNode(id=0, x=0.0, y=0.0, z=0.0, load_frac=1.0, depth=0)]
    edges = []
    node_id = 1
    current_level = [0]
    
    # Pre-calculate integer matrices for branch and azimuth
    h_int = int(height_per_level * Q_SCALE)

    for lv in range(depth):
        angle_deg = branch_angles[min(lv, len(branch_angles)-1)]
        az_base = az_offsets[min(lv, len(az_offsets)-1)]
        
        # Integer scaled rotation components
        cos_branch = int(math.cos(math.radians(angle_deg)) * Q_SCALE)
        sin_branch = int(math.sin(math.radians(angle_deg)) * Q_SCALE)
        
        step_z_int = (h_int * cos_branch) >> 16
        step_r_int = (h_int * sin_branch) >> 16
        
        next_level = []

        for pid in current_level:
            parent = nodes[pid]
            child_frac = parent.load_frac / branching_factor
            
            p_x_int = int(parent.x * Q_SCALE)
            p_y_int = int(parent.y * Q_SCALE)
            p_z_int = int(parent.z * Q_SCALE)

            for k in range(branching_factor):
                az_deg = az_base + k * (360.0 / branching_factor)
                cos_az = int(math.cos(math.radians(az_deg)) * Q_SCALE)
                sin_az = int(math.sin(math.radians(az_deg)) * Q_SCALE)
                
                cx_int = p_x_int + ((step_r_int * cos_az) >> 16)
                cy_int = p_y_int + ((step_r_int * sin_az) >> 16)
                cz_int = p_z_int - step_z_int

                child = GNode(
                    id=node_id,
                    x=float(cx_int) / Q_SCALE, 
                    y=float(cy_int) / Q_SCALE, 
                    z=float(cz_int) / Q_SCALE,
                    load_frac=child_frac,
                    parent=pid,
                    depth=lv+1,
                )
                nodes.append(child)
                edges.append((pid, node_id))
                next_level.append(node_id)
                node_id += 1

        current_level = next_level

    return nodes, edges

def gen_part():
    """Generate the Merkle Jack CAD model for text-to-cad."""
    nodes, edges = generate_tree(
        depth=DEPTH,
        branch_angles=BRANCH_ANGLES,
        az_offsets=AZ_OFFSETS,
        branching_factor=BRANCHING_FACTOR,
        height_per_level=HEIGHT_PER_LEVEL,
    )

    node_map = {n.id: n for n in nodes}
    
    with bd.BuildPart() as jack:
        for p_id, c_id in edges:
            parent = node_map[p_id]
            child = node_map[c_id]
            
            # Calculate edge vector and length
            dx = child.x - parent.x
            dy = child.y - parent.y
            dz = child.z - parent.z
            length = math.sqrt(dx**2 + dy**2 + dz**2)
            
            if length < 1e-9:
                continue
            
            # Create cylinder and position it along the edge
            cylinder = bd.Cylinder(radius=TUBULE_RADIUS, height=length, align=bd.Align.CENTER)
            
            # Calculate rotation to align cylinder with edge
            z_dir = bd.Vector(0, 0, 1)
            edge_vec = bd.Vector(dx, dy, dz).normalized()
            
            # Rotate cylinder to align with edge direction
            cross_prod = z_dir.cross(edge_vec)
            if cross_prod.length > 1e-9:
                rotation_axis = bd.Axis((0, 0, 0), tuple(cross_prod.normalized()))
                rotation_angle = edge_vec.get_angle(z_dir)
                cylinder = cylinder.rotate(axis=rotation_axis, angle=rotation_angle)
            
            # Move cylinder to midpoint of edge
            midpoint = (bd.Vector(parent.x, parent.y, parent.z) + 
                       bd.Vector(child.x, child.y, child.z)) / 2
            cylinder = cylinder.move(bd.Location(midpoint))
    
    return jack

if __name__ == "__main__":
    print("Generating Merkle Jack CAD Model...")
    print(f"Depth: {DEPTH}")
    print(f"Branching Factor: {BRANCHING_FACTOR}")
    print(f"Tubule Radius: {TUBULE_RADIUS} mm")
    print(f"Height per Level: {HEIGHT_PER_LEVEL} mm")
    
    jack = gen_part()
    print(f"Created CAD model with {len(jack.faces())} faces")
    
    # Export as STL using trimesh for physics testing
    output_path = "/home/allaun/Documents/Research Stack/5-Applications/text-to-cad/models/merkle_jack.stl"
    
    # Convert build123d shape to trimesh
    # Use tessellation to get mesh data
    mesh = trimesh.creation.cylinder(radius=TUBULE_RADIUS, height=1.0)
    
    # For now, create a simple representation with cylinders
    # TODO: Properly convert build123d shape to mesh
    mesh.export(output_path)
    print(f"Exported STL file to: {output_path}")
    
    # Also export the tree geometry as JSON for physics simulation
    import json
    output_json = "/home/allaun/Documents/Research Stack/5-Applications/text-to-cad/models/merkle_jack.json"
    nodes, edges = generate_tree(
        depth=DEPTH,
        branch_angles=BRANCH_ANGLES,
        az_offsets=AZ_OFFSETS,
        branching_factor=BRANCHING_FACTOR,
        height_per_level=HEIGHT_PER_LEVEL,
    )
    
    geometry_data = {
        "nodes": [{"id": n.id, "x": n.x, "y": n.y, "z": n.z, "load_frac": n.load_frac, "parent": n.parent, "depth": n.depth} for n in nodes],
        "edges": edges,
        "parameters": {
            "depth": DEPTH,
            "branching_factor": BRANCHING_FACTOR,
            "branch_angles": BRANCH_ANGLES,
            "az_offsets": AZ_OFFSETS,
            "tubule_radius": TUBULE_RADIUS,
            "height_per_level": HEIGHT_PER_LEVEL
        }
    }
    
    with open(output_json, 'w') as f:
        json.dump(geometry_data, f, indent=2)
    print(f"Exported geometry JSON to: {output_json}")
