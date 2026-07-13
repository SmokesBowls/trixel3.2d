from __future__ import annotations

import sys
import json
from pathlib import Path
import jsonschema

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

def _print_gate(name: str, ok: bool, message: str = "") -> bool:
    status = "TRUE" if ok else "FALSE"
    suffix = f" — {message}" if message else ""
    print(f"[ALL_RECIPES_VALIDATION][{name}] {status}{suffix}")
    return ok

def main() -> int:
    checks: list[bool] = []

    # Paths
    terrain_dir = REPO_ROOT / "recipes" / "terrain"
    transitions_dir = REPO_ROOT / "recipes" / "transitions"
    recipe_schema_path = REPO_ROOT / "recipes" / "schema" / "trixel_recipe.schema.json"
    transition_schema_path = REPO_ROOT / "recipes" / "schema" / "trixel_transition_recipe.schema.json"

    # 1. Load schemas
    with open(recipe_schema_path, "r") as f:
        recipe_schema = json.load(f)
    with open(transition_schema_path, "r") as f:
        transition_schema = json.load(f)

    # 2. Validate all 10 terrain recipes
    terrain_recipes = list(terrain_dir.glob("*.json"))
    checks.append(_print_gate("TERRAIN_RECIPES_COUNT_IS_10", len(terrain_recipes) == 10, f"found={len(terrain_recipes)}"))

    for recipe_file in sorted(terrain_recipes):
        with open(recipe_file, "r") as f:
            instance = json.load(f)
        
        valid = True
        err_msg = ""
        try:
            jsonschema.validate(instance=instance, schema=recipe_schema)
        except Exception as exc:
            valid = False
            err_msg = str(exc)

        checks.append(_print_gate(f"TERRAIN_{recipe_file.name.upper()}_VALID", valid, err_msg))

    # 3. Validate all 5 transition recipes
    transition_recipes = list(transitions_dir.glob("*.json"))
    checks.append(_print_gate("TRANSITION_RECIPES_COUNT_IS_5", len(transition_recipes) == 5, f"found={len(transition_recipes)}"))

    for trans_file in sorted(transition_recipes):
        with open(trans_file, "r") as f:
            instance = json.load(f)
        
        valid = True
        err_msg = ""
        try:
            jsonschema.validate(instance=instance, schema=transition_schema)
        except Exception as exc:
            valid = False
            err_msg = str(exc)

        checks.append(_print_gate(f"TRANSITION_{trans_file.name.upper()}_VALID", valid, err_msg))

    all_ok = all(checks)
    print(f"[ALL_RECIPES_VALIDATION][ALL_GATES] {'true' if all_ok else 'false'}")
    return 0 if all_ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
