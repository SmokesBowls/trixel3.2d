# TRIXEL DOCTRINE ARCHITECTURE COMPARISON V1

**Purpose:** Forensic comparison of `3.2_trixel_doctrine.md` (the draft
architecture document, self-identified v1.1, status "Draft") against the
Trixel pixel-geometry architecture actually built and proven in
`trixel/pixel_geometry/` (12 frozen gates) plus its immediate neighbors
(`trixel/trixel32d_worldfield_to_worldcell_projection.py`,
`trixel/trixel_recipe_renderer.py`, `recipes/`).

**Classification:** Architecture archaeology / comparison only.

**Explicitly NOT done by this document:** no code was changed, no
doctrine file was edited (`3.2_trixel_doctrine.md` and
`trixel/pixel_geometry/DOCTRINE_SELECTION_RECORD.md` are unmodified), and
the draft is not treated as automatically authoritative anywhere below.
Every claim cites a specific current file, line range, gate, or fixture.

**One fact that changes the framing before anything else:**
`trixel/pixel_geometry/DOCTRINE_SELECTION_RECORD.md` already designates
`3.2_trixel_doctrine.md` as canonical (2026-09-20 decision) and names its
section 5 (Immutability Invariant, Embedding vs. Topology Operation) as
the authority `trixel/pixel_geometry/` builds against.
`embedding_v1.py` lines 1-8 cite that section by number directly. So this
is not two independent systems that happen to have converged — for the
one invariant it covers, the draft was consciously adopted as authority
at the start of this build, and what follows below measures how far
implementation has actually gone in exercising the rest of the document.

---

## Per-concept comparison

Format: `DRAFT CONCEPT / CURRENT EQUIVALENT / STATUS / CURRENT FILES /
PROOFS / DIFFERENCE / ARCHITECTURAL CONSEQUENCE`

### 1. Address/Lattice layer (draft §4, layer 1)

- **Current equivalent:** `trixel/pixel_geometry/addressing_v1.py` —
  `build_footprint(width, height, payload)`, `cell_index`,
  `corner_index`, `cell_addresses`, `corner_addresses`,
  `validate_footprint_structure`.
- **Status:** PRESENT_AND_PROVEN.
- **Files:** `addressing_v1.py:20-76`.
- **Proofs:** every one of the 12 gates depends on this module; nothing
  compiles without it.
- **Difference:** draft §5.1 bundles dimensions, addresses, **adjacency
  stencil**, **orientation convention**, and **cell metric** into one
  CellFootprint object. Current code only stores dimensions/addresses/
  payload here; adjacency lives in a separate module
  (`adjacency_v1.py`), and orientation convention and cell metric are
  never stored fields at all — cell metric is an implicit constant
  (1.0) baked into `embed_flat`'s formula and checked after the fact
  (`edge_lengths()`, `verify_isometry()`), not read from the footprint.
- **Architectural consequence:** identity is correct but distributed
  across files rather than bundled in one object the way draft
  describes. There is no single value you can point to and call "this
  footprint's cell metric" — only a convention every embedding function
  independently honors.

### 2. Artwork Authority layer (draft §4, layer 2)

- **Current equivalent:** three unconnected things — (a)
  `addressing_v1.build_footprint`'s `payload` parameter, described in
  its own docstring as "intrinsic per-cell content (label/color/etc.)"
  (`addressing_v1.py:23-26`); (b) `artwork_mapping_v1.py` (UV
  coordinates only, never color/material); (c) `trixel_recipe_renderer.py`
  + `recipes/terrain/*.json` + `recipes/transitions/*.json`, a
  full declarative texture-generation system that lives entirely
  outside `pixel_geometry` and has no code path back to a cell address.
- **Status:** PARTIAL.
- **Files:** `addressing_v1.py:20-36`, `artwork_mapping_v1.py`,
  `trixel_recipe_renderer.py`, `recipes/`.
- **Proofs:** `gate_pixel_geometry_artwork_fold_v1.py` (13 checks)
  proves UV survives fold-vs-stretch; `gate_tundra_recipe_render_
  contract.py` / `gate_all_recipes_validation_contract.py` prove the
  recipe renderer separately — no gate proves the two are connected,
  because they aren't.
- **Difference:** draft's Artwork Authority assigns "color, palette
  role, material intent, and metadata to addressed cells" as one
  authority. Current reality has no single authority doing this —
  `payload` is an opaque, unschema'd blob; UV assignment carries no
  color/material meaning at all; the recipe system generates real
  artwork but never writes into a footprint's payload.
- **Architectural consequence:** `docs/TRIXEL_CAPABILITY_COURTYARD_V1.md`
  §4 confirms the gap directly in practice — terrain-lane pieces in the
  courtyard use "representative flat colors sampled from" recipe
  renders, i.e. a human/script manually samples a rendered PNG and
  assigns the resulting flat color, rather than any coded Artwork
  Authority driving cell payload.

### 3. Topology Authority layer (draft §4 layer 3, §3.1, §3.3, §11)

- **Current equivalent:** `adjacency_v1.py` (`source_adjacency`,
  `closed_wrap_seam_adjacency`, `compiled_adjacency_matches_source`,
  `compiled_adjacency_matches_closed_wrap`,
  `no_proximity_derived_adjacency`) + `contracts_v1.py`'s
  `TOPOLOGY_PRESERVE_EXACT` / `TOPOLOGY_CLOSED_WRAP_SEAM` +
  `compiler_v1.py`'s `topology_policy` field and `dispositions` dict
  (every value currently `"PRESERVED_1_TO_1"`).
- **Status:** PRESENT_BUT_DIFFERENT for adjacency authority (near-exact
  terminology match to draft §3.3); ABSENT for disposition variety.
- **Files:** `adjacency_v1.py:1-99`, `contracts_v1.py:21-40`,
  `compiler_v1.py:44,61,66,95`.
- **Proofs:** every gate's adjacency check calls
  `compiled_adjacency_matches_source`;
  `gate_pixel_geometry_cylindrical_wrap_v1.py` (17 checks) proves the
  seam case; `gate_pixel_geometry_ramp_close_proximity_v1.py` (11
  checks) is a direct, literal proof of draft §11's "Geometric
  proximity MUST NOT create adjacency."
- **Difference:** draft's Topology Authority also owns occupancy and a
  full PRESERVED/MERGED/SPLIT/CULLED taxonomy. Current code exercises
  exactly two topology policies and one disposition value, ever — grep
  across `trixel/pixel_geometry/` finds zero code paths that produce
  `MERGED`, `SPLIT`, or `CULLED` anywhere.
- **Architectural consequence:** current package can honestly answer
  "was this edge declared or merely proximate" (draft's central
  concern) but cannot yet answer "was this cell merged/split/culled and
  why" — that authority has no code, no contract ID beyond
  `TOPOLOGY_POLICY_CONTRACT` itself, and no gate.

### 4. Geometry Authority layer (draft §4 layer 4, §6.3)

- **Current equivalent:** `embedding_v1.py` (`embed_flat`,
  `embed_rigid`, `embed_hard_90_degree_hinge_fold`,
  `embed_cylindrical_closed_wrap`, `embed_declared_angle_ramp_fold`) +
  `compiler_v1.py` (`compile_footprint`, `compile_closed_wrap_footprint`,
  `edge_lengths`, `positions_by_cell_center`) + `ramp_geometry_v1.py`.
- **Status:** PRESENT_AND_PROVEN — the most thoroughly exercised layer
  in the codebase; 8 of the 12 gates are embedding/compiler proofs.
- **Files:** `embedding_v1.py`, `compiler_v1.py`, `ramp_geometry_v1.py`.
- **Proofs:** gates 1–12 all depend on this layer; the closed-wrap and
  declared-angle-ramp gates specifically prove the embedding functions
  by direct formula comparison, not just visual inspection.
- **Difference:** draft says Geometry Authority produces "positions,
  edges, faces, normals, **and UV mappings**." `compiler_v1.py` never
  computes normals anywhere (confirmed: no `normal` token exists in any
  compiler/embedding file except an unrelated docstring use in
  `terrain_ramp_integration_v1.py:104`), and UVs are computed by a
  wholly separate module (`artwork_mapping_v1.py`) that
  `compile_footprint()` never calls — a caller must invoke both and
  merge the results itself (visible in
  `tools/export_trixel_capability_courtyard.py`'s `ObjWriter`).
- **Architectural consequence:** no single "canonical geometry" object
  bundles position + index + normal + uv together the way draft §8.1's
  `geometry` block implies. This is a concrete, fixable seam, not a
  philosophical one.

### 5. Render Expansion layer (draft §4 layer 5, §6.3, §10, §11)

- **Current equivalent:** `tools/export_trixel_capability_courtyard.py`,
  `tools/build_trixel_capability_courtyard_blend.py`,
  `tools/render_trixel_capability_courtyard.py`, plus
  `terrain_ramp_integration_v1.py`'s `ramp_position_to_world` /
  `translate_built_geometry` (whole-artifact rigid placement into a
  larger scene).
- **Status:** PRESENT_BUT_DIFFERENT.
- **Files:** as above.
- **Proofs:** `gate_pixel_geometry_capability_courtyard_v1.py` (30
  checks) verifies world placement/attachment after export;
  `tools/inspect_trixel_capability_courtyard_blend.py` re-opens the
  saved `.blend` fresh to verify it independently of build-time state.
- **Difference:** `build_trixel_capability_courtyard_blend.py`'s own
  docstring (lines 20-25) states almost exactly draft §10.1's authority
  table: "No Blender deformer is used to fake any Trixel geometry...
  the only Blender-side operations here are import, rename, collection
  placement, and (for the debug overlay only) a non-destructive
  Wireframe modifier." But draft's Render Expansion implies a stage
  that can *duplicate or reorganize* canonical geometry (e.g. vertex
  splitting for hard-normal seams, LOD) under a preservation contract.
  Current render/export code never duplicates or reorganizes vertices
  for any reason — it is strict 1:1 passthrough. There is no code path
  that has ever needed to honor `RENDER_EXPANSION_PRESERVES_CANONICAL_
  OWNERSHIP` because nothing currently exercises the duplication case
  the invariant is meant to guard.
- **Architectural consequence:** the invariant is followed (vacuously)
  by current practice but is PLANNED_OR_IMPLIED, not PRESENT_AND_PROVEN,
  as its own named, independently checked gate — no gate anywhere
  asserts `RENDER_EXPANSION_DOES_NOT_CHANGE_CANONICAL_OWNERSHIP` by
  name the way draft §9.1 lists it.

### 6. CellFootprint / FootprintDefinition / FootprintInstance (draft §5)

- **Current equivalent:** `build_footprint()`'s returned dict is
  literally tagged `"contract": "trixel.footprint_definition.v1"`
  (`addressing_v1.py:32`), matching `FOOTPRINT_DEFINITION_CONTRACT` in
  `contracts_v1.py:8`. There is **no** FootprintInstance object
  anywhere. `contracts_v1.py:9` declares
  `FOOTPRINT_INSTANCE_CONTRACT = "trixel.footprint_instance.v1"`, but a
  repo-wide grep confirms no function anywhere ever constructs or
  returns a dict carrying that contract string — the name is frozen but
  unused.
- **Status:** PRESENT_BUT_DIFFERENT for FootprintDefinition; ABSENT for
  FootprintInstance as a first-class object.
- **Files:** `addressing_v1.py:32`, `contracts_v1.py:8-9`.
- **Proofs:** none — this is a structural absence, not a tested one.
- **Difference:** draft §5.4's instance specification (footprint_
  definition + footprint_instance + local_dimensions + cell_metric +
  adjacency + embedding + topology_policy, bundled as one addressable,
  inspectable JSON record) has no analogue. Every current "instance" —
  each of the 13 courtyard pieces, every gate's specimen — exists only
  as an ad hoc Python call site (e.g. `embed_declared_angle_ramp_fold
  (footprint, hinge_corner_x=8, angle_degrees=30.0)`), never as a
  durable record.
- **Architectural consequence:** you cannot currently query "list every
  footprint instance in this scene and its topology policy" — you have
  to read the composition script's source line by line.

### 7. Immutability Invariant (draft §5.2, §5.3)

- **Current equivalent:** the intrinsic/extrinsic split between
  `addressing_v1.py` and `embedding_v1.py`.
- **Status:** PRESENT_AND_PROVEN — the strongest single point of
  convergence in the codebase.
- **Files:** `embedding_v1.py:1-8` (direct citation: "per the doctrine's
  Immutability Invariant (3.2_trixel_doctrine.md section 5.2)").
- **Proofs:** every embedding gate re-derives the same cell/corner
  addresses across differently embedded geometry and checks payload/UV
  survive unchanged (e.g. `gate_pixel_geometry_artwork_fold_v1.py`'s
  UV-identity checks via `artwork_mapping_v1.uvs_are_identical`).
- **Difference:** none in substance. Process discipline goes further
  than draft literally requires — once a gate/embedding is frozen it is
  never edited again, re-verified via fresh git clone repeatedly. Draft
  only requires intrinsic cell structure to survive embedding, not
  literal source-file immutability; the current project added the
  latter as a process rule on top.
- **Architectural consequence:** none negative — flagged in section C
  below as a candidate doctrine addition.

### 8. Source adjacency / compiled adjacency / geometric proximity (draft §3.3, §11)

- **Current equivalent:** `adjacency_v1.source_adjacency`,
  `compiler_v1`'s `compiled_adjacency` output field,
  `adjacency_v1.no_proximity_derived_adjacency`.
- **Status:** PRESENT_AND_PROVEN.
- **Files:** `adjacency_v1.py:1-99`.
- **Proofs:** `gate_pixel_geometry_ramp_close_proximity_v1.py` (11
  checks) is a direct toxic proof of exactly draft §11's "Geometric
  proximity MUST NOT create adjacency" sentence — it deliberately
  places two unrelated pieces in exact geometric contact and proves
  `no_proximity_derived_adjacency` flags the closeness while
  `compiled_adjacency` stays clean regardless.
- **Difference:** terminology is close to verbatim (draft's three-row
  table in §3.3 vs. current's three function names) — this is the
  single cleanest concept match in the whole document.
- **Architectural consequence:** none; this is a load-bearing, correctly
  implemented invariant.

### 9. Seam management / cell vs. corner addresses (draft §7)

- **Current equivalent:** `addressing_v1.cell_index` vs. `corner_index`
  for the address distinction; `adjacency_v1.closed_wrap_seam_adjacency`
  (lines 40-59) for seam declaration.
- **Status:** PRESENT_AND_PROVEN for the cell/corner distinction;
  PRESENT_BUT_DIFFERENT for seam declaration (only one hardcoded case
  exists, not a general primitive).
- **Files:** `addressing_v1.py:39-49`, `adjacency_v1.py:40-59`,
  `embedding_v1.py:124-131`.
- **Proofs:** `gate_pixel_geometry_cylindrical_wrap_v1.py` (17 checks).
- **Difference:** `embedding_v1.py:124-131`'s docstring states almost
  exactly draft §7.2's note — corner x=0 and corner x=width "remain
  distinct corner ADDRESSES... whose positions merely coincide," never
  promoted to shared identity by coincidence alone. But
  `closed_wrap_seam_adjacency` only ever declares the first-column/
  last-column seam for a cylinder; there is no general "declare an
  arbitrary seam between any two non-adjacent cells" API draft §7.1's
  wording implies would generalize (e.g. for a tree-branch fork).
- **Architectural consequence:** the concept is proven correct where it
  is exercised, but the implementation is a special case, not a
  reusable primitive.

### 10. Compiler Output Specification (draft §8)

- **Current equivalent:** `compile_footprint()`'s return dict:
  `contract`, `embedding_id`, `topology_policy`, `footprint_width`,
  `footprint_height`, `compiled_adjacency`, `dispositions`, `positions`,
  `indices`, `primitive_provenance`.
- **Status:** PRESENT_BUT_DIFFERENT.
- **Files:** `compiler_v1.py:63-74`.
- **Proofs:** every gate consumes this exact shape.
- **Difference:** draft §8.1 wants a `source{width,height,pixel_world_
  size}` sub-object (current flattens to `footprint_width`/
  `footprint_height`, no `pixel_world_size` field anywhere), a
  `geometry{positions,indices,uvs}` sub-object (current flattens
  `positions`/`indices` to top level and omits `uvs` entirely — UVs
  live in a separate call), and `pixel_dispositions` as a **list** of
  rich per-pixel records (draft §8.2:
  `source_pixel`/`topology_disposition`/`visibility_state`/
  `structural_roles`/`target_region`/`output_primitives`/`merged_with`/
  `rule`). Current `dispositions` is a **dict** keyed by cell address
  whose only ever value is the string `"PRESERVED_1_TO_1"` — none of
  draft's richer per-record fields exist. Current also adds
  `compiled_adjacency` directly into the output, which draft's §8.1
  shape does not list at all.
- **Architectural consequence:** current output would fail a strict
  schema check against draft §8.1, but every semantic question the
  draft cares about is answerable for the one disposition case that
  exists (PRESERVED). It cannot answer merge/split provenance questions
  because nothing currently produces them. Adding `compiled_adjacency`
  to the output was independently useful and is arguably an improvement
  over draft's spec (see section C).

### 11. Acceptance Gates and connectivity verification (draft §9)

- **Current equivalent:** 12 capability-named gate files under
  `trixel/gates/gate_pixel_geometry_*.py`, each containing many
  individual named checks (`report(...)` calls), rather than one
  reusable set of invariant-named gates.
- **Status:** PARTIAL.
- **Files:** `trixel/gates/gate_pixel_geometry_*.py` (12 files).
- **Proofs / verified sub-findings:**
  - `PRESERVED_PIXEL_METRIC_WITHIN_CONTRACT` — PRESENT_AND_PROVEN,
    repeated per-gate as `*_CELL_METRIC_1_0` / `verify_isometry` checks.
  - `TOPOLOGY_POLICY_IS_DECLARED` — PRESENT_AND_PROVEN structurally
    (field is never optional) but never independently gate-asserted by
    that name.
  - `COMPILATION_IS_DETERMINISTIC` — **PRESENT_AND_PROVEN**, verified
    directly: `gate_pixel_geometry_terrain_ramp_integration_v1.py:151-159`
    and five sibling gates rebuild the scene a second time and diff the
    JSON-serialized output (`COMPOSED_SCENE_IS_DETERMINISTIC` check).
    This is real, independent verification of exactly draft §9.1's
    invariant, just under a different name.
  - `EVERY_CANONICAL_PRIMITIVE_HAS_PROVENANCE` — true by construction
    (the same loop in `compiler_v1.py:46-61` that emits triangles always
    appends a provenance record) but never independently checked by a
    dedicated assertion.
  - `NO_UNDECLARED_PIXEL_MERGE/SPLIT/CULL` — vacuously true; nothing
    exists that could violate them.
  - The lattice-connectivity traversal mechanism (draft §9.2's
    START/TRAVERSE/COLLECT/COMPARE) — **ABSENT**. A repo-wide grep for
    traversal/reachability/BFS/flood-fill terms in
    `trixel/pixel_geometry/` returns no matches. Every current adjacency
    check is exact dict-equality (`compiled_adjacency == source_
    adjacency(footprint)`), which is a strictly narrower check than a
    graph traversal — it would catch a byte-different adjacency dict but
    not, in principle, a corrupted graph that happened to still satisfy
    equality against a wrongly-constructed expectation.
- **Architectural consequence:** if merge/split/cull are ever
  implemented, there is currently no reusable connectivity verifier to
  extend — draft §9.2's mechanism would need to be built from scratch,
  since none of the 12 gates walk the adjacency graph for reachability.

### 12. Provenance invariant (draft §6.5, §8.3)

- Covered under #4 and #10 above. **Status: PRESENT_BUT_DIFFERENT** —
  coarser-grained than draft asks (one `topology_policy` per whole
  compilation, not per-primitive `rule` attribution), but since only one
  policy is ever active per compilation today, the coarser grain has not
  yet caused an actual information loss — it would only start mattering
  once a single compiled output could mix disposition types.

### 13. Prohibited Operations (draft §11), line by line

- "Geometry MUST NOT invent cell identity." — **PRESENT_AND_PROVEN**;
  every triangle in `compiler_v1.py` originates from
  `cell_addresses(footprint)`, never a synthesized address.
- "Geometric proximity MUST NOT create adjacency." —
  **PRESENT_AND_PROVEN**; see #3/#8 above.
- "A mesh weld MUST NOT merge ownership." — **PRESENT_AND_PROVEN** for
  the one case that could tempt it (cylindrical seam coincidence);
  `embedding_v1.py:124-131` reasons about this explicitly.
- "A mesh split MUST NOT split ownership." — **PLANNED_OR_IMPLIED**; no
  split code path exists, so nothing could currently violate this, but
  there is also no toxic gate proving it the way the proximity case has
  one.
- "A UV seam MUST NOT break logical adjacency." — **PRESENT_AND_PROVEN**
  by module isolation: `artwork_mapping_v1.py` imports only from
  `addressing_v1.py`; `adjacency_v1.py` also imports only from
  `addressing_v1.py`. Neither can affect the other even accidentally.
- "A material boundary MUST NOT redefine topology." —
  **PRESENT_AND_PROVEN** by the same isolation; no material/texture code
  exists in `adjacency_v1.py` or `compiler_v1.py`.
- "A renderer MAY duplicate... but MUST NOT create/destroy/merge/split
  visual ownership." — **PLANNED_OR_IMPLIED**; see #5 above.
- "A footprint embedding MUST preserve intrinsic cell structure." —
  **PRESENT_AND_PROVEN**, stated verbatim in intent by
  `embedding_v1.py`'s own module docstring, citing doctrine §5.2 by
  number.
- "Any operation that cannot preserve intrinsic cell structure MUST
  invoke an explicit topology policy." — **PRESENT_AND_PROVEN** for the
  one case that exercises it: `contracts_v1.py:32-40`'s comment on
  `TOPOLOGY_CLOSED_WRAP_SEAM` independently re-derives this exact
  reasoning — "calling it preserve_exact would be dishonest, since an
  edge really was added."

### 14. Blender's Role (draft §10)

- Covered under #5. **Status: PRESENT_AND_PROVEN in spirit** —
  `build_trixel_capability_courtyard_blend.py`'s docstring states the
  same authority ordering as draft §10.1's table without having been
  written with that table in front of it (Blender never computes
  geometry; Trixel functions are construction authority; the one
  Blender-native geometric operation used anywhere is explicitly
  non-destructive and debug-only).

### 15. The Flood Fill Proof / connectivity (draft §12, §9.2)

- **Status: ABSENT.** No flood-fill, no occupancy-based validation, no
  BFS/reachability code exists anywhere in `trixel/pixel_geometry/`.
  Confirmed by grep (see #11).

### 16. Intended use cases (draft §15.2) vs. what's actually been proven

- Draft names: tree/flora generation, terrain patch compilation,
  character construction, building/architecture generation, cave/
  environment construction.
- Current proofs cover terrain-patch-adjacent shapes only: ramps, a
  shared hub, a folded retaining wall, a closed cylindrical pillar. No
  taper exists — and the codebase says so about itself, unprompted:
  `contracts_v1.py:15-20` ("Taper/branch/character/terrain integration
  are still out of scope") and
  `docs/TRIXEL_CAPABILITY_COURTYARD_V1.md` §1 ("Taper is deliberately
  absent — it crosses into topology mutation, a capability this ladder
  has not yet earned."). Tree/flora and character construction both
  depend on taper (draft's own tapered-instance example, §5.4, is
  explicitly a trunk).
- **Status: PLANNED_OR_IMPLIED**, and unusually self-aware about it —
  the gap is named in the current code's own comments, not just
  inferred from absence.

---

## Answers to the 13 questions

1. **Fundamental identity-bearing object?** The dict returned by
   `build_footprint()` (contract `trixel.footprint_definition.v1`) is
   the closest match — a FootprintDefinition. There is no
   FootprintInstance wrapper (see #6); the real unit of identity in
   practice is the `(footprint, cell_address)` pair, since payload
   travels with cell address through every embedding but the footprint
   itself is never wrapped in a named, placed instance record.

2. **CellFootprint equivalent?** `build_footprint()`'s dict
   (`width`, `height`, `payload`, `contract`). Missing relative to
   draft §5.1: no stored adjacency stencil (computed on demand instead),
   no stored orientation convention, no stored cell metric (implicit
   constant, verified post hoc rather than declared).

3. **Intrinsic vs. embedding distinction?** Yes, cleanly present and
   the strongest match in the document: `addressing_v1.py` (intrinsic)
   vs. `embedding_v1.py` (extrinsic), with `embedding_v1.py` citing
   doctrine §5.2 by section number in its own module docstring.

4. **Where does topology authority live** for adjacency/seams (proven,
   `adjacency_v1.py` + `contracts_v1.py`'s `TOPOLOGY_*` constants) vs.
   merge/split/cull/transitions (**no home at all** — no file, function,
   or contract ID exists for any of these four)?

5. **Can geometry create relationships merely from touching/welding/
   overlap?** No — proven negatively three ways: the closed-wrap
   docstring reasoning (`embedding_v1.py:124-131`), the dedicated toxic
   gate (`gate_pixel_geometry_ramp_close_proximity_v1.py`), and the fact
   that `compiled_adjacency` in `compiler_v1.py` is only ever set from
   `source_adjacency()` or an explicitly supplied `seam_adjacency`, never
   from `positions`.

6. **Does the architecture distinguish logical cell identity / logical
   adjacency / canonical geometric samples / render vertices?** Three of
   four, cleanly: cell identity (`cell_index`/`cell_addresses`), logical
   adjacency (`adjacency_v1.py`), canonical geometric samples
   (`corner_index`/`positions`). "Render vertices" as a concept distinct
   from canonical samples does not exist — OBJ export writes compiled
   positions 1:1, never splitting or duplicating for render-specific
   reasons.

7. **Where is provenance recorded, and can we answer "why does this
   primitive exist / which source cell caused it / which rule
   authorized it"?** `compiler_v1.py`'s `primitive_provenance` list
   answers "which cell" and "why" for every case that currently exists.
   "Which rule" is answerable only at whole-compilation granularity via
   the separate `topology_policy` field, not per-primitive as draft
   §8.2 wants — not yet a real information loss, since only one policy
   is ever active per compiled output today.

8. **How does the WorldField→world_cell bridge relate to the draft?**
   `trixel/trixel32d_worldfield_to_worldcell_projection.py`'s
   `project_worldfield_cell_to_worldcell()` (field_x→world_cell_x,
   field_y→world_cell_z, elevation→world_cell_y) has **zero
   dependency** on any `pixel_geometry` file in either direction, and
   the draft never mentions WorldField or world_cell anywhere in its
   512 lines. This is not a divergence from the draft — it's a
   coordinate-space concept entirely outside the draft's scope, most
   likely because the draft is scoped to single-footprint compilation,
   not the larger terrain/WorldField authority.

9. **Where do the recipe systems belong?** `trixel_recipe_renderer.py`
   + `recipes/*.json` map in spirit to draft's Artwork Authority (layer
   2) but are structurally disconnected — they operate on raw pixel
   grids, not `pixel_geometry` cell addresses, and
   `docs/TRIXEL_CAPABILITY_COURTYARD_V1.md` §4 confirms the connection
   between the two is currently manual (a human/script samples a
   rendered PNG and assigns the resulting color), not coded.

10. **Where do the 12 pixel-geometry proofs fit?** Heavily layers 1
    (Address/Lattice) and 4 (Geometry Authority), touching layer 3
    (Topology Authority) for the cylinder/proximity proofs and layer 5
    (Render Expansion) for terrain-integration/courtyard world
    placement. Layer 2 (Artwork Authority) is touched by exactly one
    gate (`gate_pixel_geometry_artwork_fold_v1.py`), and only to prove
    UV survives folding — not that artwork assigns meaning to cells.

11. **Which draft parts are stronger than current implementation?**
    (a) the full disposition taxonomy plus visibility state and
    structural roles; (b) the lattice-connectivity traversal mechanism
    (§9.2), which is strictly stronger than current's exact-equality
    adjacency checks; (c) per-primitive rule attribution (§8.2); (d)
    FootprintInstance as a durable, serializable object (§5.4); (e)
    adjacency stencil and cell metric as stored fields on the footprint
    itself rather than side-channel constants.

12. **Which current parts are more advanced and should update doctrine
    rather than being forced backward?** (a) the toxic/adversarial proof
    pattern (deliberately construct and prove rejection of a wrong
    case) — methodologically stronger than draft §9's assertion-only
    gate model; (b) the freeze + fresh-clone re-verification discipline,
    which empirically re-proves `COMPILATION_IS_DETERMINISTIC` and
    non-regression on every commit, something draft's static invariant
    list names but never operationalizes as a required practice; (c)
    declared-angle ramp solving (`ramp_geometry_v1.solve_ramp_run_and_
    angle` + `embed_declared_angle_ramp_fold`) — a concrete embedding
    category beyond anything draft's own examples (`cylinder_wrap.v1`,
    `tapered_trunk.v1`) name; (d) `compiled_adjacency` embedded directly
    in the compiled output, making adjacency independently inspectable
    without recomputation — an improvement over draft §8.1's required
    shape, worth folding back into it.

13. **What in the draft is now demonstrably wrong?** Nothing is
    contradicted by current evidence — every divergence found is
    current code implementing a subset of the draft, never something
    that falsifies a draft claim. The closest thing to friction: draft
    §5.1 lists cell metric as a per-footprint field (implying it could
    vary between footprints), but every current embedding hardcodes
    `cell_metric = 1.0` directly into `embed_flat`'s formula rather than
    reading it from the footprint object. This is a latent
    inflexibility, not a falsification — nothing has yet needed a
    non-1.0 metric, so it hasn't been tested either way.

---

## A. Current architecture already converged with draft

1. Intrinsic (address) vs. extrinsic (embedding) separation —
   `addressing_v1.py` vs. `embedding_v1.py`, with a direct section-number
   citation to the draft in `embedding_v1.py`'s own docstring.
2. The source-adjacency / compiled-adjacency / geometric-proximity
   three-way distinction (draft §3.3) — near-verbatim in
   `adjacency_v1.py`'s function names, with the central prohibition
   directly proven by a dedicated toxic gate.
3. Visual-cell vs. corner-sample address distinction (draft §7.2) —
   `cell_index` vs. `corner_index`, and the closed-wrap embedding's own
   docstring reasoning about coincident-position-without-merged-identity
   matches draft's corner-sample note almost exactly.
4. "Any operation that cannot preserve intrinsic cell structure MUST
   invoke an explicit topology policy" (draft §11) — the closed-wrap
   case does exactly this, with an independently-written code comment
   re-deriving the same justification the draft gives.
5. Blender as evidence/candidate artifact, never authority (draft §10)
   — stated almost word for word in `build_trixel_capability_courtyard_
   blend.py`'s docstring, with the one Blender-native geometric
   operation used anywhere restricted to a non-destructive debug-only
   overlay.
6. Topology policy is always explicitly declared, never optional
   (draft §9.1's `TOPOLOGY_POLICY_IS_DECLARED`).
7. `COMPILATION_IS_DETERMINISTIC` (draft §9.1) is independently proven,
   not just assumed — six gates rebuild their scene and diff JSON
   output under the name `COMPOSED_SCENE_IS_DETERMINISTIC`.
8. `DOCTRINE_SELECTION_RECORD.md` already formally designates this exact
   draft as canonical for the Immutability Invariant — this convergence
   point was consciously adopted, not independently rediscovered.

## B. Draft capabilities not yet present in current Trixel

1. Disposition taxonomy beyond `PRESERVED_1_TO_1` — no MERGED/SPLIT/
   CULLED code path, contract ID, or gate exists anywhere.
2. Visibility state and structural roles (draft §3.1) — no VISIBLE/
   OCCLUDED or CAP_CONTRIBUTOR/TRANSITION_CONTRIBUTOR concept anywhere.
3. FootprintInstance as a first-class, serializable object distinct from
   FootprintDefinition (draft §5.4) — `FOOTPRINT_INSTANCE_CONTRACT` is
   declared but never constructed by any function.
4. Lattice-connectivity traversal verification (draft §9.2) — no BFS/
   reachability code exists; current checks are exact adjacency-dict
   equality only, which is strictly weaker.
5. Per-primitive `rule`/`merged_with`/`target_region` provenance fields
   (draft §8.2) — current provenance is coarser (cell_address/
   primitive_start/primitive_count/payload only).
6. General-purpose seam declaration (draft §7.1) — only the one
   hardcoded closed-cylinder case exists; no API to declare an arbitrary
   seam between two non-adjacent cells for other shapes.
7. Taper / discrete circumference reduction (draft §5.4's tapered
   trunk example) — explicitly and self-consciously out of scope, named
   as such in the current code's own comments.
8. Artwork Authority as one unified layer (draft §4 layer 2) — currently
   split across an opaque payload blob, a UV-only module, and an
   unconnected recipe/texture system with no coded relationship between
   them.

## C. Current Trixel evolutions that should modify or supersede the draft

1. The toxic/adversarial proof pattern (deliberately construct and prove
   *rejection* of a wrong case, not just acceptance of a right one) —
   methodologically stronger than draft §9's assertion-only gate model.
   Worth writing into doctrine as a required pattern for every future
   disposition/topology gate, especially once merge/split/cull are
   eventually built.
2. The freeze + fresh-clone re-verification discipline — operationalizes
   `COMPILATION_IS_DETERMINISTIC` and non-regression as a required,
   repeatable process on every commit, which draft's static invariant
   list names but never turns into a practice.
3. Declared-angle ramp solving (`ramp_geometry_v1.solve_ramp_run_and_
   angle`, `embed_declared_angle_ramp_fold`) — a concrete, worked
   embedding category (arbitrary rigid-fold angles solved from a
   required rise/run) beyond anything draft's own embedding examples
   name. Worth formalizing into doctrine as a named embedding category
   alongside `cylinder_wrap.v1` and `tapered_trunk.v1`.
4. `compiled_adjacency` embedded directly in the compiled output (not
   part of draft §8.1's required shape at all) — makes adjacency
   independently inspectable from the compiled artifact alone, without
   recomputing `source_adjacency()`. A genuine improvement worth folding
   back into §8.1.
5. World-placement / terrain-attachment functions
   (`terrain_ramp_integration_v1.py`) — an entire capability class
   (attaching a pixel_geometry artifact edge-exact to an independently
   built terrain surface from a different authority, with geometric
   verification, not just duplication) that draft's five-layer model
   has no clean home for. It is not quite Render Expansion (which draft
   scopes to duplication/reorganization, not cross-authority
   attachment verification). Doctrine's layer model may need a sixth
   concept — something like "Composition/Attachment Authority" — to
   describe this cleanly rather than stretching Render Expansion to
   cover it.

---

**Net read:** current `trixel/pixel_geometry/` has independently arrived
at, or consciously adopted, the draft's core discipline — intrinsic/
extrinsic separation, the three-way adjacency distinction, and the
prohibition on proximity-derived topology are all proven, not just
philosophically endorsed. What the draft has that current code does not
is almost entirely in one place: the richer disposition/provenance
taxonomy (MERGED/SPLIT/CULLED, visibility state, structural roles,
per-primitive rule attribution) and the connectivity-traversal
verification mechanism that would be needed to safely implement it. None
of that has been contradicted by anything built so far — it has simply
not been needed yet, because no trial in the 12-gate ladder has required
a topology change more complex than "preserve exactly" or "add one
declared seam."
