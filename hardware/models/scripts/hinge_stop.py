# %%
from build123d import *
from ocp_vscode import show_object
from precision_organization.lib.domain_services.helpers import align_with
# %%
block_length = 64.0
block_width = 17.0
block_height = 8.0

hole_radius = 5.0 / 2
hole1_x_offset = 16.0
hole1_y_offset = 6.0
hole2_x_offset = 6.0
hole2_y_offset = 6.0

# %%
block = Box(block_length, block_width, block_height)
# %%
hole1 = Cylinder(hole_radius, block_height + 2)
align_with(hole1, block, {Axis.X: ['min', hole1_x_offset], Axis.Y: ['min', hole1_y_offset], Axis.Z: 'min'})
# %%
hole2 = Cylinder(hole_radius, block_height + 2)
align_with(hole2, block, {Axis.X: ['max', -hole2_x_offset], Axis.Y: ['min', hole2_y_offset], Axis.Z: 'min'})
# %%
show_object(block, 'block', options={'color': [200, 200, 250]})
# %%
show_object(hole1, 'hole 1', options={'color': [250, 150, 150]})
show_object(hole2, 'hole 2', options={'color': [250, 150, 150]})
# %%
hinge_stop = block - hole1 - hole2
# %%
show_object(hinge_stop, 'hinge stop', options={'color': [150, 250, 150]})
# %%
export_step(hinge_stop, "hinge_stop-16-8.step")
# %%
