# Parametric models and fabrication exports

The printable mechanisms are authored in millimetres with build123d algebra-mode scripts. Canonical STEP outputs and the slicer-ready 3MF projects used during development are checked in so the design can be inspected without recreating the original CAD environment.

## Environment

- Python 3.10 or newer
- Dependencies from [`requirements-cad.txt`](../../requirements-cad.txt)
- Optional: `ocp-vscode` for interactive previews

```shell
python -m pip install -r requirements-cad.txt
# Optional interactive viewer:
python -m pip install ocp-vscode
```

The compatibility baseline is build123d 0.10.0. The scripts make preview support optional, so STEP export works without a running VS Code viewer.

## Generators

Run scripts from any working directory; each one writes its canonical STEP file to [`exports/`](exports/).

| Script | Canonical STEP output | Default overall bounds |
| --- | --- | --- |
| [`scripts/cam_lobe.py`](scripts/cam_lobe.py) | `arcade_cam_lobe_80-3.6-4.0-4.0.step` | 93 × 18 × 6 mm |
| [`scripts/servo_bracket.py`](scripts/servo_bracket.py) | `clown_servo_bracket.step` | 44 × 16 × 24 mm |
| [`scripts/hinge_stop.py`](scripts/hinge_stop.py) | `hinge_stop-16-8.step` | 64 × 17 × 8 mm |
| [`scripts/switch_bracket.py`](scripts/switch_bracket.py) | `switch_tunnel_bracket.step` | 54 × 12 × 35 mm |

Example:

```shell
python hardware/models/scripts/cam_lobe.py
```

Review the resulting STEP diff before replacing a fabrication file. The scripts intentionally expose their dimensions near the top for physical iteration.

## Export history

The additional cam and hinge-stop filenames preserve design iterations rather than a formal release sequence. The repository does not record which exact variant was installed in the delivered cabinet, so those files should not be deleted or renamed based only on their timestamps.

The 3MF files are Bambu Studio 2.3.2 projects created around an X1 Carbon with a 0.4 mm nozzle. They contain a mix of 0.20 mm Precision and 0.28 mm Extra Draft profiles. Treat those settings as historical starting points and select material, orientation, supports, tolerances, and a printer profile appropriate to the machine actually producing the part.

## Cabinet model

[`../cabinet/arcade_cabinet.py`](../cabinet/arcade_cabinet.py) is a spatial layout study whose numeric values are inches. build123d's default geometry/export convention is millimetres, so the script intentionally does **not** export a manufacturing STEP: an unscaled export would declare those inch-valued numbers as millimetres and open 25.4× too small.

The cabinet study retains six target positions while the delivered firmware enables five. It also preserves the original 96-inch raw floor-board study and back-panel placement; change those dimensions only against physical measurements of the build.
