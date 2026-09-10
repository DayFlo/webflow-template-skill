import json
import os
import subprocess
import sys
import tempfile
import unittest

from _paths import fixture, script

import diff_inventory


def load(name):
    with open(fixture(name), "r", encoding="utf-8") as fh:
        return json.load(fh)


class DiffInventoryTests(unittest.TestCase):
    def test_pass_when_only_additions(self):
        result = diff_inventory.diff(load("snapshot_pre.json"), load("snapshot_post_pass.json"))
        self.assertEqual(result["verdict"], "pass")
        self.assertEqual(result["changedPreExisting"], [])
        self.assertEqual(result["removed"], [])
        created = {(c["kind"], c["key"]) for c in result["created"]}
        self.assertIn(("styles", "product-landing_comparison-grid"), created)
        self.assertIn(("components", "comp-comparison"), created)
        self.assertIn(("variant", "comp-hero/icon-top"), created)
        self.assertIn(("prop", "comp-hero/eyebrow"), created)
        self.assertIn(("variables", "var-surface-2"), created)
        self.assertEqual(result["counts"]["created"], 5)

    def test_object_key_order_does_not_count_as_change(self):
        pre = {"styles": {"a": {"x": 1, "y": 2}}}
        post = {"styles": {"a": {"y": 2, "x": 1}}}
        self.assertEqual(diff_inventory.diff(pre, post)["verdict"], "pass")

    def test_fail_on_changed_and_removed(self):
        result = diff_inventory.diff(load("snapshot_pre.json"), load("snapshot_post_fail.json"))
        self.assertEqual(result["verdict"], "fail")
        changed = {(c["kind"], c["key"]) for c in result["changedPreExisting"]}
        self.assertIn(("styles", "hero_title"), changed)
        self.assertIn(("components", "comp-hero"), changed)          # base edited
        self.assertIn(("variant", "comp-hero/default"), changed)     # base variant edited
        self.assertIn(("variables", "var-brand"), changed)
        self.assertNotIn(("styles", "hero_media"), changed)          # unchanged object
        removed = {(r["kind"], r["key"]) for r in result["removed"]}
        self.assertEqual(removed, {("styles", "u-text-center")})
        comp = next(c for c in result["changedPreExisting"] if c["key"] == "comp-hero" and c["kind"] == "components")
        self.assertEqual(comp["fields"], ["base"])

    def test_accepted_deviations_do_not_fail(self):
        pre = load("snapshot_pre.json")
        post = load("snapshot_post_fail.json")
        accept = ["styles:hero_title", "components:comp-hero", "variant:comp-hero/default", "variables:var-brand", "styles:u-text-center"]
        result = diff_inventory.diff(pre, post, accept=accept)
        self.assertEqual(result["verdict"], "pass")
        self.assertEqual(result["counts"]["accepted"], 5)
        partial = diff_inventory.diff(pre, post, accept=accept[:2])
        self.assertEqual(partial["verdict"], "fail")

    def test_instance_count_changes_are_not_edits(self):
        pre = {"components": {"faq": {"name": "FAQ section", "instanceCount": 45, "propCount": 13, "lastUpdated": "a",
                                       "props": {"p1": "text"}, "variants": {"Base": "present"}}}}
        post = {"components": {"faq": {"name": "FAQ section", "instanceCount": 46, "propCount": 13, "lastUpdated": "b",
                                        "props": {"p1": "text"}, "variants": {"Base": "present"}}}}
        result = diff_inventory.diff(pre, post)
        self.assertEqual(result["verdict"], "pass", result)
        post["components"]["faq"]["name"] = "FAQ section (renamed)"
        renamed = diff_inventory.diff(pre, post)
        self.assertEqual(renamed["verdict"], "fail")
        self.assertEqual(renamed["changedPreExisting"][0]["fields"], ["name"])

    def test_malformed_snapshot(self):
        with self.assertRaises(ValueError):
            diff_inventory.diff({"styles": ["a"]}, {"styles": {}})
        with self.assertRaises(ValueError):
            diff_inventory.diff([], {})

    def test_cli_exit_codes(self):
        ok = subprocess.run([sys.executable, script("diff_inventory.py"), fixture("snapshot_pre.json"), fixture("snapshot_post_pass.json")], capture_output=True, text=True)
        self.assertEqual(ok.returncode, 0, ok.stdout)
        self.assertEqual(json.loads(ok.stdout)["verdict"], "pass")
        bad = subprocess.run([sys.executable, script("diff_inventory.py"), fixture("snapshot_pre.json"), fixture("snapshot_post_fail.json")], capture_output=True, text=True)
        self.assertEqual(bad.returncode, 1)
        self.assertEqual(json.loads(bad.stdout)["verdict"], "fail")
        accepted = subprocess.run([sys.executable, script("diff_inventory.py"), fixture("snapshot_pre.json"), fixture("snapshot_post_fail.json"),
                                   "--accept", "styles:hero_title", "--accept", "components:comp-hero", "--accept", "variant:comp-hero/default",
                                   "--accept", "variables:var-brand", "--accept", "styles:u-text-center"], capture_output=True, text=True)
        self.assertEqual(accepted.returncode, 0, accepted.stdout)
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            fh.write("[]")
            path = fh.name
        try:
            err = subprocess.run([sys.executable, script("diff_inventory.py"), path, fixture("snapshot_post_pass.json")], capture_output=True, text=True)
            self.assertEqual(err.returncode, 2)
        finally:
            os.unlink(path)
        help_result = subprocess.run([sys.executable, script("diff_inventory.py"), "--help"], capture_output=True, text=True)
        self.assertEqual(help_result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
