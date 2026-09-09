# Flow: build

The per-page workflow. Input: a design plus a submitter who can answer
questions. Output: an unpublished draft page in your Webflow site built from a
template family, a verification report, and the brief and run manifest as
records.

References used: `../references/rules.md` (binding throughout),
`../references/interview.md` (Phase 2), `../references/catalog/` (Phases 0, 3,
5), `../references/brief-schema.md` and `../references/outline-spec.md`
(Phase 4), `../references/manifest-schema.md` (Phases 5 to 7),
`../references/unsupported.md` (Phases 1, 7), `../references/webflow-conventions.md`
(slugs, folders, naming, and every site-specific fact this flow depends on).

Scripts: `../scripts/validate_brief.py`, `../scripts/render_outline.py`,
`../scripts/diff_inventory.py`, `../scripts/manifest.py`. If a script cannot
run, follow the matching reference by hand and say so in the report.

Work through the phases in order. Do not write anything to Webflow before
Phase 5, and do not start Phase 5 before the outline is approved.

**Read the conventions before planning any phase** — the repository's
`webflow-conventions.md`, or `<prefix>/conventions.md` from the instruction
store on a surface that has no repository, or the `conventions` field of an
attached catalog bundle. They are the same content. The facts that
shape a build differ from site to site and are measured at onboarding, not
assumed here: whether the Agent Instruction store is readable; the pacing every
element, props, settings, and builder call needs, which follows from the site's
CMS collection and asset counts; whether loose-section content and slot children
are reachable at all or are manual handoff items; whether the connector token
can write page schema; whether branching is available; the breakpoint list; and
whether the Designer is reachable. Where that file says UNMEASURED, treat the
answer as unknown and say so in the report rather than guessing. If the site has
not been onboarded, there is no catalog and the build stops at Phase 3; point
the user at `flows/onboard.md`.

Throughout, `<prefix>` is the instruction prefix from `webflow-conventions.md`,
"Toolkit settings" (default `page-templates`).

## Phase 0: Preflight (silent unless something is wrong)

1. Call `webflow_guide_tool` once per conversation (skip if already done).
2. Load the site and the family catalog from Webflow Agent Instructions:
   `data_agent_instructions_tool > search_instructions` for the `<prefix>`
   skill and `rules/<prefix>.md`, then `read_instruction` for the SKILL.md
   index, `<prefix>/conventions.md` (the measured facts, on a surface with no
   repository copy of `webflow-conventions.md`), and each
   `catalog/<family>.md`. If the site has none, fall back to the
   bundled `../references/catalog/` and tell the user: "This site has not been
   onboarded; I am using the copy bundled with the skill, which may be empty or
   stale."
   If `search_instructions` returns **HTTP 403 `forbidden`** ("you cannot read
   this SiteAgentInstructions"), the OAuth user lacks
   `agent_instructions:read`. This does not stop the build: use the bundled
   catalog and `../references/rules.md`, remember for the run that the
   instruction store is unavailable (Phase 5 step 1 and Phase 7 depend on it),
   and say once: "The Webflow instruction store is not readable for this
   account; I am using the catalog bundled with the skill." Catalog entries
   with `status: proposed` are usable; note it for Phase 3 and Phase 7.

   A catalog entry that comes back as a **draft** is a family onboarding wrote
   straight into the store (Webflow-store mode) that no maintainer has
   confirmed yet: read it exactly as `status: proposed`.

   **Third case: no store readable and no catalog bundle attached.** The
   bundled `../references/catalog/` ships **empty**, so on claude.ai a 403, or
   a site with no toolkit instructions, can leave the run with no families at
   all. Do not improvise one. Say: "I cannot read a catalog for this site.
   Two ways forward: run `flows/onboard.md` against this site, or attach the
   catalog bundle a previous onboarding produced - the JSON or the HTML file;
   chat accepts HTML, JSON and plain text but not a zip." If the user attaches
   a bundle, take the families, the filled conventions, and the index from it,
   say which date it carries, and treat it as possibly stale (the site may have
   moved on since). If they have neither, state what is degraded before going
   any further: the rulebook still applies (it is bundled at
   `../references/rules.md`), Phases 1 and 2 still work, and the run **stops at
   Phase 3** because there is no family to build from. Nothing site-specific is
   known either - pacing, breakpoints, the capability table, folder ids, slug
   and SEO conventions - so no Webflow write happens in this run at all.
3. **Master pages only**, and only if the flow needs them for scoring: one
   batched `data_pages_tool > get_page_metadata` covering the master page of
   each family you are about to offer (slug and parent folder must match the
   entry). Never use `get_all_elements` here, and do **not** fetch the
   component list: components are reconciled in Phase 3, after a family is
   chosen, so a run only ever asks about the handful of components of the
   family it picked instead of the site's whole library. A master page that is
   missing, moved, or renamed **blocks that family** for this run. Say which
   family is blocked and why, and point the maintainer at `flows/maintain.md`
   (Refresh inventory, then fix the entry). Other families remain usable.
4. Check for an open run manifest with the same slug (once the slug is known,
   re-check): `search_instructions` under `<prefix>/runs/`. If one is `open`,
   offer `flows/resume.md` (resume or clean up) instead of starting a duplicate
   build. When the instruction store is unavailable (403), look in
   `../references/runs/` for `<yyyy-mm-dd>-<slug>.manifest.json` with
   `status: open` (Claude Code, Codex; live runs write there) and otherwise ask
   the user whether a manifest file for this slug exists locally or as a
   download from an earlier conversation.
5. Probe Designer availability once: `designer_tool > get_current_page`. A
   success means the Bridge App is running and snapshots, folder creation, and
   canvas navigation are available. On success also call `get_all_breakpoints`
   once and keep the list for Phase 6; compare it with the list
   `webflow-conventions.md` recorded at onboarding and say so if it changed. A
   failure is not an error; try to bring the Designer to the foreground first,
   then remember the answer for the run and degrade as described in Phases 5
   and 6.

   **Designer foreground procedure** (the Bridge App only answers while its
   Designer tab is open and in the foreground). The failed `get_current_page`
   response contains the launch link for whichever Webflow account and site the
   caller is connected to: "Launch the app using following link <url>". Take
   the url from that response every time. It is a credential and it is
   different for every operator and site, so it is never stored in this
   repository, in a manifest, or in a run record (rule 15).
   - Claude Code or Codex: run `open "<url>"` (`xdg-open` on Linux), wait about
     40 seconds, and re-probe `get_current_page`; up to three attempts before
     recording the Designer as unreachable.
   - Claude.ai: show the url as a markdown link, ask the user to click it and
     leave the tab in front, then re-probe once they confirm.
   Record the outcome (reachable or not, and after how many attempts) in the
   run record; it decides whether Phase 6 snapshots run.

## Phase 1: Intake and design digest

Accepted inputs, in order of preference:

1. Claude Design **standalone HTML export** or **zip export**. (The "Send to
   Claude Code" handoff bundle is only usable on the Claude Code surface and
   its internal format is unpublished; treat HTML or zip as canonical.)
2. Design canvas files produced in Claude Code (`.dc.html` artboards).
3. Other HTML/CSS; Figma exports as HTML or images.
4. Screenshots, PDFs.
5. Links: fetch only if the surface allows it and the link is public;
   otherwise ask for an export.
6. Copy documents (final text) and an image list with public URLs or Webflow
   asset names.

Produce a **design digest** in chat. Separate what you observed from what you
assumed, and label each line accordingly.

- Ordered sections with a type guess: hero, logo bar, feature grid,
  testimonial, pricing, FAQ, CTA band, footer, or "unclear".
- Per section: headings and their levels; body copy; CTAs (label,
  destination); media (source, alt if any, intrinsic size); layout intent
  (columns, alignment, density); states (hover, active, empty).
- Tokens observed: colors, fonts, sizes, spacing, radii, shadows. Build the
  **token reconciliation table** against site variables from the catalog and
  `webflow-conventions.md`: `exact`, `near` (name the substituted token), or
  `none` (flag it). Template styling wins; the design's values are evidence of
  intent, not instructions.
- Interactions and motion observed (hover, scroll, carousels). Webflow
  Interactions cannot be created through MCP; every one of these goes to the
  manual handoff list (`../references/unsupported.md`).
- Missing assets and placeholder copy (lorem, "TBD", "[image]").

Keep the digest under the length of the design itself. A screenshot-only input
produces a digest with more `assumed` lines; that is expected, and the
interview closes the gaps.

## Phase 2: Interview

Question bank and skip logic: `../references/interview.md`. Rules:

- At most **3 questions per turn**.
- Never ask what the digest or an earlier answer already establishes.
- Offer **"use family defaults"** as a fast path once a family is likely; it
  fills SEO patterns, schema type, folder, nav/footer inclusion, and slug
  pattern from the catalog entry.
- After the last topic, confirm a short summary (six to ten lines) and wait
  for a yes before Phase 3.

Topics, in this order: page purpose and audience; primary action and its
destination; page title, slug, folder; SEO title and description, Open Graph
image; nav and footer inclusion; required and optional sections; per-slot
content status (final, draft, missing, manual); images (public URL or asset
already in Webflow by name); forms (existing form or embed to reuse);
responsive intent for anything unusual; localization needs (report-only);
schema type; launch owner. Answers land in the brief under `answers` and are
copied into `page` and `sections` where they belong.

## Phase 3: Template selection

If the catalog is empty, stop here: say the site has not been onboarded, that
there is no family to build from, and point the maintainer at
`flows/onboard.md`. Do not invent a family.

1. Score each usable family against the digest: section overlap, CTA pattern,
   layout similarity, content type. A simple count is fine; explain the score
   in one line per family.
2. Present the **top three** (or all, if fewer). For each: purpose, section
   outline, template model, fit score, reference image (asset URL or stored
   snapshot from the catalog entry), and what would be **Reused**, **Adapted**,
   or **New** for this design under that family.
3. Recommend one. The user may:
   - pick another family;
   - override the template model for this run (`duplicate-master`,
     `component-recipe`, `hybrid`); record the override in the brief;
   - choose the isolation mode. Offer `branch` **only** when
     `webflow-conventions.md` records branching as available, and when you do,
     repeat whatever that file still lists as UNMEASURED as a warning: on most
     sites onboarding can verify only the read path (`get_all_elements` accepts
     a branch page id and returns the branch tree), while writes on a branch
     page and `create_branch` without the Designer stay unverified until the
     first branch-mode run, and conflicts on long-lived branches are a real
     cost. Never offer `branch` when the file says branching is unavailable or
     unmeasured.
   - propose a **new family**. A new family goes through `flows/maintain.md`
     (Create a family) and needs maintainer confirmation before this build
     continues. On Claude.ai, hand the user a note for the maintainer and stop
     the build there.
4. **Reconcile the chosen family.** The catalog names components; their ids are
   resolved here, once the family is known, and recorded only in the run
   manifest. This is the only component read a build makes before Phase 5.
   Resolve every name in the family's section outline and shell tables except
   the `loose` rows (nothing to resolve; their copied class paths are checked
   after `create_page` in Phase 5) and the `candidate:<slug>` rows (nothing
   exists to resolve yet):
   - when the family's components share a component group, **one**
     `data_component_tool > query_components` with a single labelled query
     whose `keywords` name the group and a `limit` that covers it;
   - otherwise batched `data_component_tool > get_component` by `name` (add
     `group` when a name needs it) in a **single tool call**.

   Never `get_all_components` here, and never pass `includeProps`,
   `includeVariants`, or `includeInstanceCount` (all three default to off);
   they belong to the onboarding census and the maintain flow's impact
   analysis, which genuinely need them. The tradeoff, stated honestly: N
   by-name lookups are N server calls where the full list is one, and on a site
   where the per-minute request budget binds, a family that needs many
   components should use the one-call group-filtered `query_components` form
   rather than many `get_component` calls.

   Then the two guards:
   - a name that resolves to **zero** components **blocks that family** for
     this run: "The catalog names `<name>`, which no component on the site
     matches; `<family>` is blocked for this run." Point the maintainer at
     `flows/maintain.md` (Refresh inventory, then fix the entry). Other
     families stay usable; offer the next-best one.
   - a name that resolves to **more than one** component blocks the family too,
     with a different message: "The catalog names `<name>`, which matches <n>
     components on this site (groups: <groups>); `<family>` is blocked until a
     maintainer disambiguates the row by group or renames one of the
     components." Whether this is routine or a drift alarm depends on the
     name-uniqueness answer in `webflow-conventions.md`, "Component names": on
     a site where onboarding found all names unique it is an alarm.

   Keep the resolved name-to-id map for the run and write it into the manifest
   when Phase 5 opens it; nothing in the repository stores a component id, so a
   component that is deleted and recreated only has to keep its name. A resumed
   run re-resolves rather than trusting a stale map: the lookup is cheap.

Reuse levels per section: **Reused** (existing component or variant, values
only), **Adapted** (new variant or new prop on an existing component), **New**
(new component created in this run; becomes a candidate). Every section in the
outline gets exactly one label. A master section copied as a loose element tree
(catalog `Component name` = `loose`) is always **Reused**; to change its layout,
replace it with a component (Reused or Adapted) or a New section.

When the recommended family has `status: proposed`, say so in the
recommendation: "This family was proposed by onboarding and has not been
confirmed by a maintainer; the build can proceed, and the report will say the
family is unconfirmed." Once the maintain flow has confirmed the family
(`status: promoted`), drop the caveat here and in Phase 7; read the status from
the entry every run rather than assuming it.

## Phase 4: Visual outline (approval gate)

1. Assemble the **brief** (`../references/brief-schema.md`; worked example in
   `../assets/examples/example.brief.json`, minimal example in
   `../assets/brief.example.json`). The outline and the build both read this
   one object, so what is reviewed is what gets built. Mark every slot the
   build cannot write with status `manual` rather than `final`. Which slots
   those are is site-specific and comes from the capability table in
   `webflow-conventions.md`, "Rate limits and response sizes": on a site whose
   element reads exceed the request budget that is text, links, and images
   inside loose sections and any slot child; on a small site it may be nothing
   at all. The submitter approves knowing which parts the publisher finishes by
   hand; the outline's handoff panel counts and lists them.
2. Validate it: `python3 scripts/validate_brief.py brief.json`. Fix every
   violation before rendering. Without scripts, run the checklist in
   `brief-schema.md` by hand.
3. Render the **outline**: `python3 scripts/render_outline.py brief.json >
   outline.html`. Without scripts, follow `../references/outline-spec.md`. The
   outline is a single self-contained HTML file with no external assets,
   showing four views: desktop plus the three narrower ones. Map them onto the
   breakpoints `webflow-conventions.md` recorded for your site and say in the
   outline which site breakpoints the frames stand for. Sections are stacked in
   order with their Reused / Adapted / New label, component name and variant,
   editable slots with content status (`manual` slots say "publisher enters in
   the Designer"), an open-decisions panel, the token substitutions, and the
   manual handoff list, which opens with the count of `manual` slots.
4. Show it: as an artifact in Claude.ai, or open the file on Claude Code and
   Codex. Alongside it, in chat, the **section mapping table**: design section
   → family section → component/variant → content that lands there → status.
5. Iterate until the user says **approved**. Record `approvedAt` in the brief.
   Approval covers the concrete outline and every proposed addition (new
   variants, new components, new variables). After approval, routine
   implementation choices proceed without further confirmations; anything that
   would change the approved outline comes back as a question first.

## Phase 5: Build

Order matters. **Every Webflow write is appended to the run manifest before the
next step** (`python3 scripts/manifest.py append ...` or the manual procedure in
`manifest-schema.md`). Pace every element, props, settings, and builder call as
`webflow-conventions.md` says for this site (rule 10).

1. **Open the run manifest.** `manifest.py create` with site, family and
   version, model, isolation mode, surface, and the brief hash. Write it to
   Webflow as `<prefix>/runs/<yyyy-mm-dd>-<slug>.md` with `isDraft: true`
   (`data_agent_instructions_tool > create_instruction`), the body starting with
   "This is a run record, not guidance." Offer the same content as a download.
   If `create_instruction` returns **403** (or the store was already unavailable
   in Phase 0), do not abort: keep the manifest and the brief as local files
   next to each other (Claude Code, Codex: the working directory) or, on
   Claude.ai, hand both to the user as downloads at the end of every phase, skip
   the `update_instruction` calls the later steps would make, and record in the
   manifest and the report that the Webflow instruction store was not writable
   and the run record lives locally.
2. **Pre-snapshot.** Read the names and definitions of every style, component,
   and variable the run may touch (the family's components with variants and
   props, the classes the catalog rows name, the variables in the
   reconciliation table) and, cheaply, the full component list
   (`get_all_components` without props; the guard compares the whole list, so
   this is the one place in a build that reads every component, and it still
   goes without `includeInstanceCount`). Shape and field mapping:
   `manifest-schema.md`, "Snapshot shape"; a trimmed worked example is
   `scripts/tests/fixtures/example/pre.snapshot.json`. Style reads are
   serialized; do not copy instance counts into the snapshot. Save the snapshot
   JSON with the manifest (`preSnapshotHash`). This is what the guard compares
   against in Phase 6.

   On Claude Code the three reads (`get_all_components` with props and
   variants, `get_variables` per collection, `query_styles` with
   `include_properties`) can be large enough that the client saves the result
   to a file and shows only smaller ones inline. Build the snapshot from the
   saved files with `python3 scripts/build_snapshot.py` (it maps the tool
   output onto the snapshot shape, keeps only the named classes, expands props
   and variants for the family's components, and prints the sha256 for
   `manifest.py set --pre-snapshot-hash`). Never retype an inline result into
   the snapshot: a transcription slip becomes a false guard verdict. If a
   result comes back inline, make the same call larger so it is saved (read two
   variable collections in one call; add padding `name_path` queries to
   `query_styles`, which the script ignores because it keeps only `--classes`),
   and use the identical call for the post-snapshot. Do the asset-library
   lookups the brief needs **before** this step, and leave the gap
   `webflow-conventions.md` prescribes between the last bulk read
   (`list_assets`, `get_all_components`, `get_variables`) and the first element
   read of step 5: they share one per-minute request budget (rule 10).
3. **Isolation.** `draft-main`: nothing to do. `branch`: `data_pages_tool >
   create_branch` from the master (duplicate-master, hybrid) or from an empty
   page (recipe), poll `get_branch_task_status` until done, and use the branch
   page ID for every later call. Whether the data tools address a branch page by
   its own page id on the **read** path is recorded in
   `webflow-conventions.md`; writes on a branch page and `create_branch`
   without the Designer are unverified until the first branch-mode run. If a
   write rejects the branch page ID, stop and report rather than falling back
   to main silently.
4. **Page.** `data_pages_tool > create_page` with `title`, `slug`,
   `parentFolderId` (from the brief's folder; folders are pre-created at
   onboarding), `seo`, `openGraph`, and **`draft: true` set explicitly**, plus
   `duplicateOf` = the master page ID for duplicate-master and hybrid.
   Immediately `get_page_metadata` and confirm `draft: true` reads back. If it
   does not, stop, fix it (`update_page`), and re-read before anything else.
5. **Sections.** First, one `data_element_tool > get_all_elements` with a small
   depth (2 is usually enough: body, `main`, and the section roots) on the new
   page to map what the duplicate produced onto the catalog rows. Pacing per
   rule 10 and the site's own numbers: no bulk read in the preceding quiet
   window, the prescribed gap before the next element read, and on a 429 one
   ten-minute zero-traffic wait and one retry, then a `failed` manifest step
   naming the endpoint, the page left as a draft, the manifest `open`, and a
   BLOCKED report (`flows/resume.md` continues from that step). Do not reach for
   a full-depth read on an image-heavy page unless onboarding measured that it
   works here: the element tools resolve an asset per image node, which is what
   tips a large site over its budget. Read the content nodes later, one section
   at a time, with `query_elements` scoped to the section root (step 6), on a
   site where `query_elements` works at all. Space **every** element, props,
   settings, and builder call, writes included, as the conventions file says,
   and batch actions per call.

   The mapping: the children of `main` in order, each either a component
   instance (match by the component id Phase 3 resolved for the row's name) or
   a loose section root (match by position and class path, the brief's
   `masterSection` and `classPath`). Then, per the approved outline: remove
   master sections the outline dropped with `remove_element` on the copied
   section root (allowed here because every copied element was created by this
   run's `create_page`; the same applies to copied component instances); insert
   component instances the outline adds with `data_component_builder >
   insert_component_instance`, passing the id Phase 3 resolved for that name, at
   the position the outline gives, filling slots with `insert_in_slot`; reorder
   with `move_element`. Loose sections are never created new: a section the
   master lacks is a component or a New section. Read back `get_all_elements`
   once after the pass.
6. **Content.** Props through `data_component_props_tool >
   set_component_instance_prop_values`, batched per instance (several instances
   per call are fine). Its link values may accept only `url`, `email`, and
   `phone` modes although the schema lists `page`: when that is so, a prop that
   must point to a page keeps the component's default page link or is set
   through `data_element_settings_tool` on the button inside the instance; say
   which in the report. Text props take `type: string`.

   Whether the build can reach **loose-section nodes and slot children** is the
   capability table in `webflow-conventions.md`. Where it can: find the nodes
   with `data_element_tool > query_elements` and an `element_filter` scoped to
   the copied section root (by element type, by class, or by the master's
   current text), then write with `data_element_settings_tool`: text, link
   `href` with target and any tracking attribute, image asset and alt. Set the
   H1 first. Where the conventions file says it cannot (deep reads 429, or slot
   children come back without element ids), treat every loose-section slot and
   every slot-child prop as a manual handoff item, keep component props as the
   only automated content path, and tell the submitter at the outline stage
   which slots will be filled by hand.

   Where the master carries more repeated nodes than the brief (a fourth stat
   card, a fifth FAQ question block) remove the surplus with `remove_element`;
   where it carries fewer, insert with `data_element_builder` (loose) or
   `insert_in_slot` (component slot) and say so in the report. Images: prefer one
   **already in the asset library**, matched by name (`data_assets_tool`). Alt
   text on every image; internal links resolved to page IDs, never typed as
   paths.

   **Before any `asset_tool > upload_image_by_url`, stop and warn, in these
   words:** "Uploading an asset makes it public immediately.
   `upload_image_by_url` puts the file in the site's asset library, and Webflow
   serves library assets from a public CDN URL from the moment of upload,
   before any publish and whether or not this draft page is ever published.
   Anyone who has the URL can fetch it without logging in. Deleting the asset
   later does not un-serve a URL someone already has. May I upload
   `<file or source url>`, or is there an asset already in the library I should
   use instead?" Wait for the answer. Never upload something confidential,
   unreleased, or under embargo in order to get a draft built (rule 19). Record
   every upload in the manifest and list them in the report as their own
   **already public** line (Phase 7).

   Slots the brief marks `missing` get a visible `TODO: <slot name>`
   placeholder.
7. **Adapted sections.** New variant on the existing component
   (`data_component_variants_tool > create_variant`, then `set_variant_styles`)
   or new prop definitions (`data_component_props_tool`). Never edit base
   variant styles of a pre-existing component in a build run.
8. **New sections.** `data_component_tool > create_blank_component` with
   `group` = family slug and `description` = `<family>@<version> | candidate |
   run <slug>`. Build inside the component with `data_element_builder`, or with
   `data_whtml_builder` only after remapping the CSS to existing classes and
   variables: single root element, no `<style>`, no `@keyframes`, only the
   Webflow breakpoint media queries the conventions file records. Create styles
   (`data_style_tool`) before the elements that use them; new class names follow
   the site's naming system with the family prefix (`webflow-conventions.md`).
   Write a candidate record to `<prefix>/candidates/<slug>.md` (`isDraft: true`).
9. **Page-level metadata.** JSON-LD via `data_pages_tool >
   bulk_update_pages_schema_markup` from the family's schema template with the
   brief's values, **if** `webflow-conventions.md` records the page schema write
   as allowed for the connector token. Where it is refused (**403
   `insufficient_permissions`**; the token can read schema but not write it),
   record the step as `failed`, do not put `FAQPage` into an FAQ component's
   `Schema` prop unless the visible question blocks match it, and hand the
   JSON-LD payload to the publisher (Page settings > Custom code) until the
   scope is granted. No page scripts. Custom embeds only if the approved outline
   listed them; otherwise a manual handoff note. Write the candidate record for
   any Adapted or New section to `<prefix>/candidates/<slug>.md`
   (`isDraft: true`); when the store is unavailable, write it locally next to
   the manifest and hand it to the maintainer with the report.
10. **Never**, in this phase or any other: `publish_site`; `publish_branch`
    (except staging, on explicit request, in branch mode);
    `unregister_component`; `delete_variable`; `remove_element` on anything not
    created in this run; `update_style` on a pre-existing class;
    `set_site_scripts`; `set_page_scripts`; localization writes.

If the Designer is not reachable and a step needs it (folder creation, canvas
navigation), do not improvise: use the pre-created folder from the catalog, or
record the step as a manual handoff item.

## Phase 6: Verify (readback, not memory)

Every check reads the live site. Do not answer from what you intended to do.

- **Structure.** One `data_element_tool > get_all_elements` on the page
  (serialized, never alongside other element reads), as deep as the conventions
  file says this site tolerates: section order matches the approved outline;
  component instances and variants match the recipe; prop values are set; no
  leftover master sections; loose section roots keep the class paths the catalog
  rows name. Everything else in this phase uses the cheap reads
  (`get_page_metadata`, `get_all_components`, `query_pages_schema_markup`).
- **Page.** `get_page_metadata`: `draft: true`, correct slug, folder, SEO, Open
  Graph. Schema markup reads back with the expected type.
- **Guard.** Post-snapshot the same styles, components, and variables as Phase 5
  step 2 and run `python3 scripts/diff_inventory.py pre.json post.json`. Any
  change to a **pre-existing** definition fails the run. Name each change in the
  report and ask the user whether to revert it by hand in the Designer or accept
  it; acceptance is recorded in the manifest as a deliberate deviation
  (`diff_inventory.py --accept kind:key`). Save `postSnapshotHash` and
  `guardVerdict` to the manifest.
- **Content.** No lorem or TODO text except slots the brief marked `missing`
  (those carry the visible `TODO:` prefix and are listed); heading hierarchy is
  one H1 and no skipped levels; alt text present on every image; links resolve
  (internal page IDs exist, external URLs well-formed); primary CTA present
  above the fold (first or second section).
- **Visual.** If the Designer is reachable: `designer_tool > switch_page` to the
  page, then `element_snapshot_tool` on the page root and each section, **one
  call at a time** (parallel calls have been observed to return
  `status: false`). If the foreground procedure was run, the Bridge App is now
  bound to a newly opened tab showing the site's home page: `switch_page` again
  first, or the snapshot returns `status: undefined`. Iframes render blank. The
  tool takes only an element id (no breakpoint or viewport argument), so a
  snapshot shows whatever breakpoint the Designer canvas is on; to review the
  narrower views, ask the human to switch the canvas breakpoint (using the ids
  from the conventions file) and snapshot again. Element ids come from the
  Phase 6 structure read; when that read is blocked (rate limit), snapshots are
  too, unless the human selects an element and `designer_tool >
  get_selected_element` returns its id. Otherwise the report says: "Visual
  verification pending. Open the page in the Designer with the Bridge App
  running and re-run verify."
- **Ships-at-next-publish list and already-public list.** `python3
  scripts/manifest.py ships manifest.json` returns both. `shipsAtNextPublish`:
  components, styles, and variables created on main by this run; empty when
  isolation is `branch`. `alreadyPublic`: every asset this run uploaded,
  reported in **both** isolation modes, because the asset library is
  site-level, a branch does not isolate it, and Webflow serves library assets
  from a public CDN URL from the moment of upload (rule 19). Without the
  script, read `created.styleNames`, `created.componentIds`,
  `created.variableIds` and `created.assetIds` from the manifest by hand
  (`manifest-schema.md`).

A failed guard sets the manifest `status` to `failed` until the user decides; a
clean run sets `verified`.

## Phase 7: Report and handoff

Return, in this order:

1. Where to find the page. Always the page ID, the slug, and the folder path in
   plain text (`Pages panel > <folder> > <page>`). If the Bridge App is
   connected, call `designer_tool > switch_page` with the page id so the draft
   is already on the canvas, and say so. A `https://<site-short-name>.design.webflow.com?pageId=<page id>`
   URL may be offered as a convenience link only if `webflow-conventions.md`
   records that it works on this site, and marked "unverified" otherwise.
2. Slug and folder; isolation mode (and branch name if any).
3. The section mapping table **as built**, with reuse labels.
4. Verification results, item by item, and the guard verdict.
5. Manual work list: Interactions, embeds, fonts, anything from
   `unsupported.md`, every slot the brief marked `manual`, and any step skipped
   because the Designer was closed.
6. Open decisions still unresolved.
7. **Already public: assets uploaded by this run.** One line per asset, with
   its name and its CDN URL: "these files are on Webflow's public CDN now,
   before any publish and whether or not this page is ever published; anyone
   who has the URL can fetch them without logging in. Deleting an asset later
   does not un-serve a URL someone already has." Say "none: every image came
   from the existing asset library" when the run uploaded nothing, because that
   is the good outcome and it is worth stating. This line comes **before** the
   ships-at-next-publish list and is more urgent than it: that one is a
   prediction about the next publish, this one has already happened.
8. Ships-at-next-publish list, in plain words: "these will go live for the whole
   site when someone next publishes, even though the page stays a draft."
9. Candidate additions written to Webflow (`<prefix>/candidates/`), with the
   note that a maintainer promotes them through `flows/maintain.md`. If the
   family used has `status: proposed`, say so here: the family, its master, and
   its component names were proposed by onboarding and have not been confirmed
   by a maintainer.
10. The brief and the manifest as downloads (and their instruction paths). If the
   instruction store was unavailable (403), say: "The Webflow instruction store
   was not readable or writable for this account; the run record and the brief
   exist only as these files. Keep them; resume and cleanup need them."
11. Publishing instructions for the human publisher, named according to
    `webflow-conventions.md`, "Publish policy". They finish the manual work
    list, review in the Designer, turn off the draft flag when ready, and
    publish (or merge the branch) themselves. The skill has not published and
    will not; the page is not published until the manual list is done.

Close the manifest (`status: verified` or `failed`) and update the instruction
copy in Webflow before ending the conversation.
