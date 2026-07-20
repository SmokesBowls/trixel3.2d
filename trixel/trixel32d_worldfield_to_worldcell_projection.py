from __future__ import annotations

import math
from numbers import Real
from typing import Final

CONTRACT_ID: Final[str] = "worldfield_to_worldcell_projection.v1"
INPUT_SPACE: Final[str] = "worldfield_grid"
OUTPUT_SPACE: Final[str] = "godot_y_up"
ELEVATION_RULE: Final[str] = "world_cell_y via round(elevation * max_height_layers)"


def project_worldfield_cell_to_worldcell(
    field_x: int,
    field_y: int,
    elevation: float,
    *,
    max_height_layers: int,
) -> dict[str, object]:
    """Project one 2D WorldField sample into one 3D world-cell identity."""

    _validate_int(field_x, "field_x")
    _validate_int(field_y, "field_y")
    elevation_value = _validate_elevation(elevation)
    _validate_int(max_height_layers, "max_height_layers")
    if max_height_layers <= 0:
        raise ValueError("max_height_layers must be a positive int")

    world_cell_x = field_x
    world_cell_z = field_y
    world_cell_y = round(elevation_value * max_height_layers)

    return {
        "contract": CONTRACT_ID,
        "input_space": INPUT_SPACE,
        "output_space": OUTPUT_SPACE,
        "field": {
            "field_x": field_x,
            "field_y": field_y,
            "elevation": elevation_value,
        },
        "world_cell": {
            "world_cell_x": world_cell_x,
            "world_cell_y": world_cell_y,
            "world_cell_z": world_cell_z,
        },
        "world_cell_tuple": [world_cell_x, world_cell_y, world_cell_z],
        "projection_rule": {
            "field_x": "world_cell_x",
            "field_y": "world_cell_z",
            "elevation": ELEVATION_RULE,
        },
    }


def _validate_int(value: object, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an int")


def _validate_elevation(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError("elevation must be numeric")
    elevation = float(value)
    if not math.isfinite(elevation):
        raise ValueError("elevation must be finite")
    if elevation < 0.0 or elevation > 1.0:
        raise ValueError("elevation must be in the inclusive range 0.0..1.0")
    return elevation
