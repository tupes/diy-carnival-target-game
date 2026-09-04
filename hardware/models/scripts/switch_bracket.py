"""Generate the hollow switch and wiring-tunnel bracket."""

import argparse
from pathlib import Path

from build123d import Box, Cylinder, Pos, Rot, export_step


EXPORT_PATH = (
    Path(__file__).resolve().parents[1] / "exports" / "switch_tunnel_bracket.step"
)


def build_switch_bracket(
    core_width=34.0,
    depth=12.0,
    height=35.0,
    foot_width=10.0,
    base_thickness=4.0,
    tunnel_width=16.0,
    tunnel_height=24.0,
):
    """Build and return the switch bracket in millimetres."""
    core = Box(core_width, depth, height).moved(Pos(0, 0, height / 2))
    feet = Box(
        core_width + foot_width * 2,
        depth,
        base_thickness,
    ).moved(Pos(0, 0, base_thickness / 2))
    bracket_blank = core + feet

    tunnel = Box(tunnel_width, depth * 2.0, tunnel_height).moved(
        Pos(0, 0, tunnel_height / 2)
    )
    shelf_holes = Cylinder(radius=2.0, height=base_thickness * 3.0).moved(
        Pos(22, 0, 0)
    ) + Cylinder(radius=2.0, height=base_thickness * 3.0).moved(Pos(-22, 0, 0))
    switch_holes = (Rot(X=90) * Cylinder(radius=1.5, height=depth * 2.0)).moved(
        Pos(7.5, 0, 29.5)
    ) + (Rot(X=90) * Cylinder(radius=1.5, height=depth * 2.0)).moved(Pos(-7.5, 0, 29.5))

    return bracket_blank - tunnel - shelf_holes - switch_holes


def preview_switch_bracket(switch_bracket):
    """Show the part when the optional ocp_vscode package is available."""
    try:
        from ocp_vscode import show_object
    except ImportError as exc:
        raise RuntimeError(
            "Preview requested, but ocp_vscode is not installed."
        ) from exc

    show_object(
        switch_bracket,
        "switch bracket",
        options={"color": [150, 250, 150]},
    )


def main(preview=False):
    switch_bracket = build_switch_bracket()
    export_step(switch_bracket, str(EXPORT_PATH))
    if preview:
        preview_switch_bracket(switch_bracket)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--preview",
        action="store_true",
        help="show the generated part with the optional ocp_vscode package",
    )
    args = parser.parse_args()
    main(preview=args.preview)
