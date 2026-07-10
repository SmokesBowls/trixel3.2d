# trixel3.2d

Known-good rebuild island for the Trixel 3.2d pipeline.

Current proven slice:

- `worldfield_to_worldcell_projection.v1`
- WorldField 2D substrate coordinate bridge to 3D Y-up `world_cell`
- Explicit mapping:
  - `field_x -> world_cell_x`
  - `field_y -> world_cell_z`
  - `elevation -> world_cell_y via round(elevation * max_height_layers)`

This repo intentionally starts small. Files from the older pipeline should only be added when a failing proof identifies them as required.

## Verify

```bash
python3 -m py_compile conductor_building_blocks/terrain/worldfield_to_worldcell_projection.py trixel/gates/gate_worldfield_to_worldcell_projection_contract.py
python3 trixel/gates/gate_worldfield_to_worldcell_projection_contract.py
```

Expected final line:

```text
[WORLDFIELD_TO_WORLDCELL_PROJECTION][ALL_GATES] true
```
