# Changelog

All notable changes to the `webflow-template` skill. The format follows
Keep a Changelog; versions follow semver and are mirrored in `SKILL.md`
frontmatter (`metadata.version`).

## [1.0.0] - Unreleased

First public release. The skill is site-agnostic: it ships the flows, the
rulebook, the schemas, and the scripts, and generates everything site-specific
at onboarding.

### Added

- `SKILL.md` entry point, explicit invocation only
  (`disable-model-invocation: true`).
- Flows: `onboard` (run first), `build` (Phases 0 to 7), `maintain`, `sync`,
  `resume`. Onboarding picks a store in its step 0 - Webflow Agent
  Instructions (the default on claude.ai and wherever there is no repository),
  a git repository (the reviewed path), or downloads only - measures the site
  identically in all three, and hands over a download bundle either way.
- The public-exposure guarantee: rulebook rule 19, a "What this can and cannot
  make public" section in `SKILL.md` and the repository README, a warning and a
  confirmation before every asset upload, an `alreadyPublic` list in
  `manifest.py ships` and in the build report, and a one-time check at
  onboarding that the instruction store does not appear in published output.
- References: the 19-rule Webflow MCP rulebook (rule 19 is the
  public-exposure guarantee), the interview question bank,
  the brief schema, the run manifest schema, the outline rendering spec, the
  catalog entry format, the candidates process, the unsupported-features list,
  and `webflow-conventions.md` as a template whose MEASURE rows are onboarding's
  worklist.
- Scripts (Python 3, standard library only): `validate_brief.py`,
  `render_outline.py`, `diff_inventory.py`, `catalog_lint.py`, `manifest.py`,
  `build_snapshot.py`, with `unittest` coverage and fixtures under
  `scripts/tests/`.
- A worked example for a fictional site: one catalog family and a filled
  conventions file in `references/examples/`, and a brief, a rendered outline,
  and a dry-run manifest in `assets/examples/`.
- `agents/openai.yaml` for Codex (`allow_implicit_invocation: false`, Webflow
  MCP dependency) and `.mcp.json` for Claude Code.
- `checks/repo_check.py` (via `checks/repo-check.sh`) at the repository root:
  manifest and metadata structure, plus a disclosure guard that fails on a
  Bridge App launch link, a secret-shaped token, or an identifier outside the
  synthetic set.

### Known limitations

- **The catalog ships empty.** Nothing works end to end until
  `flows/onboard.md` has run against a real site. That is deliberate; a catalog
  is not portable.
- **Branch-mode writes are unverified.** Onboarding can establish that element
  reads accept a branch page id. Whether writes on a branch page and
  `create_branch` without the Designer work is unknown until someone runs a
  branch-mode build and reports back.
- **The rate-limit behaviour in rule 10 is a shape, not a number.** The
  conservative defaults are a starting point; the real pacing for a site is
  whatever onboarding measures. A small site may need none of it.
- **Only the Webflow MCP server's own surface is covered.** Interactions,
  Google and Adobe fonts, roles and access, CMS schema changes, and publishing
  are manual Designer work (`references/unsupported.md`).
- **The worked example is fictional.** It exercises the scripts and shows the
  formats; it is not evidence that a build succeeds on any particular site.
