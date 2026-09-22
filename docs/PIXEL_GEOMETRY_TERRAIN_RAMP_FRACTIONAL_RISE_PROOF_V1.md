# PIXEL_GEOMETRY / TERRAIN RAMP FRACTIONAL RISE PROOF V1

**Proof ID:** `PIXEL_GEOMETRY_TERRAIN_RAMP_FRACTIONAL_RISE_PROOF_V1`
**Applies To:** the seam between `trixel/pixel_geometry/` and `trixel/trixel32d_surface_builder.py`
**Classification:** Vertical-slice proof, not a production feature
**Status:** Accepted -- gate green, evidence generated
**Date:** 2026-09-22

---

## 1. Purpose

```text
current terrain integration (integer rise)   PROVEN, FROZEN, UNTOUCHED
non-integer rise                              THIS PROOF
different ramp orientation                    later
multiple ramps / composition                  later
taper                                         later -- different topology problem
```

The first terrain integration proof
(`PIXEL_GEOMETRY_TERRAIN_RAMP_INTEGRATION_PROOF_V1`) chose a worked
example where the required rise (`5.0`) happened to be a whole number of
terrain height layers. That left the exact remaining weak spot open: did
the seam close because the placement math is sound, or because the rise
happened to fit the terrain's own integer quantization?

This proof attacks that question directly rather than adding another
orientation variant. Worked example:

```text
ramp cells     = 5
cell metric    = 1.0
required rise  = 2.5

angle = 30 degrees
run   = sqrt(5^2 - 2.5^2) = 4.330127018922193...
```

The key experiment is not to make the terrain builder produce
`world_cell_y = 2.5`. Both terrain blocks are built through the
**unmodified** consumer/builder with the same ordinary elevation (`0.0`)
and the same `max_height_layers` (`1`, an arbitrary whole number never
derived from the rise) -- terrain-local height authority never represents
`2.5` at any point, before or after placement. The fractional rise is
reached entirely by one explicit whole-artifact rigid translation applied
**after** the builder has already finished.

---

## 2. What was built

- `trixel/pixel_geometry/terrain_ramp_integration_v1.py` -- added
  `translate_built_geometry(built, translation)`, a small addition to the
  same narrow module: it moves every position in an already-BUILT terrain
  packet by a translation vector, touching nothing else (vertex count,
  indices, normals, colors, and the packet's own declared `world_cell_y`
  are all untouched). This is the one new capability this proof needed --
  everything else reuses the frozen ramp embedding and the unmodified
  terrain consumer/builder exactly as before.
- `tools/export_terrain_ramp_fractional_rise_evidence.py` -- builds both
  terrain blocks from the **identical** request shape (same elevation,
  same `center_row`, same `max_height_layers`) as if the upper block were
  just another untouched copy of the lower one, not yet placed anywhere
  near the ramp. Placement happens afterward, explicitly:
  `upper_placement_translation()` derives a single `(0, 2.5, -8.330...)`
  translation from the ramp's own solved run and the required rise, and
  `translate_built_geometry` applies it.
- `trixel/gates/gate_pixel_geometry_terrain_ramp_fractional_rise_v1.py` --
  17/17 checks green (listed below).
- `tools/render_terrain_ramp_fractional_rise_evidence.py` -- Blender
  `--background` script, same flat-`Kd`-material, no-texture,
  no-subdivision discipline as the prior integration proof.

---

## 3. What the gate measured

```text
[PIXEL_GEOMETRY_TERRAIN_RAMP_FRACTIONAL_RISE][LOWER_TERRAIN_BUILDS_WITH_EXISTING_POLICY] TRUE
[PIXEL_GEOMETRY_TERRAIN_RAMP_FRACTIONAL_RISE][UPPER_TERRAIN_BUILDS_WITH_EXISTING_POLICY] TRUE
[PIXEL_GEOMETRY_TERRAIN_RAMP_FRACTIONAL_RISE][TERRAIN_ELEVATION_STAYS_INTEGER_EVERYWHERE] TRUE  -- lower={0} upper={0}
[PIXEL_GEOMETRY_TERRAIN_RAMP_FRACTIONAL_RISE][REQUIRED_RISE_IS_GENUINELY_NON_INTEGER] TRUE  -- required_rise=2.5
[PIXEL_GEOMETRY_TERRAIN_RAMP_FRACTIONAL_RISE][WHOLE_ARTIFACT_TRANSLATION_Y_EQUALS_REQUIRED_RISE_EXACTLY] TRUE  -- translation_y=2.5
[PIXEL_GEOMETRY_TERRAIN_RAMP_FRACTIONAL_RISE][TERRAIN_PLACEMENT_TRANSLATION_PRESERVES_INTERNAL_DISTANCES] TRUE
[PIXEL_GEOMETRY_TERRAIN_RAMP_FRACTIONAL_RISE][TRANSLATED_ARTIFACT_STILL_DECLARES_INTEGER_LOCAL_HEIGHT] TRUE  -- got {0}
[PIXEL_GEOMETRY_TERRAIN_RAMP_FRACTIONAL_RISE][RAMP_ATTACHMENT_REACHES_FRACTIONAL_WORLD_HEIGHT] TRUE  -- far_edge_ys={2.5}
[PIXEL_GEOMETRY_TERRAIN_RAMP_FRACTIONAL_RISE][RAMP_USES_FROZEN_DECLARED_ANGLE_EMBEDDING] TRUE
[PIXEL_GEOMETRY_TERRAIN_RAMP_FRACTIONAL_RISE][RAMP_CELL_METRIC_REMAINS_1_0] TRUE
[PIXEL_GEOMETRY_TERRAIN_RAMP_FRACTIONAL_RISE][RAMP_ARTWORK_UVS_UNCHANGED] TRUE
[PIXEL_GEOMETRY_TERRAIN_RAMP_FRACTIONAL_RISE][LOWER_ATTACHMENT_EDGE_MATCHES_EXACTLY] TRUE
[PIXEL_GEOMETRY_TERRAIN_RAMP_FRACTIONAL_RISE][UPPER_ATTACHMENT_EDGE_MATCHES_EXACTLY] TRUE
[PIXEL_GEOMETRY_TERRAIN_RAMP_FRACTIONAL_RISE][NO_RAMP_VERTEX_SCALING] TRUE
[PIXEL_GEOMETRY_TERRAIN_RAMP_FRACTIONAL_RISE][NO_TERRAIN_VERTEX_SCALING] TRUE
[PIXEL_GEOMETRY_TERRAIN_RAMP_FRACTIONAL_RISE][NO_POSITION_DERIVED_ADJACENCY] TRUE
[PIXEL_GEOMETRY_TERRAIN_RAMP_FRACTIONAL_RISE][COMPOSED_SCENE_IS_DETERMINISTIC] TRUE
[PIXEL_GEOMETRY_TERRAIN_RAMP_FRACTIONAL_RISE][ALL_GATES] true
```

The two checks that carry this proof's actual claim are
`TERRAIN_ELEVATION_STAYS_INTEGER_EVERYWHERE` (terrain-local authority
never sees `2.5`, before or after placement) and
`WHOLE_ARTIFACT_TRANSLATION_Y_EQUALS_REQUIRED_RISE_EXACTLY` (the
fractional height is entirely accounted for by one explicit, external,
rigid translation). Both attachment edges still match exactly, at a
world height (`2.5`) the terrain builder was never asked to produce.

---

## 4. Conclusion (narrow, on purpose)

Terrain quantization does not constrain composition-space placement.
`trixel32d_surface_builder.py`'s own vertical metric can stay in ordinary
whole-number height-layer space indefinitely while the artifact it
produces is placed at an arbitrary fractional world height by an external,
explicit rigid translation. This separates two concepts that the first
integration proof left conflated:

```text
terrain-local height authority   !=   world-placement authority
```

This proof does **not** establish that arbitrary (non-axis-aligned)
placements work the same way, that multiple stacked translations compose
safely, or that this generalizes past a single flat block being moved as
one rigid unit. Those remain open, explicitly deferred questions.

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

python3 trixel/gates/gate_pixel_geometry_terrain_ramp_fractional_rise_v1.py
python3 tools/export_terrain_ramp_fractional_rise_evidence.py

blender --background --python tools/render_terrain_ramp_fractional_rise_evidence.py
```
