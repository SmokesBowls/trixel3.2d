from __future__ import annotations

import hashlib
import io
import re
from typing import Any, NoReturn

from PIL import Image

INGRESS_CONTRACT = "trixel32d_image_pixel_field.v1"
ELEVATION_POLICIES = ("FLAT_ZERO", "LUMINANCE_BT709")

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_BT709_WEIGHTS = (0.2126, 0.7152, 0.0722)


class ImageIngressError(ValueError):
    """The first fail-closed image ingress failure."""


def decode_image_bytes_to_pixel_field(
    image_bytes: object,
    *,
    expected_sha256: object,
    terrain: object,
    recipe: object,
    elevation_policy: object,
) -> dict[str, Any]:
    """Decode checksum-pinned PNG bytes into row-major `pixel_field_data` cells.

    The bytes are the authority: they are hashed before decoding and must match
    the pin exactly. Pixel (x, y) with image row 0 at the top becomes the cell
    at (field_x = x, field_y = y) — no rotation, no axis swap, no vertical
    flip. Every RGBA byte is preserved exactly as component/255. DENSE field
    coverage gives a transparent or semi-transparent pixel no declared cell
    meaning, so any alpha below 255 rejects fail-closed. Elevation is Trixel
    interpretation under an explicit declared policy; the source image is
    never modified.
    """
    if not isinstance(image_bytes, bytes) or not image_bytes:
        _reject("image_bytes must be non-empty bytes")
    if not isinstance(expected_sha256, str) or _SHA256_PATTERN.fullmatch(expected_sha256) is None:
        _reject("expected_sha256 must be 64 lowercase hexadecimal characters")
    actual_sha256 = hashlib.sha256(image_bytes).hexdigest()
    if actual_sha256 != expected_sha256:
        _reject(
            "image bytes do not match the pinned checksum: "
            f"expected {expected_sha256}, got {actual_sha256}"
        )
    if not isinstance(terrain, str) or not terrain.strip():
        _reject("terrain must be a non-empty string")
    if not isinstance(recipe, str) or not recipe.strip():
        _reject("recipe must be a non-empty string")
    if elevation_policy not in ELEVATION_POLICIES:
        _reject(
            "elevation_policy must be one of "
            + ", ".join(f"'{policy}'" for policy in ELEVATION_POLICIES)
        )

    try:
        image = Image.open(io.BytesIO(image_bytes))
        image.load()
    except Exception as exc:
        _reject(f"image bytes could not be decoded: {exc}")
    if image.format != "PNG":
        _reject(f"image must be a PNG, got format '{image.format}'")
    if image.mode != "RGBA":
        _reject(f"image mode must be RGBA exactly, got '{image.mode}'; no silent conversion")

    width, height = image.size
    pixel_field_data: list[dict[str, Any]] = []
    for field_y in range(height):
        for field_x in range(width):
            red, green, blue, alpha = image.getpixel((field_x, field_y))
            if alpha != 255:
                _reject(
                    f"pixel ({field_x},{field_y}) has alpha {alpha}; DENSE coverage gives a "
                    "transparent or semi-transparent pixel no declared cell meaning"
                )
            if elevation_policy == "FLAT_ZERO":
                elevation = 0.0
            else:
                luminance = sum(
                    weight * component
                    for weight, component in zip(_BT709_WEIGHTS, (red, green, blue))
                ) / 255.0
                elevation = min(1.0, max(0.0, luminance))
            pixel_field_data.append({
                "field_x": field_x,
                "field_y": field_y,
                "elevation": elevation,
                "terrain": terrain,
                "recipe": recipe,
                "base_color": [red / 255.0, green / 255.0, blue / 255.0, alpha / 255.0],
            })

    return {
        "contract": INGRESS_CONTRACT,
        "source_sha256": actual_sha256,
        "source_byte_length": len(image_bytes),
        "width": width,
        "height": height,
        "elevation_policy": elevation_policy,
        "terrain": terrain,
        "recipe": recipe,
        "pixel_field_data": pixel_field_data,
    }


def _reject(message: str) -> NoReturn:
    raise ImageIngressError(message)
