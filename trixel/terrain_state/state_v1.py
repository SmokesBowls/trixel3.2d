"""Pure, explicit-policy water accounting on accepted terrain topology.

Exact rational potentials and intrinsic distances determine routing. Embedding
never supplies incidence, and arriving water cannot move again in the same step.
"""

from __future__ import annotations

import copy
import json
import math
from fractions import Fraction
from types import MappingProxyType
from typing import Protocol, cast


class TopologyAdapter(Protocol):
    """Read-only boundary; one detached snapshot is consumed per run."""

    def snapshot(self) -> dict: ...


def _fields(value, fields, label):
    if type(value) is not dict or set(value) != set(fields):
        raise ValueError(f"{label} must be a dict with exactly {sorted(fields)}")


def _text(value, label):
    if type(value) is not str or not value.strip():
        raise ValueError(f"{label} must be a nonblank string")
    return value


def _number(value, label):
    if type(value) not in (int, float) or (
        type(value) is float and not math.isfinite(value)
    ):
        raise ValueError(f"{label} must be a finite non-boolean number")
    return Fraction(str(value))


def _quantity(value, label):
    if type(value) is not int or value < 0:
        raise ValueError(f"{label} must be a nonnegative integer, not bool")
    return value


def _vector(value, label):
    if type(value) not in (list, tuple) or len(value) != 3:
        raise ValueError(f"{label} must be a finite three-vector")
    return tuple(_number(component, label) for component in value)


def _cell_map(value, ids, validate, label):
    if type(value) is not dict or set(value) != set(ids):
        raise ValueError(f"{label} must cover exactly the topology cell IDs")
    return {cell: validate(value[cell], f"{label}[{cell!r}]") for cell in ids}


def _topology(snapshot):
    _fields(snapshot, {"contract", "topology_id", "metric_unit", "elevation_unit", "nodes"}, "topology")
    if snapshot["contract"] != "trixel.terrain_topology_snapshot.v1":
        raise ValueError("unknown topology contract")
    for field in ("topology_id", "metric_unit", "elevation_unit"):
        _text(snapshot[field], field)
    nodes = snapshot["nodes"]
    if type(nodes) is not list or not nodes:
        raise ValueError("nodes must be a nonempty list")
    by_id = {}
    edges = {}
    for node in nodes:
        _fields(node, {"cell_id", "reference_elevation", "neighbors"}, "node")
        cell = _text(node["cell_id"], "cell_id")
        if cell in by_id:
            raise ValueError("duplicate cell ID")
        _number(node["reference_elevation"], "reference_elevation")
        if type(node["neighbors"]) is not list:
            raise ValueError("neighbors must be a list")
        adjacency = {}
        for edge in node["neighbors"]:
            _fields(edge, {"cell_id", "distance"}, "edge")
            target = _text(edge["cell_id"], "neighbor cell_id")
            distance = _number(edge["distance"], "distance")
            if distance <= 0 or target == cell or target in adjacency:
                raise ValueError("edges must be unique, non-self, with positive distance")
            adjacency[target] = distance
        by_id[cell] = node
        edges[cell] = adjacency
    for cell, adjacency in edges.items():
        for target, distance in adjacency.items():
            if target not in edges or edges[target].get(cell) != distance:
                raise ValueError("edges must have known reciprocal endpoints and equal distances")
    # Record ordering is representational, not accepted incidence authority.
    result = {field: snapshot[field] for field in ("contract", "topology_id", "metric_unit", "elevation_unit")}
    result["nodes"] = [copy.deepcopy(by_id[cell]) for cell in sorted(by_id)]
    for node in result["nodes"]:
        node["neighbors"].sort(key=lambda edge: edge["cell_id"])
    return result, edges


def _freeze(value):
    if type(value) is dict:
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if type(value) is list:
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value):
    if isinstance(value, MappingProxyType):
        return {key: _thaw(item) for key, item in value.items()}
    if type(value) is tuple:
        return [_thaw(item) for item in value]
    return value


class FrozenTopologyAdapter:
    """Validated private immutable copy with independently detached snapshots."""

    __slots__ = ("__topology",)

    def __init__(self, snapshot):
        topology, _ = _topology(snapshot)
        self.__topology = _freeze(topology)

    def snapshot(self) -> dict:
        return cast(dict, _thaw(self.__topology))


def _role(value, label):
    if type(value) is not str or value not in ("route", "storage_sink", "outlet"):
        raise ValueError(f"{label} must declare route, storage_sink, or outlet")
    return value


def _json_number(value):
    if value.denominator == 1:
        return value.numerator
    try:
        result = float(value)
    except OverflowError as exc:
        raise ValueError("effective potential exceeds finite JSON numeric range") from exc
    if not math.isfinite(result):
        raise ValueError("effective potential exceeds finite JSON numeric range")
    if Fraction(str(result)) != value:
        raise ValueError("effective potential cannot round-trip exactly through a JSON number")
    return result


def run_simulation(adapter: TopologyAdapter, policy, initial_water, rainfall_steps, *, embedding) -> dict:
    """Validate every input, then execute synchronous one-edge water steps."""
    snapshot_method = getattr(adapter, "snapshot", None)
    if not callable(snapshot_method):
        raise ValueError("adapter must expose snapshot()")
    topology, edges = _topology(snapshot_method())
    ids = sorted(edges)
    if type(policy) is not dict:
        raise ValueError("policy must be a dict")
    mode = policy.get("potential_mode")
    if mode not in ("declared", "gravity_coupled"):
        raise ValueError("unknown potential mode")
    potential_field = "potential_by_cell" if mode == "declared" else "gravity"
    _fields(policy, {"contract", "potential_mode", "potential_unit", "routing", "update_rule", "outlet_rule", "sink_rule", "roles", "loss_per_step", potential_field}, "policy")
    literals = {
        "contract": "trixel.terrain_physical_policy.v1",
        "routing": "steepest_descent_then_cell_id.v1",
        "update_rule": "synchronous_one_edge_per_step.v1",
        "outlet_rule": "discharge_all_after_loss.v1",
        "sink_rule": "retain_all_after_loss.v1",
    }
    for field, expected in literals.items():
        if policy[field] != expected:
            raise ValueError(f"unknown {field}")
    _text(policy["potential_unit"], "potential_unit")
    roles = _cell_map(policy["roles"], ids, _role, "roles")
    losses = _cell_map(policy["loss_per_step"], ids, _quantity, "loss_per_step")
    initial = _cell_map(initial_water, ids, _quantity, "initial_water")
    if type(rainfall_steps) is not list:
        raise ValueError("rainfall_steps must be a list")
    rain_schedule = [_cell_map(rain, ids, _quantity, "rainfall") for rain in rainfall_steps]
    positions = _cell_map(embedding, ids, _vector, "embedding")
    if mode == "declared":
        potentials = _cell_map(policy["potential_by_cell"], ids, _number, "potential_by_cell")
        effective = {cell: policy["potential_by_cell"][cell] for cell in ids}
    else:
        gravity = _vector(policy["gravity"], "gravity")
        if not any(gravity):
            raise ValueError("gravity must be nonzero")
        potentials = {cell: -sum((g * p for g, p in zip(gravity, positions[cell])), Fraction(0)) for cell in ids}
        effective = {cell: _json_number(potentials[cell]) for cell in ids}
    direction = dict.fromkeys(ids)
    for cell in ids:
        if roles[cell] == "route":
            candidates = [(target, (potentials[cell] - potentials[target]) / distance)
                          for target, distance in edges[cell].items()
                          if potentials[target] < potentials[cell]]
            if not candidates:
                raise ValueError(f"route cell {cell!r} has no strictly downhill declared neighbor")
            direction[cell] = min(candidates, key=lambda candidate: (-candidate[1], candidate[0]))[0]
    provenance = {"topology": topology, "policy": copy.deepcopy(policy),
                  "initial_water": initial.copy(), "rainfall_steps": copy.deepcopy(rain_schedule)}
    if mode == "gravity_coupled":
        provenance["embedding"] = copy.deepcopy(embedding)
    states = [initial.copy()]
    accumulated = dict.fromkeys(ids, 0)
    ledger = []
    totals = {"initial_water": sum(initial.values()), "rainfall": 0,
              "stored_water": sum(initial.values()), "boundary_discharge": 0,
              "declared_losses": 0}
    for step, rain in enumerate(rain_schedule, 1):
        before = states[-1]
        incoming = dict.fromkeys(ids, 0)
        rows = []
        for cell in ids:
            available = before[cell] + rain[cell]
            loss = min(losses[cell], available)
            remaining = available - loss
            outgoing = remaining if roles[cell] == "route" else 0
            discharge = remaining if roles[cell] == "outlet" else 0
            retained = remaining if roles[cell] == "storage_sink" else 0
            target = direction[cell]
            if target is not None:
                incoming[target] += outgoing
            rows.append({"step": step, "cell_id": cell, "water_before": before[cell],
                         "rainfall": rain[cell], "incoming_transfers": 0,
                         "outgoing_transfers": outgoing, "outgoing_to": target,
                         "declared_loss": loss, "water_after": retained,
                         "boundary_discharge": discharge})
            totals["rainfall"] += rain[cell]
            totals["declared_losses"] += loss
            totals["boundary_discharge"] += discharge
        after = {}
        for row in rows:
            cell = row["cell_id"]
            row["incoming_transfers"] = incoming[cell]
            row["water_after"] += incoming[cell]
            accumulated[cell] += incoming[cell]
            after[cell] = row["water_after"]
        ledger.extend(rows)
        states.append(after)
    totals["stored_water"] = sum(states[-1].values())
    materials = {
        cell: ("standing_water_candidate" if roles[cell] == "storage_sink" and states[-1][cell] > 0
               else "flow_affected_candidate" if accumulated[cell] > 0
               else "unchanged_candidate") for cell in ids
    }
    return {"contract": "trixel.terrain_state_result.v1", "topology_id": topology["topology_id"],
            "potential_by_cell": effective, "flow_direction": direction, "states": states,
            "ledger": ledger, "totals": totals, "accumulated_flow": accumulated,
            "candidate_materials": materials, "input_provenance": provenance}


def serialize_result(result) -> bytes:
    """Encode the canonical result without changing its values or list order."""
    return (json.dumps(result, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
