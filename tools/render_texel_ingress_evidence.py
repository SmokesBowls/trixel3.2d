"""Evidence harness: pinned Texel PNG -> Trixel ingress -> existing construction -> software render.

Produces one side-by-side PNG: unchanged Texel source (nearest-neighbor upscale)
next to a painter's-algorithm render of the Trixel-built geometry. No Godot, no
runtime, no scene, no collision, no transport.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from trixel.trixel32d_image_ingress import decode_image_bytes_to_pixel_field
from trixel.trixel32d_surface_consumer import consume_surface_request_packet

sys.path.insert(0, str(REPO / "tests"))
from test_trixel32d_image_ingress import PINNED_SHA256, TEXEL_FIXTURE, request_around

OUT_DIR = REPO / "fixtures" / "texel"
PANEL = 720
GUTTER = 16
LABEL_BAND = 26


def vsub(a, b):
    return [a[i] - b[i] for i in range(3)]


def vcross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def vdot(a, b):
    return sum(a[i] * b[i] for i in range(3))


def vnorm(a):
    length = math.sqrt(vdot(a, a))
    return [c / length for c in a]


def render_geometry(built: dict) -> Image.Image:
    positions = built["geometry"]["positions"]
    indices = built["geometry"]["indices"]
    colors = built["geometry"]["colors"]

    view_dir = vnorm([1.0, 0.62, 0.9])          # from scene toward camera (oblique)
    world_up = [0.0, 1.0, 0.0]
    cam_right = vnorm(vcross(world_up, view_dir))
    cam_up = vnorm(vcross(view_dir, cam_right))
    light = vnorm([0.35, 1.0, 0.2])

    projected = [
        (vdot(p, cam_right), vdot(p, cam_up), vdot(p, view_dir)) for p in positions
    ]
    xs = [p[0] for p in projected]
    ys = [p[1] for p in projected]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    span = max(max_x - min_x, max_y - min_y)
    margin = 30
    scale = (PANEL - 2 * margin) / span
    off_x = (PANEL - (max_x - min_x) * scale) / 2.0
    off_y = (PANEL - (max_y - min_y) * scale) / 2.0

    def to_screen(p):
        return (
            off_x + (p[0] - min_x) * scale,
            PANEL - (off_y + (p[1] - min_y) * scale),
        )

    triangles = []
    for t in range(0, len(indices), 3):
        i0, i1, i2 = indices[t], indices[t + 1], indices[t + 2]
        p0, p1, p2 = positions[i0], positions[i1], positions[i2]
        normal = vcross(vsub(p1, p0), vsub(p2, p0))
        length = math.sqrt(vdot(normal, normal))
        if length == 0.0:
            continue
        normal = [c / length for c in normal]
        if vdot(normal, view_dir) <= 0.0:
            continue  # back-face
        depth = (projected[i0][2] + projected[i1][2] + projected[i2][2]) / 3.0
        shade = 0.52 + 0.48 * max(0.0, vdot(normal, light))
        base = colors[i0]
        fill = tuple(min(255, round(base[c] * 255.0 * shade)) for c in range(3))
        triangles.append((depth, [to_screen(projected[i]) for i in (i0, i1, i2)], fill))

    triangles.sort(key=lambda item: item[0])  # far first
    image = Image.new("RGB", (PANEL, PANEL), (24, 26, 30))
    draw = ImageDraw.Draw(image)
    for _, points, fill in triangles:
        draw.polygon(points, fill=fill)
    return image


def main() -> None:
    source_bytes = TEXEL_FIXTURE.read_bytes()
    assert hashlib.sha256(source_bytes).hexdigest() == PINNED_SHA256

    decoded = decode_image_bytes_to_pixel_field(
        source_bytes,
        expected_sha256=PINNED_SHA256,
        terrain="grass",
        recipe="default.generic",
        elevation_policy="LUMINANCE_BT709",
    )
    request = request_around(decoded)
    built = consume_surface_request_packet(request, recipe_root=REPO / "recipes" / "terrain")
    assert built.get("status") == "BUILT", built.get("errors")

    (OUT_DIR / "texel_ingress_built_response.json").write_text(
        json.dumps(built, indent=1, sort_keys=True), encoding="utf-8"
    )

    import io
    source_img = Image.open(io.BytesIO(source_bytes))
    source_img.load()
    left = source_img.convert("RGB").resize((PANEL, PANEL), Image.NEAREST)
    right = render_geometry(built)
    right.save(OUT_DIR / "texel_ingress_trixel_render.png", format="PNG")

    total_w = PANEL * 2 + GUTTER
    total_h = PANEL + LABEL_BAND
    sheet = Image.new("RGB", (total_w, total_h), (12, 12, 14))
    sheet.paste(left, (0, LABEL_BAND))
    sheet.paste(right, (PANEL + GUTTER, LABEL_BAND))
    draw = ImageDraw.Draw(sheet)
    draw.text((6, 6), f"Texel source 16x16 (unchanged, sha256 {PINNED_SHA256[:16]}...)", fill=(220, 220, 220))
    draw.text(
        (PANEL + GUTTER + 6, 6),
        f"Trixel-built geometry ({request['identity']['request_id']}, LUMINANCE_BT709 x 6 layers)",
        fill=(220, 220, 220),
    )
    out = OUT_DIR / "texel_ingress_side_by_side.png"
    sheet.save(out, format="PNG")

    after = TEXEL_FIXTURE.read_bytes()
    assert hashlib.sha256(after).hexdigest() == PINNED_SHA256, "source mutated!"
    print("request_id:", request["identity"]["request_id"])
    print("built status:", built["status"], "| surface_id:", built.get("surface_id"))
    print("positions:", len(built["geometry"]["positions"]), "indices:", len(built["geometry"]["indices"]))
    print("evidence:", out)
    print("source unchanged:", PINNED_SHA256)


if __name__ == "__main__":
    main()
