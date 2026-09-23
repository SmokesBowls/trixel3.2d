# TRIXEL LEGACY CAPABILITY RECOVERY MAP

**Classification:** Read-only archaeology. No code moved, edited, repaired, or promoted.
**Scope of this pass:** reconstruct what the old, larger Trixel/EngAIn pipeline could
actually do, which surviving files did each part, and how much of each capability
exists in `trixel3.2d` today. Nothing here authorizes implementation.

**Roots searched:** `~/Desktop/burdens_of_a_forgotten_past/` (EngAIn, conductor,
trixel_legacy_2d, texel-studio, trixel3.2d), `/mnt/data-drive/` (EngAIn_Recovery,
a second full copy of `burdens_of_a_forgotten_past/`, `New Folder/05_DO_NOT_TOUCH_ORIGINALS/`,
`intentioallyzipped/`, audit directories). Several trees exist multiply — e.g. there
are at least three copies of the `EngAIn/godotnew/semantic` Godot project
(`/mnt/data-drive/burdens_of_a_forgotten_past/...`, `/mnt/data-drive/New Folder/05_DO_NOT_TOUCH_ORIGINALS/EngAIn_runtime_candidate/...`,
and a `~/Downloads/godotnew` / `~/notebook/godotnew`). This map cites the copy at
`/mnt/data-drive/burdens_of_a_forgotten_past/EngAIn/godotnew/semantic/`, which matches
the screenshots (project title bar, console log lines) exactly. Where a file exists
in more than one copy, only the first-found path is cited; duplicates are noted
where relevant but not individually catalogued.

---

## Executive summary

Old Trixel was not one system — it was at least **five separable subsystems** wired
together by JSON/HTTP contracts, of which the current `trixel3.2d/trixel/pixel_geometry/`
proof ladder reconstructs **only one (Geometry Realization)**, and only a narrow slice
of that one (single-footprint compilation; no terrain-scale integration with the old
WorldField/TrixelWorld address space). The other four systems — narrative→scene
extraction, WorldField/TrixelWorld generation, the brush/material/recipe stack, and
the Godot semantic runtime — are legacy-only or partially rebuilt in a *different*,
disconnected form (`trixel_recipe_renderer.py` in the terrain lane) inside `trixel3.2d`.
There is direct visual proof (the shared screenshots) that the old pipeline produced
a real, walkable, textured terrain grid end-to-end at least once. There is no
evidence current `trixel3.2d` can reproduce that.

---

## 1. NARRATIVE / SEMANTIC INTERPRETATION

**What the evidence shows it could do:** take raw manuscript chapters, extract claims/
entities (MrLore), segment into scenes, classify each scene's terrain/environment
profile from prose keywords, and emit a game-ready scene JSON with entities,
positions, and a `terrain_family`/`environment` classification — all without a human
manually describing the world.

```
FILE: /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/tier3/mettaext/semantic_environment_extractor.py
ROLE: classifies prose into one of 9 environment profiles (coastal, forest, wasteland,
  industrial, volcanic, underground, cosmic, urban, default) and a scale hint (tiny..massive)
  via keyword tables (PROFILE_KEYWORDS, SCALE_KEYWORDS).
INPUT: prose text (chapter/scene text)
OUTPUT: {profile, confidence, scale_hint, ...} (module continues past what was read)
CALLS: none observed upstream of stdlib
CALLED BY: pipeline_runner.py / master_pipeline.py (per module docstrings); referenced
  conceptually by TrixelEnvironmentPlanner.gd's `environment_inference` field handling
PIPELINE POSITION: narrative → environment-intent classification (first machine step
  after raw text)
RUNNABILITY: unknown (pure-Python, no obviously broken imports in the head read; not executed)
DEPENDENCIES: stdlib only (argparse, json, re, pathlib) in the portion read
DUPLICATES/DESCENDANTS: none found
WORKING EVIDENCE: none directly observed for this file; downstream scene JSON (see
  pass5_game_bridge.py below) carries `terrain_family`/`environment` fields consistent
  with this classifier's output shape
CURRENT TRIXEL3.2D EQUIVALENT: ABSENT — no narrative/prose-to-environment classifier
  exists anywhere in trixel3.2d
STATUS: LEGACY_ONLY
```

```
FILE: /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/tier3/mettaext/passroom/pass5_game_bridge.py
ROLE: "ZON Memory Fabric → Game Scene." Converts Pass4 ZON output (structured entity/
  claim memory) into game-ready scene JSON, including a large keyword→terrain_family/
  environment voting registry (`_VOTING_KEYWORD_REGISTRY`, e.g. "ash"→ash/wasteland,
  "volcano"→ash/volcanic) used to infer environment from prose descriptors when no
  explicit tag exists.
INPUT: Pass4 `.zonj.json` files (ZON compiled output)
OUTPUT: game scene JSON (entities, terrain_family, environment, etc.)
CALLS: none observed beyond stdlib in the head read
CALLED BY: pipeline_runner.py (per master_pipeline.py's delegation)
PIPELINE POSITION: narrative (ZON memory) → runtime scene document, immediately
  upstream of TrixelEnvironmentPlanner.gd's `plan()` entrypoint
RUNNABILITY: unknown, not executed this pass
DEPENDENCIES: stdlib (json, re, argparse, pathlib)
DUPLICATES/DESCENDANTS: `pass5_game_bridge.py.bak_spatial_wire_20260702_070004` exists
  alongside it — an earlier revision kept as a backup, not deleted
WORKING EVIDENCE: real generated output exists at
  `EngAIn/godotnew/semantic/pass_to_render/scenes/scene.001_the_ethereal_vigil.min.json`
  and `scene.030_ummade_army.min.json`, plus a matching runtime snapshot at
  `pass_to_render/snapshots/scene.030_ummade_army.snapshot.json` — these are the actual
  artifacts `Main.gd`'s scene chooser loads and POSTs to the runtime server (see §5)
CURRENT TRIXEL3.2D EQUIVALENT: ABSENT
STATUS: LEGACY_ONLY
```

```
FILE: /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/tier3/mettaext/  (passroom/pass1_explicit.py, pass1_spatial.py, pass2_entity_filter.py, pass2_event_builder.py, pass2_enhanced.py, pass3_merge.py, pass4_zon_bridge.py, passroom_bridge.py)
ROLE: a 5-stage "passroom" (pass1..pass5) narrative compiler: explicit/spatial
  extraction → entity filtering/event building → merge → ZON bridge → game bridge.
INPUT: chapter text / chapter packets from `chapterroom/`
OUTPUT: `.zon` / `.zonj.json` files per scene, staged under
  `tier3/mettaext/stageroom/output/passroom/<scene>/`
CALLS: chained pass1→pass2→pass3→pass4→pass5 per `pipeline_runner.py`
CALLED BY: `master_pipeline.py` (compatibility wrapper), `pipeline_runner.py` (canonical)
PIPELINE POSITION: core of Narrative/Semantic Interpretation
RUNNABILITY: unknown; extensive `.bak_*` sibling files (e.g.
  `pass2_entity_filter.py.bak_world_rules`, `pipeline_runner.py.bak_pass1_spatial_20260702_071252`)
  indicate active, iterative repair work in progress at time of capture — a sign of
  partial instability, not proof of breakage
DEPENDENCIES: unknown, not traced import-by-import in this pass
DUPLICATES/DESCENDANTS: `.bak_*` files throughout `tier3/mettaext/` are earlier
  revisions kept in place, not separate implementations
WORKING EVIDENCE: real per-scene output directories with `.zon`, `.zonj.json`, and
  `out_pass1_*.txt` debug dumps exist for multiple chapters (e.g.
  `stageroom/output/passroom/scene.004_the_convergence.scene002/`), and
  `chapterroom/scene_packets/` holds real segmented scene text files
  (e.g. `scene.004_the_convergence.scene002.txt`) — direct evidence the pipeline ran
  against real manuscript chapters (`EngAIn/tier1/mrlore/raw/chapters/book_0*...md`)
CURRENT TRIXEL3.2D EQUIVALENT: ABSENT
STATUS: LEGACY_ONLY
```

```
FILE: /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/tier1/mrlore/  (mrlore_contradiction_candidate_audit_summary.py, mrlore_proposed_claim_audit_summary.py, mrlore_review_queue_noise_audit.py, mrlore_p3_sequential_entity_second_pass_quality_audit.py, raw/chapters/*.md)
ROLE: "MrLore" — claim/entity extraction and continuity auditing over the raw
  manuscript (`raw/chapters/book_0N_*.md`), feeding the passroom pipeline above.
  A separate, larger audit tree exists at `/mnt/data-drive/mrlore-audit/` with dated
  reports (e.g. `2026-09-18-g1-proof-only-audit.md`).
INPUT: manuscript chapter markdown
OUTPUT: claim/contradiction/entity audit summaries, feeding ZON compilation
CALLS/CALLED BY: unknown, not traced
PIPELINE POSITION: upstream-most stage — raw text → structured claims/entities
RUNNABILITY: unknown
DEPENDENCIES: unknown
DUPLICATES/DESCENDANTS: `/mnt/data-drive/mrlore-audit/` (separate, dated audit reports,
  distinct from `EngAIn/tier1/mrlore/`)
WORKING EVIDENCE: real manuscript chapters present (`book_01_book_of_genesis_*.md`
  through `book_07_light_resonance_and_the_function_*.md`); real `.zonj.json` per-chapter
  output in `.engain_cache/parsed/scenes/`
CURRENT TRIXEL3.2D EQUIVALENT: ABSENT
STATUS: LEGACY_ONLY
```

**Narrative capability verdict:** this system is genuinely the largest and most
mature of the five — real manuscript in, real structured scene JSON out, with staged,
inspectable intermediate artifacts at every pass. None of it exists in `trixel3.2d`,
which starts from hand-built footprints, never from text.

---

## 2. WORLD REPRESENTATION / GENERATION

**What the evidence shows it could do:** hold a chunked 2D float terrain field
(WorldField), convert float values to named terrain types via declared thresholds,
and push those deltas into a semantic terrain grid (TrixelWorld) that a planner then
turns into a placeable `terrain_grid` for rendering.

```
FILE: /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/tier2/worldfield/world_field_nucleus.py
ROLE: "WorldField - Phase 0 Nucleus." Chunked 2D float field, `Chunk` class
  (32x32 default, `data`/`dirty` flags), `WorldField` class with `get_chunk_key`,
  `get_local_coords`, `get_or_create_chunk`. Docstring: "4 core ops... Python
  authority with Godot bridge."
INPUT: (x, y) world coordinates + float values (add/subtract/smooth/clamp, per its
  own docstring — not fully read)
OUTPUT: dirty chunk deltas for `GodotWorldFieldBridge` to expose
CALLS: none (pure data structure)
CALLED BY: `trixel_world_adapter.py` (see below)
PIPELINE POSITION: raw substrate of World Representation — the float layer beneath
  the semantic terrain grid
RUNNABILITY: unknown, not executed
DEPENDENCIES: stdlib only in the portion read
DUPLICATES/DESCENDANTS: none found
WORKING EVIDENCE: none directly observed running; referenced by name and described
  in detail in `TRIXEL_AUTHORITY_MAP.md` (see §3 authority quote below)
CURRENT TRIXEL3.2D EQUIVALENT: PARTIAL — `trixel/global_sample/field_v1.py` +
  `patch_v1.py` implement a smooth heightfield sampler, conceptually similar (a
  continuous field an address samples into), but it is NOT chunked, has no
  add/subtract/smooth/clamp op vocabulary, and is not wired to any threshold→terrain
  classifier
STATUS: PARTIALLY_REBUILT (different implementation, same rough role)
```

```
FILE: /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/tier2/worldfield/terrain_thresholds.py
ROLE: `value_to_terrain()` — maps a float in [0,1] to a terrain type name by declared
  threshold bands (per `TRIXEL_AUTHORITY_MAP.md`'s quoted values: 0.00-0.10 deep_water,
  0.10-0.22 shallow_water, 0.22-0.30 shoreline, 0.30-0.42 sand, 0.42-0.62 grass, plus
  other declared profiles for wasteland/volcanic/cosmic).
INPUT: float value + (implied) active terrain profile
OUTPUT: terrain type string, one of `VALID_TERRAIN_TYPES`
CALLS: none
CALLED BY: `trixel_world_adapter.py`
PIPELINE POSITION: the explicit "AP threshold rule" layer between WorldField and
  TrixelWorld
RUNNABILITY: unknown, not executed
DEPENDENCIES: stdlib only (imported via try/except fallback in trixel_world_adapter.py,
  suggesting it's sometimes imported as a package-relative module and sometimes flat —
  a packaging inconsistency, not necessarily a break)
DUPLICATES/DESCENDANTS: none found
WORKING EVIDENCE: the exact terrain vocabulary this module would produce
  (deep_water/shallow_water/shoreline/sand/grass/rock/forest_edge/pier) is the SAME
  vocabulary hardcoded into `SemanticRenderer.gd`'s `terrain_grid` default and
  `_terrain_height()` match statement — strong circumstantial evidence this threshold
  table (or one very like it) really did drive what the Godot runtime rendered
CURRENT TRIXEL3.2D EQUIVALENT: ABSENT — no float→terrain-name threshold system exists
  in trixel3.2d; the closest concept is `trixel/trixel32d_worldfield_to_worldcell_projection.py`,
  but that maps *coordinates*, not float values, to terrain identity, and has zero
  terrain-type vocabulary at all
STATUS: LEGACY_ONLY
```

```
FILE: /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/tier2/worldfield/trixel_world_adapter.py
ROLE: "Connects WorldField (float terrain state) to TrixelWorld (semantic terrain
  grid)." Explicit docstring: receives dirty chunk data, converts floats→terrain
  strings via terrain_thresholds, pushes changes into TrixelWorld's semantic grid,
  emits `TerrainDelta` events downstream. Self-described as "the AP rule layer... does
  NOT own state — WorldField owns floats, TrixelWorld owns semantics."
INPUT: dirty WorldField chunks
OUTPUT: `TerrainDelta(world_x, world_y, old_terrain, new_terrain)` events
CALLS: `terrain_thresholds.value_to_terrain`
CALLED BY: intended to be called by "GodotWorldFieldBridge" per its own docstring;
  ALSO directly invoked as a CLI subprocess by `TrixelEnvironmentPlanner.gd` (see below)
PIPELINE POSITION: exactly the bridge point the user's pipeline sketch names —
  "WorldField → trixel_world_adapter.py ... → TrixelWorld"
RUNNABILITY: **broken as wired from Godot.** `TrixelEnvironmentPlanner.gd` line 12
  hardcodes `WORLD_FIELD_SCRIPT := "/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/terrain/trixel_world_adapter.py"`.
  Verified: `EngAIn/terrain/` **does not exist** on disk. The real file lives at
  `EngAIn/tier2/worldfield/trixel_world_adapter.py` (a second copy exists at
  `conductor/conductor_building_blocks/terrain/trixel_world_adapter.py`, which DOES
  match the hardcoded directory name `terrain/` but is missing the `EngAIn/` prefix
  the script expects — i.e. still not the exact path). `TrixelEnvironmentPlanner.plan()`
  checks `FileAccess.file_exists(WORLD_FIELD_SCRIPT)` before ever invoking it and
  silently falls through to a static fallback grid when it's missing — this is a
  real, confirmed dead code path in the legacy Godot→Python bridge, not speculation.
DEPENDENCIES: `terrain_thresholds.py` (relative import with flat-import fallback)
DUPLICATES/DESCENDANTS: `conductor/conductor_building_blocks/terrain/trixel_world_adapter.py`
  (not diffed against the tier2 copy — unknown if identical)
WORKING EVIDENCE: none of it running successfully was observed; the broken-path
  finding above is itself the working evidence of its *current* state
CURRENT TRIXEL3.2D EQUIVALENT: ABSENT
STATUS: LEGACY_ONLY (and currently unreachable via its only known Godot call site)
```

```
FILE: /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/tier2/worldfield/grid_facts_emitter.py
ROLE: unknown — not read this pass, name suggests it emits factual/derived data
  about the terrain grid (e.g. for downstream contract validation)
STATUS: UNKNOWN
```

**Also relevant — a second, unrelated "spatial authority" system**, described in its
own voice in `TRIXEL_AUTHORITY_MAP.md` (see §4 below): **trixelmap**, which reads ZONJ/
vault/scene JSON and produces `spatial_authority.json`, `resolved_layout.json`,
`terrain_field.json` — a *region-placement* layer, explicitly distinct from and
upstream of both TrixelWorld (semantic grid) and Trixelcomposer (pixel art). No
trixelmap implementation file was located in the trees searched this pass (only its
authority-contract description survives in the docs above) — this is worth a
follow-up search specifically for `trixelmap` / `spatial_authority.json` /
`resolved_layout.json` if the user wants it traced further.

```
FILE: /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/runtime/trixel32d_requests/, trixel32d_reports/, trixel32d_built_drops/, trixel32d_apply_authorizations/
ROLE: a file-drop request/response protocol for terrain surface building — request →
  report → built-drop → apply-authorization, each stage its own directory, individual
  requests filed under `t32ddrop_<hash>` subdirectories, plus versioned payload/drop
  JSON schemas (`TRIXEL32D_SURFACE_REQUEST_PAYLOAD_V1.json`,
  `TRIXEL32D_SURFACE_BUILT_PAYLOAD_V1.json`, `TRIXEL32D_SURFACE_BUILT_DROP_V1.json`,
  `TRIXEL32D_SURFACE_BUILT_INTAKE_V1.receipt.json`).
INPUT: a surface-build request (terrain grid geometry request)
OUTPUT: a built-surface drop + intake receipt
CALLS/CALLED BY: unknown, not traced to a specific producing/consuming script this pass
PIPELINE POSITION: looks like an inter-process handoff between whatever built terrain
  surfaces (Blender? a builder script?) and whatever consumed them — structurally
  parallel to (but NOT the same file-naming convention as) current trixel3.2d's
  `trixel32d_surface_builder.py`/`trixel32d_surface_consumer.py`/`trixel32d_surface_emitter.py`
RUNNABILITY: unknown; the presence of real numbered drop directories with matching
  request/report/drop artifacts is evidence this protocol executed at least twice
  (`t32ddrop_49396807a2d11932`, `t32ddrop_939c10c2a2de957b`, plus two more distinct
  request-only hashes)
DEPENDENCIES: unknown
DUPLICATES/DESCENDANTS: the "V1" naming (`TRIXEL32D_SURFACE_*_V1`) and the general
  request/report shape are similar in spirit to current
  `trixel/trixel32d_surface_builder.py`'s design, but this is a DIFFERENT, EngAIn-side
  runtime handoff mechanism, not the same code
WORKING EVIDENCE: real drop artifacts on disk (see paths above)
CURRENT TRIXEL3.2D EQUIVALENT: PRESENT_BUT_DIFFERENT — `trixel3.2d/trixel/trixel32d_surface_builder.py`
  and siblings implement a similar-sounding "connected terrain surface" builder, but
  as an in-process Python library, not a file-drop request/response protocol; whether
  either descends from the other is UNKNOWN
STATUS: UNKNOWN relationship to current code; legacy artifacts confirmed real
```

**World Representation verdict:** the WorldField→threshold→TrixelWorld chain is real,
documented in its own words (`TRIXEL_AUTHORITY_MAP.md`), and directly evidenced by
vocabulary overlap with the working Godot renderer — but its one known Godot call
site is broken (dead file path), and none of it exists in trixel3.2d, which has no
chunked float field, no threshold vocabulary, and no semantic-grid concept at all.

---

## 3. GEOMETRY REALIZATION

**What the evidence shows it could do (legacy):** turn a semantic terrain grid into
placed 3D tiles in Godot, with role-aware tile selection (edge/corner/center) via
`TrixelRoleResolver`, and a vocabulary-alias layer (`TrixelEnvironmentPlanner`)
translating semantic terrain tokens into concrete tile names. This is Godot-side,
per-tile placement — not a topology/disposition compiler.

```
FILE: /mnt/data-drive/burdens_of_a_forgotten_past/EngAIn/godotnew/semantic/trixel/TrixelEnvironmentPlanner.gd
ROLE: static-class "planner" bridging a runtime scene document (from the narrative
  pipeline) to a placeable `terrain_grid` + `prop_placements` + `landmark_nodes`.
  Loads a vocabulary-alias JSON (`initialize_vocabulary_bindings`,
  `primitive_vocabulary_bindings.json`), can load a "treaty terrain plan" JSON
  directly (`load_treaty_terrain_plan`, schema-validated: requires `scene_id`,
  `terrain_grid`, `render_manifest`), and its `plan()` entrypoint attempts to shell
  out to the Python WorldField adapter (`_fetch_world_field_plan`, via `OS.execute`
  on `python3` with `WORLD_FIELD_SCRIPT`), falling back to a static procedurally
  generated grid (`_generate_base_grid` + `_apply_environment_rules`, hardcoded
  per-biome rules e.g. shoreline→water bands, forest_edge→border ring, sand→rock
  strip) when that fails or is missing.
INPUT: `runtime_scene_doc` Dictionary (terrain_family, environment, region,
  spatial_scale_hint, level_design, terrain_metadata, locations, landmarks)
OUTPUT: `{terrain_grid, prop_placements, landmark_nodes, terrain_family, environment, map_size}`
CALLS: `trixel_world_adapter.py` (broken path, see §2), `resolve_tile_alias()` (own
  static method, used by `SemanticRenderer._load_atlas_for`)
CALLED BY: `SemanticRenderer.gd` (`resolve_tile_alias`); presumably `Boot.gd` or
  `Main.gd` call `plan()` itself (not directly confirmed — `plan()` was never seen
  called in the files read this pass, though its heavy diagnostic logging
  (`[TRIXEL_PLANNER_INPUT]`, `[TRIXEL_PLAN]`) matches console lines visible in the
  shared screenshots almost exactly)
PIPELINE POSITION: World Representation output → Geometry Realization input, the
  exact seam the user's pipeline sketch names
RUNNABILITY: **partially broken** — the WorldField subprocess path is confirmed dead
  (§2); the static procedural fallback path is self-contained Godot script logic with
  no missing dependencies observed, so that half is plausibly runnable
DEPENDENCIES: `primitive_vocabulary_bindings.json` (present, same directory),
  Python3 + `trixel_world_adapter.py` (present but at the wrong path for this script)
DUPLICATES/DESCENDANTS: an identically-named file exists at
  `conductor/conductor_building_blocks/trixel/TrixelEnvironmentPlanner.gd` — not
  diffed against this copy this pass
WORKING EVIDENCE: the screenshot log lines `[TRIXEL_PLAN] source=world...` and
  `[boot] Adapted runtime scene...` match this file's exact print-statement
  vocabulary (`[TRIXEL_PLAN] source=%s` at line ~207, `[TRIXEL_PLANNER_INPUT]` at
  ~151-154) — this is direct, strong evidence this exact file is what ran in the
  screenshotted session, and that at the time of that screenshot it reached at least
  the static-fallback branch (rendering the visible green/tan/gray isometric grid),
  though whether the WorldField subprocess branch ever succeeded historically (before
  the path went stale) is UNKNOWN
CURRENT TRIXEL3.2D EQUIVALENT: ABSENT — trixel3.2d's `pixel_geometry` package has no
  concept of a terrain-grid-to-tile planner, biome-based procedural fallback rules,
  or a vocabulary-alias layer; it operates one level lower, on individual addressed
  footprints, never on a whole placed world grid
STATUS: PARTIALLY_REBUILT is too strong — mark LEGACY_ONLY, with one dependency confirmed broken
```

```
FILE: /mnt/data-drive/burdens_of_a_forgotten_past/EngAIn/godotnew/semantic/trixel/TrixelRoleResolver.gd
ROLE: given a terrain_grid + (x,y) + terrain name, resolves which atlas tile "role"
  (center/edge/corner variant) to use based on neighboring cells — this is the actual
  per-tile geometric/visual placement decision `SemanticRenderer._spawn_terrain_grid()`
  calls per cell.
INPUT: terrain_grid Array, gx, gy, terrain string
OUTPUT: role string (e.g. "center", used as a key into atlas `rects`)
CALLS: none observed
CALLED BY: `SemanticRenderer.gd::_spawn_terrain_grid()` and `::update_tile_from_event()`
PIPELINE POSITION: Geometry Realization — the per-cell role/adjacency-to-tile-variant
  decision, analogous in spirit (not implementation) to current trixel3.2d's
  disposition/adjacency layer, but operating on rendered tile SELECTION, not on
  canonical mesh topology
RUNNABILITY: unknown, not read in full (only referenced via call sites)
DEPENDENCIES: unknown
DUPLICATES/DESCENDANTS: none found
WORKING EVIDENCE: called directly in `SemanticRenderer._spawn_terrain_grid()`, which
  is the function that would have produced the rendered grid visible in the screenshots
CURRENT TRIXEL3.2D EQUIVALENT: ABSENT (no atlas-role/neighbor-aware tile-variant
  resolution exists anywhere in pixel_geometry)
STATUS: LEGACY_ONLY
```

```
FILE: trixel3.2d/trixel/pixel_geometry/  (addressing_v1.py, adjacency_v1.py, embedding_v1.py, compiler_v1.py, artwork_mapping_v1.py, ramp_geometry_v1.py, terrain_ramp_integration_v1.py)
ROLE: THE CURRENT geometry compiler — see the separate architecture-comparison
  document (`docs/TRIXEL_DOCTRINE_ARCHITECTURE_COMPARISON_V1.md`, written earlier
  this session) for full detail. In the context of this wider recovery map, its
  honest position is: a rigorous, individually-proven, single-footprint compiler
  (address → embed → compile → canonical geometry, with adjacency/immutability
  invariants proven by 12 frozen gates) that has NEVER been exercised against a
  whole placed WORLD grid, a semantic terrain classification, or narrative input of
  any kind. It is the newest, most rigorously tested piece of Trixel to exist — and
  also the narrowest in scope of everything catalogued in this document.
INPUT: hand-constructed footprint dicts (width, height, payload), hand-chosen
  embedding parameters
OUTPUT: canonical positions + triangle indices + provenance
CALLS: nothing outside `trixel/pixel_geometry/`
CALLED BY: `trixel/gates/gate_pixel_geometry_*.py` (12 gates), `tools/export_trixel_capability_courtyard.py`
PIPELINE POSITION: this session's entire focus — Geometry Realization only
RUNNABILITY: runnable — verified repeatedly via fresh git clone + full gate rerun
  this session
DEPENDENCIES: none beyond stdlib
DUPLICATES/DESCENDANTS: none — this is new code written this session, not a
  reconstruction of any specific legacy file
WORKING EVIDENCE: 12 green gates, the Capability Courtyard `.blend` (uncommitted,
  pending user review)
CURRENT TRIXEL3.2D EQUIVALENT: n/a — this IS the current implementation
STATUS: REBUILT, but only for the narrow "single footprint, address-to-mesh"
  slice of Geometry Realization. It does NOT reproduce legacy's grid-of-many-tiles,
  role/neighbor-resolved, semantically-driven terrain placement.
```

**Geometry Realization verdict:** legacy geometry realization operated at WORLD-GRID
scale (many tiles, role-resolved by neighbor, chosen by a terrain-family planner).
Current trixel3.2d geometry realization operates at SINGLE-FOOTPRINT scale (one
addressed cell grid, embedded once, compiled once) with much stronger formal
invariant proof per footprint. Neither subsumes the other; they solve different
grain sizes of the same general problem, and nothing currently bridges them.

---

## 4. VISUAL / ART REALIZATION

**What the evidence shows it could do:** this is the richest, most surprising finding
of this pass. The legacy stack had a full brush/material engine — GIMP brush-format
parsers, a "pure stamp" rendering engine, a normalized brush/palette asset model, a
named-recipe vocabulary (`hard_pixel`, `hatch_texture`, `charcoal_grain`,
`bristle_rake`, `oil_smear`, `acrylic_variant`, `terrain_stroke`), a materials-behavior
vocabulary layer (edge/fill/variation/age/color/blend), even a tree/flora rendering
system — organized as explicitly separated "voices" with hard authority boundaries,
documented in the file below.

```
FILE: /home/mytruelove/Desktop/burdens_of_a_forgotten_past/trixel_legacy_2d/from_engain/docs_contracts/TRIXEL_TIER1_AUTHORITY/TRIXEL_AUTHORITY_MAP.md
ROLE: a first-person "performance contract" narrative document naming and bounding
  every major Trixel-family component's authority, written by (or in the voice of) an
  AI collaborator during the original build. Names and describes (without necessarily
  including the files themselves in this exact tree):
    trixelmap           — spatial authority extraction/placement (ZONJ/vault/scene → region graph → resolved_layout.json/terrain_field.json), explicitly NOT a painter or renderer
    demand_resolver.py  — resolves "semantic visual demand" into deterministic visual references, explicitly non-authoritative over world truth
    composer_abi_adapter.py — normalizes legacy composer/editor systems into ABI envelopes, stamped non-authoritative/non-deterministic unless seeded
    atlas_composer.py   — composes replacement atlas.png files under a FIXED UV topology owned by atlas_meta.json (this is the direct legacy ancestor of the atlas_meta.json/atlas.png convention still visible in TrixelAtlas.gd/SemanticRenderer.gd today)
    engine_mr.py         — "pure stamp engine": snapshot-in/snapshot-out, renders BrushRecipe strokes into a SurfaceBuffer, no I/O
    GIMP parser family    — .vbr/.gbr/.gih/.gdyn/.gpl/.gfig/.ggr format parsers, each a separate "voice"
    brush_models_mr.py   — frozen normalized dataclasses: BrushShapeAsset, BrushDynamicsAsset, PaletteAsset, VariantBrushBundle, BrushRecipe
    trixel_brush_adapter.py — the ONLY allowed boundary between GIMP parser output and normalized Trixel brush models ("nothing downstream should ever import a parser")
    surface_behavior_mr.py — abstract material-behavior vocabulary: edge, fill, variation, age/motion, color discipline, blend intent — renders nothing itself
    trixel_recipes_mr.py — named visual-outcome recipes: hard_pixel, hatch_texture, charcoal_grain, bristle_rake, oil_smear, acrylic_variant, terrain_stroke
    world_tree_mr.py     — tree/flora visual system: Gfig-backed scaffolds, species definitions, influence fields, tree rendering passes (i.e. legacy DID have a working
      or at least designed taper/branch-capable flora renderer — directly relevant to
      the "taper is out of scope" boundary current trixel3.2d has drawn for itself)
    scene_models_mr.py   — abstract environment descriptors (bands, paths, atmosphere nodes)
    stress_scene_mr.py   — maximum-diversity system probe (explicitly not meant to be pretty — a stress/coverage test, analogous in spirit to trixel3.2d's toxic-proof gates)
INPUT: (per the document itself) uploaded Trixel files, existing contracts, user's
  lane/authority rules
OUTPUT: this markdown document itself — a boundary/authority description, not code
CALLS/CALLED BY: n/a (documentation artifact); the files it describes were not
  independently located in the trees searched this pass — this document may be the
  ONLY surviving trace of some of them
PIPELINE POSITION: describes the entire Visual/Art Realization system's internal
  boundaries
RUNNABILITY: n/a (this file is documentation, not executable)
DEPENDENCIES: n/a
DUPLICATES/DESCENDANTS: sibling contract files in the same directory:
  `TRIXELMAP_CONTRACT_WITH_METTAEXT.md`, `TRIXELMAP_CONTRACT_WITH_ENGIONALITY.md`,
  `TRIXELMAP_CONTRACT_WITH_GODOTSIM.md`, `TRIXELMAP_CONTRACT_WITH_MRLORE.md`,
  `TRIXELMAP_AUTHORITY_HANDSHAKE.md`, `TRIXEL_ADAPTER_CONTRACT_v1.md`,
  `TRIXEL_ASSET_TRUE_FALSE_CONTRACT.md` — not individually read this pass
WORKING EVIDENCE: the document quotes real behavior it claims to have observed
  ("the terminal loop worked mechanically, but the plan step was degenerate...
  phase transitions were stuck and random scattered coordinates did not become
  composition") — i.e. it is itself reporting a partially-working, partially-failed
  system, not claiming full success. This is the single most important caveat in this
  whole recovery map: the document's own verdict is
  `CURRENT_ARTISTIC_AUTONOMY = MECHANICALLY_PRESENT_BUT_COMPOSITIONALLY_UNPROVEN`.
CURRENT TRIXEL3.2D EQUIVALENT: see `trixel_recipe_renderer.py` below — vastly simpler,
  no brush/GIMP-format lineage, no palette/material asset model, no tree system
STATUS: LEGACY_ONLY, and self-reported as never fully proven even in its own time
```

```
FILE: /home/mytruelove/Desktop/burdens_of_a_forgotten_past/trixel_legacy_2d/from_engain/mechanimation/trixel_composer/trixelcomposer-main/  (enhanced_trixel_core.py, empire_bridge.py, terminal_trixel.py)
ROLE: the actual "Trixelcomposer" code referenced throughout the authority map above
  — a terminal + "enhanced" (GUI, per the map) + "Empire Bridge" trio sharing a
  perceive/plan/act/assess/learn/feedback/persist creative loop over a 16x16 canvas,
  with `.zw` persistence.
INPUT: brush/palette assets, creative-loop state
OUTPUT: composed pixel art (PNG), `.zw`/JSONL memory logs
CALLS/CALLED BY: unknown, not traced import-by-import this pass
PIPELINE POSITION: Visual/Art Realization core
RUNNABILITY: per `TRIXEL_AUTHORITY_MAP.md`'s own report: mechanically ran (PNG export
  worked, JSONL memory worked, CLI loop ran cleanly) but composition quality failed
  (phase transitions stuck, output was "random scattered coordinates," not real
  composition) — i.e. **runnable but not creatively functional**, a directly reported
  finding, not an inference
DEPENDENCIES: unknown
DUPLICATES/DESCENDANTS: `brush_tutorial_zw.txt`, `trixel composer research.txt`,
  `trixel_creative_cycle.txt` in the same directory — design notes, not code
WORKING EVIDENCE: `TRIXEL_AUTHORITY_MAP.md`'s direct quote above
CURRENT TRIXEL3.2D EQUIVALENT: ABSENT
STATUS: LEGACY_ONLY (self-reported partial failure, not merely unfinished)
```

```
FILE: /mnt/data-drive/burdens_of_a_forgotten_past/EngAIn/godotnew/semantic/trixel/TrixelAtlas.gd, TrixelAtlas.tscn, trixelassets/{cliff,deep_water,forest_edge,grass,pier,rock,sand,shallow_water,shoreline}/
ROLE: a working static-atlas tile system — one directory per terrain type, each
  presumably holding `atlas.png` + `atlas_meta.json` (per `SemanticRenderer._read_atlas_meta`'s
  expected path `res://trixel/trixelassets/<terrain>/atlas_meta.json`). This is the
  MODE_ATLAS_2D fallback every other render mode in RenderPolicy degrades to.
INPUT: none (static assets)
OUTPUT: atlas.png + region-rect metadata per terrain
CALLS/CALLED BY: `SemanticRenderer._atlas_static()`, `_read_atlas_meta()`, `_build_rects()`
PIPELINE POSITION: the guaranteed-available fallback layer of Visual/Art Realization
RUNNABILITY: **runnable — this is the one visual asset path with the strongest
  direct evidence of actually working**, since it requires no subprocess, no HTTP
  call, no generation step; just static files. The rendered terrain grid visible in
  the screenshots is most likely showing MODE_ATLAS_2D or MODE_COMPOSER_2_3D output
  (a static atlas as the first frame either way).
DEPENDENCIES: none beyond the asset files themselves
DUPLICATES/DESCENDANTS: none found
WORKING EVIDENCE: the screenshots directly show a colored, tiled isometric terrain
  grid (green/tan/gray cells) consistent with atlas-based tile rendering
CURRENT TRIXEL3.2D EQUIVALENT: ABSENT as a Godot-consumable asset; trixel3.2d's own
  `fixtures/pixel_geometry/*.png` + `.mtl`/`map_Kd` textures serve a related but
  differently-plumbed purpose (OBJ/Blender texturing, not a Godot atlas+UV-rect system)
STATUS: LEGACY_ONLY, but this specific piece is the most likely component to still
  work today if the Godot project were opened, since it has no broken external
  dependencies
```

```
FILE: trixel3.2d/trixel/trixel_recipe_renderer.py + trixel3.2d/recipes/terrain/*.json + recipes/transitions/*.json
ROLE: current trixel3.2d's ENTIRE material/art system: a `Canvas`/`RecipeRenderer`
  pair that paints procedural PNG textures from declarative JSON recipes (noise,
  color rules, transition blending).
INPUT: recipe JSON (e.g. `forest.dense_canopy.json`, `grass_to_dirt.json`, `cliff_edge.json`)
OUTPUT: PNG texture
CALLS: PIL/Pillow only
CALLED BY: `trixel/gates/gate_tundra_recipe_render_contract.py`,
  `gate_all_recipes_validation_contract.py`, and this session's courtyard tooling
  (which samples flat colors from its renders rather than calling it programmatically
  — see `docs/TRIXEL_DOCTRINE_ARCHITECTURE_COMPARISON_V1.md` §2)
PIPELINE POSITION: Visual/Art Realization — but a single, flat, non-hierarchical
  layer: no brush format lineage, no palette/material asset model, no numbered
  material catalog, no tree/flora renderer, no ABI adapter separating legacy formats
  from normalized models. It IS a working, provable, gate-tested renderer — just a
  much smaller one than legacy's.
RUNNABILITY: runnable, gate-verified this and prior sessions
CURRENT TRIXEL3.2D EQUIVALENT: n/a — this IS the current implementation
STATUS: REBUILT, but for a small fraction of what legacy's art stack covered —
  no brush/palette/material asset model, no numbered material catalog, no tree system,
  no ABI-adapter discipline separating format-specific parsers from normalized truth
```

**Art system verdict — the numbered material sheet specifically:**

```
FILE: /mnt/data-drive/burdens_of_a_forgotten_past/EngAIn/trixelworld/test results/test8/building_material_sheet.png
  (also: building_material_sheet_v2.png, same directory)
ROLE: a rendered/exported reference sheet of numbered building materials — screenshots
  show rows 04 PLASTER/STUCCO, 05 TIMBER BEAM, 06 PLANK WALL, 07 ROOF SHINGLE,
  08 WEATHERED WOOD, 09 SANDSTONE RUIN, 10 METAL TRIM, 11 GLASS WINDOW, 12 GROUND PATH.
  Its path (`.../trixelworld/test results/test8/...`) indicates this was itself a TEST
  OUTPUT of some generation/rendering pass, not hand-painted source art — i.e. it is
  evidence a material-generation system produced numbered, categorized building
  materials at least once, but the generator that made it was not identified in this
  pass (candidates: the Trixelcomposer stack above, or a separate, unlocated
  "trixelworld" material generator — `trixelworld` appears as its own top-level
  directory name in three of the copies found, distinct from `trixel_composer`,
  suggesting a THIRD, separate system this pass did not trace).
INPUT: unknown (generator not located)
OUTPUT: this PNG sheet
CALLS/CALLED BY: unknown — the generating script was not found in the time available
  this pass; a follow-up search specifically for files under any `trixelworld/`
  directory (there are at least 3 copies: `conductor/conductor_building_blocks/trixelworld/`,
  `/mnt/data-drive/New Folder/05_DO_NOT_TOUCH_ORIGINALS/EngAIn_runtime_candidate/trixelworld/`,
  `/mnt/data-drive/burdens_of_a_forgotten_past/EngAIn/trixelworld/`) would be needed
  to identify it
PIPELINE POSITION: Visual/Art Realization output artifact
RUNNABILITY: UNKNOWN — only the output artifact was located, not the generator
DEPENDENCIES: unknown
DUPLICATES/DESCENDANTS: `building_material_sheet_v2.png` — a second, presumably later
  revision, in the same directory
WORKING EVIDENCE: the PNG sheet itself (real, numbered, categorized materials with a
  clean pixel-art aesthetic per the screenshots) — this IS direct working evidence
  that SOMETHING in this pipeline could produce categorized, numbered building
  material art
CURRENT TRIXEL3.2D EQUIVALENT: ABSENT — no numbered material catalog concept exists
  anywhere in trixel3.2d; `recipes/*.json` are named by descriptive slug
  (`forest.dense_canopy`), not by number, and cover terrain/transitions only, never
  building materials (plaster, timber, shingle, glass, metal trim)
STATUS: LEGACY_ONLY, generator UNKNOWN (follow-up search recommended, not performed here)
```

**Visual/Art Realization verdict:** this is the largest capability GAP between old
and new Trixel. Legacy had (by its own documentation) a layered brush-engine
architecture with real format-parser lineage (actual GIMP brush files), a
normalized asset model, a named-recipe vocabulary, and evidence of numbered
building-material generation — even though the composer's own creative-loop output
was self-reported as not yet compositionally proven. Current trixel3.2d has a single
flat procedural-recipe renderer covering only natural terrain, with no material
catalog, no brush lineage, and no building-material vocabulary at all.

---

## 5. RUNTIME / CONSUMER

**What the evidence shows it could do:** run a real Godot 4 project that loads a
scene-chooser UI from a manifest, POSTs a selected scene JSON to a local HTTP
runtime server, polls for a snapshot, renders a textured terrain grid via
SemanticRenderer, and spawns bridge entities (characters) at server-provided
positions — this is the part with the strongest, most direct working evidence of
this entire recovery pass (the shared screenshots).

```
FILE: /mnt/data-drive/burdens_of_a_forgotten_past/EngAIn/godotnew/semantic/Main.gd
ROLE: top-level runtime orchestrator (440 lines read in full). Builds a scene-chooser
  UI from `engain_manifest.json` + `scene_index.json`, on selection normalizes the
  scene payload, drives a `SceneTransitionBouncer` state machine
  (SCENE_REQUESTED→SERVER_COMMITTED→TERRAIN_LAYOUT_READY→SNAPSHOT_SYNCED→scene_ready),
  fetches a runtime snapshot from the HTTP server, hydrates `bridge_entities` into
  the scene as capsule actors (or mapped scenes per an asset manifest), and enforces
  a `world_rules.json`-driven spawnability allowlist. Also contains a hardcoded
  debug/demo `spawn_dragon()` easter-egg triggered once terrain is ready.
INPUT: `engain_manifest.json`, `scene_index.json`, per-scene JSON files, HTTP
  responses from `127.0.0.1:8080`
OUTPUT: live Godot scene tree (terrain + actors)
CALLS: `SimClient` (autoload), `SceneClient` (autoload), `Boot` (node group lookup),
  `SceneTransitionBouncer`, `semantic_renderer` (`$World/SemanticRenderer`)
CALLED BY: n/a — top-level scene script
PIPELINE POSITION: Runtime/Consumer orchestration, the outermost layer of the whole
  pipeline
RUNNABILITY: **strong direct evidence of having run** — its exact print-statement
  vocabulary (`[Main] Loaded`, `[Main] World ok: true`, `[Main] Camera ok: true`,
  `[Main] SemanticRenderer ok: true`, `[Main] Actors ok: true`, `[Main] UI ok: true`,
  `[CHOOSER] clicked file=...`, `[boot] Scene payload received...`,
  `[boot] Adapted runtime scene...`) matches the shared screenshot's console output
  line-for-line. One screenshot also shows `ERROR: sim_runtime fail [...] at:
  _on_sim_fail (res://... SimClient.gd:57)` and `Snapshot fetch failed, code: 0` —
  i.e. the run captured in the screenshots had the HTTP backend either not running
  or unreachable at that moment, while the terrain grid still rendered (proving the
  static/local-fallback path works independent of the HTTP server)
DEPENDENCIES: `engain_manifest.json` (path: `/home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/manifests/engain_manifest.json` — hardcoded absolute path,
  same fragility pattern as `TrixelEnvironmentPlanner.gd`'s WORLD_FIELD_SCRIPT
  constant; not verified to exist in this pass), `world_rules.json` (hardcoded path
  `EngAIn/manifests/world_rules.json`, also not verified to exist)
DUPLICATES/DESCENDANTS: `Main.gd.bak_world_rules` — an earlier revision kept in place
WORKING EVIDENCE: the screenshots, directly
CURRENT TRIXEL3.2D EQUIVALENT: ABSENT — trixel3.2d has no runtime consumer at all; its
  Blender-based courtyard tooling is a static-scene BUILD tool, not a live,
  server-backed, scene-selectable runtime
STATUS: LEGACY_ONLY, with direct screenshot evidence of a real (if partially
  degraded — HTTP snapshot failing) run
```

```
FILE: /mnt/data-drive/burdens_of_a_forgotten_past/EngAIn/godotnew/semantic/autoload/SimClient.gd
ROLE: HTTP client autoload — POSTs scene-load requests and GETs snapshots against
  `sim_base = "http://127.0.0.1:8080"`, single-request-in-flight guarded
  (`_in_flight`), stamps every outbound scene doc with governance fields
  (`reality_mode: "LIVE"`, `actor_authority_tier: 3`, `issuer`/`source:
  "godot_semantic_runtime"`).
INPUT: scene doc Dictionary, command text
OUTPUT: HTTP requests to the runtime server; `sim_response`/`sim_failed` signals
CALLS: Godot `HTTPRequest`
CALLED BY: `Main.gd` (`SimClient.load_scene_doc`)
PIPELINE POSITION: Runtime/Consumer transport layer
RUNNABILITY: the CLIENT side is straightforward Godot HTTPRequest usage, plausibly
  runnable; whether the SERVER side (below) is currently runnable is a separate
  question this pass did not verify by execution
DEPENDENCIES: a running HTTP server at 127.0.0.1:8080
WORKING EVIDENCE: the screenshot's `SimClient.gd:57` error trace confirms this exact
  file, at this exact line, executed and failed during the captured session (server
  unreachable at that moment)
CURRENT TRIXEL3.2D EQUIVALENT: ABSENT
STATUS: LEGACY_ONLY
```

```
FILE: /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn/tier2/godotsim/http_handlers.py
ROLE: the Python HTTP server SimClient talks to. Confirmed route handlers via grep:
  `do_GET`/`/snapshot` (returns `self.runtime.get_snapshot()`), `do_POST`/`/scene/load`
  (`_handle_scene_load`), `/embodiment/pending`, `/embodiment/apply` (embodiment
  contract application — the same "Trixel Embodiment Contract" concept
  `SemanticRenderer.apply_embodiment_contract()` consumes), `/command`, vault-link/
  vault-search handlers. Extensive `[TRACE_SCENE030]` debug logging throughout,
  suggesting this exact server was being actively debugged against scene 030
  ("ummade_army") — the same scene file present in `pass_to_render/scenes/`.
INPUT: HTTP requests from Godot's SimClient
OUTPUT: JSON responses; drives `self.runtime` (an `EngAInRuntime` object, per its own
  top-of-file comment) which owns snapshot/subsystem state
CALLS: `self.runtime.get_snapshot()`, scene-manager methods (`scene_manager.py`,
  same directory), embodiment contract application
CALLED BY: Godot's `SimClient.gd` over HTTP
PIPELINE POSITION: Runtime/Consumer server-side authority — the actual "runtime
  truth" TRIXEL_AUTHORITY_MAP.md's various component voices repeatedly defer to
RUNNABILITY: unknown — not executed this pass; the extensive matching trace-log
  vocabulary between this file and the screenshots' console output is strong
  circumstantial evidence it was running (or at least intended to be running)
  concurrently with the Godot session captured
DEPENDENCIES: `EngAInRuntime` class (not located this pass — likely `runtime_core.py`
  or `runtime_gateway.py` in the same `tier2/godotsim/` directory, not opened)
DUPLICATES/DESCENDANTS: none found
WORKING EVIDENCE: matching `[TRACE_SCENE030]` log-line vocabulary with Main.gd/SimClient.gd
CURRENT TRIXEL3.2D EQUIVALENT: ABSENT
STATUS: LEGACY_ONLY
```

> **CORRECTIVE NOTE (added by a later, narrower follow-up pass — see
> `docs/TRIXEL_VISUAL_GENERATOR_LINEAGE_TRACE_V1.md`):** the file above,
> `tier2/godotsim/http_handlers.py`, must **not** be read as defining EngAIn's
> original/day-1 server identity. It is a proof-harness-grade HTTP server that this
> exact Godot specimen happens to talk to, not necessarily the canonical runtime
> spine. The real EngAIn runtime spine, per the user's own direct correction, is
> four files split by responsibility from the start: `launchengine.py` (startup/
> orchestration), `simruntime.py` (live simulation runtime), `engainos/server.py`
> (EngAInOS service host), and `engainos/http_handlers.py` (HTTP boundary for that
> spine — note the different path/module than the file catalogued above). The
> identity rule: the full EngAIn runtime = launched through `launchengine.py` +
> `simruntime.py` active + EngAInOS server active + EngAInOS HTTP handlers serving
> the runtime seam. Everything else — Trixel services (SimClient/tile_server/
> ArtworkClient), Godot, semantic extraction, later Dragon/Hermes layers, and
> `start_stack.fish`-orchestrated processes — plugs into or around that spine, and
> may be a legitimate proof harness, but is not itself "the full EngAIn runtime."
> **The four spine files have not yet been traced** — that is the explicit subject
> of a pending future follow-up, not done here. This note only corrects the
> mislabeling; it does not supply the spine trace.

**Runtime/Consumer verdict:** this is the layer with the best direct, session-specific
evidence of having actually executed (the screenshots are literally console output
from this exact code). It is also entirely absent from trixel3.2d, which has no
server, no live scene-selection runtime, and no entity-hydration concept — only
offline Python compilation and a static Blender scene build.

---

## Special entry: Novel text → generated continent/world

**OLD WORKING EVIDENCE:** the six shared screenshots, specifically: the Godot editor
titled "semantic — Terrain Resolution Refactor — FireDragon" running the project at
this pipeline's `godotnew/semantic` location; console output reading `[Main] Loaded`
/ `[Main] World ok: true` / `[Main] SemanticRenderer ok: true` /
`[boot] Adapted runtime scene...` / `[BOOT_PAYLOAD_terrain]` /
`[BOOT_LEVEL_DESIGN] entry...` / `[TRIXEL_PLAN] source=world...`; and a rendered,
textured isometric terrain grid (green/tan/gray tiles on a blue water border) shown
in two separate screenshots, one a debug console overlay and one the clean rendered
view.

**SURVIVING IMPLEMENTATION — the traceable chain, stage by stage:**

1. Manuscript chapters (`EngAIn/tier1/mrlore/raw/chapters/book_0N_*.md`) — **present, real files**.
2. MrLore claim/entity/continuity extraction (`EngAIn/tier1/mrlore/*.py`) — **present**, runnability unverified.
3. Passroom 5-stage compiler (`EngAIn/tier3/mettaext/passroom/pass1..pass5_*.py`) — **present**, with real staged per-scene output on disk (`.zon`/`.zonj.json` files, segmented scene text) proving at least partial historical execution.
4. `pass5_game_bridge.py` → game-ready scene JSON — **present**, and its OUTPUT is directly present too: `EngAIn/godotnew/semantic/pass_to_render/scenes/scene.030_ummade_army.min.json` plus a matching snapshot JSON — this is a real, on-disk, end-of-pipeline artifact.
5. `Main.gd`'s scene chooser loads that scene JSON, POSTs it via `SimClient` to a local HTTP server (`EngAIn/tier2/godotsim/http_handlers.py`, `/scene/load`).
6. The server's runtime resolves a snapshot (`/snapshot`), which `Main.gd` polls and uses to hydrate `bridge_entities`.
7. `TrixelEnvironmentPlanner.plan()` attempts to call the WorldField/TrixelWorld chain (`trixel_world_adapter.py`) for terrain — **this specific hop is confirmed BROKEN** (stale hardcoded path, verified missing directory) — and falls back to a static procedural grid instead when that happens.
8. `SemanticRenderer.gd` renders the resulting `terrain_grid` using `TrixelRoleResolver` (tile role selection) and `RenderPolicy`/`TrixelAtlas` (texture source selection), producing the visible tiled terrain.

**Every stage above has a real, located file.** The one CONFIRMED break is step 7
(WorldField bridge path). Whether steps 1-6 actually executed together, in sequence,
producing THIS specific screenshotted scene, versus steps 1-4 having run at some
earlier point and steps 5-8 being driven by the already-generated JSON artifact on a
later, separate occasion, is **UNKNOWN** — the artifacts don't carry timestamps this
pass checked, and the screenshot itself shows a snapshot-fetch failure (server
unreachable at that moment), meaning entity hydration from the live server did NOT
succeed in the captured moment even though terrain rendering did.

**CURRENT TRIXEL3.2D EQUIVALENT:** ABSENT for essentially the entire chain. Nothing
in trixel3.2d reads manuscript text, extracts entities/claims, classifies
environment, generates a terrain grid from semantic classification, or runs a live
scene-selectable Godot runtime. The only overlapping concept is that both old and new
systems eventually produce "a grid of typed cells with geometry" — but current
trixel3.2d's grids are hand-authored footprints with hand-chosen embeddings, never
derived from narrative or a semantic world model.

**STATUS: ABSENT.** Not REBUILT, not PARTIALLY_REBUILT. Current trixel3.2d cannot
reproduce this capability at any stage from text input. This must not be
overstated in the other direction either: legacy's OWN evidence (the snapshot-fetch
failure visible in the screenshot, the self-reported "compositionally unproven"
verdict on the art side) shows this capability was itself fragile and only
partially reliable even at its historical peak — this is not "a perfect system we
lost," it is "a real, partially-working system we have fragments of."

---

## Special entry: Material sheet / palette-brush-surface system

**OLD WORKING EVIDENCE:** `building_material_sheet.png` / `_v2.png` (numbered rows
04-12: plaster/stucco, timber beam, plank wall, roof shingle, weathered wood,
sandstone ruin, metal trim, glass window, ground path — confirmed via the shared
Aseprite screenshots showing exact row labels and rendered swatches), plus the
`TRIXEL_AUTHORITY_MAP.md` documentation of a full brush-engine architecture (GIMP
format parsers, normalized brush/palette models, named recipe vocabulary, material
behavior vocabulary, tree/flora renderer).

**SURVIVING IMPLEMENTATION:** the DOCUMENTATION of the brush engine survives in
detail (`TRIXEL_AUTHORITY_MAP.md`); the actual composer CODE partially survives
(`trixel_legacy_2d/from_engain/mechanimation/trixel_composer/trixelcomposer-main/`:
`enhanced_trixel_core.py`, `empire_bridge.py`, `terminal_trixel.py`) but per the
authority map's own report, its creative/composition output was never proven
reliable. The GENERATOR that specifically produced the numbered
`building_material_sheet.png` was **not located** in this pass — it most likely lives
under one of the three `trixelworld/` directories found (`conductor/conductor_building_blocks/trixelworld/`, two recovery copies), none of which were opened this pass. A
follow-up targeted search of `trixelworld/` specifically (not just its `test
results/` output folder) is needed to find it.

**CURRENT TRIXEL3.2D EQUIVALENT:** `trixel/trixel_recipe_renderer.py` +
`recipes/terrain/*.json` + `recipes/transitions/*.json`. Overlap assessment:
- Both are procedural, declarative, JSON-driven texture generators — **structurally similar at the top level**.
- Legacy's recipe vocabulary is BUILDING-MATERIAL-oriented and numbered/catalog-based (plaster, timber, shingle, sandstone, glass, metal — architectural surfaces); current trixel3.2d's recipes are TERRAIN-oriented and name-slugged (`forest.dense_canopy`, `grass_to_dirt`, `cliff_edge`, `mountain.rocky_ridge`) — **near-zero vocabulary overlap**; current has no building-material recipes at all.
- Legacy had a real brush/palette ASSET MODEL underneath its recipes (BrushShapeAsset, PaletteAsset, BrushRecipe, sourced from real GIMP brush files) — current trixel3.2d's renderer has no asset model at all; it's pure procedural pixel math (`Canvas.set_pixel`, noise, color rules) with no imported brush data anywhere.
- Legacy had an explicit ABI-adapter discipline isolating legacy/GIMP-specific parsing from normalized downstream models — current trixel3.2d has no such layering; its renderer is a single flat script.
- Legacy had a tree/flora renderer (`world_tree_mr.py`) — current trixel3.2d explicitly and self-consciously excludes anything taper/branch-related (see `trixel/pixel_geometry/contracts_v1.py` lines 15-20 and `docs/TRIXEL_CAPABILITY_COURTYARD_V1.md` §1, both already cited in the architecture-comparison document).

**STATUS: PARTIALLY_REBUILT at the loosest possible reading** (both are procedural
JSON-recipe PNG renderers), but this significantly overstates the overlap — the
actual VOCABULARY (building materials vs. terrain), the ASSET MODEL (real
brush/palette data vs. none), and the SCOPE (numbered material catalog + tree
system vs. terrain-only) do not overlap in any concrete way. A more honest label is
**LEGACY_ONLY for the building-material capability specifically**, with current
trixel3.2d providing only a distant structural cousin for terrain textures.

---

## A. What could old Trixel actually do, which surviving system did each thing, and how much exists in trixel3.2d today

| Capability | Old system(s) | Working evidence | In trixel3.2d today |
|---|---|---|---|
| Extract claims/entities/continuity from manuscript prose | MrLore (`tier1/mrlore/`) | real chapter files + `.zonj.json` output | **ABSENT** |
| Classify scene text into environment/terrain profile | `semantic_environment_extractor.py`, `pass5_game_bridge.py`'s keyword registry | consistent field vocabulary in generated scene JSON | **ABSENT** |
| Compile narrative into a game-ready scene document | passroom pass1-pass5 chain | real staged `.zon`/`.zonj.json`/scene-packet files per chapter | **ABSENT** |
| Hold a chunked float terrain substrate | `world_field_nucleus.py` (WorldField) | described in detail in `TRIXEL_AUTHORITY_MAP.md`; not directly observed running | **PARTIAL** (`global_sample/field_v1.py` is a different, non-chunked design) |
| Convert float terrain to named terrain type | `terrain_thresholds.py` | vocabulary matches Godot renderer's hardcoded terrain names | **ABSENT** |
| Bridge float field to semantic terrain grid | `trixel_world_adapter.py` | — | **ABSENT**, and legacy's own only known call site to it is **broken** (stale path) |
| Plan a placeable terrain grid from world/narrative intent | `TrixelEnvironmentPlanner.gd` | screenshot log lines match this file's print statements exactly | **ABSENT** |
| Resolve per-cell tile role from neighbors | `TrixelRoleResolver.gd` | called directly by the renderer that produced the screenshotted grid | **ABSENT** |
| Compile an addressed footprint into invariant-proven canonical mesh geometry | trixel3.2d `pixel_geometry/` (new) | 12 green gates, fresh-clone verified | **REBUILT** — this is the ONE capability trixel3.2d does that legacy's surviving files don't clearly show being done with comparable rigor |
| Render textured terrain tiles from a static/generated atlas | `TrixelAtlas.gd` + `trixelassets/*` + `SemanticRenderer.gd` | direct screenshot evidence of a rendered, textured grid | **ABSENT** as a live Godot system; trixel3.2d has a separate, offline OBJ/Blender texturing path instead |
| Generate procedural material/terrain textures from declarative recipes | Trixelcomposer stack (brush/palette/GIMP-format lineage) + unlocated `trixelworld` generator | `TRIXEL_AUTHORITY_MAP.md`'s detailed self-report (mechanically present, compositionally unproven); real numbered `building_material_sheet.png` output | **PARTIAL** — `trixel_recipe_renderer.py` covers terrain only, no building materials, no brush/palette asset model, no numbered catalog |
| Render tree/flora with taper | `world_tree_mr.py` (described, not located as code) | described in authority map | **ABSENT**, explicitly and self-consciously out of scope in current trixel3.2d |
| Run a live, scene-selectable, server-backed 3D runtime | `Main.gd` + `SimClient.gd`/`SceneClient.gd`/`VaultClient.gd`/`ArtworkClient.gd` + `http_handlers.py` server | direct screenshot evidence, including a live (if partially failing) session | **ABSENT** — trixel3.2d has no runtime, server, or live scene selection; only offline compilation + a static Blender scene build |
| Apply a generated recipe texture onto real terrain geometry via an authority-gated contract | `SemanticRenderer.apply_embodiment_contract()` + `/embodiment/apply` HTTP endpoint | referenced consistently across Main.gd, SemanticRenderer.gd, http_handlers.py | **ABSENT** — no embodiment-contract concept, no authority-gated materialization step, exists in trixel3.2d; the courtyard tooling manually samples recipe-rendered colors instead of consuming any contract |

**Headline answer:** old Trixel was a five-stage pipeline that could take real
manuscript text and end in a rendered, if fragile, playable-looking 3D scene with
narrative-driven terrain and entities — genuinely more than any one piece of it,
including the current geometry compiler, does today. The current `trixel3.2d`
rebuild has reconstructed exactly one of those five stages (Geometry Realization),
and has done so with a level of formal rigor (frozen invariants, toxic proofs,
fresh-clone verification) that no surviving legacy file demonstrably matches — but
it operates at a different grain (single hand-built footprint vs. whole
narrative-driven world grid) and has no connection to the other four stages at all.
The single largest capability gap is the Visual/Art Realization layer: legacy had a
real (if self-reported as compositionally unproven) brush/palette/material asset
model with building-material and tree/flora vocabulary; current trixel3.2d has one
flat terrain-only procedural recipe renderer with no material catalog and no asset
model underneath it.
