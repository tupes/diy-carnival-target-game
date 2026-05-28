# %%
import math
from build123d import *
from ocp_vscode import show_object

from precision_organization.lib.domain_services.helpers import align_with
# %%
# Measurements in inches
panel_thickness = 0.75
thin_panel_thickness = 0.5
absolute_width = 48.0 
cab_depth = 36.0      
cab_height = 36.0
ground_clearance = 36.0 
# %%
# 1. 2x4 Corner Legs 
leg = Box(1.5, 3.5, 72.0)
leg_z = 72.0 / 2  
leg_left_x = -absolute_width/2.0 + (1.5 / 2.0)
leg_right_x = absolute_width/2.0 - (1.5 / 2.0)
# %%
leg_fl = leg.moved(Pos(leg_left_x, 1.75, leg_z))
leg_fr = leg.moved(Pos(leg_right_x, 1.75, leg_z))
leg_bl = leg.moved(Pos(leg_left_x, cab_depth - 1.75, leg_z))
leg_br = leg.moved(Pos(leg_right_x, cab_depth - 1.75, leg_z))
legs = leg_fl + leg_fr + leg_bl + leg_br
# %%
show_object(legs, "legs", options={'color': [150, 100, 50]})
# %%
front_height = 0.0
rear_height = 24.0
drop = rear_height - front_height

# The inner depth is exactly cab_depth since the back panel mounts BEHIND the 36" side panels
inner_depth = cab_depth 
# ramp_length = math.sqrt(inner_depth**2 + drop**2) 
ramp_length = 96.0
# ramp_angle = math.degrees(math.asin(drop / inner_depth))
ramp_angle = math.degrees(math.atan(drop / inner_depth))
# Calculate the exact length of the board used INSIDE the cabinet
board_inside_len = inner_depth / math.cos(math.radians(ramp_angle))
# Shift the raw board so its 3D origin (0,0,0) is exactly at the fulcrum pivot point
pivot_offset = (ramp_length / 2.0) - board_inside_len
# %%
# 2. Side Panels (36" x 36")
side_panel = Box(thin_panel_thickness, cab_depth, cab_height)
panel_z = ground_clearance + (cab_height / 2.0) 
panel_left_x = leg_left_x + (1.5 / 2.0) + (thin_panel_thickness / 2.0)
panel_right_x = leg_right_x - (1.5 / 2.0) - (thin_panel_thickness / 2.0)
# %%
left_panel = side_panel.moved(Pos(panel_left_x, cab_depth/2.0, panel_z))
right_panel = side_panel.moved(Pos(panel_right_x, cab_depth/2.0, panel_z))
side_panels = left_panel + right_panel
# %%
show_object(side_panels, "side_panels", options={'color': [100, 150, 200]})
# %%
# 3. Back Panel 
back_panel = Box(absolute_width, panel_thickness, cab_height).moved(
    Pos(0, cab_depth + panel_thickness/2.0, panel_z + rear_height)
)
show_object(back_panel, "back_panel", options={'color': [200, 150, 100]})
# %%
# 4. Internal Dimensions 
inner_width = absolute_width - (1.5 * 2) - (thin_panel_thickness * 2)
# %%
# 5. Sloped Floor - With Wall-Edge Pass-through Holes
# floor_raw = Rot(X=ramp_angle) * Pos(0, inner_depth/2.0, ground_clearance + front_height + (drop / 2)) * Box(inner_width, ramp_length, 0.75)
# floor_raw = Rot(X=ramp_angle) * Pos(0, -ramp_length/2.0, -0.75/2.0) * Box(inner_width, ramp_length, 0.75)
floor_raw = Rot(X=ramp_angle) * Pos(0, -pivot_offset, 0.75/2.0) * Box(inner_width, ramp_length, 0.75)
# align_with(floor_raw, back_panel, {Axis.Y: '<'})
# anchor_z = ground_clearance + rear_height
# floor_raw.move(Location((0, 0, anchor_z)))
# Move the fulcrum pivot point to sit exactly on top of the front stretcher
pivot_world_y = 0.0
pivot_world_z = ground_clearance + front_height
floor_raw.move(Pos(0, pivot_world_y, pivot_world_z))
# Y-coordinates for the back edge of each shelf
shelf_rear_y = [7.0, 21.5, 35.0] # Nudged the last one slightly forward to avoid the back wall corner

hole_cutters = []
for hy in shelf_rear_y:
    # Holes drilled strictly on the extreme right edge
    cutter = Cylinder(radius=0.5, height=20.0).moved(Pos(panel_right_x - 1.0, hy, ground_clearance + 5.0))
    hole_cutters.append(cutter)

floor = floor_raw
for cutter in hole_cutters:
    floor -= cutter

show_object(floor, "floor", options={'color': [200, 150, 200]})
# %%
# 6. Front Stretcher
stretcher = Box(absolute_width, thin_panel_thickness, 12.0).moved(
    Pos(0, -thin_panel_thickness/2, ground_clearance + 2.0)
)
align_with(stretcher, side_panels, {Axis.Z: '<'})
show_object(stretcher, "stretcher", options={'color': [150, 200, 150]})
# %%
# 7. Shelves (7" deep)
shelf = Box(inner_width, 7.0, 0.5)
shelf_1 = shelf.moved(Pos(0, 3.5, ground_clearance + 10.0))
shelf_2 = shelf.moved(Pos(0, 18.0, ground_clearance + 21.0))
shelf_3 = shelf.moved(Pos(0, 32.5, ground_clearance + 32.0))
shelves = shelf_1 + shelf_2 + shelf_3
show_object(shelves, "shelves", options={'color': [150, 200, 200]})
# %%
# 8. Clowns
clown = Box(8.0, 0.25, 8.0)
clown_z_offset = 0.25 + 4.0 

row1_spread = 5.0   
row2_spread = 10.0  
row3_spread = 15.0  

c1_left = clown.moved(Pos(-row1_spread, 0.0, ground_clearance + 10.0 + clown_z_offset))
c1_right = clown.moved(Pos(row1_spread, 0.0, ground_clearance + 10.0 + clown_z_offset))
c2_left = clown.moved(Pos(-row2_spread, 14.5, ground_clearance + 21.0 + clown_z_offset))
c2_right = clown.moved(Pos(row2_spread, 14.5, ground_clearance + 21.0 + clown_z_offset))
c3_left = clown.moved(Pos(-row3_spread, 29.0, ground_clearance + 32.0 + clown_z_offset))
c3_right = clown.moved(Pos(row3_spread, 29.0, ground_clearance + 32.0 + clown_z_offset))

clowns = c1_left + c1_right + c2_left + c2_right + c3_left + c3_right
show_object(clowns, "clowns", options={'color': [200, 200, 50]})
# %%
# 9. Electronics & Wiring

# ESP32 positioned perfectly inline with Row 2 to minimize max wire length
esp_x = panel_right_x - (thin_panel_thickness / 2.0) - 0.5
esp_y = 21.5 # Dead center of the cabinet depth
esp_z = ground_clearance + 2.0
esp32 = Box(1.0, 2.0, 0.5).moved(Pos(esp_x, esp_y, esp_z))
show_object(esp32, "ESP32_Board", options={'color': [50, 50, 50]})
# %%
# Clowns mapped to their respective shelf heights and rear edges
clown_positions = [
    (-row1_spread, 0.0, 10.0, 7.0), (row1_spread, 0.0, 10.0, 7.0),       # Row 1
    (-row2_spread, 14.5, 21.0, 21.5), (row2_spread, 14.5, 21.0, 21.5),   # Row 2
    (-row3_spread, 29.0, 32.0, 35.0), (row3_spread, 29.0, 32.0, 35.0)    # Row 3
]
# %%
wire_paths = []
for hx, hy, z_offset, rear_y in clown_positions:
    z_shelf_top = ground_clearance + z_offset + 0.25
    z_shelf_bot = ground_clearance + z_offset - 0.25
    
    # Calculate floor intersection height for dropping the wire
    z_floor = ground_clearance + front_height + (drop * rear_y / inner_depth)
    
    # 3D Routing Nodes representing your exact plan
    p1 = (hx, hy + 4.0, z_shelf_top + 0.5)      # Start at servo
    p2 = (hx, rear_y + 0.5, z_shelf_top + 0.5)  # Back to the edge of the shelf
    p3 = (hx, rear_y + 0.5, z_shelf_bot)        # Hook under the shelf edge
    p4 = (panel_right_x - 1.0, rear_y + 0.5, z_shelf_bot) # Run under the shelf to the wall
    p5 = (panel_right_x - 1.0, rear_y + 0.5, esp_z)       # Drop through floor hole to ESP32 level
    p6 = (esp_x, esp_y, esp_z)                  # Connect to ESP32
    
    cable = Polyline(p1, p2, p3, p4, p5, p6)
    wire_paths.append(cable)

wiring_harness = Compound(children=wire_paths)
# %%
show_object(wiring_harness, "Wiring_Harness", options={'color': [50, 255, 50]})
# %%
# 10. Final Assembly
full_cabinet = legs + left_panel + right_panel + back_panel + stretcher + floor + shelves + clowns + esp32 + wiring_harness
# %%
show_object(full_cabinet, "arcade_cabinet", options={'color': [200, 150, 100]})
# %%
# Export to view layout
export_step(full_cabinet, "arcade_cabinet_layout.step")