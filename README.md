# webflow-template

A Claude Code / Claude.ai / Codex skill that turns a design into an
**unpublished draft page** in a Webflow site, built from a reusable **template
family** — the components, styles, variables, and layout conventions the site
already has. It never publishes.

The shape of every build is fixed:

> receive a design → digest it → interview the submitter → pick a family →
> approve a visual outline → build an unpublished page → verify by readback →
> report and hand off

Alongside the build flow it carries the maintainer flows: onboard a site,
maintain the template catalog, sync the catalog to Webflow Agent Instructions,
and resume or clean up an interrupted run.

## What this can and cannot make public

Using this skill must not put anything on the public internet. Four categories
of write, and the guarantee for each (the full rule is `references/rules.md`
rule 19; the same table is in `SKILL.md`):

| What | Public? | The guarantee |
| --- | --- | --- |
| **The draft page** | No | Created with `draft: true` set explicitly and confirmed by readback. Draft pages are excluded from publishing, so the page does not go live at the next site publish either. A human turns the flag off. |
| **New components, styles, variables** | Not yet - **at the next site publish, yes** | Site-level, so they ship whenever anyone next publishes the site, even though the page stays a draft. Every run reports them as the ships-at-next-publish list. Branch mode keeps them off main until merge. |
| **Uploaded assets** | **Yes, immediately** | This is the one exception. `asset_tool > upload_image_by_url` puts the file in the site's asset library, and Webflow serves library assets from a public CDN URL from the moment of upload, before any publish and whether or not the page is ever published. The build warns and asks before every upload, prefers an asset already in the library, and reports each one as an "already public" line, separate from and more urgent than ships-at-next-publish. Deleting an asset later does not un-serve a URL someone already has. |
| **Branch staging publish** | Gated, not open | Only on explicit request in that turn, only in branch mode, only to staging, never production. Measured, not assumed: an anonymous request to a Webflow branch staging URL redirects to the Webflow login and returns HTTP 403. |

Two more, because they are where the data lives:

- **Agent Instructions**, the store the catalog can live in, are gated behind
  the `agent_instructions:read` scope, delivered to authorized MCP clients as
  site metadata, with no publish path and no presence in page content. That is
  strong evidence they are not public, but no explicit vendor statement was
  found, so it is not stated as a guarantee: onboarding runs a one-time check
  per site (write a throwaway instruction with a unique marker, have a human
  publish on their normal cadence, confirm the marker appears nowhere in public
  output, delete it).
- **CMS items are never used as a store. Standing non-goal.** The Data API
  models CMS items with staged and live states and publish and unpublish
  events: they are publish-shaped by design, so a catalog entry, brief,
  candidate, or run record kept in a collection would sit one publish away from
  the public internet.

`checks/repo-check.sh` fails if this section disappears from either file, or if
the rulebook stops forbidding `publish_site`.

## Onboarding runs first

**The skill ships without a catalog, and that is deliberate.** A template
family names components, master pages, and folders that exist on exactly one
Webflow site, so there is no portable catalog to ship. `flows/onboard.md` reads
a site once, read-only, and generates (these are the file names of the
repository store; the same content has other homes, see the table below):

- `references/catalog/<family>.md`, one entry per template family;
- `references/webflow-conventions.md`, which ships as a template full of
  placeholders and comes back filled with what onboarding measured;
- a local site inventory (gitignored; it is a complete map of the site);
- `references/sync-state.json`, and the rulebook and catalog installed into
  Webflow Agent Instructions.

Until that has run, a build gets as far as template selection and stops.

**Onboarding does not need a repository, and neither do you.** Its first step
picks a store:

| Store | Default for | Where the catalog lives | What reviews a change |
| --- | --- | --- | --- |
| **Webflow** | claude.ai, and anyone without repo write access | Webflow Agent Instructions under the instruction prefix (default `page-templates`) | the person in the conversation, at each write |
| **Repository** | maintainers on Claude Code or Codex with git | files under `references/`, pushed to Webflow by the sync flow | a pull request |
| **Downloads only** | the fallback when the `agent_instructions` scopes are missing | files the user keeps and re-attaches to each build | nobody |

The measuring is identical in all three. Every one of them also hands over the
same content as a **download bundle** (one JSON file, or one HTML page; chat
accepts HTML, JSON and plain text but not zip), and a build accepts that bundle
when it cannot read the store.

The cost of the Webflow store is stated rather than hidden: **there is no pull
request, so there is no second reader.** What stands in for one is an explicit
confirmation before each write, proposed families kept as drafts until a
maintainer confirms them, a `## Decisions` section inside every entry, and the
bundle as the only history. `flows/maintain.md` describes promoting and pruning
through conversation when there is no repository.

The same applies to the facts the flows depend on. The request pacing, whether
loose-section content is reachable at all, whether branching is available, the
breakpoint list, whether component names are unique, whether the connector
token can write page schema: none of these is a constant. Each is a MEASURE row
in the conventions template, and a row that has not been measured stays
UNMEASURED and is treated as unknown rather than guessed.

A worked example for a fictional site — one catalog entry, a filled conventions
file, a brief, a rendered outline, and a dry-run manifest — is under
`plugins/design-automations/skills/webflow-template/references/examples/` and
`.../assets/examples/`. It exists so the formats are legible before you have a
catalog of your own. Onboarding does not touch it.

## Install

The repository is a plugin marketplace root: a `.claude-plugin/marketplace.json`
for Claude Code, an `.agents/plugins/marketplace.json` for Codex, and one plugin
directory, `plugins/design-automations`, containing the skill.

### Claude Code

```
/plugin marketplace add DayFlo/webflow-template-skill
/plugin install design-automations@webflow-template-skill
```

Then invoke it by name: `/design-automations:webflow-template`. Plugin skills
are namespaced, so the unqualified form (skill name only, no plugin prefix)
works only for a copy placed in `.claude/skills`.

The plugin ships `.mcp.json` pointing at `https://mcp.webflow.com/mcp`. Claude
Code will prompt for the Webflow OAuth flow on first use.

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

Then invoke with `$webflow-template`. `agents/openai.yaml` sets
`allow_implicit_invocation: false`, so Codex will not pick the skill up from
unrelated conversation.

### Claude.ai

Distribute the plugin through your organization's plugin settings, connect the
first-party Webflow connector, and select "webflow-template" by name. Python
scripts only run there if code execution is enabled; every script has a written
fallback procedure the skill follows by hand when it is not.

The whole story on claude.ai, end to end, with no repository and no git:

1. **Onboard once.** Ask for onboarding by name. It probes the instruction
   store once, measures the site read-only, proposes families, asks you to
   confirm them, and writes the catalog, the filled conventions, and the index
   into Webflow Agent Instructions under the instruction prefix - asking before
   each write, because that confirmation is the only review this path has.
2. **Keep the bundle.** Onboarding hands you the same content as one JSON file
   (or one HTML page). Keep it: if a build ever cannot read the store, attach
   the bundle and it will use it.
3. **Build.** Every later conversation reads the catalog, the conventions, and
   the rulebook straight out of Webflow, and writes the brief, the run record,
   and any candidates back as drafts.
4. **If the store is not readable**, the skill says which two scopes are
   missing - `agent_instructions:read` and `agent_instructions:write` - and
   falls back to the bundle. It does not retry a 403 and it does not fail the
   run. With neither a store nor a bundle, a build stops at template selection
   and says so.
5. **Promotion and pruning** happen in conversation through the maintain flow,
   which spells out what is given up without a pull request.

## What is verified and what is not

Being honest about this matters more than the feature list.

**Verified in this repository, offline:**

- The six Python scripts do what their specs say. 96 unit tests cover brief
  validation, outline rendering, the inventory guard, catalog linting, the run
  manifest, and snapshot building, plus a skill-tree test that checks every
  path the docs point at exists, that the SKILL.md and CHANGELOG versions agree,
  and that no machine-specific path is committed.
- The worked example passes end to end: the brief validates with
  `--require-approval`, the committed outline is byte-identical to a fresh
  render of the brief, the catalog entry passes `catalog_lint.py`, and the guard
  fixtures produce exactly the pass and fail verdicts the manifest records.
- The plugin and marketplace manifests parse and carry the keys Claude Code and
  Codex need (`checks/repo-check.sh`, also run in CI), and `claude plugin
  validate` accepts both the marketplace root and the plugin directory.
- Nothing in the tree carries a credential-shaped string or an identifier
  outside the synthetic set (same script).

**Not verified, and stated as such wherever it matters:**

- **No live Webflow run is included.** The example is fictional. Nothing here
  is evidence that a build succeeds against any particular site; the first real
  evidence is your own onboarding run.
- **Branch-mode writes.** Onboarding can establish that element reads accept a
  branch page id. Whether writes on a branch page and `create_branch` without
  the Designer work is unknown until someone runs a branch-mode build.
- **Rate-limit pacing.** `references/rules.md` rule 10 gives a conservative
  default and the shape of the failure. The real numbers for a site are
  whatever onboarding measures; a small site may need no pacing at all.
- **Designer URL forms.** Only `designer_tool > switch_page` is known to
  navigate the connected Designer tab. Any `...design.webflow.com?pageId=` URL
  is a guess until someone checks it on the site in question.
- **Agent Instructions and page schema writes** depend on scopes the connector
  token may not have. Both fall back cleanly; neither aborts a build.
- **Whether Agent Instruction bodies are private.** The evidence is strong
  (scope-gated, delivered as site metadata to authorized MCP clients, no
  publish path, never in page content) and no vendor statement was found either
  way, so the skill does not claim it as a guarantee. Onboarding's one-time
  exposure check is how you settle it for your own site.

**Measured outside this repository, recorded because it matters:** an anonymous
request to a Webflow branch staging URL redirects to the Webflow login and
returns HTTP 403, so a branch staging publish is gated behind a login rather
than open to the internet. That was checked against a live Webflow site; nothing
in this tree verifies it.

## Safety

- Never calls `publish_site`. `publish_branch` only to staging, only in branch
  mode, only on explicit request, always recorded.
- Every page is created with `draft: true` set explicitly and confirmed by
  readback before any other write.
- Warns before uploading an asset, and prefers one already in the library: an
  upload is public from the moment it lands (see the table above).
- Never edits a pre-existing shared definition (class, base variant, variable).
  A pre/post inventory guard fails the run if anything pre-existing changed.
- Never deletes anything the run did not create.
- Every Webflow write is appended to a run manifest before the next write, so
  an interrupted run can be resumed or cleaned up.
- The Webflow Designer Bridge App launch link is a credential. It is read from
  a failed probe response at run time and is never written to a file, a
  manifest, a run record, or a commit.

The full rulebook is
`plugins/design-automations/skills/webflow-template/references/rules.md`, 19
rules, and it is what gets installed into the site's Agent Instructions so that
every other agent connected to the site reads the same rules. Rule 19 is the
public-exposure guarantee above.

## Layout

```
.claude-plugin/marketplace.json        Claude Code marketplace manifest
.agents/plugins/marketplace.json       Codex marketplace manifest
checks/repo-check.sh                   wrapper CI and the docs call
checks/repo_check.py                   structure + disclosure checks
plugins/design-automations/
  .claude-plugin/plugin.json
  .mcp.json                            Webflow MCP server
  skills/webflow-template/
    SKILL.md                           entry point, explicit invocation only
    flows/                             onboard, build, maintain, sync, resume
    references/                        rulebook, schemas, catalog format, conventions template
    references/examples/               a filled catalog entry and conventions file (fictional)
    scripts/                           six Python 3 scripts, standard library only
    scripts/tests/                     unit tests and synthetic fixtures
    assets/                            outline template, brief examples, worked example
```

## Development

```
cd plugins/design-automations/skills/webflow-template/scripts
python3 -m unittest discover -s tests
```

```
bash checks/repo-check.sh          # structure and disclosure
REPO_CHECK_LIVE=1 bash checks/repo-check.sh   # also runs claude plugin validate
```

Python 3.11, standard library only. No network access is required by anything
in this repository.

### Contributing: synthetic identifiers only

Every Webflow-shaped identifier in this tree is invented, and comes from two
families and no others:

| Shape | Pattern | Used for |
| --- | --- | --- |
| 24-hex | `0000000000000000000000xx` | sites, pages, folders |
| UUID | `1111aaaa-0000-4000-8000-000000000xxx` | components, props, variables |

`checks/repo-check.sh` fails on any identifier outside those two patterns, on
any Bridge App launch link, and on any other long secret-shaped token. If you
add an example or a fixture, mint the next id in sequence rather than pasting
one from a real site.

## Licence

MIT. See `LICENSE`. Copyright (c) 2026 Dayton Floyd.
