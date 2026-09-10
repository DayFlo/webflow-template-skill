import json
import os
import subprocess
import sys
import tempfile
import unittest

from _paths import REFERENCES, fixture, script

import catalog_lint


class FrontMatterParserTests(unittest.TestCase):
    def test_scalars_and_lists(self):
        text = "---\nname: Product landing\nslug: 'product-landing'\nallowedFolders:\n  - /products\n  - /integrations\nversion: \"1.0.0\"\n---\nbody\n"
        fields, body, errors = catalog_lint.parse_front_matter(text)
        self.assertEqual(errors, [])
        self.assertEqual(fields["name"], "Product landing")
        self.assertEqual(fields["slug"], "product-landing")
        self.assertEqual(fields["version"], "1.0.0")
        self.assertEqual(fields["allowedFolders"], ["/products", "/integrations"])
        self.assertEqual(body.strip(), "body")

    def test_unclosed_and_missing(self):
        _, _, errors = catalog_lint.parse_front_matter("---\nname: x\n")
        self.assertTrue(any("not closed" in e for e in errors))
        _, _, errors = catalog_lint.parse_front_matter("# no front matter\n")
        self.assertTrue(any("must start" in e for e in errors))

    def test_table_parser(self):
        header, rows = catalog_lint.parse_table("text\n| A | B |\n| --- | --- |\n| 1 | 2 |\n| 3 | |\n\nafter")
        self.assertEqual(header, ["a", "b"])
        self.assertEqual(rows, [{"a": "1", "b": "2"}, {"a": "3", "b": ""}])


class CatalogLintTests(unittest.TestCase):
    def test_valid_catalog_passes(self):
        result = catalog_lint.lint(fixture("catalog_valid"), fixture("catalog_valid", "sync-state.json"))
        self.assertTrue(result["ok"], result["errors"])
        self.assertEqual(sorted(f["slug"] for f in result["families"]), ["integration-page", "partner-page", "product-landing"])
        self.assertEqual(result["errors"], [])

    def test_proposed_status_and_loose_rows_are_accepted(self):
        result = catalog_lint.lint(fixture("catalog_valid"))
        partner = next(f for f in result["families"] if f["slug"] == "partner-page")
        self.assertEqual(partner["status"], "proposed")
        self.assertEqual(partner["templateModel"], "duplicate-master")
        # loose rows are counted but never enter the cross-family component list
        self.assertEqual(partner["looseSections"], 2)
        self.assertEqual(partner["candidateSections"], 1)
        self.assertEqual(partner["components"], ["Setup steps"])
        promoted = next(f for f in result["families"] if f["slug"] == "product-landing")
        self.assertEqual(promoted["status"], "promoted")
        self.assertEqual(promoted["looseSections"], 0)

    def test_additional_schema_types(self):
        # optional list beside schemaType; a scalar, an empty list, a blank item, or a repeat of schemaType is an error
        result = catalog_lint.lint(fixture("catalog_valid"))
        self.assertTrue(result["ok"], result["errors"])
        by_slug = {f["slug"]: f for f in result["families"]}
        self.assertEqual(by_slug["product-landing"]["schemaTypes"], ["WebPage", "FAQPage"])
        self.assertEqual(by_slug["partner-page"]["schemaTypes"], ["SoftwareApplication"], "no additionalSchemaTypes means schemaType alone")
        broken = catalog_lint.lint(fixture("catalog_broken"))
        schema_errors = [e for e in broken["errors"] if e["rule"] == "FM-SCHEMA"]
        self.assertEqual([e["file"] for e in schema_errors], ["bad-family.md"])
        self.assertIn("must be a list", schema_errors[0]["message"])
        for text, expected in (
            ("additionalSchemaTypes:\n", "is empty"),
            ("additionalSchemaTypes:\n  - FAQPage\n  - ''\n", "empty item"),
            ("additionalSchemaTypes:\n  - WebPage\n", "repeats schemaType"),
        ):
            fields, _, errors = catalog_lint.parse_front_matter("---\nname: x\nslug: x\nversion: 1.0.0\nschemaType: WebPage\n" + text + "---\nbody\n")
            self.assertEqual(errors, [])
            with tempfile.TemporaryDirectory() as tmp:
                with open(os.path.join(tmp, "x.md"), "w", encoding="utf-8") as fh:
                    fh.write("---\nname: x\nslug: x\nversion: 1.0.0\ntemplateModel: component-recipe\nisolationDefault: draft-main\n"
                             "allowedFolders:\n  - /x\nschemaType: WebPage\n" + text + "---\n"
                             "## Purpose\nx\n## Section outline\n| # | Section | Component name | Class path | Owner | Required | Props | Variants | Slots | Content guidance | Image sizes |\n"
                             "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| 1 | hero | Hero | | shared | required | | | | | |\n"
                             "## Shell components\n## Allowed folders\n| Path | Folder ID |\n| --- | --- |\n| /x | 0000000000000000000000c5 |\n"
                             "## SEO and Open Graph defaults\nx\n## JSON-LD template\nx\n## Example pages\n## Do and don't\nx\n## Changelog\n- 1.0.0 (2026-01-06): x\n")
                messages = " ".join(e["message"] for e in catalog_lint.lint(tmp)["errors"] if e["rule"] == "FM-SCHEMA")
                self.assertIn(expected, messages, text)

    def test_shipped_catalog_is_empty(self):
        """The skill ships without a catalog: onboarding generates it per site."""
        catalog_dir = os.path.join(REFERENCES, "catalog")
        entries = [n for n in sorted(os.listdir(catalog_dir))
                   if n.endswith(".md") and n.lower() != "readme.md"]
        self.assertEqual(entries, [], "references/catalog/ must ship empty; flows/onboard.md writes it")
        result = catalog_lint.lint(catalog_dir)
        self.assertTrue(result["ok"], result["errors"])
        self.assertEqual(result["families"], [])

    def test_example_catalog_is_a_promoted_family_and_lints(self):
        """references/examples/catalog/ is the worked example the README points at."""
        result = catalog_lint.lint(os.path.join(REFERENCES, "examples", "catalog"))
        self.assertTrue(result["ok"], result["errors"])
        by_slug = {f["slug"]: f for f in result["families"]}
        self.assertIn("product-landing", by_slug)
        fam = by_slug["product-landing"]
        self.assertEqual(fam["status"], "promoted")
        self.assertGreaterEqual(int(fam["version"].split(".")[0]), 1)
        self.assertEqual(fam["candidateSections"], 0, "a promoted family may not carry candidate placeholders")
        self.assertEqual(fam["looseSections"], 1, "the example shows the loose convention")
        self.assertEqual(fam["schemaTypes"], ["WebPage", "FAQPage"])

    def test_extra_h2_sections_are_tolerated(self):
        with open(fixture("catalog_valid", "partner-page.md"), "r", encoding="utf-8") as fh:
            text = fh.read()
        _, body, _ = catalog_lint.parse_front_matter(text)
        sections = catalog_lint.parse_sections(body)
        self.assertIn("Audience", sections)
        self.assertIn("Reference image", sections)
        result = catalog_lint.lint(fixture("catalog_valid"))
        self.assertFalse([e for e in result["errors"] if e["rule"] == "HEADINGS"])

    def test_loose_rejected_for_recipe_and_shell(self):
        result = catalog_lint.lint(fixture("catalog_broken"))
        errors = [e for e in result["errors"] if e["file"] == "recipe-loose.md"]
        rules = {e["rule"] for e in errors}
        self.assertIn("OUTLINE-LOOSE", rules)
        self.assertIn("SHELL-TABLE", rules)
        self.assertIn("FM-STATUS", rules)
        messages = " ".join(e["message"] for e in errors)
        self.assertIn("not allowed when templateModel is component-recipe", messages)
        self.assertIn("master's class path", messages)
        self.assertIn("Owner 'self'", messages)
        self.assertIn("'loose' is only valid in the section outline", messages)
        self.assertIn("status 'draft' must be one of proposed, promoted, deprecated", messages)

    def test_empty_catalog_passes(self):
        result = catalog_lint.lint(fixture("catalog_empty"))
        self.assertTrue(result["ok"])
        self.assertEqual(result["families"], [])

    def test_bundled_catalog_and_sync_state_pass(self):
        result = catalog_lint.lint(os.path.join(REFERENCES, "catalog"), os.path.join(REFERENCES, "sync-state.json"))
        self.assertTrue(result["ok"], result["errors"])

    def test_broken_catalog_reports_rules(self):
        result = catalog_lint.lint(fixture("catalog_broken"), fixture("catalog_broken", "sync-state-missing-keys.json"))
        self.assertFalse(result["ok"])
        rules = {e["rule"] for e in result["errors"]}
        for rule in ("FM-SLUG", "FM-VERSION", "FM-ISOLATION", "FM-MASTER", "FM-FOLDERS", "FM-SCHEMA", "HEADINGS", "OUTLINE-TABLE",
                     "FOLDERS-TABLE", "EXAMPLES-TABLE", "XREF-UNIQUE", "XREF-BORROW", "CHANGELOG", "SYNC-STATE", "COMPONENT-ID"):
            self.assertIn(rule, rules, f"{rule} not reported")
        messages = " ".join(e["message"] for e in result["errors"])
        self.assertIn("does not match file name", messages)
        self.assertIn("requires masterPageId", messages)
        self.assertIn("already owned by family", messages)
        self.assertIn("Component name is empty", messages)
        self.assertIn("unknown family 'ghost-family'", messages)
        self.assertIn("missing key 'lastSync'", messages)
        self.assertIn("Owner must be", messages)
        self.assertIn("use the leaf slug", messages)                  # masterPageSlug given as a path
        self.assertIn("OUTLINE-CANDIDATE", rules)
        self.assertIn("not allowed in a promoted family", messages)
        self.assertIn("must be 'candidate:<kebab-slug>'", messages)
        self.assertIn("candidate placeholder row must have Owner 'self'", messages)

    def test_component_ids_are_rejected_in_component_columns(self):
        """Components are keyed by name; a Webflow id in a component column is an error."""
        result = catalog_lint.lint(fixture("catalog_broken"))
        errors = [e for e in result["errors"] if e["rule"] == "COMPONENT-ID"]
        wheres = sorted(e["message"].split(":")[0] for e in errors)
        self.assertEqual(wheres, ["section outline row 5", "section outline row 6", "shell row 1"])
        messages = " ".join(e["message"] for e in errors)
        self.assertIn("carries a Webflow component id", messages)            # bare 24-hex cell
        self.assertIn("1111aaaa-0000-4000-8000-000000000009", messages)      # dashed id beside a name
        self.assertIn("the catalog names components", messages)
        # the id-bearing rows never reach the ownership index
        broken = next(f for f in result["families"] if f["file"] == "bad-family.md")
        self.assertNotIn("0000000000000000000000d1", broken["components"])

    def test_class_path_belongs_to_loose_rows_only(self):
        result = catalog_lint.lint(fixture("catalog_broken"))
        messages = " ".join(e["message"] for e in result["errors"] if e["file"] == "bad-family.md")
        self.assertIn("Class path is only for 'loose' rows", messages)

    def test_committed_catalogs_carry_no_component_ids(self):
        """No committed catalog entry may name a component by id (rule COMPONENT-ID)."""
        for catalog_dir in (os.path.join(REFERENCES, "catalog"),
                            os.path.join(REFERENCES, "examples", "catalog"),
                            fixture("catalog_valid")):
            result = catalog_lint.lint(catalog_dir)
            self.assertEqual([e for e in result["errors"] if e["rule"] == "COMPONENT-ID"], [], catalog_dir)
            for family in result["families"]:
                for name in family["components"]:
                    self.assertIsNone(catalog_lint.WEBFLOW_ID.search(name), f"{family['file']}: {name}")

    def test_sync_state_not_json(self):
        result = catalog_lint.lint(fixture("catalog_valid"), fixture("catalog_broken", "sync-state-not-json.json"))
        self.assertFalse(result["ok"])
        self.assertEqual([e["rule"] for e in result["errors"]], ["SYNC-STATE"])

    def test_cli_exit_codes(self):
        ok = subprocess.run([sys.executable, script("catalog_lint.py"), fixture("catalog_valid"), "--sync-state", fixture("catalog_valid", "sync-state.json")], capture_output=True, text=True)
        self.assertEqual(ok.returncode, 0, ok.stdout)
        self.assertTrue(json.loads(ok.stdout)["ok"])
        bad = subprocess.run([sys.executable, script("catalog_lint.py"), fixture("catalog_broken")], capture_output=True, text=True)
        self.assertEqual(bad.returncode, 1)
        self.assertFalse(json.loads(bad.stdout)["ok"])
        missing = subprocess.run([sys.executable, script("catalog_lint.py"), fixture("no-such-dir")], capture_output=True, text=True)
        self.assertEqual(missing.returncode, 2)
        help_result = subprocess.run([sys.executable, script("catalog_lint.py"), "--help"], capture_output=True, text=True)
        self.assertEqual(help_result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
