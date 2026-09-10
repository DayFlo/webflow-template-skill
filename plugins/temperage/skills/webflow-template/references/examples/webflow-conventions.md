# Webflow conventions (Example Co, worked example)

**Fictional.** Every id, name, count, and timestamp below was invented for the
worked example in `references/examples/` and `assets/examples/`. No Webflow
site was read to produce it. It exists to show what
`references/webflow-conventions.md` looks like once `flows/onboard.md` has
filled the template in, so that a maintainer can recognize a finished file.
Onboarding overwrites the template with your site's real measurements; it does
not touch this file.

Measured by a read-only onboarding pass on 2026-01-04 and confirmed on
2026-01-05. Nothing was written to Webflow except the page folders in step 6.

## Toolkit settings

| Setting | Value | Notes |
| --- | --- | --- |
| Instruction prefix | `page-templates` | Default kept; nothing else on the site owns it. Paths: `rules/page-templates.md`, `page-templates/SKILL.md`, `page-templates/conventions.md`, `page-templates/catalog/<family>.md`, `page-templates/candidates/<slug>.md`, `page-templates/runs/<date>-<slug>.md`. |
| Store | repository | The maintainer has repo write access, so git is the reviewed source and `flows/sync.md` pushes to Webflow. |

## Sites

| Site | Site ID | shortName | Purpose | Custom domains | Publish policy |
| --- | --- | --- | --- | --- | --- |
| Example Co Website | `0000000000000000000000a0` | `example-co` | Marketing site: products, integrations, pricing | `example.com` | Humans publish, in Webflow. The skill never publishes. |

Locale: one primary locale, English, localization not enabled, no secondary
locales.

## Site-level tracking

`get_site_scripts` returned nothing: no registered script is applied site-wide.

| Question | Answer | Measured |
| --- | --- | --- |
| Delivery — how tracking reaches a page | A named shell component: `Analytics script`, placed first inside the body of every page and named in the Product landing shell row | 2026-01-04 |
| Link extras the MCP can see on existing CTAs | UTM keys: `utm_source`, `utm_medium`, `utm_campaign` on outbound CTAs only; internal CTAs carry no extras and no custom attribute | 2026-01-04 |
| Sibling CTA the answer was read on | "Start free trial" in the `CTA band` on `/products/orbit` — `href` `https://app.example.com/signup?utm_source=example-co&utm_medium=site&utm_campaign=orbit` | 2026-01-04 |

Whether the `Analytics script` component fires anything on click is not
readable through MCP and was not guessed at. A build matches the three UTM keys
on an outbound CTA, writes internal destinations bare, and hands anything else
to the publisher.

## Class naming

House BEM with layer prefixes. Not Client-First: probes for `padding-global`,
`text-size-*` and `heading-style-*` returned nothing.

| Prefix | Layer | Real examples read from the site |
| --- | --- | --- |
| `l-` | Layout and utility | `l-section`, `l-section--header`, `l-container`, `l-pad-b--64px`, `l-pad-b--112px`, `l-bg--surface-0`, `l-bg--surface-1`, `l-bg--surface-2`, `l-mode--dark`, `l-overflow--hidden` |
| `c-` | Site-wide components | `c-button`, `c-button__text`, `c-button__icon` |
| page prefix | One-off page styles, prefixed with a page nickname | `orbit-hero__bg` |

Known inconsistencies: a handful of unprefixed legacy classes (`button`,
`footer__sub`) survive beside the prefixed system. Listed for human review; the
skill does not standardize them.

## Design tokens (variables)

| Collection | ID | Modes | Variables | Contents |
| --- | --- | --- | --- | --- |
| Colour | `collection-1111aaaa-0000-4000-8000-000000000200` | Base, Dark Mode | 8 | `surface/*`, `text/*`, `accent/*`; Dark Mode remaps the aliases and is what `l-mode--dark` switches |

No dangling aliases: every alias target exists.

## Templates and reusable sections

| Family | Slug | Model | Master page (id, slug) | Exemplar | Shell components | Body signature | Confidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Product landing | `product-landing` | hybrid | `0000000000000000000000b1` `product-landing-master` | same | Analytics script, Site nav, Site footer | Hero, optional logo bar, media walkthrough, one loose `l-section` band, feature grid, FAQ, CTA band | Confirmed 2026-01-05 (1.1.0) |

Shared section components across families, by name with instance counts from
the 2026-01-04 census: `FAQ section` (46), `CTA band` (29), `Feature grid` (6),
`Two column layout section` (24). Slot fillers: `FAQ question block` (240).

## Component names

| Question | Answer | Measured |
| --- | --- | --- |
| Total components | 12 | 2026-01-04 |
| Distinct names | 12 | 2026-01-04 |
| Names unique? | yes | 2026-01-04 |

## Page folders

| Folder ID | Path | Children | Notes |
| --- | --- | --- | --- |
| `0000000000000000000000c1` | `/products` | 6 | Product pages |
| `0000000000000000000000c2` | `/integrations` | 2 | Static partner integration pages |

| Family | Allowed folders |
| --- | --- |
| Product landing | `/products` (`0000000000000000000000c1`), `/integrations` (`0000000000000000000000c2`) |
| Anything else | ask |

Both folders already existed, so step 6 created none.

## Slug, title, SEO and Open Graph conventions

- Slugs: lowercase kebab-case, one to three words, matching siblings in the folder.
- SEO title: `<Subject> | Example Co`, under 60 characters.
- SEO description: 140 to 160 characters, from the hero subhead.
- Open Graph: title and description copied from SEO; image 1200x630 from the asset library (`og-default.png`).

## Schema defaults

Masters were read with `query_pages_schema_markup` before deciding.

| Family | `schemaType` | `additionalSchemaTypes` |
| --- | --- | --- |
| Product landing | `WebPage` | `FAQPage` |

Page schema **write** (`bulk_update_pages_schema_markup`): allowed for the
connector token on this site, verified 2026-01-05.

## Isolation default

`draft-main` for the one family. `branch` is offered per run because branching
is available; the run repeats the unverified-write warning below.

## Publish policy

Humans publish, in Webflow. The responsible publisher for a page the skill
built is the person whose Webflow MCP connection ran the build, named in the
run report. They finish the manual work list, review in the Designer, clear the
draft flag, and publish.

## Branching

| Question | Answer | Measured |
| --- | --- | --- |
| `list_branches` result | 200, available, one live branch | 2026-01-04 |
| Branch page reads | `get_all_elements` on a branch page id returned the branch tree | 2026-01-04 |
| Branch page writes | UNMEASURED until the first branch-mode build | |
| `create_branch` without the Designer | UNMEASURED until the first branch-mode build | |
| Live branches and their state | 1, ready, no conflicts | 2026-01-04 |

## Designer availability

| Question | Answer | Measured |
| --- | --- | --- |
| Bridge App reachable during capture | yes, while the Designer tab was open and in front | 2026-01-05 |
| Snapshot behaviour | sequential `element_snapshot_tool` calls succeeded; parallel calls returned `status: false`; the snapshot uses whatever breakpoint the canvas is on | 2026-01-05 |

| Breakpoint id | Designer name | minWidth | maxWidth | Base |
| --- | --- | --- | --- | --- |
| `main` | Desktop | none | none | yes |
| `medium` | Tablet | none | 991 | no |
| `small` | Mobile (L) | none | 767 | no |
| `tiny` | Mobile | none | 479 | no |

The outline's four frames map onto `main`, `medium`, `small`, `tiny`. The
Bridge App launch link is read from the failed probe response at run time and
is not recorded here (rule 15).

## Agent Instructions

| Question | Answer | Measured |
| --- | --- | --- |
| `search_instructions` result | 200, no hits | 2026-01-04 |
| Paths another team already owns | none | 2026-01-04 |
| Toolkit paths already present | none | 2026-01-04 |
| Exposure check (`flows/onboard.md` step 10) | marker not found in public output after a publish on 2026-01-06 | 2026-01-06 |

## Token scopes observed

Pages read and write, elements, components, props, styles, variables, assets,
Designer tools, Agent Instructions read and write, page schema read and write:
all allowed for the connector user on 2026-01-05.

## Rate limits and response sizes

| Probe | Result |
| --- | --- |
| CMS collections | 3 |
| Assets | 180 |
| `get_all_elements` depth 1, 2, 3, -1 on the busiest page | all 200, one at a time |
| `query_elements` type-filtered | 200 |
| Two element calls 20 seconds apart | 200 |
| Bulk read then an element read, back to back | 200 |
| Response sizes | all under the chat token limit; nothing had to be saved to a file |
| Slot children at depth 3 | returned **with** element ids |

Pacing adopted for this site: serialize element reads, leave 20 seconds
between them, and retry once after 60 seconds on a 429. This site is small
enough that the shared per-minute budget was never a binding constraint, which
is the opposite of the large-site case study in `rules.md` rule 10.

| Capability | On this site | Measured |
| --- | --- | --- |
| Component props | automated | 2026-01-05 |
| Loose-section text, links, images | automated | 2026-01-05 |
| Slot children | automated | 2026-01-05 |
| Depth-limited structure reads | all depths | 2026-01-05 |

## Fonts, forms, CMS collections

Two custom fonts, woff2, `font-display: swap`. No forms on the pages this
family covers. Three CMS collections, none of which a `product-landing` page
depends on.

## Reconciliation log

| When | Call | Result |
| --- | --- | --- |
| 2026-01-04 | `webflow_guide_tool` (once) | tool list read |
| 2026-01-04 | `data_sites_tool > list_sites`, `get_site` | one site, primary locale only |
| 2026-01-04 | `data_component_tool > get_all_components` with all three include flags | 200, 12 components, names unique |
| 2026-01-04 | `data_scripts_tool > get_site_scripts`, then CTA links on the exemplar pages | no site-wide scripts; `Analytics script` component; three UTM keys on outbound CTAs |
| 2026-01-04 | `data_pages_tool > list_branches` | 200, branching available |
| 2026-01-04 | `data_agent_instructions_tool > search_instructions` | 200, no hits |
| 2026-01-05 | `designer_tool > get_current_page`, `get_all_breakpoints` | reachable; four breakpoints |
| 2026-01-05 | `data_pages_tool > query_pages_schema_markup` on the master | 200, `WebPage` |
