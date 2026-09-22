# PIXEL ART DECLARED-ANGLE RAMP PROOF V1

**Proof ID:** `PIXEL_ART_DECLARED_ANGLE_RAMP_PROOF_V1`
**Applies To:** `trixel/pixel_geometry/` embedding layer
**Classification:** Vertical-slice proof, not a production feature
**Status:** Accepted -- gate green, evidence generated
**Date:** 2026-09-21

---

## 1. Purpose

The production ladder to this point:

```text
flat                         PROVEN (gate_pixel_geometry_flat_footprint_v1)
rigid transform               PROVEN (gate_pixel_geometry_rigid_embedding_v1)
hard 90 degree fold            PROVEN (gate_pixel_geometry_hinge_fold_v1, frozen)
pixel art fold vs stretch      PROVEN (gate_pixel_geometry_artwork_fold_v1)
closed cylindrical wrap        PROVEN (gate_pixel_geometry_cylindrical_wrap_v1)
declared-angle ramp            THIS PROOF
```

Per instruction, this trial's first question was deliberately **not**
"what angle looks right." It was solved as closed-form geometry, before
any embedding code ran:

> Given cell metric, number of cells, and a required rise, what
> horizontal run and angle are geometrically possible without stretching
> any source cell?

A straight chain of `N` unit cells is a rigid rotation for any angle --
rotation never stretches anything, the same fact `embed_rigid` already
relies on. So every non-stretching `(run, rise)` pair for that chain lies
exactly on one circle:

```text
run^2 + rise^2 = (num_cells * cell_metric)^2
```

`rise` is the only free input; `run` and `angle` are then **determined**,
never independently chosen. This also gives the feasibility law for free:
no point on that circle has `rise > num_cells * cell_metric`, so a
required rise beyond that is not a worse angle to search for -- it is not
on the circle at all, and the only correct responses are to add cells or
introduce another fold, never to force the fit.

This proof does not connect to grass/step/path terrain -- that remains
explicit future work.

---

## 2. What was built

- `trixel/pixel_geometry/ramp_geometry_v1.py` -- the math, standing alone
  from any embedding or position concept.
  `solve_ramp_run_and_angle(num_cells, required_rise, cell_metric=1.0)`
  returns `(angle_degrees, run, chain_length)` computed directly from the
  circle equation, or raises `ValueError` (`REJECT_EMBEDDING`) when
  `required_rise` exceeds `num_cells * cell_metric`.
- `trixel/pixel_geometry/embedding_v1.py` -- added
  `embed_declared_angle_ramp_fold(footprint, hinge_corner_x, angle_degrees)`,
  a direct generalization of `embed_hard_90_degree_hinge_fold`: the far
  side beyond the hinge is a rigid rotation by `angle_degrees` instead of
  a hardwired 90. At `angle_degrees=90.0` it reproduces the frozen
  hinge-fold function's output exactly -- proven by the gate comparing
  both formulas directly, not merely asserted. It intentionally has no
  opinion about whether a given angle reaches any particular rise; that
  question belongs only to `ramp_geometry_v1`.
- `trixel/pixel_geometry/contracts_v1.py` -- added
  `EMBEDDING_DECLARED_ANGLE_RAMP_FOLD`.
- `trixel/gates/gate_pixel_geometry_declared_angle_ramp_v1.py` -- proves
  the math first (several `(num_cells, rise)` pairs land exactly on the
  metric circle; infeasible rises are rejected), then the embedding
  (metric preservation, UV/adjacency/disposition invariance, exact
  reproduction of the frozen 90-degree case, and that the far endpoint
  actually lands at the solved `(run, rise)`), then a toxic control: a
  locally-built (never production) endpoint that forces both run and rise
  to the full chain length simultaneously -- off the metric circle by
  construction -- correctly measured stretching to `sqrt(2)` and flagged
  as artwork deformation.
- `tools/export_declared_angle_ramp_evidence.py` -- writes
  `pixel_art_declared_angle_ramp_16x16.obj` (real `v`/`vt`/`f v/vt`
  faces) using the solved angle for the worked example (8 cells beyond
  the hinge, required rise `5.0` -> angle `38.682...` degrees, run
  `6.245...`), reusing the same diagnostic PNG and `.mtl` as the prior two
  proofs, plus a manifest of only computed values.
- `tools/render_declared_angle_ramp_evidence.py` -- Blender
  `--background` script rendering FLAT / HARD FOLD (90 deg, frozen) /
  DECLARED-ANGLE RAMP (38.68 deg) side by side
  (`pixel_art_declared_angle_ramp_comparison.png`), `Closest` texture
  interpolation only, no subdivision/smoothing/displacement/UV-unwrap/auto
  projection.

---

## 3. What the gate measured

```text
[PIXEL_GEOMETRY_DECLARED_ANGLE_RAMP][RAMP_MATH_SOLUTIONS_LAND_EXACTLY_ON_THE_METRIC_CIRCLE] TRUE
[PIXEL_GEOMETRY_DECLARED_ANGLE_RAMP][RAMP_MATH_REJECTS_RISE_BEYOND_CHAIN_LENGTH] TRUE
[PIXEL_GEOMETRY_DECLARED_ANGLE_RAMP][WORKED_EXAMPLE_SOLVED_BEFORE_EMBEDDING] TRUE  -- num_cells=8 rise=5.0 -> angle=38.682187 deg, run=6.244998
[PIXEL_GEOMETRY_DECLARED_ANGLE_RAMP][RAMP_FOLD_AT_90_DEGREES_REPRODUCES_FROZEN_HINGE_FOLD_EXACTLY] TRUE
[PIXEL_GEOMETRY_DECLARED_ANGLE_RAMP][RAMP_ALL_CELL_EDGES_REMAIN_1_0] TRUE
[PIXEL_GEOMETRY_DECLARED_ANGLE_RAMP][RAMP_ARTWORK_UVS_UNCHANGED] TRUE
[PIXEL_GEOMETRY_DECLARED_ANGLE_RAMP][RAMP_SOURCE_ADJACENCY_UNCHANGED] TRUE
[PIXEL_GEOMETRY_DECLARED_ANGLE_RAMP][RAMP_ALL_CELLS_PRESERVED_1_TO_1] TRUE
[PIXEL_GEOMETRY_DECLARED_ANGLE_RAMP][RAMP_IS_EMBEDDING_NOT_ARTWORK_DEFORMATION] TRUE
[PIXEL_GEOMETRY_DECLARED_ANGLE_RAMP][RAMP_FAR_ENDPOINT_MATCHES_SOLVED_RUN_AND_RISE] TRUE
[PIXEL_GEOMETRY_DECLARED_ANGLE_RAMP][TOXIC_OFF_CIRCLE_ENDPOINT_STRETCHES_EDGES] TRUE  -- measured=1.414213562 expected=1.414213562
[PIXEL_GEOMETRY_DECLARED_ANGLE_RAMP][TOXIC_OFF_CIRCLE_ENDPOINT_DETECTED_AS_ARTWORK_DEFORMATION] TRUE
[PIXEL_GEOMETRY_DECLARED_ANGLE_RAMP][ALL_GATES] true
```

As with the prior two proofs, the green result is two claims: the ramp
holds `1.0` on every cell edge at a genuinely non-trivial, mathematically
solved angle (not 0, not 90), **and** a toxic endpoint deliberately placed
off the metric circle is correctly measured stretching and flagged as
deformation. The rendered comparison shows the same result visually: FLAT
and HARD FOLD as already established, and RAMP leaning at a visibly
shallower angle than the hard fold, with the same square, unstretched
checker cells throughout.

---

## 4. Conclusion (narrow, on purpose)

Given a declared cell metric and a fixed number of cells in a straight
chain, the set of world-space endpoints reachable without stretching any
cell is exactly the circle `run^2 + rise^2 = (num_cells * cell_metric)^2`.
Angle is not a free aesthetic parameter of a non-stretching ramp -- it is
determined by whichever rise is required, and a required rise off that
circle is not reachable by any angle at this cell count.

`embed_declared_angle_ramp_fold` builds the geometry once such an angle
is known to be reachable; it does not decide reachability itself, and
`ramp_geometry_v1.solve_ramp_run_and_angle` never builds geometry. Keeping
these separate is what let this trial reproduce the frozen 90-degree
hinge fold exactly as a special case rather than as a second, divergent
implementation.

This proof does **not** establish that Trixel solves multi-segment ramps
(approach + incline + landing), tapers, branches, characters, or terrain
integration. Those remain open questions for their own explicit trials.

---

## 5. Reproduction

```bash
python3 trixel/gates/gate_pixel_geometry_flat_footprint_v1.py
python3 trixel/gates/gate_pixel_geometry_rigid_embedding_v1.py
python3 trixel/gates/gate_pixel_geometry_hinge_fold_v1.py

python3 tools/generate_pixel_geometry_diagnostic_art.py

python3 trixel/gates/gate_pixel_geometry_artwork_fold_v1.py
python3 tools/export_pixel_art_fold_stretch_evidence.py

python3 trixel/gates/gate_pixel_geometry_cylindrical_wrap_v1.py
python3 tools/export_cylindrical_wrap_evidence.py

python3 trixel/gates/gate_pixel_geometry_declared_angle_ramp_v1.py
python3 tools/export_declared_angle_ramp_evidence.py

blender --background --python tools/render_declared_angle_ramp_evidence.py
```
