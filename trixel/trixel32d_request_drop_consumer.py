"""Trixel-side consumer for checksum-locked surface-request file drops.

Transport contract shared with EngAInOS (mirrored constants, no EngAIn code):
one fixed-name request envelope and payload per drop slot; the response drop's
envelope existence is the consume state of the slot (identity semantics — no
clock, no expiration, no second ledger).

The request payload checksum is verified BEFORE parsing. Validation and
construction go through the existing request consumer and builder unchanged.
The response is serialized exactly once with the declared canonical
serialization — json.dumps(response, indent=1, sort_keys=True) encoded UTF-8 —
and the response drop carries those bytes; byte identity is the only rule.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from trixel.trixel32d_surface_consumer import consume_surface_request_packet
from trixel.trixel32d_surface_emitter import emit_rejected_surface

REQUEST_DROP_CONTRACT = "engainos.trixel32d_request_drop.v1"
REQUEST_DROP_PACKET_TYPE = "trixel32d_request_drop"
REQUEST_ENVELOPE_FILENAME = "TRIXEL32D_SURFACE_REQUEST_DROP_V1.json"
REQUEST_PAYLOAD_FILENAME = "TRIXEL32D_SURFACE_REQUEST_PAYLOAD_V1.json"

RESPONSE_DROP_CONTRACT = "engainos.trixel32d_built_drop.v1"
RESPONSE_DROP_PACKET_TYPE = "trixel32d_built_drop"
RESPONSE_ENVELOPE_FILENAME = "TRIXEL32D_SURFACE_BUILT_DROP_V1.json"
RESPONSE_PAYLOAD_FILENAME = "TRIXEL32D_SURFACE_BUILT_PAYLOAD_V1.json"

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_REQUEST_ENVELOPE_FIELDS = frozenset({
    "contract",
    "packet_type",
    "drop_id",
    "generated_by",
    "payload_file",
    "payload_sha256",
    "request_id",
    "topology_policy",
})


def canonical_response_bytes(response: dict[str, Any]) -> bytes:
    """The single declared canonical serialization for response payloads."""
    return json.dumps(response, indent=1, sort_keys=True).encode("utf-8")


def consume_request_drop(
    request_drop_dir: str | Path,
    response_drop_dir: str | Path,
    *,
    recipe_root: str | Path,
    expected_request_id: str,
) -> dict[str, Any]:
    """Consume one request drop fail-closed and write one response drop.

    Stale (identity-mismatched) and duplicate drops are refused without
    consuming the slot. A corrupt or invalid drop for the expected identity
    consumes the slot with a REJECTED response and no partial geometry.
    """
    request_dir = Path(request_drop_dir)
    response_dir = Path(response_drop_dir)

    if not isinstance(expected_request_id, str) or not expected_request_id:
        return _refused("expected_request_id must be a non-empty string")

    if (response_dir / RESPONSE_ENVELOPE_FILENAME).exists():
        return _refused(
            "response drop already exists; this request slot was consumed and a"
            " duplicate consume rejects"
        )

    envelope_path = request_dir / REQUEST_ENVELOPE_FILENAME
    if not envelope_path.is_file():
        return _refused(f"request drop envelope is missing: {REQUEST_ENVELOPE_FILENAME}")
    try:
        envelope = json.loads(envelope_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return _consume_rejected(
            response_dir, None,
            f"request drop envelope could not be parsed: {type(exc).__name__}",
        )
    if not isinstance(envelope, dict):
        return _consume_rejected(response_dir, None, "request drop envelope must be a JSON object")

    unknown = sorted(set(envelope.keys()) - _REQUEST_ENVELOPE_FIELDS)
    if unknown:
        return _consume_rejected(
            response_dir, None,
            f"request drop envelope contains undeclared keys: {', '.join(unknown)}",
        )
    missing = sorted(_REQUEST_ENVELOPE_FIELDS - set(envelope.keys()))
    if missing:
        return _consume_rejected(
            response_dir, None,
            f"request drop envelope is missing required keys: {', '.join(missing)}",
        )
    if envelope.get("contract") != REQUEST_DROP_CONTRACT:
        return _consume_rejected(
            response_dir, None, f"request drop envelope contract must be '{REQUEST_DROP_CONTRACT}'"
        )
    if envelope.get("packet_type") != REQUEST_DROP_PACKET_TYPE:
        return _consume_rejected(
            response_dir, None,
            f"request drop envelope packet_type must be '{REQUEST_DROP_PACKET_TYPE}'",
        )
    if envelope.get("payload_file") != REQUEST_PAYLOAD_FILENAME:
        return _consume_rejected(
            response_dir, None,
            f"request drop envelope payload_file must be exactly '{REQUEST_PAYLOAD_FILENAME}'",
        )

    envelope_request_id = envelope.get("request_id")
    if envelope_request_id != expected_request_id:
        return _refused(
            "request drop is stale: envelope request_id does not match the"
            " currently expected request identity"
        )

    declared_sha256 = envelope.get("payload_sha256")
    if not isinstance(declared_sha256, str) or _SHA256_PATTERN.fullmatch(declared_sha256) is None:
        return _consume_rejected(
            response_dir, envelope_request_id,
            "request drop envelope payload_sha256 must be 64 lowercase hexadecimal characters",
        )
    if envelope.get("drop_id") != f"t32ddrop_{declared_sha256[:16]}":
        return _consume_rejected(
            response_dir, envelope_request_id,
            "request drop envelope drop_id must derive from the payload checksum",
        )

    payload_path = request_dir / REQUEST_PAYLOAD_FILENAME
    if not payload_path.is_file():
        return _consume_rejected(
            response_dir, envelope_request_id,
            f"request drop payload is missing: {REQUEST_PAYLOAD_FILENAME}",
        )
    payload_bytes = payload_path.read_bytes()
    actual_sha256 = hashlib.sha256(payload_bytes).hexdigest()
    if actual_sha256 != declared_sha256:
        return _consume_rejected(
            response_dir, envelope_request_id,
            "request drop payload bytes do not match the declared checksum: "
            f"expected {declared_sha256}, got {actual_sha256}",
        )

    try:
        request = json.loads(payload_bytes.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        return _consume_rejected(
            response_dir, envelope_request_id,
            f"request drop payload could not be parsed: {type(exc).__name__}",
        )
    payload_request_id = (
        request.get("identity", {}).get("request_id") if isinstance(request, dict) else None
    )
    if payload_request_id != envelope_request_id:
        return _consume_rejected(
            response_dir, envelope_request_id,
            "request drop envelope request_id does not match the payload identity;"
            " a misdeclaring envelope rejects",
        )

    response = consume_surface_request_packet(request, recipe_root=recipe_root)
    return _write_response_drop(response_dir, response)


def _write_response_drop(response_dir: Path, response: dict[str, Any]) -> dict[str, Any]:
    response_bytes = canonical_response_bytes(response)
    response_sha256 = hashlib.sha256(response_bytes).hexdigest()
    envelope = {
        "contract": RESPONSE_DROP_CONTRACT,
        "packet_type": RESPONSE_DROP_PACKET_TYPE,
        "drop_id": f"t32ddrop_{response_sha256[:16]}",
        "generated_by": "trixel3.2d",
        "payload_file": RESPONSE_PAYLOAD_FILENAME,
        "payload_sha256": response_sha256,
        "request_id": response.get("request_id"),
        "surface_id": response.get("surface_id"),
        "topology_policy": response.get("topology_policy"),
    }
    response_dir.mkdir(parents=True, exist_ok=True)
    (response_dir / RESPONSE_PAYLOAD_FILENAME).write_bytes(response_bytes)
    (response_dir / RESPONSE_ENVELOPE_FILENAME).write_text(
        json.dumps(envelope, indent=2, sort_keys=True), encoding="utf-8"
    )
    return {
        "consumed": True,
        "errors": list(response.get("errors") or []),
        "status": response.get("status"),
        "request_id": response.get("request_id"),
        "surface_id": response.get("surface_id"),
        "response_sha256": response_sha256,
        "response_payload_path": str(response_dir / RESPONSE_PAYLOAD_FILENAME),
        "response_envelope_path": str(response_dir / RESPONSE_ENVELOPE_FILENAME),
    }


def _consume_rejected(
    response_dir: Path, request_id: str | None, error: str
) -> dict[str, Any]:
    """A corrupt or invalid drop for the expected identity consumes the slot
    with a REJECTED response and no partial geometry."""
    rejected = emit_rejected_surface(request_id, error)
    result = _write_response_drop(response_dir, rejected)
    result["errors"] = [error]
    return result


def _refused(message: str) -> dict[str, Any]:
    """Stale and duplicate drops are refused without consuming the slot."""
    return {
        "consumed": False,
        "errors": [message],
        "status": None,
        "request_id": None,
        "surface_id": None,
        "response_sha256": None,
        "response_payload_path": None,
        "response_envelope_path": None,
    }
