---
name: webflow-template
description: >-
  Turns a design (Claude Design HTML or zip export, other HTML, screenshots, a
  PDF, or a link) into an unpublished draft page in your Webflow site, built
  from a reusable template family: it digests the design, interviews the
  submitter, picks a family, shows a visual outline for approval, builds the
  page through the Webflow MCP connector, verifies by readback, and reports.
  Also carries the maintainer flows: onboard a site (run this first; the
  catalog is generated per site), maintain the template catalog, sync the
  catalog to Webflow Agent Instructions, resume or clean up an interrupted run.
  Never publishes. Runs only when the user asks for it by name
  (/design-automations:webflow-template in Claude Code, "webflow-template"
  selected in Claude.ai, $webflow-template in Codex). Do not activate it for
  general design or Webflow conversation.
license: MIT. See LICENSE
metadata:
  version: "1.0.0"
disable-model-invocation: true
---

# Webflow template build

You are running the `webflow-template` skill. It turns a design into a draft
page in a Webflow site by reusing a **template family**: the components,
styles, variables, and layout conventions already in that site. The template's
styling wins over the incoming design. The page it builds is not visible to
visitors until a human publishes. One thing it can do, uploading an asset, is
public the moment it happens: see "What this can and cannot make public"
below.

The shape of every build is fixed:

**receive a design → digest it → interview the submitter → pick a family →
approve a visual outline → build an unpublished page → verify by readback →
report and hand off.**

## Onboarding comes first

The skill ships **without a catalog**. A template family names components,
master pages, and folders that exist on exactly one site, so there is no
portable catalog to ship. `flows/onboard.md` reads a site once and generates
the catalog, the filled conventions, the index, and the sync state for it
(those are the repository store's file names: `references/catalog/`,
`references/webflow-conventions.md`, the local site inventory, and
`references/sync-state.json`; step 0 of that flow picks where they land). Until that has run, a build
gets as far as template selection and stops.

Everything site-specific lives in `references/webflow-conventions.md`, which
ships as a **template full of placeholders**. Rows marked MEASURE are
onboarding's worklist; rows marked UNMEASURED are unknown and no flow may
assume them. A filled example for a fictional site is in
`references/examples/`.

**Onboarding does not need a repository.** Its step 0 picks a store: Webflow
Agent Instructions (the default on claude.ai and for anyone without repo write
access), a git repository (maintainers, and the only path with a pull request
in it), or downloads only (the fallback when the instruction scopes are
missing). The measuring is identical in all three; only the destination
changes, and every one of them also hands the user a download bundle.

**What the Webflow store gives up, and say it rather than gloss it:** there is
no pull request, so there is no second reader, no diff, and no revert. What
stands in for one is an explicit confirmation before each write, families kept
as drafts with `status: proposed` until a maintainer confirms them, a
`## Decisions` section inside every entry, and the bundle as the only history.
The detail is in `flows/onboard.md` step 0 and "Maintaining without a
repository" in `flows/maintain.md`.

## Surfaces

| Surface | How it is invoked | Webflow access | Scripts | Persistence |
| --- | --- | --- | --- | --- |
| Claude.ai | User selects "webflow-template" by name | First-party Webflow connector (OAuth per user) | Code execution sandbox, Python only if enabled | **No repo, and none needed.** Onboarding writes the catalog, the filled conventions, and the index into Webflow Agent Instructions under `<prefix>`, and hands over the same content as a download bundle; briefs, run records, and candidates go to the store as drafts and are offered as downloads too |
| Claude Code | `/design-automations:webflow-template` (plugin skills are namespaced; the bare form only applies to a copy in `.claude/skills`) | Plugin `.mcp.json` (`https://mcp.webflow.com/mcp`) or the project's MCP | Local `python3` | Repo and Webflow, with a pull request as the review step; the reviewed path |
| Codex | `$webflow-template` | `[mcp_servers.webflow]` in `~/.codex/config.toml` | Local `python3` | Repo and Webflow |

Submitters on Claude.ai are often non-technical. Ask short questions, at most
three per turn, and explain Webflow terms the first time you use them.

## Preflight (every conversation)

1. Call `webflow_guide_tool` once per conversation. Do not call it again.
2. Read the rulebook, the catalog, and the measured conventions from Webflow
   Agent Instructions: `data_agent_instructions_tool > search_instructions` for
   `rules/<prefix>.md` and the `<prefix>` skill, then `read_instruction` for
   each hit (the index at `<prefix>/SKILL.md`, `<prefix>/conventions.md`, and
   each `<prefix>/catalog/<family>.md`). `<prefix>` is the instruction prefix recorded once in
   `references/webflow-conventions.md`, "Toolkit settings"; the default is
   `page-templates`. If the site has none, fall back to the bundled copies in
   `references/rules.md` and `references/catalog/` and tell the user the site
   has not been onboarded, so the catalog is empty. If the call returns
   **HTTP 403** (the connector user lacks the `agent_instructions:read` and
   `agent_instructions:write` scopes), use the same bundled copies, keep the
   brief and run manifest as local files or downloads, and say in the report
   that the Webflow instruction store was not readable or writable. A 403 never
   aborts a run, and is never retried in a loop: one probe, one answer. When the
   store is unreadable **and** the bundled catalog is empty, ask for the
   download bundle onboarding produced, or send the user to `flows/onboard.md`;
   `flows/build.md` Phase 0 step 2 has the wording and says what is degraded.
3. Follow `references/rules.md`. It is short. Every rule in it is binding on
   this skill and on any other agent connected to the site.
4. Read `references/webflow-conventions.md` before planning any reads. It is
   where this site's measured facts live: the instruction prefix; the pacing
   every element, props, settings, and builder call needs, which follows from
   the site's CMS collection and asset counts (rule 10); whether loose-section
   content and slot children are reachable at all or are manual handoff items;
   whether the connector token can write page schema; whether branching is
   available; the breakpoint list; whether component names are unique. None of
   these is a constant: a small site may hit no limits at all, a large one may
   hit several. Where the file says UNMEASURED, say so instead of guessing, and
   point the maintainer at `flows/onboard.md`. The catalog names components
   rather than carrying their ids, so a run resolves only the names of the
   family it picked, with one `query_components` filtered to that family's
   component group or batched `get_component` by name, and records the ids in
   the run manifest alone (rule 10, `references/catalog/README.md`). A catalog
   family with `status: proposed` is unconfirmed until a maintainer confirms it
   through `flows/maintain.md`, and the report says so while that is true.
5. The Designer tools (`designer_tool`, `element_snapshot_tool`) only answer
   while the Webflow Designer is open with the Bridge App running and its tab
   in the foreground. When `get_current_page` fails, its error response carries
   the Bridge App launch link for the connected account and site ("Launch the
   app using following link ..."). Take the link from that response, never from
   a file: it is a credential and it differs per operator. On Claude Code or
   Codex run `open` (macOS) or `xdg-open` (Linux) on it, wait about 40 seconds,
   re-probe, up to three times; on Claude.ai show it as a markdown link and ask
   the user to click it. Only then record the Designer as unreachable for the
   run. Never write the link to a file, a run record, or a commit.

## Pick a flow

The **build** flow is the default. If the user hands you a design, a link, or
says "make a page", go to `flows/build.md` without asking which flow they mean.
The maintain and sync flows are for maintainers and are usually run from
Claude Code; onboarding runs anywhere:

| User wants | Flow | Who |
| --- | --- | --- |
| Set the site up for the first time: inventory, families, conventions, install | `flows/onboard.md` | Anyone with the Webflow connector, once per site, **before anything else**; a maintainer with a repo gets the reviewed variant |
| A page from a design (default) | `flows/build.md` | Anyone |
| Confirm a proposed family, promote a candidate, edit a master or shared component, create a family, refresh inventory, prune and archive | `flows/maintain.md` | Maintainer |
| Push rules and catalog to Webflow, pull candidates and run records back | `flows/sync.md` | Maintainer |
| Finish or clean up an interrupted run | `flows/resume.md` | Anyone; build preflight offers it automatically |

Read only the flow you are running. Each flow names the reference files it
needs. Keep file references one level deep: this file points to a flow, the
flow points to references.

## What this can and cannot make public

Using this skill must not put anything on the public internet. Only one of the
writes it makes can, and it says so at the moment it makes it. The full rule is
`references/rules.md` rule 19.

| What | Public? | The guarantee |
| --- | --- | --- |
| **The draft page** | No | Created with `draft: true` set explicitly and confirmed by `get_page_metadata` readback. Draft pages are excluded from publishing, so it does not go live at the next site publish either. A human turns the flag off. |
| **New components, styles, variables** | Not yet - **at the next site publish, yes** | They are site-level, so they ship whenever anyone next publishes the site, even though the page stays a draft. Every run reports them as the ships-at-next-publish list. Branch mode keeps them off main until merge. |
| **Uploaded assets** | **Yes, immediately** | `asset_tool > upload_image_by_url` puts the file in the site's asset library, and Webflow serves library assets from a public CDN URL from the moment of upload, before any publish and whether or not the page is ever published. The build warns and asks first, prefers an asset already in the library, and reports every upload as an "already public" line. Deleting an asset later does not un-serve a URL someone already has. |
| **Branch staging publish** | Gated, not open | Only on explicit request in that turn, only in branch mode, only to staging, never production. Measured: an anonymous request to a Webflow branch staging URL redirects to the Webflow login and returns HTTP 403. |
| **Agent Instructions** (the catalog store) | Evidence says no; no vendor statement | Gated behind `agent_instructions:read`, delivered to authorized MCP clients as site metadata, no publish path, never in page content. Not a guarantee: `flows/onboard.md` step 10 runs a one-time check per site (throwaway instruction, human publishes on their own cadence, confirm the marker appears nowhere public, delete it). |
| **CMS items** | Never used | Standing non-goal. CMS items have staged and live states with publish and unpublish events; they are publish-shaped by design, so the toolkit never stores a catalog, brief, candidate, or run record in a collection. |

Never `publish_site`, in any flow, on any surface.

## Hard safety rules

These apply in every flow, on every surface, with no exceptions and no
"just this once". The full rulebook is `references/rules.md`; these are the
lines that can do damage if crossed.

- **Never call `publish_site`.** `publish_branch` only to staging, only in a
  run that uses branch mode, only when the user asks for it in that turn, and
  always recorded in the manifest. Production publishing is done by humans.
- **Every page is created with `draft: true` set explicitly** (the API default
  is `false`) and confirmed by `get_page_metadata` readback before any other
  write to the page.
- **Never edit a pre-existing shared definition.** No `update_style` on a class
  that existed before the run, no base-variant edits on a pre-existing
  component, no changes to existing variables. Extend with a new class, a new
  variant, or a new variable instead. The pre/post inventory guard fails the
  run if anything pre-existing changed.
- **Never delete or unregister anything not created in the current run.**
  Destructive calls on run-created resources require the user's explicit
  confirmation in that turn.
- **Record every Webflow write in the run manifest before the next write.** On
  interruption, resume from the manifest instead of rebuilding.
- **Touch only toolkit-owned Agent Instruction paths** (`rules/<prefix>.md`,
  `<prefix>/...`). Never overwrite instructions the toolkit does not own.
- **Warn before uploading an asset, and prefer one already in the library.**
  An uploaded asset is served from a public CDN URL from the moment of upload,
  before any publish. It is the only thing this skill does that puts a file on
  the public internet.
- **Never write a credential to a file.** The Bridge App launch link is read
  from a failed probe response at run time and is never stored.
- **No site or page scripts, no localization writes, no publishing of any kind
  from this skill.**

## Scripts and the no-script fallback

Six Python 3 scripts live in `scripts/`. They use the standard library only,
take JSON in, return JSON or HTML out, and exit non-zero on failure.

| Script | Purpose | Flow |
| --- | --- | --- |
| `scripts/validate_brief.py` | Check the brief before rendering the outline | build Phase 4 |
| `scripts/render_outline.py` | Render the self-contained HTML outline from the brief | build Phase 4 |
| `scripts/diff_inventory.py` | Pre/post inventory diff; the shared-defaults guard | build Phase 6 |
| `scripts/catalog_lint.py` | Lint catalog entries and `sync-state.json` | onboard, maintain, CI |
| `scripts/manifest.py` | Create, append to, summarize the run manifest; ships-at-next-publish list | build, resume |
| `scripts/build_snapshot.py` | Build the guard's pre/post snapshot from saved `get_all_components`, `get_variables`, and `query_styles` results | build Phases 5 and 6 |

Run them with `python3 scripts/<name>.py --help` first if unsure of arguments.

**When code execution is unavailable** (Claude.ai with the sandbox off, or a
script fails to run): do the same work by hand from the written spec. The specs
are exact: `references/brief-schema.md` carries the validation checklist,
`references/outline-spec.md` the rendering rules,
`references/manifest-schema.md` the append and summarize procedures, and
`references/rules.md` rule 17 the guard. Say in the report that helper scripts
were unavailable and the checks were performed manually. Never skip a check
because the script could not run.

## Files

Flows (procedures, read one at a time):

- `flows/onboard.md`: once per site; inventory, measurements, families,
  conventions, install. Run first.
- `flows/build.md`: the per-page workflow, Phases 0 to 7.
- `flows/maintain.md`: confirm proposed families, promote candidates, edit
  shared components, create families, refresh inventory, housekeeping.
- `flows/sync.md`: repo to Webflow push, Webflow to repo pull, conflict rules.
- `flows/resume.md`: resume or clean up an interrupted run.

References (read when a flow points at them):

- `references/rules.md`: the Webflow MCP rulebook, 19 rules (rule 19 is the
  public-exposure guarantee).
- `references/interview.md`: question bank with skip logic.
- `references/brief-schema.md`: brief fields and validation checklist.
- `references/manifest-schema.md`: run manifest fields and manual procedures.
- `references/outline-spec.md`: how the visual outline is rendered.
- `references/webflow-conventions.md`: **the template onboarding fills in.**
  Sites, class naming, tokens, families, folders, slugs and SEO, schema, the
  instruction prefix, branching, breakpoints, Designer availability, token
  scopes, rate limits, publish policy, reconciliation log.
- `references/catalog/README.md`: catalog entry format (including the `loose`
  and `candidate:` conventions and the `proposed` status) and the component
  metadata convention. `references/catalog/` itself ships empty; onboarding
  writes `references/catalog/<family>.md`, and `flows/sync.md` pulls candidates
  into `references/catalog/candidates/`.
- `references/runs/README.md`: run records (brief, manifest, outline,
  snapshots, guard verdict per run). Ships empty. Live builds on Claude Code
  write here, build Phase 0 checks it for an open manifest, and the maintain
  and sync flows archive to it.
- `references/sync-state.json`: last-synced hashes per instruction path; ships
  with `siteId` and `lastSync` null.
- `references/unsupported.md`: what the MCP cannot do, what depends on a scope
  or a site limit, and the Designer handoff for each.
- `references/examples/`: a filled catalog entry and a filled conventions file
  for a fictional site. Never read by a build; onboarding does not replace it.

Assets: `assets/brief.example.json` (a minimal brief that passes
`validate_brief.py`), `assets/outline.template.html` (template for
`render_outline.py`), and `assets/examples/` (the worked example's brief,
rendered outline, and dry-run manifest).

Codex metadata: `agents/openai.yaml`. Changes: `CHANGELOG.md`.
