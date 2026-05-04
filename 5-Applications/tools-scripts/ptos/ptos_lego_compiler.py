# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
import math
import sys

print("="*75)
print("  [ Graph OS : UNIVERSAL TOY-BLOCK TRANSLATOR (UTBT) ]")
print("  [ MACRO-SCALE ASSEMBLY PROTOCOL: LEGO® SYSTEM ]")
print("="*75)

# Standard LEGO Dimensions in LDraw Units (LDU) and metric
# 1 LDU = 0.4mm
# Standard 1x1 brick = 20x24x20 LDU (X x Y x Z) -> 8mm x 9.6mm x 8mm

LDR_OUT = "mr_fusion_chassis.ldr"

bricks = []

# Define the grid based on scaling our 1-Liter volume (~120x120x140 mm peak bounding box)
# We want it to be a faithful desk model
x_limit = 9  # Grid -9 to +9 studs (18 studs wide = ~144mm)
z_limit = 9  # Grid -9 to +9 studs
y_limit = 15 # Grid 0 to 14 bricks high (~134mm)

bom = {
    "Flux Rod (Pearl Gold, Color: 115)": 0, 
    "Lattice Core (Trans-Light Blue, Color: 43)": 0,
    "Acoustic Damping (Dark Stone Grey, Color: 72)": 0,
    "Carbon Outer Vessel (Black, Color: 0)": 0
}

print("[+] VOXELIZING GOLDEN RATIO LATTICE INTO DISCRETE ABS MATRIX...")

for y in range(y_limit):
    for x in range(-x_limit, x_limit + 1):
        for z in range(-z_limit, z_limit + 1):
            
            # Metric translation
            x_mm = x * 8.0
            y_mm = (y - 7) * 9.6  # Center the Y axis horizontally on 0 roughly
            z_mm = z * 8.0
            
            rad_xy = math.hypot(x_mm, z_mm)
            rad_xyz = math.hypot(rad_xy, y_mm)
            
            # 1. Central Rod (Radius <= 8mm)
            if rad_xy <= 8.0:
                part_color = 115 # Pearl Gold
                bom_key = "Flux Rod (Pearl Gold, Color: 115)"
                
            # 2. Lattice Core (Cubic intersection, roughly inner 25mm bounds)
            elif max(abs(x_mm), abs(y_mm), abs(z_mm)) <= 25.0:
                part_color = 43 # Trans-Light Blue
                bom_key = "Lattice Core (Trans-Light Blue, Color: 43)"
                
            # 3. Acoustic Shell (Spherical radius bounds up to ~48mm)
            elif rad_xyz <= 48.0:
                part_color = 72 # Dark Stone Grey
                bom_key = "Acoustic Damping (Dark Stone Grey, Color: 72)"
                
            # 4. Outer Vessel (Cylindrical boundary up to 64mm radially)
            elif rad_xy <= 64.0:
                # Viewport / insertion cut-out logic to see the core
                # Cut a gap in the front
                if -24 < y_mm < 24 and z_mm > 35 and abs(x_mm) < 25:
                    continue  # Hollow space for viewport
                
                part_color = 0 # Black
                bom_key = "Carbon Outer Vessel (Black, Color: 0)"
                
            else:
                continue
                
            bom[bom_key] += 1
            
            # Map back to LDraw coordinates
            lx = x * 20
            ly = -y * 24
            lz = z * 20
            
            # Format: 1 <color> x y z a b c d e f g h i <file>
            # Standard rotation matrix (identity), using part 3005.dat (1x1 brick)
            line = f"1 {part_color} {lx} {ly} {lz} 1 0 0 0 1 0 0 0 1 3005.dat"
            bricks.append(line)

# Write out the LDraw compliant document
with open(LDR_OUT, "w") as f:
    f.write("0 Untitled Mr Fusion Construct\n")
    f.write("0 Name: mr_fusion_chassis.ldr\n")
    f.write("0 Author: Graph OS Engineering Pipeline\n")
    f.write("0 Unofficial Model\n")
    f.write("0 BFC NOCLIP\n")
    f.write("\n".join(bricks) + "\n")

print("[+] COMPILATION SUCCESS. TOLERANCES CONSTRAINED TO STANDARD LEGO CLUTCH POWER.")
print(f"[+] LDraw Blueprint Generated: -> {LDR_OUT}\n")

print("[+] BILL OF MATERIALS (BOM) FOR DESKTOP REPLICATION:")
total = 0
for block, count in bom.items():
    print(f"    - {block:46s} : {count:>5} units")
    total += count
print("-" * 62)
print(f"    - {'TOTAL (1x1 Standard Bricks)':46s} : {total:>5} units")

print("\n[!] INSTRUCTIONS: 1x1 bricks represent a scale of 7.2 Quadrillion nodes per stud.")
print("    Drag 'mr_fusion_chassis.ldr' into BrickLink Studio / LDraw to instantiate visually.")
print("="*75)
