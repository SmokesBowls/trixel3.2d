#!/usr/bin/env python3
"""Trial 2 -- Rigid whole-footprint embedding proof (translate + rotate)."""
from __future__ import annotations

import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from trixel.pixel_geometry.addressing_v1 import build_footprint
from trixel.pixel_geometry.adjacency_v1 import compiled_adjacency_matches_source
from trixel.pixel_geometry.compiler_v1 import compile_footprint, edge_lengths
from trixel.pixel_geometry.embedding_v1 import embed_flat, embed_rigid
from trixel.pixel_geometry.contracts_v1 import EMBEDDING_RIGID

CHECKS: list[bool] = []


def report(name: str, ok: bool, message: str = "") -> bool:
    suffix = f" — {message}" if message else ""
    print(f"[PIXEL_GEOMETRY_RIGID][{name}] {'TRUE' if ok else 'FALSE'}{suffix}")
    CHECKS.append(ok)
    return ok


def close(a: float, b: float, tol: float = 1e-9) -> bool:
    return abs(a - b) <= tol


def main() -> int:
    labels = [["A", "B", "C", "D"], ["E", "F", "G", "H"], ["I", "J", "K", "L"], ["M", "N", "O", "P"]]
    footprint = build_footprint(4, 4, labels)
    local = embed_flat(footprint)
    flat_compiled = compile_footprint(footprint, local, embedding_id="flat_identity.v1")
    flat_edges = edge_lengths(flat_compiled)

    # Translation only.
    translated = embed_rigid(local, translation=(5.0, 2.0, -3.0))
    translated_compiled = compile_footprint(footprint, translated, embedding_id=EMBEDDING_RIGID)
    report(
        "TRANSLATION_PRESERVES_ADJACENCY",
        compiled_adjacency_matches_source(footprint, translated_compiled["compiled_adjacency"]),
    )
    report(
        "TRANSLATION_PRESERVES_EDGE_LENGTHS",
        all(close(a, b) for a, b in zip(flat_edges, edge_lengths(translated_compiled))),
    )
    expected = {addr: (p[0] + 5.0, p[1] + 2.0, p[2] - 3.0) for addr, p in local.items()}
    report(
        "TRANSLATION_MATCHES_DECLARED_TRANSFORM",
        all(all(close(a, b) for a, b in zip(expected[k], translated[k])) for k in expected),
    )

    # 90-degree rotation about Y, no translation.
    rotated = embed_rigid(local, rotation_axis="y", rotation_degrees=90.0)
    rotated_compiled = compile_footprint(footprint, rotated, embedding_id=EMBEDDING_RIGID)
    report(
        "ROTATION_PRESERVES_ADJACENCY",
        compiled_adjacency_matches_source(footprint, rotated_compiled["compiled_adjacency"]),
    )
    report(
        "ROTATION_PRESERVES_EDGE_LENGTHS",
        all(close(a, b) for a, b in zip(flat_edges, edge_lengths(rotated_compiled))),
    )
    theta = math.radians(90.0)
    cos_t, sin_t = math.cos(theta), math.sin(theta)
    expected_rot = {
        addr: (p[0] * cos_t + p[2] * sin_t, p[1], -p[0] * sin_t + p[2] * cos_t)
        for addr, p in local.items()
    }
    report(
        "ROTATION_MATCHES_DECLARED_TRANSFORM",
        all(all(close(a, b) for a, b in zip(expected_rot[k], rotated[k])) for k in expected_rot),
    )

    # Translation + rotation together.
    both = embed_rigid(local, translation=(1.0, 1.0, 1.0), rotation_axis="x", rotation_degrees=90.0)
    both_compiled = compile_footprint(footprint, both, embedding_id=EMBEDDING_RIGID)
    report(
        "COMBINED_TRANSFORM_PRESERVES_EDGE_LENGTHS",
        all(close(a, b) for a, b in zip(flat_edges, edge_lengths(both_compiled))),
    )

    # No topology decision emitted by any rigid embedding: same policy field.
    report(
        "NO_TOPOLOGY_DECISION_EMITTED",
        translated_compiled["topology_policy"] == rotated_compiled["topology_policy"] == "preserve_exact.v1",
    )

    # Toxic case: a genuinely NON-rigid transform (anisotropic scale) must
    # be caught by the edge-length check -- proving the check has teeth,
    # not just rubber-stamping whatever comes in.
    scaled = {addr: (p[0] * 2.0, p[1], p[2]) for addr, p in local.items()}
    scaled_compiled = compile_footprint(footprint, scaled, embedding_id="toxic_nonrigid_scale")
    scale_edges_match = all(close(a, b) for a, b in zip(flat_edges, edge_lengths(scaled_compiled)))
    report(
        "TOXIC_NONRIGID_SCALE_CORRECTLY_FAILS_METRIC_CHECK",
        not scale_edges_match,
        "a real anisotropic scale must NOT preserve edge lengths -- if this ever reads TRUE, the metric check itself is broken",
    )

    all_ok = all(CHECKS)
    print(f"[PIXEL_GEOMETRY_RIGID][ALL_GATES] {'true' if all_ok else 'false'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
