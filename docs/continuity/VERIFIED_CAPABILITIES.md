# trixel3.2d — Verified Capabilities

| Check | Command (repo root) | Result 2026-11-25 |
|---|---|---|
| Full suite | `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests` | 85 passed, 100 subtests |
| Builds an EngAIn-assembled request; geometry not mirrored | EngAIn `tier1/engainos/tests/test_trixel32d_bound_assembly.py::test_asymmetric_landmarks_through_trixel_are_not_mirrored` | pass |
| Live route end to end (request drop → build → EngAIn intake re-hash) | EngAIn `tier1/engainos/tests/test_trixel32d_live_route.py` | 85 pass |
| Built surface consumed and shown in Godot | godotnew `tests/h01_runtime_link_check.py`, `tests/h03_reference_stage.py --selftest` | 22/22; APPLIED |
