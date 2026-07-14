# Global-Sample Patch and Field Authority v1

Status: normative Trixel contract

Contract IDs:

- `trixel.global_sample_patch.v1`
- `trixel.global_sample_patch_field.v1`

## Ownership boundary

Trixel owns the generic patch language, canonical-top compiler, rectangular field assembler, global-address seam law, schemas, and fail-closed proof gates.

Domain consumers own elevation algorithms, terrain recipes, texture paths, fixtures, engine adapters, scenes, and screenshots. A domain name such as Pyroclast MUST NOT become part of the generic compiler or assembler.

Godot is a consumer of accepted packets. Godot rendering evidence does not become Trixel authority.

## Patch law

One patch has:

- 16x16 logical cells and one 16x16 logical artwork region;
- 17x17 cell-corner elevation samples;
- row-major serialization by local Z row, then local X column;
- 289 canonical top positions;
- 512 canonical top triangles;
- 1,536 canonical top indices.

The canonical counts apply to the top-surface contract, not to optional final render vertices created by normals, UV seams, materials, cliffs, or bottoms.

## Global address law

```text
global_sample_x = patch_x * 16 + local_sample_x
global_sample_z = patch_z * 16 + local_sample_z
sample_index = local_sample_z * 17 + local_sample_x
```

Local cells are bounded to `[0, 15]`; local samples are bounded to `[0, 16]`. Adjacent patch boundaries MUST resolve through the same global address. Two values for one global address are a contract failure.

## Field law

A rectangular field declares patch origin and dimensions. Cell dimensions, global sample dimensions, canonical topology counts, unique sample count, and neighbor-boundary count are derived, never caller-authored estimates.

Patch packets are independently regenerable from:

```text
patch address + shared elevation(global_sample_x, global_sample_z) + presentation references
```

No skirts, cliffs, bottoms, overlaps, hidden seam triangles, or post-generation edge repair are part of v1.

## Vendor boundary

Downstream repositories may vendor a pinned bundle. The bundle manifest MUST name its exact Trixel commit and tree plus SHA-256 for every exported file and an aggregate bundle SHA-256. Downstream integrity gates MUST fail closed on missing, added, removed, or modified bundle files.

Domain fixtures and engine evidence remain downstream and MUST NOT be promoted back into this neutral authority package.
