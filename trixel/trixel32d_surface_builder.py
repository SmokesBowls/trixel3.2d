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
    """Build canonical geometry for the request's declared topology policy."""
    topology_policy = request["construction"]["topology_policy"]
    if topology_policy == "HEIGHT_FIELD_COMPLETE_EDGE_CONNECTED_SURFACE":
        return _build_complete_edge_connected_surface(request)
    if topology_policy == "HEIGHT_FIELD_CONNECTED_SURFACE":
        return _build_connected_surface(request)
    return _build_independent_cell_extrusions(request)


def _build_independent_cell_extrusions(request: dict[str, Any]) -> dict[str, Any]:
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


def _build_connected_surface(request: dict[str, Any]) -> dict[str, Any]:
    """Build one coherent stitched slab: shared-edge tops, exposed walls only.

    Every cell keeps its exact top face color and projected height. Internal
    faces between adjacent cells are omitted; a vertical wall exists only where
    two adjacent tops differ in height (owned by the higher cell, spanning
    exactly the difference) or on the field perimeter down to the slab base.
    The base is one thickness below the lowest top, closed by per-cell bottom
    faces, so the result is one coherent, geometrically closed terrain slab.

    Declared limitation: walls are full-edge quads, so where three or more
    differing heights meet at a corner, vertical wall side edges form exact
    collinear T-junction overlaps. Every boundary is coordinate-coincident
    (no cracks or holes), but the mesh is not strictly edge-manifold. This
    matters later for collision, mesh processing, or LOD, and must be
    resolved (wall splitting per height interval) before those consumers;
    it does not affect rendering of this policy.
    """
    planar = request["planar_config"]
    gap_fill = request["gap_fill"]
    vectors = request["orientation"]["vectors"]
    right = _normalize(vectors["right"])
    forward = _normalize(vectors["forward"])
    up = _normalize(vectors["up"])
    max_height_layers = int(request["vertical_metric"]["max_height_layers"])

    half_right = _scale(right, float(planar["cell_width"]) / 2.0)
    half_forward = _scale(forward, float(planar["cell_depth"]) / 2.0)
    thickness = float(gap_fill["thickness_local_units"])
    gap_color = [float(value) for value in gap_fill["resolved_color"]]
    width = int(planar["field_width_columns"])

    cells = request["pixel_field_data"]
    projections = [
        project_worldfield_cell_to_worldcell(
            cell["field_x"],
            cell["field_y"],
            cell["elevation"],
            max_height_layers=max_height_layers,
        )
        for cell in cells
    ]
    heights = [
        float(cast(dict[str, Any], projection["world_cell"])["world_cell_y"])
        for projection in projections
    ]
    base_height = min(heights) - thickness

    positions: list[list[float]] = []
    normals: list[list[float]] = []
    uvs: list[list[float]] = []
    colors: list[list[float]] = []
    indices: list[int] = []
    cell_ranges: list[dict[str, Any]] = []
    primitive_provenance: list[dict[str, Any]] = []

    def center_at(field_x: int, field_y: int, height: float) -> list[float]:
        column_offset = (field_x - float(planar["center_column"])) * float(planar["cell_width"])
        row_offset = (field_y - float(planar["center_row"])) * float(planar["cell_depth"])
        return _add(
            _scale(right, column_offset),
            _scale(forward, row_offset),
            _scale(up, height),
        )

    def neighbor_height(field_x: int, field_y: int) -> float | None:
        if field_x < 0 or field_y < 0 or field_x >= width:
            return None
        ordinal = field_y * width + field_x
        if ordinal >= len(heights):
            return None
        return heights[ordinal]

    for ordinal, cell in enumerate(cells):
        field_x = cell["field_x"]
        field_y = cell["field_y"]
        top_height = heights[ordinal]
        top_center = center_at(field_x, field_y, top_height)
        base_center = center_at(field_x, field_y, base_height)
        cell_color = [float(value) for value in cell["base_color"]]

        faces: list[tuple[str, str, list[list[float]], list[float], list[float]]] = [(
            "PRIMARY_PIXEL_FACE",
            "top",
            _quad(top_center, _negate(half_right), half_right, _negate(half_forward), half_forward),
            up,
            cell_color,
        ), (
            "NEUTRAL_GAP_FILL",
            "bottom",
            _quad(base_center, _negate(half_right), half_right, half_forward, _negate(half_forward)),
            _negate(up),
            gap_color,
        )]

        wall_specs = (
            ("-field_y", (field_x, field_y - 1)),
            ("+field_x", (field_x + 1, field_y)),
            ("+field_y", (field_x, field_y + 1)),
            ("-field_x", (field_x - 1, field_y)),
        )
        for face_name, (neighbor_x, neighbor_y) in wall_specs:
            other_height = neighbor_height(neighbor_x, neighbor_y)
            if other_height is None:
                wall_bottom = base_height
            elif other_height < top_height:
                wall_bottom = other_height
            else:
                continue  # shared or lower edge: the internal face is omitted
            wall_top_center = top_center
            wall_bottom_center = center_at(field_x, field_y, wall_bottom)
            if face_name == "-field_y":
                quad = _quad_between(
                    wall_top_center, wall_bottom_center, half_forward,
                    negative=True, horizontal=half_right,
                )
                normal = _negate(forward)
            elif face_name == "+field_x":
                quad = _quad_side(
                    wall_top_center, wall_bottom_center, half_right, half_forward,
                    positive=True,
                )
                normal = right
            elif face_name == "+field_y":
                quad = _quad_between(
                    wall_top_center, wall_bottom_center, half_forward,
                    negative=False, horizontal=_negate(half_right),
                )
                normal = forward
            else:
                quad = _quad_side(
                    wall_top_center, wall_bottom_center, half_right, _negate(half_forward),
                    positive=False,
                )
                normal = _negate(right)
            faces.append(("NEUTRAL_GAP_FILL", face_name, quad, normal, gap_color))

        surfaces: list[dict[str, Any]] = []
        for face_ordinal, (role, face, quad, normal, face_color) in enumerate(faces):
            vertex_start = len(positions)
            index_start = len(indices)
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
            "world_cell": cast(dict[str, Any], projections[ordinal]["world_cell"]),
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
        "recipe_references": sorted({cell["recipe"] for cell in cells}),
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


def _build_complete_edge_connected_surface(request: dict[str, Any]) -> dict[str, Any]:
    """Build the stitched slab with complete shared wall edges (no T-junctions).

    Identical footprint, heights, and colors to HEIGHT_FIELD_CONNECTED_SURFACE.
    Each vertical wall is split at every incident elevation breakpoint at its
    two end corners: the wall becomes a deterministic ladder triangulation
    between its left and right corner height chains, so every neighboring wall
    face shares identical vertices and complete edges. Horizontal wall edges
    (top and bottom) stay complete full-cell edges shared with top faces.

    Declared limitation PINCH_EDGE_NON_MANIFOLD: where diagonally opposed
    cells pair strictly higher/lower, the true solid has a vertical pinch
    edge and its boundary is non-manifold there by nature. Those inventoried
    edges carry exactly four direction-balanced incident triangles; every
    other welded edge carries exactly two. No claim is made about downstream
    collision tooling; collision remains denied and untested.
    """
    planar = request["planar_config"]
    gap_fill = request["gap_fill"]
    vectors = request["orientation"]["vectors"]
    right = _normalize(vectors["right"])
    forward = _normalize(vectors["forward"])
    up = _normalize(vectors["up"])
    max_height_layers = int(request["vertical_metric"]["max_height_layers"])

    half_right = _scale(right, float(planar["cell_width"]) / 2.0)
    half_forward = _scale(forward, float(planar["cell_depth"]) / 2.0)
    thickness = float(gap_fill["thickness_local_units"])
    gap_color = [float(value) for value in gap_fill["resolved_color"]]
    width = int(planar["field_width_columns"])
    height_rows = int(planar["field_height_rows"])

    cells = request["pixel_field_data"]
    projections = [
        project_worldfield_cell_to_worldcell(
            cell["field_x"],
            cell["field_y"],
            cell["elevation"],
            max_height_layers=max_height_layers,
        )
        for cell in cells
    ]
    heights = [
        float(cast(dict[str, Any], projection["world_cell"])["world_cell_y"])
        for projection in projections
    ]
    base_height = min(heights) - thickness

    def cell_height(field_x: int, field_y: int) -> float | None:
        if field_x < 0 or field_y < 0 or field_x >= width or field_y >= height_rows:
            return None
        return heights[field_y * width + field_x]

    def lattice_breakpoints(lattice_x: int, lattice_y: int) -> list[float]:
        incident: set[float] = set()
        for cell_x, cell_y in (
            (lattice_x - 1, lattice_y - 1),
            (lattice_x, lattice_y - 1),
            (lattice_x - 1, lattice_y),
            (lattice_x, lattice_y),
        ):
            value = cell_height(cell_x, cell_y)
            if value is not None:
                incident.add(value)
        return sorted(incident)

    def center_at(field_x: int, field_y: int, elevation_value: float) -> list[float]:
        column_offset = (field_x - float(planar["center_column"])) * float(planar["cell_width"])
        row_offset = (field_y - float(planar["center_row"])) * float(planar["cell_depth"])
        return _add(
            _scale(right, column_offset),
            _scale(forward, row_offset),
            _scale(up, elevation_value),
        )

    positions: list[list[float]] = []
    normals: list[list[float]] = []
    uvs: list[list[float]] = []
    colors: list[list[float]] = []
    indices: list[int] = []
    cell_ranges: list[dict[str, Any]] = []
    primitive_provenance: list[dict[str, Any]] = []

    # Wall spec per canonical direction: neighbor delta, outward normal sign,
    # left/right corner lattice ids and horizontal corner offsets from center.
    def wall_specs(field_x: int, field_y: int) -> list[tuple[str, tuple[int, int], list[float], tuple[int, int], tuple[int, int], list[float], list[float]]]:
        minus_hr = _negate(half_right)
        minus_hf = _negate(half_forward)
        return [
            ("-field_y", (field_x, field_y - 1), _negate(forward),
             (field_x, field_y), (field_x + 1, field_y),
             _add(minus_hf, minus_hr), _add(minus_hf, half_right)),
            ("+field_x", (field_x + 1, field_y), right,
             (field_x + 1, field_y), (field_x + 1, field_y + 1),
             _add(half_right, minus_hf), _add(half_right, half_forward)),
            ("+field_y", (field_x, field_y + 1), forward,
             (field_x, field_y + 1), (field_x + 1, field_y + 1),
             _add(half_forward, minus_hr), _add(half_forward, half_right)),
            ("-field_x", (field_x - 1, field_y), _negate(right),
             (field_x, field_y), (field_x, field_y + 1),
             _add(minus_hr, minus_hf), _add(minus_hr, half_forward)),
        ]

    for ordinal, cell in enumerate(cells):
        field_x = cell["field_x"]
        field_y = cell["field_y"]
        top_height = heights[ordinal]
        flat_center = center_at(field_x, field_y, 0.0)
        top_center = center_at(field_x, field_y, top_height)
        base_center = center_at(field_x, field_y, base_height)
        cell_color = [float(value) for value in cell["base_color"]]

        surfaces: list[dict[str, Any]] = []
        face_ordinal = 0

        def emit_face(
            role: str,
            face: str,
            face_positions: list[list[float]],
            face_normals: list[list[float]],
            face_uvs: list[list[float]],
            face_color: list[float],
            face_indices: list[int],
        ) -> None:
            nonlocal face_ordinal
            vertex_start = len(positions)
            index_start = len(indices)
            positions.extend(face_positions)
            normals.extend(face_normals)
            uvs.extend(face_uvs)
            colors.extend([face_color[:] for _ in face_positions])
            indices.extend(vertex_start + local_index for local_index in face_indices)
            surfaces.append({
                "role": role,
                "face": face,
                "vertex_start": vertex_start,
                "vertex_count": len(face_positions),
                "index_start": index_start,
                "index_count": len(face_indices),
            })
            primitive_provenance.append({
                "primitive_start": index_start // 3,
                "primitive_count": len(face_indices) // 3,
                "cell_key": f"{field_x},{field_y}",
                "source_cell_ordinal": ordinal,
                "face_ordinal": face_ordinal,
                "role": role,
                "face": face,
            })
            face_ordinal += 1

        top_quad = _quad(top_center, _negate(half_right), half_right, _negate(half_forward), half_forward)
        emit_face(
            "PRIMARY_PIXEL_FACE", "top", top_quad,
            [up[:] for _ in range(4)], [uv[:] for uv in QUAD_UVS], cell_color,
            list(QUAD_INDICES),
        )
        bottom_quad = _quad(base_center, _negate(half_right), half_right, half_forward, _negate(half_forward))
        emit_face(
            "NEUTRAL_GAP_FILL", "bottom", bottom_quad,
            [_negate(up) for _ in range(4)], [uv[:] for uv in QUAD_UVS], gap_color,
            list(QUAD_INDICES),
        )

        for face_name, neighbor_key, outward, left_lattice, right_lattice, left_offset, right_offset in wall_specs(field_x, field_y):
            other_height = cell_height(*neighbor_key)
            if other_height is None:
                wall_bottom = base_height
            elif other_height < top_height:
                wall_bottom = other_height
            else:
                continue

            left_cuts = [
                value for value in lattice_breakpoints(*left_lattice)
                if wall_bottom < value < top_height
            ]
            right_cuts = [
                value for value in lattice_breakpoints(*right_lattice)
                if wall_bottom < value < top_height
            ]
            left_chain = [wall_bottom] + left_cuts + [top_height]
            right_chain = [wall_bottom] + right_cuts + [top_height]

            left_base = _add(flat_center, left_offset)
            right_base = _add(flat_center, right_offset)
            span = top_height - wall_bottom
            face_positions: list[list[float]] = []
            face_uvs: list[list[float]] = []
            left_ids: list[int] = []
            right_ids: list[int] = []
            for value in left_chain:
                left_ids.append(len(face_positions))
                face_positions.append(_add(left_base, _scale(up, value)))
                face_uvs.append([0.0, (value - wall_bottom) / span])
            for value in right_chain:
                right_ids.append(len(face_positions))
                face_positions.append(_add(right_base, _scale(up, value)))
                face_uvs.append([1.0, (value - wall_bottom) / span])

            face_indices: list[int] = []
            i = 0
            j = 0
            while i < len(left_chain) - 1 or j < len(right_chain) - 1:
                advance_left = j == len(right_chain) - 1 or (
                    i < len(left_chain) - 1 and left_chain[i + 1] <= right_chain[j + 1]
                )
                if advance_left:
                    triangle = (left_ids[i], right_ids[j], left_ids[i + 1])
                    i += 1
                else:
                    triangle = (left_ids[i], right_ids[j], right_ids[j + 1])
                    j += 1
                a, b, c = triangle
                winding_normal = _cross_of(
                    _sub(face_positions[b], face_positions[a]),
                    _sub(face_positions[c], face_positions[a]),
                )
                if _dot_of(winding_normal, outward) < 0.0:
                    triangle = (a, c, b)
                face_indices.extend(triangle)

            emit_face(
                "NEUTRAL_GAP_FILL", face_name, face_positions,
                [outward[:] for _ in face_positions], face_uvs, gap_color,
                face_indices,
            )

        cell_ranges.append({
            "cell_key": f"{field_x},{field_y}",
            "source_cell_ordinal": ordinal,
            "field_x": field_x,
            "field_y": field_y,
            "world_cell": cast(dict[str, Any], projections[ordinal]["world_cell"]),
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
        "recipe_references": sorted({cell["recipe"] for cell in cells}),
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


def _sub(left: Sequence[float], right_vector: Sequence[float]) -> list[float]:
    return [float(left[index]) - float(right_vector[index]) for index in range(3)]


def _cross_of(left: Sequence[float], right_vector: Sequence[float]) -> list[float]:
    return [
        left[1] * right_vector[2] - left[2] * right_vector[1],
        left[2] * right_vector[0] - left[0] * right_vector[2],
        left[0] * right_vector[1] - left[1] * right_vector[0],
    ]


def _dot_of(left: Sequence[float], right_vector: Sequence[float]) -> float:
    return sum(left[index] * right_vector[index] for index in range(3))


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
