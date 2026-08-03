# TRIXEL PERCEPTUAL PRESENTATION DOCTRINE UPDATE V1

**Update ID:** `TRIXEL_PERCEPTUAL_PRESENTATION_DOCTRINE_UPDATE_V1`  
**Applies To:** Trixel 3.2d doctrine version 1.1  
**Classification:** Doctrine Addendum / Architectural Authority Lock  
**Status:** Accepted formulation for future implementation and proof work  
**Date:** 2026-08-03

---

## 1. Purpose

This update extends the Trixel doctrine by defining the authority, limits, and proof obligations of the perceptual presentation lane.

It does not replace the existing doctrine. It does not change the authority of the address/lattice, artwork, topology, geometry, or render-expansion layers.

The existing doctrine establishes what a trixel is, what it owns, how its topology is authorized, and how its geometry is embodied.

This update establishes how an already accepted trixel may be observed and presented from a particular camera at a particular frame.

> **Presentation may change how a trixel is seen. It may not change what the trixel is.**

---

## 2. Authority Separation

Trixel recognizes two separate authority lanes.

### 2.1 Structural Authority

```text
WorldField facts
    ↓
projection contract
    ↓
structural request
    ↓
topology and footprint policy
    ↓
canonical trixel geometry
    ↓
stable identity, ownership, adjacency, provenance
```

Structural authority determines:

- which trixels exist;
- which exact addresses they possess;
- which source cells or structural rules authorize them;
- which geometry they own;
- which topology and adjacency relationships are valid;
- which material and semantic classes they carry;
- which provenance records explain their existence.

Structural authority is persistent and camera-independent.

### 2.2 Presentation Authority

```text
canonical trixel geometry
    ↓
camera visibility and regional sampling
    ↓
dominant or boundary identity resolution
    ↓
semantic palette restriction
    ↓
perceptual color comparison
    ↓
identity-aware temporal stabilization
    ↓
deterministic triangular reconstruction
    ↓
Godot display
```

Presentation authority determines:

- which accepted trixels are visible from the current camera;
- how a screen observation region samples those trixels;
- which accepted structural identity dominates or forms a boundary;
- which palette entries are legal for that identity;
- which legal color is perceptually closest;
- whether the previous presentation decision may be retained;
- which stable triangular display orientation is used;
- how the result is displayed by Godot.

Presentation authority is derived, camera-dependent, and non-structural.

The first lane answers what exists.

The second lane answers how what exists is seen.

No presentation process may regain structural authority by interpreting the rendered image.

---

## 3. Screen Cells Are Observations, Not Owners

A presentation screen cell is not a structural trixel.

A screen cell is a temporary observation location within a camera-dependent sampling grid.

A structural trixel remains the owner of its identity, geometry, material, semantics, topology, and provenance regardless of where or whether it appears on the screen.

A presentation record must preserve both values explicitly:

```json
{
  "screen_cell": [43, 27],
  "dominant_trixel_id": "surface_001.cell_2_1.face_top.03"
}
```

The screen coordinate identifies where the observation occurred.

The structural identity identifies what accepted trixel the observation represents.

The following equivalence is prohibited:

```text
screen cell identity == structural trixel identity
```

The required relationship is:

```text
screen cell
    observes
structural trixel
```

A screen cell may observe different structural trixels over time. A structural trixel may occupy multiple screen cells in one frame. A screen cell may contain coverage from more than one structural trixel and therefore require an explicit dominant or boundary classification.

None of those presentation relationships may alter structural ownership.

---

## 4. Presentation Contracts

The perceptual presentation lane is divided into four conceptual contracts.

These names establish doctrine and future contract boundaries. This update does not claim that corresponding schema or runtime files already exist.

### 4.1 `trixel.presentation_profile.v1`

Governs deliberate presentation policy, including:

- presentation resolution;
- sampling and aggregation policy;
- edge classification policy;
- perceptual color space;
- palette reference;
- temporal-history policy;
- hysteresis thresholds;
- orientation policy;
- reconstruction grammar;
- upscale policy;
- debug requirements.

It must not define structural identity, ownership, topology, adjacency, or provenance.

### 4.2 `trixel.palette.v1`

Governs permitted output colors and semantic eligibility.

A palette entry may contain:

- display sRGB value;
- linear RGB value;
- OKLab coordinates;
- optional OKLCH authoring values;
- semantic tags;
- material compatibility;
- illumination class;
- lightness band;
- scene-profile eligibility;
- stable palette index.

A palette entry is not legal merely because it is numerically close to the sampled color.

### 4.3 `trixel.presentation_frame.v1`

Records the derived presentation decision for one camera frame.

A frame record should identify, at minimum:

- source structural surface identity or hash;
- camera packet identity or hash;
- presentation profile identity or hash;
- frame index;
- screen cell;
- dominant or boundary structural trixel identity;
- sampled representative color;
- legal palette subset or subset identity;
- selected palette index;
- previous palette index when history was considered;
- hysteresis decision;
- edge class;
- reconstruction orientation;
- orientation source;
- coverage or confidence.

A frame record is derived evidence. It is not a new structural surface artifact.

### 4.4 `trixel.presentation_proof.v1`

Proves the behavior of the presentation lane over a deterministic run.

It should bind:

- accepted structural surface hash;
- palette hash;
- presentation profile hash;
- camera-path hash;
- frame count;
- raw palette-switch count;
- stabilized palette-switch count;
- same-identity unstable switch count;
- identity-change count;
- invalid history reuse count;
- orientation-switch count;
- deterministic replay result;
- final status.

The proof must not report visual approval alone. It must measure whether the declared stability and identity-preservation claims are true.

---

## 5. Semantic Palette Authorization

Palette restriction is an authorization rule, not merely a performance optimization.

A candidate palette entry must satisfy all applicable conditions:

```text
perceptually close
AND semantically legal
AND materially legal
AND scene-profile legal
AND illumination-class legal
```

Conceptually:

```text
legal_candidates =
    palette entries
        filtered by presentation profile
        filtered by material class
        filtered by semantic class
        filtered by illumination class

selected_entry =
    minimum perceptual distance among legal_candidates
```

The renderer must not search the entire global palette when structural meaning limits the legal set.

A terrain-grass trixel must not become skin-colored merely because a skin palette entry is numerically or perceptually close.

Semantic restriction protects world meaning. Perceptual comparison protects visual coherence. The color decision is governed by both.

---

## 6. Perceptual Color Law

Palette matching must not be performed directly against gamma-encoded sRGB unless the input is explicitly declared to be in the intended comparison space.

The preferred conceptual path is:

```text
sRGB, when applicable
    ↓ gamma removal
linear RGB
    ↓ perceptual transform
OKLab
    ↓ constrained distance comparison
legal palette entry
    ↓ display conversion
RGB output
```

OKLab is preferred for internal distance calculations. OKLCH may be exposed for palette authorship. RGB remains the final display representation.

Applying gamma removal twice is prohibited. The presentation implementation must know which color representation each input buffer contains.

---

## 7. Regional Sampling Law

A presentation cell should represent a source region rather than blindly inherit one arbitrary center sample whenever regional evidence is required to preserve stability or thin geometry.

Regional sampling may consider:

- color samples;
- structural trixel IDs;
- coverage percentage;
- depth;
- normals;
- material class;
- semantic class;
- motion information;
- emissive contribution;
- transparency state, when explicitly supported.

The output may include:

- representative linear color;
- dominant structural trixel ID;
- boundary identity set;
- depth representative;
- normal representative;
- edge class;
- coverage;
- confidence.

Regional aggregation must not merge structural identities. It may only determine which accepted identities contribute to one screen observation and how that observation should be classified.

---

## 8. Identity Resolution Law

For every presentation cell in every frame:

```text
dominant_trixel_id must reference a structural trixel
present in the accepted source surface.
```

No presentation operation may:

- create a structural identity;
- rename a structural identity;
- merge structural identities;
- split a structural identity;
- reassign structural ownership;
- infer structural adjacency from screen proximity;
- infer structural topology from color boundaries;
- promote a screen cell into a world owner.

A boundary presentation cell may reference multiple accepted structural identities, but every referenced identity must already exist in the accepted surface.

The boundary classification describes the observation. It does not create a structural relationship.

---

## 9. Temporal History Law

Presentation history is subordinate to structural identity.

For the first proof, previous-frame history may be reused only when:

```text
current dominant_trixel_id == previous dominant_trixel_id
```

If the identity differs, prior palette history must be rejected.

This prevents a newly revealed trixel from inheriting the displayed color of a different trixel that previously occupied the same screen cell.

A future reprojection policy may permit history reuse across different screen coordinates only when it proves that both observations refer to the same structural trixel.

Until such a policy is independently specified and proven, strict identity equality remains the authority rule.

### 9.1 Hysteresis

A palette candidate must not replace the previous accepted palette entry merely because it is fractionally closer.

The previous entry should be retained unless the new candidate is better by a declared threshold.

```text
switch only when:

candidate_distance + switch_threshold < previous_distance
```

The threshold may vary by declared presentation class, but it must not be hidden or inferred from uncontrolled frame state.

Temporal stabilization may suppress unstable presentation changes.

It may not suppress a structural identity change.

---

## 10. Triangular Reconstruction Authority

Triangular reconstruction determines the visible Trixel display grammar.

Orientation evidence must be evaluated in this authority order:

1. canonical structural orientation;
2. topology or slope orientation;
3. persistent material-boundary orientation;
4. stable depth or normal edge orientation;
5. deterministic structural-identity-derived fallback.

Stages 3 and 4 may influence presentation only when they do not contradict stages 1 and 2.

Camera-derived evidence is subordinate to structural evidence.

The deterministic fallback must derive from stable structural identity rather than screen position:

```text
orientation =
    stable_hash(structural_trixel_id) mod orientation_count
```

The following fallback is prohibited:

```text
orientation = hash(screen_cell) mod orientation_count
```

A screen-derived fallback would cause orientation to migrate as an object moved through the viewport. A structural-identity fallback keeps orientation attached to the accepted surface.

---

## 11. Relationship to Authored Recipes

Existing deterministic recipes remain artwork-authority inputs.

```text
deterministic authored recipe
    ↓
approved source artwork
    ↓
palette extraction or deliberate palette authorship
    ↓
validated trixel.palette.v1
```

A recipe may provide evidence for desired colors, transitions, material character, and scene appearance.

A recipe does not become responsible for:

- camera sampling;
- screen-cell identity resolution;
- temporal history;
- hysteresis;
- edge classification;
- triangular reconstruction;
- presentation-frame evidence;
- replay proof.

Artwork authority and presentation authority remain distinct.

---

## 12. CPU, GPU, and Godot Boundaries

The CPU side should prepare stable, semantic, and infrequently changing information:

- accepted structural surface import;
- hash and contract validation;
- structural ID registry;
- material and semantic mappings;
- palette loading;
- legal palette-range preparation;
- compact GPU lookup resources;
- history resource lifecycle;
- proof and receipt metadata.

The GPU side may perform per-frame presentation calculations:

- world rendering;
- regional sampling;
- representative color calculation;
- dominant identity selection;
- perceptual conversion;
- legal palette comparison;
- hysteresis;
- edge classification;
- triangular reconstruction;
- final display expansion.

Shaders must not parse EngAIn manifests or JSON contracts.

Godot is the presentation consumer. Godot may display accepted and derived results, but it may not reinterpret the screen image to create new trixel identity, ownership, adjacency, or topology.

---

## 13. Required Debug Evidence

A visually appealing result is not sufficient proof.

The first implementation must be able to expose the reason for each important presentation decision.

Independent debug views should be able to show:

- structural trixel ID;
- dominant identity per presentation cell;
- boundary identities, when applicable;
- raw sampled color;
- representative linear color;
- perceptual candidate value;
- legal palette subset;
- selected palette index;
- previous palette index;
- history eligibility;
- hysteresis decision;
- edge classification;
- reconstruction orientation;
- orientation authority source;
- coverage;
- confidence.

Debug presentation is evidence only. It does not become structural authority.

---

## 14. Minimum Proof Claim

The first perceptual-presentation proof must remain narrow.

> **For a fixed accepted surface, fixed palette, fixed presentation profile, and deterministic camera path, identity-aware perceptual presentation reduces unstable same-identity color switching without changing structural ownership.**

The proof compares two runs over identical source data.

### Run A

```text
perceptual palette quantization
without identity-aware temporal stabilization
```

### Run B

```text
the same perceptual palette quantization
with strict identity-aware hysteresis
```

Both runs must bind the same:

- structural surface hash;
- palette hash;
- presentation profile hash;
- camera-path hash;
- frame count;
- structural identity set.

The proof must demonstrate:

```text
SAME_ACCEPTED_STRUCTURAL_SURFACE
SAME_PALETTE
SAME_PRESENTATION_PROFILE
SAME_CAMERA_PATH
SAME_FRAME_COUNT
SAME_STRUCTURAL_IDENTITIES
FEWER_UNSTABLE_SAME_IDENTITY_PALETTE_CHANGES
ZERO_INVALID_HISTORY_REUSE
ZERO_PRESENTATION_CREATED_STRUCTURAL_IDENTITIES
DETERMINISTIC_REPLAY
```

The first proof does not need to establish advanced reprojection, transparency, dynamic characters, particles, perspective-general stabilization, or a complete production renderer.

---

## 15. Presentation Acceptance Invariants

```text
PRESENTATION_REFERENCES_ACCEPTED_STRUCTURAL_IDENTITIES
SCREEN_CELL_IS_NOT_STRUCTURAL_OWNER
NO_PRESENTATION_CREATED_IDENTITY
NO_PRESENTATION_RENAMED_IDENTITY
NO_PRESENTATION_MERGED_OWNERSHIP
NO_PRESENTATION_SPLIT_OWNERSHIP
NO_SCREEN_PROXIMITY_DERIVED_ADJACENCY
SEMANTICALLY_ILLEGAL_PALETTE_ENTRY_IS_NEVER_SELECTED
PALETTE_SELECTION_USES_DECLARED_PERCEPTUAL_SPACE
HISTORY_REUSE_REQUIRES_IDENTITY_AUTHORIZATION
IDENTITY_CHANGE_REJECTS_INCOMPATIBLE_HISTORY
HYSTERESIS_DOES_NOT_HIDE_STRUCTURAL_IDENTITY_CHANGE
STRUCTURAL_ORIENTATION_OVERRIDES_CAMERA_DERIVED_ORIENTATION
FALLBACK_ORIENTATION_IS_STRUCTURAL_IDENTITY_STABLE
PRESENTATION_FRAME_IS_DERIVED_AND_NON_AUTHORITATIVE
PRESENTATION_PROOF_BINDS_ALL_DECLARED_INPUT_HASHES
PRESENTATION_REPLAY_IS_DETERMINISTIC
GODOT_DISPLAY_DOES_NOT_REAUTHOR_THE_WORLD
```

---

## 16. Prohibited Interpretations

```text
Rendered image → inferred canonical trixel surface
Screen cell → structural owner
Color boundary → structural topology
Depth edge → structural adjacency
Camera visibility → structural existence
Palette index → material authority
Temporal history → identity authority
Godot mesh instance → canonical ownership
Post-process triangle → topology decision
Perceptual similarity → semantic legality
```

The presentation lane is an observer and presenter of accepted structure.

It is not a second compiler of world truth.

---

## 17. Doctrine Integration

This update extends the established architecture as follows:

```text
Address/Lattice Authority
    ↓
Artwork Authority
    ↓
Topology Authority
    ↓
Geometry Authority
    ↓
Render Expansion
    ↓
Perceptual Presentation Authority
    ↓
Godot Display
```

Perceptual Presentation Authority is downstream of canonical geometry and render expansion.

It may derive visibility, sampling, palette, stability, and reconstruction decisions.

It may not flow authority backward into any prior layer.

```text
accepted structural trixel
    ↓ authorizes
presentation observation
    ↓ authorizes
visible display result
```

Never:

```text
visible display result
    ↓ inferred backward
structural trixel truth
```

---

## 18. Final Governing Statement

```text
Trixel does not recover a world from pixels.

Trixel first compiles an authoritative discrete world into attributable
geometry.

Its perceptual presentation lane then observes that accepted world from
a declared camera, resolves only accepted structural identities, restricts
color choices through semantic authorization, compares legal colors in a
declared perceptual space, stabilizes derived choices through identity-aware
history, and reconstructs the result through a deterministic triangular
visual grammar.

Presentation may change how a trixel is seen.

Presentation may not change what the trixel is.
```

---

## 19. Effect of This Update

This update adds a downstream doctrine boundary.

It does not declare the perceptual presentation renderer implemented.

It does not declare the four conceptual contracts implemented.

It does not declare a presentation proof passed.

It establishes the rules that any future implementation, schema, gate, fixture, renderer, or Godot consumer must obey before it can be admitted as part of Trixel 3.2d.

**END OF UPDATE**
