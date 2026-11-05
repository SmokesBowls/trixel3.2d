from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "trixel" / "gates" / "gate_terrain_state_lane_a_v1.py"
FIXTURE = ROOT / "fixtures" / "terrain_state" / "watershed_v1.json"
CONTRACT = ROOT / "docs" / "TERRAIN_STATE_LANE_A_CONTRACT_V1.md"


class TerrainStateProofGateTests(unittest.TestCase):
    def test_gate_publishes_verified_reproducible_evidence_and_ledger(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        before = FIXTURE.read_bytes(), CONTRACT.read_bytes()
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        with tempfile.TemporaryDirectory(prefix="trixel-lane-a-gate-") as temp:
            first, second = Path(temp) / "first", Path(temp) / "second"
            for target in [first, second]:
                completed = subprocess.run([sys.executable, str(GATE), "--output-dir", str(target)],
                                           cwd=ROOT, env=env, capture_output=True, text=True, timeout=60)
                self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
                self.assertIn("[TERRAIN_STATE_LANE_A][ALL_GATES] TRUE", completed.stdout)
            self.assertEqual({p.name for p in first.iterdir()}, {"evidence.json", "ledger.tsv", "manifest.json"})
            for name in ["evidence.json", "ledger.tsv", "manifest.json"]:
                self.assertEqual((first / name).read_bytes(), (second / name).read_bytes())
            evidence = json.loads((first / "evidence.json").read_text(encoding="utf-8"))
            self.assertEqual(evidence["result"]["totals"], fixture["expected"]["totals"])
            self.assertEqual(evidence["result"]["ledger"], fixture["expected"]["ledger"])
            self.assertEqual(evidence["embeddings"], fixture["embeddings"])
            self.assertEqual(evidence["expected"], fixture["expected"])
            self.assertEqual(evidence["fixture_sha256"], hashlib.sha256(before[0]).hexdigest())
            self.assertEqual(evidence["contract_sha256"], hashlib.sha256(before[1]).hexdigest())
            manifest = json.loads((first / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["scope"], "isolated_terrain_state_proof_only")
            self.assertEqual(set(manifest["outputs"]), {"evidence.json", "ledger.tsv"})
            for name, digest in manifest["outputs"].items():
                self.assertEqual(digest, hashlib.sha256((first / name).read_bytes()).hexdigest())
            self.assertGreaterEqual(len(manifest["inputs"]), 5)
            for relative, digest in manifest["inputs"].items():
                self.assertEqual(digest, hashlib.sha256((ROOT / relative).read_bytes()).hexdigest())
            with (first / "ledger.tsv").open(encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream, delimiter="\t"))
            self.assertEqual(len(rows), len(fixture["expected"]["ledger"]))
            for actual, expected in zip(rows, fixture["expected"]["ledger"]):
                self.assertEqual(actual, {k: "" if v is None else str(v) for k, v in expected.items()})
        self.assertEqual(before, (FIXTURE.read_bytes(), CONTRACT.read_bytes()))

    def test_gate_requires_explicit_output_destination(self):
        completed = subprocess.run([sys.executable, str(GATE)], cwd=ROOT,
                                   capture_output=True, text=True, timeout=60)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("--output-dir", completed.stderr)


if __name__ == "__main__":
    unittest.main()
