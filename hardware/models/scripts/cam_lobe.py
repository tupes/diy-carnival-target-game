"""Generate the calibrated SG90 cam lobe used to reset a clown target."""

import argparse
from pathlib import Path

from build123d import Box, Circle, Cylinder, Pos, export_step, extrude, make_hull


EXPORT_PATH = (
    Path(__file__).resolve().parents[1]
    / "exports"
    / "arcade_cam_lobe_80-3.6-4.0-4.0.step"
)


def build_cam_lobe(
    cam_reach=80.0,
    base_radius=9.0,
    tip_radius=4.0,
    cam_thickness=6.0,
    horn_length=16.0,
    pocket_depth=4.0,
    arm_depth=4.0,
    hub_radius=3.6,
    arm_width=4.6,
    screw_radius=1.2,
):
    """Build and return the cam lobe in millimetres."""
    base_circle = Circle(radius=base_radius)
    tip_circle = Pos(cam_reach, 0) * Circle(radius=tip_radius)
    cam_profile = make_hull([base_circle.edges(), tip_circle.edges()])
    cam_body = extrude(cam_profile, amount=cam_thickness)

    hub_recess = Cylinder(radius=hub_radius, height=pocket_depth)
    arm_recess = Pos(horn_length / 2, 0, 0) * Box(
        length=horn_length,
        width=arm_width,
        height=arm_depth,
    )

    # Preserve the original minimum-Z alignment without the private helper.
    arm_recess.move(
        Pos(
            0,
            0,
            hub_recess.bounding_box().min.Z - arm_recess.bounding_box().min.Z,
        )
    )

    pocket_tool = hub_recess + arm_recess
    horn_pocket = Pos(0, 0, cam_thickness - pocket_depth / 2) * pocket_tool
    screw_hole = Cylinder(radius=screw_radius, height=cam_thickness * 3)

    return cam_body - horn_pocket - screw_hole


def preview_cam_lobe(cam_lobe):
    """Show the part when the optional ocp_vscode package is available."""
    try:
        from ocp_vscode import show_object
    except ImportError as exc:
        raise RuntimeError(
            "Preview requested, but ocp_vscode is not installed."
        ) from exc

    show_object(cam_lobe, "cam lobe", options={"color": [100, 100, 250]})


def main(preview=False):
    cam_lobe = build_cam_lobe()
    export_step(cam_lobe, str(EXPORT_PATH))
    if preview:
        preview_cam_lobe(cam_lobe)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--preview",
        action="store_true",
        help="show the generated part with the optional ocp_vscode package",
    )
    args = parser.parse_args()
    main(preview=args.preview)
