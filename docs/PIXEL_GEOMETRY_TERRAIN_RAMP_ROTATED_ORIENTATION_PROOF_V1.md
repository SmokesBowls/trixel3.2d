# PIXEL_GEOMETRY / TERRAIN RAMP ROTATED ORIENTATION PROOF V1

**Proof ID:** `PIXEL_GEOMETRY_TERRAIN_RAMP_ROTATED_ORIENTATION_PROOF_V1`
**Applies To:** the seam between `trixel/pixel_geometry/` and `trixel/trixel32d_surface_builder.py`
**Classification:** Vertical-slice proof, not a production feature
**Status:** Accepted -- gate green, evidence generated
**Date:** 2026-09-22

---

## 1. Purpose

```text
flat                                  PROVEN
rigid                                 PROVEN
hard fold                             PROVEN
artwork fold/stretch                  PROVEN
closed cylinder                       PROVEN
declared-angle ramp                   PROVEN
integer-rise terrain composition      PROVEN, FROZEN
fractional-rise terrain composition   PROVEN, FROZEN
rotated terrain composition           THIS PROOF
```

```text
CONTROL                              ROTATED TEST
lower terrain                        lower terrain -- ramp along +X --
      |  ramp travels along -Z                          upper terrain
upper terrain
```

Deliberately boring geometrically: reuses the **exact same** worked
example as the integer-rise control (8 ramp cells, required rise `5.0` ->
angle `38.682` deg, run `6.245...`). No new ramp mathematics, no new rise,
no new artwork, no taper. The only new variable is `rotation_degrees=0.0`
passed to `ramp_position_to_world`, sending the ramp's fold-direction axis
to world `+X` instead of world `-Z`.

The question under test: does the composition seam still close when the
ramp's intrinsic travel direction no longer coincides with the terrain
lane's original forward axis? Answering that required keeping ramp-local,
terrain-local, and world coordinates genuinely distinct, and proving the
placement transform performs the conversion generally -- not an embedded
assumption that "the ramp always points north."

---

## 2. What was built

- `trixel/pixel_geometry/terrain_ramp_integration_v1.py` -- generalized,
  backward-compatibly:
  - `ramp_position_to_world()` gained a `rotation_degrees: float = 90.0`
    parameter. The formula is now a general rotation about Y
    (`world_x = x*cos(theta) + z*sin(theta) + offset_x`, `world_z =
    -x*sin(theta) + z*cos(theta) + offset_z`); the default `90.0`
    reproduces the two frozen proofs' fixed mapping bit for bit (both
    still pass, unmodified, with zero changes to their own code).
  - `verify_isometry()` gained the same parameter, same default.
  - New sibling function `terrain_attachment_edge_x()` (the X-boundary
    analogue of the frozen `terrain_attachment_edge()`, which is
    untouched) and new `verify_attachment_edges()` (an orientation-general
    sibling of the frozen `verify_attachment()`, also untouched) that
    takes already-extracted edges rather than assuming Z-axis polarity.
- `tools/export_terrain_ramp_rotated_orientation_evidence.py` -- builds
  the rotated scene. The terrain block is the control's shape
  *transposed*: 4 columns (depth, along X) x 8 rows (path width, along Z)
  with a 2-row dirt path, instead of 8 columns x 4 rows with a 2-column
  dirt path -- the direct, unavoidable consequence of the path now
  needing to face an X-boundary edge instead of a Z-boundary edge, not a
  new terrain concept. Terrain placement (`center_column_lower =
  (COLUMNS-1)+0.5`, `center_column_upper = -run-0.5`) is the same
  closed-form pattern as the control, just applied to `center_column`
  instead of `center_row` -- and the attachment edge polarity flips
  (lower uses its `high_x` edge, upper its `low_x` edge, the opposite of
  the control's `low_z`/`high_z` pairing), a direct, provable consequence
  of the rotation's sign flip, not a new rule.
- `trixel/gates/gate_pixel_geometry_terrain_ramp_rotated_orientation_v1.py`
  -- 16/16 checks green (listed below), including an independent,
  from-scratch recomputation of the rotation matrix (not just trusting
  `ramp_position_to_world`'s own internals) and a direct comparison
  against the frozen control's own solved ramp math object, proving
  nothing about the ramp itself changed.
- `tools/render_terrain_ramp_rotated_orientation_evidence.py` -- same
  Blender discipline as the prior two integration proofs.

---

## 3. What the gate measured

```text
[PIXEL_GEOMETRY_TERRAIN_RAMP_ROTATED_ORIENTATION][LOWER_TERRAIN_BUILDS_WITH_EXISTING_POLICY] TRUE
[PIXEL_GEOMETRY_TERRAIN_RAMP_ROTATED_ORIENTATION][UPPER_TERRAIN_BUILDS_WITH_EXISTING_POLICY] TRUE
[PIXEL_GEOMETRY_TERRAIN_RAMP_ROTATED_ORIENTATION][REUSES_IDENTICAL_RAMP_MATH_AS_INTEGER_RISE_CONTROL] TRUE
[PIXEL_GEOMETRY_TERRAIN_RAMP_ROTATED_ORIENTATION][ROTATION_IS_THE_ONLY_NEW_VARIABLE] TRUE
[PIXEL_GEOMETRY_TERRAIN_RAMP_ROTATED_ORIENTATION][RAMP_USES_FROZEN_DECLARED_ANGLE_EMBEDDING] TRUE
[PIXEL_GEOMETRY_TERRAIN_RAMP_ROTATED_ORIENTATION][RAMP_CELL_METRIC_REMAINS_1_0] TRUE
[PIXEL_GEOMETRY_TERRAIN_RAMP_ROTATED_ORIENTATION][RAMP_ARTWORK_UVS_UNCHANGED] TRUE
[PIXEL_GEOMETRY_TERRAIN_RAMP_ROTATED_ORIENTATION][ROTATION_TRANSFORM_IS_ISOMETRY_INDEPENDENTLY_VERIFIED] TRUE
[PIXEL_GEOMETRY_TERRAIN_RAMP_ROTATED_ORIENTATION][ROTATION_TRANSFORM_MATCHES_MODULE_FUNCTION] TRUE
[PIXEL_GEOMETRY_TERRAIN_RAMP_ROTATED_ORIENTATION][RAMP_TRAVELS_ALONG_WORLD_X_NOT_WORLD_Z] TRUE
[PIXEL_GEOMETRY_TERRAIN_RAMP_ROTATED_ORIENTATION][LOWER_ATTACHMENT_EDGE_MATCHES_EXACTLY] TRUE
[PIXEL_GEOMETRY_TERRAIN_RAMP_ROTATED_ORIENTATION][UPPER_ATTACHMENT_EDGE_MATCHES_EXACTLY] TRUE
[PIXEL_GEOMETRY_TERRAIN_RAMP_ROTATED_ORIENTATION][NO_RAMP_VERTEX_SCALING] TRUE
[PIXEL_GEOMETRY_TERRAIN_RAMP_ROTATED_ORIENTATION][NO_TERRAIN_VERTEX_SCALING] TRUE
[PIXEL_GEOMETRY_TERRAIN_RAMP_ROTATED_ORIENTATION][NO_POSITION_DERIVED_ADJACENCY] TRUE
[PIXEL_GEOMETRY_TERRAIN_RAMP_ROTATED_ORIENTATION][COMPOSED_SCENE_IS_DETERMINISTIC] TRUE
[PIXEL_GEOMETRY_TERRAIN_RAMP_ROTATED_ORIENTATION][ALL_GATES] true
```

Both frozen terrain-integration gates (`gate_pixel_geometry_terrain_ramp_
integration_v1.py`, `gate_pixel_geometry_terrain_ramp_fractional_rise_v1.py`)
still pass unmodified after the module's generalization -- their default
`rotation_degrees=90.0` reproduces their original fixed formula exactly.
The render shows the same clean, unbroken seam as the prior two proofs,
now with the whole composition rotated: terrain blocks arranged side by
side along X with the dirt path running horizontally, and the ramp
bridging them diagonally.

---

## 4. Conclusion (narrow, on purpose)

The composition seam does not depend on the ramp's travel direction
coinciding with the terrain lane's default forward axis. Ramp-local,
terrain-local, and world coordinates are genuinely separable: the
placement transform (a rotation about Y plus a translation, parametrized
by `rotation_degrees`) performs the conversion for any declared
orientation, and the attachment-edge verification correctly flips
polarity (which terrain edge faces the ramp) as a provable consequence of
that rotation, not a hardcoded assumption.

This proof does **not** establish that arbitrary (non-axis-aligned, e.g.
45-degree) orientations work the same way, that the terrain block's own
`orientation.vectors` could be rotated instead of the ramp's placement
(a different, untested approach), or that multiple ramps at different
orientations can compose into one scene without new adjacency concerns.
Those remain open, explicitly deferred questions.

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
python3 trixel/gates/gate_pixel_geometry_terrain_ramp_fractional_rise_v1.py

python3 trixel/gates/gate_pixel_geometry_terrain_ramp_rotated_orientation_v1.py
python3 tools/export_terrain_ramp_rotated_orientation_evidence.py

blender --background --python tools/render_terrain_ramp_rotated_orientation_evidence.py
```
