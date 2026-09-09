# Changelog

Notable changes to this repository: the marketplace root, the
`design-automations` plugin, and the checks. The `webflow-template` skill keeps
its own changelog at
`plugins/design-automations/skills/webflow-template/CHANGELOG.md`, and that is
the version `SKILL.md` mirrors.

The format follows Keep a Changelog; versions follow semver.

## [1.0.0] - Unreleased

First public release.

### Added

- Marketplace root: `.claude-plugin/marketplace.json` for Claude Code and
  `.agents/plugins/marketplace.json` for Codex, both named
  `webflow-template-skill`.
- The `design-automations` plugin at `plugins/design-automations`, carrying the
  `webflow-template` skill and a `.mcp.json` for the Webflow MCP server. The
  plugin name is kept so the invocation is
  `/design-automations:webflow-template`.
- `checks/repo_check.py`, run by the `checks/repo-check.sh` wrapper: manifests
  parse and carry the keys Claude Code and Codex need; the documented command
  form is the namespaced one; the skill version matches its changelog; the
  shipped catalog is empty; the licence names a copyright holder. Then the
  disclosure guard: no Bridge App launch link, no long secret-shaped token, no
  home-directory path, no branch staging domain, and no Webflow-shaped
  identifier outside the repository's synthetic set. It uses no git and no
  network so it runs in any checkout.
- `.github/workflows/ci.yml`: unit tests, catalog lint on the shipped
  (empty) catalog and on the worked example, brief validation, and
  `checks/repo-check.sh`.
- MIT `LICENSE`, Copyright (c) 2026 Dayton Floyd.
- A public-exposure guarantee that cannot be quietly deleted: `repo_check.py`
  fails unless the "What this can and cannot make public" section is present in
  both `README.md` and the skill's `SKILL.md`, the rulebook still forbids
  `publish_site`, and the uploaded-asset warning is still in the rulebook and
  the build flow.

### Notes

The skill is site-agnostic by construction. Nothing about any particular
Webflow site is baked into the flows, rulebook, schemas, or scripts: every
fact a build depends on is measured at onboarding and recorded in
`references/webflow-conventions.md`. No catalog, no site inventory, and no run
records are shipped, and every identifier in the tree is synthetic.
