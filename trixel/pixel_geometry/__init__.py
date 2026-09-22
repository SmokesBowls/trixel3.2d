"""trixel.pixel_geometry.v1 -- a new, parallel construction lane.

Does not modify, replace, or depend on the existing terrain authorities
(trixel32d_surface_builder, trixel/global_sample/**, the recipe renderer).
Those remain untouched and are the ones any real recipe/scene still uses
today. This package exists to answer one question the terrain authorities
were never built to answer: can a footprint's intrinsic cell structure
survive a hard 90-degree fold, not just a flat plane or a smooth height
field?

See DOCTRINE_SELECTION_RECORD.md for which doctrine file this package
treats as authoritative.
"""
