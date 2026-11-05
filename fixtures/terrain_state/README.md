# Lane A terrain-state proof

This is a controlled abstract watershed, not terrain generation, a rendered mountain, a lake-level solver, or an accepted material/geometry change.

Authority: `docs/TERRAIN_STATE_LANE_A_CONTRACT_V1.md`.

## Reproduce from the repository root

```sh
PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/test_terrain_state_lane_a.py tests/test_terrain_state_proof_gate.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 python trixel/gates/gate_terrain_state_lane_a_v1.py --output-dir fixtures/terrain_state/proof_v1
```

The output destination is mandatory; the simulator itself performs no file IO. The gate only publishes after the named behavior tests and independent expected ledger pass. For an exploratory run, use a separate output directory.

## Fixture

`watershed_v1.json` freezes ten opaque terrain-node IDs, accepted reference elevations, exact reciprocal intrinsic distances, roles, declared potential, losses, initial water, four rainfall steps, flat/folded embeddings, and independently specified expected states and a 40-row ledger. Input node and neighbor order are representational, not authority. The frozen reference uses canonical ID ordering; permutation tests check that other orders produce the same result.

- `crest_w` and `crest_e` drain to distinct valleys.
- `valley_e` and `tributary` feed `channel`, which routes toward the boundary `outlet`.
- `basin_feed` feeds the retained-water `basin` sink.
- `near_other` is an isolated storage sink placed at the same display position as `channel`; it receives no transfer from the channel.
- The fold preserves every declared graph-edge distance and changes no declared drainage potential.

A separate three-node gravity test reverses the downhill recipient by changing the supplied embedding under fixed gravity. It keeps topology, reference elevations, and intrinsic metrics unchanged. No position-based edge creation is permitted.

## Read the evidence

- `proof_v1/evidence.json`: input provenance, effective potential, designated routes, initial/subsequent water states, accumulated received flow, ledger, candidate materials, both watershed embeddings, expected reference data, and limitations.
- `proof_v1/ledger.tsv`: one row per cell per step, suitable for a text editor or spreadsheet.
- `proof_v1/manifest.json`: hashes of source inputs and published outputs; no timestamp or output-directory-dependent content.

Each ledger row obeys:

`water_before + rainfall + incoming_transfers = water_after + outgoing_transfers + declared_loss + boundary_discharge`

Incoming water is available only in the next step. A dry node can have a designated route without moving water. A sink can receive water without an outgoing route. Loss amounts are capped at locally available pre-transfer water.

The four-step balance is:

`4 initial + 18 rainfall = 3 stored + 13 discharged + 6 declared losses`

Candidate materials are diagnostic labels, not recipe bindings or artwork authorization. Reference elevations remain immutable. Richat reconstruction, polygon topology, metric/material ownership, erosion, sediment, saturation, overflow, and actual lake surfaces remain separate workstreams.

Precision boundary: routing uses exact rational arithmetic from declared decimal numeric inputs. Gravity-derived effective potentials must also round-trip exactly through v1's JSON-number representation. Unsupported precision rejects before stepping rather than reporting rounded-equal or underflowed potentials. This is a proof-version restriction, not a substitute physical policy.
