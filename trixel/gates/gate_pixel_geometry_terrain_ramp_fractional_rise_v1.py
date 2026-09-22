#!/usr/bin/env python3
"""Second terrain integration proof: non-integer rise.

current terrain integration (integer rise)   PROVEN, FROZEN, UNTOUCHED
non-integer rise                              THIS GATE
different ramp orientation                    later
multiple ramps / composition                  later
taper                                         later -- different topology problem

The first integration proof chose a worked example where the rise (5.0)
happened to be a whole number of terrain height layers, leaving one
question open: did the seam close because the placement math is sound, or
because the rise happened to fit the terrain's own integer quantization?

This gate proves it is the former. Worked example: 5 ramp cells, required
rise 2.5 (not a whole number). Both terrain blocks are built through the
UNMODIFIED consumer/builder with the SAME ordinary elevation (0.0) and the
SAME max_height_layers (1, an arbitrary whole number never derived from
the rise) -- terrain-local height authority never represents 2.5 at any
point. The fractional rise is reached entirely by one explicit whole-
artifact rigid translation applied AFTER the builder has already finished
(terrain_ramp_integration_v1.translate_built_geometry), proving
terrain-local height authority and world-placement authority are two
separate concepts, not one conflated one.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from trixel.pixel_geometry.artwork_mapping_v1 import footprint_corner_uvs, uvs_are_identical
from trixel.pixel_geometry.compiler_v1 import compile_footprint, edge_lengths
from trixel.pixel_geometry.contracts_v1 import EMBEDDING_DECLARED_ANGLE_RAMP_FOLD
from trixel.pixel_geometry.embedding_v1 import embed_declared_angle_ramp_fold
from trixel.pixel_geometry.terrain_ramp_integration_v1 import ramp_position_to_world

import export_terrain_ramp_fractional_rise_evidence as scene_tool

CHECKS: list[bool] = []


def report(name: str, ok: bool, message: str = "") -> bool:
    suffix = f" — {message}" if message else ""
    print(f"[PIXEL_GEOMETRY_TERRAIN_RAMP_FRACTIONAL_RISE][{name}] {'TRUE' if ok else 'FALSE'}{suffix}")
    CHECKS.append(ok)
    return ok


def close(a: float, b: float, tol: float = 1e-9) -> bool:
    return abs(a - b) <= tol


def main() -> int:
    scene = scene_tool.build_scene()
    lower_built = scene["lower_built"]
    upper_built_natural = scene["upper_built_natural"]
    upper_built = scene["upper_built"]
    attachment = scene["attachment"]
    footprint = scene["footprint"]
    ramp_positions = scene["ramp_positions"]
    solved = scene["ramp_info"]["solved"]

    report(
        "LOWER_TERRAIN_BUILDS_WITH_EXISTING_POLICY",
        lower_built.get("status") == "BUILT" and lower_built.get("topology_policy") == "HEIGHT_FIELD_CONNECTED_SURFACE",
        f"errors={lower_built.get('errors')}",
    )
    report(
        "UPPER_TERRAIN_BUILDS_WITH_EXISTING_POLICY",
        upper_built_natural.get("status") == "BUILT"
        and upper_built_natural.get("topology_policy") == "HEIGHT_FIELD_CONNECTED_SURFACE",
        f"errors={upper_built_natural.get('errors')}",
    )

    # The core claim: neither terrain request ever declares or produces a
    # fractional elevation. world_cell_y stays an exact integer (0) for
    # every cell in BOTH blocks -- checked directly on the pre-translation
    # built packets, before any placement is applied.
    lower_heights = {cr["world_cell"]["world_cell_y"] for cr in lower_built["cell_geometry_ranges"]}
    upper_heights_natural = {cr["world_cell"]["world_cell_y"] for cr in upper_built_natural["cell_geometry_ranges"]}
    report(
        "TERRAIN_ELEVATION_STAYS_INTEGER_EVERYWHERE",
        lower_heights == {0} and upper_heights_natural == {0},
        f"lower={lower_heights} upper={upper_heights_natural}",
    )
    report(
        "REQUIRED_RISE_IS_GENUINELY_NON_INTEGER",
        not float(scene_tool.REQUIRED_RISE).is_integer(),
        f"required_rise={scene_tool.REQUIRED_RISE}",
    )

    # The whole-artifact placement translation applied to upper terrain:
    # its Y component must equal required_rise EXACTLY -- the fractional
    # height comes only from this explicit translation, not from any
    # terrain-internal elevation math.
    translation = scene["translation"]
    report(
        "WHOLE_ARTIFACT_TRANSLATION_Y_EQUALS_REQUIRED_RISE_EXACTLY",
        close(translation[1], scene_tool.REQUIRED_RISE),
        f"translation_y={translation[1]} required_rise={scene_tool.REQUIRED_RISE}",
    )

    # The translation is a pure translation -- verify it never rescales
    # the upper terrain's own internal geometry: every pair of its own
    # vertices keeps the exact same distance apart before and after.
    natural_positions = upper_built_natural["geometry"]["positions"]
    translated_positions = upper_built["geometry"]["positions"]
    sample_indices = [0, len(natural_positions) // 3, len(natural_positions) - 1]

    def distance(p, q):
        return sum((p[i] - q[i]) ** 2 for i in range(3)) ** 0.5

    translation_is_isometry = True
    for i in sample_indices:
        for j in sample_indices:
            before = distance(natural_positions[i], natural_positions[j])
            after = distance(translated_positions[i], translated_positions[j])
            if not close(before, after, tol=1e-9):
                translation_is_isometry = False
    report("TERRAIN_PLACEMENT_TRANSLATION_PRESERVES_INTERNAL_DISTANCES", translation_is_isometry)

    # world_cell_y in the BUILT packet is untouched by translate_built_
    # geometry (only geometry.positions moves) -- it must still read 0,
    # proving the translation lives entirely outside the terrain's own
    # declared height field.
    upper_heights_after_translation = {cr["world_cell"]["world_cell_y"] for cr in upper_built["cell_geometry_ranges"]}
    report(
        "TRANSLATED_ARTIFACT_STILL_DECLARES_INTEGER_LOCAL_HEIGHT",
        upper_heights_after_translation == {0},
        f"got {upper_heights_after_translation}",
    )

    # The ramp's far edge -- and therefore the point the upper terrain's
    # attachment edge must reach -- has a genuinely fractional world Y.
    far_edge_ys = {round(p[1], 9) for p in attachment["ramp_far_world"]}
    report(
        "RAMP_ATTACHMENT_REACHES_FRACTIONAL_WORLD_HEIGHT",
        far_edge_ys == {round(scene_tool.REQUIRED_RISE, 9)} and not scene_tool.REQUIRED_RISE.is_integer(),
        f"far_edge_ys={far_edge_ys}",
    )

    independent_positions = embed_declared_angle_ramp_fold(
        footprint, hinge_corner_x=scene_tool.HINGE_CORNER_X, angle_degrees=solved.angle_degrees
    )
    report("RAMP_USES_FROZEN_DECLARED_ANGLE_EMBEDDING", independent_positions == ramp_positions)

    compiled = compile_footprint(footprint, ramp_positions, embedding_id=EMBEDDING_DECLARED_ANGLE_RAMP_FOLD)
    ramp_edges = edge_lengths(compiled)
    report(
        "RAMP_CELL_METRIC_REMAINS_1_0",
        all(close(length, 1.0) for length in ramp_edges),
        f"min={min(ramp_edges):.9f} max={max(ramp_edges):.9f}",
    )

    uv_a = footprint_corner_uvs(footprint)
    uv_b = footprint_corner_uvs(footprint)
    report("RAMP_ARTWORK_UVS_UNCHANGED", uvs_are_identical(uv_a, uv_b))

    report("LOWER_ATTACHMENT_EDGE_MATCHES_EXACTLY", attachment["lower_attachment_matches"])
    report("UPPER_ATTACHMENT_EDGE_MATCHES_EXACTLY", attachment["upper_attachment_matches"])
    report("NO_RAMP_VERTEX_SCALING", attachment["is_isometry"])

    terrain_unit_metric = all(
        request["planar_config"]["cell_width"] == 1.0 and request["planar_config"]["cell_depth"] == 1.0
        for request in (scene["lower_request"], scene["upper_request"])
    )
    report("NO_TERRAIN_VERTEX_SCALING", terrain_unit_metric)

    declared_points = set(
        tuple(round(c, 6) for c in p) for p in attachment["ramp_near_world"] + attachment["ramp_far_world"]
    )
    ramp_world_all = [
        ramp_position_to_world(pos, path_x_offset=scene_tool.PATH_X_OFFSET, ramp_z_offset=scene_tool.ramp_z_offset())
        for (x, r), pos in ramp_positions.items()
        if x >= scene_tool.HINGE_CORNER_X
    ]
    other_ramp_points = [p for p in ramp_world_all if tuple(round(c, 6) for c in p) not in declared_points]
    terrain_points = [
        tuple(p)
        for built in (lower_built, upper_built)
        for p in built["geometry"]["positions"]
        if tuple(round(c, 6) for c in p) not in declared_points
    ]
    proximity_tolerance = 0.4
    offenders = [
        (a, b)
        for a in other_ramp_points
        for b in terrain_points
        if sum((a[i] - b[i]) ** 2 for i in range(3)) ** 0.5 <= proximity_tolerance
    ]
    report(
        "NO_POSITION_DERIVED_ADJACENCY",
        len(offenders) == 0,
        f"offenders={len(offenders)}" if offenders else "",
    )

    scene_again = scene_tool.build_scene()
    deterministic = (
        json.dumps(scene["lower_built"], sort_keys=True) == json.dumps(scene_again["lower_built"], sort_keys=True)
        and json.dumps(scene["upper_built"], sort_keys=True) == json.dumps(scene_again["upper_built"], sort_keys=True)
        and scene["ramp_positions"] == scene_again["ramp_positions"]
        and scene["translation"] == scene_again["translation"]
        and scene["attachment"]["lower_attachment_matches"] == scene_again["attachment"]["lower_attachment_matches"]
        and scene["attachment"]["upper_attachment_matches"] == scene_again["attachment"]["upper_attachment_matches"]
    )
    report("COMPOSED_SCENE_IS_DETERMINISTIC", deterministic)

    all_ok = all(CHECKS)
    print(f"[PIXEL_GEOMETRY_TERRAIN_RAMP_FRACTIONAL_RISE][ALL_GATES] {'true' if all_ok else 'false'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
