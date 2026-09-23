#!/usr/bin/env python3
"""Trixel Capability Courtyard: one composed scene, not a museum of test
cases.

Every piece below calls a FROZEN, already-proven production function
exactly as its own gate proved it -- this tool adds no new geometric
capability, no new production module, no new embedding math. It is pure
composition, using the same placement discipline (derive offsets from
declared geometry, never fit them afterward) established across all
twelve pixel_geometry gates.

Layout (world X = east(+)/west(-), world Z = north(-)/south(+)):

    NORTH TERRACE  Y=3.0                    (declared-angle ramp, rise 3.0,
         ^ north ramp (rotation=90)          integer, exact 3-4-5 triangle)
         |
    WEST WALL -- CENTRAL HUB (12x12, built ONCE) -- EAST RAMP (rotation=0)
    (hinge fold        |                                    -> EAST TERRACE
     + rigid 180)       v south ramp (rotation=270)
                   SOUTH TERRACE  Y=2.5      (fractional, via whole-artifact
                                              translation, never terrain-
                                              local elevation)

    Elsewhere in the courtyard, clear of everything above:
      - wrapped 8-sided pillar (closed cylindrical wrap, diagnostic strip)
      - rigid floor/wall reuse (one footprint, embed_flat + embed_rigid)
      - close-proximity exhibit (two independent strips, exact contact,
        no declared relationship)

Capabilities demonstrated, each by calling its own frozen function:
  embed_flat, embed_rigid, embed_hard_90_degree_hinge_fold,
  embed_cylindrical_closed_wrap, embed_declared_angle_ramp_fold,
  ramp_geometry_v1.solve_ramp_run_and_angle, trixel32d_surface_builder via
  consume_surface_request_packet (HEIGHT_FIELD_CONNECTED_SURFACE),
  terrain_ramp_integration_v1 (ramp_position_to_world, translate_built_
  geometry, terrain_attachment_edge / _x, verify_attachment_edges).

Taper is deliberately absent -- it crosses into topology mutation, which
this ladder has not yet earned.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from PIL import Image

from trixel.pixel_geometry.addressing_v1 import build_footprint, corner_index
from trixel.pixel_geometry.adjacency_v1 import compiled_adjacency_matches_source, no_proximity_derived_adjacency, source_adjacency
from trixel.pixel_geometry.artwork_mapping_v1 import footprint_corner_uvs
from trixel.pixel_geometry.compiler_v1 import compile_footprint, edge_lengths
from trixel.pixel_geometry.contracts_v1 import (
    EMBEDDING_CYLINDRICAL_CLOSED_WRAP,
    EMBEDDING_DECLARED_ANGLE_RAMP_FOLD,
    EMBEDDING_FLAT,
    EMBEDDING_HARD_90_DEGREE_HINGE_FOLD,
    EMBEDDING_RIGID,
)
from trixel.pixel_geometry.embedding_v1 import (
    embed_cylindrical_closed_wrap,
    embed_declared_angle_ramp_fold,
    embed_flat,
    embed_hard_90_degree_hinge_fold,
    embed_rigid,
)
from trixel.pixel_geometry.ramp_geometry_v1 import solve_ramp_run_and_angle
from trixel.pixel_geometry.terrain_ramp_integration_v1 import (
    ramp_position_to_world,
    terrain_attachment_edge,
    terrain_attachment_edge_x,
    translate_built_geometry,
    verify_attachment_edges,
)
from trixel.trixel32d_surface_consumer import consume_surface_request_packet

RECIPE_ROOT = REPO_ROOT / "recipes" / "terrain"
FIXTURES = REPO_ROOT / "fixtures" / "pixel_geometry"
TEXTURES = FIXTURES / "courtyard_textures"
OUT_OBJ = FIXTURES / "trixel_capability_courtyard.obj"
OUT_MANIFEST = FIXTURES / "trixel_capability_courtyard_manifest.json"

DIAGNOSTIC_ART = FIXTURES / "pixel_fold_diagnostic_16x16.png"

# Representative flat colors sampled from the REAL rendered recipes
# (trixel_recipe_renderer.py, unmodified) -- never invented by hand.
GRASS_COLOR = [0.141, 0.498, 0.125, 1.0]
DIRT_COLOR = [0.518, 0.482, 0.188, 1.0]
GAP_FILL_COLOR = [0.30, 0.28, 0.24, 1.0]

# --- Central hub -----------------------------------------------------------
HUB_COLUMNS = 12
HUB_ROWS = 12
HUB_CENTER = 5.5  # (0+11)/2 -- hub spans world -6..6 on both axes
DIRT_COLUMNS = {5, 6}  # north/south path
DIRT_ROWS = {5, 6}     # east path
MAX_HEIGHT_LAYERS = 3  # matches the north/east ramps' integer rise exactly

# --- North & East ramps (integer rise, exact 3-4-5 triangle) --------------
NE_FAR_SEGMENT_CELLS = 5
NE_REQUIRED_RISE = 3.0
HINGE_CORNER_X = 1
NE_RAMP_WIDTH = HINGE_CORNER_X + NE_FAR_SEGMENT_CELLS  # 6
PATH_WIDTH_CELLS = 2

# --- South ramp (fractional rise, reusing the fractional-rise proof's own
# worked example exactly) ---------------------------------------------------
S_FAR_SEGMENT_CELLS = 5
S_REQUIRED_RISE = 2.5


def solve_ne_ramp():
    return solve_ramp_run_and_angle(NE_FAR_SEGMENT_CELLS, NE_REQUIRED_RISE)


def solve_s_ramp():
    return solve_ramp_run_and_angle(S_FAR_SEGMENT_CELLS, S_REQUIRED_RISE)


def hub_edge_z(low: bool) -> float:
    if low:  # north edge (field_y = HUB_ROWS-1)
        return (HUB_CENTER - (HUB_ROWS - 1)) - 0.5
    return (HUB_CENTER - 0) + 0.5  # south edge (field_y = 0)


def hub_edge_x(high: bool) -> float:
    if high:  # east edge (field_x = HUB_COLUMNS-1)
        return ((HUB_COLUMNS - 1) - HUB_CENTER) + 0.5
    return (0 - HUB_CENTER) - 0.5  # west edge (field_x = 0)


def build_ramp_footprint(width: int) -> dict:
    payload = [["dirt_ramp" for _ in range(width)] for _ in range(PATH_WIDTH_CELLS)]
    return build_footprint(width, PATH_WIDTH_CELLS, payload)


def build_hub_request() -> dict[str, Any]:
    cells = []
    for field_y in range(HUB_ROWS):
        for field_x in range(HUB_COLUMNS):
            is_dirt = field_x in DIRT_COLUMNS or field_y in DIRT_ROWS
            cells.append(
                {
                    "field_x": field_x,
                    "field_y": field_y,
                    "elevation": 0.0,
                    "terrain": "dirt" if is_dirt else "grass",
                    "recipe": "default.generic",
                    "base_color": DIRT_COLOR if is_dirt else GRASS_COLOR,
                }
            )
    return _terrain_request("t32dreq_courtyard_hub", HUB_COLUMNS, HUB_ROWS, HUB_CENTER, HUB_CENTER, cells)


def _terrain_request(request_id: str, columns: int, rows: int, center_column: float, center_row: float, cells: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "packet_type": "trixel32d_surface_request",
        "identity": {
            "contract": "trixel32d_surface_request.v1",
            "packet_type": "trixel32d_surface_request",
            "request_id": request_id,
            "source_scene_id": "scene.trixel_capability_courtyard.001",
            "provenance": {
                "source_scene_id": "scene.trixel_capability_courtyard.001",
                "topology_artifact_id": "trixel_capability_courtyard.synthetic_field.001",
                "metric_layout_artifact_id": "trixel_capability_courtyard.metric.001",
            },
        },
        "coordinate_space": "WORLD_FIELD_GRID_TO_LOCAL_Y_UP",
        "up_axis_policy": "MUST_BE_STANDARD_Y_UP_IN_PRIMARY_DIRECTION",
        "orientation": {
            "basis_authority": "VECTORS",
            "field_axis_binding": {"field_x_increases_along": "RIGHT", "field_y_increases_along": "FORWARD"},
            "tolerance": 0.0001,
            "vectors": {"right": [1.0, 0.0, 0.0], "forward": [0.0, 0.0, -1.0], "up": [0.0, 1.0, 0.0]},
        },
        "construction": {"appearance_policy": "RECIPE_REFERENCE", "ordering": "ROW_MAJOR", "topology_policy": "HEIGHT_FIELD_CONNECTED_SURFACE"},
        "planar_config": {
            "field_coverage": "DENSE",
            "field_width_columns": columns,
            "field_height_rows": rows,
            "cell_width": 1.0,
            "cell_depth": 1.0,
            "center_column": center_column,
            "center_row": center_row,
        },
        "vertical_metric": {
            "granted_by": "cartographer",
            "vertical_measurement_rule": "ELEVATION_TIMES_MAX_HEIGHT_LAYERS",
            "unit": "meter",
            "max_height_layers": MAX_HEIGHT_LAYERS,
            "source_artifact_id": "trixel_capability_courtyard.metric.001",
        },
        "gap_fill": {
            "enabled": True,
            "mode": "CONNECTED_SLAB",
            "adjacency_policy": "SHARED_EDGE_STITCHED",
            "resolved_color": GAP_FILL_COLOR,
            "thickness_local_units": 0.5,
        },
        "pixel_field_data": cells,
    }


def _terrace_cells(columns: int, rows: int, dirt_cells: set[int], dirt_is_column: bool, elevation: float) -> list[dict[str, Any]]:
    cells = []
    for field_y in range(rows):
        for field_x in range(columns):
            is_dirt = (field_x in dirt_cells) if dirt_is_column else (field_y in dirt_cells)
            cells.append(
                {
                    "field_x": field_x,
                    "field_y": field_y,
                    "elevation": elevation,
                    "terrain": "dirt" if is_dirt else "grass",
                    "recipe": "default.generic",
                    "base_color": DIRT_COLOR if is_dirt else GRASS_COLOR,
                }
            )
    return cells


# --- North terrace: reuses the integer-rise control's own terrace shape ---
NORTH_COLUMNS, NORTH_ROWS = 8, 4
NORTH_DIRT_COLUMNS = {3, 4}
NORTH_CENTER_COLUMN = 3.5


def build_north() -> dict[str, Any]:
    solved = solve_ne_ramp()
    footprint = build_ramp_footprint(NE_RAMP_WIDTH)
    positions = embed_declared_angle_ramp_fold(footprint, hinge_corner_x=HINGE_CORNER_X, angle_degrees=solved.angle_degrees)
    path_x_offset = -1.0
    ramp_z_offset = hub_edge_z(low=True) + float(HINGE_CORNER_X)  # near edge lands on hub's north edge
    # Far edge world_z = -(hinge_corner_x+run) + ramp_z_offset; the hinge_corner_x
    # terms cancel exactly, leaving far_z = hub_edge_z(low=True) - run.
    terrace_center_row = (hub_edge_z(low=True) - solved.run) - 0.5
    cells = _terrace_cells(NORTH_COLUMNS, NORTH_ROWS, NORTH_DIRT_COLUMNS, True, elevation=1.0)
    request = _terrain_request("t32dreq_courtyard_north_terrace", NORTH_COLUMNS, NORTH_ROWS, NORTH_CENTER_COLUMN, terrace_center_row, cells)
    built = consume_surface_request_packet(request, recipe_root=RECIPE_ROOT)
    return {
        "footprint": footprint, "positions": positions, "solved": solved, "rotation_degrees": 90.0,
        "offset_kwargs": dict(path_x_offset=path_x_offset, ramp_z_offset=ramp_z_offset),
        "terrace_built": built, "terrace_request": request,
        "hub_edge": terrain_attachment_edge, "hub_edge_kwargs": dict(field_x_values=DIRT_COLUMNS, field_y=HUB_ROWS - 1, edge="low_z"),
        "terrace_edge_fn": terrain_attachment_edge, "terrace_edge_kwargs": dict(field_x_values=NORTH_DIRT_COLUMNS, field_y=0, edge="high_z"),
    }


# --- East terrace: reuses the rotated proof's own transposed terrace shape -
EAST_COLUMNS, EAST_ROWS = 4, 8
EAST_DIRT_ROWS = {3, 4}
EAST_CENTER_ROW = 3.5


def build_east() -> dict[str, Any]:
    solved = solve_ne_ramp()  # identical worked example to north -- "same ramp implementation, rotated"
    footprint = build_ramp_footprint(NE_RAMP_WIDTH)
    positions = embed_declared_angle_ramp_fold(footprint, hinge_corner_x=HINGE_CORNER_X, angle_degrees=solved.angle_degrees)
    ramp_z_offset = -1.0
    path_x_offset = hub_edge_x(high=True) - float(HINGE_CORNER_X)
    # Far edge world_x = (hinge_corner_x+run) + path_x_offset; the hinge_corner_x
    # terms cancel exactly, leaving far_x = hub_edge_x(high=True) + run.
    terrace_center_column = -(hub_edge_x(high=True) + solved.run) - 0.5
    cells = _terrace_cells(EAST_COLUMNS, EAST_ROWS, EAST_DIRT_ROWS, False, elevation=1.0)
    request = _terrain_request("t32dreq_courtyard_east_terrace", EAST_COLUMNS, EAST_ROWS, terrace_center_column, EAST_CENTER_ROW, cells)
    built = consume_surface_request_packet(request, recipe_root=RECIPE_ROOT)
    return {
        "footprint": footprint, "positions": positions, "solved": solved, "rotation_degrees": 0.0,
        "offset_kwargs": dict(path_x_offset=path_x_offset, ramp_z_offset=ramp_z_offset),
        "terrace_built": built, "terrace_request": request,
        "hub_edge": terrain_attachment_edge_x, "hub_edge_kwargs": dict(field_y_values=DIRT_ROWS, field_x=HUB_COLUMNS - 1, edge="high_x"),
        "terrace_edge_fn": terrain_attachment_edge_x, "terrace_edge_kwargs": dict(field_y_values=EAST_DIRT_ROWS, field_x=0, edge="low_x"),
    }


# --- South terrace: fractional rise via whole-artifact translation --------
SOUTH_COLUMNS, SOUTH_ROWS = 8, 4
SOUTH_DIRT_COLUMNS = {3, 4}
SOUTH_CENTER_COLUMN = 3.5
SOUTH_CENTER_ROW = (SOUTH_ROWS - 1) + 0.5  # "natural" placement, matching the fractional-rise proof's own pattern


def build_south() -> dict[str, Any]:
    solved = solve_s_ramp()
    footprint = build_ramp_footprint(S_FAR_SEGMENT_CELLS + HINGE_CORNER_X)
    rotation_degrees = 270.0
    # theta=270: world_x = -ramp_z + offset_x ; world_z = ramp_x + offset_z
    positions = embed_declared_angle_ramp_fold(footprint, hinge_corner_x=HINGE_CORNER_X, angle_degrees=solved.angle_degrees)
    path_x_offset = 1.0  # r=0 -> world_x=+1, r=2 -> world_x=-1: same [-1,1] interval, reversed order
    ramp_z_offset = hub_edge_z(low=False) - float(HINGE_CORNER_X)  # near edge lands on hub's south edge

    # Build the terrace in its own "natural" (untranslated) local frame --
    # same shape/placement pattern as the north terrace's own construction,
    # at elevation 0.0 (terrain-local height authority never sees 2.5).
    cells = _terrace_cells(SOUTH_COLUMNS, SOUTH_ROWS, SOUTH_DIRT_COLUMNS, True, elevation=0.0)
    natural_request = _terrain_request("t32dreq_courtyard_south_terrace", SOUTH_COLUMNS, SOUTH_ROWS, SOUTH_CENTER_COLUMN, SOUTH_CENTER_ROW, cells)
    natural_built = consume_surface_request_packet(natural_request, recipe_root=RECIPE_ROOT)

    # Ramp's far edge world Z (constant across the edge -- the fold never
    # touches the r/width component, so ramp_x, and therefore world_z =
    # ramp_x + ramp_z_offset, is the same for every corner on that edge).
    far_z = (float(HINGE_CORNER_X) + solved.run) + ramp_z_offset
    far_y = S_REQUIRED_RISE

    # X needs NO shift: the ramp's width span (r=0..2 with path_x_offset=1.0
    # covers world X in [-1, 1], same interval as the terrace's own natural
    # dirt-column span at CENTER_COLUMN=3.5) already matches the terrace's
    # own natural placement exactly, just as reusing the hub's own
    # CENTER_COLUMN needed no shift in the hub proof.
    #
    # South travels toward +Z (away from the hub), the OPPOSITE direction
    # from north's -Z travel. The attachment edge must therefore be the
    # terrace's LOW-Z edge (its closest-to-hub side), not high-Z as north
    # uses -- using high-Z here would make the terrace's own body extend
    # BACKWARD toward the hub, overlapping the ramp's own climb, instead of
    # continuing further south past the attachment point.
    natural_low_z = SOUTH_CENTER_ROW - (SOUTH_ROWS - 1) - 0.5
    shift = (0.0, far_y - 0.0, far_z - natural_low_z)
    terrace_built = translate_built_geometry(natural_built, shift)

    return {
        "footprint": footprint, "positions": positions, "solved": solved, "rotation_degrees": rotation_degrees,
        "offset_kwargs": dict(path_x_offset=path_x_offset, ramp_z_offset=ramp_z_offset),
        "terrace_built": terrace_built, "terrace_request": natural_request, "shift": shift,
        "hub_edge": terrain_attachment_edge, "hub_edge_kwargs": dict(field_x_values=DIRT_COLUMNS, field_y=0, edge="high_z"),
        "terrace_edge_fn": terrain_attachment_edge,
        "terrace_edge_kwargs": dict(field_x_values=SOUTH_DIRT_COLUMNS, field_y=SOUTH_ROWS - 1, edge="low_z"),
    }


# --- West retaining wall: hinge fold + rigid 180-degree reorientation -----
WALL_HINGE_CORNER_X = 1
WALL_FACE_DEPTH = 2
WALL_WIDTH = WALL_HINGE_CORNER_X + WALL_FACE_DEPTH  # 3
WALL_LENGTH = HUB_ROWS  # spans the hub's full north-south extent


def build_west_wall() -> dict[str, Any]:
    payload = [["stone_wall" for _ in range(WALL_WIDTH)] for _ in range(WALL_LENGTH)]
    footprint = build_footprint(WALL_WIDTH, WALL_LENGTH, payload)
    folded = embed_hard_90_degree_hinge_fold(footprint, hinge_corner_x=WALL_HINGE_CORNER_X)
    # Rotate 180 degrees about Z: (x,y,z) -> (-x,-y,z) -- a proper rotation
    # (determinant +1), never a reflection, so winding/handedness survive.
    # This both turns the fold's default upward face into a downward-hanging
    # one (Y flips) AND reverses which way the cap extends (X flips), so the
    # cap runs AWAY from the hub (into more negative X) instead of back into
    # it. The length axis (Z, matching the hub's north-south span) is
    # untouched by a Z-axis rotation.
    reoriented = embed_rigid(folded, rotation_axis="z", rotation_degrees=180.0)
    translate = (hub_edge_x(high=False), 0.0, hub_edge_z(low=True))
    positions = {addr: tuple(p[i] + translate[i] for i in range(3)) for addr, p in reoriented.items()}
    return {"footprint": footprint, "positions": positions, "translate": translate}


# --- Rigid floor/wall reuse: the exact same small footprint, twice --------
DEMO_SIZE = 3


def build_floor_wall_demo() -> dict[str, Any]:
    payload = [["demo_stone" for _ in range(DEMO_SIZE)] for _ in range(DEMO_SIZE)]
    footprint = build_footprint(DEMO_SIZE, DEMO_SIZE, payload)  # ONE footprint object, used twice below

    floor_local = embed_flat(footprint)
    floor_translate = (-11.0, 0.0, 8.0)
    floor_positions = embed_rigid(floor_local, translation=floor_translate)

    wall_local = embed_flat(footprint)
    wall_rotated = embed_rigid(wall_local, rotation_axis="x", rotation_degrees=90.0, translation=(-11.0, 0.0, 8.0 + float(DEMO_SIZE)))
    return {"footprint": footprint, "floor_positions": floor_positions, "wall_positions": wall_rotated}


# --- Wrapped pillar: 8-sided closed cylindrical wrap, diagnostic strip ----
PILLAR_SIDES = 8
PILLAR_HEIGHT_CELLS = 4
PILLAR_CENTER = (17.0, 0.0, -6.0)  # clear of the east terrace (X:[10,14], Z:[-4,4])


def build_pillar() -> dict[str, Any]:
    payload = [["pillar" for _ in range(PILLAR_SIDES)] for _ in range(PILLAR_HEIGHT_CELLS)]
    footprint = build_footprint(PILLAR_SIDES, PILLAR_HEIGHT_CELLS, payload)
    local = embed_cylindrical_closed_wrap(footprint)
    # embed_cylindrical_closed_wrap's own local frame puts the circular wrap
    # in (X,Y) and the pillar's HEIGHT along local Z -- lying on its side.
    # Rotate -90 (270) about X: (x,y,z) -> (x, z, -y), a proper rotation, so
    # the height axis becomes world Y (standing up) and the circular
    # footprint becomes the ground-plane (X,Z) cross-section.
    standing = embed_rigid(local, rotation_axis="x", rotation_degrees=270.0)
    positions = {addr: (p[0] + PILLAR_CENTER[0], p[1] + PILLAR_CENTER[1], p[2] + PILLAR_CENTER[2]) for addr, p in standing.items()}
    return {"footprint": footprint, "positions": positions}


# --- Close-proximity exhibit: two strips, exact contact, no relationship --
EXHIBIT_ORIGIN = (-13.0, 0.0, 12.0)


def build_proximity_exhibit() -> dict[str, Any]:
    footprint_a = build_ramp_footprint(NE_RAMP_WIDTH)
    solved_a = solve_ne_ramp()
    positions_a_local = embed_declared_angle_ramp_fold(footprint_a, hinge_corner_x=HINGE_CORNER_X, angle_degrees=solved_a.angle_degrees)
    offsets_a = dict(path_x_offset=-1.0 + EXHIBIT_ORIGIN[0], ramp_z_offset=1.0 + EXHIBIT_ORIGIN[2])

    footprint_b = build_ramp_footprint(NE_RAMP_WIDTH)
    solved_b = solve_ne_ramp()
    positions_b_local = embed_declared_angle_ramp_fold(footprint_b, hinge_corner_x=HINGE_CORNER_X, angle_degrees=solved_b.angle_degrees)
    offsets_b = dict(path_x_offset=-1.0 + EXHIBIT_ORIGIN[0], ramp_z_offset=-1.0 + EXHIBIT_ORIGIN[2])

    return {
        "footprint_a": footprint_a, "positions_a": positions_a_local, "rotation_a": 90.0, "offsets_a": offsets_a,
        "footprint_b": footprint_b, "positions_b": positions_b_local, "rotation_b": 0.0, "offsets_b": offsets_b,
    }


def build_scene() -> dict[str, Any]:
    hub_built = consume_surface_request_packet(build_hub_request(), recipe_root=RECIPE_ROOT)
    north = build_north()
    south = build_south()
    east = build_east()
    wall = build_west_wall()
    floor_wall_demo = build_floor_wall_demo()
    pillar = build_pillar()
    exhibit = build_proximity_exhibit()

    return {
        "hub_built": hub_built,
        "north": north, "south": south, "east": east,
        "wall": wall, "floor_wall_demo": floor_wall_demo, "pillar": pillar, "exhibit": exhibit,
    }


# --- OBJ export -------------------------------------------------------------

WALL_TEXTURE = TEXTURES / "stone_16x16.png"
DEMO_TEXTURE = TEXTURES / "cracked_rock_16x16.png"
EXHIBIT_A_COLOR = [0.55, 0.35, 0.20, 1.0]
EXHIBIT_B_COLOR = [0.20, 0.35, 0.55, 1.0]


class ObjWriter:
    def __init__(self) -> None:
        self.lines: list[str] = []
        self.vertex_offset = 1
        self.uv_offset = 1
        self.face_blocks: list[tuple[str, list[str]]] = []

    def add_terrain(self, built: dict[str, Any]) -> None:
        positions = built["geometry"]["positions"]
        for pos in positions:
            self.lines.append(f"v {pos[0]} {pos[1]} {pos[2]}")
        base = self.vertex_offset
        for cell_range in built["cell_geometry_ranges"]:
            material = "dirt_flat" if cell_range["terrain"] == "dirt" else "grass_flat"
            for surface in cell_range["surfaces"]:
                mat = material if surface["role"] == "PRIMARY_PIXEL_FACE" else "gap_fill_flat"
                start = surface["vertex_start"]
                quad = [base + start, base + start + 1, base + start + 2, base + start + 3]
                self.face_blocks.append((mat, [f"{quad[0]} {quad[1]} {quad[2]}", f"{quad[1]} {quad[3]} {quad[2]}"]))
        self.vertex_offset += len(positions)

    def add_flat_ramp(self, footprint: dict, positions: dict, *, rotation_degrees: float, offset_kwargs: dict, hinge_corner_x: int, material: str) -> None:
        width = footprint["width"]
        ordered = sorted(positions, key=lambda addr: corner_index(addr[0], addr[1], width))
        index = {addr: self.vertex_offset + i for i, addr in enumerate(ordered)}
        for addr in ordered:
            world = ramp_position_to_world(positions[addr], rotation_degrees=rotation_degrees, **offset_kwargs)
            self.lines.append(f"v {world[0]} {world[1]} {world[2]}")
        compiled = compile_footprint(footprint, positions, embedding_id=EMBEDDING_DECLARED_ANGLE_RAMP_FOLD)
        for prov in compiled["primitive_provenance"]:
            if prov["cell_address"][0] < hinge_corner_x:
                continue
            start = prov["primitive_start"] * 3
            tri_a = compiled["indices"][start : start + 3]
            tri_b = compiled["indices"][start + 3 : start + 6]
            for tri in (tri_a, tri_b):
                verts = [index[ordered[i]] for i in tri]
                self.face_blocks.append((material, [f"{verts[0]} {verts[1]} {verts[2]}"]))
        self.vertex_offset += len(ordered)

    def add_textured_footprint(
        self, footprint: dict, positions: dict, *, embedding_id: str, material: str, exclude_stub_below: int | None = None
    ) -> None:
        width = footprint["width"]
        ordered = sorted(positions, key=lambda addr: corner_index(addr[0], addr[1], width))
        vindex = {addr: self.vertex_offset + i for i, addr in enumerate(ordered)}
        uvindex = {addr: self.uv_offset + i for i, addr in enumerate(ordered)}
        for addr in ordered:
            p = positions[addr]
            self.lines.append(f"v {p[0]} {p[1]} {p[2]}")
        uv_map = footprint_corner_uvs(footprint)
        for addr in ordered:
            u, v = uv_map[addr]
            self.lines.append(f"vt {u} {v}")
        compiled = compile_footprint(footprint, positions, embedding_id=embedding_id)
        faces: list[str] = []
        for prov in compiled["primitive_provenance"]:
            if exclude_stub_below is not None and prov["cell_address"][0] < exclude_stub_below:
                continue
            start = prov["primitive_start"] * 3
            for tri in (compiled["indices"][start : start + 3], compiled["indices"][start + 3 : start + 6]):
                refs = " ".join(f"{vindex[ordered[i]]}/{uvindex[ordered[i]]}" for i in tri)
                faces.append(refs)
        self.face_blocks.append((material, faces))
        self.vertex_offset += len(ordered)
        self.uv_offset += len(ordered)

    def write(self, out_path: Path, mtl_name: str, *, object_name: str = "trixel_capability_courtyard") -> None:
        lines = [f"mtllib {mtl_name}", f"o {object_name}"] + self.lines
        for material, faces in self.face_blocks:
            lines.append(f"usemtl {material}")
            for face in faces:
                lines.append(f"f {face}")
        out_path.write_text("\n".join(lines) + "\n")


# --- Per-piece OBJ export (one file per piece, for .blend assembly) --------

PARTS_DIR = FIXTURES / "courtyard_parts"


def export_pieces(scene: dict[str, Any], out_dir: Path = PARTS_DIR) -> dict[str, Path]:
    """Write each courtyard piece as its OWN OBJ file (sharing one .mtl),
    so a downstream Blender assembly script can import them as separate,
    identifiable objects instead of one fused mesh."""
    out_dir.mkdir(parents=True, exist_ok=True)
    mtl_path = out_dir / "courtyard_parts.mtl"
    write_mtl(mtl_path)

    paths: dict[str, Path] = {}

    def write_piece(name: str, build: "callable[[ObjWriter], None]") -> None:
        writer = ObjWriter()
        build(writer)
        out_path = out_dir / f"{name}.obj"
        writer.write(out_path, mtl_path.name, object_name=name)
        paths[name] = out_path

    write_piece("hub", lambda w: w.add_terrain(scene["hub_built"]))

    for prefix in ("north", "south", "east"):
        spec = scene[prefix]
        write_piece(
            f"{prefix}_ramp",
            lambda w, spec=spec: w.add_flat_ramp(
                spec["footprint"], spec["positions"], rotation_degrees=spec["rotation_degrees"],
                offset_kwargs=spec["offset_kwargs"], hinge_corner_x=HINGE_CORNER_X, material="dirt_flat",
            ),
        )
        write_piece(f"{prefix}_terrace", lambda w, spec=spec: w.add_terrain(spec["terrace_built"]))

    wall = scene["wall"]
    write_piece(
        "west_wall",
        lambda w: w.add_textured_footprint(wall["footprint"], wall["positions"], embedding_id=EMBEDDING_HARD_90_DEGREE_HINGE_FOLD, material="wall_stone"),
    )

    demo = scene["floor_wall_demo"]
    write_piece(
        "floor_demo",
        lambda w: w.add_textured_footprint(demo["footprint"], demo["floor_positions"], embedding_id=EMBEDDING_FLAT, material="demo_stone"),
    )
    write_piece(
        "wall_demo",
        lambda w: w.add_textured_footprint(demo["footprint"], demo["wall_positions"], embedding_id=EMBEDDING_RIGID, material="demo_stone"),
    )

    pillar = scene["pillar"]
    write_piece(
        "pillar",
        lambda w: w.add_textured_footprint(pillar["footprint"], pillar["positions"], embedding_id=EMBEDDING_CYLINDRICAL_CLOSED_WRAP, material="pillar_diagnostic"),
    )

    exhibit = scene["exhibit"]
    ex_a_positions = {addr: ramp_position_to_world(p, rotation_degrees=exhibit["rotation_a"], **exhibit["offsets_a"]) for addr, p in exhibit["positions_a"].items()}
    ex_b_positions = {addr: ramp_position_to_world(p, rotation_degrees=exhibit["rotation_b"], **exhibit["offsets_b"]) for addr, p in exhibit["positions_b"].items()}
    write_piece(
        "exhibit_a",
        lambda w: w.add_flat_ramp(exhibit["footprint_a"], ex_a_positions, rotation_degrees=0.0, offset_kwargs={"path_x_offset": 0.0, "ramp_z_offset": 0.0}, hinge_corner_x=HINGE_CORNER_X, material="exhibit_a_flat"),
    )
    write_piece(
        "exhibit_b",
        lambda w: w.add_flat_ramp(exhibit["footprint_b"], ex_b_positions, rotation_degrees=0.0, offset_kwargs={"path_x_offset": 0.0, "ramp_z_offset": 0.0}, hinge_corner_x=HINGE_CORNER_X, material="exhibit_b_flat"),
    )

    return paths


def write_mtl(mtl_path: Path) -> None:
    """Write the shared .mtl at `mtl_path`, computing each texture's
    map_Kd path RELATIVE TO WHEREVER mtl_path ACTUALLY IS -- never a
    hardcoded relative string -- so the same function works whether it is
    called for the combined courtyard OBJ (in fixtures/pixel_geometry/)
    or the per-piece OBJs (in fixtures/pixel_geometry/courtyard_parts/)."""
    import os

    mtl_dir = mtl_path.parent
    lines = []
    for name, color in (("grass_flat", GRASS_COLOR), ("dirt_flat", DIRT_COLOR), ("gap_fill_flat", GAP_FILL_COLOR)):
        lines += [f"newmtl {name}", f"Kd {color[0]} {color[1]} {color[2]}", "illum 1"]
    for name, color in (("exhibit_a_flat", EXHIBIT_A_COLOR), ("exhibit_b_flat", EXHIBIT_B_COLOR)):
        lines += [f"newmtl {name}", f"Kd {color[0]} {color[1]} {color[2]}", "illum 1"]
    for name, texture_path in (("wall_stone", WALL_TEXTURE), ("demo_stone", DEMO_TEXTURE), ("pillar_diagnostic", DIAGNOSTIC_ART)):
        rel = os.path.relpath(texture_path, start=mtl_dir)
        lines += [f"newmtl {name}", "Kd 1.0 1.0 1.0", "illum 1", f"map_Kd {rel}"]
    mtl_path.write_text("\n".join(lines) + "\n")


def _write_obj(scene: dict[str, Any]) -> None:
    writer = ObjWriter()

    writer.add_terrain(scene["hub_built"])
    for name in ("north", "south", "east"):
        spec = scene[name]
        writer.add_flat_ramp(
            spec["footprint"], spec["positions"], rotation_degrees=spec["rotation_degrees"],
            offset_kwargs=spec["offset_kwargs"], hinge_corner_x=HINGE_CORNER_X, material="dirt_flat",
        )
        writer.add_terrain(spec["terrace_built"])

    wall = scene["wall"]
    writer.add_textured_footprint(wall["footprint"], wall["positions"], embedding_id=EMBEDDING_HARD_90_DEGREE_HINGE_FOLD, material="wall_stone")

    demo = scene["floor_wall_demo"]
    writer.add_textured_footprint(demo["footprint"], demo["floor_positions"], embedding_id=EMBEDDING_FLAT, material="demo_stone")
    writer.add_textured_footprint(demo["footprint"], demo["wall_positions"], embedding_id=EMBEDDING_RIGID, material="demo_stone")

    pillar = scene["pillar"]
    writer.add_textured_footprint(pillar["footprint"], pillar["positions"], embedding_id=EMBEDDING_CYLINDRICAL_CLOSED_WRAP, material="pillar_diagnostic")

    exhibit = scene["exhibit"]
    ex_a_positions = {addr: ramp_position_to_world(p, rotation_degrees=exhibit["rotation_a"], **exhibit["offsets_a"]) for addr, p in exhibit["positions_a"].items()}
    ex_b_positions = {addr: ramp_position_to_world(p, rotation_degrees=exhibit["rotation_b"], **exhibit["offsets_b"]) for addr, p in exhibit["positions_b"].items()}
    writer.add_flat_ramp(exhibit["footprint_a"], ex_a_positions, rotation_degrees=0.0, offset_kwargs={"path_x_offset": 0.0, "ramp_z_offset": 0.0}, hinge_corner_x=HINGE_CORNER_X, material="exhibit_a_flat")
    writer.add_flat_ramp(exhibit["footprint_b"], ex_b_positions, rotation_degrees=0.0, offset_kwargs={"path_x_offset": 0.0, "ramp_z_offset": 0.0}, hinge_corner_x=HINGE_CORNER_X, material="exhibit_b_flat")

    mtl_path = OUT_OBJ.with_suffix(".mtl")
    write_mtl(mtl_path)
    writer.write(OUT_OBJ, mtl_path.name)


def main() -> int:
    scene = build_scene()
    for label, built in (
        ("hub", scene["hub_built"]),
        ("north_terrace", scene["north"]["terrace_built"]),
        ("south_terrace", scene["south"]["terrace_built"]),
        ("east_terrace", scene["east"]["terrace_built"]),
    ):
        if built.get("status") != "BUILT":
            print(f"terrain build failed for {label}:", built.get("errors"))
            return 1

    FIXTURES.mkdir(parents=True, exist_ok=True)
    _write_obj(scene)
    piece_paths = export_pieces(scene)
    print(f"wrote {len(piece_paths)} per-piece OBJs to {PARTS_DIR}")

    manifest = {
        "hub": {"columns": HUB_COLUMNS, "rows": HUB_ROWS},
        "north": {"far_segment_cells": NE_FAR_SEGMENT_CELLS, "required_rise": NE_REQUIRED_RISE, "angle_degrees": scene["north"]["solved"].angle_degrees, "run": scene["north"]["solved"].run},
        "south": {"far_segment_cells": S_FAR_SEGMENT_CELLS, "required_rise": S_REQUIRED_RISE, "angle_degrees": scene["south"]["solved"].angle_degrees, "run": scene["south"]["solved"].run, "shift": list(scene["south"]["shift"])},
        "east": {"far_segment_cells": NE_FAR_SEGMENT_CELLS, "required_rise": NE_REQUIRED_RISE, "angle_degrees": scene["east"]["solved"].angle_degrees, "run": scene["east"]["solved"].run},
        "pillar": {"sides": PILLAR_SIDES, "height_cells": PILLAR_HEIGHT_CELLS},
        "obj": OUT_OBJ.name,
    }
    OUT_MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"wrote {OUT_OBJ}")
    print(f"wrote {OUT_MANIFEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
