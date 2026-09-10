"""The worked example: the brief in assets/examples validates, renders without
external assets, names components the example catalog names (never by id), its
dry-run manifest created nothing, and the guard fixtures under
fixtures/example pass and fail as the example records.

Every assertion here holds for any site. Anything that would depend on a
particular site's inventory index lives in test_skill_tree.py instead, which
does not require an index to exist.
"""
import copy
import json
import os
import re
import subprocess
import sys
import unittest

from _paths import ASSETS, REFERENCES, fixture, script

import catalog_lint
import diff_inventory
import manifest as m
import render_outline
import validate_brief

EXAMPLES = os.path.join(ASSETS, "examples")
EXAMPLE_CATALOG = os.path.join(REFERENCES, "examples", "catalog")
EXTERNAL = re.compile(r"(src|href)\s*=\s*[\"']?\s*(https?:)?//", re.IGNORECASE)

# The synthetic id families used everywhere in this repository. Nothing else is
# allowed to look like a Webflow identifier; checks/repo-check.sh enforces it
# across the whole tree and these tests enforce it for the example.
SYNTHETIC_24HEX = re.compile(r"^0{22}[0-9a-f]{2}$")
SYNTHETIC_UUID = re.compile(r"^1111aaaa-0000-4000-8000-0{9}[0-9a-f]{3}$")

MEDIA_SIDEBAR_ID = "1111aaaa-0000-4000-8000-000000000009"
CANDIDATE_KEY = "candidate:partner-setup-steps"
NEW_STYLES = ("c-setupsteps", "c-setupsteps__li", "c-setupsteps__li__num")


def load(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def brief():
    return load(os.path.join(EXAMPLES, "example.brief.json"))


def manifest():
    return load(os.path.join(EXAMPLES, "example.manifest.json"))


def catalog_entry(slug):
    with open(os.path.join(EXAMPLE_CATALOG, f"{slug}.md"), "r", encoding="utf-8") as fh:
        return fh.read()


class ExampleBriefTests(unittest.TestCase):
    def test_brief_validates_with_approval(self):
        self.assertEqual(validate_brief.validate(brief(), require_approval=True), [])

    def test_the_same_brief_fails_only_on_approval_when_unapproved(self):
        """The approval gate is the only thing standing between a valid brief and Phase 5."""
        unapproved = brief()
        unapproved["approvedAt"] = None
        self.assertEqual(validate_brief.validate(unapproved), [])
        paths = sorted(v["path"] for v in validate_brief.validate(unapproved, require_approval=True))
        self.assertEqual(paths, ["approvedAt"])

    def test_reuse_mix(self):
        sections = brief()["sections"]
        levels = {s["reuseLevel"] for s in sections}
        self.assertEqual(levels, {"reused", "adapted", "new"}, "the example exercises all three reuse levels")
        adapted = [s for s in sections if s["reuseLevel"] == "adapted"]
        self.assertEqual([s["familySection"] for s in adapted], ["media-sidebar"])
        self.assertEqual(adapted[0]["adaptation"]["newVariant"], "media--right")
        new = [s for s in sections if s["reuseLevel"] == "new"]
        self.assertEqual([s["familySection"] for s in new], ["setup-steps"])
        self.assertEqual(new[0]["newComponentSpec"]["candidateSlug"], "partner-setup-steps")
        self.assertEqual(sorted(new[0]["newComponentSpec"]["newClasses"]), sorted(NEW_STYLES))

    def test_slot_statuses_and_images(self):
        sections = brief()["sections"]
        slots = [slot for s in sections for slot in s["slots"]]
        by_status = {}
        for slot in slots:
            by_status[slot["status"]] = by_status.get(slot["status"], 0) + 1
        self.assertEqual(by_status.get("draft"), 1)
        self.assertEqual(by_status.get("missing"), 1)
        self.assertEqual(by_status.get("manual"), 1, "a manual slot is what the publisher finishes by hand")
        self.assertGreater(by_status.get("final", 0), 20)
        for slot in slots:
            if slot["status"] in ("final", "draft", "manual"):
                self.assertTrue(slot["content"], slot["name"])
            else:
                self.assertIsNone(slot["content"], slot["name"])
        images = [img for s in sections for img in s.get("images", [])]
        self.assertEqual(sum(1 for i in images if "url" in i), 2)
        self.assertEqual(sum(1 for i in images if "assetName" in i), 3)
        self.assertTrue(all(i["alt"] for i in images))

    def test_brief_sections_name_components_the_catalog_names(self):
        """Components are keyed by name: every named section exists in the family entry
        (outline or shell), no section carries a Webflow id, and the ids the brief does
        carry (site, folder, page links) are from the synthetic set."""
        data = brief()
        entry = catalog_entry(data["family"])
        self.assertTrue(SYNTHETIC_24HEX.match(data["site"]["id"]), data["site"]["id"])
        self.assertTrue(SYNTHETIC_24HEX.match(data["page"]["folder"]["id"]), data["page"]["folder"]["id"])
        self.assertIn(data["page"]["folder"]["id"], entry, "the folder the brief uses is in the family's Allowed folders table")
        for section in data["sections"]:
            name = section.get("componentName")
            if name is None:
                continue
            self.assertIsNone(catalog_lint.WEBFLOW_ID.search(name),
                              f"{section['familySection']} names a Webflow id")
            if name == "loose" or name.startswith("candidate:"):
                continue
            self.assertIn(name, entry,
                          f"{section['familySection']} names {name!r}, which {data['family']}.md does not")
        loose = [s for s in data["sections"] if s.get("componentName") == "loose"]
        self.assertTrue(loose, "the example carries a loose section, as a hybrid family may")
        for s in loose:
            self.assertEqual(s["reuseLevel"], "reused")
            self.assertTrue(s["classPath"].startswith(("header.", "section.")))
            self.assertIsInstance(s["masterSection"], int)

    def test_no_lorem(self):
        text = json.dumps(brief()).lower()
        self.assertNotIn("lorem", text)
        self.assertNotIn("ipsum", text)


class ExampleOutlineTests(unittest.TestCase):
    def test_outline_renders_without_external_assets(self):
        template = render_outline.load_template(None)
        html = render_outline.render(brief(), template, generated_at="2026-01-05T18:40:00Z")
        self.assertIsNone(EXTERNAL.search(html))
        self.assertNotIn("{{", html)
        self.assertNotIn("<img", html)
        self.assertNotIn("<link", html)
        self.assertEqual(html.count('class="frame '), 4)
        self.assertIn("TODO: a4", html)
        self.assertIn("Approved 2026-01-05T18:30:00Z", html)
        for label in ("Reused", "Adapted", "New"):
            self.assertIn(f">{label}</span>", html)
        self.assertIn("new variant media--right", html)
        self.assertIn("Setup steps section · candidate", html)

    def test_unapproved_outline_says_so(self):
        template = render_outline.load_template(None)
        unapproved = brief()
        unapproved["approvedAt"] = None
        self.assertIn("Not yet approved", render_outline.render(unapproved, template))

    def test_committed_outline_file_is_self_contained(self):
        path = os.path.join(EXAMPLES, "example.outline.html")
        with open(path, "r", encoding="utf-8") as fh:
            html = fh.read()
        self.assertIsNone(EXTERNAL.search(html), path)
        self.assertIn("no external assets", html)

    def test_committed_outline_matches_the_committed_brief(self):
        """Regenerate with render_outline.py after editing the brief."""
        with open(os.path.join(EXAMPLES, "example.outline.html"), "r", encoding="utf-8") as fh:
            committed = fh.read()
        fresh = render_outline.render(brief(), render_outline.load_template(None))
        strip = re.compile(r"Generated [^<·]*·")
        self.assertEqual(strip.sub("", fresh), strip.sub("", committed),
                         "assets/examples/example.outline.html is stale; re-render it from the brief")


class ExampleGuardTests(unittest.TestCase):
    def test_fixture_pass(self):
        result = diff_inventory.diff(load(fixture("example", "pre.snapshot.json")),
                                     load(fixture("example", "post.pass.json")))
        self.assertEqual(result["verdict"], "pass", result)
        created = {(c["kind"], c["key"]) for c in result["created"]}
        self.assertIn(("variant", f"{MEDIA_SIDEBAR_ID}/media--right"), created)
        self.assertIn(("components", CANDIDATE_KEY), created)
        for cls in NEW_STYLES:
            self.assertIn(("styles", cls), created)
        self.assertEqual(result["counts"]["created"], 5)
        # instanceCount moved on two pre-existing components and must not count as an edit
        self.assertEqual(result["changedPreExisting"], [])

    def test_fixture_fail_names_the_edited_base_class(self):
        result = diff_inventory.diff(load(fixture("example", "pre.snapshot.json")),
                                     load(fixture("example", "post.fail.json")))
        self.assertEqual(result["verdict"], "fail")
        self.assertEqual([(c["kind"], c["key"]) for c in result["changedPreExisting"]], [("styles", "c-button")])
        self.assertEqual(result["created"], [])
        accepted = diff_inventory.diff(load(fixture("example", "pre.snapshot.json")),
                                       load(fixture("example", "post.fail.json")),
                                       accept=["styles:c-button"])
        self.assertEqual(accepted["verdict"], "pass")

    def test_cli_on_fixtures(self):
        ok = subprocess.run([sys.executable, script("diff_inventory.py"),
                             fixture("example", "pre.snapshot.json"), fixture("example", "post.pass.json")],
                            capture_output=True, text=True)
        self.assertEqual(ok.returncode, 0, ok.stdout)
        bad = subprocess.run([sys.executable, script("diff_inventory.py"),
                              fixture("example", "pre.snapshot.json"), fixture("example", "post.fail.json")],
                             capture_output=True, text=True)
        self.assertEqual(bad.returncode, 1)

    def test_fixture_ids_are_synthetic(self):
        pre = load(fixture("example", "pre.snapshot.json"))
        self.assertTrue(SYNTHETIC_24HEX.match(pre["siteId"]), pre["siteId"])
        for cid, component in pre["components"].items():
            self.assertTrue(SYNTHETIC_UUID.match(cid), cid)
            for pid in component["props"]:
                self.assertTrue(SYNTHETIC_UUID.match(pid), pid)
        for vid, variable in pre["variables"].items():
            self.assertTrue(SYNTHETIC_UUID.match(vid[len("variable-"):]), vid)
            self.assertTrue(SYNTHETIC_UUID.match(variable["collection"][len("collection-"):]), variable["collection"])


class ExampleManifestTests(unittest.TestCase):
    def test_manifest_is_a_valid_dry_run(self):
        man = manifest()
        self.assertEqual(m.validate_manifest(man), [])
        self.assertEqual(man["slug"], "orbit")
        self.assertEqual(man["family"], "product-landing")
        self.assertEqual(man["status"], "open")
        self.assertEqual(man["publishActions"], [])
        self.assertTrue(man["steps"])
        self.assertTrue(all(s["status"] == "skipped" for s in man["steps"]))
        self.assertTrue(all(s["note"].startswith("dry-run: not executed") for s in man["steps"]))
        actions = [s["action"] for s in man["steps"]]
        self.assertNotIn("publish_site", actions)
        self.assertNotIn("publish_branch", actions)
        # create_page duplicates the master and is immediately followed by the readback gate
        create = next(s for s in man["steps"] if s["action"] == "create_page")
        self.assertTrue(SYNTHETIC_24HEX.match(create["ids"]["duplicateOf"]))
        self.assertTrue(SYNTHETIC_24HEX.match(create["ids"]["parentFolderId"]))
        self.assertTrue(create["ids"]["draft"])
        self.assertEqual(man["steps"][create["seq"]]["action"], "get_page_metadata")
        self.assertEqual(man["briefHash"], m.brief_hash(brief()))

    def test_manifest_created_nothing_and_ships_nothing(self):
        man = manifest()
        self.assertEqual(man["created"], m.empty_created())
        self.assertEqual(m.ships(man)["shipsAtNextPublish"], [])
        self.assertEqual(man["guardVerdict"]["verdict"], "pass")
        self.assertTrue(man["preSnapshotHash"].startswith("sha256:"))
        self.assertTrue(man["postSnapshotHash"].startswith("sha256:"))

    def test_manifest_guard_verdict_matches_the_fixtures(self):
        man = manifest()
        fresh = diff_inventory.diff(load(fixture("example", "pre.snapshot.json")),
                                    load(fixture("example", "post.pass.json")))
        self.assertEqual(man["guardVerdict"], fresh,
                         "the manifest's recorded verdict must match what the fixtures produce")

    def test_manifest_instruction_paths_use_the_default_prefix(self):
        """The instruction prefix is configurable; the example uses the documented default."""
        paths = [p for s in manifest()["steps"] for p in s["ids"].get("instructionPaths", [])]
        self.assertTrue(paths)
        for path in paths:
            self.assertTrue(path.startswith("page-templates/"), path)

    def test_ships_list_if_the_example_ran(self):
        """Replay the planned writes as executed steps to show what would ship."""
        planned = manifest()
        live = m.create(slug=planned["slug"], surface=planned["surface"], site_id=planned["site"]["id"],
                        family=planned["family"], family_version=planned["familyVersion"],
                        template_model=planned["templateModel"], isolation_mode=planned["isolationMode"],
                        brief_hash_value=planned["briefHash"], started_at=planned["startedAt"])
        for step in planned["steps"]:
            m.append(live, tool=step["tool"], action=step["action"], status="ok", ids=step["ids"], note="replayed")
        kinds = [(i["kind"], i["id"]) for i in m.ships(live)["shipsAtNextPublish"]]
        self.assertIn(("component", CANDIDATE_KEY), kinds)
        for cls in NEW_STYLES:
            self.assertIn(("style", cls), kinds)

    def test_manifest_and_brief_agree_on_the_family(self):
        man, data = manifest(), brief()
        self.assertEqual(man["family"], data["family"])
        self.assertEqual(man["familyVersion"], data["familyVersion"])
        self.assertEqual(man["templateModel"], data["templateModel"])
        self.assertEqual(man["isolationMode"], data["isolationMode"])
        self.assertEqual(man["site"]["id"], data["site"]["id"])
        self.assertEqual(man["slug"], data["page"]["slug"])


class ExampleCliTests(unittest.TestCase):
    def test_validate_brief_cli_accepts_the_example(self):
        result = subprocess.run([sys.executable, script("validate_brief.py"),
                                 os.path.join(EXAMPLES, "example.brief.json"),
                                 "--require-approval"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertTrue(json.loads(result.stdout)["ok"])

    def test_catalog_lint_cli_accepts_the_example_catalog(self):
        result = subprocess.run([sys.executable, script("catalog_lint.py"), EXAMPLE_CATALOG],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertTrue(json.loads(result.stdout)["ok"])


if __name__ == "__main__":
    unittest.main()
