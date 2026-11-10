import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from build_style_map import render, validate
from export_style_map import export


class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "data/style-map.json").read_text(encoding="utf-8"))

    def test_missing_evidence_is_rejected(self):
        data = copy.deepcopy(self.data)
        data["clusters"][0]["patterns"][0]["evidence"] = ["999999"]
        with self.assertRaises(ValueError):
            validate(data)

    def test_mismatch_is_rejected(self):
        data = copy.deepcopy(self.data)
        next(iter(data["evidence"].values()))["local_check"]["diffs"] = 1
        with self.assertRaises(ValueError):
            validate(data)

    def test_private_source_field_is_rejected(self):
        data = copy.deepcopy(self.data)
        next(iter(data["evidence"].values()))["source_path"] = "private/candidate.cpp"
        with self.assertRaises(ValueError):
            validate(data)

    def test_local_path_in_prose_is_rejected(self):
        data = copy.deepcopy(self.data)
        data["scope"] = "Read D:/private/secret.txt"
        with self.assertRaises(ValueError):
            validate(data)

    def test_renderer_preserves_rejected_verdict(self):
        data = copy.deepcopy(self.data)
        next(iter(data["evidence"].values()))["server_verdict"] = "unfit"
        self.assertIn("Recorded server verdict: **unfit**", render(data)["evidence.md"])

    def test_export_omits_private_fields_and_keeps_latest_verdict(self):
        public = next(iter(self.data["evidence"].values()))
        key = public["id"]
        source = {"clusters": [], "unrecoverable_from_this_evidence": [], "evidence": {key: {
            "address": public["address"], "size": public["size"], "current_source_sha256": public["source_sha256"],
            "source_hash_check": public["hash_check"], "local_check": {"status": "match", "diffs": 0, "checker": "fixture", "reviewed_diagnostics": ["private diagnostic"]},
            "submission_id": "private-receipt", "source": "private source", "source_path": "D:/private/source.cpp", "server_detail": "private diagnostic",
        }}}
        data = export(source, [{"receipt": "private-receipt", "server_verdict": "pending"}], {"recent": [{"id": "private-receipt", "verdict": "unfit"}]})
        self.assertEqual(data["evidence"][key]["server_verdict"], "unfit")
        self.assertEqual(data["evidence"][key]["local_check"]["reviewed_diagnostic_count"], 1)
        self.assertNotIn("private source", json.dumps(data))
        self.assertNotIn("private-receipt", json.dumps(data))
        self.assertNotIn("D:/private", json.dumps(data))


if __name__ == "__main__":
    unittest.main()
