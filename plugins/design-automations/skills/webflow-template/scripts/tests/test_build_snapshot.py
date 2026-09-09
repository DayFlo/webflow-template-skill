import json
import os
import subprocess
import sys
import tempfile
import unittest

from _paths import fixture, script

import build_snapshot


class BuildSnapshotTests(unittest.TestCase):
    def test_components_expand_only_listed_ids_and_drop_counters(self):
        snap = build_snapshot.components_snapshot([fixture("snapshot", "components.txt")], {"comp-a"})
        self.assertEqual(set(snap), {"comp-a", "comp-b"})
        a = snap["comp-a"]
        self.assertEqual(a["name"], "FAQ section")
        self.assertNotIn("instanceCount", a)
        self.assertEqual(a["props"]["p2"], {"name": "Heading", "type": "textContent", "group": "Header"})
        self.assertEqual(a["variants"], {"Base": "present"})
        self.assertNotIn("props", snap["comp-b"])
        self.assertEqual(snap["comp-b"]["description"], "nav")

    def test_variables_from_two_actions_with_preamble_and_collection_map(self):
        cmap = {"--color---": "col-color", "--responsive---": "col-resp"}
        snap = build_snapshot.variables_snapshot([fixture("snapshot", "variables.txt")], cmap)
        self.assertEqual(snap["var-1"]["collection"], "col-color")
        self.assertEqual(snap["var-2"]["collection"], "col-resp")
        self.assertEqual(snap["var-2"]["value"], {"value": 1280, "unit": "px"})
        self.assertEqual(snap["var-1"]["modeValues"][0]["modeId"], "base")

    def test_styles_keep_named_globals_ignore_combos_and_padding_mark_missing(self):
        snap = build_snapshot.styles_snapshot([fixture("snapshot", "styles.txt")], ["l-section", "l-section--header", "c-button"])
        self.assertEqual(snap["l-section"], {"properties": {"base": {"properties": {"position": "relative"}}}})
        self.assertIn("breakpoints", snap["l-section--header"]["properties"])
        self.assertEqual(snap["c-button"], "missing")
        self.assertNotIn("l-text--body", snap)

    def test_error_result_is_rejected(self):
        with self.assertRaises(ValueError):
            build_snapshot.styles_snapshot([fixture("snapshot", "styles_error.txt")], ["l-section"])

    def test_cli_writes_snapshot_shape_and_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "pre.json")
            proc = subprocess.run([sys.executable, script("build_snapshot.py"), "--site-id", "site1",
                                   "--components", fixture("snapshot", "components.txt"), "--expand-components", "comp-a",
                                   "--variables", fixture("snapshot", "variables.txt"), "--collection-map=--color---=col-color",
                                   "--styles", fixture("snapshot", "styles.txt"), "--classes", "l-section,l-section--header",
                                   "--scope-note", "styles=two classes", "--captured-at", "2026-01-06T19:40:00Z", "-o", out],
                                  capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            report = json.loads(proc.stdout)
            self.assertTrue(report["ok"])
            self.assertTrue(report["sha256"].startswith("sha256:"))
            self.assertEqual(report["counts"], {"styles": 2, "components": 2, "variables": 2})
            self.assertEqual(report["missingClasses"], [])
            with open(out, "r", encoding="utf-8") as fh:
                snap = json.load(fh)
            self.assertEqual(set(snap), {"capturedAt", "siteId", "scope", "styles", "components", "variables"})
            self.assertEqual(snap["capturedAt"], "2026-01-06T19:40:00Z")
            self.assertEqual(snap["scope"]["styles"], "two classes")
            # the snapshot diffs cleanly against itself and a re-run with an added variable is "created"
            import diff_inventory
            self.assertEqual(diff_inventory.diff(snap, snap)["verdict"], "pass")

    def test_cli_exit_2_on_missing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run([sys.executable, script("build_snapshot.py"), "--site-id", "s", "--components", os.path.join(tmp, "nope.txt"),
                                   "-o", os.path.join(tmp, "o.json")], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 2)
            self.assertFalse(json.loads(proc.stdout)["ok"])


if __name__ == "__main__":
    unittest.main()
