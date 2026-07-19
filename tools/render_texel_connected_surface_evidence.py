"""Evidence: stitched connected-surface render + comparison against the accepted lattice.

Reuses the pinned Texel fixture and the same deterministic software renderer.
The lattice panel is the exact accepted evidence PNG bytes, never rerendered.
No Godot, no runtime, no placement, no collision, no transport.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(REPO / "tests"))

from render_texel_ingress_evidence import PANEL, GUTTER, LABEL_BAND, render_geometry
from test_trixel32d_image_ingress import PINNED_SHA256, TEXEL_FIXTURE
from test_trixel32d_connected_surface import build_connected

OUT_DIR = REPO / "fixtures" / "texel"
ACCEPTED_LATTICE = OUT_DIR / "texel_ingress_trixel_render.png"
ACCEPTED_LATTICE_SHA256 = "9505d3fbed324c389c0d595087dc60f7a66130bd604175fd64bd11d256290852"


def main() -> None:
    lattice_bytes = ACCEPTED_LATTICE.read_bytes()
    assert hashlib.sha256(lattice_bytes).hexdigest() == ACCEPTED_LATTICE_SHA256

    decoded, built = build_connected()
    assert built.get("status") == "BUILT", built.get("errors")

    (OUT_DIR / "texel_connected_surface_built_response.json").write_text(
        json.dumps(built, indent=1, sort_keys=True), encoding="utf-8"
    )

    stitched = render_geometry(built)
    stitched.save(OUT_DIR / "texel_connected_surface_render.png", format="PNG")

    import io
    lattice = Image.open(io.BytesIO(lattice_bytes)).convert("RGB")

    total_w = PANEL * 2 + GUTTER
    total_h = PANEL + LABEL_BAND
    sheet = Image.new("RGB", (total_w, total_h), (12, 12, 14))
    sheet.paste(lattice, (0, LABEL_BAND))
    sheet.paste(stitched, (PANEL + GUTTER, LABEL_BAND))
    draw = ImageDraw.Draw(sheet)
    draw.text(
        (6, 6),
        "Accepted lattice (ALL_FACES_INDEPENDENT, exact accepted bytes)",
        fill=(220, 220, 220),
    )
    draw.text(
        (PANEL + GUTTER + 6, 6),
        f"Stitched slab (HEIGHT_FIELD_CONNECTED_SURFACE, {built['surface_id']})",
        fill=(220, 220, 220),
    )
    comparison = OUT_DIR / "texel_lattice_vs_connected.png"
    sheet.save(comparison, format="PNG")

    source_after = TEXEL_FIXTURE.read_bytes()
    assert hashlib.sha256(source_after).hexdigest() == PINNED_SHA256, "source mutated!"
    print("surface_id:", built["surface_id"], "| request_id:", built["request_id"])
    print("faces:", len(built["geometry"]["positions"]) // 4,
          "positions:", len(built["geometry"]["positions"]),
          "indices:", len(built["geometry"]["indices"]))
    print("stitched render:", OUT_DIR / "texel_connected_surface_render.png")
    print("comparison:", comparison)
    print("source unchanged:", PINNED_SHA256)


if __name__ == "__main__":
    main()
