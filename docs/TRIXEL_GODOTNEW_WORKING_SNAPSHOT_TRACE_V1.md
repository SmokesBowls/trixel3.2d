# TRIXEL GODOTNEW WORKING-SNAPSHOT TRACE V1

**Classification:** Read-only archaeology, narrow follow-up to
`TRIXEL_LEGACY_CAPABILITY_RECOVERY_MAP.md`. No code moved, edited, repaired, or
promoted anywhere. `/home/mytruelove/Downloads/godotnew/` is treated as a specimen
to trace outward from, not as authority, and nothing from it has been copied into
`trixel3.2d`.

**Specimen root:** `/home/mytruelove/Downloads/godotnew/semantic/`. All eight target
files were found at exactly the paths given in the task, no layout adjustment needed.

**Byte-identity check against the prior pass's copy**
(`/mnt/data-drive/burdens_of_a_forgotten_past/EngAIn/godotnew/semantic/`):
`autoload/SimClient.gd`, `autoload/ArtworkClient.gd`, `autoload/TrixelTileClient.gd`,
`trixel/TrixelEnvironmentPlanner.gd`, `trixel/TrixelRoleResolver.gd`,
`trixel/TrixelAtlas.gd`, and `scripts/SemanticRenderer.gd` are all **byte-identical**
between the two copies (`diff` exit code 0). Only `Main.gd` differs, in exactly two
lines (see below) — this Downloads copy is not a divergent fork of the logic, it is
the same logic with two different hardcoded manifest paths.

---

## Per-file extraction (external references, quoted verbatim)

### Main.gd

```gdscript
const WORLD_RULES_PATH := "/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/tier1/engainos/assets/world_rules.json"
```
```gdscript
var manifest_path := "/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/tier1/engainos/assets/engain_manifest.json"
```
These are the **two lines that differ** from the other copy, which instead reads
`.../EngAIn/manifests/world_rules.json` and `.../EngAIn/manifests/engain_manifest.json`.
**Verified: this Downloads copy's paths exist on disk; the other copy's paths do
not** (see "Cross-check" section below) — this is the first concrete evidence this
copy really is the more working-era of the two.

Other external references in `Main.gd` (unchanged from the prior pass's reading,
re-confirmed present in this copy):
- `http.request("http://127.0.0.1:8080/snapshot")` — polls the SimClient-backed runtime server directly via a raw `HTTPRequest`, independent of the `SimClient` autoload, as a fallback/watchdog path (`_fetch_server_commit_fallback_snapshot`, `_fetch_snapshot_with_token`).
- Disk snapshot path used by the `F9` debug key: `"pass_to_render/snapshots/scene.030_ummade_army.snapshot.json"` — **this exact file is physically present** in this specimen at `semantic/pass_to_render/snapshots/scene.030_ummade_army.snapshot.json` (1429 bytes).
- Depends on autoloads `SimClient` and `SceneClient` (signals: `SimClient.sim_response`, `SceneClient.scene_loaded.emit(...)`), and on a `Boot` node found via group `"engain_boot"` or `find_child("Boot", true, false)`, calling `boot.accept_main_owned_scene_for_layout(...)` and `boot.set_accept_scene_from_signal(...)` / `boot.set_hydration_suppression(...)` if present.

### autoload/SimClient.gd

```gdscript
@export var sim_base: String = "http://127.0.0.1:8080"
```
POSTs to `%s/scene/load`, `%s/command`; GETs `%s/snapshot`, `%s/embodiment/pending`.
No filesystem paths referenced — pure HTTP client, all state server-side.

### autoload/ArtworkClient.gd

```gdscript
@export var api_base: String = "http://127.0.0.1:8090"
```
```gdscript
var url: String = "%s/api/trixel/artwork/%s" % [api_base, scene_id.uri_encode()]
```
A **third, separate HTTP service** (port 8090) from SimClient's 8080. Fetches a PNG
directly as the HTTP response body (`img.load_png_from_buffer(body)`), not a JSON
envelope with a path. Never referenced by `Main.gd`, `SemanticRenderer.gd`, or any
other file read this pass — appears to be a wired-but-unused (or used-elsewhere,
not-yet-located) client.

### autoload/TrixelTileClient.gd

```gdscript
const HOST := "127.0.0.1"
const PORT := 8766
```
```gdscript
var url := "http://%s:%d/atlas?terrain=%s&environment=%s&seed=%d" % [HOST, PORT, terrain.uri_encode(), environment.uri_encode(), seed]
```
```gdscript
var url := "http://%s:%d/tile?scene_id=%s&terrain=%s&environment=%s" % [HOST, PORT, scene_id.uri_encode(), terrain.uri_encode(), environment.uri_encode()]
```
A **fourth, separate HTTP service** (port 8766). Both `/atlas` and `/tile` return
JSON with a `"png"` field that is a **filesystem path**, then loaded locally via
`Image.load_from_file(png_path)` — i.e. the server writes a PNG to disk and hands
back the path, rather than streaming image bytes. This is the client
`SemanticRenderer._load_atlas_for()` calls for `MODE_RECIPE_3D` / `MODE_COMPOSER_2_3D`.

### trixel/TrixelEnvironmentPlanner.gd

```gdscript
const WORLD_FIELD_SCRIPT := "/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/terrain/trixel_world_adapter.py"
```
Byte-identical to the prior pass's copy — **same dead path**, re-verified missing
this pass (`EngAIn/terrain/` does not exist; see Cross-check below).

Also shells out via `OS.execute("python3", args, ...)` with args including
`--demo --width --height --context-file <tmp> --scene-json <source_path> --scene-id <id>`,
writing a temp context file to `/tmp/engain_wf_context_%s.json`. Loads
`primitive_vocabulary_bindings.json` via `initialize_vocabulary_bindings(bindings_path)`
— present in this specimen at `semantic/primitive_vocabulary_bindings.json`, real
content confirmed (9 terrain-alias mappings, e.g. `"basalt": "rock"`,
`"forest": "forest_edge"`).

### trixel/TrixelRoleResolver.gd

No external paths, no HTTP, no autoload dependency — pure static function over an
in-memory `Array` grid. Full deep-dive below.

### trixel/TrixelAtlas.gd

```gdscript
const ASSET_ROOT := "res://trixel/trixelassets"
```
Loads, per terrain in a fixed draw order (`deep_water, shallow_water, shoreline,
sand, grass, forest_edge, pier, rock, cliff`): `<ASSET_ROOT>/<terrain>/manifest.json`,
`<ASSET_ROOT>/<terrain>/atlas_meta.json`, `<ASSET_ROOT>/<terrain>/atlas.png`. This is
a **self-contained preview/debug scene** (`extends Node2D`, has its own `_draw()`),
not a dependency of `SemanticRenderer.gd` — it builds its own 20x16 sample grid and
its own **second, independent copy** of the exact same role-resolution algorithm as
`TrixelRoleResolver.gd` (see duplication note below), rather than calling the shared
resolver.

### scripts/SemanticRenderer.gd

```gdscript
const ATLAS_ROOT := "res://trixel/trixelassets"
```
Confirmed unchanged from prior pass: calls `TrixelEnvironmentPlanner.resolve_tile_alias(terrain)`
(direct dependency on the planner's in-memory vocabulary cache), calls
`get_node_or_null("/root/TrixelTileClient")` and `tc.fetch_atlas(terrain)` /
`tc.get_cached_atlas(terrain)` (direct dependency on the TrixelTileClient autoload,
port 8766), reads `<ATLAS_ROOT>/<terrain>/atlas_meta.json` and `atlas.png` as the
static/fallback source. Also consumes an "embodiment contract"
(`apply_embodiment_contract`) with a hardcoded required
`contract_version = "trixel_embodiment.v1"` and `materialization.authority == "SemanticRenderer"`,
loading `materialization.recipe_texture_path` from disk via `Image.load_from_file()`.

---

## Wiring trace (as actually found)

```
GODOTNEW WORKING SNAPSHOT  (specimen: /home/mytruelove/Downloads/godotnew/semantic/)

Main.gd
   ↓ reads at startup
world_rules.json + engain_manifest.json
   = /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/tier1/engainos/assets/{world_rules,engain_manifest}.json
   → BOTH FILES EXIST (confirmed). This differs from the OTHER godotnew copy
     (/mnt/data-drive/.../EngAIn/godotnew/semantic/Main.gd), which hardcodes
     EngAIn/manifests/{world_rules,engain_manifest}.json — CONFIRMED MISSING
     (that manifests/ dir only holds legacy_root_artifacts/ and relocation_proof/).

Main.gd
   ↓ engain_manifest.json → active.scene_library = "latest_ingested"
   ↓                         .index =
scene_index.json = EngAIn/tier3/mettaext/loaded/scene_index.json
   → EXISTS (confirmed) — this is real output of the mettaext passroom pipeline
     traced in the prior recovery map.

Main.gd
   ↓ engain_manifest.json → active.asset_pack = "debug_placeholders"
   ↓                         .manifest =
assets.manifest.json = EngAIn/assets/debug_placeholders/assets.manifest.json
   → MISSING (confirmed). Consequence: Main.gd's `_spawn_bridge_entity()` "scene"
     mode (loading a real mapped Godot scene per entity) cannot resolve; every
     entity falls back to the hardcoded "procedural_capsule" placeholder path.
     This is a second, independently confirmed broken link, distinct from the
     WorldField one.

Main.gd
   ↓ calls / expects
SimClient (autoload)
   ↓ endpoint
http://127.0.0.1:8080  → /scene/load (POST), /snapshot (GET), /command (POST),
                          /embodiment/pending (GET)
   → server-side handler previously located: EngAIn/tier2/godotsim/http_handlers.py
     (unchanged finding from the prior pass; not re-verified running this pass)

Main.gd
   ↓ ALSO directly (bypassing SimClient) on the fallback/watchdog path
http://127.0.0.1:8080/snapshot  (raw HTTPRequest)

Main.gd  (F9 debug key)
   ↓ reads from disk directly, no server involved
pass_to_render/snapshots/scene.030_ummade_army.snapshot.json
   → PRESENT in this specimen (1429 bytes) alongside its source scene doc
     pass_to_render/scenes/scene.030_ummade_army.min.json (550 bytes) — this is
     the exact scene the user flagged as matching what the runtime loads.

Main.gd
   ↓
TrixelEnvironmentPlanner.plan()
   ↓ invokes (OS.execute python3)
EngAIn/terrain/trixel_world_adapter.py
   → STILL DEAD in this specimen too (byte-identical file to the other copy;
     EngAIn/terrain/ directory confirmed NOT to exist). This one specific hop is
     CONFIRMED broken in BOTH copies — not refined, not contradicted, re-confirmed
     independently.
   ↓ on failure, falls through to
_generate_base_grid() + _apply_environment_rules()  (pure GDScript, no external dep)
   ↓ produces
{terrain_grid, prop_placements, landmark_nodes, terrain_family, environment, map_size}
   NOTE: the planner never produces or emits a literal "TRIXEL_PLAN" object — that
   string is only ever a PRINT LABEL (`print("[TRIXEL_PLAN] source=...")`), not a
   contract/struct name. The actual returned value is the Dictionary shown above.
   This corrects an implicit assumption in the task's trace skeleton.

TrixelEnvironmentPlanner (via resolve_tile_alias, used by SemanticRenderer)
   ↓ backed by
primitive_vocabulary_bindings.json  (present in this specimen, real 9-entry alias table)

SemanticRenderer.gd  (._spawn_terrain_grid → _load_atlas_for → TrixelRoleResolver.resolve_role)
   ↓ consumes
terrain_grid (from planner, or its own hardcoded 2-row default if planner never ran)
   ↓ resolves per-cell role via
TrixelRoleResolver.resolve_role(grid, x, y, terrain)   [see deep-dive below]
   ↓ resolves texture SOURCE via
RenderPolicy.resolve(terrain) → one of atlas_2d | recipe_3d | composer_2_3d | custom_upload
   ↓ atlas_2d/composer_2_3d fallback reads
res://trixel/trixelassets/<terrain>/{manifest.json, atlas_meta.json, atlas.png}
   ↓ recipe_3d/composer_2_3d "live" path calls
TrixelTileClient.fetch_atlas(terrain, environment, seed)
   ↓ endpoint
http://127.0.0.1:8766/atlas?terrain=...&environment=...&seed=...
   → SERVER LOCATED this pass: conductor/conductor_building_blocks/trixelcomposer/tile_server.py
     (FastAPI; confirmed via `Runs on port 8766, separate from godotengain (8765)
     and EngAInOS (8080)` in its own docstring, and route decorators
     `@app.get("/tile")`, `@app.get("/atlas")`, `@app.get("/atlas/list")`,
     `@app.get("/tile.png")`). This is a genuinely new finding relative to the
     prior recovery map's unresolved "who generates the material art" question —
     see the Corrections section below for what this does and doesn't answer.

SemanticRenderer.gd (separately)
   ↓ can also consume, when explicitly supplied
apply_embodiment_contract(contract)  — requires contract_version=="trixel_embodiment.v1"
   ↓ loads
materialization.recipe_texture_path  (disk path, generator not identified this pass)
   ↓ applies to
BlenderTerrainMount node (sibling under $World, resolved by node search, not a fixed path)
```

---

## TrixelRoleResolver.gd deep-dive

**Yes** — it is a real, working neighbor-aware role resolver, not just a
name-shaped stub. Read in full (65 lines). Exact algorithm:

```gdscript
static func resolve_role(grid: Array, x: int, y: int, terrain: String) -> String:
	var has_n := terrain_at(grid, x, y - 1) == terrain
	var has_s := terrain_at(grid, x, y + 1) == terrain
	var has_e := terrain_at(grid, x + 1, y) == terrain
	var has_w := terrain_at(grid, x - 1, y) == terrain
	var count := 0
	if has_n: count += 1
	if has_s: count += 1
	if has_e: count += 1
	if has_w: count += 1

	if count == 0: return "single"
	if count == 4: return "center"
	if count == 3:
		if not has_n: return "edge_n"
		if not has_s: return "edge_s"
		if not has_e: return "edge_e"
		if not has_w: return "edge_w"
	if count == 2:
		if has_s and has_e: return "corner_nw"
		if has_s and has_w: return "corner_ne"
		if has_n and has_e: return "corner_sw"
		if has_n and has_w: return "corner_se"
		if has_n and has_s: return "path_straight_v"
		if has_e and has_w: return "path_straight_h"
	if count == 1:
		if has_n: return "path_end_s"
		if has_s: return "path_end_n"
		if has_e: return "path_end_w"
		if has_w: return "path_end_e"
	return "center"
```

It counts which of the 4 cardinal neighbors share the same terrain type, then maps
the resulting pattern to one role string. It then feeds directly into
`SemanticRenderer._spawn_terrain_cell()`'s `rects.get(role, rects.get("center", ...))`
lookup against the atlas's `tile_order`-derived rect dictionary — i.e. **yes, this is
exactly the bridge the task hypothesized**: neighbor pattern → role name → concrete
atlas rect (and, transitively, a concrete pixel region of `atlas.png`).

**One deliberately-not-obvious detail worth flagging**: the corner naming is
counterintuitive on first read. `corner_nw` fires when `has_s and has_e` — i.e. when
the neighbors present are SOUTH and EAST, the role returned is named `corner_**nw**`.
This only makes sense under a convention where the role name describes which corner
of the OWN tile is "open" toward the missing neighbors (missing N and missing W →
the open corner faces northwest), not which neighbors are present. This is exactly
the kind of thing that looks like a bug on casual read but is a consistent, if
undocumented, convention — worth being careful about if this logic is ever ported.

**Role taxonomy comparison — user's hypothesis vs. actual code:**

| User hypothesized | Actually found in code | Verdict |
|---|---|---|
| `center` | `center` (count==4, and also the default fallback for any unhandled pattern) | CONFIRMED |
| `edge_n` / `edge_s` / `edge_e` / `edge_w` | present exactly as named (count==3 cases) | CONFIRMED |
| `corner_*` | present, but only 4 variants (`corner_nw/ne/sw/se`) using the inverted-open-corner convention above | CONFIRMED, naming convention clarified |
| `inner_*` | **not found anywhere in TrixelRoleResolver.gd or TrixelAtlas.gd** | NOT CONFIRMED — no "inner" role exists in the code read |
| `single` | present exactly (count==0) | CONFIRMED |
| `path_straight` | present, but SPLIT into two axis-specific variants: `path_straight_v` (N+S) and `path_straight_h` (E+W), not one generic `path_straight` | CONFIRMED with correction |
| `path_turn` | **not found** — the two-neighbor "adjacent" cases (e.g. N+E) all resolve to `corner_*`, not a `path_turn` role; there is no distinct turn concept | NOT CONFIRMED |
| `path_t` | **not found** — no 3-neighbor case returns anything path-shaped; all count==3 cases return `edge_*` | NOT CONFIRMED |
| `path_cross` | **not found** — count==4 always returns `center`, never a cross/junction role | NOT CONFIRMED |
| *(not hypothesized)* `path_end_n/s/e/w` | present (count==1 cases) — a role family the user's hypothesis didn't anticipate at all | NEW, extends the taxonomy |

**Actual full taxonomy (11 roles):** `single, center, edge_n, edge_s, edge_e, edge_w,
corner_nw, corner_ne, corner_sw, corner_se, path_straight_v, path_straight_h,
path_end_n, path_end_s, path_end_e, path_end_w` (16 if you count each fully — the
count==2/count==1 branches produce 6 and 4 distinct roles respectively). This reads
as a **general edge/corner/single tile-autotiling scheme with an added path-endpoint
family**, not a dedicated path-network scheme (no turn/T/cross concept exists) — the
`path_straight_*`/`path_end_*` roles look like they were added on top of a standard
9-16-tile autotiler specifically to support the `pier` terrain (a linear feature
running through water, matching the pier-placement logic seen in `TrixelAtlas.gd`'s
own sample-grid builder: *"Pier running from shoreline into the water"*), not a
general road/path network system.

**Duplication found:** `TrixelAtlas.gd` (lines 128-179) contains a **second,
independent, line-for-line-identical copy** of this exact algorithm as its own
private `_resolve_role()` method, rather than calling
`TrixelRoleResolver.resolve_role()`. Both copies were diffed by hand (not via the
`diff` tool, since they're different files/functions) and are logically identical.
This is a real, confirmed duplication — the kind of thing that would drift silently
if one copy were ever edited without the other.

**Atlas asset-family confirmation:** the atlas folder convention
(`res://trixel/trixelassets/<terrain>/{manifest.json, atlas_meta.json, atlas.png}`)
is confirmed for 9 terrain families (`deep_water, shallow_water, shoreline, sand,
grass, forest_edge, pier, rock, cliff` — `TrixelAtlas.gd`'s own `TERRAIN_DRAW_ORDER`
constant), matching the task's list. A spot-check via the earlier port-8766 grep
also turned up `.../trixelassets/rock/corner_se.png.import`, directly confirming a
`corner_se`-named asset exists on disk for at least one family — independent
corroboration that the role taxonomy above is really what drives asset selection,
not just what the code would produce in theory.

---

## Corrections/updates to `TRIXEL_LEGACY_CAPABILITY_RECOVERY_MAP.md`

1. **The WorldField bridge dead-path finding is CONFIRMED, not refined or
   contradicted.** This specimen's `TrixelEnvironmentPlanner.gd` is byte-identical
   and points at the exact same nonexistent `EngAIn/terrain/trixel_world_adapter.py`.
   Two independent copies of this file, in two different locations, both hardcode
   the same broken path — this looks like a real historical break, not a
   copy-specific accident.

2. **New, independently confirmed second broken link**: `Main.gd`'s entity→scene
   asset-mapping path (`asset_packs.debug_placeholders.manifest`) is also missing on
   disk in this specimen, meaning even a fully successful scene load would only ever
   spawn capsule placeholders for entities, never real character scenes, regardless
   of the WorldField outcome. This was not previously noted in the recovery map.

3. **This specimen is measurably closer to a working state than the copy used in
   the prior pass**, on the *manifest/world-rules* dependency specifically (both
   files exist here; neither exists at the other copy's hardcoded paths) — but is
   **exactly as broken on the WorldField dependency**. "More working-era" is true
   for one dependency, not a blanket property of the whole specimen.

4. **Partial answer to the prior pass's open thread ("who generates the numbered
   material sheet / terrain atlases?")**: `conductor/conductor_building_blocks/trixelcomposer/tile_server.py`
   is confirmed as the HTTP transport layer serving `TrixelTileClient`'s `/atlas`
   and `/tile` requests on port 8766. This is genuinely new information — it gives a
   concrete, locatable server process in the chain. **It is not itself confirmed to
   be the pixel generator** (its role, per its own routes, looks like a thin
   FastAPI wrapper — `/atlas/list`, `/tile.png` — sitting in front of whatever
   actually paints pixels, most plausibly the `trixelcomposer` core files named in
   `TRIXEL_AUTHORITY_MAP.md` (`enhanced_trixel_core.py` etc.), which live in the
   same `conductor/conductor_building_blocks/trixelcomposer/` directory this server
   was found in). This narrows the follow-up search considerably (from "search the
   whole filesystem for `trixelworld`" to "read `tile_server.py`'s handler bodies and
   whatever it imports from `conductor/conductor_building_blocks/trixelcomposer/`")
   but does not close the thread.

5. **Minor correction to the task's own trace skeleton**: `TRIXEL_PLAN` is not a
   data contract or object the planner "produces" — it is only ever a `print()`
   label in `TrixelEnvironmentPlanner.plan()`. The actual returned value is a plain
   Dictionary (`terrain_grid`, `prop_placements`, `landmark_nodes`, `terrain_family`,
   `environment`, `map_size`). Worth keeping the distinction clean in any future
   documentation, since "TRIXEL_PLAN" reads like a named contract but isn't one in
   the code as it exists.

6. **New evidence of deliberate multi-service orchestration**: `EngAIn/start_stack.fish`
   (found via the port-8766 grep, not fully read) implements guarded background
   process startup with port-listening checks, PID files, and per-service logs —
   real operational tooling for running this as a coordinated multi-server stack
   (Godot + EngAInOS:8080 + tile_server:8766 + presumably others), reinforcing that
   this was built and operated as a real running system at some point, not just
   designed on paper.

7. **Two more separate HTTP services confirmed** beyond the one (port 8080)
   documented in the prior pass: `ArtworkClient.gd` (port 8090, `/api/trixel/artwork/<scene_id>`)
   and `TrixelTileClient.gd` (port 8766, `/atlas`, `/tile`). The prior recovery map's
   Runtime/Consumer section only documented the 8080 service — the full legacy
   runtime was at least a 3-4 HTTP-service constellation, not one server.
