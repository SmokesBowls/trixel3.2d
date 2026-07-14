# trixel3.2d

Known-good rebuild island for the Trixel 3.2d pipeline.

Current proven slices:

- `worldfield_to_worldcell_projection.v1`
  - WorldField 2D substrate coordinate bridge to 3D Y-up `world_cell`
  - Explicit mapping:
    - `field_x -> world_cell_x`
    - `field_y -> world_cell_z`
    - `elevation -> world_cell_y via round(elevation * max_height_layers)`
- `trixel.global_sample_patch.v1`
  - 16x16 logical cells, 17x17 authoritative cell-corner samples
  - exactly 289 canonical top positions, 512 triangles, and 1,536 indices
- `trixel.global_sample_patch_field.v1`
  - neutral rectangular field assembly from shared global X/Z sample addresses
  - fail-closed shared-address/value seam gates

This repo intentionally starts small. Files from the older pipeline should only be added when a failing proof identifies them as required.

## Verify

```bash
PYTHONDONTWRITEBYTECODE=1 python3 trixel/gates/gate_worldfield_to_worldcell_projection_contract.py
PYTHONDONTWRITEBYTECODE=1 python3 trixel/gates/gate_global_sample_patch_contract.py
PYTHONDONTWRITEBYTECODE=1 python3 trixel/gates/gate_global_sample_field_contract.py
```

Each gate exits zero and ends with its own `[...][ALL_GATES] true/TRUE` line.
