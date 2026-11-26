# trixel3.2d — Current State

Last updated: 2026-11-25. Branch `main`, remote `git@github.com:SmokesBowls/trixel3.2d.git`, all pushed. Code unchanged since `dffe13a` ("ready to wire in Engain almost", 2026-11-05); `7749c95` added these records.

## Role

Independent construction system. Receives explicit `trixel32d_surface_request.v1` drops and returns built surfaces. It authors no manuscript truth and grants no runtime authority.

## Seam to EngAIn (the only integration point)

- EngAIn's 8765 live route (`EngAIn/tier1/engainos/bridgeroom/trixel32d_live_route.py`) runs, as a subprocess:
  `python3 tools/consume_trixel32d_request_drop.py <request_drop_dir> <response_drop_dir> <expected_request_id>`
- In: `TRIXEL32D_SURFACE_REQUEST_DROP_V1.json` + `TRIXEL32D_SURFACE_REQUEST_PAYLOAD_V1.json`.
  Out: `TRIXEL32D_SURFACE_BUILT_DROP_V1.json` + `TRIXEL32D_SURFACE_BUILT_PAYLOAD_V1.json` (`trixel32d_surface_built.v1`, coordinate space `TRIXEL_LOCAL_Y_UP`).
- Recipes are resolved from `recipes/terrain/<recipe_id>.json`. EngAIn's WorldField `TERRAIN_TO_RECIPE` targets all exist here (verified by EngAIn `tier2/worldfield/tests`).
- No imports in either direction; no code in this repo changed during the EngAIn integration (OP_A–H04b).

## Geometry conventions confirmed by a real build (EngAIn OP_E)

Cell centre = right·(x−cx)·cell_width + forward·(y−cy)·cell_depth + up·round(elevation·max_height_layers), with right=+X, forward=−Z, up=+Y; one height layer = one unit along up. `max_height_layers` is `int()`ed. World-cell index space (`trixel32d_worldfield_to_worldcell_projection`) uses world_cell_z = +field_y: a different space from the built geometry.

## Recent own work

Fractional sub-cell geometry Phases A–D (`acf321e` … `fd39ff1`); terrain-state lane A contract + proof fixtures (`dffe13a`).
