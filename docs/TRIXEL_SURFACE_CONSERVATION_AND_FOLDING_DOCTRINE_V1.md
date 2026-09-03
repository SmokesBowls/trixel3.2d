# TRIXEL SURFACE CONSERVATION AND FOLDING DOCTRINE V1

**Update ID:** `TRIXEL_SURFACE_CONSERVATION_AND_FOLDING_DOCTRINE_V1`  
**Applies To:** Trixel 3.2d artwork-to-geometry embodiment  
**Classification:** Doctrine Addendum / Architectural Design Lock  
**Status:** Accepted conceptual doctrine for future implementation and proof work  
**Date:** 2026-09-03

---

## 1. Purpose

This document preserves a core Trixel design principle that is easy to lose when the implementation is discussed only in terms of meshes, UVs, sprites, pixels, or terrain.

The principle is simple:

> **Fold, do not stretch.**

Flat artwork is treated as finite visual material. When that material is embodied on geometry, the geometry may fold, step, split, turn, occlude, or otherwise change topology, but the renderer must not silently stretch the source artwork merely because more geometric surface has become visible.

This doctrine applies at both small and large scales:

- a 16x16 sprite or tile becoming dimensional geometry;
- a larger illustrated map being draped over sculpted terrain;
- any future Trixel surface where source visual material is expected to preserve its authored spatial identity while geometry changes.

The tile explanation and the blanket explanation are two perceptions of the same rule.

---

## 2. The Core Law

Trixel treats source artwork as having **finite visual extent**.

A source pixel, texel, logical visual cell, or authored region is not an infinitely elastic patch of paint. It represents a bounded portion of the source artwork.

Therefore:

```text
geometry changes
DO NOT imply
source artwork stretches
```

Instead:

```text
geometry changes
    ↓
existing visual material is redistributed through
folding / continuation / topology / occlusion / edge movement
```

A useful statement of the law is:

> **Visual material has conserved surface extent unless an explicit authority introduces additional visual material.**

The word "conserved" is not intended to force one implementation technique. It establishes what the implementation must not fake.

If a surface requires more geometric distance than the source visual material can cover without distortion, the system must expose or resolve that mismatch deliberately. It may not hide the mismatch by elastic texture stretching.

---

## 3. The Blanket Model

The clearest physical analogy is a printed blanket laid over a table.

Start with a blanket whose visible rectangular area closely matches the tabletop:

```text
PRINTED BLANKET
──────────────────────────────

TABLE / FLAT GEOMETRY
──────────────────────────────
```

Now raise a mountain-shaped object under the center:

```text
                 /\
                /  \
_______________/    \_______________
```

A real blanket does not create extra printed material to cover the longer path up the slope, over the peak, and down the other side.

Instead, the new contour consumes more of the blanket's existing surface area. Material is pulled inward from somewhere else. If the blanket has no slack, its outer edges move inward and may expose part of the table.

Conceptually:

```text
flat footprint:
|<----------- blanket ----------->|
|<------------ table ------------>|

raised terrain:
       existing blanket material
          ____/\____
      ___/        \___
_____/                \_____

      |<-- exposed -->|
      table may become visible
```

This is the large-scale physical model for Trixel folding.

The important observation is not that every Trixel implementation must literally use cloth simulation. The important observation is that **raising geometry creates real surface-distance demand**.

That demand has to be paid for somehow.

Valid sources of that additional path length include:

- existing slack;
- folded reserve;
- neighboring visual material moving inward;
- an explicit seam;
- an explicit cut;
- a topology transition;
- an explicitly authorized new artwork region.

Invalid payment is:

- silently scaling the existing image larger;
- silently smearing pixels over a longer surface;
- silently cloning source material to fill the gap.

---

## 4. The Tile / Sprite Model

The same law applies to a small sprite or tile.

Suppose the source visual sequence is:

```text
[A][B][C][D]
```

A stretching renderer may try to create more visible surface by doing something equivalent to:

```text
[A][ A ][ B ][ B ][ C ][ C ][ D ]
```

or by continuously scaling the original cells until they cover the requested geometry.

Trixel instead preserves visual identity and changes embodiment:

```text
[A][B]
      \
      [C]
      [D]
```

The visible material continues around a fold.

`A`, `B`, `C`, and `D` remain attributable to the same source visual material. Their orientation or geometric placement may change, but they are not arbitrarily stretched into new visual content.

This is why the historical phrase **folding, not stretching** matters. It was never merely a stylistic preference. It is an ownership and conservation rule between artwork and geometry.

---

## 5. Source Artwork Is Not Paint Glued to Geometry

Conventional UV mapping commonly behaves as though source artwork were paint glued to a rubber sheet.

A UV coordinate is assigned to vertices, and when those vertices move farther apart, the image between them stretches to continue covering the surface.

That behavior is useful for ordinary rendering, but it is not automatically valid Trixel behavior.

Trixel must distinguish:

```text
SOURCE ARTWORK
what visual material exists

from

GEOMETRY
where that visual material is embodied
```

The source image is therefore better understood as **visual material authority**, not as an infinitely elastic skin.

The geometry is allowed to ask for a different shape.

It is not allowed to rewrite the amount or identity of source visual material merely to satisfy that shape.

---

## 6. Structural Consequence: Surface Demand

When flat geometry is deformed, the shortest distance across the underlying footprint can stay the same while the distance measured along the new surface increases.

For a one-dimensional cross-section:

```text
flat distance:
L_flat = x1 - x0
```

After deformation, the surface path is conceptually:

```text
L_surface = integral sqrt(1 + (dz/dx)^2) dx
```

When the surface has non-zero slope:

```text
L_surface >= L_flat
```

In two dimensions, the same idea becomes a surface-area problem rather than only a path-length problem.

This gives Trixel a useful concept:

> **Geometric surface demand** is the amount of embodied surface required by the accepted geometry.

And another:

> **Visual material supply** is the finite authored surface extent available from the source artwork.

If demand increases while supply remains fixed, the difference must be resolved explicitly.

Conceptually:

```text
surface_demand <= visual_material_supply + authorized_new_material
```

If that relation cannot be satisfied without distortion, the system has a **coverage conflict**.

A coverage conflict must become visible to topology, authoring, proof, or rejection logic. It must not disappear inside UV interpolation.

---

## 7. Permitted Embodiment Operations

The following operations are conceptually compatible with the doctrine when they preserve explicit source attribution and obey the relevant topology authority:

- preserve;
- translate;
- rotate;
- fold;
- bend within declared tolerance;
- step;
- offset;
- cut;
- split;
- merge under an explicit merge rule;
- create a seam;
- create a cap from explicitly authorized cap material;
- create a transition region from explicitly authorized transition material;
- occlude;
- cull;
- hide behind geometry;
- reveal previously folded or reserved material;
- move an outer boundary inward;
- consume declared slack or reserve.

These are not all automatically legal in every contract. They are the family of operations that can solve geometric change without pretending the source image is infinitely elastic.

---

## 8. Prohibited Silent Operations

The following are prohibited as hidden fixes for insufficient visual material:

```text
UNDECLARED_TEXTURE_STRETCH
UNDECLARED_NONUNIFORM_VISUAL_SCALE
UNDECLARED_SOURCE_DUPLICATION
UNDECLARED_PIXEL_SMEAR
UNDECLARED_TILE_REPEAT
UNDECLARED_MIRROR_FILL
UNDECLARED_SEAM_CREATION
UNDECLARED_NEW_ARTWORK
```

This doctrine does not forbid repetition, scaling, mirroring, or generated material when those are explicit authored or procedural decisions.

It forbids them from being used silently to conceal a conservation failure.

If an artist explicitly authors a repeating ground texture, repetition is legitimate.

If a terrain compiler secretly repeats part of a unique illustrated world map because a mountain needs more surface area, it is not legitimate.

---

## 9. Attribution Law

Every accepted output surface region should be explainable in terms of its source authority.

A future implementation should be able to classify output regions into outcomes such as:

```text
PRESERVED
FOLDED
SPLIT
MERGED
OCCLUDED
CULLED
CAP
TRANSITION
AUTHORIZED_GENERATED_MATERIAL
```

The exact schema is future work, but the architectural requirement is already clear:

> **No visible surface should exist merely because the renderer needed pixels.**

For unique authored artwork, every visible output region should have an attributable relationship to source visual material or to an explicit authority that created new material.

---

## 10. The Terrain / Map Case

The 2026-09-03 terrain discussion provides a large-scale proof intuition.

A world map image is placed over a dense flat terrain mesh. The terrain is then sculpted upward where the map depicts mountain ranges.

Ordinary UV mapping produces:

```text
flat map
    ↓
raise geometry
    ↓
same UV region covers a longer surface
    ↓
map artwork stretches
```

The desired Trixel behavior is:

```text
flat visual sheet + terrain substrate
    ↓
raise terrain
    ↓
visual sheet must travel farther over the new contour
    ↓
existing sheet area is consumed
    ↓
edges draw inward, slack is consumed, or folds/seams appear
```

This makes the map a useful physical-scale test of the same doctrine originally discussed with small sprite and tile surfaces.

The map and the 16x16 tile are not different principles.

They are different scales of the same principle.

---

## 11. Recommended Separation for Experiments

For experimental tools such as Blender, the doctrine suggests keeping two conceptual objects separate:

```text
Terrain_Substrate
    owns geometric shape

Map_Sheet
    owns source artwork and finite visual extent
```

The map sheet may be oversized to provide deliberate slack.

As terrain is raised, a prototype may explore:

- draping;
- shrinkwrap-style projection;
- cloth-like surface conservation;
- constrained surface deformation;
- fold reserve;
- edge draw-in;
- explicit seams.

A simple Shrinkwrap modifier may be useful for visualization, but it does not by itself prove surface conservation. A literal cloth simulation is physically closer to the blanket analogy, but it may be too expensive or unstable for production.

The final Trixel implementation is therefore not required to use Blender cloth, Shrinkwrap, or any particular DCC technique.

Those are experiments for understanding the law.

---

## 12. Distortion Budget

Perfect mathematical isometry may be unnecessary or impossible for every production case.

Trixel therefore needs a future distinction between:

- **intentional fold/bend deformation**, which changes orientation while preserving visual identity;
- **small bounded distortion**, which may be tolerated for numerical or raster reasons;
- **semantic stretch**, where the artwork visibly changes scale to satisfy geometry.

The first two may be legal under a declared tolerance.

The third is the behavior this doctrine is intended to prevent.

A future contract should declare measurable tolerances rather than relying on vague visual judgment.

Possible proof measurements include:

- local area scale ratio;
- local edge-length scale ratio;
- anisotropy;
- source-cell aspect-ratio change;
- accumulated surface-demand deficit;
- boundary draw-in distance;
- amount of consumed reserve/slack;
- number and location of explicit seams;
- source attribution coverage.

No threshold values are locked by this document.

---

## 13. Candidate Conservation Invariant

A useful future invariant is:

```text
SOURCE_VISUAL_MATERIAL
=
VISIBLE_EMBODIED_MATERIAL
+ OCCLUDED_MATERIAL
+ FOLDED_RESERVE
+ CULLED_OR_RETIRED_MATERIAL
+ EXPLICITLY_ACCOUNTED_TRANSITIONS
```

This is an accounting model, not yet a runtime schema.

Its purpose is to prevent visual material from appearing or disappearing without explanation.

Likewise, newly generated material should be accounted separately:

```text
TOTAL_OUTPUT_MATERIAL
=
ATTRIBUTED_SOURCE_MATERIAL
+ EXPLICITLY_AUTHORIZED_GENERATED_MATERIAL
```

The following equality is prohibited as an implicit assumption:

```text
TOTAL_OUTPUT_MATERIAL
=
whatever amount of texture the geometry happens to need
```

---

## 14. Relationship to Trixel Perceptual Presentation

This doctrine operates upstream of the perceptual-presentation lane documented in:

`docs/TRIXEL_PERCEPTUAL_PRESENTATION_DOCTRINE_UPDATE_V1.md`

The perceptual-presentation doctrine states that presentation may change how a trixel is seen but may not change what the trixel is.

The conservation/folding doctrine complements that rule:

```text
Artwork Authority
    ↓
Surface Conservation / Folding Authority
    ↓
Topology Authority
    ↓
Geometry Authority
    ↓
Render Expansion
    ↓
Perceptual Presentation Authority
```

Presentation may sample, quantize, stabilize, and reconstruct accepted structure for a camera.

It may not repair an upstream artwork/geometry coverage conflict by inventing or stretching structural visual material.

---

## 15. Small-Scale and Large-Scale Explanations Must Both Be Preserved

Trixel should retain both explanations because they make the same law understandable from different directions.

### Small-scale explanation

> A sprite or tile folds around geometry without stretching its source pixels or silently duplicating them.

### Large-scale explanation

> A printed blanket draped over terrain has finite material. Raising a mountain consumes surface area and pulls material inward rather than magically enlarging the print.

The tile model is useful for implementation.

The blanket model is useful for intuition.

Neither replaces the other.

---

## 16. Minimum Future Proof

A first narrow proof does not need to solve the complete production renderer.

A useful proof could begin with:

1. a deterministic rectangular source artwork sheet;
2. a deterministic flat substrate;
3. a deterministic raised ridge or mountain deformation;
4. a declared visual-material reserve or oversized source sheet;
5. a conservation-aware embodiment pass;
6. measurements of local visual scaling and boundary movement;
7. deterministic replay.

The proof should compare two runs.

### Run A — ordinary stretch

```text
fixed UV attachment
terrain deformation
image stretches with geometry
```

### Run B — conservation-aware embodiment

```text
finite visual sheet
terrain deformation
surface demand consumes reserve / causes edge draw-in / explicit fold
```

The proof should demonstrate at minimum:

```text
SAME_SOURCE_ARTWORK
SAME_TARGET_GEOMETRY
SOURCE_ATTRIBUTION_PRESERVED
NO_SILENT_SOURCE_DUPLICATION
NO_UNDECLARED_TILE_REPEAT
NO_UNDECLARED_SEAM
BOUNDED_DECLARED_DISTORTION
SURFACE_DEMAND_ACCOUNTED
DETERMINISTIC_REPLAY
```

A stronger proof may additionally demonstrate measurable border draw-in or explicit fold reserve consumption.

---

## 17. Non-Goals

This doctrine does not yet define:

- a final production solver;
- a Blender modifier stack;
- a Godot shader;
- a GPU cloth system;
- a required mesh representation;
- a specific subdivision density;
- a final UV replacement;
- a final trixel surface-conservation schema;
- exact distortion thresholds;
- exact seam policy;
- exact fold-generation policy.

Those belong to future implementation and proof work.

This document locks the **problem definition and conservation rule**, not the final algorithm.

---

## 18. Architectural Acceptance Invariants

```text
SOURCE_ARTWORK_HAS_FINITE_VISUAL_EXTENT
GEOMETRY_CHANGE_DOES_NOT_IMPLY_ARTWORK_STRETCH
NO_SILENT_SOURCE_DUPLICATION
NO_SILENT_TILE_REPEAT
NO_SILENT_NEW_VISUAL_MATERIAL
SURFACE_DEMAND_MUST_BE_ACCOUNTED
OUTPUT_SURFACE_RETAINS_SOURCE_ATTRIBUTION
FOLDS_AND_SEAMS_REQUIRE_EXPLICIT_TOPOLOGY
GENERATED_MATERIAL_REQUIRES_EXPLICIT_AUTHORITY
PRESENTATION_CANNOT_REPAIR_STRUCTURAL_COVERAGE_BY_REAUTHORING_ARTWORK
SMALL_TILE_AND_LARGE_MAP_CASES_OBEY_THE_SAME_CONSERVATION_LAW
```

---

## 19. Short Form

When the architecture becomes complicated, return to this sentence:

> **Trixel treats artwork like printed material, not rubber paint: if geometry needs more surface, the system must fold, move, reveal, cut, seam, or explicitly create material — never silently stretch the source to make the problem disappear.**
