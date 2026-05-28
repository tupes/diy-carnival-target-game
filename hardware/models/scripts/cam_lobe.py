# %%
from build123d import *
from ocp_vscode import show_object
from precision_organization.lib.domain_services.helpers import align_with
# %%
# --- Parameters ---
cam_reach = 80.0        # Length in mm. Extend this if the cam is still too short!
base_radius = 9.0       # Radius of the meat around the servo shaft
tip_radius = 4.0        # Radius of the pushing tip
cam_thickness = 6.0     # Total thickness of the plastic
# %%
# --- 1. The 2D Cam Profile ---
# We define a large circle at the origin, and a small circle pushed out to our 'reach'.
base_circle = Circle(radius=base_radius)
tip_circle = Pos(cam_reach, 0) * Circle(radius=tip_radius)
# %%
# make_hull wraps a tight boundary around both circles to create a teardrop cam lobe
cam_profile = make_hull([base_circle.edges(), tip_circle.edges()])
# %%
show_object(cam_profile, 'cam profile', options={'color': [200, 200, 250]})
# %%
# --- 2. Extrude to 3D ---
cam_body = extrude(cam_profile, amount=cam_thickness)
# %%
show_object(cam_body, 'cam body', options={'color': [150, 150, 250]})
# %%
# --- 3. The Servo Horn Pocket (Negative Space) ---
# Dimensions for a standard SG90 micro-servo single-arm horn
horn_length = 16.0      # Length of the straight arm
pocket_depth = 4.0
arm_depth = 4.0      
hub_radius = 3.6        # Radius of the round part of the servo horn (plus a tiny clearance)
arm_width = 4.6         # Width of the straight arm
# %%
# Create the round center hub
hub_recess = Cylinder(radius=hub_radius, height=pocket_depth)
# %%
# Create the straight arm, shifted so it extends out from the center
arm_recess = Pos(horn_length/2, 0, 0) * Box(length=horn_length, width=arm_width, height=arm_depth)
align_with(arm_recess, hub_recess, {Axis.Z: 'min'})
# %%
# Fuse them together into a single keyhole-shaped tool
pocket_tool = hub_recess + arm_recess
# %%
show_object(pocket_tool, 'pocket tool', options={'color': [250, 150, 150]})
# %%
# Position the tool at the top surface of the cam
horn_pocket = Pos(0, 0, cam_thickness - pocket_depth/2) * pocket_tool
# %%
show_object(horn_pocket, 'horn pocket', options={'color': [250, 150, 150]})
# %%
# --- 4. The Securing Screw Hole ---
# A small hole all the way through for the retaining screw
screw_hole = Cylinder(radius=1.2, height=cam_thickness * 3)
# %%
# --- 5. Final Boolean Assembly ---
# Subtract the pocket and the hole from the main body
final_cam = cam_body - horn_pocket - screw_hole
# %%
show_object(final_cam, 'final cam lobe', options={'color': [100, 100, 250]})
# %%
# Export the final part for OrcaSlicer
export_step(final_cam, "arcade_cam_lobe_80-3.6-4.0-4.0.step")
# %%
