# TRIXEL CAPABILITY COURTYARD V1

**Proof ID:** `TRIXEL_CAPABILITY_COURTYARD_V1`
**Applies To:** composition of everything in `trixel/pixel_geometry/` proven through the twelve-gate ladder
**Classification:** Showcase scene, not a new geometric capability
**Status:** Accepted -- gate green, evidence generated
**Date:** 2026-09-22

---

## 1. Purpose

Not another isolated proof render -- one composed scene, ~32x28 world
units, that naturally uses everything the twelve-gate pixel_geometry
ladder earned:

```text
flat                                  used (hub, all terraces)
rigid                                 used (floor/wall reuse, pillar orientation, wall reorientation)
hard fold                             used (west retaining wall)
closed cylinder                       used (eight-sided pillar)
declared-angle ramp                   used (north/south/east ramps)
terrain/ramp integration              used (three ramps attach to one hub)
fractional world placement            used (south terrace, Y=2.5)
rotated ramp instances                used (east ramp, same implementation as north, rotated)
independent multiple ramps            used (three ramps exist simultaneously)
shared-terrain multi-ramp hub         used (the central 12x12 hub itself)
exact geometric contact without
topological connection                used (the close-proximity exhibit)
```

Taper is deliberately absent -- it crosses into topology mutation, a
capability this ladder has not yet earned.

Every piece calls a FROZEN, already-proven production function exactly
as its own gate proved it. This tool adds no new geometric capability and
no new production module -- it is pure composition.

---

## 2. Scope decision: no real-time interactivity

The original specification asked for a walkable player controller,
physical collision, and a live F1 debug toggle. Before building anything,
this was raised explicitly: everything built in this session has been
Python geometry plus Blender `--background` still renders -- there is no
player controller, no collision, and no real-time toggle anywhere in this
toolchain, and building one would mean either a new engine dependency or
crossing into the separate `godotollama` repo that the project's own
doctrine keeps interactive/walkable harnesses in.

The user chose to stay entirely inside `trixel3.2d` with the existing
toolchain: a composed scene rendered by Blender, with the "F1 toggle"
idea approximated as two separate renders (clean vs. debug-overlay)
rather than a live in-engine toggle. That is what this proof delivers.

---

## 3. Layout

```text
    NORTH TERRACE  Y=3.0                    (declared-angle ramp, rise 3.0,
         ^ north ramp (rotation=90)          integer, exact 3-4-5 triangle)
         |
    WEST WALL -- CENTRAL HUB (12x12, built ONCE) -- EAST RAMP (rotation=0)
    (hinge fold        |                                    -> EAST TERRACE
     + rigid 180)       v south ramp (rotation=270)
                   SOUTH TERRACE  Y=2.5      (fractional, via whole-artifact
                                              translation, never terrain-
                                              local elevation)

    Elsewhere, clear of everything above:
      - wrapped 8-sided pillar (closed cylindrical wrap, diagnostic strip)
      - rigid floor/wall reuse (one footprint, embed_flat + embed_rigid)
      - close-proximity exhibit (two independent strips, exact contact,
        no declared relationship)
```

The central hub is an 8x8-cell-larger version of the shared-terrain-hub
proof's own design: 12x12, flat grass, a plus-shaped dirt path
(`DIRT_COLUMNS={5,6}` for the north/south path, `DIRT_ROWS={5,6}` for the
east path), built through the **unmodified** `consume_surface_request_
packet` exactly once. Three ramps attach to three different declared
edges of that same hub.

---

## 4. Real artwork, not placeholder colors

Grass, dirt, stone, and cracked-rock textures are rendered from the
**existing, unmodified** `trixel_recipe_renderer.py` against real recipe
files already in the repository (`recipes/terrain/forest.dense_canopy.json`,
`recipes/transitions/grass_to_dirt.json`, `recipes/transitions/cliff_edge.json`,
`recipes/terrain/mountain.rocky_ridge.json`). Terrain-lane pieces (the hub,
all three terraces) use representative flat colors sampled from those
renders, matching the terrain builder's own native per-cell-color
appearance model -- it has no texture-mapping capability, and this proof
does not add one. Pixel-geometry pieces (the wall, the floor/wall demo,
the pillar) use the actual rendered PNGs as real UV textures via `map_Kd`,
matching the same convention the fold-vs-stretch and cylinder proofs
already established. The pillar reuses the existing diagnostic strip
(`pixel_fold_diagnostic_16x16.png`) rather than a new asset -- its
built-in asymmetric marker is exactly the "find where the seam closes"
landmark the spec asked for.

---

## 5. What was built

- `tools/export_trixel_capability_courtyard.py` -- the composition. No
  new embedding math anywhere: `embed_flat`, `embed_rigid`,
  `embed_hard_90_degree_hinge_fold`, `embed_cylindrical_closed_wrap`,
  `embed_declared_angle_ramp_fold`, and `ramp_geometry_v1.solve_ramp_
  run_and_angle` are all called exactly as their own gates already
  proved them. Two real bugs were caught and fixed while building this
  (see below), both in the composition code, never in a frozen module.
- `trixel/gates/gate_pixel_geometry_capability_courtyard_v1.py` --
  30/30 checks green (selected below). Not a new capability proof --
  every check reuses an already-proven invariant (cell metric, exact
  attachment, adjacency staying clean, isometry) applied across all
  eight-plus pieces.
- `tools/render_trixel_capability_courtyard.py` -- `--clean` and
  `--debug` renders, an angled-overhead "strategy view" chosen because
  the courtyard's ~32x28 footprint cannot be read from a single
  ground-level shot. `--debug` adds a wireframe modifier to every mesh
  plus text labels at each attachment seam, the cylinder seam, and each
  terrace's world Y.

### Bugs caught while composing (fixed in the composition, not the frozen modules)

1. **South terrace placement sign error.** The formula reused north's
   `high_z`-edge-as-attachment convention without accounting for south
   traveling in the *opposite* world direction (+Z, away from the hub,
   versus north's -Z). This made the terrace's own body extend backward
   over the ramp's climb instead of continuing further south. Fixed by
   using the terrace's `low_z` edge as the attachment instead, with the
   shift derivation corrected to match.
2. **Pillar lying on its side.** `embed_cylindrical_closed_wrap`'s own
   local frame puts the circular wrap in (X,Y) and the pillar's height
   along local Z -- so an unrotated placement left it horizontal. Fixed
   with one more `embed_rigid(rotation_axis="x", rotation_degrees=270)`
   call before translating it into position.

Both were caught by the gate and by direct bounding-box inspection before
any render was produced, not by eyeballing a finished picture.

---

## 6. What the gate measured (selected)

```text
[PIXEL_GEOMETRY_CAPABILITY_COURTYARD][HUB_BUILT_ONCE] TRUE  -- got=1344 expected=1344
[PIXEL_GEOMETRY_CAPABILITY_COURTYARD][NORTH_HUB_ATTACHMENT_EXACT] TRUE
[PIXEL_GEOMETRY_CAPABILITY_COURTYARD][NORTH_TERRACE_ATTACHMENT_EXACT] TRUE
[PIXEL_GEOMETRY_CAPABILITY_COURTYARD][SOUTH_HUB_ATTACHMENT_EXACT] TRUE
[PIXEL_GEOMETRY_CAPABILITY_COURTYARD][SOUTH_TERRACE_ATTACHMENT_EXACT] TRUE
[PIXEL_GEOMETRY_CAPABILITY_COURTYARD][EAST_HUB_ATTACHMENT_EXACT] TRUE
[PIXEL_GEOMETRY_CAPABILITY_COURTYARD][EAST_TERRACE_ATTACHMENT_EXACT] TRUE
[PIXEL_GEOMETRY_CAPABILITY_COURTYARD][WEST_WALL_CELL_METRIC_1_0] TRUE
[PIXEL_GEOMETRY_CAPABILITY_COURTYARD][WEST_WALL_EXTENDS_AWAY_FROM_HUB] TRUE
[PIXEL_GEOMETRY_CAPABILITY_COURTYARD][FLOOR_WALL_DEMO_REUSES_SAME_FOOTPRINT_OBJECT] TRUE
[PIXEL_GEOMETRY_CAPABILITY_COURTYARD][FLOOR_AND_WALL_INSTANCES_SHARE_INTRINSIC_ADJACENCY] TRUE
[PIXEL_GEOMETRY_CAPABILITY_COURTYARD][PILLAR_SEAM_COINCIDES_EXACTLY] TRUE  -- seam_gap=0.00e+00
[PIXEL_GEOMETRY_CAPABILITY_COURTYARD][PILLAR_STANDS_UPRIGHT] TRUE  -- y_range=0.0..4.0
[PIXEL_GEOMETRY_CAPABILITY_COURTYARD][EXHIBIT_GENUINELY_TOUCHES] TRUE  -- min_distance=0.00e+00
[PIXEL_GEOMETRY_CAPABILITY_COURTYARD][EXHIBIT_COMPILED_ADJACENCY_STAYS_CLEAN] TRUE
[PIXEL_GEOMETRY_CAPABILITY_COURTYARD][NO_UNDECLARED_PIECE_ADJACENCY] TRUE
[PIXEL_GEOMETRY_CAPABILITY_COURTYARD][ALL_GATES] true
```

All twelve prior pixel_geometry gates and all 37 pre-existing terrain-lane
tests still pass, unmodified, alongside this one. `git status` shows zero
modified tracked files -- every frozen production module is byte-identical
to before this proof was built.

---

## 7. Conclusion (narrow, on purpose)

Eight-plus pieces, each built by a different frozen embedding function,
compose into one coherent scene without any of them needing to change,
without any new production capability, and without any accidental
adjacency between pieces that never declared a relationship to each
other. The two bugs this composition caught were both directional/
orientation mistakes in the *composition* code -- exactly the kind of
error this ladder's discipline (derive placement from declared geometry,
verify with a gate, never eyeball a render as the proof) exists to catch
before it reaches a render.

This proof does **not** establish a walkable, collidable, real-time
Trixel environment -- that remains explicitly out of scope for this
toolchain (see Section 2). It does not include taper. It does not
establish that courtyards at a larger scale, with more than three ramps
or more than one hub, compose the same way without new adjacency
concerns.

---

## 8. Reproduction

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

python3 trixel/gates/gate_pixel_geometry_capability_courtyard_v1.py
python3 tools/export_trixel_capability_courtyard.py

blender --background --python tools/render_trixel_capability_courtyard.py -- --clean
blender --background --python tools/render_trixel_capability_courtyard.py -- --debug
```
