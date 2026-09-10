import json
import os
import subprocess
import sys
import tempfile
import unittest

from _paths import ASSETS, fixture, script

import validate_brief


def load(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


class ValidateBriefTests(unittest.TestCase):
    def test_example_brief_passes(self):
        brief = load(os.path.join(ASSETS, "brief.example.json"))
        self.assertEqual(validate_brief.validate(brief), [])

    def test_manual_slot_status_is_accepted_and_still_needs_content(self):
        brief = load(os.path.join(ASSETS, "brief.example.json"))
        brief["sections"][0]["slots"].append(
            {"name": "Hero body", "content": "Copy the publisher pastes in the Designer", "status": "manual"}
        )
        self.assertEqual(validate_brief.validate(brief), [])
        brief["sections"][0]["slots"][-1]["content"] = ""
        violations = validate_brief.validate(brief)
        self.assertTrue(
            any(v["check"] == 16 and "manual" in v["message"] for v in violations),
            violations,
        )

    def test_invalid_brief_reports_each_check(self):
        brief = load(fixture("brief_invalid.json"))
        violations = validate_brief.validate(brief)
        checks = {v["check"] for v in violations}
        paths = {v["path"] for v in violations}
        # one violation per rule family the fixture breaks
        for expected in (2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20):
            self.assertIn(expected, checks, f"check {expected} not reported")
        self.assertIn("sections[0].componentName", paths)        # reused without componentName
        self.assertIn("sections[1].componentName", paths)        # a Webflow id where a name belongs
        self.assertIn("sections[1].adaptation", paths)           # adapted without adaptation
        self.assertIn("sections[2].newComponentSpec", paths)     # new without spec
        self.assertIn("sections[1].order", paths)                # duplicate order
        self.assertIn("page.folder.id", paths)                   # null id for non-root folder

    def test_missing_required_fields(self):
        violations = validate_brief.validate({})
        self.assertEqual({v["check"] for v in violations}, {1})
        self.assertEqual(len(violations), 7)

    def test_non_object_brief(self):
        violations = validate_brief.validate(["not", "an", "object"])
        self.assertEqual(violations[0]["path"], "$")

    def test_require_approval(self):
        brief = load(os.path.join(ASSETS, "brief.example.json"))
        self.assertEqual(brief["approvedAt"], None)
        violations = validate_brief.validate(brief, require_approval=True)
        self.assertEqual([v["path"] for v in violations], ["approvedAt"])
        brief["approvedAt"] = "2026-01-04T18:00:00Z"
        self.assertEqual(validate_brief.validate(brief, require_approval=True), [])

    def test_loose_sections(self):
        brief = load(os.path.join(ASSETS, "brief.example.json"))
        loose = {"order": 9, "familySection": "benefit-a", "reuseLevel": "reused", "componentName": "loose",
                 "classPath": "section.l-section.l-bg--surface-1", "masterSection": 4, "slots": []}
        brief["sections"].append(loose)
        self.assertEqual(validate_brief.validate(brief), [])          # hybrid allows loose
        brief["templateModel"] = "component-recipe"
        paths = [v["path"] for v in validate_brief.validate(brief)]
        self.assertIn("sections[8].componentName", paths)               # recipe does not
        brief["templateModel"] = "duplicate-master"
        loose["reuseLevel"] = "adapted"
        loose["adaptation"] = {"newVariant": "x"}
        messages = " ".join(v["message"] for v in validate_brief.validate(brief))
        self.assertIn("must be reused", messages)
        loose["reuseLevel"] = "reused"
        del loose["classPath"]
        messages = " ".join(v["message"] for v in validate_brief.validate(brief))
        self.assertIn("class path in classPath", messages)

    def test_component_name_may_not_be_a_webflow_id(self):
        """Briefs name components; the id is resolved at run time and lives in the manifest."""
        brief = load(os.path.join(ASSETS, "brief.example.json"))
        for bad in ("1111aaaa-0000-4000-8000-000000000009", "0000000000000000000000b3",
                    "FAQ section 1111aaaa-0000-4000-8000-000000000007"):
            brief["sections"][1]["componentName"] = bad
            violations = validate_brief.validate(brief)
            self.assertEqual([(v["path"], v["check"]) for v in violations], [("sections[1].componentName", 14)], bad)
            self.assertIn("is a Webflow id", violations[0]["message"])
        brief["sections"][1]["componentName"] = "Hero / Product"
        self.assertEqual(validate_brief.validate(brief), [])

    def test_candidate_placeholder(self):
        brief = load(os.path.join(ASSETS, "brief.example.json"))
        brief["sections"][5]["componentName"] = "candidate:comparison-grid"
        brief["approvedAt"] = "2026-01-05T18:00:00Z"
        self.assertEqual(validate_brief.validate(brief), [])
        violations = validate_brief.validate(brief, require_approval=True)
        self.assertEqual([v["path"] for v in violations], ["sections[5].componentName"])
        self.assertIn("placeholder", violations[0]["message"])
        brief["sections"][5]["componentName"] = "candidate:Not_A_Slug"
        messages = " ".join(v["message"] for v in validate_brief.validate(brief))
        self.assertIn("candidate:<kebab-slug>", messages)

    def test_branching_unavailable_rejects_branch_mode(self):
        brief = load(os.path.join(ASSETS, "brief.example.json"))
        self.assertEqual(brief["isolationMode"], "draft-main")
        self.assertEqual(validate_brief.validate(brief, branching="unavailable"), [])
        brief["isolationMode"] = "branch"
        self.assertEqual(validate_brief.validate(brief), [], "without the site fact, branch is a valid enum value")
        self.assertEqual(validate_brief.validate(brief, branching="available"), [])
        violations = validate_brief.validate(brief, branching="unavailable")
        self.assertEqual([(v["path"], v["check"]) for v in violations], [("isolationMode", 6)])
        self.assertIn("never offered", violations[0]["message"])
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump(brief, fh)
            path = fh.name
        try:
            rejected = subprocess.run([sys.executable, script("validate_brief.py"), path, "--branching", "unavailable"], capture_output=True, text=True)
            self.assertEqual(rejected.returncode, 1, rejected.stdout)
            accepted = subprocess.run([sys.executable, script("validate_brief.py"), path, "--branching", "available"], capture_output=True, text=True)
            self.assertEqual(accepted.returncode, 0, accepted.stdout)
            bad_flag = subprocess.run([sys.executable, script("validate_brief.py"), path, "--branching", "maybe"], capture_output=True, text=True)
            self.assertEqual(bad_flag.returncode, 2, "argparse rejects unknown branching values")
        finally:
            os.unlink(path)

    def test_root_folder_allows_null_id(self):
        brief = load(os.path.join(ASSETS, "brief.example.json"))
        brief["page"]["folder"] = {"path": "/", "id": None}
        self.assertEqual(validate_brief.validate(brief), [])

    def test_cli_exit_codes(self):
        ok = subprocess.run([sys.executable, script("validate_brief.py"), os.path.join(ASSETS, "brief.example.json")], capture_output=True, text=True)
        self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
        self.assertTrue(json.loads(ok.stdout.strip())["ok"])

        bad = subprocess.run([sys.executable, script("validate_brief.py"), fixture("brief_invalid.json")], capture_output=True, text=True)
        self.assertEqual(bad.returncode, 1)
        lines = [json.loads(line) for line in bad.stdout.strip().splitlines()]
        self.assertTrue(all("path" in line and "message" in line for line in lines))
        self.assertGreater(len(lines), 10)

        missing = subprocess.run([sys.executable, script("validate_brief.py"), fixture("does-not-exist.json")], capture_output=True, text=True)
        self.assertEqual(missing.returncode, 2)

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            fh.write("{not json")
            path = fh.name
        try:
            broken = subprocess.run([sys.executable, script("validate_brief.py"), path], capture_output=True, text=True)
            self.assertEqual(broken.returncode, 2)
        finally:
            os.unlink(path)

    def test_help(self):
        result = subprocess.run([sys.executable, script("validate_brief.py"), "--help"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("--require-approval", result.stdout)
        self.assertIn("--branching", result.stdout)


if __name__ == "__main__":
    unittest.main()
