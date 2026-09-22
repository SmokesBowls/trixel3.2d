# PIXEL_GEOMETRY / TERRAIN MULTI-RAMP COMPOSITION PROOF V1

**Proof ID:** `PIXEL_GEOMETRY_TERRAIN_MULTI_RAMP_COMPOSITION_PROOF_V1`
**Applies To:** the seam between `trixel/pixel_geometry/` and `trixel/trixel32d_surface_builder.py`
**Classification:** Vertical-slice proof, not a production feature
**Status:** Accepted -- gate green, evidence generated
**Date:** 2026-09-22

---

## 1. Purpose

```text
integer-rise terrain composition      PROVEN, FROZEN, UNTOUCHED
fractional-rise terrain composition   PROVEN, FROZEN, UNTOUCHED
rotated terrain composition           PROVEN, FROZEN, UNTOUCHED
multiple ramps / composition          THIS PROOF
taper                                 later -- different topology problem, not attempted here
```

```text
SCENE A (unmodified, reused verbatim)       SCENE B (unmodified, reused
lower terrain                               verbatim, then rigidly
      |  ramp along -Z (rotation=90)        translated as one whole)
upper terrain                               lower -- ramp along +X
                                             (rotation=0) -- upper
```

Deliberately controlled: no new ramp mathematics, no new cell metric, no
new slope. Both scenes reuse the exact same already-proven worked example
(8 ramp cells, required rise `5.0`). The question under test:

> Can two independently placed metric-preserving ramp artifacts coexist
> in one terrain composition without either placement transform,
> attachment seam, adjacency graph, or terrain artifact interfering with
> the other?

Taper is explicitly **not** attempted here. It changes intrinsic topology
-- a different problem from composing already-proven, topology-preserving
pieces. Composition is exhausted first.

---

## 2. What was built

- `tools/export_terrain_multi_ramp_composition_evidence.py` -- composes
  Scene A (the frozen integer-rise control,
  `export_terrain_ramp_integration_evidence.build_scene()`, called
  completely unmodified) and Scene B (the frozen rotated-orientation
  proof, `export_terrain_ramp_rotated_orientation_evidence.build_scene()`,
  called unmodified and then moved as **one rigid whole** by a
  `(0, 0, -30)` translation). Scene B's terrain uses the already-frozen
  `translate_built_geometry()`; its ramp gains the identical additive
  shift added directly into its existing placement offset parameters --
  still exactly a rotation-plus-translation, still an isometry, still
  zero new capability.
- `trixel/gates/gate_pixel_geometry_terrain_multi_ramp_composition_v1.py`
  -- 15/15 checks green (listed below), including two checks with no
  precedent in the single-ramp proofs: cross-scene non-interference
  (nothing in Scene A may end up suspiciously close to anything in Scene
  B, a strictly stronger bar than either scene's own internal
  `NO_POSITION_DERIVED_ADJACENCY`, since here there is no declared
  relationship between the scenes to exempt at all) and composition-order
  independence (building Scene A before Scene B must produce byte-
  identical results to building Scene B first, proving no shared mutable
  state leaks between the two independent scene builders).
- `tools/render_terrain_multi_ramp_composition_evidence.py` -- same
  Blender discipline as the prior three integration proofs.

No new production module was needed: `terrain_ramp_integration_v1.py` is
untouched by this proof (its `rotation_degrees` generalization was
already committed by the rotated-orientation proof). This proof is purely
a composition exercise over already-frozen building blocks.

---

## 3. What the gate measured

```text
[PIXEL_GEOMETRY_TERRAIN_MULTI_RAMP_COMPOSITION][SCENE_A_LOWER_BUILDS_WITH_EXISTING_POLICY] TRUE
[PIXEL_GEOMETRY_TERRAIN_MULTI_RAMP_COMPOSITION][SCENE_A_UPPER_BUILDS_WITH_EXISTING_POLICY] TRUE
[PIXEL_GEOMETRY_TERRAIN_MULTI_RAMP_COMPOSITION][SCENE_B_LOWER_BUILDS_WITH_EXISTING_POLICY] TRUE
[PIXEL_GEOMETRY_TERRAIN_MULTI_RAMP_COMPOSITION][SCENE_B_UPPER_BUILDS_WITH_EXISTING_POLICY] TRUE
[PIXEL_GEOMETRY_TERRAIN_MULTI_RAMP_COMPOSITION][BOTH_SCENES_REUSE_IDENTICAL_RAMP_MATH] TRUE
[PIXEL_GEOMETRY_TERRAIN_MULTI_RAMP_COMPOSITION][SCENES_USE_INDEPENDENT_ORIENTATIONS] TRUE
[PIXEL_GEOMETRY_TERRAIN_MULTI_RAMP_COMPOSITION][SCENE_A_LOWER_ATTACHMENT_EDGE_MATCHES_EXACTLY] TRUE
[PIXEL_GEOMETRY_TERRAIN_MULTI_RAMP_COMPOSITION][SCENE_A_UPPER_ATTACHMENT_EDGE_MATCHES_EXACTLY] TRUE
[PIXEL_GEOMETRY_TERRAIN_MULTI_RAMP_COMPOSITION][SCENE_B_LOWER_ATTACHMENT_EDGE_MATCHES_EXACTLY] TRUE
[PIXEL_GEOMETRY_TERRAIN_MULTI_RAMP_COMPOSITION][SCENE_B_UPPER_ATTACHMENT_EDGE_MATCHES_EXACTLY] TRUE
[PIXEL_GEOMETRY_TERRAIN_MULTI_RAMP_COMPOSITION][SCENE_A_PLACEMENT_IS_ISOMETRY] TRUE
[PIXEL_GEOMETRY_TERRAIN_MULTI_RAMP_COMPOSITION][SCENE_B_PLACEMENT_IS_ISOMETRY] TRUE
[PIXEL_GEOMETRY_TERRAIN_MULTI_RAMP_COMPOSITION][NO_CROSS_SCENE_ADJACENCY] TRUE
[PIXEL_GEOMETRY_TERRAIN_MULTI_RAMP_COMPOSITION][SCENES_ARE_GENUINELY_SEPARATED_NOT_JUST_NON_COINCIDENT] TRUE  -- min_cross_scene_distance=15.914148
[PIXEL_GEOMETRY_TERRAIN_MULTI_RAMP_COMPOSITION][COMPOSED_SCENE_IS_DETERMINISTIC] TRUE
[PIXEL_GEOMETRY_TERRAIN_MULTI_RAMP_COMPOSITION][COMPOSITION_ORDER_DOES_NOT_MATTER] TRUE
[PIXEL_GEOMETRY_TERRAIN_MULTI_RAMP_COMPOSITION][ALL_GATES] true
```

All three prior terrain-integration gates
(`gate_pixel_geometry_terrain_ramp_integration_v1.py`,
`..._fractional_rise_v1.py`, `..._rotated_orientation_v1.py`) still pass
unmodified. The render shows both compositions clearly, separated by a
wide, unambiguous gap -- Scene A's vertical -Z composition above, Scene
B's rotated +X composition below, neither touching or influencing the
other.

---

## 4. Conclusion (narrow, on purpose)

Two independently placed, metric-preserving ramp artifacts coexist in one
terrain composition without interference: each scene's placement
transform, attachment seams, and (already-proven) internal non-adjacency
hold exactly as they did in isolation, and composing them introduces no
new adjacency, no overlap, and no order-dependence. The whole-scene
translation applied to Scene B is itself just another instance of the
same rotation-plus-translation discipline every prior proof in this
ladder has relied on -- no new geometric capability was required to prove
this, only correct composition.

This proof does **not** establish that ramps can share a single terrain
block's attachment edges (a genuine "hub" composition, where one lower
terrain feeds two ramps), that more than two ramps compose the same way,
or that ramps placed closer together (deliberately testing the boundary
of `NO_CROSS_SCENE_ADJACENCY`) still separate cleanly. Those remain open,
explicitly deferred questions. Composition is judged exhausted enough to
move on only once the user says so -- this proof does not claim to be the
last composition question.

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
python3 tools/export_terrain_multi_ramp_composition_evidence.py

blender --background --python tools/render_terrain_multi_ramp_composition_evidence.py
```
