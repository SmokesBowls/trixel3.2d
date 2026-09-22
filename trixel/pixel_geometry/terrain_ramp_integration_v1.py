"""Attachment verification between a pixel_geometry ramp and two pre-built
trixel32d_surface_builder terrain packets.

This module's responsibility is deliberately narrow:

    input:
        a compiled pixel_geometry ramp (corner positions)
        two ALREADY-BUILT trixel32d_surface_builder terrain packets
    verify:
        the ramp's near attachment edge coincides with the lower
        terrain's attachment edge, in world space
        the ramp's far attachment edge coincides with the upper
        terrain's attachment edge, in world space
    output:
        the placement transform used, plus the two edge comparisons

It NEVER builds terrain (trixel32d_surface_builder.py /
trixel32d_surface_consumer.py stay untouched and are called directly by
the caller, not by this module) and NEVER re-derives ramp geometry
(embedding_v1.py / ramp_geometry_v1.py stay untouched and are called
directly by the caller). The only degrees of freedom this module
introduces are the ramp's placement offsets (path_x_offset,
ramp_z_offset) -- both a pure rotation-plus-translation of the ramp's own
already-computed positions, never a rescaling of them.
"""
from __future__ import annotations

import copy
import math
from typing import Any

Position = tuple[float, float, float]


def ramp_position_to_world(
    position: Position, *, path_x_offset: float, ramp_z_offset: float, rotation_degrees: float = 90.0
) -> Position:
    """Map one ramp-local (x, y, r) position into world space by a
    rotation about Y (the shared up axis) plus a translation.

        world_x = ramp_x*cos(theta) + ramp_z*sin(theta) + path_x_offset
        world_y = ramp_y
        world_z = -ramp_x*sin(theta) + ramp_z*cos(theta) + ramp_z_offset

    where theta = rotation_degrees. world_y is always a direct passthrough
    -- both frames are Y-up, and one pixel_geometry cell_metric unit of
    rise equals one terrain vertical_metric meter by construction,
    regardless of how the ramp is oriented in the X-Z plane.

    The default, rotation_degrees=90.0, is exactly the fixed mapping the
    first two terrain-integration proofs used (world_x = ramp_z +
    path_x_offset, world_z = -ramp_x + ramp_z_offset -- the ramp's
    fold-direction axis becomes world -Z, its width axis becomes world X)
    -- calling this function with no rotation_degrees argument reproduces
    their behavior bit for bit. rotation_degrees=0.0 instead sends the
    ramp's fold-direction axis straight to world +X, for a ramp whose
    travel direction does not coincide with the terrain lane's original
    forward axis.

    For ANY rotation_degrees this is still a rotation plus a translation
    -- an isometry, proven by verify_isometry() below, not merely
    asserted -- so no orientation choice this function accepts can ever
    stretch the ramp."""
    ramp_x, ramp_y, ramp_z = position
    theta = math.radians(rotation_degrees)
    cos_t, sin_t = math.cos(theta), math.sin(theta)
    world_x = ramp_x * cos_t + ramp_z * sin_t + path_x_offset
    world_z = -ramp_x * sin_t + ramp_z * cos_t + ramp_z_offset
    return (world_x, ramp_y, world_z)


def verify_isometry(
    *, path_x_offset: float, ramp_z_offset: float, rotation_degrees: float = 90.0, tol: float = 1e-9
) -> bool:
    """Prove ramp_position_to_world never scales anything at the given
    rotation_degrees: two arbitrary sample points must keep the exact
    same distance apart after the transform as before it."""
    sample_a: Position = (0.3, 1.7, 0.9)
    sample_b: Position = (4.1, -2.2, 3.4)

    def distance(p: Position, q: Position) -> float:
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(p, q)))

    before = distance(sample_a, sample_b)
    world_a = ramp_position_to_world(
        sample_a, path_x_offset=path_x_offset, ramp_z_offset=ramp_z_offset, rotation_degrees=rotation_degrees
    )
    world_b = ramp_position_to_world(
        sample_b, path_x_offset=path_x_offset, ramp_z_offset=ramp_z_offset, rotation_degrees=rotation_degrees
    )
    after = distance(world_a, world_b)
    return abs(before - after) <= tol


def translate_built_geometry(built: dict[str, Any], translation: Position) -> dict[str, Any]:
    """Return a copy of a BUILT trixel32d_surface_builder packet with every
    position moved by `translation`. This is what keeps terrain-local
    height authority separate from world-placement authority: the
    builder's own elevation/max_height_layers math never sees this
    translation and stays in its ordinary integer-layer space -- this
    function only moves an already-built artifact afterward, the same
    translation-only discipline as embedding_v1.embed_rigid's whole-
    footprint transform. It never touches vertex count, indices,
    normals, colors, or any other field."""
    dx, dy, dz = translation
    translated = copy.deepcopy(built)
    translated["geometry"]["positions"] = [
        [p[0] + dx, p[1] + dy, p[2] + dz] for p in built["geometry"]["positions"]
    ]
    translated["geometry"]["vertices"] = translated["geometry"]["positions"]
    return translated


def terrain_attachment_edge(
    built: dict[str, Any], *, field_x_values: set[int], field_y: int, edge: str
) -> list[Position]:
    """Extract the world-space positions of one boundary edge of a
    BUILT trixel32d_surface_builder packet's top faces, for the given
    columns and row. edge='low_z' picks each face's two lowest-Z
    vertices, edge='high_z' its two highest-Z vertices -- never assumed
    by index, always read back from the actual built positions, so a
    change in the builder's internal vertex ordering cannot silently
    break this check."""
    if edge not in ("low_z", "high_z"):
        raise ValueError("edge must be 'low_z' or 'high_z'")
    positions = built["geometry"]["positions"]
    result: list[Position] = []
    for cell_range in built["cell_geometry_ranges"]:
        if cell_range["field_x"] not in field_x_values or cell_range["field_y"] != field_y:
            continue
        top = next(s for s in cell_range["surfaces"] if s["role"] == "PRIMARY_PIXEL_FACE")
        verts = [tuple(positions[v]) for v in range(top["vertex_start"], top["vertex_start"] + top["vertex_count"])]
        z_values = [v[2] for v in verts]
        target_z = min(z_values) if edge == "low_z" else max(z_values)
        result.extend(v for v in verts if abs(v[2] - target_z) <= 1e-9)
    return result


def terrain_attachment_edge_x(
    built: dict[str, Any], *, field_y_values: set[int], field_x: int, edge: str
) -> list[Position]:
    """The X-boundary sibling of terrain_attachment_edge(): for a ramp
    whose travel direction has been rotated to point along X instead of
    -Z, the attachment edge is a fixed COLUMN (field_x) spanning a set of
    ROWS, not a fixed row spanning columns. edge='low_x' picks each face's
    two lowest-X vertices, edge='high_x' its two highest-X vertices --
    read back from the actual built positions, exactly like its Z-axis
    sibling, never assumed by index. terrain_attachment_edge() itself is
    left untouched; this is a new, separate function so no existing
    caller's behavior can change."""
    if edge not in ("low_x", "high_x"):
        raise ValueError("edge must be 'low_x' or 'high_x'")
    positions = built["geometry"]["positions"]
    result: list[Position] = []
    for cell_range in built["cell_geometry_ranges"]:
        if cell_range["field_y"] not in field_y_values or cell_range["field_x"] != field_x:
            continue
        top = next(s for s in cell_range["surfaces"] if s["role"] == "PRIMARY_PIXEL_FACE")
        verts = [tuple(positions[v]) for v in range(top["vertex_start"], top["vertex_start"] + top["vertex_count"])]
        x_values = [v[0] for v in verts]
        target_x = min(x_values) if edge == "low_x" else max(x_values)
        result.extend(v for v in verts if abs(v[0] - target_x) <= 1e-9)
    return result


def _dedupe(points: list[Position], *, tol: float = 1e-9) -> list[Position]:
    unique: list[Position] = []
    for point in points:
        if not any(all(abs(a - b) <= tol for a, b in zip(point, existing)) for existing in unique):
            unique.append(point)
    return unique


def edges_coincide(a: list[Position], b: list[Position], *, tol: float = 1e-9) -> bool:
    """True only if the two point sets are identical (order-independent,
    deduplicated) within tolerance."""
    unique_a = _dedupe(a, tol=tol)
    unique_b = _dedupe(b, tol=tol)
    if len(unique_a) != len(unique_b):
        return False
    remaining = list(unique_b)
    for point in unique_a:
        match = next(
            (candidate for candidate in remaining if all(abs(x - y) <= tol for x, y in zip(point, candidate))),
            None,
        )
        if match is None:
            return False
        remaining.remove(match)
    return True


def verify_attachment(
    *,
    ramp_positions: dict[tuple[int, int], Position],
    lower_terrain_built: dict[str, Any],
    upper_terrain_built: dict[str, Any],
    hinge_corner_x: int,
    ramp_far_corner_x: int,
    path_x_offset: float,
    ramp_z_offset: float,
    lower_field_x_values: set[int],
    lower_field_y: int,
    upper_field_x_values: set[int],
    upper_field_y: int,
    tol: float = 1e-9,
) -> dict[str, Any]:
    """The one function this module exists for: compare the ramp's near
    and far edges against the declared terrain attachment edges, in world
    space, under the stated placement offsets."""
    ramp_near_world = [
        ramp_position_to_world(pos, path_x_offset=path_x_offset, ramp_z_offset=ramp_z_offset)
        for (x, r), pos in ramp_positions.items()
        if x == hinge_corner_x
    ]
    ramp_far_world = [
        ramp_position_to_world(pos, path_x_offset=path_x_offset, ramp_z_offset=ramp_z_offset)
        for (x, r), pos in ramp_positions.items()
        if x == ramp_far_corner_x
    ]
    lower_edge = terrain_attachment_edge(
        lower_terrain_built, field_x_values=lower_field_x_values, field_y=lower_field_y, edge="low_z"
    )
    upper_edge = terrain_attachment_edge(
        upper_terrain_built, field_x_values=upper_field_x_values, field_y=upper_field_y, edge="high_z"
    )
    return {
        "lower_attachment_matches": edges_coincide(ramp_near_world, lower_edge, tol=tol),
        "upper_attachment_matches": edges_coincide(ramp_far_world, upper_edge, tol=tol),
        "ramp_near_world": ramp_near_world,
        "ramp_far_world": ramp_far_world,
        "lower_edge": lower_edge,
        "upper_edge": upper_edge,
        "is_isometry": verify_isometry(path_x_offset=path_x_offset, ramp_z_offset=ramp_z_offset, tol=tol),
    }


def verify_attachment_edges(
    *,
    ramp_near_world: list[Position],
    ramp_far_world: list[Position],
    lower_edge: list[Position],
    upper_edge: list[Position],
    path_x_offset: float,
    ramp_z_offset: float,
    rotation_degrees: float = 90.0,
    tol: float = 1e-9,
) -> dict[str, Any]:
    """The orientation-general sibling of verify_attachment(): takes the
    ramp's near/far world points and the two terrain attachment edges
    ALREADY EXTRACTED by the caller (using whichever of
    terrain_attachment_edge / terrain_attachment_edge_x and edge polarity
    fits the ramp's actual travel direction -- this function has no
    opinion about that, on purpose, since "which edge faces the ramp"
    depends on rotation_degrees in a way that is the caller's declared
    scene layout to own, not something to infer here). Only the
    comparison and the isometry proof are shared logic.
    verify_attachment() itself is untouched -- this is a separate
    function so its frozen callers' behavior cannot change."""
    return {
        "lower_attachment_matches": edges_coincide(ramp_near_world, lower_edge, tol=tol),
        "upper_attachment_matches": edges_coincide(ramp_far_world, upper_edge, tol=tol),
        "ramp_near_world": ramp_near_world,
        "ramp_far_world": ramp_far_world,
        "lower_edge": lower_edge,
        "upper_edge": upper_edge,
        "is_isometry": verify_isometry(
            path_x_offset=path_x_offset, ramp_z_offset=ramp_z_offset, rotation_degrees=rotation_degrees, tol=tol
        ),
    }
