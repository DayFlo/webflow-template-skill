import json
import os
import subprocess
import sys
import tempfile
import unittest

from _paths import ASSETS, script

import manifest as m


def make():
    return m.create(slug="acme-integration", surface="claude-ai", site_id="site1", family="product-landing", family_version="1.1.0",
                    template_model="hybrid", isolation_mode="draft-main", brief_hash_value="sha256:abc", started_at="2026-01-04T15:00:00Z")


class ManifestTests(unittest.TestCase):
    def test_create_defaults(self):
        man = make()
        self.assertEqual(man["runId"], "2026-01-04-acme-integration")
        self.assertEqual(man["status"], "open")
        self.assertEqual(man["steps"], [])
        self.assertEqual(man["publishActions"], [])
        self.assertEqual(man["created"]["componentIds"], [])
        self.assertEqual(m.validate_manifest(man), [])

    def test_create_rejects_bad_enums(self):
        with self.assertRaises(ValueError):
            m.create(slug="x", surface="email", site_id="s", family="f", family_version="1.0.0", template_model="hybrid", isolation_mode="draft-main", brief_hash_value="h")
        with self.assertRaises(ValueError):
            m.create(slug="x", surface="codex", site_id="s", family="f", family_version="1.0.0", template_model="clone", isolation_mode="draft-main", brief_hash_value="h")

    def test_append_merges_ids(self):
        man = make()
        step, violations = m.append(man, tool="data_pages_tool", action="create_page", ids={"pageId": "p1"}, at="2026-01-04T15:01:00Z")
        self.assertEqual(violations, [])
        self.assertEqual(step["seq"], 1)
        self.assertEqual(man["created"]["pageId"], "p1")
        m.append(man, tool="data_component_tool", action="create_blank_component", ids={"componentIds": ["c1"]})
        m.append(man, tool="data_style_tool", action="create_style", ids={"styleNames": "s1"})
        m.append(man, tool="data_component_tool", action="create_blank_component", ids={"componentIds": ["c1", "c2"]})
        self.assertEqual(man["created"]["componentIds"], ["c1", "c2"])
        self.assertEqual(man["created"]["styleNames"], ["s1"])
        self.assertEqual([s["seq"] for s in man["steps"]], [1, 2, 3, 4])
        with self.assertRaises(ValueError):
            m.append(man, tool="t", action="a", status="done")

    def test_created_lists_only_what_the_run_appended(self):
        # cleanup (flows/resume.md) deletes only what is under "created"; a resource that was never
        # appended, or was only touched (not created), must not appear there
        man = make()
        self.assertEqual(man["created"], {"pageId": None, "branchId": None, "componentIds": [], "styleNames": [],
                                          "variableIds": [], "assetIds": [], "instructionPaths": []})
        m.append(man, tool="data_pages_tool", action="get_page_metadata", ids={"masterPageId": "master-1"})   # read, not a creation
        m.append(man, tool="data_pages_tool", action="create_page", ids={"pageId": "p1", "duplicateOf": "master-1"})
        m.append(man, tool="data_component_tool", action="create_blank_component", ids={"componentIds": ["c-new"]})
        m.append(man, tool="data_component_props_tool", action="set_component_instance_prop_values", ids={"elementId": "el-9"})
        m.append(man, tool="data_element_tool", action="remove_element", status="failed", ids={"elementId": "el-10"})
        created = man["created"]
        self.assertEqual(created["pageId"], "p1")
        self.assertEqual(created["componentIds"], ["c-new"])
        self.assertNotIn("master-1", json.dumps(created))
        self.assertNotIn("el-9", json.dumps(created))
        self.assertNotIn("el-10", json.dumps(created))
        self.assertEqual(sorted(created), sorted(["pageId", "branchId", "componentIds", "styleNames", "variableIds", "assetIds", "instructionPaths"]))
        summary = m.summarize(man)
        self.assertEqual(summary["created"]["componentIds"], 1)
        self.assertEqual(summary["steps"]["failed"], 1)

    def test_publish_site_is_recorded_and_flagged(self):
        man = make()
        step, violations = m.append(man, tool="data_sites_tool", action="publish_site")
        self.assertEqual(len(man["publishActions"]), 1)
        self.assertEqual(man["steps"][-1]["action"], "publish_site")
        self.assertTrue(any("rule 8" in v for v in violations))

    def test_publish_branch_rules(self):
        man = make()
        _, violations = m.append(man, tool="data_pages_tool", action="publish_branch", note="staging")
        self.assertTrue(violations, "publish_branch outside branch mode must be flagged")
        branch = m.create(slug="x", surface="claude-code", site_id="s", family="f", family_version="1.0.0", template_model="hybrid",
                          isolation_mode="branch", brief_hash_value="h")
        _, violations = m.append(branch, tool="data_pages_tool", action="publish_branch", note="staging, user asked")
        self.assertEqual(violations, [])
        self.assertEqual(len(branch["publishActions"]), 1)

    def test_set_and_summarize(self):
        man = make()
        m.append(man, tool="data_pages_tool", action="create_page", ids={"pageId": "p1"})
        m.append(man, tool="data_element_tool", action="move_element", status="failed")
        m.set_fields(man, status="failed", guard_verdict={"verdict": "fail"}, pre_hash="sha256:pre", post_hash="sha256:post", accept=["styles:x", "styles:x"])
        self.assertEqual(man["acceptedDeviations"], ["styles:x"])
        summary = m.summarize(man)
        self.assertEqual(summary["status"], "failed")
        self.assertEqual(summary["steps"], {"total": 2, "ok": 1, "failed": 1, "skipped": 0})
        self.assertEqual(summary["lastStep"], {"seq": 2, "action": "move_element", "status": "failed"})
        self.assertEqual(summary["guardVerdict"], "fail")
        self.assertEqual(summary["created"]["pageId"], "p1")
        self.assertEqual(summary["family"], "product-landing@1.1.0")
        with self.assertRaises(ValueError):
            m.set_fields(man, status="done")

    def test_ships(self):
        man = make()
        m.append(man, tool="data_component_tool", action="create_blank_component", ids={"componentIds": ["c1"]})
        m.append(man, tool="data_style_tool", action="create_style", ids={"styleNames": ["product-landing_grid"]})
        m.append(man, tool="data_variable_tool", action="create_variable", ids={"variableIds": ["v1"]})
        m.append(man, tool="asset_tool", action="upload_image_by_url", ids={"assetIds": ["a1"]})
        result = m.ships(man)
        self.assertEqual([(i["kind"], i["id"]) for i in result["shipsAtNextPublish"]],
                         [("component", "c1"), ("style", "product-landing_grid"), ("variable", "v1")])
        # an uploaded asset never joins the ships list: it does not wait for a
        # publish, it is public from the moment of upload (rules.md rule 19)
        self.assertEqual(result["alreadyPublic"], [{"kind": "asset", "id": "a1"}])
        self.assertIn("public CDN", result["alreadyPublicNote"])
        man["isolationMode"] = "branch"
        man["created"]["branchId"] = "b1"
        branch = m.ships(man)
        self.assertEqual(branch["shipsAtNextPublish"], [])
        self.assertIn("b1", branch["note"])
        # a branch isolates components, styles and variables; it does not
        # isolate the site-level asset library
        self.assertEqual(branch["alreadyPublic"], [{"kind": "asset", "id": "a1"}])

    def test_ships_says_so_when_nothing_was_uploaded(self):
        man = make()
        m.append(man, tool="data_style_tool", action="create_style", ids={"styleNames": ["s"]})
        result = m.ships(man)
        self.assertEqual(result["alreadyPublic"], [])
        self.assertIn("existing asset library", result["alreadyPublicNote"])

    def test_brief_hash_is_stable(self):
        self.assertEqual(m.brief_hash({"a": 1, "b": [1, 2]}), m.brief_hash({"b": [1, 2], "a": 1}))
        self.assertTrue(m.brief_hash({}).startswith("sha256:"))

    def test_cli_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "manifest.json")
            create = subprocess.run([sys.executable, script("manifest.py"), "create", "--slug", "acme-integration", "--surface", "claude-code",
                                     "--site-id", "site1", "--family", "product-landing", "--family-version", "1.1.0", "--template-model", "hybrid",
                                     "--isolation-mode", "draft-main", "--brief", os.path.join(ASSETS, "brief.example.json"), "-o", path],
                                    capture_output=True, text=True)
            self.assertEqual(create.returncode, 0, create.stdout + create.stderr)
            with open(path) as fh:
                man = json.load(fh)
            self.assertTrue(man["briefHash"].startswith("sha256:"))

            append = subprocess.run([sys.executable, script("manifest.py"), "append", path, "--tool", "data_pages_tool", "--action", "create_page",
                                     "--ids", '{"pageId": "p1"}', "--note", "draft confirmed"], capture_output=True, text=True)
            self.assertEqual(append.returncode, 0, append.stdout)
            self.assertEqual(json.loads(append.stdout)["step"]["seq"], 1)

            forbidden = subprocess.run([sys.executable, script("manifest.py"), "append", path, "--tool", "data_sites_tool", "--action", "publish_site"],
                                       capture_output=True, text=True)
            self.assertEqual(forbidden.returncode, 1)
            with open(path) as fh:
                self.assertEqual(len(json.load(fh)["publishActions"]), 1)

            verdict_path = os.path.join(tmp, "verdict.json")
            with open(verdict_path, "w") as fh:
                json.dump({"verdict": "pass"}, fh)
            setr = subprocess.run([sys.executable, script("manifest.py"), "set", path, "--status", "verified", "--guard-verdict", verdict_path,
                                   "--post-snapshot-hash", "sha256:post"], capture_output=True, text=True)
            self.assertEqual(setr.returncode, 0, setr.stdout)

            summary = subprocess.run([sys.executable, script("manifest.py"), "summarize", path], capture_output=True, text=True)
            self.assertEqual(summary.returncode, 0)
            data = json.loads(summary.stdout)
            self.assertEqual(data["status"], "verified")
            self.assertEqual(data["guardVerdict"], "pass")
            self.assertEqual(data["publishActions"], 1)

            ships = subprocess.run([sys.executable, script("manifest.py"), "ships", path], capture_output=True, text=True)
            self.assertEqual(ships.returncode, 0)
            self.assertEqual(json.loads(ships.stdout)["shipsAtNextPublish"], [])

            garbage = os.path.join(tmp, "garbage.json")
            with open(garbage, "w") as fh:
                fh.write("{}")
            bad = subprocess.run([sys.executable, script("manifest.py"), "summarize", garbage], capture_output=True, text=True)
            self.assertEqual(bad.returncode, 1)
            missing = subprocess.run([sys.executable, script("manifest.py"), "summarize", os.path.join(tmp, "nope.json")], capture_output=True, text=True)
            self.assertEqual(missing.returncode, 2)

        help_result = subprocess.run([sys.executable, script("manifest.py"), "--help"], capture_output=True, text=True)
        self.assertEqual(help_result.returncode, 0)
        for sub in ("create", "append", "set", "summarize", "ships"):
            self.assertIn(sub, help_result.stdout)


def checklist(**overrides):
    rows = {
        "outline-match": {"verdict": "pass", "evidence": "get_all_elements: main children in outline order"},
        "family-rules": {"verdict": "handoff", "evidence": "no analytics component instance on the page",
                         "handoff": "Place the existing Analytics embed component in the Designer."},
        "cta": {"verdict": "pass", "evidence": "Button/Label = 'Book a demo', link = /demo"},
        "seo": {"verdict": "pass", "evidence": "get_page_metadata: draft true, slug acme-integration"},
        "guard": {"verdict": "pass", "evidence": "diff_inventory.py verdict pass"},
        "tracking": {"verdict": "warn", "evidence": "convention UNMEASURED in webflow-conventions.md"},
    }
    rows.update(overrides)
    return [{"id": rid, **row} for rid, row in rows.items()]


class NormativeChecklistTests(unittest.TestCase):
    def test_set_records_the_six_rows_in_phase_6_order(self):
        man = make()
        shuffled = list(reversed(checklist()))
        m.set_fields(man, checklist=shuffled)
        self.assertEqual([row["id"] for row in man["normativeChecklist"]],
                         ["outline-match", "family-rules", "cta", "seo", "guard", "tracking"])
        self.assertEqual(man["normativeChecklist"][1]["handoff"], "Place the existing Analytics embed component in the Designer.")
        self.assertNotIn("handoff", man["normativeChecklist"][0])

    def test_create_leaves_the_checklist_empty(self):
        self.assertIsNone(make()["normativeChecklist"])

    def test_recording_the_table_does_not_move_status(self):
        # the guard sets "failed"; a handoff row is publisher work, not a failed run
        man = make()
        m.set_fields(man, checklist=checklist(guard={"verdict": "fail", "evidence": "changedPreExisting: styles:nav_link"}))
        self.assertEqual(man["status"], "open")

    def test_all_six_rows_are_required_once_each(self):
        rows = checklist()
        with self.assertRaises(ValueError):
            m.normative_checklist([r for r in rows if r["id"] != "seo"])
        with self.assertRaises(ValueError):
            m.normative_checklist(rows + [dict(rows[0])])
        with self.assertRaises(ValueError):
            m.normative_checklist(rows[:-1] + [{"id": "performance", "verdict": "pass", "evidence": "e"}])
        with self.assertRaises(ValueError):
            m.normative_checklist({"outline-match": "pass"})

    def test_verdict_vocabulary_and_evidence_are_enforced(self):
        with self.assertRaises(ValueError):
            m.normative_checklist(checklist(cta={"verdict": "ok", "evidence": "e"}))
        with self.assertRaises(ValueError):
            m.normative_checklist(checklist(cta={"verdict": "pass", "evidence": "   "}))
        with self.assertRaises(ValueError):
            m.normative_checklist(checklist(cta={"verdict": "pass"}))
        # a handoff row must say what the publisher does
        with self.assertRaises(ValueError):
            m.normative_checklist(checklist(**{"family-rules": {"verdict": "handoff", "evidence": "no analytics component"}}))

    def test_tracking_cannot_fail_the_run(self):
        # rule 14: missing link extras are a handoff, never a FAIL
        with self.assertRaises(ValueError) as ctx:
            m.normative_checklist(checklist(tracking={"verdict": "fail", "evidence": "no utm_source on the CTA"}))
        self.assertIn("rule 14", str(ctx.exception))
        rows = m.normative_checklist(checklist(tracking={"verdict": "handoff", "evidence": "CTA carries no utm_source; siblings do",
                                                         "handoff": "Add the same utm_source=site utm_medium=cta the pricing hero CTA uses."}))
        self.assertEqual(rows[-1]["verdict"], "handoff")

    def test_cli_set_normative_checklist(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "manifest.json")
            with open(path, "w") as fh:
                json.dump(make(), fh)
            rows_path = os.path.join(tmp, "checklist.json")
            with open(rows_path, "w") as fh:
                json.dump(checklist(), fh)
            ok = subprocess.run([sys.executable, script("manifest.py"), "set", path, "--normative-checklist", rows_path],
                                capture_output=True, text=True)
            self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
            self.assertEqual(json.loads(ok.stdout)["normativeChecklist"]["tracking"], "warn")
            with open(path) as fh:
                self.assertEqual(len(json.load(fh)["normativeChecklist"]), 6)

            bad = subprocess.run([sys.executable, script("manifest.py"), "set", path, "--normative-checklist",
                                  json.dumps(checklist(tracking={"verdict": "fail", "evidence": "no utm_source"}))],
                                 capture_output=True, text=True)
            self.assertEqual(bad.returncode, 1)
            with open(path) as fh:
                self.assertEqual(json.load(fh)["normativeChecklist"][-1]["verdict"], "warn", "a rejected table must not overwrite the recorded one")


class SkippedStepTests(unittest.TestCase):
    def test_skipped_steps_do_not_touch_created_or_publish_actions(self):
        # dry runs and resumed runs append steps as "skipped"; nothing was made in this call
        man = make()
        m.append(man, tool="data_pages_tool", action="create_page", status="skipped", ids={"pageId": "<created pageId>"}, note="dry-run")
        m.append(man, tool="data_component_tool", action="create_blank_component", status="skipped", ids={"componentIds": ["c-new"]})
        step, violations = m.append(man, tool="data_sites_tool", action="publish_site", status="skipped", ids={})
        self.assertEqual(man["created"], m.empty_created())
        self.assertEqual(man["publishActions"], [])
        self.assertEqual(len(man["steps"]), 3)
        self.assertEqual(step["status"], "skipped")
        # the rule 8 violation is still raised so a dry run cannot plan a publish quietly
        self.assertTrue(any("rule 8" in v for v in violations))
        self.assertEqual(m.ships(man)["shipsAtNextPublish"], [])

    def test_failed_steps_still_merge(self):
        man = make()
        m.append(man, tool="data_pages_tool", action="create_page", status="failed", ids={"pageId": "p-orphan"}, note="timeout after create")
        self.assertEqual(man["created"]["pageId"], "p-orphan")


if __name__ == "__main__":
    unittest.main()
