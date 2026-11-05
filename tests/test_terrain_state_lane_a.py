from __future__ import annotations

import copy
import json
import math
import unittest
from pathlib import Path

from trixel.terrain_state.state_v1 import FrozenTopologyAdapter, run_simulation, serialize_result

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "terrain_state" / "watershed_v1.json"


def fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class ExternalReadOnlyAdapter:
    """An unrelated caller-owned adapter: no grid or production inheritance."""

    def __init__(self, snapshot):
        self.data = snapshot
        self.calls = 0

    def snapshot(self):
        self.calls += 1
        return self.data


def run(f, *, embedding="flat"):
    return run_simulation(
        FrozenTopologyAdapter(f["topology"]), f["policy"], f["initial_water"],
        f["rainfall_steps"], embedding=f["embeddings"][embedding],
    )


def fork_fixture():
    ids = ["source", "a", "b"]
    neighbors = {"source": [("a", 1), ("b", 1)], "a": [("source", 1)], "b": [("source", 1)]}
    topology = {
        "contract": "trixel.terrain_topology_snapshot.v1", "topology_id": "fork.v1",
        "metric_unit": "proof_distance_unit", "elevation_unit": "proof_elevation_unit",
        "nodes": [{"cell_id": n, "reference_elevation": 0,
                   "neighbors": [{"cell_id": target, "distance": d} for target, d in neighbors[n]]}
                  for n in ids],
    }
    policy = copy.deepcopy(fixture()["policy"])
    policy["roles"] = {"source": "route", "a": "storage_sink", "b": "storage_sink"}
    policy["loss_per_step"] = dict.fromkeys(ids, 0)
    policy["potential_by_cell"] = {"source": 2, "a": 0, "b": 0}
    return {
        "topology": topology, "policy": policy,
        "initial_water": {"source": 7, "a": 0, "b": 0},
        "rainfall_steps": [dict.fromkeys(ids, 0)],
        "embeddings": {"flat": {"source": [0, 0, 0], "a": [-1, 0, 0], "b": [1, 0, 0]}},
    }


class TerrainStateLaneATests(unittest.TestCase):
    def test_fixture_has_independently_accounted_expected_ledger(self):
        f = fixture()
        expected = f["expected"]
        self.assertEqual(len(expected["ledger"]), 40)
        cumulative_rain = cumulative_loss = cumulative_discharge = 0
        for step in range(1, 5):
            rows = [r for r in expected["ledger"] if r["step"] == step]
            self.assertEqual({r["cell_id"] for r in rows}, set(f["initial_water"]))
            for r in rows:
                self.assertEqual(r["water_before"] + r["rainfall"] + r["incoming_transfers"],
                                 r["water_after"] + r["outgoing_transfers"] + r["declared_loss"] + r["boundary_discharge"])
            self.assertEqual(sum(r["incoming_transfers"] for r in rows), sum(r["outgoing_transfers"] for r in rows))
            cumulative_rain += sum(r["rainfall"] for r in rows)
            cumulative_loss += sum(r["declared_loss"] for r in rows)
            cumulative_discharge += sum(r["boundary_discharge"] for r in rows)
            self.assertEqual(sum(f["initial_water"].values()) + cumulative_rain,
                             sum(expected["states"][step].values()) + cumulative_loss + cumulative_discharge)

    def test_exact_watershed_states_routes_ledger_and_totals(self):
        f = fixture()
        result = run(f)
        self.assertEqual(result["contract"], "trixel.terrain_state_result.v1")
        for key, expected in f["expected"].items():
            self.assertEqual(result[key], expected, key)
        self.assertEqual(result["potential_by_cell"], f["policy"]["potential_by_cell"])
        self.assertEqual(result["input_provenance"]["topology"], f["topology"])
        self.assertEqual(result["input_provenance"]["policy"], f["policy"])
        self.assertEqual(result["input_provenance"]["initial_water"], f["initial_water"])
        self.assertEqual(result["input_provenance"]["rainfall_steps"], f["rainfall_steps"])
        self.assertEqual(result["candidate_materials"]["basin"], "standing_water_candidate")
        self.assertEqual(result["candidate_materials"]["channel"], "flow_affected_candidate")
        self.assertEqual(result["candidate_materials"]["near_other"], "unchanged_candidate")
        self.assertTrue(all(v.endswith("_candidate") for v in result["candidate_materials"].values()))

    def test_all_transfers_follow_declared_edges_not_touching_positions(self):
        f = fixture()
        self.assertEqual(f["embeddings"]["flat"]["channel"], f["embeddings"]["flat"]["near_other"])
        neighbors = {n["cell_id"]: {e["cell_id"] for e in n["neighbors"]} for n in f["topology"]["nodes"]}
        result = run(f)
        for row in result["ledger"]:
            if row["outgoing_transfers"]:
                self.assertIn(row["outgoing_to"], neighbors[row["cell_id"]])
        self.assertEqual(result["accumulated_flow"]["near_other"], 0)
        self.assertEqual(result["flow_direction"]["crest_w"], "valley_w")
        self.assertEqual(result["flow_direction"]["crest_e"], "valley_e")
        channel_step_2 = next(r for r in result["ledger"] if r["step"] == 2 and r["cell_id"] == "channel")
        self.assertEqual(channel_step_2["incoming_transfers"], 4)
        self.assertEqual(channel_step_2["outgoing_transfers"], 3)
        self.assertEqual(channel_step_2["water_after"], 4)

    def test_route_is_distinct_from_movement_and_sink_can_receive(self):
        result = run(fixture())
        dry = next(r for r in result["ledger"] if r["step"] == 2 and r["cell_id"] == "crest_w")
        self.assertEqual(dry["outgoing_to"], "valley_w")
        self.assertEqual(dry["outgoing_transfers"], 0)
        sink = next(r for r in result["ledger"] if r["step"] == 1 and r["cell_id"] == "basin")
        self.assertIsNone(sink["outgoing_to"])
        self.assertEqual(sink["incoming_transfers"], 6)
        self.assertEqual(sink["water_after"], 6)

    def test_loss_is_capped_at_available_water(self):
        f = fixture()
        f["policy"]["loss_per_step"]["near_other"] = 100
        result = run(f)
        rows = [r for r in result["ledger"] if r["cell_id"] == "near_other"]
        self.assertEqual([r["declared_loss"] for r in rows], [2, 0, 0, 0])
        self.assertTrue(all(r["water_after"] >= 0 for r in result["ledger"]))

    def test_fixed_potential_fold_has_identical_state_and_bytes(self):
        f = fixture()
        for node in f["topology"]["nodes"]:
            for edge in node["neighbors"]:
                for embedding in f["embeddings"].values():
                    self.assertAlmostEqual(math.dist(embedding[node["cell_id"]], embedding[edge["cell_id"]]), edge["distance"])
        flat, folded = run(f), run(f, embedding="folded")
        self.assertEqual(flat, folded)
        self.assertEqual(serialize_result(flat), serialize_result(folded))

    def test_explicit_gravity_reorientation_changes_flow_not_graph(self):
        f = fork_fixture()
        for node in f["topology"]["nodes"]:
            node["reference_elevation"] = {"source": 1, "a": 0, "b": 2}[node["cell_id"]]
            for edge in node["neighbors"]:
                edge["distance"] = math.sqrt(2)
        f["embeddings"] = {
            "flat": {"source": [0, 1, 0], "a": [-1, 0, 0], "b": [1, 2, 0]},
            "folded": {"source": [0, -1, 0], "a": [-1, 0, 0], "b": [1, -2, 0]},
        }
        f["policy"]["potential_mode"] = "gravity_coupled"
        del f["policy"]["potential_by_cell"]
        f["policy"]["gravity"] = [0, -1, 0]
        original = copy.deepcopy(f)
        first, second = run(f), run(f, embedding="folded")
        self.assertEqual(first["flow_direction"]["source"], "a")
        self.assertEqual(second["flow_direction"]["source"], "b")
        self.assertEqual(first["states"][-1], {"source": 0, "a": 7, "b": 0})
        self.assertEqual(second["states"][-1], {"source": 0, "a": 0, "b": 7})
        self.assertEqual(first["input_provenance"]["topology"], second["input_provenance"]["topology"])
        self.assertEqual(first["input_provenance"]["embedding"], f["embeddings"]["flat"])
        self.assertEqual(second["input_provenance"]["embedding"], f["embeddings"]["folded"])
        self.assertEqual(f, original)
        for embedding in f["embeddings"].values():
            self.assertAlmostEqual(math.dist(embedding["source"], embedding["a"]), math.sqrt(2))
            self.assertAlmostEqual(math.dist(embedding["source"], embedding["b"]), math.sqrt(2))

    def test_replay_and_serialization_are_exact(self):
        f = fixture()
        first, second = run(f), run(f)
        self.assertEqual(first, second)
        encoded = serialize_result(first)
        self.assertIsInstance(encoded, bytes)
        self.assertEqual(encoded, serialize_result(second))
        self.assertTrue(encoded.endswith(b"\n"))
        self.assertEqual(json.loads(encoded), first)

    def test_input_order_cannot_change_result_or_provenance(self):
        def reverse_map_order(value):
            if isinstance(value, dict):
                reordered = {key: reverse_map_order(value[key]) for key in reversed(value)}
                self.assertEqual(list(reordered), list(reversed(value)))
                if len(value) > 1:
                    self.assertNotEqual(list(reordered), list(value))
                return reordered
            if isinstance(value, list):
                # Preserve chronological rainfall and vector component order.
                return [reverse_map_order(item) for item in value]
            return value

        gravity = fork_fixture()
        gravity["policy"]["potential_mode"] = "gravity_coupled"
        del gravity["policy"]["potential_by_cell"]
        gravity["policy"]["gravity"] = [0, -1, 0]
        gravity["embeddings"]["flat"] = {
            "source": [0, 1, 0], "a": [-1, 0, 0], "b": [1, 2, 0],
        }

        for f in [fixture(), gravity]:
            with self.subTest(potential_mode=f["policy"]["potential_mode"]):
                permuted = reverse_map_order(f)
                self.assertEqual(permuted, f)
                self.assertEqual(permuted["rainfall_steps"], f["rainfall_steps"])
                self.assertEqual(permuted["embeddings"], f["embeddings"])
                if "gravity" in f["policy"]:
                    self.assertEqual(permuted["policy"]["gravity"], f["policy"]["gravity"])
                permuted["topology"]["nodes"].reverse()
                for node in permuted["topology"]["nodes"]:
                    node["neighbors"].reverse()
                original_result, permuted_result = run(f), run(permuted)
                self.assertEqual(original_result, permuted_result)
                self.assertEqual(serialize_result(original_result), serialize_result(permuted_result))
                if f["policy"]["potential_mode"] == "gravity_coupled":
                    self.assertEqual(original_result["potential_by_cell"], {"source": 1, "a": 0, "b": 2})
                    self.assertEqual(original_result["input_provenance"]["embedding"], f["embeddings"]["flat"])
                    self.assertEqual(permuted_result["input_provenance"]["embedding"], permuted["embeddings"]["flat"])

    def test_external_adapter_is_snapshotted_once_without_mutation(self):
        f = fixture()
        before = copy.deepcopy(f)
        adapter = ExternalReadOnlyAdapter(f["topology"])
        result = run_simulation(adapter, f["policy"], f["initial_water"], f["rainfall_steps"], embedding=f["embeddings"]["flat"])
        self.assertEqual(adapter.calls, 1)
        self.assertEqual(f, before)
        result["input_provenance"]["topology"]["nodes"][0]["reference_elevation"] = 999
        self.assertEqual(f, before)

    def test_frozen_adapter_has_detached_snapshots(self):
        original = fixture()["topology"]
        before = copy.deepcopy(original)
        adapter = FrozenTopologyAdapter(original)
        original["nodes"][0]["neighbors"].clear()
        self.assertEqual(adapter.snapshot(), before)
        first, second = adapter.snapshot(), adapter.snapshot()
        self.assertIsNot(first, second)
        first["nodes"][0]["reference_elevation"] = 999
        self.assertEqual(adapter.snapshot(), before)

    def test_empty_rainfall_schedule_is_valid_zero_step_replay(self):
        f = fixture()
        f["rainfall_steps"] = []
        result = run(f)
        self.assertEqual(result["states"], [f["initial_water"]])
        self.assertEqual(result["ledger"], [])
        self.assertEqual(result["totals"], {"initial_water": 4, "rainfall": 0, "stored_water": 4, "boundary_discharge": 0, "declared_losses": 0})

    def test_routing_uses_metric_slope_then_exact_id_tie_break(self):
        f = fork_fixture()
        self.assertEqual(run(f)["flow_direction"]["source"], "a")
        f["policy"]["potential_by_cell"] = {"source": 2, "a": 0, "b": 1}
        for node in f["topology"]["nodes"]:
            for edge in node["neighbors"]:
                if {node["cell_id"], edge["cell_id"]} == {"source", "a"}:
                    edge["distance"] = 4
        self.assertEqual(run(f)["flow_direction"]["source"], "b")

    def test_rejects_invalid_topology_without_mutating_adapter_data(self):
        def malformed():
            t = fixture()["topology"]
            yield "empty", dict(t, nodes=[])
            for key in t:
                bad = copy.deepcopy(t); del bad[key]; yield "missing " + key, bad
            yield "extra field", dict(t, geometry_command="mutate")
            yield "duplicate ID", dict(t, nodes=t["nodes"] + [copy.deepcopy(t["nodes"][0])])
            for value in [0, -1, float("nan"), float("inf"), True, "1", None]:
                bad = copy.deepcopy(t); bad["nodes"][0]["neighbors"][0]["distance"] = value
                yield "metric " + repr(value), bad
            for value in [True, None, "1", float("nan"), float("inf")]:
                bad = copy.deepcopy(t); bad["nodes"][0]["reference_elevation"] = value
                yield "elevation " + repr(value), bad
            bad = copy.deepcopy(t); bad["nodes"][0]["neighbors"] = None; yield "neighbors container", bad
            bad = copy.deepcopy(t); bad["nodes"][0]["neighbors"].append(copy.deepcopy(bad["nodes"][0]["neighbors"][0])); yield "duplicate edge", bad
            bad = copy.deepcopy(t); bad["nodes"][0]["neighbors"][0]["cell_id"] = "unknown"; yield "unknown neighbor", bad
            bad = copy.deepcopy(t); bad["nodes"][0]["neighbors"][0]["cell_id"] = bad["nodes"][0]["cell_id"]; yield "self edge", bad
            bad = copy.deepcopy(t); bad["nodes"][0]["neighbors"].clear(); yield "asymmetry", bad
            bad = copy.deepcopy(t); bad["nodes"][0]["neighbors"][0]["distance"] = 2; yield "reciprocal distance", bad
            bad = copy.deepcopy(t); bad["nodes"][0]["hidden"] = True; yield "node extra", bad
            bad = copy.deepcopy(t); bad["nodes"][0]["neighbors"][0]["hidden"] = True; yield "edge extra", bad
        for label, topology in malformed():
            with self.subTest(label=label):
                before = copy.deepcopy(topology)
                adapter = ExternalReadOnlyAdapter(topology)
                f = fixture()
                with self.assertRaises(ValueError):
                    run_simulation(adapter, f["policy"], f["initial_water"], f["rainfall_steps"], embedding=f["embeddings"]["flat"])
                # NaN is not equal to itself; compare serialization of the input copies.
                self.assertEqual(json.dumps(topology, sort_keys=True), json.dumps(before, sort_keys=True))

    def test_rejects_missing_unknown_and_contradictory_physical_rules(self):
        f = fixture()
        cases = []
        for key in f["policy"]:
            bad = copy.deepcopy(f); del bad["policy"][key]; cases.append(("missing " + key, bad))
        for key in ["routing", "update_rule", "outlet_rule", "sink_rule", "potential_mode"]:
            bad = copy.deepcopy(f); bad["policy"][key] = "invented"; cases.append((key, bad))
        for key in ["roles", "loss_per_step", "potential_by_cell"]:
            for value in [None, [], {}]:
                bad = copy.deepcopy(f); bad["policy"][key] = value; cases.append((key + repr(value), bad))
            bad = copy.deepcopy(f); bad["policy"][key]["extra"] = 0; cases.append((key + " extra", bad))
        bad = copy.deepcopy(f); bad["policy"]["roles"]["basin"] = "route"; cases.append(("undefined downhill route", bad))
        bad = copy.deepcopy(f); bad["policy"]["roles"]["basin"] = "lake"; cases.append(("unknown role", bad))
        bad = copy.deepcopy(f); bad["policy"]["gravity"] = [0, -1, 0]; cases.append(("conflicting potential modes", bad))
        bad = copy.deepcopy(f); bad["policy"]["material_command"] = "apply"; cases.append(("unknown authority field", bad))
        for label, candidate in cases:
            with self.subTest(label=label):
                before = copy.deepcopy(candidate)
                with self.assertRaises(ValueError): run(candidate)
                self.assertEqual(candidate, before)

    def test_rejects_invalid_water_potential_and_embedding(self):
        cases = []
        for field in ["initial_water", "rainfall", "loss_per_step"]:
            for value in [-1, True, 1.5, "1", None]:
                f = fixture()
                target = f["initial_water"] if field == "initial_water" else f["rainfall_steps"][0] if field == "rainfall" else f["policy"]["loss_per_step"]
                target["basin"] = value; cases.append((field + repr(value), f))
        for value in [True, None, "1", float("nan"), float("inf")]:
            f = fixture(); f["policy"]["potential_by_cell"]["basin"] = value; cases.append(("potential" + repr(value), f))
        for value in [None, [], [0, 0], [0, 0, 0, 0], [0, True, 0], [0, float("inf"), 0]]:
            f = fixture(); f["embeddings"]["flat"]["basin"] = value; cases.append(("embedding" + repr(value), f))
        for key in ["initial_water", "rainfall_steps", "embedding"]:
            f = fixture()
            if key == "initial_water": del f["initial_water"]["basin"]
            elif key == "rainfall_steps": del f["rainfall_steps"][0]["basin"]
            else: del f["embeddings"]["flat"]["basin"]
            cases.append(("coverage " + key, f))
        f = fixture(); f["rainfall_steps"] = None; cases.append(("schedule container", f))
        for label, candidate in cases:
            with self.subTest(label=label):
                before = json.dumps(candidate, sort_keys=True)
                with self.assertRaises(ValueError): run(candidate)
                self.assertEqual(json.dumps(candidate, sort_keys=True), before)

    def test_rejects_unrepresentable_effective_potential(self):
        for baseline in [0, 1]:
            f = fork_fixture()
            f["policy"]["potential_mode"] = "gravity_coupled"
            del f["policy"]["potential_by_cell"]
            f["policy"]["gravity"] = [0, -1e-200, -1]
            f["embeddings"]["flat"] = {
                "source": [0, 1e-200, baseline],
                "a": [-1, 0, baseline],
                "b": [1, 2e-200, baseline],
            }
            # Exact rational routing must not be published as zero/equal float
            # potentials. v1 rejects unsupported output precision, not physics.
            with self.subTest(baseline=baseline), self.assertRaises(ValueError):
                run(f)

    def test_rejects_missing_zero_and_nonfinite_gravity(self):
        for gravity in [None, [], [0, 0, 0], [0, -1], [0, True, 0], [0, float("nan"), 0], [0, float("inf"), 0]]:
            f = fork_fixture()
            f["policy"]["potential_mode"] = "gravity_coupled"
            del f["policy"]["potential_by_cell"]
            f["policy"]["gravity"] = gravity
            with self.subTest(gravity=gravity), self.assertRaises(ValueError): run(f)


if __name__ == "__main__":
    unittest.main()
