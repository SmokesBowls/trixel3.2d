# PIXEL_GEOMETRY / RAMP CLOSE-PROXIMITY TOXIC PROOF V1

**Proof ID:** `PIXEL_GEOMETRY_RAMP_CLOSE_PROXIMITY_PROOF_V1`
**Applies To:** `trixel/pixel_geometry/adjacency_v1.py`'s no-proximity-derived-adjacency doctrine, under cross-object composition
**Classification:** Vertical-slice proof, not a production feature
**Status:** Accepted -- gate green, evidence generated
**Date:** 2026-09-22

---

## 1. Purpose

```text
independent distant ramps          PROVEN, FROZEN (min separation 15.9 units)
shared-terrain hub                 PROVEN, FROZEN (one shared terrain artifact)
close-proximity toxic ramps        THIS PROOF
taper / topology mutation          later -- a different topology problem
```

The independent multi-ramp proof showed two compositions don't interfere
when kept 15.9 units apart. That was an easy case: nothing was ever close
enough to be tempting. This proof makes proximity actively misleading.

Required result:

```text
GEOMETRICALLY_CLOSE                 true
DECLARED_RAMP_TO_RAMP_ADJACENCY     none
COMPILED_RAMP_TO_RAMP_ADJACENCY     none
PROXIMITY_CREATES_TOPOLOGY          false
```

No artificial adversarial offset was needed to construct this: ramp A
(the integer-rise control's own ramp, unmodified) and ramp B (the
rotated-orientation proof's own ramp, unmodified) were placed using
**each ramp's own default, already-frozen placement** -- zero added
shift. That alone produces measured exact-position coincidences between
their vertices (distance `0.0`, not merely "close"), because both
single-ramp proofs independently anchor their near edge close to world
origin. The two ramps declare no relationship to each other whatsoever.

---

## 2. What was built

- `tools/export_ramp_close_proximity_evidence.py` -- builds ramp A
  (`export_terrain_ramp_integration_evidence.build_ramp()`, called
  unmodified, rotation 90) and ramp B
  (`export_terrain_ramp_rotated_orientation_evidence.build_ramp()`,
  called unmodified, rotation 0), each placed with its own frozen offset
  constants and zero additional shift. No terrain is involved -- this
  proof is scoped precisely to ramp-to-ramp adjacency, matching the
  required-result block above.
- `trixel/gates/gate_pixel_geometry_ramp_close_proximity_v1.py` -- 11/11
  checks green (listed below). No production module needed any change:
  the proof reuses `adjacency_v1.no_proximity_derived_adjacency`,
  `adjacency_v1.compiled_adjacency_matches_source`,
  `adjacency_v1.source_adjacency`, `compiler_v1.edge_lengths`, and
  `embedding_v1.embed_declared_angle_ramp_fold` completely unmodified.
- `tools/render_ramp_close_proximity_evidence.py` -- same Blender
  discipline as every prior proof, with the two ramps given distinct flat
  colors (brown / blue) so their geometric touching is visible without
  implying they are the same object.

---

## 3. What the gate measured

```text
[PIXEL_GEOMETRY_RAMP_CLOSE_PROXIMITY][RAMP_A_USES_FROZEN_DECLARED_ANGLE_EMBEDDING] TRUE
[PIXEL_GEOMETRY_RAMP_CLOSE_PROXIMITY][RAMP_B_USES_FROZEN_DECLARED_ANGLE_EMBEDDING] TRUE
[PIXEL_GEOMETRY_RAMP_CLOSE_PROXIMITY][RAMP_A_CELL_METRIC_REMAINS_1_0] TRUE
[PIXEL_GEOMETRY_RAMP_CLOSE_PROXIMITY][RAMP_B_CELL_METRIC_REMAINS_1_0] TRUE
[PIXEL_GEOMETRY_RAMP_CLOSE_PROXIMITY][GEOMETRICALLY_CLOSE] TRUE  -- min_distance=0.000000000 exact_coincidences=4
[PIXEL_GEOMETRY_RAMP_CLOSE_PROXIMITY][DECLARED_RAMP_TO_RAMP_ADJACENCY_NONE] TRUE
[PIXEL_GEOMETRY_RAMP_CLOSE_PROXIMITY][PROXIMITY_DIAGNOSTIC_CORRECTLY_FLAGS_THE_CLOSENESS] TRUE  -- cross_ramp_offenders=4 total_offenders=4
[PIXEL_GEOMETRY_RAMP_CLOSE_PROXIMITY][COMPILED_RAMP_TO_RAMP_ADJACENCY_NONE] TRUE
[PIXEL_GEOMETRY_RAMP_CLOSE_PROXIMITY][NO_UNDECLARED_SHARED_VERTICES] TRUE
[PIXEL_GEOMETRY_RAMP_CLOSE_PROXIMITY][PROXIMITY_CREATES_TOPOLOGY_FALSE] TRUE
[PIXEL_GEOMETRY_RAMP_CLOSE_PROXIMITY][COMPOSED_SCENE_IS_DETERMINISTIC] TRUE
[PIXEL_GEOMETRY_RAMP_CLOSE_PROXIMITY][ALL_GATES] true
```

`PROXIMITY_DIAGNOSTIC_CORRECTLY_FLAGS_THE_CLOSENESS` is a deliberate
role-reversal of `no_proximity_derived_adjacency`: every prior gate that
called this function (flat, hinge-fold, cylinder) expected an **empty**
offender list as the green result. Here the offender list is expected to
be **non-empty** -- proving the diagnostic genuinely detected the
toxic closeness rather than the test being vacuous -- and every offender
found is confirmed to be a cross-ramp pair (`a[0] != b[0]`), not an
accidental same-ramp bug. `NO_UNDECLARED_SHARED_VERTICES` additionally
confirms that the two footprints' numerically-overlapping cell addresses
(both are the same 9x2 shape) never cause key confusion between the two
independent adjacency structures.

All five prior terrain-composition gates still pass unmodified. The
render shows the two ramps visibly touching at their apex -- matching the
measured exact coincidence -- while remaining two clearly distinct colored
surfaces, never merged into one.

---

## 4. Conclusion (narrow, on purpose)

Genuine geometric proximity between two independently placed,
metric-preserving ramps -- up to and including exact vertex coincidence --
never gets promoted into declared or compiled adjacency. Each ramp's
`compiled_adjacency` stays exactly `source_adjacency()` of its own
footprint alone, regardless of what happens to be nearby. The
`no_proximity_derived_adjacency` diagnostic correctly distinguishes
"these are close" from "these are neighbors" even under the most
adversarial placement this ladder has tried.

This proof does **not** establish that three or more ramps interacting
pairwise all stay this clean simultaneously, that partial overlap of
solid geometry (not just vertex coincidence) is handled the same way, or
that a renderer/physics consumer downstream of this data would also
correctly decline to treat touching ramps as connected -- this proof is
scoped to the declared/compiled adjacency graph only. Taper remains
deferred further still, as a genuinely different topology problem.

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

python3 trixel/gates/gate_pixel_geometry_ramp_close_proximity_v1.py
python3 tools/export_ramp_close_proximity_evidence.py

blender --background --python tools/render_ramp_close_proximity_evidence.py
```
