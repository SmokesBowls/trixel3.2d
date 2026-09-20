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

## Doctrine and design locks

These documents preserve architectural rules that future implementation and proof work must not accidentally erase:

- [`docs/TRIXEL_SURFACE_CONSERVATION_AND_FOLDING_DOCTRINE_V1.md`](docs/TRIXEL_SURFACE_CONSERVATION_AND_FOLDING_DOCTRINE_V1.md)
  - formalizes **fold, do not stretch**
  - treats source artwork as finite visual material rather than infinitely elastic texture paint
  - unifies the original sprite/tile folding model with the larger printed-blanket-over-terrain model
  - defines surface demand, visual material supply, source attribution, prohibited silent stretching/duplication, and a candidate proof path
- [`docs/TRIXEL_PERCEPTUAL_PRESENTATION_DOCTRINE_UPDATE_V1.md`](docs/TRIXEL_PERCEPTUAL_PRESENTATION_DOCTRINE_UPDATE_V1.md)
  - separates structural authority from camera-dependent perceptual presentation
  - presentation may change how an accepted trixel is seen, but may not change what the trixel is

Doctrine documents are not claims that the corresponding runtime solver already exists. Proven runtime behavior remains limited to independently gated slices.

## Verify

```bash
PYTHONDONTWRITEBYTECODE=1 python3 trixel/gates/gate_worldfield_to_worldcell_projection_contract.py
PYTHONDONTWRITEBYTECODE=1 python3 trixel/gates/gate_global_sample_patch_contract.py
PYTHONDONTWRITEBYTECODE=1 python3 trixel/gates/gate_global_sample_field_contract.py
```

Each gate exits zero and ends with its own `[...][ALL_GATES] true/TRUE` line.
