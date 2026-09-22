#!/usr/bin/env python3
"""Closed cylindrical wrap proof: can an entire pixel-art sheet become a
closed 3D object while every pixel keeps its intrinsic footprint?

flat                         PROVEN (gate_pixel_geometry_flat_footprint_v1)
rigid transform              PROVEN (gate_pixel_geometry_rigid_embedding_v1)
hard 90 degree fold          PROVEN (gate_pixel_geometry_hinge_fold_v1, frozen)
pixel art fold vs stretch    PROVEN (gate_pixel_geometry_artwork_fold_v1)
cylindrical closed wrap      THIS GATE

The cylinder is not "bend the artwork until it looks round." It is a
sequence of exact folds: one declared hinge per column boundary, angle
360/N degrees, radius DERIVED from the declared 1.0 cell metric
(radius = 1 / (2*sin(pi/N))) so every column-to-column chord is exactly
1.0 -- never a radius chosen first that forces the cells to stretch to
meet it. The same 16x16 diagnostic artwork used by the fold-vs-stretch
proof is reused unchanged, so the comparison is: same source pixels, same
UV addresses, same cell metric, only the embedding changes.

A green result means all of:
  - every cell edge (horizontal wrap-steps AND vertical row-steps) is
    exactly 1.0
  - the artwork's UV addresses never moved (still address-only, still
    identical to the flat footprint's)
  - the closing seam between column 0 and column N-1 is an EXPLICIT
    declared adjacency (adjacency_v1.closed_wrap_seam_adjacency()), never
    inferred from the corner positions merely coinciding
  - a deliberately wrong radius (toxic, local to this gate only, never a
    production embedding) is correctly measured as stretching edges past
    1.0 and flagged as artwork deformation
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
from trixel.pixel_geometry.adjacency_v1 import (
    closed_wrap_seam_adjacency,
    compiled_adjacency_matches_closed_wrap,
    no_proximity_derived_adjacency,
    source_adjacency,
)
from trixel.pixel_geometry.artwork_mapping_v1 import footprint_corner_uvs, uvs_are_identical
from trixel.pixel_geometry.compiler_v1 import compile_closed_wrap_footprint, compile_footprint, positions_by_cell_center
from trixel.pixel_geometry.contracts_v1 import EMBEDDING_CYLINDRICAL_CLOSED_WRAP
from trixel.pixel_geometry.embedding_v1 import embed_cylindrical_closed_wrap

ART_PATH = REPO_ROOT / "fixtures" / "pixel_geometry" / "pixel_fold_diagnostic_16x16.png"
SIZE = 16

# Deliberately wrong toxic radius factor: 15% larger than the exact chord
# radius, chosen only to be unambiguously wrong -- not derived from any
# metric, exactly the mistake this trial's law forbids in production.
TOXIC_RADIUS_FACTOR = 1.15

CHECKS: list[bool] = []


def report(name: str, ok: bool, message: str = "") -> bool:
    suffix = f" — {message}" if message else ""
    print(f"[PIXEL_GEOMETRY_CYLINDRICAL_WRAP][{name}] {'TRUE' if ok else 'FALSE'}{suffix}")
    CHECKS.append(ok)
    return ok


def close(a: float, b: float, tol: float = 1e-9) -> bool:
    return abs(a - b) <= tol


def build_footprint_from_art(image: Image.Image) -> dict:
    payload = [[image.getpixel((x, row)) for x in range(SIZE)] for row in range(SIZE)]
    return build_footprint(SIZE, SIZE, payload)


def horizontal_and_vertical_edges(compiled: dict) -> tuple[list[float], list[float]]:
    width, height = compiled["footprint_width"], compiled["footprint_height"]
    positions = compiled["positions"]

    def dist(a: int, b: int) -> float:
        ax, ay, az = positions[a]
        bx, by, bz = positions[b]
        return ((ax - bx) ** 2 + (ay - by) ** 2 + (az - bz) ** 2) ** 0.5

    horizontal = [
        dist(corner_index(x, r, width), corner_index(x + 1, r, width))
        for r in range(height + 1)
        for x in range(width)
    ]
    vertical = [
        dist(corner_index(x, r, width), corner_index(x, r + 1, width))
        for x in range(width + 1)
        for r in range(height)
    ]
    return horizontal, vertical


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
    """Same detector as gate_pixel_geometry_artwork_fold_v1.py: an edge is
    flagged when its realized geometric length diverges from the declared
    1.0 while its UV interval stayed the nominal, address-only span."""
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
    if not ART_PATH.exists():
        report("DIAGNOSTIC_ART_AVAILABLE", False, f"missing {ART_PATH} -- run tools/generate_pixel_geometry_diagnostic_art.py first")
        print("[PIXEL_GEOMETRY_CYLINDRICAL_WRAP][ALL_GATES] false")
        return 1

    art_image = Image.open(ART_PATH).convert("RGB")
    footprint = build_footprint_from_art(art_image)
    width = footprint["width"]

    flat_uv = footprint_corner_uvs(footprint)

    # --- B: CYLINDRICAL CLOSED WRAP ---------------------------------------
    positions = embed_cylindrical_closed_wrap(footprint)
    seam_adjacency = closed_wrap_seam_adjacency(footprint)
    compiled = compile_closed_wrap_footprint(
        footprint, positions, embedding_id=EMBEDDING_CYLINDRICAL_CLOSED_WRAP, seam_adjacency=seam_adjacency
    )
    cylinder_uv = footprint_corner_uvs(footprint)

    report(
        "EVERY_CELL_STILL_PRESERVED_1_TO_1",
        len(compiled["dispositions"]) == SIZE * SIZE
        and all(v == "PRESERVED_1_TO_1" for v in compiled["dispositions"].values()),
    )

    horizontal, vertical = horizontal_and_vertical_edges(compiled)
    report(
        "EVERY_HORIZONTAL_CELL_EDGE_EQUALS_1_0",
        all(close(length, 1.0) for length in horizontal),
        f"min={min(horizontal):.9f} max={max(horizontal):.9f} n={len(horizontal)}",
    )
    report(
        "EVERY_VERTICAL_CELL_EDGE_EQUALS_1_0",
        all(close(length, 1.0) for length in vertical),
        f"min={min(vertical):.9f} max={max(vertical):.9f} n={len(vertical)}",
    )

    report("ARTWORK_UVS_UNCHANGED_FROM_FLAT_FOOTPRINT", uvs_are_identical(flat_uv, cylinder_uv))
    cylinder_deformations = artwork_deformation_report(compiled, cylinder_uv)
    report(
        "NO_PIXEL_STRETCH",
        len(cylinder_deformations) == 0,
        f"flagged={len(cylinder_deformations)}" if cylinder_deformations else "",
    )

    # Independently recompute the embedding's own formula, position by
    # position, and compare against what embed_cylindrical_closed_wrap()
    # actually returned -- not just trusting its internals.
    angle_increment = 2.0 * math.pi / width
    radius = 1.0 / (2.0 * math.sin(math.pi / width))
    rotation_exact = True
    for x, r in positions:
        theta = x * angle_increment
        expected = (radius * math.sin(theta), radius * (1.0 - math.cos(theta)), float(r))
        actual = positions[(x, r)]
        if not all(close(a, b) for a, b in zip(expected, actual)):
            rotation_exact = False
    report("COLUMN_ROTATION_INCREMENT_IS_EXACT", rotation_exact)
    report(
        "TOTAL_WRAP_EQUALS_360_DEGREES",
        close(math.degrees(width * angle_increment), 360.0),
        f"got {math.degrees(width * angle_increment):.6f} degrees over {width} columns",
    )

    # Seam: explicitly declared adjacency, not proximity.
    seam_differs_from_cardinal = seam_adjacency != source_adjacency(footprint)
    report("SEAM_IS_EXPLICITLY_DECLARED", seam_differs_from_cardinal and compiled_adjacency_matches_closed_wrap(footprint, compiled["compiled_adjacency"]))
    first_last_neighbors = all(
        (width - 1, row) in seam_adjacency[(0, row)] and (0, row) in seam_adjacency[(width - 1, row)]
        for row in range(footprint["height"])
    )
    report("FIRST_AND_LAST_COLUMNS_ARE_DECLARED_NEIGHBORS", first_last_neighbors)

    seam_coincide = all(
        all(close(a, b) for a, b in zip(positions[(0, row)], positions[(width, row)]))
        for row in range(footprint["height"] + 1)
    )
    report("SEAM_CORNER_POSITIONS_COINCIDE_WITHIN_TOLERANCE", seam_coincide)

    centers = positions_by_cell_center(compiled)
    offenders = no_proximity_derived_adjacency(centers, seam_adjacency, proximity_tolerance=0.5)
    report(
        "NO_OTHER_ADJACENCY_CREATED_FROM_PROXIMITY",
        len(offenders) == 0,
        f"offenders={offenders}" if offenders else "",
    )

    report(
        "EVERY_PRIMITIVE_RETAINS_SOURCE_CELL_PROVENANCE",
        len(compiled["primitive_provenance"]) == SIZE * SIZE
        and all("cell_address" in prov for prov in compiled["primitive_provenance"])
        and all(
            prov["payload"] == footprint["payload"][prov["cell_address"][1]][prov["cell_address"][0]]
            for prov in compiled["primitive_provenance"]
        ),
    )

    positions_again = embed_cylindrical_closed_wrap(footprint)
    compiled_again = compile_closed_wrap_footprint(
        footprint, positions_again, embedding_id=EMBEDDING_CYLINDRICAL_CLOSED_WRAP, seam_adjacency=closed_wrap_seam_adjacency(footprint)
    )
    report(
        "COMPILATION_IS_DETERMINISTIC",
        positions == positions_again
        and compiled["indices"] == compiled_again["indices"]
        and compiled["positions"] == compiled_again["positions"],
    )

    # --- C: TOXIC WRONG RADIUS (local to this gate only) -------------------
    toxic_radius = radius * TOXIC_RADIUS_FACTOR
    toxic_positions = {
        (x, r): (toxic_radius * math.sin(x * angle_increment), toxic_radius * (1.0 - math.cos(x * angle_increment)), float(r))
        for x, r in positions
    }
    toxic_compiled = compile_closed_wrap_footprint(
        footprint, toxic_positions, embedding_id="toxic_wrong_radius_cylinder", seam_adjacency=closed_wrap_seam_adjacency(footprint)
    )
    toxic_uv = footprint_corner_uvs(footprint)
    toxic_horizontal, _ = horizontal_and_vertical_edges(toxic_compiled)

    expected_wrong_chord = 2.0 * toxic_radius * math.sin(angle_increment / 2.0)
    measured_wrong_chord = max(toxic_horizontal)
    report(
        "TOXIC_WRONG_RADIUS_STRETCHES_EDGES_BEYOND_1_0",
        any(length > 1.0 + 1e-9 for length in toxic_horizontal),
        f"max={measured_wrong_chord:.9f}",
    )
    report(
        "TOXIC_WRONG_RADIUS_MEASURED_DISCREPANCY_REPORTED",
        close(measured_wrong_chord, expected_wrong_chord, tol=1e-6),
        f"measured={measured_wrong_chord:.9f} independently_expected={expected_wrong_chord:.9f} "
        f"declared_metric=1.0 discrepancy={measured_wrong_chord - 1.0:.9f}",
    )
    toxic_deformations = artwork_deformation_report(toxic_compiled, toxic_uv)
    toxic_uv_nominal = all(
        close(d["uv_span"], 1.0 / SIZE) or close(d["uv_span"], 0.0) for d in toxic_deformations
    )
    report(
        "TOXIC_WRONG_RADIUS_DETECTED_AS_ARTWORK_DEFORMATION",
        len(toxic_deformations) > 0 and toxic_uv_nominal,
        f"flagged={len(toxic_deformations)}",
    )

    all_ok = all(CHECKS)
    print(f"[PIXEL_GEOMETRY_CYLINDRICAL_WRAP][ALL_GATES] {'true' if all_ok else 'false'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
