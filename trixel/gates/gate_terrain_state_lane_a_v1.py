#!/usr/bin/env python3
"""Execute the isolated Lane A behavior gates and publish diagnostic evidence."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FIXTURE = ROOT / "fixtures" / "terrain_state" / "watershed_v1.json"
CONTRACT = ROOT / "docs" / "TERRAIN_STATE_LANE_A_CONTRACT_V1.md"
EXPECTED_TESTS = {
    "test_fixture_has_independently_accounted_expected_ledger",
    "test_exact_watershed_states_routes_ledger_and_totals",
    "test_all_transfers_follow_declared_edges_not_touching_positions",
    "test_route_is_distinct_from_movement_and_sink_can_receive",
    "test_loss_is_capped_at_available_water",
    "test_fixed_potential_fold_has_identical_state_and_bytes",
    "test_explicit_gravity_reorientation_changes_flow_not_graph",
    "test_replay_and_serialization_are_exact",
    "test_input_order_cannot_change_result_or_provenance",
    "test_external_adapter_is_snapshotted_once_without_mutation",
    "test_frozen_adapter_has_detached_snapshots",
    "test_empty_rainfall_schedule_is_valid_zero_step_replay",
    "test_routing_uses_metric_slope_then_exact_id_tie_break",
    "test_rejects_invalid_topology_without_mutating_adapter_data",
    "test_rejects_missing_unknown_and_contradictory_physical_rules",
    "test_rejects_invalid_water_potential_and_embedding",
    "test_rejects_missing_zero_and_nonfinite_gravity",
    "test_rejects_unrepresentable_effective_potential",
}


def report(name: str, ok: bool) -> bool:
    print(f"[TERRAIN_STATE_LANE_A][{name}] {'TRUE' if ok else 'FALSE'}")
    return ok


def test_names(suite):
    names = []
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            names.extend(test_names(item))
        else:
            names.append(item.id().rsplit(".", 1)[-1])
    return names


def canonical_json(value) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True,
                        help="Explicit machine-owned diagnostic evidence destination")
    args = parser.parse_args()
    try:
        loader = unittest.TestLoader()
        suite = loader.discover(str(ROOT / "tests"), pattern="test_terrain_state_lane_a.py")
        names = test_names(suite)
        if not report("NAMED_GATES_PRESENT", set(names) == EXPECTED_TESTS and len(names) == len(EXPECTED_TESTS)):
            report("ALL_GATES", False)
            return 1
        outcome = unittest.TextTestRunner(verbosity=2).run(suite)
        if not report("BEHAVIORAL_GATES", outcome.wasSuccessful() and outcome.testsRun == len(EXPECTED_TESTS)):
            report("ALL_GATES", False)
            return 1

        from trixel.terrain_state.state_v1 import FrozenTopologyAdapter, run_simulation, serialize_result

        fixture_bytes, contract_bytes = FIXTURE.read_bytes(), CONTRACT.read_bytes()
        fixture = json.loads(fixture_bytes)
        adapter = FrozenTopologyAdapter(fixture["topology"])
        results = [run_simulation(adapter, fixture["policy"], fixture["initial_water"], fixture["rainfall_steps"],
                                  embedding=fixture["embeddings"][name]) for name in ("flat", "folded")]
        exact = all(results[0][key] == value for key, value in fixture["expected"].items())
        invariant = serialize_result(results[0]) == serialize_result(results[1])
        if not (report("INDEPENDENT_EXPECTED_LEDGER", exact) and report("FIXED_POTENTIAL_EMBEDDING_INVARIANCE", invariant)):
            report("ALL_GATES", False)
            return 1

        evidence = {
            "contract": "trixel.terrain_state_proof_evidence.v1",
            "scope": "isolated_terrain_state_proof_only",
            "fixture_id": fixture["fixture_id"],
            "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
            "contract_sha256": hashlib.sha256(contract_bytes).hexdigest(),
            "behavioral_gates": sorted(names),
            "embeddings": fixture["embeddings"],
            "expected": fixture["expected"],
            "result": results[0],
            "limitations": ["abstract graph, not a rendered mountain", "storage sinks, not lake levels",
                            "no geology generation or erosion", "material candidates, not recipe or artwork application",
                            "no Richat reconstruction or polygon-topology validation"],
        }
        ledger = io.StringIO(newline="")
        fields = ["step", "cell_id", "water_before", "rainfall", "incoming_transfers", "outgoing_transfers",
                  "outgoing_to", "declared_loss", "water_after", "boundary_discharge"]
        writer = csv.DictWriter(ledger, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(results[0]["ledger"])
        outputs = {"evidence.json": canonical_json(evidence), "ledger.tsv": ledger.getvalue().encode("utf-8")}
        input_paths = [FIXTURE, CONTRACT, Path(__file__), ROOT / "trixel" / "terrain_state" / "state_v1.py",
                       ROOT / "trixel" / "terrain_state" / "__init__.py", ROOT / "tests" / "test_terrain_state_lane_a.py"]
        manifest = {
            "contract": "trixel.terrain_state_proof_manifest.v1", "scope": "isolated_terrain_state_proof_only",
            "inputs": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in input_paths},
            "outputs": {name: hashlib.sha256(content).hexdigest() for name, content in outputs.items()},
        }
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for name, content in outputs.items():
            (args.output_dir / name).write_bytes(content)
        (args.output_dir / "manifest.json").write_bytes(canonical_json(manifest))
        readback = all((args.output_dir / name).read_bytes() == content for name, content in outputs.items())
        readback = readback and json.loads((args.output_dir / "manifest.json").read_bytes()) == manifest
        report("PUBLISHED_BYTES_VERIFIED", readback)
        print("Water totals: " + json.dumps(results[0]["totals"], sort_keys=True))
        report("ALL_GATES", readback)
        return 0 if readback else 1
    except (ValueError, OSError, ImportError) as exc:
        print(f"[TERRAIN_STATE_LANE_A][REJECTED] {exc}")
        report("ALL_GATES", False)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
