from __future__ import annotations

from pathlib import Path
from typing import Any
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

CONTRACT_ID = "worldfield_to_worldcell_projection.v1"
FORBIDDEN_SOURCE_TOKENS = (
    "height_scale",
    "cell_size",
    "renderer_centering",
    "render",
    "mesh",
    "GodotProjectionConsumerPacket",
    "surface_basis_resolver",
    "world_field_nucleus",
    "trixel_world_adapter",
    "terrain_thresholds",
    "tile_address",
)


def _print_gate(name: str, ok: bool, message: str = "") -> bool:
    status = "TRUE" if ok else "FALSE"
    suffix = f" — {message}" if message else ""
    print(f"[WORLDFIELD_TO_WORLDCELL_PROJECTION][{name}] {status}{suffix}")
    return ok


def _try_call(fn: Any, *args: Any, **kwargs: Any) -> tuple[bool, str]:
    try:
        fn(*args, **kwargs)
    except Exception as exc:
        return False, str(exc)
    return True, ""


def _coordinate_seam_gate() -> list[bool]:
    checks: list[bool] = []
    lock_path = REPO_ROOT / "TRIXEL32D_COORDINATE_SEAM_LOCK.md"
    checks.append(_print_gate("COORDINATE_SEAM_LOCK_EXISTS", lock_path.exists()))
    lock_text = lock_path.read_text(encoding="utf-8") if lock_path.exists() else ""
    checks.append(_print_gate(
        "COORDINATE_SEAM_LOCK_NAMES_WORLDFIELD_GRID_ROW",
        "world_y in this lane means terrain-grid row/depth coordinate" in lock_text
        and "world_y in this lane is not vertical height" in lock_text,
    ))
    checks.append(_print_gate(
        "COORDINATE_SEAM_LOCK_NAMES_WORLDCELL_VERTICAL_Y",
        "world_cell = (x, y, z)" in lock_text
        and "y in this lane is vertical/up" in lock_text,
    ))
    checks.append(_print_gate(
        "COORDINATE_SEAM_LOCK_NAMES_XZ_SELECTION_SEAM",
        "world_cell.x -> 2D selection x" in lock_text
        and "world_cell.z -> 2D selection y" in lock_text,
    ))
    checks.append(_print_gate(
        "COORDINATE_SEAM_LOCK_NAMES_NEXT_TARGET",
        "worldfield_to_worldcell_projection.v1" in lock_text,
    ))
    return checks


def main() -> int:
    checks: list[bool] = []
    checks.extend(_coordinate_seam_gate())
    seam_ok = all(checks)
    checks.append(_print_gate("COORDINATE_SEAM_GATE_PASSED_BEFORE_BRIDGE", seam_ok))
    if not seam_ok:
        print("[WORLDFIELD_TO_WORLDCELL_PROJECTION][ALL_GATES] false")
        return 1

    import trixel.trixel32d_worldfield_to_worldcell_projection as bridge

    packet = bridge.project_worldfield_cell_to_worldcell(
        12,
        7,
        0.5,
        max_height_layers=10,
    )
    expected = {
        "contract": CONTRACT_ID,
        "input_space": "worldfield_grid",
        "output_space": "godot_y_up",
        "field": {
            "field_x": 12,
            "field_y": 7,
            "elevation": 0.5,
        },
        "world_cell": {
            "world_cell_x": 12,
            "world_cell_y": 5,
            "world_cell_z": 7,
        },
        "world_cell_tuple": [12, 5, 7],
        "projection_rule": {
            "field_x": "world_cell_x",
            "field_y": "world_cell_z",
            "elevation": "world_cell_y via round(elevation * max_height_layers)",
        },
    }
    checks.append(_print_gate("EMITS_EXACT_PACKET_SHAPE", packet == expected))
    checks.append(_print_gate(
        "RENAMES_FIELD_X_TO_WORLDCELL_X",
        packet["field"]["field_x"] == packet["world_cell"]["world_cell_x"],
    ))
    checks.append(_print_gate(
        "RENAMES_FIELD_Y_TO_WORLDCELL_Z",
        packet["field"]["field_y"] == packet["world_cell"]["world_cell_z"],
    ))
    checks.append(_print_gate(
        "MAPS_ELEVATION_TO_INTEGER_LAYER_Y",
        packet["world_cell"]["world_cell_y"] == round(packet["field"]["elevation"] * 10),
    ))
    checks.append(_print_gate(
        "WORLDCELL_TUPLE_IS_X_Y_Z",
        packet["world_cell_tuple"] == [
            packet["world_cell"]["world_cell_x"],
            packet["world_cell"]["world_cell_y"],
            packet["world_cell"]["world_cell_z"],
        ],
    ))

    edge_zero = bridge.project_worldfield_cell_to_worldcell(0, 0, 0.0, max_height_layers=8)
    edge_one = bridge.project_worldfield_cell_to_worldcell(0, 0, 1.0, max_height_layers=8)
    checks.append(_print_gate(
        "ACCEPTS_ELEVATION_ENDPOINTS",
        edge_zero["world_cell"]["world_cell_y"] == 0
        and edge_one["world_cell"]["world_cell_y"] == 8,
    ))

    invalid_cases = (
        ("REJECTS_NON_INT_FIELD_X", (12.0, 7, 0.5), {"max_height_layers": 10}),
        ("REJECTS_BOOL_FIELD_X", (True, 7, 0.5), {"max_height_layers": 10}),
        ("REJECTS_NON_INT_FIELD_Y", (12, "7", 0.5), {"max_height_layers": 10}),
        ("REJECTS_BOOL_FIELD_Y", (12, False, 0.5), {"max_height_layers": 10}),
        ("REJECTS_ELEVATION_BELOW_ZERO", (12, 7, -0.01), {"max_height_layers": 10}),
        ("REJECTS_ELEVATION_ABOVE_ONE", (12, 7, 1.01), {"max_height_layers": 10}),
        ("REJECTS_BOOL_ELEVATION", (12, 7, True), {"max_height_layers": 10}),
        ("REJECTS_NAN_ELEVATION", (12, 7, float("nan")), {"max_height_layers": 10}),
        ("REJECTS_NON_POSITIVE_MAX_HEIGHT_LAYERS", (12, 7, 0.5), {"max_height_layers": 0}),
        ("REJECTS_BOOL_MAX_HEIGHT_LAYERS", (12, 7, 0.5), {"max_height_layers": True}),
    )
    for name, args, kwargs in invalid_cases:
        ok, message = _try_call(bridge.project_worldfield_cell_to_worldcell, *args, **kwargs)
        checks.append(_print_gate(name, ok is False, message if ok else ""))

    source_path = Path(str(bridge.__file__)).resolve()
    source_text = source_path.read_text(encoding="utf-8")
    forbidden_hits = [token for token in FORBIDDEN_SOURCE_TOKENS if token in source_text]
    checks.append(_print_gate(
        "NO_HIDDEN_SCALE_RENDERER_OR_EXISTING_LANE_COUPLING",
        not forbidden_hits,
        f"present={forbidden_hits}" if forbidden_hits else "",
    ))

    all_ok = all(checks)
    print(f"[WORLDFIELD_TO_WORLDCELL_PROJECTION][ALL_GATES] {'true' if all_ok else 'false'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
