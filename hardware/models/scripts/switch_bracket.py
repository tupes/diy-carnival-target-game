# %%
from build123d import *
from ocp_vscode import show_object
# %%
# Hollow "Tunnel" Switch Bracket
# ------------------------------

# Overall dimensions
core_width = 34.0
depth = 12.0
height = 35.0

# Flange (Feet) Dimensions
foot_width = 10.0 # Extends 10mm on each side
base_thickness = 4.0

tunnel_width = 16.0
tunnel_height = 24.0
# %%
# 1. Main Solid Body
# Centered on the XY plane, shifted up so the bottom rests at Z=0
core = Box(core_width, depth, height).moved(Pos(0, 0, height/2))
# %%
# 2. Mounting Flanges (The "Feet")
# Total width = 34 (core) + 10 (left foot) + 10 (right foot) = 54mm
feet = Box(core_width + (foot_width * 2), depth, base_thickness).moved(Pos(0, 0, base_thickness/2))
# %%
# 3. Combine into a single blank
bracket_blank = core + feet
# %%
# 4. The Wire Tunnel (Cuts through both the core and the base)
tunnel = Box(tunnel_width, depth * 2.0, tunnel_height).moved(Pos(0, 0, tunnel_height/2))
# %%
# 5. Flange Mounting Holes (Vertical, short screws)
# Positioned exactly in the center of the 10mm feet: (34/2) + 5 = 22
shelf_holes = Cylinder(radius=2.0, height=base_thickness * 3.0).moved(Pos(22, 0, 0)) + \
              Cylinder(radius=2.0, height=base_thickness * 3.0).moved(Pos(-22, 0, 0))
# %%
# 6. Switch PCB Mounting Holes (Horizontal through the top bridge)
switch_holes = (Rot(X=90) * Cylinder(radius=1.5, height=depth * 2.0)).moved(Pos(7.5, 0, 29.5)) + \
               (Rot(X=90) * Cylinder(radius=1.5, height=depth * 2.0)).moved(Pos(-7.5, 0, 29.5))
# %%
# 5. Execute Boolean Subtraction
final_bracket = bracket_blank - tunnel - shelf_holes - switch_holes
# %%
show_object(final_bracket, 'switch bracket', options={'color': [150, 250, 150]})
# %%
# Export for slicing
export_step(final_bracket, "switch_tunnel_bracket.step")
# %%
