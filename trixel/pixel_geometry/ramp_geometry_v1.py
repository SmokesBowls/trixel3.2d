"""Ramp run/angle solver: pure geometry, no positions, no embedding.

This module answers the question a declared-angle ramp embedding must
answer BEFORE any geometry is built: given a straight chain of unit-metric
cells and a required vertical rise, what horizontal run and angle are
achievable WITHOUT stretching a single source cell?

The question is not "what angle looks right" -- angle is not a free
aesthetic choice here. A straight chain of N cells, each of intrinsic
length cell_metric, forms one straight line of total length
N*cell_metric between its two endpoints. Rotating that line never
stretches it (the same fact embedding_v1.embed_rigid already relies on),
so every (run, rise) pair reachable WITHOUT stretching lies exactly on
the circle:

    run^2 + rise^2 = (num_cells * cell_metric)^2

Given a required_rise, run and angle are therefore both DETERMINED, never
independently chosen. And the circle immediately gives the feasibility
law for free: no point on it has rise > num_cells*cell_metric, so a
required_rise beyond that is not a worse angle -- it is not on the circle
at all. The chain must gain more cells, or the rise must be split across
another fold, before this function can answer anything.
"""
from __future__ import annotations

import math
from typing import NamedTuple


class RampSolution(NamedTuple):
    angle_degrees: float
    run: float
    chain_length: float


def solve_ramp_run_and_angle(
    num_cells: int, required_rise: float, *, cell_metric: float = 1.0
) -> RampSolution:
    """The one function that must be called before any declared-angle ramp
    embedding runs. Returns the angle and run that reach EXACTLY
    required_rise across num_cells unit cells without stretching any of
    them, or raises ValueError (REJECT_EMBEDDING) if no such angle exists
    at this cell count -- the chain is geometrically too short for the
    requested rise, and the caller's only correct responses are to add
    cells or introduce another fold, never to force this fit."""
    if isinstance(num_cells, bool) or not isinstance(num_cells, int) or num_cells <= 0:
        raise ValueError(f"num_cells must be a positive integer, got {num_cells!r}")
    if cell_metric <= 0:
        raise ValueError(f"cell_metric must be positive, got {cell_metric!r}")
    if required_rise < 0:
        raise ValueError(f"required_rise must be non-negative, got {required_rise!r}")

    chain_length = num_cells * cell_metric
    if required_rise > chain_length:
        raise ValueError(
            f"REJECT_EMBEDDING: required_rise={required_rise} exceeds what {num_cells} "
            f"cells of metric {cell_metric} can reach ({chain_length}) without stretching "
            "-- add cells or introduce another fold, do not force this fit"
        )

    angle_radians = math.asin(required_rise / chain_length)
    run = math.sqrt(chain_length * chain_length - required_rise * required_rise)
    return RampSolution(angle_degrees=math.degrees(angle_radians), run=run, chain_length=chain_length)
