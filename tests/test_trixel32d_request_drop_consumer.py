from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path
from typing import Any

from trixel.trixel32d_request_drop_consumer import (
    REQUEST_DROP_CONTRACT,
    REQUEST_DROP_PACKET_TYPE,
    REQUEST_ENVELOPE_FILENAME,
    REQUEST_PAYLOAD_FILENAME,
    RESPONSE_ENVELOPE_FILENAME,
    RESPONSE_PAYLOAD_FILENAME,
    consume_request_drop,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
RECIPE_ROOT = REPO_ROOT / "recipes" / "terrain"
VENDORED_REQUEST = (
    REPO_ROOT.parent / "EngAIn" / "tier1" / "engainos" / "tests" / "fixtures"
    / "trixel32d_request_texel_connected.json"
)
PINNED_RESPONSE = REPO_ROOT / "fixtures" / "texel" / "texel_connected_surface_built_response.json"
PINNED_RESPONSE_SHA256 = "86d8b22013c03ca6b20dcbebeb5240309128d3d6b7258c3236aeca60a6459139"
REQUEST_ID = "t32dreq_001241884d12dff0"
STITCHED_SURFACE_ID = "t32dsurface_f024725d200e470c"

REQUEST_BYTES = VENDORED_REQUEST.read_bytes()
REQUEST_SHA256 = hashlib.sha256(REQUEST_BYTES).hexdigest()


def write_request_drop(drop_dir: Path, payload: bytes | None = None, **envelope_overrides: Any) -> dict[str, Any]:
    payload = REQUEST_BYTES if payload is None else payload
    sha = hashlib.sha256(payload).hexdigest()
    envelope: dict[str, Any] = {
        "contract": REQUEST_DROP_CONTRACT,
        "packet_type": REQUEST_DROP_PACKET_TYPE,
        "drop_id": f"t32ddrop_{sha[:16]}",
        "generated_by": "engainos",
        "payload_file": REQUEST_PAYLOAD_FILENAME,
        "payload_sha256": sha,
        "request_id": REQUEST_ID,
        "topology_policy": "HEIGHT_FIELD_CONNECTED_SURFACE",
    }
    envelope.update(envelope_overrides)
    drop_dir.mkdir(parents=True, exist_ok=True)
    (drop_dir / REQUEST_PAYLOAD_FILENAME).write_bytes(payload)
    (drop_dir / REQUEST_ENVELOPE_FILENAME).write_text(
        json.dumps(envelope, indent=2, sort_keys=True), encoding="utf-8"
    )
    return envelope


class RequestDropCase(unittest.TestCase):
    def setUp(self):
        import tempfile
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.request_dir = base / "requests"
        self.response_dir = base / "responses"

    def tearDown(self):
        self._tmp.cleanup()

    def consume(self, **overrides: Any) -> dict[str, Any]:
        values: dict[str, Any] = {
            "recipe_root": RECIPE_ROOT,
            "expected_request_id": REQUEST_ID,
        }
        values.update(overrides)
        return consume_request_drop(self.request_dir, self.response_dir, **values)


class TestRoundTripByteIdentity(RequestDropCase):
    def test_built_response_is_byte_identical_to_pinned_payload(self):
        write_request_drop(self.request_dir)
        result = self.consume()
        self.assertTrue(result["consumed"], result["errors"])
        self.assertEqual(result["status"], "BUILT")
        self.assertEqual(result["request_id"], REQUEST_ID)
        self.assertEqual(result["surface_id"], STITCHED_SURFACE_ID)
        self.assertEqual(result["response_sha256"], PINNED_RESPONSE_SHA256)

        written = (self.response_dir / RESPONSE_PAYLOAD_FILENAME).read_bytes()
        self.assertEqual(written, PINNED_RESPONSE.read_bytes())

        envelope = json.loads(
            (self.response_dir / RESPONSE_ENVELOPE_FILENAME).read_text(encoding="utf-8")
        )
        self.assertEqual(envelope["payload_sha256"], PINNED_RESPONSE_SHA256)
        self.assertEqual(envelope["request_id"], REQUEST_ID)
        self.assertEqual(envelope["surface_id"], STITCHED_SURFACE_ID)
        self.assertEqual(envelope["topology_policy"], "HEIGHT_FIELD_CONNECTED_SURFACE")

    def test_request_payload_is_untouched_by_consumption(self):
        write_request_drop(self.request_dir)
        self.consume()
        self.assertEqual((self.request_dir / REQUEST_PAYLOAD_FILENAME).read_bytes(), REQUEST_BYTES)
        self.assertEqual(hashlib.sha256(VENDORED_REQUEST.read_bytes()).hexdigest(), REQUEST_SHA256)


class TestStaleAndDuplicate(RequestDropCase):
    def test_stale_request_id_refuses_without_consuming_slot(self):
        write_request_drop(self.request_dir)
        result = self.consume(expected_request_id="t32dreq_0000000000000000")
        self.assertFalse(result["consumed"])
        self.assertTrue(any("stale" in e for e in result["errors"]))
        self.assertFalse((self.response_dir / RESPONSE_ENVELOPE_FILENAME).exists())

    def test_duplicate_consume_refuses_without_overwriting(self):
        write_request_drop(self.request_dir)
        first = self.consume()
        self.assertTrue(first["consumed"])
        before = (self.response_dir / RESPONSE_PAYLOAD_FILENAME).read_bytes()

        second = self.consume()
        self.assertFalse(second["consumed"])
        self.assertTrue(any("duplicate consume rejects" in e for e in second["errors"]))
        self.assertEqual((self.response_dir / RESPONSE_PAYLOAD_FILENAME).read_bytes(), before)


class TestFailClosedRejection(RequestDropCase):
    def assert_rejected_response(self, result: dict[str, Any], needle: str, request_id):
        self.assertTrue(result["consumed"])
        self.assertEqual(result["status"], "REJECTED")
        self.assertTrue(any(needle in e for e in result["errors"]), result["errors"])
        payload = json.loads(
            (self.response_dir / RESPONSE_PAYLOAD_FILENAME).read_text(encoding="utf-8")
        )
        self.assertEqual(payload["status"], "REJECTED")
        self.assertIsNone(payload["geometry"])
        self.assertEqual(payload["cell_geometry_ranges"], [])
        self.assertEqual(payload["request_id"], request_id)
        self.assertIsNone(payload["surface_id"])

    def test_malformed_envelope_rejects_with_no_partial_geometry(self):
        self.request_dir.mkdir(parents=True)
        (self.request_dir / REQUEST_ENVELOPE_FILENAME).write_text("{broken", encoding="utf-8")
        (self.request_dir / REQUEST_PAYLOAD_FILENAME).write_bytes(REQUEST_BYTES)
        result = self.consume()
        self.assert_rejected_response(result, "could not be parsed", None)

    def test_undeclared_envelope_keys_reject(self):
        write_request_drop(self.request_dir, injected="value")
        result = self.consume()
        self.assert_rejected_response(result, "undeclared keys", None)

    def test_truncated_payload_rejects_before_parse(self):
        write_request_drop(self.request_dir)
        (self.request_dir / REQUEST_PAYLOAD_FILENAME).write_bytes(REQUEST_BYTES[: len(REQUEST_BYTES) // 3])
        result = self.consume()
        self.assert_rejected_response(result, "do not match the declared checksum", REQUEST_ID)

    def test_digest_mismatched_envelope_rejects(self):
        write_request_drop(self.request_dir, payload_sha256="0" * 64, drop_id="t32ddrop_0000000000000000")
        result = self.consume()
        self.assert_rejected_response(result, "do not match the declared checksum", REQUEST_ID)

    def test_misdeclaring_envelope_request_id_rejects(self):
        other_request = json.loads(REQUEST_BYTES.decode("utf-8"))
        other_request["identity"]["request_id"] = "t32dreq_ffffffffffffffff"
        other_bytes = json.dumps(other_request, indent=1, sort_keys=True).encode("utf-8")
        write_request_drop(self.request_dir, payload=other_bytes)
        result = self.consume()
        self.assert_rejected_response(result, "misdeclaring envelope rejects", REQUEST_ID)

    def test_semantically_invalid_request_rejects_through_existing_consumer(self):
        bad_request = json.loads(REQUEST_BYTES.decode("utf-8"))
        bad_request["gap_fill"]["adjacency_policy"] = "ALL_FACES_INDEPENDENT"
        bad_bytes = json.dumps(bad_request, indent=1, sort_keys=True).encode("utf-8")
        write_request_drop(self.request_dir, payload=bad_bytes)
        result = self.consume()
        self.assert_rejected_response(result, "gap_fill.adjacency_policy", REQUEST_ID)


if __name__ == "__main__":
    unittest.main()
