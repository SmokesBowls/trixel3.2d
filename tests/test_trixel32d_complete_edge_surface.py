from __future__ import annotations

import hashlib
import io
import json
import unittest
from collections import defaultdict
from pathlib import Path
from typing import Any

from PIL import Image

from trixel.trixel32d_request_drop_consumer import canonical_response_bytes
from trixel.trixel32d_surface_consumer import consume_surface_request_packet

from test_trixel32d_image_ingress import (
    RECIPE_ROOT,
    TEXEL_FIXTURE,
    decode_pinned,
    request_around,
)
from test_trixel32d_connected_surface import connected_request

REPO_ROOT = Path(__file__).resolve().parents[1]
PINNED_LATTICE_SHA256 = "fc867ab05c23236df8fd8bfa37d8a7be2619def0aba77606eecbe37965807d9d"
PINNED_CONNECTED_SHA256 = "86d8b22013c03ca6b20dcbebeb5240309128d3d6b7258c3236aeca60a6459139"
LATTICE_SURFACE_ID = "t32dsurface_245be4a987cf6fd9"
CONNECTED_SURFACE_ID = "t32dsurface_f024725d200e470c"
COMPLETE_EDGE_POLICY = "HEIGHT_FIELD_COMPLETE_EDGE_CONNECTED_SURFACE"
THICKNESS = 0.5
LAYERS = 6
WELD = 6  # rounding places for coordinate welding


def complete_edge_request(decoded: dict[str, Any]) -> dict[str, Any]:
    request = request_around(decoded)
    request["construction"]["topology_policy"] = COMPLETE_EDGE_POLICY
    request["gap_fill"]["mode"] = "COMPLETE_EDGE_SLAB"
    request["gap_fill"]["adjacency_policy"] = "SHARED_COMPLETE_EDGES"
    return request


def build_complete_edge() -> tuple[dict[str, Any], dict[str, Any]]:
    decoded = decode_pinned()
    built = consume_surface_request_packet(
        complete_edge_request(decoded), recipe_root=RECIPE_ROOT
    )
    return decoded, built


def heights_grid(decoded: dict[str, Any]) -> list[list[int]]:
    grid = [[0] * 16 for _ in range(16)]
    for cell in decoded["pixel_field_data"]:
        grid[cell["field_y"]][cell["field_x"]] = round(cell["elevation"] * LAYERS)
    return grid


def cell_height(grid: list[list[int]], x: int, y: int) -> int | None:
    if x < 0 or y < 0 or x >= 16 or y >= 16:
        return None
    return grid[y][x]


def lattice_breakpoints(grid: list[list[int]], i: int, j: int) -> set[int]:
    values = set()
    for cx, cy in ((i - 1, j - 1), (i, j - 1), (i - 1, j), (i, j)):
        value = cell_height(grid, cx, cy)
        if value is not None:
            values.add(value)
    return values


def pinch_edge_non_manifold_inventory(grid: list[list[int]]) -> dict[tuple[int, int], tuple[float, float]]:
    """Independent inventory: lattice point -> open (low, high) pinch interval."""
    result: dict[tuple[int, int], tuple[float, float]] = {}
    for j in range(1, 16):
        for i in range(1, 16):
            a = grid[j - 1][i - 1]
            b = grid[j - 1][i]
            c = grid[j][i]
            d = grid[j][i - 1]
            if min(a, c) > max(b, d):
                result[(i, j)] = (float(max(b, d)), float(min(a, c)))
            elif min(b, d) > max(a, c):
                result[(i, j)] = (float(max(a, c)), float(min(b, d)))
    return result


def lattice_position(i: int, j: int) -> tuple[float, float]:
    """Local (x, z) of lattice point: cell centers at (x-7.5, -(y-7.5))."""
    return (i - 8.0, -(j - 8.0))


class MeldedMesh:
    def __init__(self, built: dict[str, Any]):
        raw_positions = built["geometry"]["positions"]
        raw_indices = built["geometry"]["indices"]
        welded: dict[tuple[float, ...], int] = {}
        self.vertex_map: list[int] = []
        self.points: list[tuple[float, ...]] = []
        for p in raw_positions:
            key = tuple(round(c, WELD) for c in p)
            if key not in welded:
                welded[key] = len(welded)
                self.points.append(key)
            self.vertex_map.append(welded[key])
        self.triangles: list[tuple[int, int, int]] = []
        for t in range(0, len(raw_indices), 3):
            self.triangles.append(tuple(
                self.vertex_map[raw_indices[t + k]] for k in range(3)
            ))
        self.directed: dict[tuple[int, int], int] = defaultdict(int)
        self.undirected: dict[tuple[int, int], int] = defaultdict(int)
        for a, b, c in self.triangles:
            for u, v in ((a, b), (b, c), (c, a)):
                self.directed[(u, v)] += 1
                self.undirected[(min(u, v), max(u, v))] += 1


class CompleteEdgeCase(unittest.TestCase):
    decoded: dict[str, Any]
    built: dict[str, Any]
    mesh: MeldedMesh
    grid: list[list[int]]

    @classmethod
    def setUpClass(cls):
        cls.decoded, cls.built = build_complete_edge()
        assert cls.built.get("status") == "BUILT", cls.built.get("errors")
        cls.mesh = MeldedMesh(cls.built)
        cls.grid = heights_grid(cls.decoded)


class TestIdentity(CompleteEdgeCase):
    def test_distinct_surface_and_payload_identity(self):
        self.assertEqual(self.built["topology_policy"], COMPLETE_EDGE_POLICY)
        self.assertNotIn(self.built["surface_id"], (LATTICE_SURFACE_ID, CONNECTED_SURFACE_ID))
        sha = hashlib.sha256(canonical_response_bytes(self.built)).hexdigest()
        self.assertNotIn(sha, (PINNED_LATTICE_SHA256, PINNED_CONNECTED_SHA256))

    def test_existing_policies_stay_byte_identical(self):
        decoded = decode_pinned()
        lattice = consume_surface_request_packet(request_around(decoded), recipe_root=RECIPE_ROOT)
        self.assertEqual(
            hashlib.sha256(canonical_response_bytes(lattice)).hexdigest(),
            PINNED_LATTICE_SHA256,
        )
        connected = consume_surface_request_packet(connected_request(decoded), recipe_root=RECIPE_ROOT)
        self.assertEqual(
            hashlib.sha256(canonical_response_bytes(connected)).hexdigest(),
            PINNED_CONNECTED_SHA256,
        )

    def test_deterministic_byte_identical_builds(self):
        _, second = build_complete_edge()
        self.assertEqual(canonical_response_bytes(self.built), canonical_response_bytes(second))


class TestExactPreservation(CompleteEdgeCase):
    def test_top_colors_and_heights_exact(self):
        image = Image.open(io.BytesIO(TEXEL_FIXTURE.read_bytes()))
        image.load()
        colors = self.built["geometry"]["colors"]
        for cell_range in self.built["cell_geometry_ranges"]:
            tops = [s for s in cell_range["surfaces"] if s["role"] == "PRIMARY_PIXEL_FACE"]
            self.assertEqual(len(tops), 1)
            source = image.getpixel((cell_range["field_x"], cell_range["field_y"]))
            for vertex in range(tops[0]["vertex_start"], tops[0]["vertex_start"] + tops[0]["vertex_count"]):
                self.assertEqual(
                    [round(component * 255.0) for component in colors[vertex]],
                    [source[0], source[1], source[2], 255],
                )
            expected_height = self.grid[cell_range["field_y"]][cell_range["field_x"]]
            self.assertEqual(cell_range["world_cell"]["world_cell_y"], expected_height)


class TestWeldedTopology(CompleteEdgeCase):
    def expected_pinch_edges(self) -> set[tuple[int, int]]:
        inventory = pinch_edge_non_manifold_inventory(self.grid)
        point_index = {p: idx for idx, p in enumerate(self.mesh.points)}
        edges: set[tuple[int, int]] = set()
        for (i, j), (low, high) in inventory.items():
            x, z = lattice_position(i, j)
            cuts = sorted(
                {low, high}
                | {float(v) for v in lattice_breakpoints(self.grid, i, j) if low < v < high}
            )
            for bottom, top in zip(cuts, cuts[1:]):
                p_bottom = (round(x, WELD), round(bottom, WELD), round(z, WELD))
                p_top = (round(x, WELD), round(top, WELD), round(z, WELD))
                if p_bottom in point_index and p_top in point_index:
                    u, v = point_index[p_bottom], point_index[p_top]
                    edges.add((min(u, v), max(u, v)))
        return edges

    def test_single_connected_component(self):
        parent = list(range(len(self.mesh.points)))

        def find(a: int) -> int:
            while parent[a] != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a

        for tri in self.mesh.triangles:
            for other in tri[1:]:
                ra, rb = find(tri[0]), find(other)
                if ra != rb:
                    parent[ra] = rb
        self.assertEqual(len({find(v) for v in range(len(self.mesh.points))}), 1)

    def test_edge_incidence_two_everywhere_except_inventoried_pinches(self):
        pinch_edges = self.expected_pinch_edges()
        self.assertGreater(len(pinch_edges), 0)
        fours = {e for e, n in self.mesh.undirected.items() if n == 4}
        others = {e: n for e, n in self.mesh.undirected.items() if n not in (2, 4)}
        self.assertEqual(others, {}, "every edge must have incidence 2 or 4")
        self.assertEqual(fours, pinch_edges, "4-incidence must be exactly the pinch inventory")

    def test_directed_half_edges_balance_consistent_winding(self):
        for (u, v), count in self.mesh.undirected.items():
            forward_count = self.mesh.directed.get((u, v), 0)
            backward_count = self.mesh.directed.get((v, u), 0)
            self.assertEqual(forward_count + backward_count, count)
            self.assertEqual(forward_count, backward_count, f"unbalanced edge {(u, v)}")

    def test_no_duplicate_faces(self):
        seen = set()
        for tri in self.mesh.triangles:
            key = frozenset(tri)
            self.assertEqual(len(key), 3)
            self.assertNotIn(key, seen)
            seen.add(key)

    def test_no_degenerate_triangles(self):
        for a, b, c in self.mesh.triangles:
            pa, pb, pc = self.mesh.points[a], self.mesh.points[b], self.mesh.points[c]
            ab = [pb[k] - pa[k] for k in range(3)]
            ac = [pc[k] - pa[k] for k in range(3)]
            cross = [
                ab[1] * ac[2] - ab[2] * ac[1],
                ab[2] * ac[0] - ab[0] * ac[2],
                ab[0] * ac[1] - ab[1] * ac[0],
            ]
            self.assertGreater(sum(c * c for c in cross), 1e-12)

    def test_zero_t_junctions(self):
        """No welded vertex lies strictly inside any welded edge segment."""
        cell_of: dict[tuple[int, int, int], list[int]] = defaultdict(list)
        for idx, p in enumerate(self.mesh.points):
            cell_of[(int(p[0] * 2) if False else round(p[0], 3), round(p[1], 3), round(p[2], 3))].append(idx)
        # Spatial hash on quantized segment bounding boxes at 0.25 resolution.
        def boxes(p, q):
            lo = [min(p[k], q[k]) for k in range(3)]
            hi = [max(p[k], q[k]) for k in range(3)]
            import itertools
            ranges = [range(int(lo[k] * 4) - 1, int(hi[k] * 4) + 2) for k in range(3)]
            return itertools.product(*ranges)

        vertex_hash: dict[tuple[int, int, int], list[int]] = defaultdict(list)
        for idx, p in enumerate(self.mesh.points):
            vertex_hash[tuple(int(c * 4) for c in p)].append(idx)

        violations = []
        for (u, v) in self.mesh.undirected:
            p, q = self.mesh.points[u], self.mesh.points[v]
            length_sq = sum((q[k] - p[k]) ** 2 for k in range(3))
            for box in boxes(p, q):
                for idx in vertex_hash.get(box, ()):
                    if idx in (u, v):
                        continue
                    w = self.mesh.points[idx]
                    dot = sum((w[k] - p[k]) * (q[k] - p[k]) for k in range(3))
                    t = dot / length_sq
                    if not 1e-9 < t < 1.0 - 1e-9:
                        continue
                    closest = [p[k] + t * (q[k] - p[k]) for k in range(3)]
                    distance_sq = sum((w[k] - closest[k]) ** 2 for k in range(3))
                    if distance_sq < 1e-12:
                        violations.append((u, v, idx))
        self.assertEqual(violations, [])


class TestWallIntervalInventory(CompleteEdgeCase):
    def test_emitted_wall_chains_match_independent_inventory(self):
        positions = self.built["geometry"]["positions"]
        base = min(min(row) for row in self.grid) - THICKNESS
        direction_delta = {"-field_y": (0, -1), "+field_x": (1, 0), "+field_y": (0, 1), "-field_x": (-1, 0)}
        corner_lattices = {
            "-field_y": lambda x, y: ((x, y), (x + 1, y)),
            "+field_x": lambda x, y: ((x + 1, y), (x + 1, y + 1)),
            "+field_y": lambda x, y: ((x, y + 1), (x + 1, y + 1)),
            "-field_x": lambda x, y: ((x, y), (x, y + 1)),
        }
        walls_checked = 0
        for cell_range in self.built["cell_geometry_ranges"]:
            x, y = cell_range["field_x"], cell_range["field_y"]
            top = float(self.grid[y][x])
            for surface in cell_range["surfaces"]:
                face = surface["face"]
                if face not in direction_delta:
                    continue
                dx, dy = direction_delta[face]
                other = cell_height(self.grid, x + dx, y + dy)
                low = base if other is None else float(other)
                self.assertTrue(other is None or other < top)
                left_lattice, right_lattice = corner_lattices[face](x, y)
                expected = {}
                for side, lattice in (("left", left_lattice), ("right", right_lattice)):
                    cuts = sorted(
                        float(v) for v in lattice_breakpoints(self.grid, *lattice)
                        if low < v < top
                    )
                    expected[side] = [low] + cuts + [top]
                verts = [
                    positions[v]
                    for v in range(surface["vertex_start"], surface["vertex_start"] + surface["vertex_count"])
                ]
                lx, lz = lattice_position(*left_lattice)
                rx, rz = lattice_position(*right_lattice)
                emitted_left = sorted(
                    round(v[1], WELD) for v in verts
                    if abs(v[0] - lx) < 1e-9 and abs(v[2] - lz) < 1e-9
                )
                emitted_right = sorted(
                    round(v[1], WELD) for v in verts
                    if abs(v[0] - rx) < 1e-9 and abs(v[2] - rz) < 1e-9
                )
                self.assertEqual(emitted_left, [round(v, WELD) for v in expected["left"]], (x, y, face))
                self.assertEqual(emitted_right, [round(v, WELD) for v in expected["right"]], (x, y, face))
                walls_checked += 1
        self.assertEqual(walls_checked, sum(
            1 for s in (
                surface
                for cr in self.built["cell_geometry_ranges"]
                for surface in cr["surfaces"]
            ) if s["face"] in direction_delta
        ))
        self.assertGreater(walls_checked, 300)


class TestDeclarationFailClosed(CompleteEdgeCase):
    def test_mixed_declarations_reject(self):
        request = complete_edge_request(decode_pinned())
        request["gap_fill"]["mode"] = "CONNECTED_SLAB"
        built = consume_surface_request_packet(request, recipe_root=RECIPE_ROOT)
        self.assertEqual(built.get("status"), "REJECTED")
        self.assertTrue(any("gap_fill.mode" in e for e in built["errors"]))

        request = complete_edge_request(decode_pinned())
        request["gap_fill"]["adjacency_policy"] = "SHARED_EDGE_STITCHED"
        built = consume_surface_request_packet(request, recipe_root=RECIPE_ROOT)
        self.assertEqual(built.get("status"), "REJECTED")
        self.assertTrue(any("gap_fill.adjacency_policy" in e for e in built["errors"]))


if __name__ == "__main__":
    unittest.main()
