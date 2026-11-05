# Lane A: isolated terrain-state proof v1

Status: implementation contract authorized by the user; no integration authority.
Scope: deterministic water accounting over accepted, read-only terrain topology.
Upstream: 3.2_trixel_doctrine.md sections 3.3, 5.2, and 6; the existing rectangular patch and pixel-geometry contracts are unchanged.

## Authority and non-goals

Accepted topology owns node identities, symmetric neighbor incidence, intrinsic edge distances, reference elevations, and unit declarations. The simulator consumes a read-only adapter, snapshots it once per run, and never imports rectangular-grid, polygon, compiler, recipe, artwork, renderer, or donor logic. Node IDs are opaque strings; this proof does not decide whether nodes are visual cells or terrain regions.

Accepted elevations are immutable reference geography. Water is evolving state. No erosion, sediment, saturation, lake-level solver, overflow, geometry modification, recipe selection, artwork mutation, Richat ingestion, polygon generation, runtime wiring, commit, or push is authorized here. Material outputs are explicitly candidates only. A storage sink is not a simulated lake.

## Public boundary

New module: trixel/terrain_state/state_v1.py.
- TopologyAdapter protocol: snapshot() -> dict, no mutation methods.
- FrozenTopologyAdapter(snapshot): validates and privately freezes a copy; snapshot() returns a fresh copy.
- run_simulation(adapter, policy, initial_water, rainfall_steps, *, embedding) -> dict.
- serialize_result(result) -> bytes: UTF-8 JSON, sorted keys, compact separators, no nonfinite values, final newline.

The adapter snapshot has exactly contract='trixel.terrain_topology_snapshot.v1', topology_id, metric_unit, elevation_unit, and nodes. Nodes is a nonempty list of exact records {cell_id, reference_elevation, neighbors}. Each neighbor is exactly {cell_id, distance}. IDs and units are nonblank strings. Elevations are finite numbers, not booleans. Distances are finite positive numbers, not booleans. IDs are unique; edges are unique, non-self, reference existing nodes, and have reciprocal incidence with equal distances. Isolated nodes are permitted only with explicitly valid physical roles.

Policy has exactly contract='trixel.terrain_physical_policy.v1', potential_mode, potential_unit, routing, update_rule, outlet_rule, sink_rule, roles, loss_per_step, and its mode-specific potential input. Required literal rules:
- routing='steepest_descent_then_cell_id.v1'
- update_rule='synchronous_one_edge_per_step.v1'
- outlet_rule='discharge_all_after_loss.v1'
- sink_rule='retain_all_after_loss.v1'

Declared mode requires potential_by_cell and forbids gravity. Gravity-coupled mode requires gravity, a finite nonzero three-vector, and forbids potential_by_cell. Every cell has exactly one role: route, storage_sink, or outlet. Every map (roles, loss_per_step, initial_water, each rainfall step, declared potentials, embedding) covers exactly the node set. Missing/extra fields and incomplete definitions reject before any simulation. All water and loss quantities are nonnegative Python integers, excluding bool. Rainfall_steps is a list, possibly empty; each element is a complete per-cell map. Embedding maps each ID to a finite three-vector; its positions never establish incidence.

## Physical policy and deterministic stepping

Numeric evidence restriction: v1 publishes effective potentials as JSON numbers. A gravity-derived rational potential must round-trip exactly through its decimal JSON numeric representation; otherwise validation rejects before stepping. Underflow to zero, overflow, and rounding that hides an actual potential difference are unsupported, never silently accepted. This restriction does not infer alternative physics; a later exact-rational output contract can expand the supported range.

Potential is either the complete declared map or -dot(gravity, embedding_position), computed with exact rational arithmetic from validated decimal numeric representations. Lower potential is downhill. At each route node choose a strictly lower declared neighbor maximizing (potential_here - potential_neighbor) / intrinsic_edge_distance; ties resolve by lexicographically smallest cell_id. Undefined potential, a route node with no downhill edge, contradictory incidence, invalid metrics, or unspecified rules reject. Storage sinks and outlets intentionally have no outgoing cell route even when lower neighbors exist.

Routing is designated independently of actual movement. Each synchronous step:
1. Read previous stored water and add this step's rainfall.
2. Remove min(loss_per_step, available) as a declared loss.
3. Route nodes transfer all remaining available water across their designated edge. Outlets discharge all remaining available water across the declared boundary. Storage sinks retain it.
4. Collect incoming cell transfers only after all decisions; incoming water is stored until the next step. It is not re-routed, lost, or discharged in its arrival step.

Ledger has one row per cell per step in sorted ID order: step, cell_id, water_before, rainfall, incoming_transfers, outgoing_transfers, outgoing_to, declared_loss, water_after, boundary_discharge. Local equation: before + rainfall + incoming = after + outgoing + loss + discharge. Global equation at every prefix: initial + rainfall = stored + cumulative discharge + cumulative losses. Outgoing route names may exist when outgoing quantity is zero; sinks receive water without an outgoing route.

Output includes initial and subsequent states, effective potentials, flow directions, cumulative incoming transfers (accumulated flow), full ledger, totals, and candidate materials. Input provenance retains the validated topology, policy, initial water, and rainfall. Declared-mode output excludes visual embedding so fixed physics yields byte-identical results; the proof evidence separately records both embeddings. Gravity-coupled output retains the supplied embedding as physical provenance. Candidate material labels are standing_water_candidate for wet storage sinks, flow_affected_candidate for other cells with received flow, otherwise unchanged_candidate; they never select a recipe.

## Frozen proof obligations

1. A ten-node watershed has paired ridge sides draining to different valleys, a declared depression sink, a channel receiving multiple upstream contributions, an explicit boundary outlet, and an isolated node that touches the channel in embedding space without a graph edge. These are an abstract graph fixture, not a rendered mountain or geological simulation.
2. Compare the complete independently specified four-step expected states and ledger, not merely simulator-provided totals.
3. Every cell transfer follows a declared edge; spatial contact adds no edge or transfer.
4. Independently reconcile every row and every step prefix; include nonzero losses, discharge, initial water, dry routes, and receiving sinks.
5. Repeat runs and canonical serialization exactly; permuting input record/map order cannot change output.
6. Verify caller inputs and topology snapshots are unchanged on successful and rejected runs; adapters return detached snapshots.
7. Flat and folded watershed embeddings preserve every declared edge length. With fixed potential and intrinsic metrics, complete results and bytes match.
8. A separate three-node gravity fixture reverses the downhill recipient when reoriented under fixed gravity while preserving the graph and edge metrics. No new edge is allowed. Accepted reference elevations remain unchanged.
9. Reject incomplete policies, missing/extra IDs, wrong primitive/container types, nonpositive/nonfinite metrics, asymmetric or inconsistent edges, invalid quantities, unknown rules, undefined downhill routes, and gravity-derived potentials that cannot be published exactly in v1's numeric representation.
10. Standalone gate executes the actual tests and writes evidence only to an explicit output directory. No edits to accepted geography, existing compilers, artwork, fixtures, or external assets.

Richat reconstruction and the 42-cell polygon specimen remain independent workstreams. Neither is implemented or validated by this proof.
