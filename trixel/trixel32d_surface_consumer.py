from __future__ import annotations

import json
import math
import re
from numbers import Real
from pathlib import Path
from typing import Any, NoReturn

from trixel.trixel32d_surface_builder import build_canonical_surface
from trixel.trixel32d_surface_emitter import emit_rejected_surface


REQUEST_CONTRACT = "trixel32d_surface_request.v1"
RECIPE_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")


class RequestValidationError(ValueError):
    """The first fail-closed request validation failure."""


def consume_surface_request_file(
    request_path: str | Path,
    *,
    recipe_root: str | Path,
) -> dict[str, Any]:
    """Load one JSON request and return either a complete BUILT or REJECTED packet."""
    path = Path(request_path)
    try:
        request = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return emit_rejected_surface(None, f"request file could not be loaded: {exc}")
    return consume_surface_request_packet(request, recipe_root=recipe_root)


def consume_surface_request_packet(
    request: object,
    *,
    recipe_root: str | Path,
) -> dict[str, Any]:
    """Validate without defaults, then build; malformed input never reaches geometry."""
    request_id = _request_id_if_present(request)
    try:
        validated = validate_surface_request(request, recipe_root=Path(recipe_root))
    except RequestValidationError as exc:
        return emit_rejected_surface(request_id, str(exc))
    return build_canonical_surface(validated)


def validate_surface_request(request: object, *, recipe_root: Path) -> dict[str, Any]:
    if not isinstance(request, dict):
        _reject("request must be a JSON object")
    if request.get("packet_type") != "trixel32d_surface_request":
        _reject("packet_type must be 'trixel32d_surface_request'")

    identity = _mapping(request.get("identity"), "identity")
    if identity.get("contract") != REQUEST_CONTRACT:
        _reject(f"identity.contract must be '{REQUEST_CONTRACT}'")
    _nonempty_string(identity.get("request_id"), "identity.request_id")
    _nonempty_string(identity.get("source_scene_id"), "identity.source_scene_id")
    if identity.get("packet_type") != request["packet_type"]:
        _reject("identity.packet_type must match packet_type")
    provenance = _mapping(identity.get("provenance"), "identity.provenance")
    for field in ("source_scene_id", "topology_artifact_id", "metric_layout_artifact_id"):
        _nonempty_string(provenance.get(field), f"identity.provenance.{field}")

    if request.get("coordinate_space") != "WORLD_FIELD_GRID_TO_LOCAL_Y_UP":
        _reject("coordinate_space must be 'WORLD_FIELD_GRID_TO_LOCAL_Y_UP'")
    if request.get("up_axis_policy") != "MUST_BE_STANDARD_Y_UP_IN_PRIMARY_DIRECTION":
        _reject("up_axis_policy must be 'MUST_BE_STANDARD_Y_UP_IN_PRIMARY_DIRECTION'")
    _validate_orientation(request.get("orientation"))

    construction = _mapping(request.get("construction"), "construction")
    if construction.get("ordering") != "ROW_MAJOR":
        _reject("construction.ordering must be 'ROW_MAJOR'")
    if construction.get("topology_policy") != "HEIGHT_FIELD_CELL_EXTRUSION":
        _reject("construction.topology_policy must be 'HEIGHT_FIELD_CELL_EXTRUSION'")
    if construction.get("appearance_policy") != "RECIPE_REFERENCE":
        _reject("construction.appearance_policy must be 'RECIPE_REFERENCE'")

    planar = _mapping(request.get("planar_config"), "planar_config")
    width = _positive_int(planar.get("field_width_columns"), "planar_config.field_width_columns")
    height = _positive_int(planar.get("field_height_rows"), "planar_config.field_height_rows")
    if planar.get("field_coverage") != "DENSE":
        _reject("planar_config.field_coverage must be 'DENSE'")
    _positive_finite(planar.get("cell_width"), "planar_config.cell_width")
    _positive_finite(planar.get("cell_depth"), "planar_config.cell_depth")
    _finite_number(planar.get("center_column"), "planar_config.center_column")
    _finite_number(planar.get("center_row"), "planar_config.center_row")

    vertical = _mapping(request.get("vertical_metric"), "vertical_metric")
    if vertical.get("granted_by") != "cartographer":
        _reject("vertical_metric.granted_by must be 'cartographer'")
    if vertical.get("vertical_measurement_rule") != "ELEVATION_TIMES_MAX_HEIGHT_LAYERS":
        _reject("vertical_metric.vertical_measurement_rule must be 'ELEVATION_TIMES_MAX_HEIGHT_LAYERS'")
    if vertical.get("unit") != "meter":
        _reject("vertical_metric.unit must be 'meter'")
    layers = _positive_finite(vertical.get("max_height_layers"), "vertical_metric.max_height_layers")
    if not layers.is_integer():
        _reject("vertical_metric.max_height_layers must be a whole number")
    _nonempty_string(vertical.get("source_artifact_id"), "vertical_metric.source_artifact_id")

    gap = _mapping(request.get("gap_fill"), "gap_fill")
    if gap.get("enabled") is not True:
        _reject("gap_fill.enabled must be true")
    if gap.get("mode") != "PER_CELL_EXTRUSION":
        _reject("gap_fill.mode must be 'PER_CELL_EXTRUSION'")
    if gap.get("adjacency_policy") != "ALL_FACES_INDEPENDENT":
        _reject("gap_fill.adjacency_policy must be 'ALL_FACES_INDEPENDENT'")
    _rgba(gap.get("resolved_color"), "gap_fill.resolved_color")
    _positive_finite(gap.get("thickness_local_units"), "gap_fill.thickness_local_units")

    cells = request.get("pixel_field_data")
    if not isinstance(cells, list):
        _reject("pixel_field_data must be a list")
    if len(cells) != width * height:
        _reject(f"pixel_field_data must contain exactly {width * height} cells")
    if not recipe_root.is_dir():
        _reject(f"recipe root does not exist: '{recipe_root}'")

    for ordinal, cell in enumerate(cells):
        if not isinstance(cell, dict):
            _reject(f"pixel_field_data[{ordinal}] must be an object")
        expected_x = ordinal % width
        expected_y = ordinal // width
        actual_x = cell.get("field_x")
        actual_y = cell.get("field_y")
        if actual_x != expected_x or actual_y != expected_y or isinstance(actual_x, bool) or isinstance(actual_y, bool):
            _reject(
                f"pixel_field_data[{ordinal}] is not row-major: expected ({expected_x},{expected_y}), "
                f"got ({actual_x},{actual_y})"
            )
        elevation = _finite_number(cell.get("elevation"), f"pixel_field_data[{ordinal}].elevation")
        if elevation < 0.0 or elevation > 1.0:
            _reject(f"pixel_field_data[{ordinal}].elevation must be in 0.0..1.0")
        _nonempty_string(cell.get("terrain"), f"pixel_field_data[{ordinal}].terrain")
        recipe = _nonempty_string(cell.get("recipe"), f"pixel_field_data[{ordinal}].recipe")
        if not RECIPE_ID_PATTERN.fullmatch(recipe) or not (recipe_root / f"{recipe}.json").is_file():
            _reject(f"pixel_field_data[{ordinal}].recipe is unresolved: '{recipe}'")
        _rgba(cell.get("base_color"), f"pixel_field_data[{ordinal}].base_color")

    return request


def _validate_orientation(value: object) -> None:
    orientation = _mapping(value, "orientation")
    if orientation.get("basis_authority") != "VECTORS":
        _reject("orientation.basis_authority must be 'VECTORS'")
    binding = _mapping(orientation.get("field_axis_binding"), "orientation.field_axis_binding")
    if binding.get("field_x_increases_along") != "RIGHT":
        _reject("orientation.field_axis_binding.field_x_increases_along must be 'RIGHT'")
    if binding.get("field_y_increases_along") != "FORWARD":
        _reject("orientation.field_axis_binding.field_y_increases_along must be 'FORWARD'")
    tolerance = _positive_finite(orientation.get("tolerance"), "orientation.tolerance")
    vectors = _mapping(orientation.get("vectors"), "orientation.vectors")
    normalized: dict[str, list[float]] = {}
    for name in ("right", "forward", "up"):
        vector = vectors.get(name)
        if not isinstance(vector, list) or len(vector) != 3:
            _reject(f"orientation.vectors.{name} must contain 3 numbers")
        values = [_finite_number(component, f"orientation.vectors.{name}[{index}]") for index, component in enumerate(vector)]
        length = math.sqrt(sum(component * component for component in values))
        if abs(length - 1.0) > tolerance:
            _reject(f"orientation.vectors.{name} must be unit length within tolerance")
        normalized[name] = [component / length for component in values]
    for left, right in (("right", "forward"), ("right", "up"), ("forward", "up")):
        if abs(_dot(normalized[left], normalized[right])) > tolerance:
            _reject(f"orientation vectors {left} and {right} must be orthogonal")
    cross = _cross(normalized["right"], normalized["forward"])
    if math.sqrt(sum((cross[index] - normalized["up"][index]) ** 2 for index in range(3))) > tolerance:
        _reject("orientation vectors must satisfy cross(right, forward) = up")
    if math.sqrt(sum((normalized["up"][index] - [0.0, 1.0, 0.0][index]) ** 2 for index in range(3))) > tolerance:
        _reject("orientation.vectors.up must satisfy standard Y-up")


def _request_id_if_present(request: object) -> str | None:
    if not isinstance(request, dict) or not isinstance(request.get("identity"), dict):
        return None
    value = request["identity"].get("request_id")
    return value if isinstance(value, str) and value else None


def _mapping(value: object, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        _reject(f"{name} must be an object")
    return value


def _nonempty_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        _reject(f"{name} must be a non-empty string")
    return value


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        _reject(f"{name} must be a positive integer")
    return value


def _finite_number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(float(value)):
        _reject(f"{name} must be a finite number")
    return float(value)


def _positive_finite(value: object, name: str) -> float:
    number = _finite_number(value, name)
    if number <= 0.0:
        _reject(f"{name} must be positive")
    return number


def _rgba(value: object, name: str) -> list[float]:
    if not isinstance(value, list) or len(value) != 4:
        _reject(f"{name} must contain 4 finite RGBA values")
    result = [_finite_number(component, f"{name}[{index}]") for index, component in enumerate(value)]
    if any(component < 0.0 or component > 1.0 for component in result):
        _reject(f"{name} components must be in 0.0..1.0")
    return result


def _dot(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def _cross(left: list[float], right: list[float]) -> list[float]:
    return [
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    ]


def _reject(message: str) -> NoReturn:
    raise RequestValidationError(message)
