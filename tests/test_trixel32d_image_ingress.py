from __future__ import annotations

import copy
import hashlib
import io
import json
import unittest
from pathlib import Path
from typing import Any

from PIL import Image

from trixel.trixel32d_image_ingress import (
    ImageIngressError,
    decode_image_bytes_to_pixel_field,
)
from trixel.trixel32d_surface_consumer import consume_surface_request_packet

REPO_ROOT = Path(__file__).resolve().parents[1]
RECIPE_ROOT = REPO_ROOT / "recipes" / "terrain"
TEXEL_FIXTURE = REPO_ROOT / "fixtures" / "texel" / "texel_grass_tile_16x16.png"
TEXEL_PIN = REPO_ROOT / "fixtures" / "texel" / "texel_grass_tile_16x16.pin.json"

PIN = json.loads(TEXEL_PIN.read_text(encoding="utf-8"))
PINNED_SHA256 = PIN["sha256"]


def decode_pinned(**overrides: Any) -> dict[str, Any]:
    values: dict[str, Any] = {
        "expected_sha256": PINNED_SHA256,
        "terrain": "grass",
        "recipe": "default.generic",
        "elevation_policy": "LUMINANCE_BT709",
    }
    values.update(overrides)
    return decode_image_bytes_to_pixel_field(TEXEL_FIXTURE.read_bytes(), **values)


def synthetic_png(pixels: list[list[tuple[int, int, int, int]]]) -> bytes:
    height = len(pixels)
    width = len(pixels[0])
    image = Image.new("RGBA", (width, height))
    for y, row in enumerate(pixels):
        for x, rgba in enumerate(row):
            image.putpixel((x, y), rgba)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def request_around(decoded: dict[str, Any]) -> dict[str, Any]:
    """Wrap decoded pixel field in a complete proof request for the existing consumer."""
    body = json.dumps(decoded["pixel_field_data"], sort_keys=True).encode("utf-8")
    request_id = "t32dreq_" + hashlib.sha256(body).hexdigest()[:16]
    return {
        "packet_type": "trixel32d_surface_request",
        "identity": {
            "contract": "trixel32d_surface_request.v1",
            "packet_type": "trixel32d_surface_request",
            "request_id": request_id,
            "source_scene_id": "scene.texel_ingress_proof.001",
            "grid_facts_profile": "texel_image_pixel_field",
            "provenance": {
                "source_scene_id": "scene.texel_ingress_proof.001",
                "topology_artifact_id": "texel_image." + decoded["source_sha256"][:16],
                "metric_layout_artifact_id": "texel_ingress_proof.metric.001",
            },
        },
        "coordinate_space": "WORLD_FIELD_GRID_TO_LOCAL_Y_UP",
        "up_axis_policy": "MUST_BE_STANDARD_Y_UP_IN_PRIMARY_DIRECTION",
        "orientation": {
            "basis_authority": "VECTORS",
            "field_axis_binding": {
                "field_x_increases_along": "RIGHT",
                "field_y_increases_along": "FORWARD",
            },
            "tolerance": 0.0001,
            "vectors": {
                "right": [1.0, 0.0, 0.0],
                "forward": [0.0, 0.0, -1.0],
                "up": [0.0, 1.0, 0.0],
            },
        },
        "construction": {
            "appearance_policy": "RECIPE_REFERENCE",
            "ordering": "ROW_MAJOR",
            "topology_policy": "HEIGHT_FIELD_CELL_EXTRUSION",
        },
        "planar_config": {
            "field_coverage": "DENSE",
            "field_width_columns": decoded["width"],
            "field_height_rows": decoded["height"],
            "cell_width": 1.0,
            "cell_depth": 1.0,
            "center_column": (decoded["width"] - 1) / 2.0,
            "center_row": (decoded["height"] - 1) / 2.0,
        },
        "vertical_metric": {
            "granted_by": "cartographer",
            "vertical_measurement_rule": "ELEVATION_TIMES_MAX_HEIGHT_LAYERS",
            "unit": "meter",
            "max_height_layers": 6.0,
            "source_artifact_id": "texel_ingress_proof.metric.001",
        },
        "gap_fill": {
            "enabled": True,
            "mode": "PER_CELL_EXTRUSION",
            "adjacency_policy": "ALL_FACES_INDEPENDENT",
            "resolved_color": [0.35, 0.3, 0.25, 1.0],
            "thickness_local_units": 0.5,
        },
        "pixel_field_data": copy.deepcopy(decoded["pixel_field_data"]),
    }


class TestPinnedFixtureIntegrity(unittest.TestCase):
    def test_fixture_bytes_match_pin(self):
        data = TEXEL_FIXTURE.read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), PINNED_SHA256)
        self.assertEqual(len(data), PIN["byte_length"])


class TestExactDimensions(unittest.TestCase):
    def test_width_and_height_are_exact(self):
        decoded = decode_pinned()
        self.assertEqual(decoded["width"], 16)
        self.assertEqual(decoded["height"], 16)
        self.assertEqual(len(decoded["pixel_field_data"]), 256)
        xs = {cell["field_x"] for cell in decoded["pixel_field_data"]}
        ys = {cell["field_y"] for cell in decoded["pixel_field_data"]}
        self.assertEqual(xs, set(range(16)))
        self.assertEqual(ys, set(range(16)))

    def test_non_square_dimensions_survive(self):
        pixels = [[(10, 20, 30, 255)] * 5 for _ in range(2)]
        data = synthetic_png(pixels)
        decoded = decode_image_bytes_to_pixel_field(
            data,
            expected_sha256=hashlib.sha256(data).hexdigest(),
            terrain="grass",
            recipe="default.generic",
            elevation_policy="FLAT_ZERO",
        )
        self.assertEqual((decoded["width"], decoded["height"]), (5, 2))
        self.assertEqual(len(decoded["pixel_field_data"]), 10)


class TestOrientation(unittest.TestCase):
    """Corner markers prove identity mapping: no rotation, axis swap, or flip."""

    RED = (255, 0, 0, 255)
    GREEN = (0, 255, 0, 255)
    BLUE = (0, 0, 255, 255)
    WHITE = (255, 255, 255, 255)

    def decode_markers(self) -> dict[str, Any]:
        pixels = [
            [self.RED, self.WHITE, self.GREEN],
            [self.BLUE, self.WHITE, self.WHITE],
        ]
        data = synthetic_png(pixels)
        return decode_image_bytes_to_pixel_field(
            data,
            expected_sha256=hashlib.sha256(data).hexdigest(),
            terrain="grass",
            recipe="default.generic",
            elevation_policy="FLAT_ZERO",
        )

    def cell(self, decoded: dict[str, Any], x: int, y: int) -> dict[str, Any]:
        return decoded["pixel_field_data"][y * decoded["width"] + x]

    def test_no_rotation_or_axis_swap(self):
        decoded = self.decode_markers()
        self.assertEqual((decoded["width"], decoded["height"]), (3, 2))
        self.assertEqual(self.cell(decoded, 0, 0)["base_color"], [1.0, 0.0, 0.0, 1.0])
        self.assertEqual(self.cell(decoded, 2, 0)["base_color"], [0.0, 1.0, 0.0, 1.0])

    def test_no_vertical_flip(self):
        decoded = self.decode_markers()
        self.assertEqual(self.cell(decoded, 0, 1)["base_color"], [0.0, 0.0, 1.0, 1.0])
        self.assertEqual(self.cell(decoded, 0, 0)["base_color"], [1.0, 0.0, 0.0, 1.0])

    def test_row_major_ordinal_layout(self):
        decoded = self.decode_markers()
        for ordinal, cell in enumerate(decoded["pixel_field_data"]):
            self.assertEqual(cell["field_x"], ordinal % 3)
            self.assertEqual(cell["field_y"], ordinal // 3)


class TestExactRGBAPreservation(unittest.TestCase):
    def test_every_pixel_component_survives_exactly(self):
        decoded = decode_pinned()
        image = Image.open(io.BytesIO(TEXEL_FIXTURE.read_bytes()))
        image.load()
        for cell in decoded["pixel_field_data"]:
            source = image.getpixel((cell["field_x"], cell["field_y"]))
            for component, value in zip(source, cell["base_color"]):
                self.assertEqual(value, component / 255.0)
                self.assertEqual(round(value * 255.0), component)

    def test_only_declared_texel_palette_colors_appear(self):
        decoded = decode_pinned()
        palette = {
            (0x3E, 0x6B, 0x2F), (0x4F, 0x8A, 0x3D), (0x6A, 0xAB, 0x4E),
            (0x8C, 0xC9, 0x63), (0x2F, 0x52, 0x23), (0x7A, 0x5B, 0x3A),
        }
        seen = {
            tuple(round(component * 255.0) for component in cell["base_color"][:3])
            for cell in decoded["pixel_field_data"]
        }
        self.assertEqual(seen, palette)


class TestTransparencyPolicy(unittest.TestCase):
    def test_fully_transparent_pixel_rejects(self):
        pixels = [[(10, 20, 30, 255), (0, 0, 0, 0)]]
        data = synthetic_png(pixels)
        with self.assertRaises(ImageIngressError) as caught:
            decode_image_bytes_to_pixel_field(
                data,
                expected_sha256=hashlib.sha256(data).hexdigest(),
                terrain="grass",
                recipe="default.generic",
                elevation_policy="FLAT_ZERO",
            )
        self.assertIn("no declared cell meaning", str(caught.exception))

    def test_semi_transparent_pixel_rejects(self):
        pixels = [[(10, 20, 30, 254)]]
        data = synthetic_png(pixels)
        with self.assertRaises(ImageIngressError) as caught:
            decode_image_bytes_to_pixel_field(
                data,
                expected_sha256=hashlib.sha256(data).hexdigest(),
                terrain="grass",
                recipe="default.generic",
                elevation_policy="FLAT_ZERO",
            )
        self.assertIn("alpha 254", str(caught.exception))


class TestSourceNonMutation(unittest.TestCase):
    def test_source_file_bytes_are_unchanged_by_ingress(self):
        before = TEXEL_FIXTURE.read_bytes()
        decode_pinned()
        after = TEXEL_FIXTURE.read_bytes()
        self.assertEqual(before, after)
        self.assertEqual(hashlib.sha256(after).hexdigest(), PINNED_SHA256)

    def test_decoded_result_does_not_alias_source_bytes(self):
        data = TEXEL_FIXTURE.read_bytes()
        decoded = decode_image_bytes_to_pixel_field(
            data,
            expected_sha256=PINNED_SHA256,
            terrain="grass",
            recipe="default.generic",
            elevation_policy="LUMINANCE_BT709",
        )
        self.assertNotIn(data, decoded.values())


class TestFailClosedToxics(unittest.TestCase):
    def assert_rejects(self, needle: str, **overrides: Any) -> None:
        with self.assertRaises(ImageIngressError) as caught:
            decode_pinned(**overrides)
        self.assertIn(needle, str(caught.exception))

    def test_wrong_checksum_rejects(self):
        self.assert_rejects("do not match the pinned checksum", expected_sha256="0" * 64)

    def test_malformed_checksum_rejects(self):
        self.assert_rejects("64 lowercase hexadecimal", expected_sha256=PINNED_SHA256.upper())

    def test_unknown_elevation_policy_rejects(self):
        self.assert_rejects("elevation_policy", elevation_policy="GUESS")

    def test_empty_terrain_and_recipe_reject(self):
        self.assert_rejects("terrain must be a non-empty string", terrain=" ")
        self.assert_rejects("recipe must be a non-empty string", recipe="")

    def test_corrupt_bytes_reject(self):
        data = TEXEL_FIXTURE.read_bytes()[:100]
        with self.assertRaises(ImageIngressError) as caught:
            decode_image_bytes_to_pixel_field(
                data,
                expected_sha256=hashlib.sha256(data).hexdigest(),
                terrain="grass",
                recipe="default.generic",
                elevation_policy="FLAT_ZERO",
            )
        self.assertIn("could not be decoded", str(caught.exception))

    def test_non_png_rejects(self):
        image = Image.new("RGBA", (2, 2), (1, 2, 3, 255))
        buffer = io.BytesIO()
        image.save(buffer, format="BMP")
        data = buffer.getvalue()
        with self.assertRaises(ImageIngressError) as caught:
            decode_image_bytes_to_pixel_field(
                data,
                expected_sha256=hashlib.sha256(data).hexdigest(),
                terrain="grass",
                recipe="default.generic",
                elevation_policy="FLAT_ZERO",
            )
        self.assertIn("must be a PNG", str(caught.exception))

    def test_non_rgba_png_rejects(self):
        image = Image.new("RGB", (2, 2), (1, 2, 3))
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        data = buffer.getvalue()
        with self.assertRaises(ImageIngressError) as caught:
            decode_image_bytes_to_pixel_field(
                data,
                expected_sha256=hashlib.sha256(data).hexdigest(),
                terrain="grass",
                recipe="default.generic",
                elevation_policy="FLAT_ZERO",
            )
        self.assertIn("must be RGBA exactly", str(caught.exception))


class TestElevationPolicies(unittest.TestCase):
    def test_flat_zero_gives_zero_everywhere(self):
        decoded = decode_pinned(elevation_policy="FLAT_ZERO")
        self.assertTrue(all(cell["elevation"] == 0.0 for cell in decoded["pixel_field_data"]))

    def test_luminance_is_deterministic_and_bounded(self):
        first = decode_pinned()
        second = decode_pinned()
        self.assertEqual(first["pixel_field_data"], second["pixel_field_data"])
        for cell in first["pixel_field_data"]:
            self.assertGreaterEqual(cell["elevation"], 0.0)
            self.assertLessEqual(cell["elevation"], 1.0)


class TestConstructionThroughExistingPath(unittest.TestCase):
    """The decoded field flows through the unchanged consumer and builder."""

    def test_texel_fixture_builds_canonical_geometry(self):
        decoded = decode_pinned()
        request = request_around(decoded)
        built = consume_surface_request_packet(request, recipe_root=RECIPE_ROOT)
        self.assertEqual(built.get("status"), "BUILT", built.get("errors"))
        geometry = built["geometry"]
        self.assertEqual(len(geometry["positions"]), 256 * 6 * 4)
        self.assertEqual(len(geometry["indices"]), 256 * 6 * 6)
        self.assertEqual(len(built["cell_geometry_ranges"]), 256)

    def test_top_face_colors_match_source_pixels_exactly(self):
        decoded = decode_pinned()
        request = request_around(decoded)
        built = consume_surface_request_packet(request, recipe_root=RECIPE_ROOT)
        self.assertEqual(built.get("status"), "BUILT")
        image = Image.open(io.BytesIO(TEXEL_FIXTURE.read_bytes()))
        image.load()
        colors = built["geometry"]["colors"]
        for cell_range in built["cell_geometry_ranges"]:
            top = next(s for s in cell_range["surfaces"] if s["role"] == "PRIMARY_PIXEL_FACE")
            source = image.getpixel((cell_range["field_x"], cell_range["field_y"]))
            for vertex in range(top["vertex_start"], top["vertex_start"] + top["vertex_count"]):
                self.assertEqual(
                    [round(component * 255.0) for component in colors[vertex]],
                    [source[0], source[1], source[2], 255],
                )

    def test_heights_follow_declared_luminance_metric(self):
        decoded = decode_pinned()
        request = request_around(decoded)
        built = consume_surface_request_packet(request, recipe_root=RECIPE_ROOT)
        self.assertEqual(built.get("status"), "BUILT")
        elevation_by_key = {
            (cell["field_x"], cell["field_y"]): cell["elevation"]
            for cell in decoded["pixel_field_data"]
        }
        for cell_range in built["cell_geometry_ranges"]:
            expected = round(elevation_by_key[(cell_range["field_x"], cell_range["field_y"])] * 6)
            self.assertEqual(cell_range["world_cell"]["world_cell_y"], expected)


if __name__ == "__main__":
    unittest.main()
