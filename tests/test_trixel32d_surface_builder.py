from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from typing import Any

from trixel.trixel32d_surface_consumer import consume_surface_request_file
from trixel.trixel32d_surface_consumer import consume_surface_request_packet


REPO_ROOT = Path(__file__).resolve().parents[1]
ENGAIN_FIXTURE = (
    REPO_ROOT.parent
    / "EngAIn"
    / "tier1"
    / "engainos"
    / "tests"
    / "fixtures"
    / "trixel32d_request_3x2_first_proof.json"
)
RECIPE_ROOT = REPO_ROOT / "recipes" / "terrain"
BUILT_FIXTURE = REPO_ROOT / "fixtures" / "trixel32d_surface_built_3x2_first_proof.json"


def load_fixture() -> dict[str, Any]:
    return json.loads(ENGAIN_FIXTURE.read_text(encoding="utf-8"))


class Trixel32dSurfaceBuilderTests(unittest.TestCase):
    def test_canonical_engain_fixture_builds_deterministic_owned_geometry(self) -> None:
        first = consume_surface_request_file(ENGAIN_FIXTURE, recipe_root=RECIPE_ROOT)
        second = consume_surface_request_file(ENGAIN_FIXTURE, recipe_root=RECIPE_ROOT)

        self.assertEqual(first, second)
        self.assertEqual(first["packet_type"], "trixel32d_surface_built")
        self.assertEqual(first["contract"], "trixel32d_surface_built.v1")
        self.assertEqual(first["status"], "BUILT")
        self.assertEqual(first["request_id"], "t32dreq_8b14a3bac98d1025")
        self.assertEqual(first["errors"], [])
        self.assertEqual(first["rejected_cells"], [])
        self.assertEqual(first["local_spatial_metadata"]["coordinate_space"], "TRIXEL_LOCAL_Y_UP")
        self.assertEqual(first["local_spatial_metadata"]["normals_policy"], "CANONICAL_FACE_NORMALS_INCLUDED")
        self.assertEqual(first["local_spatial_metadata"]["tangents_policy"], "OMITTED_NO_TANGENT_BASIS")

        geometry = first["geometry"]
        self.assertEqual(len(geometry["positions"]), 144)
        self.assertEqual(len(geometry["normals"]), 144)
        self.assertEqual(len(geometry["uvs"]), 144)
        self.assertEqual(len(geometry["colors"]), 144)
        self.assertEqual(len(geometry["indices"]), 216)
        self.assertEqual(max(geometry["indices"]), 143)

        ranges = first["cell_geometry_ranges"]
        self.assertEqual([item["cell_key"] for item in ranges], ["0,0", "1,0", "2,0", "0,1", "1,1", "2,1"])
        self.assertTrue(all(item["disposition"] == "PRESERVED_1_TO_1" for item in ranges))
        self.assertTrue(all(len(item["surfaces"]) == 6 for item in ranges))
        self.assertEqual([surface["face"] for surface in ranges[0]["surfaces"]], [
            "top", "bottom", "-field_y", "+field_x", "+field_y", "-field_x"
        ])
        self.assertEqual(geometry["positions"][0][1], 3.0)
        self.assertEqual(geometry["positions"][4][1], 2.975)

    def test_persisted_built_fixture_matches_canonical_generation(self) -> None:
        generated = consume_surface_request_file(ENGAIN_FIXTURE, recipe_root=RECIPE_ROOT)
        persisted = json.loads(BUILT_FIXTURE.read_text(encoding="utf-8"))

        self.assertEqual(persisted, generated)

    def test_duplicate_cell_is_rejected_before_geometry(self) -> None:
        request = load_fixture()
        request["pixel_field_data"][1]["field_x"] = 0

        response = consume_surface_request_packet(request, recipe_root=RECIPE_ROOT)

        self.assertEqual(response["status"], "REJECTED")
        self.assertIsNone(response["geometry"])
        self.assertEqual(response["errors"], ["pixel_field_data[1] is not row-major: expected (1,0), got (0,0)"])

    def test_shuffled_cells_are_rejected_instead_of_reordered(self) -> None:
        request = load_fixture()
        request["pixel_field_data"][0], request["pixel_field_data"][1] = (
            request["pixel_field_data"][1],
            request["pixel_field_data"][0],
        )

        response = consume_surface_request_packet(request, recipe_root=RECIPE_ROOT)

        self.assertEqual(response["status"], "REJECTED")
        self.assertIsNone(response["geometry"])
        self.assertEqual(response["errors"], ["pixel_field_data[0] is not row-major: expected (0,0), got (1,0)"])

    def test_unresolved_recipe_is_rejected_before_geometry(self) -> None:
        request = copy.deepcopy(load_fixture())
        request["pixel_field_data"][0]["recipe"] = "missing.recipe"

        response = consume_surface_request_packet(request, recipe_root=RECIPE_ROOT)

        self.assertEqual(response["status"], "REJECTED")
        self.assertIsNone(response["geometry"])
        self.assertEqual(response["errors"], ["pixel_field_data[0].recipe is unresolved: 'missing.recipe'"])

    def test_wrong_contract_is_rejected_before_geometry(self) -> None:
        request = load_fixture()
        request["identity"]["contract"] = "trixel32d_surface_request.v2"

        response = consume_surface_request_packet(request, recipe_root=RECIPE_ROOT)

        self.assertEqual(response["status"], "REJECTED")
        self.assertIsNone(response["geometry"])
        self.assertEqual(response["errors"], ["identity.contract must be 'trixel32d_surface_request.v1'"])


if __name__ == "__main__":
    unittest.main()
