from __future__ import annotations

import math
from typing import Any, Sequence, cast

from conductor_building_blocks.terrain.worldfield_to_worldcell_projection import (
    project_worldfield_cell_to_worldcell,
)
from trixel.trixel32d_surface_emitter import emit_built_surface


FACE_SPECS = (
    ("PRIMARY_PIXEL_FACE", "top"),
    ("NEUTRAL_GAP_FILL", "bottom"),
    ("NEUTRAL_GAP_FILL", "-field_y"),
    ("NEUTRAL_GAP_FILL", "+field_x"),
    ("NEUTRAL_GAP_FILL", "+field_y"),
    ("NEUTRAL_GAP_FILL", "-field_x"),
)
QUAD_INDICES = (0, 1, 2, 1, 3, 2)
QUAD_UVS = ([0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [1.0, 1.0])


def build_canonical_surface(request: dict[str, Any]) -> dict[str, Any]:
    """Build independent six-face cell extrusions in deterministic row-major order."""
    planar = request["planar_config"]
    gap_fill = request["gap_fill"]
    vectors = request["orientation"]["vectors"]
    right = _normalize(vectors["right"])
    forward = _normalize(vectors["forward"])
    up = _normalize(vectors["up"])
    max_height_layers = int(request["vertical_metric"]["max_height_layers"])

    positions: list[list[float]] = []
    normals: list[list[float]] = []
    uvs: list[list[float]] = []
    colors: list[list[float]] = []
    indices: list[int] = []
    cell_ranges: list[dict[str, Any]] = []
    primitive_provenance: list[dict[str, Any]] = []

    half_right = _scale(right, float(planar["cell_width"]) / 2.0)
    half_forward = _scale(forward, float(planar["cell_depth"]) / 2.0)
    thickness = float(gap_fill["thickness_local_units"])
    gap_color = [float(value) for value in gap_fill["resolved_color"]]

    for ordinal, cell in enumerate(request["pixel_field_data"]):
        field_x = cell["field_x"]
        field_y = cell["field_y"]
        projection = project_worldfield_cell_to_worldcell(
            field_x,
            field_y,
            cell["elevation"],
            max_height_layers=max_height_layers,
        )
        world_cell = cast(dict[str, Any], projection["world_cell"])
        top_height = float(world_cell["world_cell_y"])
        column_offset = (field_x - float(planar["center_column"])) * float(planar["cell_width"])
        row_offset = (field_y - float(planar["center_row"])) * float(planar["cell_depth"])
        top_center = _add(
            _scale(right, column_offset),
            _scale(forward, row_offset),
            _scale(up, top_height),
        )
        bottom_center = _add(top_center, _scale(up, -thickness))
        face_quads = _cell_face_quads(
            top_center=top_center,
            bottom_center=bottom_center,
            half_right=half_right,
            half_forward=half_forward,
            right=right,
            forward=forward,
            up=up,
        )

        surfaces: list[dict[str, Any]] = []
        for face_ordinal, ((role, face), (quad, normal)) in enumerate(zip(FACE_SPECS, face_quads)):
            vertex_start = len(positions)
            index_start = len(indices)
            face_color = [float(value) for value in cell["base_color"]] if role == "PRIMARY_PIXEL_FACE" else gap_color
            positions.extend(quad)
            normals.extend([normal[:] for _ in range(4)])
            uvs.extend([uv[:] for uv in QUAD_UVS])
            colors.extend([face_color[:] for _ in range(4)])
            indices.extend(vertex_start + local_index for local_index in QUAD_INDICES)
            surfaces.append({
                "role": role,
                "face": face,
                "vertex_start": vertex_start,
                "vertex_count": 4,
                "index_start": index_start,
                "index_count": 6,
            })
            primitive_provenance.append({
                "primitive_start": index_start // 3,
                "primitive_count": 2,
                "cell_key": f"{field_x},{field_y}",
                "source_cell_ordinal": ordinal,
                "face_ordinal": face_ordinal,
                "role": role,
                "face": face,
            })

        cell_ranges.append({
            "cell_key": f"{field_x},{field_y}",
            "source_cell_ordinal": ordinal,
            "field_x": field_x,
            "field_y": field_y,
            "world_cell": world_cell,
            "disposition": "PRESERVED_1_TO_1",
            "recipe": cell["recipe"],
            "terrain": cell["terrain"],
            "surfaces": surfaces,
        })

    geometry = {
        "positions": positions,
        "vertices": positions,
        "normals": normals,
        "uvs": uvs,
        "colors": colors,
        "indices": indices,
    }
    appearance = {
        "policy": request["construction"]["appearance_policy"],
        "recipe_references": sorted({cell["recipe"] for cell in request["pixel_field_data"]}),
        "gap_fill_color": gap_color,
    }
    return emit_built_surface(
        request_id=request["identity"]["request_id"],
        geometry=geometry,
        cell_geometry_ranges=cell_ranges,
        primitive_provenance=primitive_provenance,
        appearance=appearance,
        topology_policy=request["construction"]["topology_policy"],
    )


def _cell_face_quads(
    *,
    top_center: list[float],
    bottom_center: list[float],
    half_right: list[float],
    half_forward: list[float],
    right: list[float],
    forward: list[float],
    up: list[float],
) -> tuple[tuple[list[list[float]], list[float]], ...]:
    top = _quad(top_center, _negate(half_right), half_right, _negate(half_forward), half_forward)
    bottom = _quad(bottom_center, _negate(half_right), half_right, half_forward, _negate(half_forward))
    negative_y = _quad_between(top_center, bottom_center, half_forward, negative=True, horizontal=half_right)
    positive_x = _quad_side(top_center, bottom_center, half_right, half_forward, positive=True)
    positive_y = _quad_between(top_center, bottom_center, half_forward, negative=False, horizontal=_negate(half_right))
    negative_x = _quad_side(top_center, bottom_center, half_right, _negate(half_forward), positive=False)
    return (
        (top, up),
        (bottom, _negate(up)),
        (negative_y, _negate(forward)),
        (positive_x, right),
        (positive_y, forward),
        (negative_x, _negate(right)),
    )


def _quad(center: list[float], u0: list[float], u1: list[float], v0: list[float], v1: list[float]) -> list[list[float]]:
    return [
        _add(center, u0, v0),
        _add(center, u1, v0),
        _add(center, u0, v1),
        _add(center, u1, v1),
    ]


def _quad_between(
    top: list[float], bottom: list[float], offset: list[float], *, negative: bool, horizontal: list[float]
) -> list[list[float]]:
    edge = _negate(offset) if negative else offset
    return [
        _add(bottom, edge, _negate(horizontal)),
        _add(bottom, edge, horizontal),
        _add(top, edge, _negate(horizontal)),
        _add(top, edge, horizontal),
    ]


def _quad_side(
    top: list[float], bottom: list[float], half_right: list[float], horizontal: list[float], *, positive: bool
) -> list[list[float]]:
    edge = half_right if positive else _negate(half_right)
    return [
        _add(bottom, edge, _negate(horizontal)),
        _add(bottom, edge, horizontal),
        _add(top, edge, _negate(horizontal)),
        _add(top, edge, horizontal),
    ]


def _normalize(vector: Sequence[float]) -> list[float]:
    length = math.sqrt(sum(float(value) ** 2 for value in vector))
    return [float(value) / length for value in vector]


def _add(*vectors: Sequence[float]) -> list[float]:
    return [float(sum(vector[index] for vector in vectors)) for index in range(3)]


def _scale(vector: Sequence[float], scalar: float) -> list[float]:
    return [float(value) * scalar for value in vector]


def _negate(vector: Sequence[float]) -> list[float]:
    return [-float(value) for value in vector]
