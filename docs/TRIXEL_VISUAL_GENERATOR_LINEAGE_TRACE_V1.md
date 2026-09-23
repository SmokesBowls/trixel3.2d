# TRIXEL VISUAL GENERATOR LINEAGE TRACE V1

**Classification:** Read-only archaeology, narrow follow-up. No code moved, edited,
repaired, or promoted anywhere. No 3.2d implementation.

**Framing constraint, stated explicitly per instruction:** Trixel Composer (the
`terminal_trixel.py` / `enhanced_trixel_core.py` / `empire_bridge.py` lineage traced
below) is its own system with its own identity — an autonomous terminal pixel-art
agent, older and larger in scope than the current `trixel3.2d` rebuild. Nothing
below proposes merging Composer wholesale into `trixel3.2d`, and `trixel3.2d` is not
treated as Composer or as Composer's successor. `trixel3.2d` is a later, narrower
lineage that may eventually inherit specific *proven capabilities* from this
generation (a recipe format, a role taxonomy, an atlas convention) — it does not
absorb the product. Where trixel3.2d already visibly carries something forward
(see "Correction" section), that is noted as literal file inheritance, not identity
merger.

---

## 1. Was `tile_server.py` the pixel generator? No — confirmed, and now closed

Read in full (143 lines). It is exactly what the prior pass suspected: a thin
FastAPI transport wrapper. Its only two non-trivial imports are:

```python
from trixel_render_bridge import compile_scene, render_scene, DEFAULT_TILE_DIR
from atlas_composer import compose_atlas, list_terrain_types, read_atlas_meta
```

Every route handler (`/tile`, `/compile`, `/atlas`, `/atlas/list`, `/tile.png`,
`/health`) does argument validation, then calls straight into one of those two
imported functions and returns the result as JSON or a `FileResponse`. **No pixel
code exists in `tile_server.py` itself.** The chain had to be followed one more hop
in each direction.

---

## 2. The real chain, traced hop by hop

```
conductor/conductor_building_blocks/trixelcomposer/
  tile_server.py          (HTTP transport — confirmed, no pixel code)
       │ imports
       ▼
  atlas_composer.py       (ATLAS ASSEMBLY — confirmed generator of the terrain
                            atlas PNGs SemanticRenderer/TrixelTileClient consume)
       │ imports
       ├──▶ scene_server.py        (RECIPE SELECTION — picks which recipe JSON
       │                            applies for a given terrain/environment/scene_id)
       │
       └──▶ terminal_trixel.py     (PIXEL EXECUTION — TerminalCanvas + RecipeRenderer,
                                     the actual pixel-writing code)
```

### `atlas_composer.py` (263 lines) — confirmed atlas assembler

`compose_atlas(terrain, environment, seed)`:
1. Reads `atlas_meta.json` for the terrain (from `TRIXEL_ASSETS_ROOT`, which
   defaults to `.../godotnew/semantic/trixel/trixelassets`, matching what
   `SemanticRenderer.gd`/`TrixelAtlas.gd` read from the Godot side).
2. For every `role` string listed in that meta's `tile_order` array, calls
   `_render_role(terrain, role, environment, seed, index)`.
3. `_render_role()` builds a `scene_doc`, calls
   `scene_server.compile_recipe(scene_doc)` to get a recipe, applies a per-role
   RNG-seed offset (`role_seed = base_seed + role_index * 7919`) so adjacent tiles
   look distinct, looks up a role-specific geometric transform from a hardcoded
   `_ROLE_TRANSFORMS` dict (rotate/flip so a "pointing south" surface effect faces
   the correct exposed edge for that role), then:
   ```python
   canvas   = TerminalCanvas(recipe.get("canvas", {}).get("width", 16), ...)
   renderer = RecipeRenderer(canvas)
   renderer.execute(recipe)
   canvas.apply_transform(recipe.get("transform", {}))
   ```
4. Converts the resulting `TerminalCanvas` to a PIL Image, pastes it into the
   correct grid cell of the atlas image, and after all roles are done, saves
   `.zw/atlases/trixel_atlas_<terrain>_<seed>.png`.

**This is confirmed, real, executed code** — not just design intent: 6 pre-generated
example atlas PNGs already sit on disk in this exact repo
(`.zw/atlases/trixel_atlas_{cliff,forest_edge,rock,sand,shallow_water,shoreline}_42.png`),
proving `compose_atlas()` has actually run successfully for at least those 6
terrains.

### `scene_server.py` (288 lines) — confirmed recipe selector

`compile_recipe(scene_doc)`: resolves a terrain name via a 3-tier priority
(trixelmap region-authority lookup → keyword match in `scene_id` against a
`KEYWORD_OVERRIDES` table → `terrain_hint` passthrough), selects the best-matching
recipe JSON file from `recipes/terrain/*.json` (environment-aware, falls back to
`default`), loads it, injects `scene_id`/`terrain`/`entity_count`/canvas
size/deterministic per-pass RNG seeds (MD5 of `scene_id`), and returns the
compiled recipe dict. This is pure selection/injection logic — no pixel drawing.
Notably, it references `TRIXELMAP_RECIPE_PATH = .../trixelmap/out/trixelcomposer_recipe.json`
— the first concrete, locatable evidence this pass found of the "trixelmap" spatial-
authority system described only in narrative form (`TRIXEL_AUTHORITY_MAP.md`) in the
prior recovery-map pass; its actual output file was not located, but its expected
path/shape now is.

### `terminal_trixel.py` (1228 lines in this lineage, 980 in the original) — confirmed pixel executor

`class RecipeRenderer` (line 484) → `def execute(self, recipe, ...)` (line 490):
interprets the recipe's declared `passes` list and draws directly onto a
`TerminalCanvas` instance's pixel buffer. `class TerminalCanvas` (line 147) owns
the actual `canvas` 2D pixel array and `apply_transform()` (line 247, rotate/flip
per role). **This is where pixels are actually written**, full stop — every hop
above it is selection, seeding, or transport; every hop below it (atlas paste, PNG
save, HTTP response) is packaging.

---

## 3. Original vs. conductor lineage — file-by-file comparison

Reference root: `/home/mytruelove/Downloads/trixelcomposer-main/` (untouched
original — `terminal_trixel.py`, `enhanced_trixel_core.py`, `empire_bridge.py`,
`README.md`, `brush_tutorial_zw.txt`, `trixel composer research.txt`,
`trixel_creative_cycle.txt`, plus a `.zw/` working directory with real session/
artwork/memory files). Compared against
`conductor/conductor_building_blocks/trixelcomposer/`.

```
FILE: enhanced_trixel_core.py
CLASSIFICATION: ORIGINAL
EVIDENCE: byte-for-byte identical (diff exit 0) between the two roots, 592 lines both.
ROLE (per file, not independently re-read this pass beyond the diff): unclear from
  name alone what it implements versus terminal_trixel.py; not opened in this pass
  since it is provably unmodified and thus adds nothing new to trace.
```

```
FILE: empire_bridge.py
CLASSIFICATION: ORIGINAL
EVIDENCE: byte-for-byte identical (diff exit 0), 145 lines both. terminal_trixel.py's
  own bottom-of-file stubs (`enable_empire_mode()`, `launch_empire_collaborative_session()`)
  describe Empire mode as requiring optional `aiohttp` and a remote broker, disabled
  by default — i.e. this file was already an intentionally-stubbed optional
  integration point in the ORIGINAL repo, not something EngAIn broke or half-built.
```

```
FILE: terminal_trixel.py
CLASSIFICATION: EXTENSION (substantial, not a ground-up REWRITE — same module
  identity, same core class roster largely retained, real capability added on top)
EVIDENCE: 980 → 1228 lines (+248). Class roster comparison:
    ORIGINAL:  CreativePhase, ZWArtIntentManager, CreativeAction, TerminalCanvas,
               AutonomousCreativeMemory, SnapshotManager, ExperienceStore,
               TerminalTrixelComposer
    CONDUCTOR: CreativePhase, CreativeAction, ZWArtIntentManager, TerminalCanvas,
               AutonomousCreativeMemory, SnapshotManager, ExperienceStore,
               RecipeRenderer (NEW), TerminalTrixelComposer
  `TerminalCanvas` survives essentially in place (original line 141 → conductor
  line 147, both immediately after the same neighboring classes) — the base pixel-
  buffer primitive is an ORIGINAL carry. `RecipeRenderer` is a wholly NEW class,
  added specifically to interpret the JSON recipe format `scene_server.py`/
  `atlas_composer.py` depend on — the original Composer had no recipe-JSON concept
  at all; it worked from `CreativeAction`/autonomous-loop decisions instead. Other
  additions: `entity_layer` import (wires to the new `entity_layer.py`),
  `DEFAULT_SNAPSHOT_PATH`/`MEMORY_PATH`/`SESSION_DIR`/`ARTWORK_DIR` constants
  (formalizing paths that were likely inline/implicit before), `--recipe`/`--out`/
  `--no-autonomous` CLI flags (a new non-interactive entry point alongside the
  original's autonomous-loop-only design), proper `sys.exit()` codes and
  `traceback.print_exc()` on error (operational hardening).
```

```
FILE: atlas_composer.py, scene_server.py, trixel_render_bridge.py, tile_server.py
CLASSIFICATION: EXTENSION (new files, but built directly against Composer's own
  primitives — `atlas_composer.py` explicitly imports `RecipeRenderer`/`TerminalCanvas`
  from `terminal_trixel.py` and `compile_recipe` from `scene_server.py`; none of
  these are duplicate reimplementations)
EVIDENCE: none of these four filenames exist anywhere in the original
  `trixelcomposer-main` root. All four exist only in the conductor lineage. Their
  role is to adapt Composer's recipe/canvas primitives to a terrain-atlas,
  UV-topology-constrained output shape Composer itself never had a concept of
  (`atlas_meta.json`'s `tile_order`/`columns`/`tile_width`/`tile_height` contract).
```

```
FILE: composer_abi_adapter.py
CLASSIFICATION: RUNTIME_ADAPTER
EVIDENCE: own docstring: "Thin ABI adapters for legacy Trixel composer/editor
  systems. These adapters intentionally do not rewrite or mutate the historical
  composer implementations." 409 lines, new file, no original counterpart. This is
  the file `TRIXEL_AUTHORITY_MAP.md` described in the prior pass — now located and
  read (head only, this pass) — confirming its self-description matches its code:
  it explicitly refuses to modify Composer, only wraps it.
```

```
FILE: demand_resolver.py
CLASSIFICATION: RUNTIME_ADAPTER
EVIDENCE: own docstring: "Deterministic visual demand-resolution service layer.
  Transforms semantic runtime visual demands into deterministic visual artifact
  references while strictly preserving isolation from canonical world-state
  authority." 194 lines, new file. Hardcodes the same 9-terrain
  `REGISTERED_ATLAS_ENTRIES` set (`cliff, deep_water, forest_edge, grass, pier,
  rock, sand, shallow_water, shoreline`) as `TrixelAtlas.gd`'s
  `TERRAIN_DRAW_ORDER` — consistent, corroborating evidence across the Godot and
  Python sides of exactly which 9 terrain families were actually built out.
```

```
FILE: entity_layer.py
CLASSIFICATION: EXTENSION, self-described as incomplete
EVIDENCE: own docstring, quoted directly: "This module is the stub home for entity
  data as it moves through the rendering pipeline... Integration points (not yet
  wired): tile_address.py ..., scene_server.py ..., terminal_trixel.py RecipeRenderer
  routes entity_marker → here, not canvas." 104 lines. This is the file's own
  admission that entity-vs-terrain pixel separation was planned but not finished —
  directly relevant to the "any direct connection to ZW art intent" question below.
```

```
FILE: tile_address.py
CLASSIFICATION: EXTENSION, self-described as incomplete (per entity_layer.py's own
  "not yet wired" list, which names tile_address.py as one of its unfinished
  integration points)
EVIDENCE: own docstring: "A tile address encodes not just WHERE a cell is in the
  world, but WHICH face is visible and from WHICH direction the camera sees it,"
  format `{h_prefix}{x}.{v_prefix}{y}.{d_prefix}{z}` with direction prefixes
  d/u/l/r/f/b and a visible-face vocabulary (top/bottom/wall/slope/edge/side).
  247 lines, new file, no original counterpart. This is a real, thought-out 3D
  addressing scheme distinct from — and potentially relevant future context for —
  trixel3.2d's own cell/corner addressing (`addressing_v1.py`), though nothing here
  suggests the two were ever connected; they are independent designs solving a
  related problem from different codebases and eras.
```

```
FILE: recipes/terrain/*.json (10 files), recipes/transitions/*.json (5 files),
      recipes/schema/*.json (2 files)
CLASSIFICATION: DIRECT_DESCENDANT — into trixel3.2d specifically (see Correction §5)
EVIDENCE: see Correction section below — these are not merely similar to
  trixel3.2d's recipes, they are byte-identical to them.
```

---

## 4. The five responsibilities, kept distinct

```
generates pixels     → terminal_trixel.py :: RecipeRenderer.execute() + TerminalCanvas
                        (confirmed, real, run-proven by 6 on-disk example atlas PNGs)

assembles atlas       → atlas_composer.py :: compose_atlas()
                        (confirmed; reads atlas_meta.json's tile_order, pastes each
                        rendered role tile at the correct grid position, saves PNG)

serves files           → tile_server.py :: FastAPI routes on port 8766
                        (confirmed transport-only, no pixel logic — see §1)

selects visual role    → TrixelRoleResolver.gd (Godot, live consumer side) computing
                        which role a cell needs, AND atlas_composer.py's own
                        _ROLE_TRANSFORMS dict (Python, generator side) deciding how
                        to orient that role's drawn content — these are TWO SEPARATE
                        role-aware components on two sides of the seam, not one.
                        See §5 for the taxonomy mismatch between them.

renders in Godot        → SemanticRenderer.gd :: _spawn_terrain_cell() /
                        TrixelAtlas.gd's preview scene — consumes the finished PNG
                        + atlas_meta.json rects; performs zero pixel generation of
                        its own.
```

---

## 5. Taxonomy reconciliation with the prior godotnew trace

The prior pass (`TRIXEL_GODOTNEW_WORKING_SNAPSHOT_TRACE_V1.md`) found
`TrixelRoleResolver.gd` only ever produces 16 role strings and concluded the user's
hypothesized `inner_*`, `path_turn`, `path_t`, `path_cross` roles "don't exist in
code." That conclusion is now **refined, not overturned**: those roles genuinely
don't exist in `TrixelRoleResolver.gd` (the live Godot consumer), but they **do**
exist, fully implemented, on the generator side:

- `atlas_composer.py`'s `_ROLE_TRANSFORMS` dict explicitly defines transforms for
  `inner_ne/nw/se/sw`, `path_turn_ne/nw/se/sw`, `path_cross`, and `path_t_n/s/e/w` —
  exactly the roles the user originally hypothesized.
- The `pier` terrain's real `atlas_meta.json` (on disk) declares a `tile_order` of
  **29 roles**, including the full `path_turn_*`/`path_t_*`/`path_cross` family and
  `inner_ne/nw/se/sw` — i.e. real, generated tile art exists for these roles.
- The `rock` terrain's `atlas_meta.json` declares 14 roles including all four
  `inner_*` corners (rock has no path roles, consistent with it not being a
  linear/path-like terrain).

**So the corrected picture is:** the asset-generation side (Python,
`atlas_composer.py` + the `atlas_meta.json` contracts) was built for the full rich
taxonomy the user hypothesized. The one live Godot role-selection function this
project has actually traced (`TrixelRoleResolver.gd`) implements only a strict
subset of that taxonomy and can never request an `inner_*`, `path_turn_*`,
`path_t_*`, or `path_cross` tile — meaning real drawn tiles for those roles exist on
disk but nothing in the traced Godot code path can ever select them. Whether a
richer, still-unlocated role resolver exists elsewhere (to actually reach those
tiles) is UNKNOWN — not found in this pass, and out of this pass's scope to search
for further.

---

## 6. Proof-target chain, filled with real evidence

```
request / intent
   ↓  (scene_id, terrain hint, environment, seed)
generator entry point
   ↓  atlas_composer.compose_atlas(terrain, environment, seed)   [CONFIRMED, real code]
recipe / palette / brush / procedural decisions
   ↓  scene_server.compile_recipe(scene_doc)                     [CONFIRMED, real code]
   ↓  → selects one recipes/terrain/<terrain>.<variant>.json file
individual tiles or material surfaces
   ↓  terminal_trixel.RecipeRenderer(canvas).execute(recipe)     [CONFIRMED, real code —
   ↓  canvas.apply_transform(role_transform)                      pixels literally written here]
atlas assembly, if applicable
   ↓  atlas_composer._render_role() pastes each tile into the atlas image
      at the position atlas_meta.json's tile_order/columns dictate  [CONFIRMED]
PNG / metadata output
   ↓  .zw/atlases/trixel_atlas_<terrain>_<seed>.png (6 real examples exist on disk)
      + returned {"terrain", "png", "meta"} JSON                  [CONFIRMED]
tile_server.py
   ↓  GET /atlas?terrain=&environment=&seed=  → same JSON shape   [CONFIRMED, §1]
TrixelTileClient
   ↓  Image.load_from_file(png_path) → ImageTexture, cached       [CONFIRMED, prior pass]
SemanticRenderer
   ↓  _spawn_terrain_cell() applies the texture + atlas rect to a rendered tile [CONFIRMED, prior pass]
```

**Every link in this chain is now confirmed with located, read code or on-disk
artifacts — not inferred.** The one part of the original task's target list that
was actively searched for and NOT found: a connection specifically to **numbered
building-material sheets** (the `building_material_sheet.png` with plaster/timber/
shingle/sandstone/glass/metal rows). A case-insensitive search for
`plaster|stucco|shingle|building_material` across the entire
`conductor/conductor_building_blocks/trixelcomposer/` directory returned **zero
hits**. This chain is confirmed to be **terrain-atlas-only** — the 9 registered
terrain families (`cliff, deep_water, forest_edge, grass, pier, rock, sand,
shallow_water, shoreline`) never include any building-material vocabulary anywhere
in this lineage. The building-material-sheet generator remains genuinely
unlocated; it is a different system than the one traced in this document. No
"variable pixel-density output" concept and no direct "ZW art intent" connection
beyond `entity_layer.py`'s self-described unfinished stub were found either — see
§7 below.

---

## 7. Other target items from the task, addressed directly

- **Recipe-driven pixel art:** confirmed, this whole chain IS recipe-driven pixel
  art (`recipes/terrain/*.json` → `RecipeRenderer.execute()`).
- **Variable pixel-density output:** not found. Every recipe/canvas reference this
  pass observed hardcodes 16×16 (`recipe.setdefault("canvas", {})["width"] = 16`
  in `scene_server.py`; `TILE_SIZE = 16` in `TrixelAtlas.gd`/`SemanticRenderer.gd`).
  No variable-resolution or LOD concept was found anywhere in this chain.
- **Direct connection to ZW art intent:** partial. The ORIGINAL `terminal_trixel.py`
  has a `ZWArtIntentManager` class (present in both original and conductor copies,
  survived as an ORIGINAL-lineage carry) and writes real `.zw/artwork/*.png` +
  `.zw/sessions/*.json` + `.zw/memory.json` — this is Composer's own autonomous
  creative-loop persistence, genuinely working (real files present, matching
  timestamps across both the original and conductor `.zw/` trees). But the
  RECIPE/ATLAS pipeline traced in this document (`atlas_composer.py` et al.) does
  **not** call into `ZWArtIntentManager` or `.zw/artwork` at all — it is a separate,
  parallel invocation path through `RecipeRenderer` that bypasses the autonomous
  ZW-intent loop entirely. So: ZW art intent is real and working for Composer's own
  autonomous/interactive mode, but the terrain-atlas generation chain this document
  traces does not use it.

---

## 8. Corrections to prior documents

1. **`tile_server.py` is confirmed as transport-only, closing the open question
   from `TRIXEL_GODOTNEW_WORKING_SNAPSHOT_TRACE_V1.md` §8 item 4.** The actual
   generator is `atlas_composer.py` (assembly) → `scene_server.py` (selection) →
   `terminal_trixel.py::RecipeRenderer` (pixel execution), all confirmed by reading,
   not inference, and corroborated by 6 real generated atlas PNGs already on disk.

2. **New correction to `TRIXEL_LEGACY_CAPABILITY_RECOVERY_MAP.md`'s §4 (Visual/Art
   Realization) characterization of `trixel3.2d/trixel/trixel_recipe_renderer.py`**
   — not requested as the mandatory corrective note but too significant to omit:
   the prior map described trixel3.2d's recipe renderer as structurally similar to
   but independent of legacy's art stack. This pass found that is **understated**.
   `trixel3.2d/recipes/terrain/forest.dense_canopy.json` and
   `trixel3.2d/recipes/transitions/grass_to_dirt.json` were diffed directly against
   `conductor/conductor_building_blocks/trixelcomposer/recipes/...` and are
   **byte-identical**, and the full recipe file listing (10 terrain + 5 transition +
   3 schema files) matches exactly between the two directories. `trixel3.2d`'s own
   `trixel_recipe_renderer.py` even reuses the class names `Canvas`/`RecipeRenderer`
   and an `execute(self, recipe)` method signature, mirroring this lineage's own
   naming. **The recipe FILES are a literal, direct carry from the conductor
   trixelcomposer lineage into trixel3.2d — not an independent reinvention.** This
   does not change the prior map's conclusion that trixel3.2d's *renderer code* is
   a small, standalone reimplementation with no brush/palette/material asset model
   underneath it (that remains true and confirmed) — but the recipe *content* it
   renders was inherited wholesale, not authored fresh. Per the framing constraint
   at the top of this document, this is file inheritance, not evidence that
   trixel3.2d is or should become Composer.

3. **The four-file EngAIn runtime spine correction** was applied directly to
   `TRIXEL_LEGACY_CAPABILITY_RECOVERY_MAP.md` next to its `http_handlers.py` file
   record (see that document). Summary: `tier2/godotsim/http_handlers.py` must not
   be read as EngAIn's day-1 server identity; the real spine is `launchengine.py` +
   `simruntime.py` + `engainos/server.py` + `engainos/http_handlers.py`, not yet
   traced (pending follow-up, explicitly out of scope for this pass).
