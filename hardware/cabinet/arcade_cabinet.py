"""Build the visualization-only cabinet and wiring layout.

The recorded dimensions are inch values, while build123d STEP exports are
millimetre-based. STEP export is intentionally disabled until every dimension
has been converted by 25.4 and checked against the physical cabinet.
"""

import argparse
import math

from build123d import Box, Compound, Cylinder, Polyline, Pos, Rot


def build_arcade_cabinet():
    """Build and return the inch-valued cabinet visualization."""
    panel_thickness = 0.75
    thin_panel_thickness = 0.5
    absolute_width = 48.0
    cab_depth = 36.0
    cab_height = 36.0
    ground_clearance = 36.0

    # 2x4 corner legs
    leg = Box(1.5, 3.5, 72.0)
    leg_z = 72.0 / 2
    leg_left_x = -absolute_width / 2.0 + 1.5 / 2.0
    leg_right_x = absolute_width / 2.0 - 1.5 / 2.0
    leg_fl = leg.moved(Pos(leg_left_x, 1.75, leg_z))
    leg_fr = leg.moved(Pos(leg_right_x, 1.75, leg_z))
    leg_bl = leg.moved(Pos(leg_left_x, cab_depth - 1.75, leg_z))
    leg_br = leg.moved(Pos(leg_right_x, cab_depth - 1.75, leg_z))
    legs = leg_fl + leg_fr + leg_bl + leg_br

    front_height = 0.0
    rear_height = 24.0
    drop = rear_height - front_height
    inner_depth = cab_depth
    ramp_length = 96.0
    ramp_angle = math.degrees(math.atan(drop / inner_depth))
    board_inside_len = inner_depth / math.cos(math.radians(ramp_angle))
    pivot_offset = ramp_length / 2.0 - board_inside_len

    # Side panels
    side_panel = Box(thin_panel_thickness, cab_depth, cab_height)
    panel_z = ground_clearance + cab_height / 2.0
    panel_left_x = leg_left_x + 1.5 / 2.0 + thin_panel_thickness / 2.0
    panel_right_x = leg_right_x - 1.5 / 2.0 - thin_panel_thickness / 2.0
    left_panel = side_panel.moved(Pos(panel_left_x, cab_depth / 2.0, panel_z))
    right_panel = side_panel.moved(Pos(panel_right_x, cab_depth / 2.0, panel_z))
    side_panels = left_panel + right_panel

    # Back panel
    back_panel = Box(absolute_width, panel_thickness, cab_height).moved(
        Pos(0, cab_depth + panel_thickness / 2.0, panel_z + rear_height)
    )

    inner_width = absolute_width - 1.5 * 2 - thin_panel_thickness * 2

    # Sloped floor with wall-edge cable pass-throughs
    floor_raw = (
        Rot(X=ramp_angle)
        * Pos(0, -pivot_offset, 0.75 / 2.0)
        * Box(inner_width, ramp_length, 0.75)
    )
    floor_raw.move(Pos(0, 0.0, ground_clearance + front_height))

    shelf_rear_y = [7.0, 21.5, 35.0]
    hole_cutters = []
    for rear_y in shelf_rear_y:
        cutter = Cylinder(radius=0.5, height=20.0).moved(
            Pos(panel_right_x - 1.0, rear_y, ground_clearance + 5.0)
        )
        hole_cutters.append(cutter)

    floor = floor_raw
    for cutter in hole_cutters:
        floor -= cutter

    # Front stretcher; align its top with the bottom of the side panels.
    stretcher = Box(absolute_width, thin_panel_thickness, 12.0).moved(
        Pos(0, -thin_panel_thickness / 2, ground_clearance + 2.0)
    )
    stretcher.move(
        Pos(
            0,
            0,
            side_panels.bounding_box().min.Z - stretcher.bounding_box().max.Z,
        )
    )

    # Three 7-inch shelves
    shelf = Box(inner_width, 7.0, 0.5)
    shelf_1 = shelf.moved(Pos(0, 3.5, ground_clearance + 10.0))
    shelf_2 = shelf.moved(Pos(0, 18.0, ground_clearance + 21.0))
    shelf_3 = shelf.moved(Pos(0, 32.5, ground_clearance + 32.0))
    shelves = shelf_1 + shelf_2 + shelf_3

    # Six target positions from the cabinet layout study.
    clown = Box(8.0, 0.25, 8.0)
    clown_z_offset = 0.25 + 4.0
    row1_spread = 5.0
    row2_spread = 10.0
    row3_spread = 15.0
    c1_left = clown.moved(
        Pos(-row1_spread, 0.0, ground_clearance + 10.0 + clown_z_offset)
    )
    c1_right = clown.moved(
        Pos(row1_spread, 0.0, ground_clearance + 10.0 + clown_z_offset)
    )
    c2_left = clown.moved(
        Pos(-row2_spread, 14.5, ground_clearance + 21.0 + clown_z_offset)
    )
    c2_right = clown.moved(
        Pos(row2_spread, 14.5, ground_clearance + 21.0 + clown_z_offset)
    )
    c3_left = clown.moved(
        Pos(-row3_spread, 29.0, ground_clearance + 32.0 + clown_z_offset)
    )
    c3_right = clown.moved(
        Pos(row3_spread, 29.0, ground_clearance + 32.0 + clown_z_offset)
    )
    clowns = c1_left + c1_right + c2_left + c2_right + c3_left + c3_right

    # ESP32 placement and conceptual cable routing
    esp_x = panel_right_x - thin_panel_thickness / 2.0 - 0.5
    esp_y = 21.5
    esp_z = ground_clearance + 2.0
    esp32 = Box(1.0, 2.0, 0.5).moved(Pos(esp_x, esp_y, esp_z))

    clown_positions = [
        (-row1_spread, 0.0, 10.0, 7.0),
        (row1_spread, 0.0, 10.0, 7.0),
        (-row2_spread, 14.5, 21.0, 21.5),
        (row2_spread, 14.5, 21.0, 21.5),
        (-row3_spread, 29.0, 32.0, 35.0),
        (row3_spread, 29.0, 32.0, 35.0),
    ]

    wire_paths = []
    for target_x, target_y, z_offset, rear_y in clown_positions:
        z_shelf_top = ground_clearance + z_offset + 0.25
        z_shelf_bottom = ground_clearance + z_offset - 0.25
        p1 = (target_x, target_y + 4.0, z_shelf_top + 0.5)
        p2 = (target_x, rear_y + 0.5, z_shelf_top + 0.5)
        p3 = (target_x, rear_y + 0.5, z_shelf_bottom)
        p4 = (panel_right_x - 1.0, rear_y + 0.5, z_shelf_bottom)
        p5 = (panel_right_x - 1.0, rear_y + 0.5, esp_z)
        p6 = (esp_x, esp_y, esp_z)
        wire_paths.append(Polyline(p1, p2, p3, p4, p5, p6))

    wiring_harness = Compound(children=wire_paths)
    cabinet_structure = (
        legs
        + left_panel
        + right_panel
        + back_panel
        + stretcher
        + floor
        + shelves
        + clowns
        + esp32
    )
    return Compound(children=[cabinet_structure, wiring_harness])


def preview_arcade_cabinet(arcade_cabinet):
    """Show the layout when the optional ocp_vscode package is available."""
    try:
        from ocp_vscode import show_object
    except ImportError as exc:
        raise RuntimeError(
            "Preview requested, but ocp_vscode is not installed."
        ) from exc

    show_object(
        arcade_cabinet,
        "arcade cabinet",
        options={"color": [200, 150, 100]},
    )


def main(preview=False):
    arcade_cabinet = build_arcade_cabinet()
    if preview:
        preview_arcade_cabinet(arcade_cabinet)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--preview",
        action="store_true",
        help="show the layout with the optional ocp_vscode package",
    )
    args = parser.parse_args()
    main(preview=args.preview)
