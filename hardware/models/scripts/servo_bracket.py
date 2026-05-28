# %%
from build123d import *
from ocp_vscode import show_object
# %%
# SG90 Arcade Servo Bracket 
# -------------------------

# Dimensions
thickness = 4.0
wall_width = 44.0
wall_height = 24.0
base_depth = 16.0
# %%
# 1. The Vertical Wall (Centered on origin for easy cutting)
wall = Box(wall_width, thickness, wall_height)
# %%
# 2. The Base Plate (Shifted backward to form the 'L' shape)
base = Box(wall_width, base_depth, thickness).moved(
    Pos(0, -base_depth/2 + thickness/2, -wall_height/2 + thickness/2)
)
# %%
bracket_body = wall + base
# %%
# 3. Servo Cutout (For the SG90 body to slide through the wall)
servo_cutout = Box(23.5, thickness * 3.0, 13.0)
# %%
# 4. Servo Tab Mounting Holes (For M2 machine screws and brass inserts)
# We rotate the cylinders 90 degrees on the X-axis to punch through the vertical wall
servo_holes = (Rot(X=90) * Cylinder(radius=1.1, height=15.0)).moved(Pos(14, 0, 0)) + \
              (Rot(X=90) * Cylinder(radius=1.1, height=15.0)).moved(Pos(-14, 0, 0))
# %%
# 5. Shelf Mounting Holes (For pan head wood screws)
# These remain vertical (Z-axis) to punch through the horizontal base plate
shelf_holes = Cylinder(radius=2.0, height=15.0).moved(Pos(15, -base_depth/2, -wall_height/2)) + \
              Cylinder(radius=2.0, height=15.0).moved(Pos(-15, -base_depth/2, -wall_height/2))
# %%
# 6. Execute the boolean subtraction
final_bracket = bracket_body - servo_cutout - servo_holes - shelf_holes
# %%
show_object(final_bracket)
# %%
# Export for slicing
export_step(final_bracket, "clown_servo_bracket.step")
# %%
