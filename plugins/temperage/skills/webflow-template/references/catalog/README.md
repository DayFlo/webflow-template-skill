# Template catalog

One file per template family: `catalog/<family-slug>.md`. Written by
`flows/onboard.md`, changed by `flows/maintain.md`, pushed to Webflow Agent
Instructions (`<prefix>/catalog/<family>.md`, default prefix `page-templates`;
see `webflow-conventions.md`, "Toolkit settings") by `flows/sync.md`, linted by
`scripts/catalog_lint.py`. Candidates pulled from Webflow live in `candidates/`
(see `candidates/README.md`).

**This directory ships empty.** The catalog is generated per site: there is no
such thing as a portable family, because a family names components, master
pages, and folders that exist on one site only. Until `flows/onboard.md` runs,
this folder holds this README and nothing else, a build run that reads it says
so and stops at template selection, and the maintainer is pointed at
onboarding.

A worked example of a filled entry lives in `../examples/catalog/`. It is a
fictional site, it is never read by a build run, and onboarding does not
replace it; it is there so the format is legible before anyone has a catalog of
their own. `scripts/tests/fixtures/catalog_valid/` holds three more synthetic
entries, including a `proposed` one with `loose` rows and a `candidate:`
placeholder.

Entries written by onboarding start with `status: proposed`; they are usable,
but every report built from one says the family is unconfirmed (see "Status"
below) until the maintain flow's "Confirm a proposed family" path promotes them
to `1.0.0`.

## Components are named, not identified

**A component is referred to by its exact Webflow name.** No catalog entry and
no brief carries a Webflow component id. Names are the key in the catalog, in
briefs, and in the Agent Instruction copies; the id is looked up at run time and
written only to run records (the run manifest, a candidate record, a guard
snapshot), which is where an id legitimately belongs. A component that is
deleted and recreated keeps working as long as it keeps its name.

This works **only if component names are unique on the site**, which is a
measured property, not an assumption: `flows/onboard.md` step 3 counts the
components and the distinct names and records the answer in
`webflow-conventions.md`, "Component names". A name that resolves to **zero**
components blocks that family for the run; a name that resolves to **more than
one** also blocks it, and the run tells the maintainer to disambiguate by
group. Both are `flows/build.md` Phase 3 (Reconcile), which runs after a family
is chosen so a run only ever asks about the handful of components of the family
it picked.

How a run resolves them, cheaply (`rules.md` rule 10):

- one `data_component_tool > query_components` with a single labelled query
  whose `keywords` name the family's component group, when the family's
  components share a group; or
- batched `data_component_tool > get_component` by `name` (plus `group` to
  disambiguate) in a **single tool call** otherwise.

Never `get_all_components` for reconciliation, and never pass `includeProps`,
`includeVariants`, or `includeInstanceCount` (all default to off) outside the
onboarding census and the maintain flow's impact analysis, which need them. The
honest tradeoff: N by-name lookups are N server calls where the full list is
one, so a family that needs many components uses the one-call group-filtered
`query_components` form.

`catalog_lint.py` enforces this: a Webflow id in a component column (the dashed
32-hex component form or a 24-hex string) is a `COMPONENT-ID` error.

### Why pages and folders keep their ids

The asymmetry is deliberate, not an oversight. There is no lookup by slug in
the Webflow MCP: resolving a master page by slug means paging `list_pages` over
the whole site on every run. A handful of master page ids and folder ids is a
much smaller exposure than that cost, and a page id is stable across a rename
in a way a slug is not. So `masterPageId`, the `Folder ID` column, the
`Example pages` table, and the page id a brief's `page.folder.id` carries all
stay ids. Components, which the MCP *can* look up by name, do not.

Variants are named too: a `Variants` cell, a shell note, or a brief's `variant`
field names the variant, never a variant id.

## Entry format

A front-matter block, then the required headings in the order below. The front
matter is a small `key: value` block that `catalog_lint.py` parses with the
standard library, so keep to the two forms shown: scalars and simple lists.

```markdown
---
name: Product landing
slug: product-landing
version: 1.2.0
status: promoted
templateModel: hybrid
masterPageId: 0000000000000000000000b1
masterPageSlug: product-landing-master
masterPagePath: /products/product-landing-master
isolationDefault: draft-main
allowedFolders:
  - /products
  - /solutions
schemaType: WebPage
additionalSchemaTypes:
  - FAQPage
referenceImage: product-landing.png (asset name) or a public URL
owner: <team that owns the family>
audience: Evaluating buyers arriving from paid search
---

## Purpose
One paragraph: what pages of this family are for and who reads them.

## Decisions
- Taken by <maintainer> on <date>: family kept; model hybrid; master <id> (<leaf slug>); folders /products, /solutions; slug and title, SEO and Open Graph, schema WebPage plus FAQPage; isolation draft-main; publishing by humans only.

## Section outline
| # | Section | Component name | Class path | Owner | Required | Props | Variants | Slots | Content guidance | Image sizes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | hero | Hero / Product | | self | required | heading, subhead, ctaLabel, ctaLink | default, dark | media | H1 under 60 chars; one CTA | 1600x900 |
| 2 | logo-bar | Logo bar | | shared | optional | | default | logos | 5 to 8 logos, grayscale | 240x80 each |
| 3 | benefit-1 | loose | section.l-section.l-bg--surface-1 | self | required | | | | copied from the master and edited in place | 1200x800 |

## Shell components
| Role | Component name | Owner | Notes |
| --- | --- | --- | --- |
| nav | Site nav | shared | variant `default` |
| footer | Site footer | shared | |

## Allowed folders
| Path | Folder ID |
| --- | --- |
| /products | 0000000000000000000000c1 |
| /solutions | 0000000000000000000000c2 |

## SEO and Open Graph defaults
Title pattern, description pattern, default OG image (asset name), and any
rules (length limits, brand suffix).

## JSON-LD template
A fenced JSON block with placeholders in angle brackets, e.g. `<page.title>`.

## Example pages
| Page ID | Slug | Note |
| --- | --- | --- |
| 0000000000000000000000b1 | product-landing-master | master |
| 0000000000000000000000b4 | orbit | first build |

## Do and don't
- Do: ...
- Don't: ...

## Changelog
- 1.2.0 (2026-01-06): added `dark` hero variant (promoted from run orbit).
- 1.0.0 (2026-01-04): created at onboarding.
```

The ids in that skeleton are deliberately fake. Onboarding writes the real ones
it read from your site.

### Front-matter fields

| Key | Type | Required | Lint |
| --- | --- | --- | --- |
| `name` | string | yes | non-empty |
| `slug` | string | yes | lowercase kebab-case; equals the file name without `.md` |
| `version` | string | yes | semver `MAJOR.MINOR.PATCH`; the changelog must mention it |
| `status` | `proposed` \| `promoted` \| `deprecated` | no (default `promoted`) | see "Status" |
| `templateModel` | `duplicate-master` \| `component-recipe` \| `hybrid` | yes | |
| `masterPageId` | string | when model is `duplicate-master` or `hybrid` | non-empty |
| `masterPageSlug` | string | when model is `duplicate-master` or `hybrid` | the **leaf** slug, Webflow's `slug` field (`orbit`, not `integrations/orbit`); lowercase kebab-case |
| `masterPagePath` | string | no | the master's published path (`/integrations/orbit`); informational, not linted |
| `isolationDefault` | `draft-main` \| `branch` | yes | `branch` only if `webflow-conventions.md` records branching as available |
| `allowedFolders` | list of paths | yes, non-empty | each starts with `/`; each has a row in the Allowed folders table, which carries the folder ID |
| `schemaType` | string | yes | the primary JSON-LD type |
| `additionalSchemaTypes` | list of strings | no | extra JSON-LD types emitted beside `schemaType` (for example `FAQPage` built from the FAQ slot); when present, a non-empty list with no blank item and no repeat of `schemaType` |
| `referenceImage` | string | no | asset name or public URL |
| `owner`, `audience` | string | no | |

### Status

- `proposed`: written by onboarding (or the maintain flow's create-family path)
  from the live site and **not yet confirmed by a maintainer**. A build run may
  use a `proposed` family, and Phase 3 of `flows/build.md` says so when it
  recommends one; the report must state that the family is unconfirmed and that
  the component names, model, and master were proposed by onboarding.
  Placeholder `candidate:<slug>` rows are allowed only while `proposed`. In the
  repository store a `proposed` entry stays in the repo and is never pushed; on
  a site onboarded with no repository it lives at
  `<prefix>/catalog/<family>.md` as a **draft** (`isDraft: true`) and is listed
  in the index's second, unconfirmed table (`flows/sync.md`).
- `promoted`: confirmed by a maintainer and pushed to Webflow by `flows/sync.md`
  (or, with no repository, written straight to the store as a non-draft by
  `flows/maintain.md`, "Maintaining without a repository").
- `deprecated`: kept for history; never offered to a build. Set by the maintain
  flow with a patch bump and a changelog line naming the date, the maintainer,
  and where the requests route instead; the Purpose paragraph starts with the
  same note so a reader who opens the file sees it first.

### Required headings (H2, exact text)

`Purpose`, `Section outline`, `Shell components`, `Allowed folders`,
`SEO and Open Graph defaults`, `JSON-LD template`, `Example pages`,
`Do and don't`, `Changelog`. Extra H2 sections are tolerated and three are
conventional: `Audience` (after Purpose), `Decisions` (after Audience: one line
per onboarding decision, family kept or merged or dropped, template model,
master page, allowed folders, slug and title conventions, SEO and Open Graph
defaults, schema types, isolation default, who publishes, each with who took it
and when; written by the maintain flow's "Confirm a proposed family" path, and
the place a still-open decision carries a visible `TODO`), and
`Reference image` (after the JSON-LD template; "Empty" until a snapshot
exists).

### Tables

- **Section outline** columns: `#`, `Section`, `Component name`, `Class path`,
  `Owner`, `Required`, `Props`, `Variants`, `Slots`, `Content guidance`,
  `Image sizes`. At least one row. `Component name` is non-empty, is the
  component's exact Webflow name (or `loose`, or `candidate:<slug>`), and is
  never a Webflow id. `Class path` is filled only on `loose` rows and empty
  everywhere else. `Required` is `required` or `optional`. `Owner` is `self`,
  `shared`, or another family's slug (see below). Do not put a `|` inside a
  cell; separate prop names with commas and prop groups with semicolons
  (`Header/Heading; Button/Text, Link`). `Section` is the name a brief's
  `familySection` refers to; keep it kebab-case.
- **Shell components** columns: `Role`, `Component name`, `Owner`, plus an
  optional `Notes` column (variant, conditions). Rows optional. Shell rows
  always name a component; `loose` is not valid here, and neither is an id.
- **Allowed folders** columns: `Path`, `Folder ID` (`root` for `/`). Folder ids
  stay ids; see "Why pages and folders keep their ids".
- **Example pages** columns: `Page ID`, `Slug`, `Note`. Page ids stay ids too.
  Slugs are leaf slugs, kebab-case; put the folder path in the note if it
  matters.

### Loose sections (duplicate-master and hybrid only)

On some sites the body sections of a master page are element trees built from
utility classes rather than components. A duplicate copies them as-is and the
build edits them in place. Whether your site is like that is something
onboarding finds out; when it is, the outline records such a section as:

- `Component name` = `loose`
- `Class path` = the master's class path for the section root, tag first,
  classes joined with dots (`section.l-section.l-bg--surface-1`,
  `header.l-section--header.l-pad-b--112px.l-mode--dark`)
- `Owner` = `self`
- `Props`, `Variants`, `Slots` empty; `Content guidance` says which nodes the
  build sets (heading, paragraph, button, image) and, when a real component is
  the better choice for a fresh build, names it.

Whether the build can actually write into a loose section is also measured, not
assumed: on a site whose element reads exceed the request budget, loose-section
content is a manual handoff item (`rules.md` rule 10, and the capability table
in `webflow-conventions.md`). The catalog row is the same either way; what
changes is whether the brief marks those slots `final` or `manual`.

The linter skips the cross-family uniqueness check for `loose`, rejects `loose`
when `templateModel` is `component-recipe` (a recipe inserts components only),
and rejects it in the shell table. When the entry recommends a real component
instead of the loose tree, the entry puts that component in its own `optional`
row (named so a brief can pick it) and points at it from the guidance of the
row it replaces. Either way the evidence (which master section it came from)
stays in the table, in `Class path`.

### Candidate placeholders (proposed families only)

A recipe family may need a section the site has no component for yet. Its row
uses `Component name` = `candidate:<kebab-slug>` and `Owner` = `self`; the name
the component will be given goes in `Content guidance`. The first build run
that creates the component records it as a candidate under that slug; at
promotion the maintainer replaces the placeholder with the created component's
**name**. The linter rejects placeholders once `status` is `promoted`. Briefs
use the same placeholder format (`brief-schema.md`, check 14).

### Component ownership and uniqueness

Every component belongs to exactly one family or is site-wide.

- `self`: this family owns the component: it was created for the family (a
  promoted candidate) or is the family's signature section that no other page
  type uses. A `self` component **name** may appear in exactly one family
  across the catalog; two families both claiming it is a lint error. `loose`
  rows are `self` and exempt from the check.
- `shared`: a site-wide component that predates the catalog and belongs to the
  site's component library rather than to a family: the shell, script and form
  components, and the pre-built sections used across page types. No uniqueness
  check. Changing one is the maintain flow's "Edit a master or shared
  component" path, never a build run.
- `<family-slug>`: borrowed from that family, which must exist and list the
  same name as `self`.

## Component metadata convention in Webflow

Mirrors the catalog for components the toolkit itself created, so anyone in the
Designer can see their status. **Pre-existing library components are never
touched**: a site organizes its component library its own way and several
descriptions carry team text. The toolkit rewrites neither `group` nor
`description` on them, whether an entry marks them `shared` or claims them as
`self`. The catalog entry is the record of ownership for those.

For components **created by a build run** (New sections) or by the maintain
flow's create-family path:

- `group` = family slug, set at creation by the build flow.
- `description` = `<family>@<version> | candidate | run <slug>` at creation;
  rewritten by `flows/sync.md` to `<family>@<version> | promoted` after the
  maintain flow promotes the candidate and the entry is pushed; set by the
  maintain flow to `<family>@<version> | rejected` for a declined candidate
  that still has instances.

How sync tells the two apart: a run-created component's description already
carries the toolkit tag, or its id is in `created.componentIds` of an archived
manifest under `references/runs/` (the run manifest is where ids live; see
"Components are named, not identified"). Nothing is stamped while a family is
`proposed`.

## Versioning

Patch: guidance-only edits. Minor: new variant, new prop, new optional section.
Major: new required section, changed master page, base-variant edit. Every bump
adds a changelog line with the date and the reason (run slug when promoted from
a candidate).
