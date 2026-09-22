#!/usr/bin/env python3
"""Declared-angle ramp proof: given a required rise, what run and angle
are geometrically possible without stretching a single source cell?

flat                         PROVEN (gate_pixel_geometry_flat_footprint_v1)
rigid transform               PROVEN (gate_pixel_geometry_rigid_embedding_v1)
hard 90 degree fold            PROVEN (gate_pixel_geometry_hinge_fold_v1, frozen)
pixel art fold vs stretch      PROVEN (gate_pixel_geometry_artwork_fold_v1)
closed cylindrical wrap        PROVEN (gate_pixel_geometry_cylindrical_wrap_v1)
declared-angle ramp            THIS GATE

Per instruction, this trial's first question is deliberately NOT "what
angle looks right" -- it is a closed-form geometry question, solved by
ramp_geometry_v1.solve_ramp_run_and_angle() BEFORE any embedding runs:

    Given: cell_metric, num_cells, required_rise
    What horizontal run and angle are geometrically possible
    without stretching any source cell?

A straight chain of N unit cells is a rigid rotation for any angle, so
every non-stretching (run, rise) pair lies exactly on the circle
run^2 + rise^2 = (num_cells * cell_metric)^2 -- rise is the only free
input, angle and run are both determined by it, and required_rise beyond
num_cells * cell_metric is not reachable by any angle at all.

This gate does not connect to grass/step/path terrain -- that is
explicitly future work. It proves the math and the embedding it drives.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from PIL import Image

from trixel.pixel_geometry.addressing_v1 import build_footprint, corner_index
from trixel.pixel_geometry.adjacency_v1 import compiled_adjacency_matches_source
from trixel.pixel_geometry.artwork_mapping_v1 import footprint_corner_uvs, uvs_are_identical
from trixel.pixel_geometry.compiler_v1 import compile_footprint, edge_lengths
from trixel.pixel_geometry.contracts_v1 import (
    EMBEDDING_DECLARED_ANGLE_RAMP_FOLD,
    EMBEDDING_HARD_90_DEGREE_HINGE_FOLD,
)
from trixel.pixel_geometry.embedding_v1 import embed_declared_angle_ramp_fold, embed_hard_90_degree_hinge_fold
from trixel.pixel_geometry.ramp_geometry_v1 import solve_ramp_run_and_angle

ART_PATH = REPO_ROOT / "fixtures" / "pixel_geometry" / "pixel_fold_diagnostic_16x16.png"
SIZE = 16
HINGE_X = 8            # same hinge boundary as the frozen hinge-fold and artwork-fold trials
FAR_SEGMENT_CELLS = SIZE - HINGE_X  # 8 cells beyond the hinge
REQUIRED_RISE = 5.0     # < FAR_SEGMENT_CELLS -- a real, non-90-degree, non-trivial ramp

CHECKS: list[bool] = []


def report(name: str, ok: bool, message: str = "") -> bool:
    suffix = f" — {message}" if message else ""
    print(f"[PIXEL_GEOMETRY_DECLARED_ANGLE_RAMP][{name}] {'TRUE' if ok else 'FALSE'}{suffix}")
    CHECKS.append(ok)
    return ok


def close(a: float, b: float, tol: float = 1e-9) -> bool:
    return abs(a - b) <= tol


def build_footprint_from_art(image: Image.Image) -> dict:
    payload = [[image.getpixel((x, row)) for x in range(SIZE)] for row in range(SIZE)]
    return build_footprint(SIZE, SIZE, payload)


def edges_with_addresses(compiled: dict) -> list[tuple[tuple[int, int], tuple[int, int], float]]:
    width, height = compiled["footprint_width"], compiled["footprint_height"]
    positions = compiled["positions"]

    def dist(a: int, b: int) -> float:
        ax, ay, az = positions[a]
        bx, by, bz = positions[b]
        return ((ax - bx) ** 2 + (ay - by) ** 2 + (az - bz) ** 2) ** 0.5

    edges = []
    for r in range(height + 1):
        for x in range(width):
            a, b = (x, r), (x + 1, r)
            edges.append((a, b, dist(corner_index(*a, width), corner_index(*b, width))))
    for x in range(width + 1):
        for r in range(height):
            a, b = (x, r), (x, r + 1)
            edges.append((a, b, dist(corner_index(*a, width), corner_index(*b, width))))
    return edges


def artwork_deformation_report(
    compiled: dict, uv_map: dict[tuple[int, int], tuple[float, float]], *, tol: float = 1e-9
) -> list[dict]:
    flagged = []
    for a, b, geometric_length in edges_with_addresses(compiled):
        ua, va = uv_map[a]
        ub, vb = uv_map[b]
        uv_span = ((ua - ub) ** 2 + (va - vb) ** 2) ** 0.5
        if not close(geometric_length, 1.0, tol):
            flagged.append(
                {
                    "edge": (a, b),
                    "geometric_length": geometric_length,
                    "uv_span": uv_span,
                    "stretch_factor": geometric_length / 1.0,
                }
            )
    return flagged


def main() -> int:
    # --- THE MATH, FIRST, BEFORE ANY GEOMETRY -----------------------------
    # A grid of (num_cells, required_rise) pairs, each checked against the
    # closed form independently: the solved run/rise must land exactly on
    # run^2 + rise^2 = chain_length^2, and the solved angle must reproduce
    # that same rise via chain_length*sin(angle).
    math_ok = True
    for num_cells, rise in [(8, 5.0), (8, 0.0), (8, 8.0), (1, 1.0), (16, 9.5), (3, 1.5)]:
        solution = solve_ramp_run_and_angle(num_cells, rise)
        chain_length = num_cells * 1.0
        on_circle = close(solution.run ** 2 + rise ** 2, chain_length ** 2, tol=1e-9)
        angle_reproduces_rise = close(chain_length * math.sin(math.radians(solution.angle_degrees)), rise, tol=1e-9)
        angle_reproduces_run = close(chain_length * math.cos(math.radians(solution.angle_degrees)), solution.run, tol=1e-9)
        if not (on_circle and angle_reproduces_rise and angle_reproduces_run):
            math_ok = False
    report("RAMP_MATH_SOLUTIONS_LAND_EXACTLY_ON_THE_METRIC_CIRCLE", math_ok)

    infeasible_rejected = True
    for num_cells, rise in [(8, 8.001), (1, 1.5), (3, 100.0)]:
        try:
            solve_ramp_run_and_angle(num_cells, rise)
            infeasible_rejected = False
        except ValueError:
            pass
    report("RAMP_MATH_REJECTS_RISE_BEYOND_CHAIN_LENGTH", infeasible_rejected)

    solved = solve_ramp_run_and_angle(FAR_SEGMENT_CELLS, REQUIRED_RISE)
    report(
        "WORKED_EXAMPLE_SOLVED_BEFORE_EMBEDDING",
        close(solved.chain_length, float(FAR_SEGMENT_CELLS)),
        f"num_cells={FAR_SEGMENT_CELLS} rise={REQUIRED_RISE} -> angle={solved.angle_degrees:.6f} deg, run={solved.run:.6f}",
    )

    # --- THE EMBEDDING, GENERALIZING THE FROZEN 90-DEGREE HINGE FOLD -----
    if not ART_PATH.exists():
        report("DIAGNOSTIC_ART_AVAILABLE", False, f"missing {ART_PATH} -- run tools/generate_pixel_geometry_diagnostic_art.py first")
        print("[PIXEL_GEOMETRY_DECLARED_ANGLE_RAMP][ALL_GATES] false")
        return 1

    art_image = Image.open(ART_PATH).convert("RGB")
    footprint = build_footprint_from_art(art_image)
    flat_uv = footprint_corner_uvs(footprint)

    # At 90 degrees, the generalized ramp fold must reproduce the frozen
    # hinge-fold function's output EXACTLY (both formulas compared
    # directly, not just trusted).
    frozen_positions = embed_hard_90_degree_hinge_fold(footprint, hinge_corner_x=HINGE_X)
    ramp_at_90 = embed_declared_angle_ramp_fold(footprint, hinge_corner_x=HINGE_X, angle_degrees=90.0)
    reproduces_frozen = all(
        all(close(a, b) for a, b in zip(frozen_positions[addr], ramp_at_90[addr])) for addr in frozen_positions
    )
    report("RAMP_FOLD_AT_90_DEGREES_REPRODUCES_FROZEN_HINGE_FOLD_EXACTLY", reproduces_frozen)

    # The actual worked-example ramp: solved angle, not a guessed one.
    ramp_positions = embed_declared_angle_ramp_fold(footprint, hinge_corner_x=HINGE_X, angle_degrees=solved.angle_degrees)
    ramp_compiled = compile_footprint(footprint, ramp_positions, embedding_id=EMBEDDING_DECLARED_ANGLE_RAMP_FOLD)
    ramp_uv = footprint_corner_uvs(footprint)

    ramp_edges = edge_lengths(ramp_compiled)
    report(
        "RAMP_ALL_CELL_EDGES_REMAIN_1_0",
        all(close(length, 1.0) for length in ramp_edges),
        f"min={min(ramp_edges):.9f} max={max(ramp_edges):.9f} n={len(ramp_edges)}",
    )
    report("RAMP_ARTWORK_UVS_UNCHANGED", uvs_are_identical(flat_uv, ramp_uv))
    report(
        "RAMP_SOURCE_ADJACENCY_UNCHANGED",
        compiled_adjacency_matches_source(footprint, ramp_compiled["compiled_adjacency"]),
    )
    report(
        "RAMP_ALL_CELLS_PRESERVED_1_TO_1",
        len(ramp_compiled["dispositions"]) == SIZE * SIZE
        and all(v == "PRESERVED_1_TO_1" for v in ramp_compiled["dispositions"].values()),
    )

    ramp_deformations = artwork_deformation_report(ramp_compiled, ramp_uv)
    report(
        "RAMP_IS_EMBEDDING_NOT_ARTWORK_DEFORMATION",
        len(ramp_deformations) == 0,
        f"flagged={len(ramp_deformations)}" if ramp_deformations else "",
    )

    # The far endpoint (hinge_corner_x=HINGE_X, x=SIZE) must actually land
    # at the solved (run, rise) relative to the hinge, for every row --
    # independently recomputed, not just trusted from the embedding call.
    endpoint_matches_solution = True
    for row in range(footprint["height"] + 1):
        hinge_pos = ramp_positions[(HINGE_X, row)]
        far_pos = ramp_positions[(SIZE, row)]
        dx = far_pos[0] - hinge_pos[0]
        dy = far_pos[1] - hinge_pos[1]
        if not (close(dx, solved.run) and close(dy, REQUIRED_RISE)):
            endpoint_matches_solution = False
    report("RAMP_FAR_ENDPOINT_MATCHES_SOLVED_RUN_AND_RISE", endpoint_matches_solution)

    # --- TOXIC: force an (run, rise) pair OFF the metric circle -----------
    # Local to this gate only, never a production embedding: fix BOTH run
    # and rise at the full chain length simultaneously (run=rise=
    # FAR_SEGMENT_CELLS), which is impossible without stretch since
    # run^2 + rise^2 would have to equal 2 * chain_length^2, not
    # chain_length^2.
    toxic_positions: dict[tuple[int, int], tuple[float, float, float]] = {}
    for x, r in ramp_positions:
        if x <= HINGE_X:
            toxic_positions[(x, r)] = (float(x), 0.0, float(r))
        else:
            offset = x - HINGE_X
            toxic_positions[(x, r)] = (float(HINGE_X) + offset, float(offset), float(r))
    toxic_compiled = compile_footprint(footprint, toxic_positions, embedding_id="toxic_off_circle_run_and_rise")
    toxic_uv = footprint_corner_uvs(footprint)
    toxic_edges = edge_lengths(toxic_compiled)

    expected_stretch_factor = math.sqrt(2.0)
    stretched = [length for length in toxic_edges if not close(length, 1.0)]
    measured_stretch_factor = max(stretched) if stretched else float("nan")
    report(
        "TOXIC_OFF_CIRCLE_ENDPOINT_STRETCHES_EDGES",
        bool(stretched) and close(measured_stretch_factor, expected_stretch_factor, tol=1e-6),
        f"measured={measured_stretch_factor:.9f} expected={expected_stretch_factor:.9f}",
    )
    toxic_deformations = artwork_deformation_report(toxic_compiled, toxic_uv)
    toxic_uv_nominal = all(
        close(d["uv_span"], 1.0 / SIZE) or close(d["uv_span"], 0.0) for d in toxic_deformations
    )
    report(
        "TOXIC_OFF_CIRCLE_ENDPOINT_DETECTED_AS_ARTWORK_DEFORMATION",
        len(toxic_deformations) > 0 and toxic_uv_nominal,
        f"flagged={len(toxic_deformations)}",
    )

    all_ok = all(CHECKS)
    print(f"[PIXEL_GEOMETRY_DECLARED_ANGLE_RAMP][ALL_GATES] {'true' if all_ok else 'false'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
