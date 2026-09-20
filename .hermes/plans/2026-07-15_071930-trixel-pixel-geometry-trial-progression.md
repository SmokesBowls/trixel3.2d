# Trixel Pixel-Geometry Trial Progression Plan

> **For Hermes:** Use subagent-driven-development and test-driven-development skills to implement this plan one bounded trial at a time. Require spec compliance and code-quality review before advancing to the next trial.

**Goal:** Progress from the Trixel 3.2D doctrine to a deterministic pixel-geometry compiler through isolated, fail-closed trials that prove address, ownership, adjacency, embedding, topology decisions, provenance, and render expansion in that order.

**Architecture:** A neutral `trixel.pixel_geometry.v1` package will compile immutable addressed footprints into canonical geometry. The compiler consumes versioned footprint, instance, embedding-specification, and topology-policy inputs; emits dispositions, a compiled cell graph, adjacency deltas, canonical geometry, provenance, and diagnostics; and is judged by a separate validator. Blender and Godot remain downstream evidence/render consumers and cannot authorize topology or infer ownership from meshes.

**Tech Stack:** Python 3, JSON Schema Draft 7, existing `jsonschema` dependency, deterministic JSON fixtures, standalone Python gates, optional Blender/Godot consumers only after neutral canonical proofs pass.

---

## Scope Locks

### Preserve untouched

- `trixel/global_sample/**`
- Existing global-sample schemas and gates
- Existing terrain recipes and fixtures
- Existing Blender/Godot evidence outside this repository
- Historical 16x16-sample / 15x15-quad proof artifacts

### Do not do during the neutral trials

- Do not turn Blender modifiers into compiler authority.
- Do not infer cell identity or adjacency from generated meshes.
- Do not wire the new compiler into EngAIn, Pyroclast, Godot, or Blender before the neutral gates pass.
- Do not implement trees, branches, characters, caves, cliffs, and terrain simultaneously.
- Do not add continuous deformation as a fallback.
- Do not silently merge, split, cull, weld, or create seams.
- Do not let the compiler certify its own output; validation remains independent.
- Do not replace the existing global-sample patch authority. Interoperation is a later explicit trial.

### Stop rule

Do not advance to the next trial unless:

1. its positive gate passes;
2. its toxic/negative fixtures fail for the intended reason;
3. all previous trial gates still pass;
4. the existing global-sample regression gates still pass;
5. no unrelated repository files changed.

---

## Proposed Package and Evidence Layout

```text
trixel/pixel_geometry/
    __init__.py
    contracts_v1.py
    addressing_v1.py
    adjacency_v1.py
    embedding_v1.py
    compiler_v1.py
    validator_v1.py
    policies/
        __init__.py
        preserve_exact_v1.py
        merge_ring_v1.py
        split_cell_v1.py
        cull_cell_v1.py
    schemas/
        footprint_definition_v1.schema.json
        footprint_instance_v1.schema.json
        embedding_specification_v1.schema.json
        topology_policy_v1.schema.json
        compilation_artifact_v1.schema.json
        validation_artifact_v1.schema.json

fixtures/pixel_geometry/
    trial_00_contract/
    trial_01_flat_footprint/
    trial_02_rigid_embedding/
    trial_03_cylinder_seam/
    trial_04_proximity_toxic/
    trial_05_declared_merge/
    trial_06_split_cull_transition/
    trial_07_bark_16x16/
    trial_08_tapered_trunk/
    trial_09_render_expansion/
    trial_10_global_sample_interop/

trixel/gates/
    gate_pixel_geometry_contract_v1.py
    gate_pixel_geometry_flat_footprint_v1.py
    gate_pixel_geometry_rigid_embedding_v1.py
    gate_pixel_geometry_cylinder_seam_v1.py
    gate_pixel_geometry_proximity_toxic_v1.py
    gate_pixel_geometry_declared_merge_v1.py
    gate_pixel_geometry_topology_roles_v1.py
    gate_pixel_geometry_bark_16x16_v1.py
    gate_pixel_geometry_tapered_trunk_v1.py
    gate_pixel_geometry_render_expansion_v1.py
    gate_pixel_geometry_global_sample_interop_v1.py
    gate_pixel_geometry_regression_v1.py
```

Paths are proposed and should be confirmed during Trial 0. Do not create the whole tree up front; each trial adds only the files it requires.

---

## Phase 0 — Ratify and Freeze the Authority Surface

### Task 0.1: Classify the doctrine files

**Objective:** Select one canonical doctrine and prevent three untracked variants from silently competing.

**Inspect:**
- `3.2_trixel_doctrine.md`
- `trixel3.2d_doctrine.md`
- `trixel3.2d_doctrine`

**Steps:**
1. Diff the three files without editing them.
2. Record which file is canonical, which are drafts, and whether either draft contains material absent from the candidate authority.
3. Obtain user approval before deleting, renaming, or absorbing any variant.
4. Keep all three untouched until classification is approved.

**Acceptance:** Exactly one path is declared as the future normative doctrine; no deletion is performed implicitly.

### Task 0.2: Apply the doctrine precision pass

**Objective:** Make the doctrine internally consistent before schemas claim to implement it.

**Modify only after canonical-file approval:**
- Canonical doctrine selected in Task 0.1

**Required corrections:**
- Add the explicit compiler pipeline.
- Use `EmbeddingSpecification` as compiler input and `TopologyDecisionMap` as output.
- Add `CompiledCellGraph` and `AdjacencyDelta` to required outputs.
- Separate compiler diagnostics from independent acceptance results.
- Define `PRESERVED_1_TO_1` as one canonical ownership region, not one geometric primitive.
- Separate primary terminal dispositions from optional contributor roles.
- Change renderer wording from `MUST duplicate vertices` to `MAY duplicate vertices`.
- Qualify the tapered/developable-surface example.
- Distinguish the three operational authorities from the lattice substrate and non-authoritative render expansion.

**Acceptance:** The doctrine contains no authority inversion and defines exact compiler and validator boundaries.

### Task 0.3: Freeze v1 names and authority direction

**Objective:** Prevent identifier drift during trials.

**Create:**
- `trixel/pixel_geometry/PIXEL_GEOMETRY_COMPILER_AUTHORITY_V1.md`

**Freeze:**

```text
trixel.footprint_definition.v1
trixel.footprint_instance.v1
trixel.embedding_specification.v1
trixel.topology_policy.v1
trixel.compilation_artifact.v1
trixel.validation_artifact.v1
```

**Freeze the direction:**

```text
address/lattice + artwork
    -> requested embedding + topology policy
    -> topology decisions + compiled cell graph
    -> canonical geometry + provenance
    -> independent validation
    -> optional render expansion
```

**Acceptance:** The authority document explicitly rejects geometry-derived identity and compiler self-certification.

**Checkpoint commit:** `docs: freeze pixel geometry compiler authority`

---

## Phase 1 — Contract-Only RED Gate

### Task 1.1: Add failing contract imports

**Objective:** Establish RED before implementation.

**Create:**
- `trixel/gates/gate_pixel_geometry_contract_v1.py`

**The gate must initially require nonexistent or incomplete:**
- schemas for all six packet classes;
- exact contract IDs;
- fail-closed unknown fields;
- versioned compiler input/output references;
- independent validation artifact references.

**Run:**

```bash
python trixel/gates/gate_pixel_geometry_contract_v1.py
```

**Expected:** FAIL because the v1 contract package and schemas do not exist yet.

### Task 1.2: Add minimal schemas and contract constants

**Objective:** Make only the contract gate pass; do not compile geometry.

**Create:**
- `trixel/pixel_geometry/__init__.py`
- `trixel/pixel_geometry/contracts_v1.py`
- Six schemas listed in the proposed layout

**Required input fields:**
- contract IDs and versions;
- footprint definition ID and hash/reference;
- footprint instance ID;
- local dimensions and cell metric;
- explicit address order and adjacency stencil;
- embedding specification ID and parameters;
- topology policy ID and parameters;
- compiler version.

**Required compilation outputs:**
- primary disposition map;
- optional contribution roles;
- compiled cell graph;
- adjacency delta;
- canonical geometry;
- primitive provenance;
- deterministic diagnostics.

**Required validation outputs:**
- validator ID/version;
- validated input/output hashes;
- named gate results;
- final verdict.

**Negative fixtures:**
- missing contract ID;
- unknown policy ID;
- dimensions inconsistent with payload;
- compiler artifact containing its own authoritative final verdict;
- unknown extra properties.

**Acceptance:** Positive packets pass and all malformed packets fail closed.

**Checkpoint commit:** `feat: add pixel geometry v1 contracts`

---

## Phase 2 — Trial 1: Flat 4x4 Identity Proof

### Task 2.1: Build an immutable 4x4 footprint fixture

**Objective:** Prove exact addresses and source adjacency before any curved embedding.

**Create:**
- `fixtures/pixel_geometry/trial_01_flat_footprint/footprint_definition.json`
- `fixtures/pixel_geometry/trial_01_flat_footprint/footprint_instance.json`
- `fixtures/pixel_geometry/trial_01_flat_footprint/embedding.json`
- `fixtures/pixel_geometry/trial_01_flat_footprint/policy.json`

**Fixture:**
- 4x4 cells;
- row-major local-Y then local-X address order;
- exact cardinal and diagonal neighbor vocabulary;
- unique color/metadata token per cell so swaps cannot hide;
- identity planar embedding;
- `preserve_exact.v1` policy.

### Task 2.2: Implement address and adjacency compilation

**Create:**
- `trixel/pixel_geometry/addressing_v1.py`
- `trixel/pixel_geometry/adjacency_v1.py`

**Prove:**
- 16 exact unique cell addresses;
- expected corner/cardinal/diagonal degree counts;
- no out-of-domain neighbor;
- deterministic serialization;
- artwork payload remains attached to its address.

### Task 2.3: Emit minimal canonical flat geometry

**Create:**
- `trixel/pixel_geometry/compiler_v1.py`
- `trixel/pixel_geometry/policies/preserve_exact_v1.py`
- `trixel/gates/gate_pixel_geometry_flat_footprint_v1.py`

**Required output:**
- 16 `PRESERVED_1_TO_1` primary dispositions;
- 16 ownership regions;
- compiled graph equal to source graph;
- empty adjacency delta;
- provenance for every canonical primitive;
- stable artifact hash across repeated runs.

**Toxic cases:**
- swapped artwork payloads;
- duplicate cell address;
- omitted cell;
- unexpected diagonal/cardinal link;
- primitive with no provenance.

**Acceptance:** `DECLARED_CELL_GRAPH_EQUALS_COMPILED_CELL_GRAPH TRUE` and all toxic fixtures are rejected.

**Checkpoint commit:** `feat: prove flat footprint identity`

---

## Phase 3 — Trial 2: Rigid 3D Embedding

### Task 3.1: Add rigid embedding specification

**Objective:** Prove that placement changes extrinsic coordinates without changing intrinsic identity or adjacency.

**Create:**
- `trixel/pixel_geometry/embedding_v1.py`
- `fixtures/pixel_geometry/trial_02_rigid_embedding/*`
- `trixel/gates/gate_pixel_geometry_rigid_embedding_v1.py`

**Trial variants:**
- translation only;
- 90-degree rotation about one declared axis;
- translation plus rotation.

**Prove:**
- exact same cell address set;
- exact same compiled cell graph;
- exact same dispositions and ownership;
- transformed canonical positions match declared transform;
- no topology decision is emitted beyond preservation.

**Toxic case:** A transform that changes an address or artwork owner must fail.

**Checkpoint commit:** `feat: prove rigid footprint embedding`

---

## Phase 4 — Trial 3: Exact Cylindrical Wrap and Declared Seam

### Task 4.1: Choose a metric-compatible cylinder fixture

**Objective:** Prove a curved but topology-preserving embedding before attempting taper.

**Create:**
- `fixtures/pixel_geometry/trial_03_cylinder_seam/*`
- `trixel/gates/gate_pixel_geometry_cylinder_seam_v1.py`

**Fixture rules:**
- choose circumference from declared column count and cell width;
- use a small footprint first, such as 8x2;
- declare seam adjacency explicitly between final and first columns;
- preserve row ordering and cell metric within the contract tolerance.

**Prove:**
- seam adjacency comes from the embedding specification, not vertex coincidence;
- every source cell remains one ownership region;
- non-seam adjacency is unchanged;
- seam creates only the declared adjacency delta;
- unwrap/re-parameterize recovers the intrinsic footprint within tolerance.

**Toxic cases:**
- overlapping seam positions with no seam declaration;
- seam declaration between wrong columns;
- radius/circumference mismatch under `preserve_exact.v1`;
- inferred adjacency from shared positions.

**Checkpoint commit:** `feat: prove exact cylindrical embedding`

---

## Phase 5 — Trial 4: Fold/Proximity Toxic Proof

### Task 5.1: Fold unrelated cells close together without authorizing contact

**Objective:** Prove geometric proximity cannot rewrite topology.

**Create:**
- `fixtures/pixel_geometry/trial_04_proximity_toxic/*`
- `trixel/gates/gate_pixel_geometry_proximity_toxic_v1.py`

**Prove:**
- unrelated cells may occupy nearby or coincident spatial neighborhoods;
- no adjacency appears unless declared by topology/embedding authority;
- optional collision/contact information remains separate from ownership adjacency.

**Toxic implementation:** A deliberately naive mesh-neighbor inference helper must be rejected as an authority source.

**Acceptance:** `NO_PROXIMITY_DERIVED_ADJACENCY TRUE`.

**Checkpoint commit:** `test: lock proximity against adjacency authority`

---

## Phase 6 — Trial 5: One Explicit Merge Policy

### Task 6.1: Write RED fixtures for a single circumference reduction

**Objective:** Prove the first topology-changing operation with exactly one variable.

**Create:**
- `fixtures/pixel_geometry/trial_05_declared_merge/*`
- `trixel/gates/gate_pixel_geometry_declared_merge_v1.py`

**Trial:** Reduce one declared ring by one ownership region using a deterministic pair selection. Do not taper a whole trunk yet.

**Required outputs:**
- affected cells have primary disposition `MERGED`;
- unaffected cells remain `PRESERVED_1_TO_1`;
- merge participants jointly own the target region;
- adjacency delta names removed/added edges;
- policy rule and deterministic tie-break are recorded;
- no unrelated row changes.

**Toxic cases:**
- undeclared merge;
- compiler-selected merge with no deterministic tie-break;
- dropped cell provenance;
- merged geometry claiming one source owner;
- adjacency changed without delta record.

### Task 6.2: Implement the minimal merge policy

**Create:**
- `trixel/pixel_geometry/policies/merge_ring_v1.py`

**Acceptance:** The declared merge passes; every alternative implicit merge fails closed.

**Checkpoint commit:** `feat: add explicit ring merge topology policy`

---

## Phase 7 — Trial 6: Separate Split, Cull, Transition, and Cap Roles

### Task 7.1: Prove one operation per fixture

**Objective:** Prevent topology concepts from becoming one ambiguous general-purpose mutation.

**Create:**
- `fixtures/pixel_geometry/trial_06_split_cull_transition/*`
- `trixel/gates/gate_pixel_geometry_topology_roles_v1.py`
- minimal policy module only when its RED fixture exists.

**Subtrials:**
1. One cell split into two ownership elements.
2. One cell explicitly culled with a reason.
3. A preserved or merged cell tagged with `TRANSITION_CONTRIBUTOR` as a secondary role.
4. Boundary cells tagged with `CAP_CONTRIBUTOR`, while cap geometry remains structurally owned by the policy.

**Prove:**
- exactly one primary disposition per source cell;
- zero or more contribution roles;
- cap/transition roles do not replace primary disposition;
- structural geometry names policy ownership and boundary provenance;
- each subtrial changes only its declared cells and edges.

**Checkpoint commits:** One commit per proven policy/role.

---

## Phase 8 — Trial 7: Full 16x16 Bark Footprint on Constant Cylinder

### Task 8.1: Scale the proven exact embedding

**Objective:** Prove the intended artwork footprint without introducing taper.

**Create:**
- `fixtures/pixel_geometry/trial_07_bark_16x16/*`
- `trixel/gates/gate_pixel_geometry_bark_16x16_v1.py`

**Prove:**
- 256 unique visual-cell addresses;
- exactly one 16x16 artwork ownership footprint;
- explicit cylindrical seam;
- all 256 primary dispositions preserved;
- deterministic adjacency and provenance;
- no larger atlas treated as one footprint;
- atlas region reference, if used, resolves exactly one 16x16 region.

**Acceptance:** This is the first valid bark-cylinder proof, not yet a tree or taper proof.

**Checkpoint commit:** `feat: prove 16x16 bark cylinder footprint`

---

## Phase 9 — Trial 8: Discrete Tapered Trunk Progression

### Task 9.1: Build a two-ring taper

**Objective:** Apply the proven merge policy once between two rings.

**Prove:**
- changing circumference is represented by a declared discrete decision;
- preserved cells retain metric;
- merge/transition cells retain provenance;
- adjacency delta is complete;
- no continuous squeeze is used.

### Task 9.2: Extend to a short multi-ring trunk

**Objective:** Prove deterministic progression across several isolated ring reductions.

**Create:**
- `fixtures/pixel_geometry/trial_08_tapered_trunk/*`
- `trixel/gates/gate_pixel_geometry_tapered_trunk_v1.py`

**Prove:**
- each reduction is independently attributable;
- tie-break policy gives identical decisions across runs;
- no ring becomes invalid or disconnected;
- flood-fill traversal covers the declared trunk ownership region;
- exact repeated compilation produces byte-identical canonical artifact.

**Stop condition:** Do not add branches until the tapered trunk passes all neutral gates.

**Checkpoint commit:** `feat: prove discrete tapered trunk compilation`

---

## Phase 10 — Trial 9: Render Expansion Without Authority Drift

### Task 10.1: Add a neutral render-expansion fixture

**Objective:** Prove vertex duplication for normals/UV seams does not alter canonical ownership.

**Create:**
- `fixtures/pixel_geometry/trial_09_render_expansion/*`
- `trixel/gates/gate_pixel_geometry_render_expansion_v1.py`

**Prove:**
- render vertex count may exceed canonical position count;
- every render element maps back to canonical geometry;
- canonical ownership and compiled adjacency are unchanged;
- UV seam duplication does not become logical seam creation;
- hard-normal duplication does not split ownership.

### Task 10.2: Add Blender/Godot consumers only after neutral proof

**Objective:** Use engines as evidence consumers, never authorities.

**Constraints:**
- consumers read the accepted canonical artifact;
- consumers do not infer topology;
- screenshot/render evidence remains downstream;
- headless structural gates remain separate from screenshot-producing gates.

**Checkpoint commit:** `feat: prove non-authoritative render expansion`

---

## Phase 11 — Trial 10: Interoperate with Existing Global-Sample Terrain Authority

### Task 11.1: Define the address bridge without collapsing owners

**Objective:** Relate 16x16 visual cells to 17x17 corner samples while preserving their distinct authority.

**Create:**
- `fixtures/pixel_geometry/trial_10_global_sample_interop/*`
- `trixel/gates/gate_pixel_geometry_global_sample_interop_v1.py`
- a narrow bridge module only after the gate is RED.

**Prove:**

```text
visual-cell address owns artwork and cell identity
corner-sample address owns canonical geometric positions
```

**Required checks:**
- 256 visual cells remain distinct from 289 corner samples;
- cell-to-corner incidence is deterministic;
- shared global corner addresses remain seam authority between patches;
- no corner sample becomes a visual owner;
- no artwork pixel is treated as a corner sample;
- existing global-sample gates remain unchanged and pass.

**Checkpoint commit:** `feat: bridge pixel ownership to global sample geometry`

---

## Deferred Trials — Only After the Core Ladder Passes

These are intentionally not part of the initial implementation lane:

1. Branch junction with explicit transition ownership.
2. Caps and terminal branch endings.
3. Sphere/non-developable surface policy.
4. Multiple footprint composition and collision/contact relationships.
5. Cave walls and inward-facing embeddings.
6. Character limbs and articulated footprint instances.
7. Atlas composition across multiple 16x16 regions.
8. EngAIn/WorldField/Godot integration.

Each deferred trial must vary one new authority decision at a time and inherit the full regression suite.

---

## Regression Commands

Run after every implementation task:

```bash
python trixel/gates/gate_worldfield_to_worldcell_projection_contract.py
python trixel/gates/gate_global_sample_patch_contract.py
python trixel/gates/gate_global_sample_field_contract.py
```

Run all pixel-geometry gates accumulated so far. Once the regression runner exists:

```bash
python trixel/gates/gate_pixel_geometry_regression_v1.py
```

Expected final output convention:

```text
TRIAL_XX_<NAME> TRUE
TOXIC_CASES_REJECTED TRUE
PRIOR_TRIALS_STILL_PASS TRUE
GLOBAL_SAMPLE_REGRESSION TRUE
ALL_GATES TRUE
```

Before each commit:

```bash
git diff --check
git status --short --untracked-files=all
git diff --stat
git diff
```

Only stage files named by the active trial. Do not use broad `git add .` while unrelated doctrine variants remain untracked.

---

## Promotion Ladder

```text
Doctrine ratified
    ↓
Contract packets validated
    ↓
Flat identity and adjacency proven
    ↓
Rigid embedding proven
    ↓
Exact curved embedding and seam proven
    ↓
Proximity/adjacency separation proven
    ↓
One explicit merge proven
    ↓
Split/cull/transition/cap semantics proven separately
    ↓
16x16 bark cylinder proven
    ↓
Discrete tapered trunk proven
    ↓
Render expansion proven non-authoritative
    ↓
Global-sample interoperation proven
    ↓
Branch-junction trial may begin
```

No stage is promoted because it looks correct in Blender. Promotion requires deterministic neutral artifacts, independent gate results, toxic-case rejection, and preserved prior proofs.

---

## Risks and Controls

### Risk: Building a general mesh library instead of Trixel

**Control:** Every task must prove cell address, ownership, adjacency, disposition, or provenance. Reject geometry-only features.

### Risk: Embedding performs hidden topology changes

**Control:** Compare source and compiled cell graphs. Any difference requires an explicit `AdjacencyDelta` and policy rule.

### Risk: Compiler self-approval

**Control:** Compiler emits diagnostics; independent validator emits final acceptance.

### Risk: Floating-point values weaken deterministic compilation

**Control:** Freeze numeric serialization, tolerances, coordinate conventions, iteration order, and artifact hashing before curved trials.

### Risk: Contributor roles violate one-terminal-disposition law

**Control:** Keep primary disposition and contribution roles as separate fields and validate both independently.

### Risk: Render engine becomes authority

**Control:** Render adapters consume canonical artifacts and must provide reverse mappings to canonical positions/primitives.

### Risk: Existing terrain authority is accidentally rewritten

**Control:** Keep `trixel/global_sample/**` untouched until the dedicated interoperation trial.

### Risk: Scope jumps from one footprint to a whole tree

**Control:** Require each trial to vary one property only. Constant cylinder precedes taper; taper precedes branch; branch precedes composition.

---

## Immediate Execution Slice

When implementation begins, execute only:

```text
Task 0.1 — classify doctrine variants
Task 0.2 — ratify the canonical doctrine after approval
Task 0.3 — freeze v1 authority names
Task 1.1 — write the RED contract gate
Task 1.2 — add minimal schemas/constants to reach GREEN
```

Stop and review before beginning flat geometry compilation. This keeps the first implementation ticket contract-only and prevents premature mesh construction.
