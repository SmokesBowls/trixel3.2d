# Terrain Handoff Disposition Manifest

This manifest documents the classification and architectural disposition of every file contained in the handoff bundle `/mnt/data-drive/terrain_contract_handoff` for the `trixel3.2d` repository.

## Manifest Details

| Handoff Path | Class | Action / Disposition | Target Path (if Promoted) |
| :--- | :--- | :--- | :--- |
| **`trixelcomposer/recipes/terrain/beach.tidal_flats.json`** | proven contract | Promoted | `recipes/terrain/beach.tidal_flats.json` |
| **`trixelcomposer/recipes/terrain/cave.dark_descent.json`** | proven contract | Promoted | `recipes/terrain/cave.dark_descent.json` |
| **`trixelcomposer/recipes/terrain/default.generic.json`** | proven contract | Promoted | `recipes/terrain/default.generic.json` |
| **`trixelcomposer/recipes/terrain/desert.arid_flats.json`** | proven contract | Promoted | `recipes/terrain/desert.arid_flats.json` |
| **`trixelcomposer/recipes/terrain/forest.dense_canopy.json`** | proven contract | Promoted | `recipes/terrain/forest.dense_canopy.json` |
| **`trixelcomposer/recipes/terrain/mountain.rocky_ridge.json`** | proven contract | Promoted | `recipes/terrain/mountain.rocky_ridge.json` |
| **`trixelcomposer/recipes/terrain/ocean.deep_current.json`** | proven contract | Promoted | `recipes/terrain/ocean.deep_current.json` |
| **`trixelcomposer/recipes/terrain/swamp.murky_bog.json`** | proven contract | Promoted | `recipes/terrain/swamp.murky_bog.json` |
| **`trixelcomposer/recipes/terrain/tundra.frozen_plain.json`** | proven contract | Promoted | `recipes/terrain/tundra.frozen_plain.json` |
| **`trixelcomposer/recipes/terrain/volcano.branching_lava.json`** | proven contract | Promoted | `recipes/terrain/volcano.branching_lava.json` |
| **`trixelcomposer/recipes/transitions/cliff_edge.json`** | proven contract | Promoted | `recipes/transitions/cliff_edge.json` |
| **`trixelcomposer/recipes/transitions/grass_to_dirt.json`** | proven contract | Promoted | `recipes/transitions/grass_to_dirt.json` |
| **`trixelcomposer/recipes/transitions/lava_to_ash.json`** | proven contract | Promoted | `recipes/transitions/lava_to_ash.json` |
| **`trixelcomposer/recipes/transitions/shoreline.json`** | proven contract | Promoted | `recipes/transitions/shoreline.json` |
| **`trixelcomposer/recipes/transitions/snow_to_rock.json`** | proven contract | Promoted | `recipes/transitions/snow_to_rock.json` |
| **`trixelcomposer/recipes/schema/trixel_recipe.schema.json`** | static doctrine lock | Promoted (scene_id optional) | `recipes/schema/trixel_recipe.schema.json` |
| **`trixelcomposer/recipes/schema/tile_address.schema.json`** | static doctrine lock | Promoted | `recipes/schema/tile_address.schema.json` |
| **`trixelcomposer/tile_address.py`** | proven contract | Quarantined | Already locally present |
| **`trixelcomposer/demand_resolver.py`** | runtime adapter | Archive / Unused | Not imported |
| **`terrain/terrain_material_mapping.py`** | proven contract | Archive / Unused | Not imported |
| **`terrain/terrain_surface_basis_contract.py`** | proven contract | Archive / Unused | Not imported |
| **`terrain/surface_basis_resolver.py`** | runtime adapter | Archive / Unused | Not imported |
| **`terrain/trixel_surface_painter_selector.py`** | runtime adapter | Archive / Unused | Not imported |
| **`terrain/trixel_retro_surface_paint_document.py`** | proven contract | Archive / Unused | Not imported |
| **`terrain/godot_projection_consumer_contract.py`** | render-only consumer | Archive / Unused | Not imported |
| **`terrain/projection_execution_plan.py`** | runtime adapter | Archive / Unused | Not imported |
| **`terrain/terrain_studio_import_contract.py`** | render-only consumer | Archive / Unused | Not imported |
| **`terrain/terrain_studio_biome_material_adapter.py`** | render-only consumer | Archive / Unused | Not imported |
| **`terrain/terrain_studio_height_adapter.py`** | render-only consumer | Archive / Unused | Not imported |
