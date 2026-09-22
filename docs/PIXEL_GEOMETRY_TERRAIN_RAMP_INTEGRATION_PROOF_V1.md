# PIXEL_GEOMETRY / TERRAIN RAMP INTEGRATION PROOF V1

**Proof ID:** `PIXEL_GEOMETRY_TERRAIN_RAMP_INTEGRATION_PROOF_V1`
**Applies To:** the seam between `trixel/pixel_geometry/` and `trixel/trixel32d_surface_builder.py`
**Classification:** Vertical-slice proof, not a production feature
**Status:** Accepted -- gate green, evidence generated
**Date:** 2026-09-22

---

## 1. Purpose

The production ladder to this point:

```text
flat / rigid / hard fold / artwork fold-stretch /
closed cylinder / declared-angle ramp          ALL PROVEN, UNTOUCHED
terrain ramp integration                        THIS PROOF
```

Every prior trial lived entirely inside `trixel/pixel_geometry/`, deliberately
walled off from "the existing terrain authorities" (its own `__init__.py`
says so explicitly). This proof crosses that boundary for the first time:

```text
grass lower level (existing HEIGHT_FIELD_CONNECTED_SURFACE terrain)
       |
dirt path (same terrain, different per-cell color)
       |
declared-angle ramp (pixel_geometry, frozen embedding)
       |
grass upper level (existing HEIGHT_FIELD_CONNECTED_SURFACE terrain)
```

Investigation before writing any code found that this repository actually
has **two** separate terrain authorities, not one: `trixel/global_sample/`
(a smooth heightfield whose canonical topology hardcodes horizontal
position to the grid index, so any slope in it silently stretches surface
distance) and `trixel/trixel32d_surface_builder.py` (a quantized,
integer-height-layer connected-surface builder -- the one with existing
grass/stone "texel" tile evidence, and the one this proof's phrase
"connected terrain surface lane" refers to). Neither can represent a
metric-preserving slope internally: the first stretches, the second only
knows flat-topped blocks connected by vertical cliff faces. The ramp
therefore cannot be poured into either contract as new data -- it can only
be a separately generated, separately placed geometry artifact, exactly
like the OBJ specimens every prior proof already exports.

---

## 2. What was built

- `trixel/pixel_geometry/terrain_ramp_integration_v1.py` -- the only new
  production module, deliberately narrow. It never builds terrain (the
  caller calls the unmodified `trixel32d_surface_consumer.
  consume_surface_request_packet` directly) and never re-derives ramp
  geometry (the caller calls the unmodified `embed_declared_angle_ramp_
  fold` directly). Its job is: place the ramp's already-computed
  positions into world space by a pure rotation + translation
  (`ramp_position_to_world`, proven to be an isometry -- no scaling --
  by `verify_isometry`), then check whether the ramp's near/far edges
  coincide exactly with a declared terrain attachment edge
  (`verify_attachment`).
- `tools/export_terrain_ramp_integration_evidence.py` -- builds the demo
  scene: two 8-column x 4-row terrain blocks (`GGGDDGGG` per row, columns
  3-4 are the dirt path) through the **unmodified** consumer/builder with
  `HEIGHT_FIELD_CONNECTED_SURFACE`, and the ramp through the **unmodified**
  `embed_declared_angle_ramp_fold` using the exact worked example already
  proven in `gate_pixel_geometry_declared_angle_ramp_v1.py` (8 cells beyond
  the hinge, required rise `5.0` -> angle `38.682` deg, run `6.245`).
  Critically, the terrain blocks' placement (`center_row`, `center_column`
  -- ordinary, pre-existing free parameters of the terrain request schema,
  no code changes) is **derived from the ramp's solved run**, never the
  reverse: `center_row_lower = (ROWS-1) + 0.5`, `center_row_upper =
  -solved.run - 0.5`. The ramp's minimal near-flat stub cell (needed only
  because the frozen embedding requires `0 < hinge_corner_x < width`) is
  excluded from the placed scene, since it occupies exactly the same world
  space the lower terrain's own boundary row already covers -- the
  `NO_POSITION_DERIVED_ADJACENCY` check caught this as 12 exact-position
  offenders on the first run and it was fixed by excluding that cell, not
  by loosening the check.
- `trixel/gates/gate_pixel_geometry_terrain_ramp_integration_v1.py` --
  11/11 checks green (listed below).
- `tools/render_terrain_ramp_integration_evidence.py` -- Blender
  `--background` script, flat `Kd` materials only (no textures, matching
  the terrain builder's own per-cell vertex-color appearance), no
  subdivision/smoothing/displacement, rendering
  `terrain_ramp_integration_render.png`.

---

## 3. What the gate measured

```text
[PIXEL_GEOMETRY_TERRAIN_RAMP_INTEGRATION][LOWER_TERRAIN_BUILDS_WITH_EXISTING_POLICY] TRUE
[PIXEL_GEOMETRY_TERRAIN_RAMP_INTEGRATION][UPPER_TERRAIN_BUILDS_WITH_EXISTING_POLICY] TRUE
[PIXEL_GEOMETRY_TERRAIN_RAMP_INTEGRATION][RAMP_USES_FROZEN_DECLARED_ANGLE_EMBEDDING] TRUE
[PIXEL_GEOMETRY_TERRAIN_RAMP_INTEGRATION][RAMP_CELL_METRIC_REMAINS_1_0] TRUE
[PIXEL_GEOMETRY_TERRAIN_RAMP_INTEGRATION][RAMP_ARTWORK_UVS_UNCHANGED] TRUE
[PIXEL_GEOMETRY_TERRAIN_RAMP_INTEGRATION][LOWER_ATTACHMENT_EDGE_MATCHES_EXACTLY] TRUE
[PIXEL_GEOMETRY_TERRAIN_RAMP_INTEGRATION][UPPER_ATTACHMENT_EDGE_MATCHES_EXACTLY] TRUE
[PIXEL_GEOMETRY_TERRAIN_RAMP_INTEGRATION][NO_RAMP_VERTEX_SCALING] TRUE
[PIXEL_GEOMETRY_TERRAIN_RAMP_INTEGRATION][NO_TERRAIN_VERTEX_SCALING] TRUE
[PIXEL_GEOMETRY_TERRAIN_RAMP_INTEGRATION][NO_POSITION_DERIVED_ADJACENCY] TRUE
[PIXEL_GEOMETRY_TERRAIN_RAMP_INTEGRATION][COMPOSED_SCENE_IS_DETERMINISTIC] TRUE
[PIXEL_GEOMETRY_TERRAIN_RAMP_INTEGRATION][ALL_GATES] true
```

`NO_EXISTING_TERRAIN_CONTRACT_MODIFIED` is verified externally, not as a
gate assertion: `git diff --stat` against `trixel32d_surface_builder.py`,
`trixel32d_surface_consumer.py`, `trixel32d_surface_emitter.py`,
`trixel32d_worldfield_to_worldcell_projection.py`,
`trixel/global_sample/`, and every frozen gate shows zero changes.

The rendered evidence shows a continuous dirt path rising cleanly from the
lower grass level to the upper grass level, with no visible gap or overlap
at either seam -- the same claim the numeric attachment checks make,
visible directly.

---

## 4. Conclusion (narrow, on purpose)

A metric-preserving `pixel_geometry` ramp can connect two independently
built `trixel32d_surface_builder` terrain surfaces, in exact world-space
coincidence at both seams, using only:

- the frozen `embed_declared_angle_ramp_fold` embedding, unmodified,
- the unmodified terrain consumer/builder, called twice with ordinary
  request parameters,
- one small, narrow verification/placement module that performs a
  rotation and translation (never a scale) derived from the ramp's own
  solved geometry.

Neither terrain authority (`trixel32d_surface_builder.py` or
`trixel/global_sample/`) needed to change, stretch, or reinterpret its own
rules to make this work, because the ramp was never asked to become
terrain data -- it stayed a separately placed geometry artifact throughout.

This proof does **not** establish that ramps are a first-class terrain
topology policy, that this placement approach generalizes to arbitrary
(non-axis-aligned, non-integer-rise) level layouts, or that
`trixel32d_surface_builder.py` should be extended with a native ramp
policy. Those remain open, explicitly deferred questions -- to be earned
from this successful composition proof, not assumed by it.

---

## 5. Reproduction

```bash
python3 trixel/gates/gate_pixel_geometry_flat_footprint_v1.py
python3 trixel/gates/gate_pixel_geometry_rigid_embedding_v1.py
python3 trixel/gates/gate_pixel_geometry_hinge_fold_v1.py

python3 tools/generate_pixel_geometry_diagnostic_art.py
python3 trixel/gates/gate_pixel_geometry_artwork_fold_v1.py
python3 trixel/gates/gate_pixel_geometry_cylindrical_wrap_v1.py
python3 trixel/gates/gate_pixel_geometry_declared_angle_ramp_v1.py

python3 trixel/gates/gate_pixel_geometry_terrain_ramp_integration_v1.py
python3 tools/export_terrain_ramp_integration_evidence.py

blender --background --python tools/render_terrain_ramp_integration_evidence.py
```
