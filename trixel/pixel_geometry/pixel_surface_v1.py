"""TrixelSurface: the editable 2D pixel-art authority bound to a
footprint's cell addresses.

Per user architecture correction (2026-09-22): a rendered atlas/texture
PNG must never be the authoritative visual object -- it is a disposable,
fully regenerable projection. Delete every generated image and this
module's data must be enough to rebuild it byte-for-byte. The authority
direction is:

    EDITABLE TRIXEL DATA (this module)
            -> compiled only ->
    derived render texture (tools/pixel_surface_render_v1.py, disposable)

never the reverse. This module never imports PIL and never reads or
writes an image file -- rendering lives entirely in a separate tool so
this file cannot become a texture-in/texture-out pipeline by accident. It
is pure, JSON-serializable data plus pure edit functions, the same
discipline addressing_v1.py and adjacency_v1.py already follow.

A TrixelSurface is addressed by the SAME cell addresses a pixel_geometry
footprint already declares (addressing_v1.cell_addresses) -- it carries
NO 3D information of its own. The same TrixelSurface can be handed to
multiple different embeddings of that footprint (flat, folded, raised)
simultaneously; editing it once must change every one of its embodiments
identically when re-rendered, since embedding never touches artwork,
exactly like embedding never touches payload or UV (embedding_v1.py's own
law, cited there to doctrine section 5.2).

Per-cell fields:
    density  -- int, trixels per side for this cell's tile (8, 16, 32,
                ...). Independent per cell in the data model -- this is
                what makes density a render parameter, never a geometry
                one. (tools/pixel_surface_render_v1.py's atlas compiler
                currently requires one shared density across all cells at
                render time -- see its own docstring for why per-cell
                mixed-density atlas packing remains a documented
                follow-up, not a limitation of this data model.)
    recipe   -- repo-relative path string to the recipe JSON that
                generates this cell's BASE artwork (provenance: "why does
                this cell look the way it does, before any edit" is
                always answerable).

Edits are stored as a list, each keyed by NORMALIZED fractional
cell-local position (u_frac, v_frac), each in [0.0, 1.0) -- deliberately
NOT a raw pixel index, so an edit survives a later density change instead
of becoming meaningless at a different resolution. edit_trixel_at_density
converts an explicit (px, py, at_density) address -- the way a human
naturally thinks about "this pixel" -- into that normalized form.
"""
from __future__ import annotations

import copy
from typing import Any

PIXEL_SURFACE_CONTRACT = "trixel.pixel_surface.v1"


def _cell_key(x: int, row: int) -> str:
    return f"{x},{row}"


def build_surface(
    footprint: dict[str, Any],
    *,
    default_density: int,
    recipe_by_cell: dict[tuple[int, int], str],
) -> dict[str, Any]:
    """A fresh TrixelSurface for every cell footprint declares. Every cell
    must have an assigned recipe or this raises -- there is no such thing
    as an unaddressed cell's artwork, matching EVERY_CELL_HAS_TOPOLOGY_
    DISPOSITION's completeness discipline elsewhere in this package."""
    width, height = footprint["width"], footprint["height"]
    cells: dict[str, Any] = {}
    for row in range(height):
        for x in range(width):
            addr = (x, row)
            if addr not in recipe_by_cell:
                raise ValueError(f"cell {addr} has no assigned recipe")
            cells[_cell_key(x, row)] = {"density": default_density, "recipe": str(recipe_by_cell[addr])}
    return {
        "contract": PIXEL_SURFACE_CONTRACT,
        "width": width,
        "height": height,
        "cells": cells,
        "edits": [],
    }


def validate_surface_structure(surface: dict[str, Any]) -> None:
    if surface.get("contract") != PIXEL_SURFACE_CONTRACT:
        raise ValueError("unsupported pixel surface contract")
    width, height = surface.get("width"), surface.get("height")
    if not isinstance(width, int) or not isinstance(height, int) or width <= 0 or height <= 0:
        raise ValueError("width/height must be positive ints")
    cells = surface.get("cells")
    if not isinstance(cells, dict):
        raise ValueError("cells must be a dict")
    for row in range(height):
        for x in range(width):
            key = _cell_key(x, row)
            if key not in cells:
                raise ValueError(f"cell {key} missing from surface -- every declared cell must be addressed")
            entry = cells[key]
            if not isinstance(entry.get("density"), int) or entry["density"] <= 0:
                raise ValueError(f"cell {key} has invalid density")
            if not isinstance(entry.get("recipe"), str):
                raise ValueError(f"cell {key} has invalid recipe")
    for edit in surface.get("edits", []):
        x, row = edit["cell_address"]
        if not (0 <= x < width and 0 <= row < height):
            raise ValueError(f"edit references out-of-domain cell {(x, row)}")
        if not (0.0 <= edit["u_frac"] < 1.0 and 0.0 <= edit["v_frac"] < 1.0):
            raise ValueError(f"edit at cell {(x, row)} has out-of-range fractional position")


def cell_density(surface: dict[str, Any], cell_address: tuple[int, int]) -> int:
    return surface["cells"][_cell_key(*cell_address)]["density"]


def cell_recipe(surface: dict[str, Any], cell_address: tuple[int, int]) -> str:
    return surface["cells"][_cell_key(*cell_address)]["recipe"]


def edits_for_cell(surface: dict[str, Any], cell_address: tuple[int, int]) -> list[dict[str, Any]]:
    x, row = cell_address
    return [e for e in surface["edits"] if tuple(e["cell_address"]) == (x, row)]


def set_cell_density(surface: dict[str, Any], cell_address: tuple[int, int], density: int) -> dict[str, Any]:
    """Pure: returns a new surface with one cell's density changed. Never
    touches recipe, edits, or any other cell -- density is purely a
    render-resolution parameter."""
    if density <= 0:
        raise ValueError("density must be positive")
    new_surface = copy.deepcopy(surface)
    new_surface["cells"][_cell_key(*cell_address)]["density"] = density
    return new_surface


def set_all_density(surface: dict[str, Any], density: int) -> dict[str, Any]:
    """Pure: bump every cell to the same density -- the whole-surface
    density change the identity proof exercises (8x8 -> 32x32)."""
    new_surface = copy.deepcopy(surface)
    for entry in new_surface["cells"].values():
        entry["density"] = density
    return new_surface


def edit_trixel_fractional(
    surface: dict[str, Any], cell_address: tuple[int, int], u_frac: float, v_frac: float, color: tuple[int, int, int]
) -> dict[str, Any]:
    """Pure: append one explicit pixel override to the surface's edit
    list, addressed by fractional cell-local position -- never a raw
    pixel index -- so it remains meaningful at any density this cell is
    later rendered at. Never touches geometry, embedding, or any other
    cell's data."""
    if not (0.0 <= u_frac < 1.0 and 0.0 <= v_frac < 1.0):
        raise ValueError("u_frac/v_frac must be in [0.0, 1.0)")
    new_surface = copy.deepcopy(surface)
    x, row = cell_address
    new_surface["edits"].append(
        {"cell_address": [x, row], "u_frac": u_frac, "v_frac": v_frac, "color": list(color)}
    )
    return new_surface


def edit_trixel_at_density(
    surface: dict[str, Any], cell_address: tuple[int, int], px: int, py: int, *, at_density: int, color: tuple[int, int, int]
) -> dict[str, Any]:
    """Convenience: the way a human names an edit ("trixel (3, 5) of an
    8x8 cell") converted into the density-independent fractional form
    edit_trixel_fractional actually stores."""
    if not (0 <= px < at_density and 0 <= py < at_density):
        raise ValueError(f"pixel ({px}, {py}) out of domain for density {at_density}")
    u_frac = (px + 0.5) / at_density
    v_frac = (py + 0.5) / at_density
    return edit_trixel_fractional(surface, cell_address, u_frac, v_frac, color)
