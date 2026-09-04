"""Generate the calibrated mechanical hinge stop."""

import argparse
from pathlib import Path

from build123d import Box, Cylinder, Pos, export_step


EXPORT_PATH = Path(__file__).resolve().parents[1] / "exports" / "hinge_stop-16-8.step"


def build_hinge_stop(
    block_length=64.0,
    block_width=17.0,
    block_height=8.0,
    hole_radius=2.5,
    hole1_x_offset=16.0,
    hole1_y_offset=6.0,
    hole2_x_offset=6.0,
    hole2_y_offset=6.0,
):
    """Build and return the hinge stop in millimetres."""
    block = Box(block_length, block_width, block_height)
    block_bounds = block.bounding_box()

    hole1 = Cylinder(hole_radius, block_height + 2)
    hole1_bounds = hole1.bounding_box()
    hole1.move(
        Pos(
            block_bounds.min.X - hole1_bounds.min.X + hole1_x_offset,
            block_bounds.min.Y - hole1_bounds.min.Y + hole1_y_offset,
            block_bounds.min.Z - hole1_bounds.min.Z,
        )
    )

    hole2 = Cylinder(hole_radius, block_height + 2)
    hole2_bounds = hole2.bounding_box()
    hole2.move(
        Pos(
            block_bounds.max.X - hole2_bounds.max.X - hole2_x_offset,
            block_bounds.min.Y - hole2_bounds.min.Y + hole2_y_offset,
            block_bounds.min.Z - hole2_bounds.min.Z,
        )
    )

    return block - hole1 - hole2


def preview_hinge_stop(hinge_stop):
    """Show the part when the optional ocp_vscode package is available."""
    try:
        from ocp_vscode import show_object
    except ImportError as exc:
        raise RuntimeError(
            "Preview requested, but ocp_vscode is not installed."
        ) from exc

    show_object(hinge_stop, "hinge stop", options={"color": [150, 250, 150]})


def main(preview=False):
    hinge_stop = build_hinge_stop()
    export_step(hinge_stop, str(EXPORT_PATH))
    if preview:
        preview_hinge_stop(hinge_stop)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--preview",
        action="store_true",
        help="show the generated part with the optional ocp_vscode package",
    )
    args = parser.parse_args()
    main(preview=args.preview)
