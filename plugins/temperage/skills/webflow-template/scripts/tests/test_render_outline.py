import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

from _paths import ASSETS, fixture, script

import render_outline


def load_example():
    with open(os.path.join(ASSETS, "brief.example.json"), "r", encoding="utf-8") as fh:
        return json.load(fh)


EXTERNAL = re.compile(r"(src|href)\s*=\s*[\"']?\s*(https?:)?//", re.IGNORECASE)


class RenderOutlineTests(unittest.TestCase):
    def setUp(self):
        self.brief = load_example()
        self.template = render_outline.load_template(None)
        self.assertIsNotNone(self.template, "assets/outline.template.html should be found from the script location")

    def test_output_is_self_contained(self):
        html = render_outline.render(self.brief, self.template, generated_at="2026-01-04T18:00:00Z")
        self.assertIsNone(EXTERNAL.search(html), "outline must not reference external assets")
        self.assertNotIn("{{", html, "all placeholders must be substituted")
        self.assertNotIn("<link", html)
        self.assertNotIn("<img", html)
        self.assertNotIn('<script src', html)

    def test_frames_sections_and_labels(self):
        html = render_outline.render(self.brief, self.template, generated_at="2026-01-04T18:00:00Z")
        for bp in ("desktop", "991", "767", "479"):
            self.assertIn(f'data-bp="{bp}"', html)
        self.assertEqual(html.count('class="frame '), 4)
        # every section appears once per frame
        self.assertEqual(html.count("#2 hero"), 4)
        for label in ("Reused", "Adapted", "New"):
            self.assertIn(f">{label}</span>", html)
        self.assertIn("TODO: quote", html)                 # missing slot placeholder
        self.assertIn("pill-missing", html)
        self.assertIn("new variant icon-top", html)         # adapted section
        self.assertIn("Comparison grid · candidate", html)  # new section
        self.assertIn("Not yet approved", html)
        self.assertIn("D1", html)                            # decisions panel
        self.assertIn('tr class="open"', html)
        self.assertIn("--color-brand-primary", html)         # token table
        self.assertIn("Hover lift on feature cards", html)   # handoff list
        self.assertIn("brief sha256:", html)

    def test_manual_slots_are_labelled_and_listed_in_the_handoff(self):
        brief = load_example()
        section = brief["sections"][0]
        section["slots"].append(
            {"name": "Hero body", "content": "Copy the publisher pastes", "status": "manual"}
        )
        html = render_outline.render(brief, self.template, generated_at="2026-01-07T00:00:00Z")
        self.assertIn("pill-manual", html)
        self.assertIn("publisher enters in the Designer", html)
        self.assertIn("Hero body", html)
        self.assertIn("the publisher fills in the", html)
        self.assertIn("Slots final / draft / missing / manual", html)

    def test_manual_slots_absent_leaves_handoff_unchanged(self):
        html = render_outline.render(self.brief, self.template, generated_at="2026-01-07T00:00:00Z")
        self.assertNotIn("pill-manual", html)
        self.assertNotIn("the publisher fills in the", html)

    def test_columns_collapse_per_breakpoint(self):
        three = {"layout": {"columns": 3}}
        self.assertEqual([render_outline.columns_at(three, bp) for bp in ("desktop", "991", "767", "479")], [3, 2, 2, 1])
        six = {"layout": {"columns": 6, "breakpoints": {"991": 3, "767": 3, "479": 2}}}
        self.assertEqual([render_outline.columns_at(six, bp) for bp in ("desktop", "991", "767", "479")], [6, 3, 3, 2])
        self.assertEqual(render_outline.columns_at({}, "desktop"), 1)
        self.assertEqual(render_outline.columns_at({"layout": {"columns": "nope"}}, "desktop"), 1)

    def test_content_is_escaped(self):
        brief = load_example()
        brief["sections"][1]["slots"][0]["content"] = "<script>alert(1)</script>"
        brief["page"]["title"] = "Title & <b>bold</b>"
        html = render_outline.render(brief, self.template)
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)
        self.assertIn("Title &amp; &lt;b&gt;bold&lt;/b&gt;", html)

    def test_fallback_template_when_missing(self):
        html = render_outline.render(self.brief, None)
        self.assertIn('data-bp="479"', html)
        self.assertIsNone(EXTERNAL.search(html))
        self.assertNotIn("{{", html)

    def test_rejects_non_object(self):
        with self.assertRaises(ValueError):
            render_outline.render(["x"], self.template)

    def test_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "outline.html")
            result = subprocess.run([sys.executable, script("render_outline.py"), os.path.join(ASSETS, "brief.example.json"), "-o", out], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(json.loads(result.stdout)["ok"])
            with open(out, "r", encoding="utf-8") as fh:
                self.assertIn("<!doctype html>", fh.read().lower())
        stdout = subprocess.run([sys.executable, script("render_outline.py"), os.path.join(ASSETS, "brief.example.json")], capture_output=True, text=True)
        self.assertEqual(stdout.returncode, 0)
        self.assertIn("Section mapping", stdout.stdout)
        missing = subprocess.run([sys.executable, script("render_outline.py"), fixture("nope.json")], capture_output=True, text=True)
        self.assertEqual(missing.returncode, 2)
        help_result = subprocess.run([sys.executable, script("render_outline.py"), "--help"], capture_output=True, text=True)
        self.assertEqual(help_result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
