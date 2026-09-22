# PIXEL ART CYLINDRICAL WRAP PROOF V1

**Proof ID:** `PIXEL_ART_CYLINDRICAL_WRAP_PROOF_V1`
**Applies To:** `trixel/pixel_geometry/` embedding + adjacency layers
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
cylindrical closed wrap        THIS PROOF
```

The fold-vs-stretch proof answered whether pixel artwork survives a single
hinge without stretching. This proof asks the larger question: can an
entire 2D pixel-art sheet become a **closed** 3D object -- every column
folded against its neighbor all the way around, seaming back on itself --
while every pixel still keeps its intrinsic footprint? If that holds, the
package has gone from "art can turn a corner" to "art can surround a
volume."

The cylinder is deliberately **not** implemented as "bend the artwork
until it looks round." It is a declared sequence of exact folds: one hinge
per column boundary, angle `360/N` degrees, and a radius **derived from**
the declared `1.0` cell metric rather than chosen first and forced onto
the cells:

```text
radius = 1 / (2 * sin(pi / N))
```

For the 16-column diagnostic footprint this is `radius ≈ 2.5629`, giving
`22.5` degrees per boundary and every column-to-column chord exactly
`1.0`.

---

## 2. What was built

- `trixel/pixel_geometry/embedding_v1.py` -- added
  `embed_cylindrical_closed_wrap(footprint)`. No radius parameter exists:
  the exact chord radius is always derived internally, so there is no path
  in production code that could pick a radius first and let cells
  stretch to fit it. Corner `x=0` and corner `x=width` land at exactly the
  same 3D position for every row (the closure), while remaining distinct
  corner *addresses* with independent UVs -- position coincidence is never
  used as an adjacency signal.
- `trixel/pixel_geometry/adjacency_v1.py` -- added
  `closed_wrap_seam_adjacency()`: the cardinal `source_adjacency()` PLUS
  one explicit, address-declared edge per row joining column `0` and
  column `N-1`. This is the only place any cylinder trial is authorized to
  add an edge beyond the cardinal grid, and it never looks at a 3D
  position -- exactly the same discipline `source_adjacency()` itself
  follows.
- `trixel/pixel_geometry/compiler_v1.py` -- added
  `compile_closed_wrap_footprint()`, a thin wrapper around the unmodified
  `compile_footprint()` that overrides only `compiled_adjacency` (to the
  caller-supplied declared seam adjacency) and `topology_policy` (to the
  new `TOPOLOGY_CLOSED_WRAP_SEAM`, since calling a wrap-closing topology
  `preserve_exact` would misreport that an edge was added).
- `trixel/pixel_geometry/contracts_v1.py` -- added
  `EMBEDDING_CYLINDRICAL_CLOSED_WRAP` and `TOPOLOGY_CLOSED_WRAP_SEAM`.
- `trixel/gates/gate_pixel_geometry_cylindrical_wrap_v1.py` -- the proof,
  reusing the same 16x16 diagnostic artwork and footprint-construction
  approach as the fold-vs-stretch gate. Compares the cylinder specimen's
  measured geometry against independently-recomputed formulas (never just
  trusting the embedding function's own internals), and includes a toxic
  control: a deliberately wrong radius (`1.15x` the exact chord radius,
  built locally in the gate, never a production embedding parameter) that
  is measured stretching every wrap edge to exactly `1.15` and correctly
  flagged as artwork deformation.
- `tools/export_cylindrical_wrap_evidence.py` -- writes
  `fixtures/pixel_geometry/pixel_art_cylinder_16x16.obj` (real `v`/`vt`/
  `f v/vt` faces) reusing the *same* diagnostic PNG and `.mtl` the
  fold-vs-stretch proof already wrote, plus
  `pixel_art_cylindrical_wrap_manifest.json` with only measured/computed
  values.
- `tools/render_cylindrical_wrap_evidence.py` -- Blender `--background`
  script rendering FLAT / HARD FOLD / CYLINDER side by side
  (`pixel_art_cylindrical_wrap_comparison.png`), `Closest` texture
  interpolation only, no subdivision/smoothing/displacement/UV-unwrap/auto
  projection.

---

## 3. What the gate measured

```text
[PIXEL_GEOMETRY_CYLINDRICAL_WRAP][EVERY_CELL_STILL_PRESERVED_1_TO_1] TRUE
[PIXEL_GEOMETRY_CYLINDRICAL_WRAP][EVERY_HORIZONTAL_CELL_EDGE_EQUALS_1_0] TRUE
[PIXEL_GEOMETRY_CYLINDRICAL_WRAP][EVERY_VERTICAL_CELL_EDGE_EQUALS_1_0] TRUE
[PIXEL_GEOMETRY_CYLINDRICAL_WRAP][ARTWORK_UVS_UNCHANGED_FROM_FLAT_FOOTPRINT] TRUE
[PIXEL_GEOMETRY_CYLINDRICAL_WRAP][NO_PIXEL_STRETCH] TRUE
[PIXEL_GEOMETRY_CYLINDRICAL_WRAP][COLUMN_ROTATION_INCREMENT_IS_EXACT] TRUE
[PIXEL_GEOMETRY_CYLINDRICAL_WRAP][TOTAL_WRAP_EQUALS_360_DEGREES] TRUE  -- 360.000000 degrees over 16 columns
[PIXEL_GEOMETRY_CYLINDRICAL_WRAP][SEAM_IS_EXPLICITLY_DECLARED] TRUE
[PIXEL_GEOMETRY_CYLINDRICAL_WRAP][FIRST_AND_LAST_COLUMNS_ARE_DECLARED_NEIGHBORS] TRUE
[PIXEL_GEOMETRY_CYLINDRICAL_WRAP][SEAM_CORNER_POSITIONS_COINCIDE_WITHIN_TOLERANCE] TRUE
[PIXEL_GEOMETRY_CYLINDRICAL_WRAP][NO_OTHER_ADJACENCY_CREATED_FROM_PROXIMITY] TRUE
[PIXEL_GEOMETRY_CYLINDRICAL_WRAP][EVERY_PRIMITIVE_RETAINS_SOURCE_CELL_PROVENANCE] TRUE
[PIXEL_GEOMETRY_CYLINDRICAL_WRAP][COMPILATION_IS_DETERMINISTIC] TRUE
[PIXEL_GEOMETRY_CYLINDRICAL_WRAP][TOXIC_WRONG_RADIUS_STRETCHES_EDGES_BEYOND_1_0] TRUE  -- max=1.150000000
[PIXEL_GEOMETRY_CYLINDRICAL_WRAP][TOXIC_WRONG_RADIUS_MEASURED_DISCREPANCY_REPORTED] TRUE  -- measured=1.150000000 independently_expected=1.150000000 discrepancy=0.150000000
[PIXEL_GEOMETRY_CYLINDRICAL_WRAP][TOXIC_WRONG_RADIUS_DETECTED_AS_ARTWORK_DEFORMATION] TRUE
[PIXEL_GEOMETRY_CYLINDRICAL_WRAP][ALL_GATES] true
```

As with the fold-vs-stretch gate, the green result is two claims, not one:
the cylinder holds `1.0` on every horizontal and vertical cell edge with a
seam that is explicitly declared (never inferred from the corner
positions merely coinciding), **and** a deliberately wrong radius is
correctly measured stretching every wrap edge and flagged as deformation.
The rendered comparison shows the same result visually: FLAT and HARD FOLD
keep square checker cells as already established, and CYLINDER closes into
a genuine tube with the same square, unstretched cells wrapping all the
way around back to the visible seam.

---

## 4. Conclusion (narrow, on purpose)

A 16-column discrete pixel-art footprint can be embedded as a closed
cylindrical wrap -- one exact hinge per column boundary -- without changing
its intrinsic artwork coordinates or cell metric, provided the radius is
derived from the declared metric rather than chosen independently of it.

When a radius is chosen independently of the declared metric, the wrap's
column-to-column chords deviate from `1.0` by a measurable, predictable
factor, and that deviation is detected as artwork deformation by the same
detector used in the fold-vs-stretch proof.

This proof does **not** establish that Trixel solves declared-angle ramps,
tapers, branches, characters, or terrain integration. Those remain open
questions for their own explicit trials.

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

blender --background --python tools/render_cylindrical_wrap_evidence.py
```
