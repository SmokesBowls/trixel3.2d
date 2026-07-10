PROVEN_SLICE_WORLD_FIELD_TO_WORLDCELL

Reserved candidate root:
/home/mytruelove/Desktop/burdens_of_a_forgotten_past/trixel3.2d

Source live/proof roots copied from:
/home/mytruelove/Desktop/burdens_of_a_forgotten_past/conductor
/home/mytruelove/Desktop/trixel_pipeline_repo_candidate

Status:
This is the first known-good island extracted from the larger trixel/conductor workspace.
It proves only worldfield_to_worldcell_projection.v1.
It is not the full trixel pipeline.
It does not prove renderer, mesh, Godot, surface basis integration, or Trixel family execution.

Proven rule:
field_x -> world_cell_x
field_y -> world_cell_z
elevation -> world_cell_y via round(elevation * max_height_layers)

Required public function:
conductor_building_blocks.terrain.worldfield_to_worldcell_projection.project_worldfield_cell_to_worldcell

Known-good minimal files:
- conductor_building_blocks/__init__.py
- conductor_building_blocks/terrain/__init__.py
- conductor_building_blocks/terrain/docs/COORDINATE_SEAM_LOCK_V2.md
- conductor_building_blocks/terrain/worldfield_to_worldcell_projection.py
- trixel/__init__.py
- trixel/gates/__init__.py
- trixel/gates/gate_worldfield_to_worldcell_projection_contract.py

Verification command:
python3 -m py_compile conductor_building_blocks/terrain/worldfield_to_worldcell_projection.py trixel/gates/gate_worldfield_to_worldcell_projection_contract.py && python3 trixel/gates/gate_worldfield_to_worldcell_projection_contract.py

Verification result:
[WORLDFIELD_TO_WORLDCELL_PROJECTION][ALL_GATES] true

Artifact hashes:
afcdb0a40ad0a830be2046ece8baee5da79b9ced1c5b46fd79d5c8885db549cf  conductor_building_blocks/terrain/docs/COORDINATE_SEAM_LOCK_V2.md
e054e817bbea1f6471fa1059d027c06ea81415180709cf161aaaf45d0aacbe90  conductor_building_blocks/terrain/worldfield_to_worldcell_projection.py
14ad4093be237e0741c510c3b03e6a2b5bd312bde9ae4fff06ae01e268571cd3  trixel/gates/gate_worldfield_to_worldcell_projection_contract.py
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  conductor_building_blocks/__init__.py
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  conductor_building_blocks/terrain/__init__.py
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  trixel/__init__.py
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  trixel/gates/__init__.py

Expansion rule:
Add files to this reserved candidate only when a failing proof identifies the missing dependency.
If a candidate proof fails, do not import the entire old family. Move the smallest required file or write a new seam/gate.

Archive rule:
Everything not required by passing proofs remains archive material until proven otherwise.
