# Unsupported through MCP, and the Designer handoff for each

What the Webflow MCP server cannot do, and what the report tells the human to
do instead. Every item the build flow meets from this list goes into the
brief's `unsupported[]` and the report's manual work list, worded as an
instruction someone can follow in the Designer.

Two kinds of row are mixed here and it matters which is which. Most rows are
**capability gaps**: the MCP server has no tool for the thing, on any site. The
rows at the end are **conditional**: whether they apply to you depends on a scope
your connector token may or may not have, or on a limit your site may or may
not hit. `flows/onboard.md` measures those and records the answer in
`webflow-conventions.md`; do not carry a conditional row into a report without
checking it there first.

| Gap | Kind | Why | Handoff wording (adapt the specifics) |
| --- | --- | --- | --- |
| **Webflow Interactions** (hover, scroll, load animations, carousels, accordions built with IX) | capability | No MCP tool creates or edits Interactions | "Open the page in the Designer, select `<element>`, add an Interaction: `<trigger>` → `<effect>` (`<duration>`, `<easing>`). The design showed `<what was observed>`." Never fake motion with embeds or scripts. |
| **Google or Adobe fonts** | capability | `data_fonts_tool` lists fonts; adding a Google or Adobe font is a site setting | "Site settings → Fonts → add `<family>` with weights `<list>`. Then map the `<type variable>` to it." Until then the template's font stays; report the substitution. |
| **Roles, access, and workspace settings** | capability | No MCP surface | "Ask a workspace admin to grant `<person>` `<role>` on `<site>`." |
| **Localization writes** | capability (deliberate) | Rule 16: primary locale only; `data_localization_tool` reads only for this skill | "Locale `<code>` needs the following strings translated after the page is final: `<slot list>`." |
| **Multipart asset upload on Claude.ai** | capability | `data_assets_tool > create_asset` then a POST to S3 needs sandbox network access; only used on Claude Code | "Upload `<file>` to Assets in the Designer (or give a public URL) and tell me the asset name; I will place it." |
| **Designer-dependent tools when the Designer is closed** (`element_snapshot_tool`, selection, `get_current_page`, `create_page_folder`, canvas navigation, branch context) | capability | Need the Designer open with the Bridge App running | "Open the site in the Designer with the Bridge App running and re-run verify; visual checks are pending." Folders are pre-created at onboarding so builds do not depend on this. |
| **Publishing** | capability (deliberate) | Rule 8 | "Review in the Designer, turn off the draft flag, publish yourself." |
| **Custom code beyond the approved outline** (page scripts, head code, embeds not in the outline) | capability (deliberate) | Rule 14 | "If `<embed>` is needed, add it in the Designer as an Embed element in `<section>`; the outline did not include it." |
| **CMS schema changes and Collection template pages** | capability (scope) | Out of scope for this skill | "This page needs a new CMS field `<name>` on `<collection>`; a maintainer adds it, then a later run binds it." |
| **Branch creation or merge before branch tooling is verified on your site** | conditional | Onboarding can verify only that element reads accept a branch page id; writes on a branch page and `create_branch` without the Designer stay unverified until the first branch-mode build (`webflow-conventions.md`, "Branching") | "Create the branch in the Designer (Pages → `<page>` → Create branch) and tell me the branch page ID" when the MCP path fails. |
| **Agent Instructions when the connector user lacks `agent_instructions` scopes** (HTTP 403 on `search_instructions` and `create_instruction`) | conditional | A scope on the OAuth token, not a missing tool. `webflow-conventions.md`, "Agent Instructions", records whether it applies to you | "Ask the Webflow workspace admin to grant the connector user `agent_instructions:read` and `agent_instructions:write` on the site, or run the install from an account that has them." Until then the run keeps its brief and manifest as files, and onboarding hands over the catalog as a download bundle instead of installing it. |
| **Page-level JSON-LD when the connector token lacks the page schema write scope** (HTTP 403 `insufficient_permissions` on `bulk_update_pages_schema_markup` while `query_pages_schema_markup` works) | conditional | Token scope, not a missing tool. Measured at onboarding; see "Schema defaults" | "Ask the Webflow workspace admin to grant the connector user the page schema write permission, or paste this JSON-LD into Page settings > Custom code > Head for `<page>`: `<payload>`." |
| **Content inside loose sections and slot children on a site whose element reads exceed the request budget** | conditional | Webflow MCP prefetch, not a missing tool; `rules.md` rule 10. Whether it applies is the capability table in `webflow-conventions.md`, "Rate limits and response sizes". On a small site this row does not apply at all | "In the Designer set `<node>` in `<section>` to `<value>`" for each unreachable slot; the report lists them with the brief's final text so the edit is copy and paste. |
| **A Designer URL that opens a given page** | conditional | No MCP tool returns a page URL; guessed `https://<site-short-name>.design.webflow.com?pageId=` forms may open a tab the Bridge App is not bound to. `designer_tool > switch_page` navigates the connected tab | "In the Designer open Pages > `<folder>` > `<page title>` (page id `<id>`)." When the Bridge App is connected the run has already switched the canvas to the page. |
| **Tracking a CTA carries that the build did not write** (link extras, or the family's analytics shell component) | conditional | Not a missing tool: rule 14 keeps a build from writing a tracking scheme the site does not already use, and MCP cannot read click listeners in either direction. Whether it applies is `webflow-conventions.md`, "Site-level tracking" | "In the Designer open `<page>` and give `<CTA element>` the same link extras the site's other CTAs already carry: `<UTM keys or attribute name and value>`, as on `<sibling CTA>` on `<sibling page>`." For a missing shell: "place the existing `<component name>` component the `<family>` shell table names in `<section>`." Do not invent a new attribute, a new UTM set, or a new component. |

## How to phrase a handoff

One line each, imperative, with the element and the observed value. The reader
is a designer in the Webflow Designer, not an engineer. Example:

> Hero image: add a fade-in on page load (300 ms, ease-out) to the element
> `hero_media`. The design showed the image fading in from 0 to 100 percent.

## When something is not on this list

If a tool exists but fails for the run (rate limit, permissions, unexpected
error), that is not "unsupported": record the failed step in the manifest and
retry or ask. Add a capability row here only when the capability is missing
from the MCP server itself; add a conditional row only with the probe that
established it and a pointer to where the answer is recorded.
