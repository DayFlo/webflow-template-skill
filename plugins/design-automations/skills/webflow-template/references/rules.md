# Rulebook: Webflow MCP on your site

Mirrored to the Webflow Agent Instruction path `rules/<instruction prefix>.md`
(default prefix `page-templates`, set once in `webflow-conventions.md`) by
`flows/sync.md`. Git is the reviewed copy; Webflow is the copy every connected
agent reads at runtime. Edit here, then sync.

These rules bind the `webflow-template` skill and any other agent connected to
the site through the Webflow MCP server.

1. Call `webflow_guide_tool` once per session. Read `rules/<prefix>.md` and the
   `<prefix>` skill (catalog index and family entries) before planning any
   change.
2. Use explicit `site_id` and page IDs taken from the catalog and the run
   manifest. Never guess an ID, and never pick a page by matching a name from
   memory. **Components are the exception, and only components**: the catalog
   names them, a run resolves the name to an id through the component tool
   (rule 10), and that id is written only to the run manifest. Pages and
   folders keep their ids in the catalog because the MCP has no lookup by
   slug (`catalog/README.md`, "Why pages and folders keep their ids").
3. Reuse before create: existing components, variants, styles, and variables
   first. New class names follow the site's naming system and carry the
   family prefix (`webflow-conventions.md`).
4. Components carry changing content through props and slots. Loose elements
   are used only where the family entry explicitly allows them.
5. Create styles before the elements that use them. Extend through new
   variants, new classes, or new variables. Never `update_style` on a
   pre-existing class outside the maintain flow.
6. Never delete or unregister anything not created in the current run.
   Destructive calls on run-created resources require an explicit user
   confirmation in that same turn.
7. Pages are created with `draft: true` set explicitly (the API default is
   `false`) and the flag is confirmed by `get_page_metadata` readback before
   any other write to the page.
8. Never call `publish_site`. `publish_branch` only on explicit request, in a
   run that uses branch mode, and only to staging. Production publishing is
   done by humans in Webflow. What a staging URL does for an anonymous visitor
   is recorded in rule 19; it is measured, not assumed.
9. Record every write in the run manifest before the next write. On
   interruption, resume from the manifest rather than rebuilding.
10. Batch actions per tool call where the tool allows it. Keep reads filtered
    (styles by prefix, components by need) to stay under response limits.
    Element reads (`get_all_elements`, `query_elements`) are **serialized,
    never parallel**.

    **Pacing is a measured property of your site, not a constant.** Every
    Webflow MCP call draws on one shared per-minute request budget, and the
    element, props, settings, and builder tools each prefetch the site's CMS
    collections and resolve assets for the nodes they return. How much of the
    budget one call costs therefore scales with how many CMS collections and
    assets the site has. `flows/onboard.md` step 3 characterizes this for your
    site and writes the answer into `webflow-conventions.md`, "Rate limits and
    response sizes"; every flow reads the pacing from there. Until that
    measurement exists, use the conservative defaults below.

    Conservative defaults, tightened or relaxed by what onboarding measured:
    - at least **120 seconds between any two element reads**;
    - never call `list_assets`, `get_all_components`, or `get_variables`
      within **five minutes before** an element read (do those reads first,
      then the element reads);
    - keep each element read as small as the step needs (a depth-limited
      `get_all_elements`, or `query_elements` scoped to one section root);
    - **writes count too**: the element, props, settings, and builder tools
      prefetch the same data on every call, so the spacing applies to every
      `data_element_tool`, `data_element_settings_tool`,
      `data_component_props_tool`, `data_component_builder`, and
      `data_element_builder` call, read or write, and each call should batch
      as many actions as the tool allows;
    - on a `429 Too Many Requests` wait **ten minutes with zero Webflow
      traffic** and retry once; if it fails again, record the step as `failed`
      in the manifest with the endpoint named, stop, and report BLOCKED with
      the page left as a draft;
    - prefer the cheap reads (`get_page_metadata`, `get_component`,
      `query_components`) over element reads for reconciliation and
      verification. Those have not been observed to hit the budget.

    An illustrative case study, so the shape of the failure is recognizable:
    on one site with roughly two thousand assets and eighty-plus CMS
    collections, a full-depth `get_all_elements` on an image-heavy page
    returned `GET /v2/assets` 429 even from a completely cold budget, while
    depth 1, 2 and 3 reads of the same page succeeded; `query_elements`
    returned the same 429 whatever it was asked for, because it lists the
    asset library regardless of the filter; and slot children came back at
    depth 3 with their props but **without element ids**, so they could not be
    edited or removed from that read. On that site the consequence was that
    content inside loose sections and inside component slots was not reachable
    through the MCP at all and had to be handed to the publisher. **A small
    site may never hit any of this.** Do not assume either outcome: measure it
    at onboarding, record what you found, and only then decide whether loose
    sections and slot children are automated or manual on your site.

    **Ask for the components you need, by name, and nothing else.** The
    catalog names components and the id is resolved at run time.
    `get_all_components` with `includeVariants` returns every component and
    every variant on the site in one large response; `get_component` by `name`
    (plus `group` to disambiguate) costs a fraction of that for a handful of
    names batched into a single tool call, and one `query_components` query
    whose `keywords` are a component group name pulls a whole family in one
    call. Reconciliation therefore uses `query_components` when the family's
    components share a group and batched `get_component` otherwise, never
    `get_all_components`. The tradeoff is real and worth saying out loud: N
    by-name lookups are N server calls where the full list is one, which is
    why the one-call group-filtered form exists for families that need many
    components.

    **Include-flag discipline**: the `options` flags `includeProps`,
    `includeVariants` and `includeInstanceCount` all default to **off**; leave
    them off everywhere except the onboarding census (`flows/onboard.md`
    step 3, the site's one full inventory) and the maintain flow's impact
    analysis (`includeInstanceCount`, which is the blast radius), plus the
    guard's pre/post snapshot, which needs the whole component list to diff
    it. Everywhere else they buy nothing and cost payload.
11. `data_whtml_builder` only for New sections, and only after the CSS has
    been remapped to existing classes and variables: single root element, no
    `<style>`, no `@keyframes`, only Webflow breakpoint media queries. Use the
    breakpoint widths `webflow-conventions.md` records for your site, from
    `get_all_breakpoints` at onboarding.
12. Images come from public URLs (`upload_image_by_url`) or the existing asset
    library. Every image gets alt text. Content the brief marks `missing` is
    inserted as a visible `TODO:` placeholder and listed in the report.
    **Prefer an asset already in the library: uploading one makes it public
    immediately** (rule 19), which is the only thing this skill does that puts
    a file on the internet.
13. One H1 per page, no skipped heading levels, internal links by page ID,
    external links well-formed.
14. No site scripts, no page scripts, and no custom code beyond what the
    approved outline lists. Tracking stays in whatever site-wide container the
    site already uses.
15. Credentials never reach a file. The Bridge App launch link returned by a
    failed `designer_tool` call carries an app token, is tied to the connected
    Webflow account, and differs per operator; use it inside the run and never
    write it (or any token, cookie, or authorization header) to a brief, a
    manifest, a run record, a catalog entry, a document, or a commit. When a
    procedure needs the link, say "read it from the error response" instead of
    pasting it.
16. Primary locale only. Localization needs are reported, not written.
17. Verify by reading back structure, props, page metadata, and the pre/post
    inventory diff (the guard). Report what will ship at the next publish:
    components, styles, and variables created on main by the run. Report
    separately, and first, what is **already** public: the assets the run
    uploaded (rule 19).
18. Interactions, custom fonts from Google or Adobe, and role or access changes
    are unsupported through MCP. List them as manual Designer work; never
    approximate them with scripts or embeds.
19. **Public exposure is its own category, and only one write in this skill
    crosses it.** Using this skill must not put anything on the public
    internet. Four categories, and the guarantee for each:

    - **The draft page.** Created with `draft: true` (rule 7) and confirmed by
      readback. Draft pages are excluded from publishing, so the page is not
      public and does not become public at the next site publish either. A
      human turns the flag off when they are ready.
    - **New components, styles, and variables.** Site-level, so they are not
      public now but **do go live at the next site publish**, whoever publishes
      and for whatever reason, even though the page itself stays a draft. Every
      run lists them as the ships-at-next-publish list (rule 17).
    - **Uploaded assets. This is the exception: uploading an asset makes it
      public immediately.** `asset_tool > upload_image_by_url` puts the file in
      the site's asset library, and Webflow serves library assets from a public
      CDN URL **from the moment of upload** — before any publish, and whether
      or not the draft page is ever published. Anyone who has the URL can fetch
      it without logging in. Prefer an asset already in the library; ask the
      submitter before uploading anything new; never upload something
      confidential, unreleased, or under embargo in order to get a draft built.
      Deleting the asset later does not un-serve a URL someone already has.
      Every run lists uploaded assets in the report as their own **already
      public** line, separate from and more urgent than the
      ships-at-next-publish list.
    - **Branch staging publish.** Only on explicit request in that turn, only
      in a run that uses branch mode, only to staging, never to production
      (rule 8). Measured, not assumed: an anonymous request to a Webflow branch
      staging URL redirects to the Webflow login and returns HTTP 403, so
      staging is gated behind a Webflow login rather than open to the internet.

    Two more, for completeness, because they are where a future contributor
    would be tempted to put data:

    - **Agent Instructions**, the store this toolkit writes the rulebook,
      catalog, candidates, and run records to, are gated behind the
      `agent_instructions:read` scope, are delivered to authorized MCP clients
      as site metadata, have no publish path, and never appear in page content.
      That is strong evidence they are not public. It is not a vendor
      statement, and none was found, so it is not a guarantee:
      `flows/onboard.md` runs a one-time verification the first time the store
      is enabled on a site. Until that has run there, treat the store as
      probably private and unverified, and keep secrets out of it (rule 15
      already keeps credentials out of every file).
    - **CMS items are never a store for this toolkit. Standing non-goal.** The
      Data API models CMS items with staged and live states and publish and
      unpublish events: they are publish-shaped by design, so a catalog entry,
      brief, candidate, or run record kept in a collection would sit one
      publish away from the public internet. Do not move the store there, and
      do not add a "just for drafts" exception.
