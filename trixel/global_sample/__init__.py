"""Public neutral global-sample patch and field contracts."""

from .field_v1 import (
    FIELD_CONTRACT_ID,
    assemble_field_packet,
    collect_unique_global_samples,
    generate_field_patch_packets,
    iter_neighbor_pairs,
    validate_field_packet,
    validate_field_patch_set,
)
from .patch_v1 import (
    CELL_COUNT,
    PATCH_CONTRACT_ID,
    SAMPLE_COUNT,
    TOP_INDEX_COUNT,
    TOP_POSITION_COUNT,
    TOP_TRIANGLE_COUNT,
    build_patch_packet,
    cell_index,
    compile_canonical_top,
    global_sample_address,
    sample_index,
    validate_patch_packet,
    validate_patch_structure,
)

__all__ = [
    "CELL_COUNT",
    "FIELD_CONTRACT_ID",
    "PATCH_CONTRACT_ID",
    "SAMPLE_COUNT",
    "TOP_INDEX_COUNT",
    "TOP_POSITION_COUNT",
    "TOP_TRIANGLE_COUNT",
    "assemble_field_packet",
    "build_patch_packet",
    "cell_index",
    "collect_unique_global_samples",
    "compile_canonical_top",
    "generate_field_patch_packets",
    "global_sample_address",
    "iter_neighbor_pairs",
    "sample_index",
    "validate_field_packet",
    "validate_field_patch_set",
    "validate_patch_packet",
    "validate_patch_structure",
]
