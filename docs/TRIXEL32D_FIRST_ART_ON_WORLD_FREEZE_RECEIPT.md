# TRIXEL32D-FIRST-ART-ON-WORLD — Freeze Receipt

**Commit:** `84682b8`
**Tag:** `TRIXEL32D-FIRST-ART-ON-WORLD` (annotated)
**Date:** 2026-09-22 / 2026-09-23
**Status:** Accepted, frozen

---

## What this milestone is

The first proof that real, editable Trixel pixel art can be bound onto
the *actual* Trixel Capability Courtyard geometry — not a fresh test
footprint, not an isolated specimen.

```
geometry proven
      ↓
pixels proven (editable TrixelSurface, corrected architecture)
      ↓
PIXELS ON THE ACTUAL 3.2 WORLD  ← this freeze
      ↓
next phase
```

## Exact files included

75 files, all new (no existing tracked file was modified — see
verification below). Full list: `git show --stat 84682b8`. By category:

**New production/library code**
- `trixel/pixel_geometry/pixel_surface_v1.py` — the editable TrixelSurface
  authority (JSON-backed: per-cell density, recipe provenance, edits).
- `trixel/pixel_geometry/cell_atlas_layout_v1.py` — pure cell-to-atlas-rect
  arithmetic.

**Tools**
- `tools/pixel_surface_render_v1.py` — disposable surface → raster compile.
- `tools/recipe_pixel_atlas_v1.py` — recipe-rendering primitives (a
  dependency of the render tool above).
- `tools/build_trixel_surface_identity_proof.py` /
  `_blend.py` — the identity/regenerability proof.
- `tools/export_trixel_capability_courtyard.py` — the existing courtyard
  geometry builder, staged here **unmodified** because
  `bind_trixel_art_to_courtyard.py` depends on it directly.
- `tools/bind_trixel_art_to_courtyard.py` — the actual milestone tool.
- `tools/build_courtyard_with_trixel_art_blend.py` — its Blender
  visualization.

**Gates**
- `trixel/gates/gate_pixel_geometry_trixel_surface_identity_v1.py` (8
  checks) — proves the TrixelSurface authority: JSON round-trips, edits
  propagate identically across independently re-rendered embodiments,
  an edit changes exactly one pixel, density changes never touch
  geometry, and a deleted cache rebuilds byte-identical from JSON alone.
- `trixel/gates/gate_pixel_geometry_capability_courtyard_v1.py` (30
  checks) — proves the underlying courtyard geometry this milestone's
  art sits on, staged as supporting proof of "3.2 geometry remains
  intact."

**Fixtures (generated proof artifacts + required textures)**
- `fixtures/pixel_geometry/trixel_surface_identity_proof/**`
- `fixtures/trixel_surface_identity_proof.blend`
- `fixtures/pixel_geometry/courtyard_with_trixel_art/**` (per-piece
  OBJ/MTL, per-piece atlas PNGs, per-piece TrixelSurface JSON, the
  accepted render)
- `fixtures/trixel_capability_courtyard_with_art.blend` — the visual proof
- `fixtures/pixel_geometry/courtyard_textures/{stone,cracked_rock}_16x16.png`
  — the two textures `export_trixel_capability_courtyard.py` actually
  references (wall/floor-demo materials); the two unused ones
  (`dirt_16x16.png`, `grass_16x16.png`) were left unstaged.

**Explicitly left unstaged** (per instruction — unrelated/superseded,
not depended on by this milestone):
- The original pending courtyard: `fixtures/trixel_capability_courtyard.blend`,
  `fixtures/pixel_geometry/trixel_capability_courtyard.{obj,mtl}`,
  its manifest/renders, `courtyard_parts/`, and its own build/render/
  inspect tools. **Preserved unchanged, still pending separate review.**
- The superseded atlas-as-authority experiment: `tools/build_recipe_bound_hub_proof*.py`,
  `tools/build_recipe_density_proof*.py`, their two gates, and their
  fixtures — retained on disk as an experiment, not committed.
- Five unrelated docs from the same session (doctrine comparison, legacy
  capability recovery map, two lineage traces).

## Verification performed

1. Full gate suite (21 gates, `trixel/gates/gate_*.py`): **all pass**,
   in the working copy and independently again in a fresh clone at the
   tag.
2. Full test suite (`pytest tests/`): 65 pass in the working environment.
   In a fresh clone, 7 tests fail — confirmed **pre-existing, not a
   regression**: identical failures reproduce on the immediately
   preceding commit `d32c6c6`, root-caused to tests reading a fixture
   via an absolute path outside the repo
   (`/mnt/data-drive/EngAIn_Recovery/.../EngAIn/tier1/engainos/tests/fixtures/...`)
   that only exists on this machine's working environment, not in a
   throwaway clone. Unrelated to anything in this commit.
3. `tools/export_trixel_capability_courtyard.py` confirmed byte-identical
   before and after this work (md5sum check) — read-only reuse, never
   edited.
4. `bind_trixel_art_to_courtyard.py` re-run successfully from a fresh
   clone of the tag, using only committed files, reproducing the
   courtyard-with-art fixtures.
5. `git status` confirmed zero tracked files modified at every step;
   the original pending courtyard fixtures are untouched on disk.

## Accepted scope

- Actual Trixel Capability Courtyard geometry reused, not a new test
  scene.
- Real Trixel pixel art (grass/dirt recipes) visible on the hub, all
  three terraces, and all three ramps.
- The dirt path is visually continuous from the hub onto the sloped
  ramp surface.
- 3.2 geometry (positions/indices) is provably untouched by art
  binding — the art-binding tool only rewrites UV on primary-pixel-face
  surfaces; gap-fill/wall surfaces and all positions/indices pass
  through unmodified.
- The original courtyard artifact remains completely unchanged.

## Explicitly NOT claimed

- Final art quality.
- Complete terrain taxonomy (only grass/dirt recipes are wired up; the
  other 8 terrain recipes and 4 remaining transition recipes are not).
- Object art (walls/floor/pillar keep their pre-existing non-recipe
  textures, untouched, out of scope for this pass).
- Semantic/Dragon integration — nothing here connects to the narrative/
  world-generation pipeline the legacy-architecture archaeology
  surfaced; this milestone is scoped entirely to
  `trixel/pixel_geometry/` and its immediate neighbors.

## Visual proof

`fixtures/pixel_geometry/courtyard_with_trixel_art/courtyard_with_art_render.png`
and `fixtures/trixel_capability_courtyard_with_art.blend`.
