"""Frozen v1 contract identifiers for trixel.pixel_geometry.

Per Task 0.3 of the trial-progression plan: names are frozen here so
trials cannot drift identifiers mid-ladder.
"""
from __future__ import annotations

FOOTPRINT_DEFINITION_CONTRACT = "trixel.footprint_definition.v1"
FOOTPRINT_INSTANCE_CONTRACT = "trixel.footprint_instance.v1"
EMBEDDING_SPECIFICATION_CONTRACT = "trixel.embedding_specification.v1"
TOPOLOGY_POLICY_CONTRACT = "trixel.topology_policy.v1"
COMPILATION_ARTIFACT_CONTRACT = "trixel.compilation_artifact.v1"
VALIDATION_ARTIFACT_CONTRACT = "trixel.validation_artifact.v1"

# Embedding kinds implemented so far. Per 2026-09-20 instruction, the
# ladder stopped after the hinge-fold trial until that artifact AND its
# artwork-attached gate (gate_pixel_geometry_artwork_fold_v1.py, proving
# fold-vs-stretch, not just geometry) both passed. Both are green as of
# 2026-09-21, which is what authorizes the cylindrical closed wrap below.
# Taper/branch/character/terrain integration are still out of scope.
EMBEDDING_FLAT = "flat_identity.v1"
EMBEDDING_RIGID = "rigid_transform.v1"
EMBEDDING_HARD_90_DEGREE_HINGE_FOLD = "hard_90_degree_hinge_fold.v1"
EMBEDDING_CYLINDRICAL_CLOSED_WRAP = "cylindrical_closed_wrap.v1"
EMBEDDING_DECLARED_ANGLE_RAMP_FOLD = "declared_angle_ramp_fold.v1"

# Topology policy exercised by trials 1/2/2.5/artwork-fold: no topology
# change is authorized -- the compiled adjacency must equal the cardinal,
# non-wrapping source_adjacency() exactly.
TOPOLOGY_PRESERVE_EXACT = "preserve_exact.v1"

# Topology policy for a closed cylindrical wrap: the cardinal
# source_adjacency() PLUS one explicit, address-declared seam edge per row
# joining the first and last columns (adjacency_v1.closed_wrap_seam_
# adjacency()). This is a genuine, declared topology change -- calling it
# preserve_exact would be dishonest, since an edge really was added
# relative to the non-wrapping cardinal grid. It is still never
# proximity-derived: the seam is declared by address before any embedding
# runs, exactly like source_adjacency() itself.
TOPOLOGY_CLOSED_WRAP_SEAM = "closed_wrap_seam.v1"
