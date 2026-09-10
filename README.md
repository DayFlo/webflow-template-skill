# webflow-template

Turns a design into an **unpublished draft page** in a Webflow site, built
from a reusable template family: the components, styles, variables, and
layout conventions the site already has. Never publishes.

This repository is a plugin marketplace. One plugin,
`design-automations`, carries the skill. Claude Code and Codex install
from the repo. Claude.ai does not: zip the skill folder and upload it.
After that, the catalog lives in Webflow, not git.

**Onboard first.** Families name components that exist on one site, so
there is no portable catalog to ship. Until onboarding has run, a build
stops at template selection.

Every build: receive a design → digest it → interview the submitter →
pick a family → approve a visual outline → build an unpublished page →
verify by readback → report and hand off.

## Install

### Claude Code

```
/plugin marketplace add DayFlo/webflow-template-skill
/plugin install design-automations@webflow-template-skill
```

Invoke: `/design-automations:webflow-template`. Plugin skills are
namespaced. The unqualified form works only for a copy in
`.claude/skills`. The skill will not auto-fire
(`disable-model-invocation: true`).

The plugin ships `.mcp.json` pointing at `https://mcp.webflow.com/mcp`.
Claude Code prompts for the Webflow OAuth flow on first use.

### Codex

Copy or symlink the skill folder into the Codex user skills directory:

```
ln -s "$PWD/plugins/design-automations/skills/webflow-template" "$HOME/.agents/skills/webflow-template"
```

Register the MCP server in `~/.codex/config.toml`:

```toml
[mcp_servers.webflow]
url = "https://mcp.webflow.com/mcp"
```

Invoke: `$webflow-template`. `agents/openai.yaml` sets
`allow_implicit_invocation: false`.

### Claude.ai

Zip the skill folder (not the marketplace root) and upload it, or have a
Team / Enterprise owner provision it.

```
cd plugins/design-automations/skills
zip -r webflow-template.zip webflow-template
```

The archive must contain the `webflow-template/` directory as its root.
Claude.ai rejects a zip whose folder name does not match the skill name.
Do not send the GitHub URL; a private repository will not help.

1. Paid Claude (Pro, Max, Team, or Enterprise). Turn on **Code execution
   and file creation** (Pro / Max: **Settings → Capabilities**; Team /
   Enterprise: **Organization settings → Skills**).
2. **Customize → Skills** → **+ Create skill** → **Upload a skill**, or
   have an owner add it under **Organization settings → Skills → + Add**.
3. Connect the Webflow connector in a chat (**+** → **Connectors** →
   **Webflow**). The `agent_instructions:read` and
   `agent_instructions:write` scopes let the catalog live in Webflow.
4. Start a chat and select **webflow-template** by name.

Python scripts only run there if code execution is enabled. Every script
has a written fallback the skill follows by hand when it is not.

## Usage

Ask for a flow by name: **onboard**, **build**, **maintain**, **sync**,
or **resume**.

| Surface | Invoke |
| --- | --- |
| Claude Code | `/design-automations:webflow-template` |
| Codex | `$webflow-template` |
| Claude.ai | select **webflow-template** by name |

## Onboarding

`flows/onboard.md` reads a site once, read-only, and writes the catalog,
filled conventions, a gitignored site inventory, and the rulebook
installed into Webflow Agent Instructions. Its first step picks a store:

| Store | Default for | Where the catalog lives | What reviews a change |
| --- | --- | --- | --- |
| **Webflow** | claude.ai, and anyone without repo write access | Webflow Agent Instructions under the instruction prefix (default `page-templates`) | the person in the conversation, at each write |
| **Repository** | maintainers on Claude Code or Codex with git | files under `references/`, pushed to Webflow by the sync flow | a pull request |
| **Downloads only** | the fallback when the `agent_instructions` scopes are missing | files the user keeps and re-attaches to each build | nobody |

Measuring is identical in all three. Every path also hands over a
**download bundle** (one JSON file, or one HTML page). A build accepts
that bundle when it cannot read the store.

The Webflow store has no pull request. What stands in for one: confirm
before each write, keep proposed families as drafts until a maintainer
confirms them, and treat the bundle as the only history.

A worked example for a fictional site lives under
`plugins/design-automations/skills/webflow-template/references/examples/`
and `.../assets/examples/`. Onboarding does not touch it.

## What this can and cannot make public

Using this skill must not put anything on the public internet. Only one of
the writes it makes can, and it says so at the moment it makes it. The
full rule is `references/rules.md` rule 19; the same table is in
`SKILL.md`.

| What | Public? | The guarantee |
| --- | --- | --- |
| **The draft page** | No | Created with `draft: true` set explicitly and confirmed by readback. Draft pages are excluded from publishing, so the page does not go live at the next site publish either. A human turns the flag off. |
| **New components, styles, variables** | Not yet - **at the next site publish, yes** | Site-level, so they ship whenever anyone next publishes the site, even though the page stays a draft. Every run reports them as the ships-at-next-publish list. Branch mode keeps them off main until merge. |
| **Uploaded assets** | **Yes, immediately** | This is the one exception. `asset_tool > upload_image_by_url` puts the file in the site's asset library, and Webflow serves library assets from a public CDN URL from the moment of upload, before any publish and whether or not the page is ever published. The build warns and asks before every upload, prefers an asset already in the library, and reports each one as an "already public" line, separate from and more urgent than ships-at-next-publish. Deleting an asset later does not un-serve a URL someone already has. |
| **Branch staging publish** | Gated, not open | Only on explicit request in that turn, only in branch mode, only to staging, never production. Measured, not assumed: an anonymous request to a Webflow branch staging URL redirects to the Webflow login and returns HTTP 403. |
| **Agent Instructions** (the catalog store) | Evidence says no; no vendor statement | Gated behind `agent_instructions:read`, delivered to authorized MCP clients as site metadata, no publish path, never in page content. Not a guarantee: onboarding runs a one-time check per site (write a throwaway instruction with a unique marker, have a human publish on their normal cadence, confirm the marker appears nowhere in public output, delete it). |
| **CMS items** | Never used | Standing non-goal. The Data API models CMS items with staged and live states and publish and unpublish events: they are publish-shaped by design, so a catalog entry, brief, candidate, or run record kept in a collection would sit one publish away from the public internet. |

`checks/repo-check.sh` fails if this section disappears from either file,
or if the rulebook stops forbidding `publish_site`.

## Safety

The table above is the publish story. These are the rest:

- Never calls `publish_site`. `publish_branch` only to staging, only in
  branch mode, only on explicit request, always recorded.
- Never edits a pre-existing shared definition (class, base variant,
  variable). A pre/post inventory guard fails the run if anything
  pre-existing changed.
- Never deletes anything the run did not create.
- Every Webflow write is appended to a run manifest before the next
  write.
- The Webflow Designer Bridge App launch link is a credential. Never
  written to a file, a manifest, a run record, or a commit.

The full rulebook is
`plugins/design-automations/skills/webflow-template/references/rules.md`
(19 rules). It is installed into the site's Agent Instructions so every
other agent connected to the site reads the same rules.

## Requirements

- Claude Code, Codex, or paid Claude.ai (Pro, Max, Team, or Enterprise)
- Webflow MCP connector (OAuth). Claude Code prompts on first use.
- Python 3.11 for local scripts (standard library only). Claude.ai uses a
  written fallback when code execution is off.

## Development

```
.claude-plugin/marketplace.json        Claude Code marketplace manifest
.agents/plugins/marketplace.json       Codex marketplace manifest
checks/repo-check.sh                   structure + disclosure checks
plugins/design-automations/
  .claude-plugin/plugin.json
  .mcp.json                            Webflow MCP server
  skills/webflow-template/
    SKILL.md                           entry point, explicit invocation only
    flows/                             onboard, build, maintain, sync, resume
    references/                        rulebook, schemas, catalog format
    scripts/                           six Python 3 scripts, standard library only
```

```
cd plugins/design-automations/skills/webflow-template/scripts
python3 -m unittest discover -s tests
```

```
bash checks/repo-check.sh
REPO_CHECK_LIVE=1 bash checks/repo-check.sh   # also runs claude plugin validate
```

118 unit tests. No live Webflow run in this repository, and nothing here
talks to the network.

Every Webflow-shaped identifier in this tree is synthetic:

| Shape | Pattern | Used for |
| --- | --- | --- |
| 24-hex | `0000000000000000000000xx` | sites, pages, folders |
| UUID | `1111aaaa-0000-4000-8000-000000000xxx` | components, props, variables |

`checks/repo-check.sh` fails on any identifier outside those two
patterns, on any Bridge App launch link, and on any other long
secret-shaped token.

## License

MIT. See `LICENSE`. Copyright (c) 2026 Dayton Floyd.
