#!/usr/bin/env python3
"""CLI wrapper: consume one trixel32d request drop and write the response drop.

Usage:
  python3 tools/consume_trixel32d_request_drop.py \
      <request_drop_dir> <response_drop_dir> <expected_request_id>

Exit 0 when the slot was consumed with a BUILT response; 1 otherwise. Prints
one JSON result line either way. Passive: builds geometry data only — no
Godot, no placement, no collision, no world mutation.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from trixel.trixel32d_request_drop_consumer import consume_request_drop


def main() -> int:
    if len(sys.argv) != 4:
        print(json.dumps({"consumed": False, "errors": ["usage: request_drop_dir response_drop_dir expected_request_id"]}))
        return 1
    result = consume_request_drop(
        sys.argv[1],
        sys.argv[2],
        recipe_root=REPO / "recipes" / "terrain",
        expected_request_id=sys.argv[3],
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["consumed"] and result["status"] == "BUILT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
