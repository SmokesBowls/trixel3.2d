from __future__ import annotations

import sys
import json
import hashlib
from pathlib import Path
from PIL import Image
import jsonschema

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

def _print_gate(name: str, ok: bool, message: str = "") -> bool:
    status = "TRUE" if ok else "FALSE"
    suffix = f" — {message}" if message else ""
    print(f"[TUNDRA_RECIPE_RENDER][{name}] {status}{suffix}")
    return ok

def main() -> int:
    checks: list[bool] = []

    # 1. Paths
    recipe_path = REPO_ROOT / "recipes" / "terrain" / "tundra.frozen_plain.json"
    schema_path = REPO_ROOT / "recipes" / "schema" / "trixel_recipe.schema.json"
    golden_png_path = REPO_ROOT / "fixtures" / "tundra_texture.png"
    renderer_path = REPO_ROOT / "trixel" / "trixel_recipe_renderer.py"

    checks.append(_print_gate("RECIPE_FILE_EXISTS", recipe_path.exists()))
    checks.append(_print_gate("SCHEMA_FILE_EXISTS", schema_path.exists()))
    checks.append(_print_gate("GOLDEN_PNG_EXISTS", golden_png_path.exists()))
    checks.append(_print_gate("RENDERER_EXISTS", renderer_path.exists()))

    if not all(checks[:4]):
        print("[TUNDRA_RECIPE_RENDER][ALL_GATES] false")
        return 1

    # 2. Recipe Schema Validation
    with open(recipe_path, "r") as f:
        recipe = json.load(f)
    with open(schema_path, "r") as f:
        schema = json.load(f)

    schema_valid = True
    try:
        jsonschema.validate(instance=recipe, schema=schema)
    except Exception as exc:
        schema_valid = False
        print(f"Schema validation failed: {exc}")

    checks.append(_print_gate("RECIPE_SCHEMA_VALID", schema_valid))

    # 3. Canvas is 16x16
    canvas = recipe.get("canvas", {})
    canvas_is_16 = canvas.get("width") == 16 and canvas.get("height") == 16
    checks.append(_print_gate("CANVAS_IS_16X16", canvas_is_16))

    # 4. Passes validation
    passes = recipe.get("passes", [])
    has_gradient = any(p.get("type") == "gradient_fill" for p in passes)
    has_noise = any(p.get("type") == "noise_scatter" for p in passes)
    has_h_band = any(p.get("type") == "h_band" for p in passes)
    has_entity_marker = any(p.get("type") == "entity_marker" for p in passes)

    checks.append(_print_gate("GRADIENT_FILL_DECLARED", has_gradient))
    checks.append(_print_gate("NOISE_SCATTER_DECLARED", has_noise))
    checks.append(_print_gate("H_BAND_DECLARED", has_h_band))
    checks.append(_print_gate("ENTITY_MARKER_DECLARED", has_entity_marker))

    # 5. Render deterministic test PNG
    import trixel.trixel_recipe_renderer as renderer

    temp_png_path = REPO_ROOT / "fixtures" / "tundra_texture_temp.png"
    
    canvas_obj = renderer.Canvas(16, 16)
    renderer_obj = renderer.RecipeRenderer(canvas_obj)
    renderer_obj.execute(recipe)
    canvas_obj.save_png(temp_png_path)

    # 6. Verify PNG properties
    img = Image.open(temp_png_path)
    png_is_16 = img.size == (16, 16)
    checks.append(_print_gate("PNG_IS_16X16", png_is_16))

    colors = img.getcolors(256)
    unique_colors_count = len(colors)
    checks.append(_print_gate("PNG_HAS_19_UNIQUE_COLORS", unique_colors_count == 19, f"found={unique_colors_count}"))

    # Entity marker color [255, 255, 100] omitted check
    color_list = [c[1] for c in colors]
    entity_marker_omitted = (255, 255, 100) not in color_list
    checks.append(_print_gate("ENTITY_MARKER_OMITTED_FROM_PNG", entity_marker_omitted))

    # 7. Compare regenerated PNG hash against committed golden PNG
    with open(temp_png_path, "rb") as f:
        temp_hash = hashlib.sha256(f.read()).hexdigest()
    with open(golden_png_path, "rb") as f:
        golden_hash = hashlib.sha256(f.read()).hexdigest()

    hashes_match = temp_hash == golden_hash
    checks.append(_print_gate("REGENERATED_PNG_HASH_MATCHES_GOLDEN", hashes_match, f"temp={temp_hash}, golden={golden_hash}"))

    # Clean up temp file
    if temp_png_path.exists():
        temp_png_path.unlink()

    # 8. Assert no Godot dependency in promoted renderer
    renderer_src = renderer_path.read_text(encoding="utf-8")
    has_godot_dep = "godot" in renderer_src.lower() or "displayserver" in renderer_src.lower()
    checks.append(_print_gate("NO_GODOT_DEPENDENCY_IN_RENDERER", not has_godot_dep))

    # 9. Existing WorldField projection gate still passes
    import trixel.gates.gate_worldfield_to_worldcell_projection_contract as proj_gate
    proj_ok = proj_gate.main() == 0
    checks.append(_print_gate("WORLDFIELD_PROJECTION_GATE_PASSES", proj_ok))

    all_ok = all(checks)
    print(f"[TUNDRA_RECIPE_RENDER][ALL_GATES] {'true' if all_ok else 'false'}")
    return 0 if all_ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
