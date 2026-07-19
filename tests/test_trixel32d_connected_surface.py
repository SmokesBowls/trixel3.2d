from __future__ import annotations

import io
import json
import unittest
from typing import Any

from PIL import Image

from trixel.trixel32d_surface_consumer import consume_surface_request_packet

from test_trixel32d_image_ingress import (
    RECIPE_ROOT,
    TEXEL_FIXTURE,
    decode_pinned,
    request_around,
)


def connected_request(decoded: dict[str, Any]) -> dict[str, Any]:
    request = request_around(decoded)
    request["construction"]["topology_policy"] = "HEIGHT_FIELD_CONNECTED_SURFACE"
    request["gap_fill"]["mode"] = "CONNECTED_SLAB"
    request["gap_fill"]["adjacency_policy"] = "SHARED_EDGE_STITCHED"
    return request


def build_connected() -> tuple[dict[str, Any], dict[str, Any]]:
    decoded = decode_pinned()
    built = consume_surface_request_packet(
        connected_request(decoded), recipe_root=RECIPE_ROOT
    )
    return decoded, built


def build_lattice() -> tuple[dict[str, Any], dict[str, Any]]:
    decoded = decode_pinned()
    built = consume_surface_request_packet(
        request_around(decoded), recipe_root=RECIPE_ROOT
    )
    return decoded, built


def heights_by_key(decoded: dict[str, Any]) -> dict[tuple[int, int], int]:
    return {
        (cell["field_x"], cell["field_y"]): round(cell["elevation"] * 6)
        for cell in decoded["pixel_field_data"]
    }


def quad_key(positions: list[list[float]], surface: dict[str, Any]) -> list[tuple[float, ...]]:
    start = surface["vertex_start"]
    return [tuple(round(c, 6) for c in positions[v]) for v in range(start, start + 4)]


class TestConnectedSurfaceBuilds(unittest.TestCase):
    def test_builds_with_distinct_surface_identity(self):
        _, built = build_connected()
        self.assertEqual(built.get("status"), "BUILT", built.get("errors"))
        self.assertEqual(built["topology_policy"], "HEIGHT_FIELD_CONNECTED_SURFACE")
        _, lattice = build_lattice()
        self.assertEqual(built["request_id"], lattice["request_id"])
        self.assertNotEqual(built["surface_id"], lattice["surface_id"])

    def test_deterministic(self):
        _, first = build_connected()
        _, second = build_connected()
        self.assertEqual(
            json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True)
        )


class TestExactPreservation(unittest.TestCase):
    def test_top_face_colors_match_source_pixels_exactly(self):
        _, built = build_connected()
        image = Image.open(io.BytesIO(TEXEL_FIXTURE.read_bytes()))
        image.load()
        colors = built["geometry"]["colors"]
        top_count = 0
        for cell_range in built["cell_geometry_ranges"]:
            tops = [s for s in cell_range["surfaces"] if s["role"] == "PRIMARY_PIXEL_FACE"]
            self.assertEqual(len(tops), 1)
            top_count += 1
            source = image.getpixel((cell_range["field_x"], cell_range["field_y"]))
            for vertex in range(tops[0]["vertex_start"], tops[0]["vertex_start"] + 4):
                self.assertEqual(
                    [round(component * 255.0) for component in colors[vertex]],
                    [source[0], source[1], source[2], 255],
                )
        self.assertEqual(top_count, 256)

    def test_heights_identical_to_lattice_policy(self):
        decoded, built = build_connected()
        _, lattice = build_lattice()
        expected = heights_by_key(decoded)
        for policy_built in (built, lattice):
            for cell_range in policy_built["cell_geometry_ranges"]:
                key = (cell_range["field_x"], cell_range["field_y"])
                self.assertEqual(cell_range["world_cell"]["world_cell_y"], expected[key])


class TestStitchedFaceInventory(unittest.TestCase):
    def expected_wall_count(self, heights: dict[tuple[int, int], int]) -> int:
        walls = 0
        for (x, y), h in heights.items():
            for nx, ny in ((x, y - 1), (x + 1, y), (x, y + 1), (x - 1, y)):
                other = heights.get((nx, ny))
                if other is None or other < h:
                    walls += 1
        return walls

    def test_only_exposed_faces_exist(self):
        decoded, built = build_connected()
        heights = heights_by_key(decoded)
        faces = [s for r in built["cell_geometry_ranges"] for s in r["surfaces"]]
        tops = sum(1 for s in faces if s["face"] == "top")
        bottoms = sum(1 for s in faces if s["face"] == "bottom")
        walls = len(faces) - tops - bottoms
        self.assertEqual(tops, 256)
        self.assertEqual(bottoms, 256)
        self.assertEqual(walls, self.expected_wall_count(heights))
        self.assertEqual(len(built["geometry"]["positions"]), len(faces) * 4)
        self.assertEqual(len(built["geometry"]["indices"]), len(faces) * 6)

    def test_no_wall_between_equal_height_neighbors(self):
        decoded, built = build_connected()
        heights = heights_by_key(decoded)
        direction_of = {"-field_y": (0, -1), "+field_x": (1, 0), "+field_y": (0, 1), "-field_x": (-1, 0)}
        for cell_range in built["cell_geometry_ranges"]:
            key = (cell_range["field_x"], cell_range["field_y"])
            for surface in cell_range["surfaces"]:
                if surface["face"] in direction_of:
                    dx, dy = direction_of[surface["face"]]
                    other = heights.get((key[0] + dx, key[1] + dy))
                    self.assertTrue(
                        other is None or other < heights[key],
                        f"internal face at {key} toward {surface['face']}",
                    )

    def test_wall_spans_are_exact(self):
        decoded, built = build_connected()
        heights = heights_by_key(decoded)
        base = min(heights.values()) - 0.5
        positions = built["geometry"]["positions"]
        direction_of = {"-field_y": (0, -1), "+field_x": (1, 0), "+field_y": (0, 1), "-field_x": (-1, 0)}
        for cell_range in built["cell_geometry_ranges"]:
            key = (cell_range["field_x"], cell_range["field_y"])
            top_height = float(heights[key])
            for surface in cell_range["surfaces"]:
                if surface["face"] not in direction_of:
                    continue
                dx, dy = direction_of[surface["face"]]
                other = heights.get((key[0] + dx, key[1] + dy))
                expected_bottom = base if other is None else float(other)
                ys = [positions[v][1] for v in range(surface["vertex_start"], surface["vertex_start"] + 4)]
                self.assertAlmostEqual(max(ys), top_height, places=9)
                self.assertAlmostEqual(min(ys), expected_bottom, places=9)


class TestSlabCoherence(unittest.TestCase):
    """Welded-vertex topology: one watertight component, not 256 islands."""

    def welded_mesh(self, built: dict[str, Any]):
        positions = built["geometry"]["positions"]
        indices = built["geometry"]["indices"]
        welded: dict[tuple[float, ...], int] = {}
        vertex_map = []
        for p in positions:
            k = tuple(round(c, 6) for c in p)
            if k not in welded:
                welded[k] = len(welded)
            vertex_map.append(welded[k])
        triangles = [
            tuple(vertex_map[indices[t + i]] for i in range(3))
            for t in range(0, len(indices), 3)
        ]
        return len(welded), triangles

    def test_single_connected_component(self):
        _, built = build_connected()
        vertex_count, triangles = self.welded_mesh(built)
        parent = list(range(vertex_count))

        def find(a: int) -> int:
            while parent[a] != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a

        for tri in triangles:
            for other in tri[1:]:
                ra, rb = find(tri[0]), find(other)
                if ra != rb:
                    parent[ra] = rb
        components = {find(v) for v in range(vertex_count)}
        self.assertEqual(len(components), 1)

    def test_lattice_policy_stays_fragmented(self):
        _, lattice = build_lattice()
        vertex_count, triangles = self.welded_mesh(lattice)
        parent = list(range(vertex_count))

        def find(a: int) -> int:
            while parent[a] != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a

        for tri in triangles:
            for other in tri[1:]:
                ra, rb = find(tri[0]), find(other)
                if ra != rb:
                    parent[ra] = rb
        components = {find(v) for v in range(vertex_count)}
        self.assertGreater(len(components), 1)


class TestNoGapsAlongCellBoundaries(unittest.TestCase):
    """Every shared cell boundary is coordinate-coincident: no cracks or holes.

    Walls are full-edge quads, so vertical wall side edges may form exact
    collinear T-junction overlaps at corners where three heights meet; that is
    a declared property of this policy, not a gap. What must hold everywhere
    is segment coincidence: tops meet tops at equal heights, wall bottoms meet
    lower tops, wall tops meet their own cell top, and the slab base is
    continuous.
    """

    AXIS_OF = {"+field_x": (0, 1), "-field_x": (0, -1), "+field_y": (2, -1), "-field_y": (2, 1)}
    OPPOSITE = {"+field_x": "-field_x", "-field_x": "+field_x", "+field_y": "-field_y", "-field_y": "+field_y"}
    DELTA = {"+field_x": (1, 0), "-field_x": (-1, 0), "+field_y": (0, 1), "-field_y": (0, -1)}

    def setUp(self):
        self.decoded, self.built = build_connected()
        self.heights = heights_by_key(self.decoded)
        self.positions = self.built["geometry"]["positions"]
        self.by_key = {
            (r["field_x"], r["field_y"]): {s["face"]: s for s in r["surfaces"]}
            for r in self.built["cell_geometry_ranges"]
        }

    def edge_toward(self, surface: dict[str, Any], face_name: str) -> frozenset:
        axis, sign = self.AXIS_OF[face_name]
        verts = [
            self.positions[v]
            for v in range(surface["vertex_start"], surface["vertex_start"] + 4)
        ]
        extreme = max(v[axis] * sign for v in verts)
        return frozenset(
            tuple(round(c, 6) for c in v)
            for v in verts
            if abs(v[axis] * sign - extreme) < 1e-9
        )

    def horizontal_edge(self, surface: dict[str, Any], top: bool) -> frozenset:
        verts = [
            self.positions[v]
            for v in range(surface["vertex_start"], surface["vertex_start"] + 4)
        ]
        extreme = max(v[1] for v in verts) if top else min(v[1] for v in verts)
        return frozenset(
            tuple(round(c, 6) for c in v) for v in verts if abs(v[1] - extreme) < 1e-9
        )

    def test_every_cell_boundary_is_coincident(self):
        checked_pairs = 0
        for key, height in self.heights.items():
            faces = self.by_key[key]
            for face_name, (dx, dy) in self.DELTA.items():
                neighbor_key = (key[0] + dx, key[1] + dy)
                other = self.heights.get(neighbor_key)
                if other is None:
                    wall = faces[face_name]
                    self.assertEqual(
                        self.horizontal_edge(wall, top=True),
                        self.edge_toward(faces["top"], face_name),
                    )
                    self.assertEqual(
                        self.horizontal_edge(wall, top=False),
                        self.edge_toward(faces["bottom"], face_name),
                    )
                elif other == height:
                    self.assertNotIn(face_name, faces)
                    self.assertEqual(
                        self.edge_toward(faces["top"], face_name),
                        self.edge_toward(
                            self.by_key[neighbor_key]["top"], self.OPPOSITE[face_name]
                        ),
                    )
                elif other < height:
                    wall = faces[face_name]
                    self.assertEqual(
                        self.horizontal_edge(wall, top=True),
                        self.edge_toward(faces["top"], face_name),
                    )
                    self.assertEqual(
                        self.horizontal_edge(wall, top=False),
                        self.edge_toward(
                            self.by_key[neighbor_key]["top"], self.OPPOSITE[face_name]
                        ),
                    )
                else:
                    self.assertNotIn(face_name, faces)
                if other is not None:
                    self.assertEqual(
                        self.edge_toward(faces["bottom"], face_name),
                        self.edge_toward(
                            self.by_key[neighbor_key]["bottom"], self.OPPOSITE[face_name]
                        ),
                    )
                checked_pairs += 1
        self.assertEqual(checked_pairs, 16 * 16 * 4)


class TestFailClosedDeclarations(unittest.TestCase):
    def assert_rejected(self, request: dict[str, Any], needle: str) -> None:
        built = consume_surface_request_packet(request, recipe_root=RECIPE_ROOT)
        self.assertEqual(built.get("status"), "REJECTED")
        self.assertTrue(any(needle in e for e in built["errors"]), built["errors"])

    def test_unknown_topology_policy_rejects(self):
        request = connected_request(decode_pinned())
        request["construction"]["topology_policy"] = "HEIGHT_FIELD_SMOOTHED"
        self.assert_rejected(request, "construction.topology_policy must be one of")

    def test_connected_policy_with_lattice_gap_fill_rejects(self):
        request = connected_request(decode_pinned())
        request["gap_fill"]["mode"] = "PER_CELL_EXTRUSION"
        self.assert_rejected(request, "gap_fill.mode must be 'CONNECTED_SLAB'")

        request = connected_request(decode_pinned())
        request["gap_fill"]["adjacency_policy"] = "ALL_FACES_INDEPENDENT"
        self.assert_rejected(
            request, "gap_fill.adjacency_policy must be 'SHARED_EDGE_STITCHED'"
        )

    def test_lattice_policy_with_stitched_gap_fill_rejects(self):
        request = request_around(decode_pinned())
        request["gap_fill"]["adjacency_policy"] = "SHARED_EDGE_STITCHED"
        self.assert_rejected(
            request, "gap_fill.adjacency_policy must be 'ALL_FACES_INDEPENDENT'"
        )


if __name__ == "__main__":
    unittest.main()
