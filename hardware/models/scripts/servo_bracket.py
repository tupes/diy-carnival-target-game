"""Generate the SG90 servo mounting bracket."""

import argparse
from pathlib import Path

from build123d import Box, Cylinder, Pos, Rot, export_step


EXPORT_PATH = (
    Path(__file__).resolve().parents[1] / "exports" / "clown_servo_bracket.step"
)


def build_servo_bracket(
    thickness=4.0,
    wall_width=44.0,
    wall_height=24.0,
    base_depth=16.0,
):
    """Build and return the servo bracket in millimetres."""
    wall = Box(wall_width, thickness, wall_height)
    base = Box(wall_width, base_depth, thickness).moved(
        Pos(0, -base_depth / 2 + thickness / 2, -wall_height / 2 + thickness / 2)
    )
    bracket_body = wall + base

    servo_cutout = Box(23.5, thickness * 3.0, 13.0)
    servo_holes = (Rot(X=90) * Cylinder(radius=1.1, height=15.0)).moved(
        Pos(14, 0, 0)
    ) + (Rot(X=90) * Cylinder(radius=1.1, height=15.0)).moved(Pos(-14, 0, 0))
    shelf_holes = Cylinder(radius=2.0, height=15.0).moved(
        Pos(15, -base_depth / 2, -wall_height / 2)
    ) + Cylinder(radius=2.0, height=15.0).moved(
        Pos(-15, -base_depth / 2, -wall_height / 2)
    )

    return bracket_body - servo_cutout - servo_holes - shelf_holes


def preview_servo_bracket(servo_bracket):
    """Show the part when the optional ocp_vscode package is available."""
    try:
        from ocp_vscode import show_object
    except ImportError as exc:
        raise RuntimeError(
            "Preview requested, but ocp_vscode is not installed."
        ) from exc

    show_object(servo_bracket, "servo bracket")


def main(preview=False):
    servo_bracket = build_servo_bracket()
    export_step(servo_bracket, str(EXPORT_PATH))
    if preview:
        preview_servo_bracket(servo_bracket)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--preview",
        action="store_true",
        help="show the generated part with the optional ocp_vscode package",
    )
    args = parser.parse_args()
    main(preview=args.preview)
