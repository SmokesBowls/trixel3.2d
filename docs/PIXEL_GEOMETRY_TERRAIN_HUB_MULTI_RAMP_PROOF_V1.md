# PIXEL_GEOMETRY / TERRAIN HUB MULTI-RAMP PROOF V1

**Proof ID:** `PIXEL_GEOMETRY_TERRAIN_HUB_MULTI_RAMP_PROOF_V1`
**Applies To:** the seam between `trixel/pixel_geometry/` and `trixel/trixel32d_surface_builder.py`
**Classification:** Vertical-slice proof, not a production feature
**Status:** Accepted -- gate green, evidence generated
**Date:** 2026-09-22

---

## 1. Purpose

```text
independent multi-ramp composition    PROVEN, FROZEN, UNTOUCHED
shared-terrain multi-ramp hub         THIS PROOF
close-proximity toxic composition     later
taper / topology mutation             later -- a different topology problem
```

```text
    upper B
       |
       | ramp B travels +X (rotation=0)
       |
lower A -- CENTRAL TERRAIN (built ONCE) -- upper A
       |         (ramp A leads further -Z to its own upper terrain)
       | ramp A travels -Z (rotation=90)
       |
```

The prior proof established that two *completely independent* compositions
don't interfere when placed apart in the same world. This proof asks a
harder question:

> Can one terrain artifact participate in two independent ramp seams
> without either ramp corrupting, duplicating, or redefining the other
> attachment?

Deliberately controlled, same discipline as every prior proof in this
ladder: both ramps reuse the exact same already-proven worked example (8
ramp cells, required rise `5.0`) and the exact same frozen embedding
call. No new ramp mathematics.

---

## 2. What was built

- `tools/export_terrain_hub_multi_ramp_evidence.py` -- builds ONE central
  8x8 terrain block (`HEIGHT_FIELD_CONNECTED_SURFACE`, flat, elevation
  `0.0` everywhere) with a plus-shaped dirt path: `DIRT_COLUMNS={3,4}`
  reaches its low-Z edge (where ramp A attaches -- the exact same column
  positions the integer-rise control already used), `DIRT_ROWS={3,4}`
  reaches its high-X edge (where ramp B attaches -- the exact same row
  positions the rotated-orientation proof already used). The central
  block reuses the control's own `CENTER_COLUMN` (`3.5`) and the rotated
  proof's own `CENTER_ROW` (`3.5`), so each ramp's path-width offset
  needs **zero** change; only each ramp's travel-direction offset shifts,
  by an amount computed directly from the hub's own declared geometry
  (`shift_a = (0, 0, -4.0)`, `shift_b = (4.0, 0, 0)`) -- never chosen to
  make it fit.
  `build_ramp_and_upper()` reuses each single-ramp proof's `build_scene()`
  completely unmodified for the ramp embedding and the upper terrain, and
  applies the shift with the same technique the independent multi-ramp
  proof already established (`translate_built_geometry` for terrain, an
  additive offset for the ramp).
- `trixel/gates/gate_pixel_geometry_terrain_hub_multi_ramp_v1.py` --
  14/14 checks green (listed below).
- `tools/render_terrain_hub_multi_ramp_evidence.py` -- same Blender
  discipline as every prior integration proof.

No production module needed any change: `terrain_ramp_integration_v1.py`
is untouched by this proof.

---

## 3. What the gate measured

```text
[PIXEL_GEOMETRY_TERRAIN_HUB_MULTI_RAMP][CENTRAL_TERRAIN_BUILT_ONCE] TRUE  -- positions=640 expected=640
[PIXEL_GEOMETRY_TERRAIN_HUB_MULTI_RAMP][NO_DUPLICATED_CENTRAL_TERRAIN_GEOMETRY] TRUE  -- cell_ranges=64
[PIXEL_GEOMETRY_TERRAIN_HUB_MULTI_RAMP][RAMP_A_ATTACHMENT_EXACT] TRUE
[PIXEL_GEOMETRY_TERRAIN_HUB_MULTI_RAMP][RAMP_B_ATTACHMENT_EXACT] TRUE
[PIXEL_GEOMETRY_TERRAIN_HUB_MULTI_RAMP][RAMP_A_TRANSFORM_INDEPENDENT] TRUE
[PIXEL_GEOMETRY_TERRAIN_HUB_MULTI_RAMP][RAMP_B_TRANSFORM_INDEPENDENT] TRUE
[PIXEL_GEOMETRY_TERRAIN_HUB_MULTI_RAMP][RAMP_A_OFFSETS_COMPUTABLE_WITHOUT_RAMP_B] TRUE
[PIXEL_GEOMETRY_TERRAIN_HUB_MULTI_RAMP][RAMP_B_OFFSETS_COMPUTABLE_WITHOUT_RAMP_A] TRUE
[PIXEL_GEOMETRY_TERRAIN_HUB_MULTI_RAMP][NO_UNDECLARED_SHARED_VERTICES] TRUE
[PIXEL_GEOMETRY_TERRAIN_HUB_MULTI_RAMP][NO_RAMP_A_TO_RAMP_B_ADJACENCY] TRUE
[PIXEL_GEOMETRY_TERRAIN_HUB_MULTI_RAMP][ATTACHMENT_A_DOES_NOT_CHANGE_ATTACHMENT_B] TRUE
[PIXEL_GEOMETRY_TERRAIN_HUB_MULTI_RAMP][ATTACHMENT_B_DOES_NOT_CHANGE_ATTACHMENT_A] TRUE
[PIXEL_GEOMETRY_TERRAIN_HUB_MULTI_RAMP][COMPOSED_SCENE_IS_DETERMINISTIC] TRUE
[PIXEL_GEOMETRY_TERRAIN_HUB_MULTI_RAMP][COMPOSITION_ORDER_DOES_NOT_MATTER] TRUE
[PIXEL_GEOMETRY_TERRAIN_HUB_MULTI_RAMP][ALL_GATES] true
```

`CENTRAL_TERRAIN_BUILT_ONCE`'s expected vertex count (`640`, not a naive
`8*8*6*4=1536`) reflects `HEIGHT_FIELD_CONNECTED_SURFACE`'s own rule that
no wall exists between same-height neighbors -- the central hub is
entirely flat, so only top/bottom faces plus the grid's own perimeter
walls exist. Getting this formula right on the first pass mattered: a
wrong formula could have silently masked real duplication or silently
flagged correct, unique geometry as duplicated.

`ATTACHMENT_A_DOES_NOT_CHANGE_ATTACHMENT_B` and its mirror are the
sharpest checks in this proof: they extract each ramp's attachment edge
directly from the shared `central_built` object in isolation -- without
the other ramp's code ever running -- and confirm the result is bit-
identical to what the full combined scene produced, proving
`central_built` is immutable shared data that neither ramp's computation
could have corrupted for the other.

All four prior terrain-integration gates still pass unmodified. The
render shows the central cross-shaped hub with both ramps branching off
cleanly in different directions to their own separate upper terraces, no
visible gap or overlap at either seam.

---

## 4. Conclusion (narrow, on purpose)

One terrain artifact can participate in two independent ramp seams at
once, built exactly once, without either ramp's placement, attachment
verification, or geometry corrupting, duplicating, or redefining the
other's. The shared hub's own declared geometry (not an assumption about
either ramp) determines both ramps' placement, and the hub itself never
needs duplicating or rebuilding to serve a second ramp.

This proof does **not** establish that more than two ramps can share one
hub, that ramps can share an attachment edge with each other (rather than
each getting its own declared edge), or that ramps placed close enough to
actually risk touching still separate correctly -- that pressure test
(deliberately toxic, geometrically near but with no declared relationship)
is explicitly deferred to the next proof. Taper remains deferred further
still, as a genuinely different topology problem.

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
python3 trixel/gates/gate_pixel_geometry_terrain_multi_ramp_composition_v1.py

python3 trixel/gates/gate_pixel_geometry_terrain_hub_multi_ramp_v1.py
python3 tools/export_terrain_hub_multi_ramp_evidence.py

blender --background --python tools/render_terrain_hub_multi_ramp_evidence.py
```
