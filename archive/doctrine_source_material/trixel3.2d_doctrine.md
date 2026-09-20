
3 is because its 3d... .2 is because its 2d pixel art making   3.2d
2 is because its 2d... .5 is because it has a one sided z axis making   2.5d


Yes. That is the architectural shift.
    
    Trixel is not a mesh-deformation system.
    
    Trixel is a pixel-geometry compiler.
    
    The crucial distinction is:
    
    text
    Blender:
    existing geometry → deformation → visually acceptable geometry
    
    Trixel:
    source pixels → explicit topology decisions → attributable geometry
    
    
    Blender answers:
    
    text
    Where should these existing vertices move?
    
    
    Trixel must answer:
    
    text
    What geometry does this pixel own?
    Why does that geometry exist?
    What happens to that ownership when the form changes?
    
    
    One important refinement
    
    “Preserve the identity of every pixel” should not necessarily mean:
    
    text
    one source pixel == one final quad forever
    
    
    That would make tapering, branching, caps, collisions, and topology transitions impossible without distortion.
    
    The stronger and more useful contract is:
    
    text
    Every source pixel must have an explicit geometric disposition.
    Every generated geometric element must have traceable source-pixel provenance.
    
    
    A source pixel’s disposition might be:
    
    text
    PRESERVED_1_TO_1
    MERGED
    SPLIT
    CULLED
    OCCLUDED
    CAP_CONTRIBUTOR
    TRANSITION_CONTRIBUTOR
    
    
    Therefore, if the trunk narrows, the compiler cannot silently squeeze pixels through a modifier. It must emit an explicit topology decision:
    
    text
    pixel 12 preserved as cell 12
    pixel 13 merged with pixel 12
    pixel 14 removed by taper rule
    
    
    That preserves identity as provenance even where one-to-one geometry cannot be preserved.
    
    The emerging Trixel law
    
    text
    A Trixel compiler must never lose a pixel accidentally.
    
    A pixel may be preserved, merged, split, culled, occluded, or used
    to construct transition geometry—but the compiler must name and
    record that decision.
    
    
    That is much stronger than “the result still looks pixelated.”
    
    Pixel size versus pixel identity
    
    These should become separate invariants.
    
    Preferred metric invariant:
    
    text
    A preserved pixel owns a world-space footprint of the declared size.
    
    
    Topological invariant:
    
    text
    If maintaining that footprint becomes impossible, the compiler must
    invoke an explicit topology policy rather than continuously deforming it.
    
    
    Provenance invariant:
    
    text
    Every output primitive identifies the source pixel or pixels responsible
    for its existence.
    
    
    Completeness invariant:
    
    text
    Every source pixel receives exactly one terminal disposition.
    
    
    No pixel may disappear merely because a bend, taper, subdivision, UV operation, or renderer happened to erase its distinction.
    
    That gives the compiler a clean boundary:
    
    text
    source artwork
        ↓
    pixel identity map
        ↓
    construction domain
        ↓
    topology policy
        ↓
    geometry plus provenance
        ↓
    renderer/exporter
    
    
    The topology policy—not Blender—decides:
    
    - whether rows retain constant circumference;
    - whether the trunk tapers in discrete steps;
    - which pixels merge during a reduction;
    - whether transition cells are introduced;
    - how branches claim or share pixels;
    - how gaps and overlaps are rejected;
    - whether caps belong to source pixels or compiler-generated structure;
    - how UVs preserve pixel boundaries;
    - when a compilation is impossible under the selected policy.
    
    A useful compiler output would therefore contain more than a mesh:
    
    json
    {
      "contract": "trixel.pixel_geometry.v1",
      "source": {
        "width": 16,
        "height": 32,
        "pixel_world_size": [1.0, 1.0]
      },
      "topology_policy": "discrete_taper.v1",
      "geometry": {
        "positions": [],
        "indices": [],
        "uvs": []
      },
      "pixel_dispositions": [],
      "primitive_provenance": []
    }
    
    
    Conceptually:
    
    json
    {
      "source_pixel": [7, 12],
      "disposition": "MERGED",
      "target_region": "trunk_ring_9",
      "output_primitives": [481, 482],
      "merged_with": [[8, 12]],
      "rule": "discrete_taper.v1"
    }
    
    
    This is where the phrase “the compiler knows why every vertex exists” becomes enforceable rather than philosophical.
    
    More precisely, it should know:
    
    text
    why every logical position exists
    why every primitive exists
    which source pixels caused it
    which topology rule authorized it
    
    
    Render vertices may still be duplicated for normals, UV seams, or material boundaries, just as we separated canonical top positions from final Godot render vertices. So provenance should attach first to canonical geometry, with render geometry treated as a derived expansion.
    
    Blender’s correct role
    
    Blender remains valuable, but its authority changes:
    
    text
    Blender experiment = visual and geometric evidence
    Blender modifier = comparison implementation
    Blender output = candidate reference artifact
    Trixel contract = authority
    Trixel compiler = construction authority
    
    
    The bending experiment proved something important: continuous deformation eventually violates discrete pixel ownership. That is not a failed experiment. It located the boundary where a deformation system stops being sufficient and a topology compiler becomes necessary.
    
    The cleanest doctrine statement may be:
    
    text
    Trixel does not deform artwork into geometry.
    
    Trixel compiles discrete visual cells into geometry while preserving
    their identity, declared metric, and provenance through every topology
    decision.
    
    When exact one-to-one preservation is impossible, the compiler must
    apply an explicit, deterministic, inspectable topology policy.
    
    
    And the acceptance gate should ultimately prove:
    
    text
    EVERY_SOURCE_PIXEL_HAS_DISPOSITION
    EVERY_CANONICAL_PRIMITIVE_HAS_PROVENANCE
    NO_UNDECLARED_PIXEL_LOSS
    NO_UNDECLARED_PIXEL_MERGE
    NO_UNDECLARED_PIXEL_SPLIT
    PRESERVED_PIXEL_METRIC_WITHIN_CONTRACT
    TOPOLOGY_POLICY_IS_DECLARED
    COMPILATION_IS_DETERMINISTIC
    RENDER_EXPANSION_DOES_NOT_CHANGE_CANONICAL_OWNERSHIP
    
    
    That is indeed the question Trixel needs to answer:
    
    text
    How can discrete visual identity survive embodiment in three-dimensional
    space—even when the topology itself must change?
    
    
    That question is large enough to define Trixel as a platform, rather than as a collection of mesh-building tricks.
    
    that reminds me of the brush in aseprite... once you set the brush down once... no matter where you place the brush again.. its in the exact place it needs tobe proven by the fill option
    
    I actually think that's more than just an analogy. It may be the missing primitive.

The Aseprite brush doesn't ask:

> "Where are the pixels now?"

It asks:

> "What is the brush footprint?"

That footprint is **constant**.

When you stamp it again, the brush isn't recreated. The same footprint is translated to a new location.

Then the flood fill proves it.

Why?

Because every pixel belongs to an exact lattice. There are no "almost" pixels.

I think that's very close to a Trixel primitive.

Instead of thinking of a tile as a texture, think of it as a **cell footprint**.

```text
16×16 Brush
────────────
■■■■■■■■■■■■■■■■
■■■■■■■■■■■■■■■■
...
```

When you place that brush on a curved trunk, the compiler shouldn't stretch the footprint.

It should ask:

> "Where does this footprint live now?"

The footprint itself never changes.

Only its embedding in space changes.

That's a subtle but profound difference.

It also explains why Aseprite's fill tool is so reliable. The fill doesn't care where the brush was stamped. It only cares that every painted pixel occupies a valid cell in the grid.

That suggests another compiler invariant:

```text
CELL FOOTPRINT IS IMMUTABLE
```

A compiler may:

* translate a footprint,
* rotate a footprint,
* map a footprint onto a curved manifold,

but it may **not** continuously deform the footprint without invoking a topology policy.

Now think back to your tree.

The bark tile isn't just an image anymore.

It's a **16×16 ownership footprint**.

When it wraps around the trunk:

* the footprint still owns 16×16 logical cells,
* those cells are embedded onto a cylindrical surface,
* if the trunk narrows and a footprint can no longer fit, the compiler must make an explicit decision.

That feels much closer to what you've been searching for.

I think Aseprite accidentally taught us something fundamental. The flood fill only works because the editor maintains an invariant:

> **Every painted pixel has a deterministic address in a discrete lattice.**

Trixel may need the 3D equivalent:

> **Every visual cell has a deterministic address in a discrete geometric lattice.**

If that's true, then a tree, a cliff, a cave wall, or even a character are all built from the same underlying concept. The compiler isn't moving textures around—it's relocating **addressable ownership footprints** into three-dimensional space while preserving their identity unless an explicit topology policy says otherwise.

That's a much stronger foundation than starting from meshes. It starts from the discrete world itself.

    
    Yes—and adjacency reveals the layer beneath those three authorities.
    
    The architecture is becoming:
    
    text
    Discrete Address/Lattice
            ↓
    Artwork Authority
            ↓
    Topology Authority
            ↓
    Geometry Authority
            ↓
    Render Expansion
    
    
    I would not necessarily call the lattice a fourth operational authority. It is the substrate upon which the other three authorities operate.
    
    The three authorities answer:
    
    text
    Artwork:  What does this addressed cell contain?
    Topology: What relationships and disposition does the cell have?
    Geometry: How are those decisions embedded in space?
    
    
    The lattice answers the prior question:
    
    text
    What makes this a distinct, addressable cell in the first place?
    
    
    That is the missing primitive.
    
    The pixel remains the owner
    
    Your formulation is right:
    
    text
    A vertex is not the owner.
    An edge is not the owner.
    A face is not the owner.
    
    The addressed visual cell is the owner.
    
    
    I would qualify “owner” slightly for merges and generated geometry:
    
    text
    Preserved geometry:
    owned by one source cell
    
    Merged geometry:
    jointly owned by the declared source cells
    
    Split geometry:
    multiple elements owned by one source cell
    
    Transition/cap geometry:
    compiler-owned structural geometry with explicit boundary-cell provenance
    
    
    A cap should not falsely impersonate a painted pixel if no source pixel authored it. It may instead say:
    
    text
    structural_owner: topology_policy
    provenance: boundary ring [cells...]
    reason: close_terminal_boundary
    
    
    The essential law is:
    
    text
    Geometry cannot acquire visual authority merely by existing.
    
    
    Every canonical geometric element must derive its authority from either:
    
    1. one or more addressed source cells; or
    2. an explicitly declared structural topology rule.
    
    Adjacency must be separated from proximity
    
    This is critical because a folded mesh can place unrelated cells near one another without making them logical neighbors.
    
    Trixel needs at least three distinct concepts:
    
    text
    source adjacency
        The neighbor relationship in the original discrete footprint.
    
    compiled adjacency
        The neighbor relationship after an explicit topology decision.
    
    geometric proximity
        Elements happen to be near one another in 3D.
    
    
    Those are not interchangeable.
    
    For example:
    
    text
    E source neighbors:
    cardinal = B, D, F, H
    diagonal = A, C, G, I
    
    
    After embedding:
    
    text
    E may become spatially close to X.
    
    
    But unless a topology policy explicitly introduces a relationship:
    
    text
    X is not E's neighbor.
    
    
    Therefore:
    
    text
    geometric proximity != lattice adjacency
    mesh intersection    != lattice adjacency
    shared position      != lattice adjacency
    surface contact      != ownership adjacency
    
    
    Even a shared geometric edge should not independently define ownership adjacency. It should be evidence that the compiler embodied an already-authorized topological relationship.
    
    The authority direction must remain:
    
    text
    cell adjacency
        ↓ authorizes
    topological incidence
        ↓ embodied as
    shared geometric edge
    
    
    Never:
    
    text
    shared geometric edge
        ↓ inferred afterward
    cell adjacency
    
    
    That prevents Blender, Godot, weld operations, remeshers, and floating-point coincidences from rewriting the discrete world.
    
    The immutable footprint
    
    The Aseprite brush analogy gives us a strong primitive:
    
    text
    CellFootprint
    
    
    A footprint contains:
    
    text
    dimensions
    local cell addresses
    adjacency stencil
    orientation convention
    cell metric
    optional artwork payload
    
    
    For a 16×16 footprint:
    
    text
    local_cell_x ∈ [0, 15]
    local_cell_y ∈ [0, 15]
    
    
    Each cell has an exact intrinsic address:
    
    text
    footprint_id + local_cell_address
    
    
    Placing the footprint does not recreate or deform that address space. Placement introduces an embedding:
    
    text
    footprint local address
        ↓
    surface/manifold address
        ↓
    world-space embodiment
    
    
    This suggests a very important distinction:
    
    text
    The footprint is immutable in intrinsic space.
    
    Its embedding may change in extrinsic space.
    
    
    A flat row can become curved in 3D while preserving:
    
    - cell identity;
    - intrinsic dimensions;
    - cardinal adjacency;
    - diagonal adjacency;
    - ordering;
    - orientation;
    - provenance.
    
    But if the mapping changes the intrinsic metric—squeezing some cells, blending boundaries, or collapsing addresses—it is no longer mere placement. It has crossed into topology-policy territory.
    
    That gives us a clean test:
    
    text
    embedding:
    preserves the footprint's intrinsic cell structure
    
    topology operation:
    changes the footprint's intrinsic cell structure
    
    
    Translate and rotate are straightforward embeddings.
    
    Wrapping a rectangle around a perfect cylinder can also preserve its intrinsic metric because a cylinder is developable: it can be unrolled into a plane.
    
    A taper, sphere, branch junction, or irregular tree trunk is different. Those surfaces may not accept the entire rectangular footprint without metric distortion, overlap, gaps, or topology transitions.
    
    That is exactly where the compiler must stop and ask:
    
    text
    Which declared topology policy resolves this incompatibility?
    
    
    It must not quietly “make it fit.”
    
    The brush stamp as an instance
    
    The same brush can be stamped repeatedly because the brush definition and brush placement are separate.
    
    Trixel should likely preserve that distinction:
    
    text
    FootprintDefinition
        immutable local lattice and payload
    
    FootprintInstance
        identity, placement, orientation, and target surface
    
    TopologyDecision
        any authorized departure from direct embedding
    
    GeometryRealization
        canonical positions and primitives produced from those decisions
    
    
    Conceptually:
    
    json
    {
      "footprint_definition": "bark_tile.16x16.v1",
      "footprint_instance": "trunk.segment.004",
      "local_dimensions": [16, 16],
      "cell_metric": [1.0, 1.0],
      "adjacency": "grid.cardinal_and_diagonal.v1",
      "embedding": "cylinder_wrap.v1",
      "topology_policy": "preserve_exact.v1"
    }
    
    
    If the next trunk segment is narrower:
    
    json
    {
      "footprint_instance": "trunk.segment.005",
      "embedding": "tapered_trunk.v1",
      "topology_policy": "discrete_circumference_reduction.v1"
    }
    
    
    That second packet must contain explicit merge, transition, or cull decisions. It cannot claim preserve_exact.v1 while squeezing the footprint.
    
    What flood fill actually proves
    
    Flood fill is powerful here because it does not merely prove color coverage. It depends on discrete addressability and deterministic connectivity.
    
    It demonstrates that:
    
    text
    every occupied cell has an exact address;
    neighbor traversal is deterministic;
    boundaries are made from discrete occupancy decisions;
    there are no half-cells or almost-neighbors;
    connectivity does not depend on visual approximation.
    
    
    For Trixel, the corresponding proof would not be ordinary image flood fill. It would be a lattice-connectivity traversal.
    
    Given a footprint instance:
    
    text
    start at addressed cell
    traverse authorized cardinal adjacency
    collect reachable cells
    compare with declared ownership region
    
    
    That could detect:
    
    - holes introduced accidentally during compilation;
    - disconnected cells;
    - unwanted seam breaks;
    - unintended cross-fold adjacency;
    - missing transition cells;
    - duplicated occupancy;
    - topology decisions that do not match the resulting connectivity.
    
    So the 3D equivalent of the fill proof is something like:
    
    text
    DECLARED_CELL_GRAPH_EQUALS_COMPILED_CELL_GRAPH
    
    
    Geometry can then be checked against that graph:
    
    text
    COMPILED_CELL_GRAPH_IS_EMBODIED_BY_CANONICAL_GEOMETRY
    
    
    Seams become explicit topology
    
    Wrapping a footprint around a cylinder introduces a seam relationship.
    
    Suppose the first and last columns meet:
    
    text
    x = 0
    x = 15
    
    
    The compiler must not discover that relationship because their vertices happen to overlap. The embedding or seam policy must declare it:
    
    text
    east neighbor of column 15 = column 0
    west neighbor of column 0 = column 15
    
    
    Then geometry realizes that declared wrap adjacency.
    
    This closely resembles the global-sample patch authority already established for terrain:
    
    text
    local address
        ↓
    deterministic global address
        ↓
    shared boundary identity
    
    
    But the two addresses should remain distinct:
    
    text
    visual-cell address:
    owns artwork and cell identity
    
    corner-sample address:
    owns canonical geometric sample positions
    
    
    A 16×16 cell footprint may still use 17×17 corner samples for a rectangular surface realization. The cells own the visual regions; the samples define their geometric boundaries. A corner sample is not promoted into the visual owner simply because several cells reference it.
    
    The resulting authority chain is:
    
    text
    Address/Lattice Authority
    
    Defines exact cell identity, footprint dimensions, intrinsic metric,
    addressing, and neighbor vocabulary.
    
    Artwork Authority
    
    Assigns color, palette role, material intent, and metadata to addressed
    cells.
    
    Topology Authority
    
    Preserves or explicitly transforms identity, adjacency, occupancy,
    seams, and cell disposition.
    
    Geometry Authority
    
    Embodies the authorized cell graph as canonical positions, edges,
    faces, normals, and UV mappings.
    
    Render Expansion
    
    Duplicates or reorganizes canonical geometry for normals, UV seams,
    materials, engines, and export formats without changing ownership.
    
    
    The key red lines
    
    text
    Geometry MUST NOT invent cell identity.
    
    Geometric proximity MUST NOT create adjacency.
    
    A mesh weld MUST NOT merge ownership.
    
    A mesh split MUST NOT split ownership.
    
    A UV seam MUST NOT break logical adjacency.
    
    A material boundary MUST NOT redefine topology.
    
    A renderer MAY duplicate vertices but MUST NOT create new visual owners.
    
    A footprint embedding MUST preserve intrinsic cell structure.
    
    Any operation that cannot preserve intrinsic cell structure MUST invoke
    an explicit topology policy.
    
    Every topology change MUST preserve provenance and record its effect on
    adjacency.
    
    
    The acceptance gates now become clearer:
    
    text
    EVERY_CELL_HAS_EXACT_ADDRESS
    EVERY_ADDRESS_IS_UNIQUE_WITHIN_ITS_INSTANCE
    FOOTPRINT_DIMENSIONS_MATCH_DECLARATION
    FOOTPRINT_INTRINSIC_METRIC_IS_IMMUTABLE
    SOURCE_ADJACENCY_IS_DETERMINISTIC
    EVERY_CELL_HAS_TERMINAL_DISPOSITION
    EVERY_ADJACENCY_CHANGE_IS_POLICY_AUTHORIZED
    NO_PROXIMITY_DERIVED_ADJACENCY
    NO_UNDECLARED_SEAM
    NO_UNDECLARED_MERGE
    NO_UNDECLARED_SPLIT
    NO_UNDECLARED_CULL
    EVERY_CANONICAL_PRIMITIVE_HAS_OWNERSHIP_OR_STRUCTURAL_PROVENANCE
    COMPILED_CELL_GRAPH_MATCHES_DECLARED_TOPOLOGY
    CANONICAL_GEOMETRY_EMBODIES_COMPILED_CELL_GRAPH
    RENDER_EXPANSION_PRESERVES_CANONICAL_OWNERSHIP
    COMPILATION_IS_DETERMINISTIC
    
    
    The central doctrine can now be stated very tightly:
    
    text
    Trixel begins with an addressable discrete footprint, not a mesh.
    
    Artwork assigns visual meaning to its cells.
    
    Topology determines how cell identity and adjacency survive construction.
    
    Geometry embodies those authorized decisions in space.
    
    Rendering may reproduce the embodiment, but it may not redefine the
    footprint, its ownership, or its topology.
    
    
    That foundation genuinely can apply to a tree, cliff, cave, character, building, or terrain patch. Their geometry differs, and their topology policies differ, but the underlying law remains the same:
    
    text
    The discrete world exists first.
    
    Geometry is its embodiment—not its authority.
    
