"""The public-exposure guarantee is enforced by checks/repo_check.py.

These tests only run from a full checkout of the marketplace repository: the
skill folder is also distributed on its own (symlinked into a Codex or Claude
skills directory), and then there is no checks/ directory to import.
"""
import contextlib
import importlib.util
import io
import os
import shutil
import tempfile
import unittest

from _paths import SKILL_DIR

# SKILL_DIR is <root>/plugins/temperage/skills/webflow-template
REPO_ROOT = os.path.abspath(os.path.join(SKILL_DIR, "..", "..", "..", ".."))
CHECKER = os.path.join(REPO_ROOT, "checks", "repo_check.py")
SKILL_REL = os.path.join("plugins", "temperage", "skills", "webflow-template")


def load_checker():
    spec = importlib.util.spec_from_file_location("repo_check_under_test", CHECKER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def paths_for(root):
    skill = os.path.join(root, SKILL_REL)
    return {
        "root": root,
        "skill": skill,
        "skill_md": os.path.join(skill, "SKILL.md"),
        "readme": os.path.join(root, "README.md"),
        "rules": os.path.join(skill, "references", "rules.md"),
        "build": os.path.join(skill, "flows", "build.md"),
    }


@unittest.skipUnless(os.path.isfile(CHECKER), "checks/repo_check.py is not in this checkout")
class PublicExposureCheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.checker = load_checker()

    def run_check(self, paths):
        """Number of failures. The checker prints its own PASS/FAIL lines; they
        are swallowed here so the test output stays readable."""
        report = self.checker.Report()
        with contextlib.redirect_stdout(io.StringIO()):
            self.checker.check_public_exposure(paths, report)
        return report.fails

    def test_the_real_tree_passes(self):
        self.assertEqual(self.run_check(paths_for(REPO_ROOT)), 0)

    def _copy(self, tmp):
        """A minimal tree carrying only the four files the check reads."""
        for rel in ("README.md",
                    os.path.join(SKILL_REL, "SKILL.md"),
                    os.path.join(SKILL_REL, "references", "rules.md"),
                    os.path.join(SKILL_REL, "flows", "build.md")):
            dest = os.path.join(tmp, rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copyfile(os.path.join(REPO_ROOT, rel), dest)
        return paths_for(tmp)

    def _mutate(self, key, old, new):
        with tempfile.TemporaryDirectory() as tmp:
            paths = self._copy(tmp)
            with open(paths[key], encoding="utf-8") as fh:
                text = fh.read()
            self.assertIn(old, text)
            with open(paths[key], "w", encoding="utf-8") as fh:
                fh.write(text.replace(old, new))
            return self.run_check(paths)

    def test_deleting_the_section_from_the_readme_fails(self):
        self.assertGreater(
            self._mutate("readme", "## What this can and cannot make public", "## Something else"), 0)

    def test_deleting_the_section_from_skill_md_fails(self):
        self.assertGreater(
            self._mutate("skill_md", "## What this can and cannot make public", "## Something else"), 0)

    def test_dropping_the_publish_site_prohibition_fails(self):
        self.assertGreater(self._mutate("rules", "Never call `publish_site`", "Rarely call it"), 0)

    def test_dropping_the_asset_warning_from_the_rulebook_fails(self):
        self.assertGreater(self._mutate("rules", "from the moment of upload", "eventually"), 0)

    def test_dropping_the_asset_warning_from_the_build_flow_fails(self):
        self.assertGreater(self._mutate("build", "from the moment of upload", "eventually"), 0)


if __name__ == "__main__":
    unittest.main()
