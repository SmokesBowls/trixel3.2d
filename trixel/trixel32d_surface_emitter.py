from __future__ import annotations

import hashlib
from typing import Any


RESPONSE_CONTRACT = "trixel32d_surface_built.v1"
LOCAL_COORDINATE_SPACE = "TRIXEL_LOCAL_Y_UP"
NORMALS_POLICY = "CANONICAL_FACE_NORMALS_INCLUDED"
TANGENTS_POLICY = "OMITTED_NO_TANGENT_BASIS"


def emit_rejected_surface(request_id: str | None, error: str) -> dict[str, Any]:
    """Emit a fail-closed response containing no partial geometry."""
    return {
        "contract": RESPONSE_CONTRACT,
        "packet_type": "trixel32d_surface_built",
        "request_id": request_id,
        "surface_id": None,
        "status": "REJECTED",
        "local_spatial_metadata": _local_spatial_metadata(),
        "geometry": None,
        "cell_geometry_ranges": [],
        "primitive_provenance": [],
        "rejected_cells": [],
        "errors": [error],
    }


def emit_built_surface(
    *,
    request_id: str,
    geometry: dict[str, Any],
    cell_geometry_ranges: list[dict[str, Any]],
    primitive_provenance: list[dict[str, Any]],
    appearance: dict[str, Any],
    topology_policy: str,
) -> dict[str, Any]:
    """Wrap complete canonical geometry in the v1 built-response envelope."""
    surface_digest = hashlib.sha256(
        f"{request_id}:{topology_policy}".encode("utf-8")
    ).hexdigest()[:16]
    return {
        "contract": RESPONSE_CONTRACT,
        "packet_type": "trixel32d_surface_built",
        "request_id": request_id,
        "surface_id": f"t32dsurface_{surface_digest}",
        "status": "BUILT",
        "local_spatial_metadata": _local_spatial_metadata(),
        "topology_policy": topology_policy,
        "appearance": appearance,
        "geometry": geometry,
        "cell_geometry_ranges": cell_geometry_ranges,
        "primitive_provenance": primitive_provenance,
        "rejected_cells": [],
        "errors": [],
    }


def _local_spatial_metadata() -> dict[str, str]:
    return {
        "coordinate_space": LOCAL_COORDINATE_SPACE,
        "winding_policy": "CLOCKWISE_FRONT_FACE_GODOT",
        "normals_policy": NORMALS_POLICY,
        "tangents_policy": TANGENTS_POLICY,
    }
