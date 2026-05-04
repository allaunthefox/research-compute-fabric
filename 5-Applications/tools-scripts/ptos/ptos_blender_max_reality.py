# ==============================================================================
# COPYRIGHT NO ONE EVERYWHERE LLC (WYOMING HOLDING COMPANY)
# PROJECT: SOVEREIGN STACK
# This artifact is entirely proprietary and cryptographically proven.
# Open-Source usage requires explicit permission from Brandon Scott Schneider.
# ==============================================================================
import bpy
import math
import os
from pathlib import Path

REPO_ROOT = Path(os.getenv("RESEARCH_STACK_ROOT") or Path(__file__).resolve().parents[1])

def setup_maximum_reality():
    # Clear existing scene
    bpy.ops.wm.read_factory_settings(use_empty=True)
    
    # ------------------------------------------------------------------
    # [ RENDER ENGINE: CYCLES (GPU Accelerated, Max Reality) ]
    # ------------------------------------------------------------------
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'GPU'
    scene.cycles.samples = 1024
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 3840
    scene.render.resolution_y = 2160
    scene.render.resolution_percentage = 100
    
    # ------------------------------------------------------------------
    # [ MATERIAL SHADERS (PBR) ]
    # ------------------------------------------------------------------
    def create_pbr_material(name, color, metallic, roughness, transmission=0.0):
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get('Principled BSDF')
        bsdf.inputs['Base Color'].default_value = color
        bsdf.inputs['Metallic'].default_value = metallic
        bsdf.inputs['Roughness'].default_value = roughness
        if transmission > 0.0:
            bsdf.inputs['Transmission Weight'].default_value = transmission
            bsdf.inputs['IOR'].default_value = 1.45
        return mat

    mat_rust = create_pbr_material("Rusty_Iron", (0.2, 0.07, 0.03, 1), 0.8, 0.9)
    mat_copper = create_pbr_material("Dirty_Copper", (0.7, 0.3, 0.1, 1), 1.0, 0.6)
    mat_lego = create_pbr_material("Faded_ABS", (0.6, 0.1, 0.1, 1), 0.0, 0.4)
    mat_glass = create_pbr_material("Jar_Glass", (0.9, 0.95, 1.0, 1), 0.1, 0.05, transmission=1.0)
    mat_water = create_pbr_material("Dirty_Water", (0.6, 0.5, 0.4, 1), 0.0, 0.0, transmission=0.9)
    mat_solar = create_pbr_material("Solar_PV", (0.02, 0.05, 0.15, 1), 0.9, 0.1)
    mat_dust = create_pbr_material("Ash_Dust", (0.3, 0.25, 0.2, 1), 0.0, 1.0)

    # ------------------------------------------------------------------
    # [ GEOMETRY GENERATION (Engineering TRUE Scale) ]
    # ------------------------------------------------------------------
    
    # 1. Ground Plane (Dust Bowl)
    bpy.ops.mesh.primitive_plane_add(size=50, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.data.materials.append(mat_dust)
    
    # 2. Subterranean Condensation Matrix (Copper)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=3.0, location=(0.5, 0, -1.0))
    pipe = bpy.context.active_object
    pipe.rotation_euler[0] = math.radians(90)
    pipe.data.materials.append(mat_copper)
    
    # 3. ABS Lego Structural Frame (Heat-isolated)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.5))
    chassis = bpy.context.active_object
    chassis.scale = (0.8, 1.5, 0.2)
    chassis.data.materials.append(mat_lego)
    
    # 4. Stirling Gamma Core (True 5-Liter Volumetric Scale)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.25, depth=0.8, location=(0, 0.5, 1.0))
    hot_cyl = bpy.context.active_object
    hot_cyl.data.materials.append(mat_rust)
    
    bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=0.6, location=(0, -0.5, 1.0))
    cold_cyl = bpy.context.active_object
    cold_cyl.data.materials.append(mat_rust)
    
    # 5. Kinematics: Scavenged Bicycle Wheel Flywheel
    bpy.ops.mesh.primitive_torus_add(major_radius=0.4, minor_radius=0.02, location=(0.5, 0, 1.5))
    wheel = bpy.context.active_object
    wheel.rotation_euler[1] = math.radians(90)
    wheel.data.materials.append(mat_rust)
    
    # 6. Electrolysis Array (Glass Jar)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=0.4, location=(-0.5, 0, 0.8))
    jar = bpy.context.active_object
    jar.data.materials.append(mat_glass)
    
    # Water inside jar
    bpy.ops.mesh.primitive_cylinder_add(radius=0.14, depth=0.3, location=(-0.5, 0, 0.75))
    water = bpy.context.active_object
    water.data.materials.append(mat_water)
    
    # 7. 2-Square Meter Scavenged PV Panel
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-1.0, 0, 2.0))
    pv = bpy.context.active_object
    pv.scale = (1.5, 2.0, 0.05)
    pv.rotation_euler[0] = math.radians(20)
    pv.rotation_euler[1] = math.radians(15)
    pv.data.materials.append(mat_solar)
    
    # ------------------------------------------------------------------
    # [ CINEMATOGRAPHY & LIGHTING ]
    # ------------------------------------------------------------------
    
    # Dust Bowl Sun
    bpy.ops.object.light_add(type='SUN', location=(5, 5, 10))
    sun = bpy.context.active_object
    sun.data.energy = 5.0
    sun.data.angle = math.radians(1.5) # Soft shadows from atmospheric dust
    sun.data.color = (1.0, 0.85, 0.7) # Oppressive orange heat
    
    # Camera setup (Macroscopic Depth of Field)
    bpy.ops.object.camera_add(location=(4, -5, 3))
    cam = bpy.context.active_object
    cam.rotation_euler = (math.radians(65), 0, math.radians(45))
    cam.data.lens = 85 # 85mm portrait for tight scale
    
    # Depth of field focusing on the Stirling Core
    cam.data.dof.use_dof = True
    cam.data.dof.focus_object = hot_cyl
    cam.data.dof.aperture_fstop = 2.8
    
    bpy.context.scene.camera = cam

    # Save to disk
    blend_path = REPO_ROOT / "dust_bowl_engineering_scale.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    
    # Optional: We could also render it directly to a final image here!
    # render_path = REPO_ROOT / "dust_bowl_render.png"
    # bpy.context.scene.render.filepath = render_path
    # bpy.ops.render.render(write_still=True)

    print(f"[Graph OS] -> Blender Max-Reality Transpile Complete. Scene saved to {blend_path}")

if __name__ == "__main__":
    setup_maximum_reality()
