# Terrain-State Lane A Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Prove deterministic, fully accounted water transfer over immutable accepted topology without constructing terrain or mutating artwork.

**Architecture:** A read-only adapter supplies an opaque-node graph snapshot. A pure simulator validates complete physical definitions, computes deterministic downhill routes independently of water movement, and emits states, an exact ledger, and candidate-only material labels. Embedding affects physics only in explicit gravity-coupled mode.

**Tech Stack:** Python standard library (typing.Protocol, JSON, fractions), existing pytest/unittest harness. No new dependency.

Authority: docs/TERRAIN_STATE_LANE_A_CONTRACT_V1.md and the user-authorized scope in this session. The contract freezes exact API/record shapes, validation, stepping, and non-goals. Do not commit or push; do not alter existing source, tests, artwork, fixtures, external geology assets, or compiler contracts.

## Task 1: Freeze reference inputs and expected ledger

Create fixtures/terrain_state/watershed_v1.json. It contains the ten-node abstract watershed, explicit symmetric unit-length edges, read-only reference elevations, complete policy/initial/rainfall maps, flat and metric-preserving folded embeddings, and four-step expected state/ledger data. Compute expected quantities from an explicit transfer schedule independent of the production algorithm; reconcile every step. Record a detached source topology for the no-proximity test. No terrain generator or rendered mountain is implied.

Create tests/test_terrain_state_lane_a.py using unittest style. Test exact expected states/ledger/totals, routing vs actual movement, losses, outlets, receiving sinks, no proximity transfer, replay/canonical bytes, permutations, detached adapter copies, successful/rejected caller non-mutation, validation failure classes, empty rainfall replay, fixed-potential embedding invariance, and explicit gravity reorientation. Self-check fixture edge lengths and independent water equations. Include an adapter not subclassing the supplied implementation so the core must consume the protocol rather than grid-specific code.

## Task 2: Observe RED

Run PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/test_terrain_state_lane_a.py -q -p no:cacheprovider. Before production exists, expect the sole absent feature boundary trixel.terrain_state.state_v1. Report collection RED accurately; behavioral assertions have not yet executed. Run existing tests independently with the new file excluded; preserve their baseline. Do not add a stub to simulate GREEN.

## Task 3: Implement adapter/validation/routing/stepping

Create trixel/terrain_state/__init__.py and trixel/terrain_state/state_v1.py only. Public signatures:
- TopologyAdapter.snapshot(self) -> dict
- FrozenTopologyAdapter(snapshot)
- run_simulation(adapter, policy, initial_water, rainfall_steps, *, embedding) -> dict
- serialize_result(result) -> bytes

Freeze a validated input copy internally; snapshots must be detached. Validate topology symmetry, exact field sets, finite non-bool numerics, positive distances, exact per-cell map coverage, explicit rules and roles, integer water quantities, embedding coverage and vector shape, mode-specific inputs, and route feasibility. Compute slopes with Fraction-based arithmetic so route ties do not depend on input iteration. Synchronous updates must not move new arrivals twice. Include input provenance and full accounting evidence; exclude declared-mode display positions from simulation output, retain gravity-coupled positions as physical inputs.

Run focused tests to GREEN, then full tests. No IO, rendering, random state, grid imports, or authority calls in core. Expose only candidate material requests. Do not modify RED tests merely to make implementation pass; resolve genuine contract contradictions explicitly.

## Task 4: Standalone proof and publication

Create trixel/gates/gate_terrain_state_lane_a_v1.py. Follow neighboring gate root-bootstrap and ALL_GATES conventions. Execute the actual focused unittest suite, fail if any named behavior fails, then replay the real fixture through production. Require an explicit --output-dir; publish evidence.json and ledger.tsv plus a checksummed manifest. Evidence records both embeddings, independent expected data, simulation result, and the narrow proof scope. Validate published bytes/read-back in tests before adding runner code.

Run the proof into fixtures/terrain_state/proof_v1 (new evidence only). Inspect exact generated ledger and totals. Run same proof again into an OS temporary directory and compare output file bytes; remove the temporary directory.

## Task 5: Independent review and preservation verification

Request spec review against the frozen contract first, then quality review after spec PASS. Reviewers are read-only and must provide file:line findings with executable reproductions for important failures. Fix legitimate gaps with RED first; obtain fresh review after changes. Run full pytest, selected existing global-sample/pixel-geometry gates, syntax checks without bytecode files, and git diff --check. Hash tracked source/artifact paths before and after to prove no pre-existing file was changed. Read back generated proof manifest and ledger.

Stop after the isolated watershed proof. Richat reconstruction, polygon topology, actual lake levels, sediment, erosion, saturation, physical material ownership, and runtime integration remain separate tickets. Report actual executions and limitations, never invented runtime results.
