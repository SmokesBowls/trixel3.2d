# PIXEL ART FOLD VS STRETCH PROOF V1

**Proof ID:** `PIXEL_ART_FOLD_VS_STRETCH_PROOF_V1`
**Applies To:** `trixel/pixel_geometry/` artwork-mapping layer
**Classification:** Vertical-slice proof, not a production feature
**Status:** Accepted -- gate green, evidence generated
**Date:** 2026-09-21

---

## 1. Purpose

`gate_pixel_geometry_hinge_fold_v1.py` already proved, geometry-only, that
`trixel.pixel_geometry` can hard-fold a discrete `CellFootprint` 90 degrees
without changing cell identity, adjacency, or the declared `1.0` cell
metric. That proof never touched pixel artwork, so it could not answer the
question that motivated the fold mechanism in the first place:

> Can pixel artwork travel through a 3D fold without stretching?

This proof attaches an actual, deterministic pixel-art asset to the same
kind of footprint and measures the answer directly, alongside a
deliberately toxic control that proves the measurement itself has teeth.

---

## 2. What was built

- `tools/generate_pixel_geometry_diagnostic_art.py` -- generates
  `fixtures/pixel_geometry/pixel_fold_diagnostic_16x16.png`, a 16x16
  diagnostic image built entirely from explicit per-pixel rules (bright
  border, center cross at the hinge boundary, four differently-paletted
  checker quadrants, one asymmetric marker), with no antialiasing and no
  resampling -- one PNG pixel is one source visual cell.
- `trixel/pixel_geometry/artwork_mapping_v1.py` -- the only new production
  module. Its sole responsibility is intrinsic corner address -> canonical
  artwork coordinate (`u = corner_x / W`, `v = 1.0 - corner_row / H`). It
  never reads a 3D position, so no embedding can alter the UV it returns
  for a given address.
- `trixel/gates/gate_pixel_geometry_artwork_fold_v1.py` -- the proof
  itself, over a real 16x16 footprint built directly from the diagnostic
  PNG's pixels, comparing three specimens:
  - **A -- FLAT** (`embed_flat`, control)
  - **B -- HARD FOLD** (`embed_hard_90_degree_hinge_fold`, hinge at
    `corner_x = 8`, exactly on the diagnostic art's own center column, so
    columns 0..7 stay flat and columns 8..15 fold)
  - **C -- FORCED DIAGONAL STRETCH** (a toxic position map built only
    inside the gate/tool, never added to `embedding_v1.py`, that pins a
    source cell edge's world-space endpoints `run=1.0` / `rise=1.0` apart
    -- geometric length `sqrt(2)` -- while its UV interval stays the
    nominal one-pixel span)
- `tools/export_pixel_art_fold_stretch_evidence.py` -- writes all three
  specimens as real `.obj` files with `v` and `vt` and `f v/vt v/vt v/vt`
  faces, one shared `.mtl` pointing `map_Kd` at the one shared PNG, and
  `fixtures/pixel_geometry/pixel_art_fold_stretch_manifest.json` recording
  what was actually measured on the generated geometry (nothing
  hand-typed).
- `tools/render_pixel_art_fold_stretch_evidence.py` -- a Blender
  `--background` script that imports the three OBJs exactly as written,
  forces every image texture node to `Closest` (nearest-neighbor)
  interpolation, adds no subdivision/smoothing/displacement/UV-unwrap/auto
  projection, arranges the three specimens side by side, and renders
  `fixtures/pixel_geometry/pixel_art_fold_stretch_comparison.png`.

---

## 3. What the gate measured

```text
[PIXEL_GEOMETRY_ARTWORK_FOLD][DIAGNOSTIC_ART_IS_16X16] TRUE
[PIXEL_GEOMETRY_ARTWORK_FOLD][DIAGNOSTIC_ART_HAS_NO_RESAMPLING] TRUE
[PIXEL_GEOMETRY_ARTWORK_FOLD][FLAT_AND_FOLD_USE_IDENTICAL_INTRINSIC_UVS] TRUE
[PIXEL_GEOMETRY_ARTWORK_FOLD][HARD_FOLD_ALL_CELL_EDGES_REMAIN_1_0] TRUE
[PIXEL_GEOMETRY_ARTWORK_FOLD][HARD_FOLD_ARTWORK_COORDINATES_UNCHANGED] TRUE
[PIXEL_GEOMETRY_ARTWORK_FOLD][HARD_FOLD_SOURCE_ADJACENCY_UNCHANGED] TRUE
[PIXEL_GEOMETRY_ARTWORK_FOLD][HARD_FOLD_ALL_CELLS_PRESERVED_1_TO_1] TRUE
[PIXEL_GEOMETRY_ARTWORK_FOLD][TOXIC_DIAGONAL_HAS_EDGE_GREATER_THAN_1_0] TRUE
[PIXEL_GEOMETRY_ARTWORK_FOLD][TOXIC_DIAGONAL_EXPECTED_STRETCH_FACTOR_DETECTED] TRUE  -- measured=1.414213562 expected=1.414213562
[PIXEL_GEOMETRY_ARTWORK_FOLD][TOXIC_DIAGONAL_UV_SPAN_REMAINS_UNCHANGED] TRUE
[PIXEL_GEOMETRY_ARTWORK_FOLD][FOLD_IS_EMBEDDING_NOT_ARTWORK_DEFORMATION] TRUE
[PIXEL_GEOMETRY_ARTWORK_FOLD][DIAGONAL_CONTROL_IS_DETECTED_AS_ARTWORK_DEFORMATION] TRUE
[PIXEL_GEOMETRY_ARTWORK_FOLD][ALL_GATES] true
```

The green result is not "the fold worked." It is two independent claims
holding at once: the hard fold preserved the artwork metric with zero
edges flagged as deformed, **and** the toxic diagonal control -- the same
detector, run on geometry that everyone already knows is wrong -- correctly
flagged every stretched edge while confirming its UV interval never moved.
A gate that only checked the first half would not have proven its own
detector could catch anything.

The rendered comparison (`pixel_art_fold_stretch_comparison.png`) shows
the same result visually: the flat and hard-fold specimens keep square,
proportional checker cells (the fold turns the corner but the art does
not warp), while the forced-diagonal specimen visibly elongates into
rectangles along the sheared direction.

---

## 4. Conclusion (narrow, on purpose)

A discrete pixel-art footprint can cross a hard geometric hinge without
changing its intrinsic artwork coordinates or cell metric.

When fixed world-space endpoints require an edge longer than the declared
intrinsic cell metric, preserving those endpoints necessarily deforms the
artwork footprint.

Therefore endpoint-fitting and metric-preserving embedding are not
equivalent operations.

This proof does **not** establish that Trixel solves arbitrary ramps,
cylinders, tapers, branches, characters, or terrain integration. Those
remain open questions for their own explicit trials.

---

## 5. Reproduction

```bash
python3 trixel/gates/gate_pixel_geometry_flat_footprint_v1.py
python3 trixel/gates/gate_pixel_geometry_rigid_embedding_v1.py
python3 trixel/gates/gate_pixel_geometry_hinge_fold_v1.py

python3 tools/generate_pixel_geometry_diagnostic_art.py

python3 trixel/gates/gate_pixel_geometry_artwork_fold_v1.py

python3 tools/export_pixel_art_fold_stretch_evidence.py

blender --background --python tools/render_pixel_art_fold_stretch_evidence.py
```
