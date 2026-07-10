COORDINATE_SEAM_LOCK_V2

Status: archaeology lock / next-build boundary
Scope: conductor terrain coordinate models and projection seam
Repository root observed: /home/mytruelove/Desktop/burdens_of_a_forgotten_past/conductor

Purpose

This lock preserves the proven coordinate meanings already present in the repo.
It does not invent a final terrain mesh bridge, does not reinterpret legacy files,
and does not collapse same-named y coordinates across lanes.

Confirmed coordinate models

1. WorldField / terrain grid model is 2D.

   Evidence:
   - terrain/world_field_nucleus.py defines Chunk as size * size float data.
   - Chunk.get_index(local_x, local_y) = local_y * size + local_x.
   - WorldField.get_chunk_key(world_x, world_y) chunks on two coordinates.
   - GodotWorldFieldBridge.handle_edit(world_x, world_y, ...) casts to grid_x, grid_y
     before applying WorldField operators.
   - dirty data exports chunk_key, data, and size.

   Lock:
   - In the WorldField lane, world_x/world_y are 2D substrate coordinates.
   - world_y in this lane means terrain-grid row/depth coordinate.
   - world_y in this lane is not vertical height.

2. TileAddress / world_cell model is 3D.

   Evidence:
   - surface_basis_resolver.py requires basis_packet.world_cell to be length-3.
   - the resolver treats world_cell as a 3D identity source before matching a 2D
     surface-painter selection.

   Lock:
   - In the world_cell lane, world_cell = (x, y, z).
   - y in this lane is vertical/up in the Y-up cell model.
   - This y must not be silently equated with WorldField world_y.

3. Godot projection space exists as a contract lane.

   Evidence:
   - terrain/godot_projection_consumer_contract.py sets CONTRACT_ID to
     terrain.godot_projection_consumer.v1.
   - ALLOWED_COORDINATE_SPACES includes both godot_y_up and worldfield_grid.
   - GodotProjectionConsumerPacket is documented as a projection-target contract
     for future Godot/render consumers.
   - The packet is display/projection-target only and non-authoritative.

   Lock:
   - godot_y_up and worldfield_grid are distinct named spaces.
   - The Godot projection consumer packet names target projection intent.
   - It does not execute projection, paint, render, mutate runtime/canon/AP/spawn,
     or reconcile WorldField elevation into world_cell height.

4. surface_basis_resolver already proves a live 3D-to-2D selection seam.

   Evidence:
   - surface_basis_resolver.py reads length-3 world_cell.
   - It maps world_cell[0] to world_x.
   - It maps world_cell[2] to world_z.
   - It matches selected surface entries where selected.x == world_x and
     selected.y == world_z.

   Lock:
   - Existing resolver behavior is horizontal-plane selection matching:

       world_cell.x -> 2D selection x
       world_cell.z -> 2D selection y

   - This is a projection seam from 3D cell identity to a 2D selection surface.
   - It is not proof that WorldField world_y already means vertical height.

5. Elevation-to-world-Y is not yet the proven bridge.

   Evidence:
   - WorldField stores normalized float terrain data in a 2D chunk substrate.
   - Existing projection contracts carry coordinate_space and projection intent.
   - Current code does not prove a final reconciler that consumes field_x,
     field_y, and elevation and emits world_cell.x, world_cell.y, world_cell.z
     through a finalized height_scale/cell_size mesh projection.

   Lock:
   - Normalized height/terrain data exists.
   - A final elevation-to-world-Y/world_cell.y reconciler is not yet proven by
     the inspected code.

Unresolved seam

WorldField 2D height field and TileAddress 3D world_cell coexist, but the repo
has not yet proven one final reconciler that says:

    field_x + field_y + elevation
    become
    world_cell.x + world_cell.z + world_cell.y

That reconciler is the next design/build target.

Next target name

    worldfield_to_worldcell_projection.v1

Rationale:

The seam is not only grid-to-Godot. It is:

    WorldField 2D substrate
    -> projected/reconciled into
    TileAddress 3D world_cell / Godot Y-up projection space

Do not name this target terrain_grid_payload.v1 yet. That name hides the harder
coordinate reconciliation and risks treating a grid payload as if it already were
the final projection contract.

Builder instruction

Do not collapse the two existing meanings of y.

In WorldField:

    world_y = 2D row/depth coordinate

In world_cell:

    y = vertical/up coordinate

The bridge must rename before converting:

    field_x
    field_y
    elevation

then, only inside the projection bridge:

    world_cell_x = field_x
    world_cell_z = field_y
    world_cell_y = elevation-derived layer/height

No existing file should be silently reinterpreted.

Boundary rules for worldfield_to_worldcell_projection.v1

MUST:
- accept or derive explicit field_x, field_y, and elevation terms before conversion;
- name the source coordinate space as worldfield_grid;
- name the target coordinate space as world_cell / godot_y_up as applicable;
- document whether elevation is normalized, layered, scaled, rounded, or sampled;
- fail closed if field_y is ambiguously treated as vertical y;
- preserve WorldField world_y as row/depth until the bridge boundary;
- preserve world_cell.y as vertical/up after the bridge boundary.

MUST NOT:
- rename WorldField world_y globally to height;
- reinterpret existing world_y call sites as vertical without a bridge;
- make GodotProjectionConsumerPacket authoritative;
- put raw heightData/floatData into the Godot projection consumer packet;
- treat surface_basis_resolver x/z selection matching as a full terrain mesh
  reconciler;
- move, delete, or silently rewrite existing terrain files as part of this lock.

Final invariant

Same token, different lane:

    WorldField world_y != world_cell.y

The only acceptable place to convert between them is an explicit projection bridge
that names field_x, field_y, elevation, world_cell_x, world_cell_z, and
world_cell_y before any consumer treats the result as 3D Y-up space.
