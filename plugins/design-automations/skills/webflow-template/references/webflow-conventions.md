# Webflow conventions (template)

**This file is a template. Every value in it is a placeholder until
`flows/onboard.md` measures it against your site and writes the answer here.**
Nothing in this file is a fact about any particular Webflow site, and no flow
may treat an unfilled row as if it were.

Onboarding fills it in one read-only pass; `flows/maintain.md` (Refresh
inventory) re-measures it and updates the reconciliation log. Every other flow
reads it rather than assuming. Where a row says **MEASURE**, that is an
instruction: run the call named, record what came back, and date it. Where it
says **UNMEASURED**, no flow may rely on the row.

## Toolkit settings

| Setting | Value | Notes |
| --- | --- | --- |
| Instruction prefix | `page-templates` | **The one place this is defined.** Every Agent Instruction path the toolkit owns is built from it: the rulebook at `rules/<prefix>.md`, the catalog index at `<prefix>/SKILL.md`, this file at `<prefix>/conventions.md`, family entries at `<prefix>/catalog/<family>.md`, candidates at `<prefix>/candidates/<slug>.md`, run records at `<prefix>/runs/<date>-<slug>.md`. Change it here if another team already owns `page-templates` on your site, then re-run `flows/sync.md`; nothing else in the skill hard-codes it. |
| Toolkit-owned paths | the six above (`<prefix>/conventions.md` included) and nothing else | Sync never reads, writes, or deletes an instruction outside them (`flows/sync.md`). |
| Store | `<webflow / repository / downloads only>` | Chosen at `flows/onboard.md` step 0. `webflow` means the catalog, this file, and the index live in Agent Instructions and there is no pull request in the loop; `repository` means git is the reviewed source and `flows/sync.md` pushes; `downloads only` means the user keeps the bundle and attaches it to each build. |

## Sites

MEASURE: `data_sites_tool > list_sites`, then `get_site` for the one you are
onboarding.

| Site | Site ID | shortName | Purpose | Custom domains | Publish policy |
| --- | --- | --- | --- | --- | --- |
| `<display name>` | `<site_id>` | `<short name used in Designer URLs>` | `<what the site is for>` | `<domains>` | `<who publishes and how>` |

Locale: MEASURE (`get_site`) the primary locale, its id, whether localization
is enabled, and any secondary locales. The skill writes the primary locale only
(rule 16).

## Site-level tracking

**This is the section `rules.md` rule 14 and `flows/build.md` Phase 6 read.**
It records the tracking convention the site already uses, so that a build can
**match** it. It is never a scheme to apply: a build copies link destinations
from the brief, copies link extras only where this section already lists them,
and adds nothing else.

MEASURE two things. Delivery: `data_scripts_tool > get_site_scripts`, plus
whatever the component census and the exemplar pages show about how tracking
reaches a page. Link extras: read the links already on the site's own CTAs —
the exemplar pages' link elements as `data_element_tool > get_all_elements` and
`data_element_settings_tool` return them — and record the query parameters and
custom attribute names they carry, if any.

| Question | Answer | Measured |
| --- | --- | --- |
| Delivery — how tracking reaches a page | `<site scripts / a named shell component / per-page embeds / none / UNMEASURED>` | `<date>` |
| Link extras the MCP can see on existing CTAs | `<none / UTM keys: <keys> / custom attribute: <name> / UNMEASURED>` | `<date>` |
| Sibling CTA the answer was read on | `<page and element, so a handoff can name a real example>` | `<date>` |

Name a shell component by **name**, never by id (`catalog/README.md`), and list
it in the family's Shell components row too so Phase 6 can check the page
carries it.

`none` means none the MCP can see. Click listeners, GTM triggers, and anything
bound in a script are invisible to this server in both directions: do not infer
them, and do not record a guess as a measurement. Where either of the first two
rows is UNMEASURED, the Phase 6 `tracking` row is a WARN ("tracking convention
unmeasured; skipped"), never a FAIL, and Phase 5 writes destinations and
targets only.

The skill never adds page or site scripts, never creates or inserts an
analytics component, and never invents a UTM key or an attribute name this
table does not list (rule 14). A brief destination whose extras deviate from
this convention is asked about in the same turn before anything is written;
without that consent the link goes to the publisher as a handoff
(`unsupported.md`).

## Class naming

MEASURE: filtered `data_style_tool` queries by prefix. **Never a full style
dump.** Record the system in use with real examples from the site, one row per
prefix or layer, and say explicitly whether it is a house system, Client-First,
or something else (probe for `padding-global`, `text-size-*`,
`heading-style-*`; record what came back).

| Prefix | Layer | Real examples read from the site |
| --- | --- | --- |
| `<prefix>` | `<what it is for>` | `<examples>` |

Rules the skill follows once this table is filled (binding through `rules.md`
rules 3 and 5):

- New reusable classes take the prefix the site uses for that layer; new
  page-only classes take a short page nickname prefix, matching the existing
  pattern.
- Prefer stacking existing utilities on a section over creating a new section
  class, where the site's system works that way.
- Never edit an existing shared class in a build run; they propagate site-wide.

Known inconsistencies: list legacy or conflicting patterns here for human
review. They are evidence, not a to-do list; the skill does not standardize a
site automatically.

## Design tokens (variables)

MEASURE: `data_variable_tool > get_variable_collections`, then `get_variables`
per collection.

| Collection | ID | Modes | Variables | Contents |
| --- | --- | --- | --- | --- |
| `<name>` | `<id>` | `<modes>` | `<count>` | `<what a template would bind to>` |

Record which collection is current and which is legacy, and whether any alias
targets are missing.

## Templates and reusable sections

Filled from `flows/onboard.md` steps 4 and 5. One row per family; the section
outlines and the decisions live in `catalog/<slug>.md`.

| Family | Slug | Model | Master page (id, slug) | Exemplar | Shell components | Body signature | Confidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `<name>` | `<slug>` | `<duplicate-master / component-recipe / hybrid>` | `<id>` `<slug>` | `<page>` | `<components>` | `<what the body looks like>` | `<proposed / confirmed <date>>` |

Shared section components that appear across families: MEASURE with the
onboarding census (`get_all_components` with `includeInstanceCount`) and list
them by **name** with their instance counts. Names, never ids
(`catalog/README.md`, "Components are named").

## Component names

MEASURE at onboarding and at every inventory refresh: are all component names
on this site **unique**? The catalog keys on names, so the answer decides
whether a family can name a component at all.

| Question | Answer | Measured |
| --- | --- | --- |
| Total components | `<n>` | `<date>` |
| Distinct names | `<n>` | `<date>` |
| Names unique? | `<yes / no, with the duplicates listed>` | `<date>` |

If two components share a name, every family that names it is blocked until a
maintainer renames one or the entry disambiguates the row by `group`
(`flows/build.md` Phase 3).

## Page folders

MEASURE: folders are not returned by `list_pages` directly; infer them from
`parentId` values that are not pages, and their paths from children's
`publishedPath`.

| Folder ID | Path | Children | Notes |
| --- | --- | --- | --- |
| `<id>` | `<path>` | `<n>` | |

Allowed folders for new pages built by the skill, one row per family, agreed
with the maintainer at onboarding step 5:

| Family | Allowed folders |
| --- | --- |
| `<family>` | `<path>` (`<folder id>`) |
| Anything else | ask |

Folders that do not exist yet are pre-created at onboarding step 6
(`designer_tool > create_page_folder`, which needs the Designer open), so that
build runs never depend on the Designer for a folder.

## Slug, title, SEO and Open Graph conventions

Agreed at onboarding step 5 and applied by each family entry.

- Slugs: `<pattern, casing, separators, how they match siblings>`.
- SEO title: `<pattern>`, `<length limit>`.
- SEO description: `<length range>`.
- Open Graph: `<whether title and description are copied from SEO; image size and how it is set>`.
- Anything not settable through MCP (for example `noindex`) is manual Designer
  work and is named in the report.

## Schema defaults

Agreed at onboarding step 5, per family. MEASURE the masters first
(`query_pages_schema_markup`) and match house usage rather than inventing one.

| Family | `schemaType` | `additionalSchemaTypes` |
| --- | --- | --- |
| `<family>` | `<type>` | `<extra types>` |

Also MEASURE whether the connector token can **write** page schema
(`bulk_update_pages_schema_markup`). Reading and writing are separate
permissions; a token that reads schema may still return `403
insufficient_permissions` on the write. Record the answer: when the write is
refused, build Phase 5 records the step as `failed` and hands the JSON-LD to
the publisher instead.

## Isolation default

`<draft-main or branch>` per family. `branch` may only be offered when the
Branching section below records branching as available.

## Publish policy

The skill never publishes (rule 8). Record here who does: the responsible
publisher for a page the skill built, the review step before publishing, and
the cadence. A workable default, if the team has no rule yet: the responsible
publisher is the person whose Webflow MCP connection (the connector OAuth
identity) ran the build, named in the run report.

## Branching

MEASURE: `data_pages_tool > list_branches`.

| Question | Answer | Measured |
| --- | --- | --- |
| `list_branches` result | `<200 (available) / 403 not_enterprise_plan_site (not available)>` | `<date>` |
| Branch page reads | `<did get_all_elements on a branch page id return the branch tree?>` | `<date>` |
| Branch page writes | UNMEASURED until the first branch-mode build | |
| `create_branch` without the Designer | UNMEASURED until the first branch-mode build | |
| Live branches and their state | `<count, and whether any show has_conflicts>` | `<date>` |

`flows/build.md` Phase 3 offers `branch` **only** when this section says
available, and repeats whatever is still UNMEASURED as a warning when it does.

## Designer availability

MEASURE: `designer_tool > get_current_page`.

| Question | Answer | Measured |
| --- | --- | --- |
| Bridge App reachable during capture | `<yes / no>` | `<date>` |
| Breakpoints (`get_all_breakpoints`, cascade order) | see the table below | `<date>` |
| Snapshot behaviour | `<what element_snapshot_tool did: parallel vs sequential, iframes, breakpoint of the canvas>` | `<date>` |

**Breakpoints. MEASURE them; do not assume a set.** Webflow sites differ in
which breakpoints exist. Record exactly what `get_all_breakpoints` returned:

| Breakpoint id | Designer name | minWidth | maxWidth | Base |
| --- | --- | --- | --- | --- |
| `<id>` | `<name>` | `<min>` | `<max>` | `<yes/no>` |

The ids are the values `data_style_tool` takes in `include_breakpoints` and
`breakpoint_id`. The outline renders four frames (desktop plus three narrower
views); map them onto the breakpoints recorded here, and say in the outline
which site breakpoints the frames stand for.

**Designer foreground procedure.** The Bridge App answers only while its
Designer tab is open and in front, and it belongs to whichever Webflow account
is connected, so the launch link is **never** written down here or anywhere
else in this repository. When `get_current_page` fails, its error response
contains the sentence "Launch the app using following link `<url>`"; take that
url from the response. On Claude Code or Codex run `open "<url>"` (`xdg-open`
on Linux), wait about 40 seconds, and re-probe; up to three attempts before
recording the Designer as unreachable for the run. On Claude.ai show the url as
a markdown link and ask the user to click it and keep the tab in front. Treat
the url as a credential: use it within the run, never write it to a file, a
manifest, a run record, or a commit (rule 15).

**Designer links for a page.** MEASURE whether any URL form navigates the
connected Designer tab on your site before putting one in a report. The
MCP-native route, `designer_tool > switch_page` with the page id, navigates the
connected tab; a guessed `https://<site-short-name>.design.webflow.com?pageId=`
URL may open a new tab that the Bridge App is not bound to. Reports give the
page id and the folder path in plain text, and use `switch_page` when the
Bridge App is connected.

## Agent Instructions

MEASURE: `data_agent_instructions_tool > search_instructions`.

| Question | Answer | Measured |
| --- | --- | --- |
| `search_instructions` result | `<200 / 403 forbidden>` | `<date>` |
| Paths another team already owns | `<list, or none>` | `<date>` |
| Toolkit paths already present | `<list, or none>` | `<date>` |
| Exposure check (`flows/onboard.md` step 10) | `<not run / marker not found in public output after a publish on DATE / FOUND - stop using the store>` | `<date>` |

The exposure check runs **once per site**, the first time the store is used. It
is how the claim "Agent Instructions are not public" is settled here rather
than assumed: the evidence (scope-gated, delivered to authorized MCP clients as
site metadata, no publish path, never in page content) is strong, but no vendor
statement was found, so the answer above is a measurement, not a quote
(`rules.md` rule 19).

When the store is the catalog's only home, onboarding also appends a
`## Sync state` section to `<prefix>/conventions.md` - one row per written path
with its sha256 and timestamp - because there is no `sync-state.json` to hold
them.

A **403** means the connector user lacks `agent_instructions:read` and
`agent_instructions:write` on the site. That is a scope on the OAuth token, not
a missing tool: the install is blocked until an admin grants them, build runs
fall back to the bundled copies, and run records live as local files. A 403
never aborts a build.

## Token scopes observed

MEASURE per tool family and record read and write separately: pages, elements,
components, props, styles, variables, assets, Designer tools, Agent
Instructions, page schema markup. Name the permissions to ask a workspace admin
for when something is refused.

## Rate limits and response sizes

**This is the section `rules.md` rule 10 reads.** MEASURE it; the answer is a
property of your site's size, not of the MCP server.

What to measure, at onboarding and again whenever the site grows a lot:

| Probe | What to record |
| --- | --- |
| CMS collection count (`data_cms_tool`, names only) | `<n>` — every element, props, settings, and builder call prefetches these |
| Asset count (`data_assets_tool > list_assets`, count the pages) | `<n>` — deep element reads resolve an asset per image node |
| `get_all_elements` at depth 1, 2, 3 and -1 on a busy page, one at a time | which depths returned 200 and which returned 429, and on which endpoint |
| `query_elements`, type-filtered, on the same page | 200 or 429, and on which endpoint |
| Two element or props calls N seconds apart | the smallest spacing that held |
| A bulk read (`list_assets`, `get_all_components`, `get_variables`) followed by an element read | how long the element read had to wait |
| Response sizes for `list_pages`, `list_forms`, `get_all_components`, `get_variables` | which ones must be saved to a file and parsed locally |
| Are slot children returned with element ids at depth 3? | yes or no — if no, slot content is manual work |

Then write the pacing rule your site needs, in the same shape as the
conservative defaults in `rules.md` rule 10, and say plainly which of these are
reachable through the MCP on this site and which are manual handoff items:

| Capability | On this site | Measured |
| --- | --- | --- |
| Component props | `<automated / manual>` | `<date>` |
| Loose-section text, links, images | `<automated / manual>` | `<date>` |
| Slot children | `<automated / manual>` | `<date>` |
| Depth-limited structure reads | `<which depths>` | `<date>` |

A small site with few collections and few assets may never hit the budget at
all, in which case say so here and let the flows run at full speed.

## Fonts, forms, CMS collections

MEASURE and record: custom fonts and their weights (`data_fonts_tool`); the
forms the site uses and whether they are delivered as components
(`data_forms_tool`); CMS collection names and which ones a family depends on
(`data_cms_tool`). The skill reuses existing form components and never builds a
raw form.

## Reconciliation log

Every read-only probe this file's values came from, with its timestamp and
result. Append a row per probe; never overwrite the history.

| When | Call | Result |
| --- | --- | --- |
| `<ISO date>` | `<tool > action>` | `<what came back>` |
