"""
Mobile Microgripper (MMG) - Claw-like robotic gripper for cell spheroid bioassembly

Based on: Purdue University research (APL Bioengineering, 2026)
Reference: https://phys.org/news/2026-04-mobile-microgrippers-cells.html

Design:
- Two-arm claw structure connected by hinge
- Magnetic field control (biocompatible)
- Force-sensing with real-time adjustment
- Handles fragile cell spheroids (3D cell clumps)
- Microscopic scale

Integration with Research Stack:
- Buckyball-MOF QCA composite materials
- FAMM frustration physics for assembly control
- Magnetic field steering (MoonRF-adapted phased arrays)
"""

import build123d as bd
import trimesh
import numpy as np
import math
import json
from typing import List, Tuple, Optional

# Microgripper Geometry Parameters (microscopic scale, scaled up for CAD visualization)
SCALE_FACTOR = 1000.0  # Scale from micrometers to millimeters for visualization

ARM_LENGTH = 200.0 / SCALE_FACTOR  # 200 μm arm length
ARM_WIDTH = 30.0 / SCALE_FACTOR    # 30 μm arm width
ARM_THICKNESS = 15.0 / SCALE_FACTOR  # 15 μm arm thickness
HINGE_RADIUS = 10.0 / SCALE_FACTOR  # 10 μm hinge radius
HINGE_WIDTH = 40.0 / SCALE_FACTOR   # 40 μm hinge width
GRIPPER_GAP_OPEN = 100.0 / SCALE_FACTOR  # 100 μm open gap
GRIPPER_GAP_CLOSED = 20.0 / SCALE_FACTOR # 20 μm closed gap

# Magnetic Control Parameters
MAGNETIC_COATING_THICKNESS = 5.0 / SCALE_FACTOR  # 5 μm Fe3O4 coating
MAGNETIC_FIELD_STRENGTH = 1.2  # Tesla (from buckyball-MOF spec)

# Force-Sensing Parameters
SENSOR_THICKNESS = 10.0 / SCALE_FACTOR  # 10 μm piezoresistive sensor
SENSOR_LOCATION = 0.8  # 80% along arm from hinge

class MicrogripperGeometry:
    """Geometry parameters for mobile microgripper."""
    
    def __init__(self):
        self.arm_length = ARM_LENGTH
        self.arm_width = ARM_WIDTH
        self.arm_thickness = ARM_THICKNESS
        self.hinge_radius = HINGE_RADIUS
        self.hinge_width = HINGE_WIDTH
        self.gap_open = GRIPPER_GAP_OPEN
        self.gap_closed = GRIPPER_GAP_CLOSED
        self.magnetic_coating = MAGNETIC_COATING_THICKNESS
        self.sensor_thickness = SENSOR_THICKNESS
        self.sensor_location = SENSOR_LOCATION

def create_arm(geometry: MicrogripperGeometry, angle_offset: float = 0.0) -> list:
    """Create a single gripper arm with hinge and magnetic coating - returns list of shapes."""
    
    shapes = []
    
    # Arm body (rectangular prism)
    arm_body = bd.Box(
        length=geometry.arm_length,
        width=geometry.arm_width,
        height=geometry.arm_thickness
    )
    arm_body = arm_body.move(bd.Location((-geometry.arm_length/2, 0, 0)))
    shapes.append(arm_body)
    
    # Add hinge (cylinder)
    hinge = bd.Cylinder(
        radius=geometry.hinge_radius,
        height=geometry.hinge_width,
        align=bd.Align.CENTER
    )
    hinge = hinge.rotate(axis=bd.Axis((0, 0, 0), (0, 1, 0)), angle=90)
    hinge = hinge.move(bd.Location((0, 0, 0)))
    shapes.append(hinge)
    
    # Add magnetic coating (thin layer on arm surface)
    coating = bd.Box(
        length=geometry.arm_length,
        width=geometry.arm_width,
        height=geometry.magnetic_coating
    )
    coating = coating.move(bd.Location((-geometry.arm_length/2, 0, geometry.arm_thickness/2)))
    shapes.append(coating)
    
    # Add force sensor (piezoresistive strip)
    sensor_length = geometry.arm_length * 0.2
    sensor_x = -geometry.arm_length * geometry.sensor_location
    sensor = bd.Box(
        length=sensor_length,
        width=geometry.arm_width * 0.8,
        height=geometry.sensor_thickness
    )
    sensor = sensor.move(bd.Location((sensor_x, 0, geometry.arm_thickness/2 + geometry.magnetic_coating)))
    shapes.append(sensor)
    
    # Rotate all shapes if angle_offset is specified
    if angle_offset != 0:
        shapes = [s.rotate(axis=bd.Axis((0, 0, 0), (0, 0, 1)), angle=angle_offset) for s in shapes]
    
    return shapes

def create_microgripper(geometry: MicrogripperGeometry, grip_state: str = "open") -> bd.BuildPart:
    """Create complete mobile microgripper with two arms."""
    
    # Calculate arm angles based on grip state
    if grip_state == "open":
        arm_angle = math.degrees(math.atan(geometry.gap_open / (2 * geometry.arm_length)))
    elif grip_state == "closed":
        arm_angle = math.degrees(math.atan(geometry.gap_closed / (2 * geometry.arm_length)))
    else:
        arm_angle = 0.0
    
    with bd.BuildPart() as gripper:
        # Left arm (rotated -arm_angle)
        left_arm_shapes = create_arm(geometry, angle_offset=-arm_angle)
        for shape in left_arm_shapes:
            bd.add(shape)
        
        # Right arm (rotated +arm_angle)
        right_arm_shapes = create_arm(geometry, angle_offset=+arm_angle)
        for shape in right_arm_shapes:
            bd.add(shape)
        
        # Add magnetic control coils (simplified representation)
        # Four coils for phased array steering (MoonRF-adapted)
        coil_radius = 5.0 / SCALE_FACTOR
        coil_positions = [
            (-geometry.arm_length * 0.3, geometry.gap_open/2, geometry.arm_thickness/2 + 5.0/SCALE_FACTOR),
            (-geometry.arm_length * 0.3, -geometry.gap_open/2, geometry.arm_thickness/2 + 5.0/SCALE_FACTOR),
            (geometry.arm_length * 0.3, geometry.gap_open/2, geometry.arm_thickness/2 + 5.0/SCALE_FACTOR),
            (geometry.arm_length * 0.3, -geometry.gap_open/2, geometry.arm_thickness/2 + 5.0/SCALE_FACTOR),
        ]
        
        for pos in coil_positions:
            coil = bd.Cylinder(radius=coil_radius, height=geometry.hinge_width, align=bd.Align.CENTER)
            coil = coil.rotate(axis=bd.Axis((0, 0, 0), (0, 1, 0)), angle=90)
            coil = coil.move(bd.Location(pos))
            bd.add(coil)
    
    return gripper

def gen_part():
    """Generate the Mobile Microgripper CAD model for text-to-cad."""
    
    geometry = MicrogripperGeometry()
    
    # Create microgripper in open state
    gripper = create_microgripper(geometry, grip_state="open")
    
    return gripper

if __name__ == "__main__":
    print("Generating Mobile Microgripper CAD Model...")
    print(f"Scale Factor: {SCALE_FACTOR}x (μm → mm)")
    print(f"Arm Length: {ARM_LENGTH/SCALE_FACTOR:.1f} μm")
    print(f"Arm Width: {ARM_WIDTH/SCALE_FACTOR:.1f} μm")
    print(f"Hinge Radius: {HINGE_RADIUS/SCALE_FACTOR:.1f} μm")
    print(f"Open Gap: {GRIPPER_GAP_OPEN/SCALE_FACTOR:.1f} μm")
    print(f"Closed Gap: {GRIPPER_GAP_CLOSED/SCALE_FACTOR:.1f} μm")
    print(f"Magnetic Coating: {MAGNETIC_COATING_THICKNESS/SCALE_FACTOR:.1f} μm")
    print(f"Sensor Thickness: {SENSOR_THICKNESS/SCALE_FACTOR:.1f} μm")
    
    gripper = gen_part()
    print(f"Created CAD model")
    
    # Export geometry as JSON for physics simulation
    output_json = "/home/allaun/Documents/Research Stack/5-Applications/text-to-cad/models/mobile_microgripper.json"
    
    geometry_data = {
        "type": "mobile_microgripper",
        "scale_factor": SCALE_FACTOR,
        "dimensions": {
            "arm_length_um": ARM_LENGTH,
            "arm_width_um": ARM_WIDTH,
            "arm_thickness_um": ARM_THICKNESS,
            "hinge_radius_um": HINGE_RADIUS,
            "hinge_width_um": HINGE_WIDTH,
            "gap_open_um": GRIPPER_GAP_OPEN,
            "gap_closed_um": GRIPPER_GAP_CLOSED
        },
        "magnetic_control": {
            "coating_thickness_um": MAGNETIC_COATING_THICKNESS,
            "field_strength_tesla": MAGNETIC_FIELD_STRENGTH,
            "coil_count": 4,
            "control_method": "phased_array_magnetic_field"
        },
        "force_sensing": {
            "sensor_thickness_um": SENSOR_THICKNESS,
            "sensor_location_fraction": SENSOR_LOCATION,
            "sensor_type": "piezoresistive"
        },
        "integration": {
            "buckyball_mof_composite": True,
            "famm_frustration_control": True,
            "moonrf_phased_array": True
        },
        "references": [
            "Purdue University APL Bioengineering (2026)",
            "BUCKYBALL_MOF_QCA_SPEC.md",
            "BUCKYBALL_FAMM_TORSIONAL_FLUID.md",
            "ENERGY_EXTRACTION_COMPRESSION_BUCKYBALL.md"
        ]
    }
    
    with open(output_json, 'w') as f:
        json.dump(geometry_data, f, indent=2)
    print(f"Exported geometry JSON to: {output_json}")
    
    print("\nMobile Microgripper CAD model generation complete!")
    print("Note: STEP export requires skill tool. Use: ./.venv/bin/python skills/cad/scripts/gen_step_part models/mobile_microgripper.py")
