# Flow: maintain

Maintainer flow. It is how the template library grows and how shared things
change on purpose. Six paths; run the one the user asked for.

It is written for Claude Code with repo access, where every path ends in a pull
request. On a site onboarded **without a repository** (`flows/onboard.md`
step 0, "Store: Webflow") there is no PR to open and no repo file to edit: read
"Maintaining without a repository" at the end of this file first, then run the
path you need with the substitutions it lists.

References: `../references/catalog/README.md` (entry format, status, component
metadata convention), `../references/catalog/candidates/README.md` (promotion),
`../references/rules.md`, `../references/site-inventory.md` (the local capture
from onboarding), `../references/webflow-conventions.md`,
`../references/unsupported.md` (the Agent Instructions scope row). Scripts:
`../scripts/catalog_lint.py`. Follow-up flow: `sync.md` after any catalog
change. `<prefix>` throughout is the instruction prefix from the conventions
file (default `page-templates`).

Preflight for every path: `webflow_guide_tool` once per conversation; read the
family entry involved; resolve the components involved **by name**, batched into
one `data_component_tool > get_component` call (add `group` when a name needs
it) or one group-filtered `query_components`, because the catalog names
components and does not carry their ids (`catalog/README.md`, "Components are
named"). Add `includeInstanceCount` only on the paths below that need the blast
radius; `includeProps` and `includeVariants` stay off unless the path says
otherwise (rule 10). Pace element reads (`get_all_elements`, `query_elements`)
as `webflow-conventions.md` records for this site. If the Agent Instructions
store returns **403** on `search_instructions`, every step below that reads or
writes an instruction is replaced by its local counterpart (files under
`../references/`); say so once and continue.

## Confirm a proposed family

Entries written by onboarding (or the create-family path) carry
`status: proposed` at version `0.1.0`. Until this path runs, every build that
uses the family says the family is unconfirmed.

1. Walk the onboarding decisions for the family, at most three questions per
   turn, and record every answer in the entry: keep, merge, rename, or drop the
   family; template model; master page (id and leaf slug); allowed folders with
   IDs; slug and title conventions; SEO and Open Graph defaults; default JSON-LD
   schema type (onboarding's proposal is a judgment call the maintainer must
   accept or replace); isolation default (`branch` only if
   `webflow-conventions.md` records branching as available); who publishes.
   Write the answers in the entry's `## Decisions` section (one line each, with
   who took them and when; `catalog/README.md`); a decision still open stays
   there as a visible `TODO`, never as a guess.
2. Re-check what the entry names with the cheap reads: `get_page_metadata` on
   the master page (slug and parent folder must match), and one batched by-name
   lookup for every component name in the outline and shell tables
   (`get_component` by `name`, or one `query_components` filtered to the
   family's group). A name that resolves to **zero** components, or to **more
   than one**, is fixed in the entry now, never later: zero means the component
   was renamed or deleted, more than one means the row needs a `group` to
   disambiguate. Both are what blocks a family at build time (`flows/build.md`
   Phase 3), so a maintainer clears them here.
   Read the live values against the entry, not against the allowed folders:
   "parent folder must match" means the parent named by `masterPagePath`, and a
   native page-template master may sit at the site root with a generated slug
   and no parent. The component tool needs a `pageId` argument even for a
   site-wide read; pass the master's id. `list_pages` can exceed the chat token
   limit on a large site: save each page of results to a file and check folder
   ids, slug collisions, and whether a master's branch page is still listed
   locally. Batch the `get_page_metadata` reads for every family into one call.
3. Resolve every `candidate:<slug>` placeholder row. The linter rejects
   placeholders once the entry is `promoted`. Either replace the placeholder
   with the component a build run created and this flow promoted (path "Promote
   a candidate"), or replace it with an existing component that serves in the
   meantime, mark the row `optional`, and record the missing piece under "Do and
   don't" so the first run that builds it is handled as a New section. Dropping
   the row is also allowed when the section was speculative.
4. Set `status: promoted` and `version: 1.0.0`. When the schema decision names
   more than one type, the primary goes in `schemaType` and the rest in
   `additionalSchemaTypes`. Remove "proposed" wording from Purpose, SEO
   defaults, and JSON-LD sections (or turn it into the decision taken). Add the
   changelog line `1.0.0 (<date>): confirmed by <maintainer>; <decisions changed
   from the proposal>`, and name the live reconciliation result in it.
5. Update the templates table in `../references/webflow-conventions.md`
   (confidence column becomes "confirmed") and, if a family was dropped or
   merged, its row and its `catalog/<slug>.md` (set `status: deprecated`, bump
   the patch version, start Purpose with the deprecation note and where the
   requests route instead, add the changelog line, keep the file for history).
   Fill the site-wide sections the decisions settle (slug and title, SEO and
   Open Graph, schema defaults, isolation default, publish policy) and record
   every probe made in this path, with its timestamp, in the conventions file's
   reconciliation log.
6. `python3 scripts/catalog_lint.py references/catalog --sync-state
   references/sync-state.json`. Fix every error.
7. Open the PR. After merge, run `sync.md` (push). Once the entry is
   `promoted`, `flows/build.md` Phase 3 and Phase 7 stop adding the
   "unconfirmed family" caveat; nothing else in the build flow changes.

No component metadata is stamped in this path: the components a proposed family
lists are pre-existing library components, and the toolkit does not rewrite
their `group` or `description` (see `catalog/README.md`, "Component metadata
convention in Webflow").

## Promote a candidate

A candidate is a component, variant, or variable created by a build run and
recorded in `<prefix>/candidates/<slug>.md` (pulled into
`../references/catalog/candidates/` by `sync.md`). When the run could not write
to the instruction store (403), the candidate record arrives as the local file
the run handed to the maintainer with its report; copy it into
`../references/catalog/candidates/` first.

1. Review it: in the Designer, or by `element_snapshot_tool` on an instance when
   the Designer is open. Check responsive behavior at every breakpoint the
   conventions file lists.
2. `get_component` by name with `includeInstanceCount` for the component: note
   where it is used. The count is the reason the flag is on here.
3. Fix naming, `group`, and `description` if needed. Names follow the site
   naming system with the family prefix. `group` = family slug. This is allowed
   here because the component was created by a run; pre-existing components are
   never regrouped.
4. Add it to the family entry: section outline row (component **name**, owner
   `self`, required or optional, props exposed, variants, slot names, content
   guidance, image sizes; `Class path` stays empty, it is for `loose` rows) or
   the variants column of an existing row. If the entry carried a
   `candidate:<slug>` placeholder for it, replace the placeholder with the
   component's name, never with its id. Add usage guidance to "Do and don't" if
   the candidate needs it.
5. Bump the family version: patch for guidance-only edits, minor for a new
   variant or prop, major for a new required section or a changed master. Add a
   changelog line to the entry.
6. `python3 scripts/catalog_lint.py references/catalog --sync-state
   references/sync-state.json`.
7. Open the PR. After merge, run `sync.md`: it pushes the entry and rewrites
   this component's description to `<family>@<version> | promoted` (the rewrite
   applies to run-created components only).

Rejected candidates: delete from Webflow (`unregister_component`, with the
user's explicit confirmation in that turn) **only if the instance count is
zero**. Otherwise leave the component, set its description to
`<family>@<version> | rejected`, and add a note to the family entry's "Do and
don't" so no run picks it up again.

## Edit a master or shared component

Impact analysis first, always:

1. `get_all_components` with `includeInstanceCount`, or `get_component` by name
   with `includeInstanceCount`, for the component. This is one of the two places
   the include flags are genuinely needed (the other is the onboarding census);
   the instance count is the blast radius (rule 10).
2. Pages that use it: `data_element_tool > query_elements` with a
   `component_filter`, per page from the inventory, or across the master and
   example pages of every family that lists the component. Serialized, one page
   per call, at the site's pacing.
3. Present the blast radius: instance count, pages, families.

Then, in order of preference:

- **Prefer a new variant** (`data_component_variants_tool > create_variant`,
  `set_variant_styles`) or a new prop. Existing pages keep their look.
- **Base-variant edits** (`set_variant_styles` on the base variant, or
  `data_style_tool > update_style` on a class the component uses) require the
  user's explicit confirmation in that turn, naming the pages that will change.
  Record the edit in the family changelog with the reason and the date. This is
  the only flow where `update_style` on a pre-existing class is allowed.
- Master page edits: same analysis; every future duplicate-master or hybrid page
  inherits the change. Re-snapshot the reference image afterwards
  (`element_snapshot_tool`) and update `referenceImage` in the entry.

Bump the family version (major for base-variant or master changes), lint, PR,
sync.

## Create a family

From an existing page or from a run's outline (the "new family" path in
`build.md` Phase 3):

1. Confirm the exemplar page (id, slug) or the outline sections.
2. Choose the template model with the user: master exists and body sections are
   components → hybrid; master exists and body is loose → duplicate-master; no
   master → component-recipe. Record the reasoning.
3. Confirm allowed folders (pre-create with `designer_tool >
   create_page_folder` if needed and the Designer is open), slug pattern, SEO
   and Open Graph defaults, schema type, isolation default (only if branching is
   available per `webflow-conventions.md`).
4. Write `../references/catalog/<family>.md` in the format from
   `catalog/README.md`. Component **names** exactly as the component tool
   returns them, never from memory and never as ids; check the name is unique on
   the site before writing it (`query_components` on the name), because a name
   that matches two components blocks the family at build time. If the
   maintainer took every decision in this conversation, write it at `1.0.0` with
   `status: promoted`; if anything is left open, write it at `0.1.0` with
   `status: proposed` and finish through "Confirm a proposed family". Stamp
   `group` and `description` only on components a run created for this family
   (confirm first); pre-existing components keep theirs.
5. Add the family to the templates table in `webflow-conventions.md`.
6. Lint, PR, sync. Tell the waiting build (if any) that the family is available.

## Refresh inventory

1. Re-run the read-only inventory from `onboard.md` step 3, including the
   measurements: component-name uniqueness, branching, breakpoints, token
   scopes, and the rate-limit probes. A site that has grown can cross the
   request-budget threshold it was previously under; that changes the pacing
   rule and possibly the capability table, so re-measure rather than assume the
   old answers hold.
2. Diff against the cached `../references/site-inventory.md`: renamed or deleted
   components (a rename is what breaks a name-keyed catalog row, so check names
   first), **newly duplicated component names**, deleted or moved master pages,
   new components with no family, changed naming patterns, changed branching
   answer, changed breakpoint list, changed Agent Instructions answer (a 403
   that turned into a 200 means the sync flow can finally install the rules; say
   so), and changed rate-limit behaviour.
3. Report drift and, for each catalog entry affected, propose the fix (update
   the master id, mark the section optional, block the family).
4. Write the new `site-inventory.json` and render `site-inventory.md` with a new
   timestamp and the new sha256 in the header. Both stay local: they are
   gitignored. Update every MEASURE row of `webflow-conventions.md` whose answer
   changed, with the new date, and append the probes to the reconciliation log.
   If the capture shows two components sharing a name, say so loudly: name
   keying depends on uniqueness, and every family that names the duplicate is
   blocked until a maintainer renames one or the entry disambiguates by group.
   Lint. PR.

## Housekeeping

1. `search_instructions` under `<prefix>/runs/` and `<prefix>/candidates/`. On
   **403**, there is nothing remote to prune: the run records and candidate
   files exist only as the local files the runs produced. Skip steps 2 and 4 and
   go to step 3 with those files.
2. Prune runs older than 90 days and candidates already promoted or rejected
   (`delete_instruction`), listing each path and asking once for the batch. Run
   records with `status: open` are never pruned without asking about the run
   itself (`resume.md`).
3. Archive manifests worth keeping (every run that built a page, every pruned
   run) into `../references/runs/` as `<yyyy-mm-dd>-<slug>.manifest.json` with
   the brief beside it as `<yyyy-mm-dd>-<slug>.brief.json`. The folder's README
   says what lands there. Candidate records already promoted are removed from
   `../references/catalog/candidates/` at the same time (the family entry now
   covers them).
4. Update `sync-state.json` so pruned paths disappear from `paths`; leave it
   untouched when the store returned 403.
5. Open the PR with the archived files and the state change.

## Maintaining without a repository

On a site whose catalog lives in Webflow Agent Instructions and nowhere else,
every path above still applies; only the mechanics change.

**Substitutions.** Wherever a path says:

| It says | Do this instead |
| --- | --- |
| read `../references/catalog/<family>.md` | `read_instruction` on `<prefix>/catalog/<family>.md` (`resolve_references: false`) |
| edit the entry and lint it | edit the body in the conversation; run `catalog_lint.py` if code execution is available, otherwise walk the checklist in `catalog/README.md` by hand and say the linter did not run |
| open the PR | show the whole new body, ask for an explicit yes, then `update_instruction` on that one path |
| after merge, run `sync.md` | nothing: the write above *is* the sync. Update the index at `<prefix>/SKILL.md` in the same way, and the sync-state rows at the end of `<prefix>/conventions.md` |
| `../references/site-inventory.md` (Refresh inventory) | re-run `onboard.md` step 3 in the conversation and compare against what the conventions file records; there is no cached capture to diff against |
| archive to `../references/runs/` (Housekeeping) | hand the run record back to the user as a download before deleting it; that download is the archive |

**Promotion, in conversation.** Confirming a proposed family or promoting a
candidate is the same walk of the same decisions. What changes is the ending:

1. Read the entry from the store and show the user what will change, in full.
   A diff nobody reads is not a review; a body the user reads is.
2. Take the decisions one turn at a time, at most three questions per turn, and
   write each answer into the entry's `## Decisions` section with who took it
   and when. With no git log, that section is the only record of why.
3. Set `status: promoted`, `version: 1.0.0`, add the changelog line, and flip
   the instruction from draft to non-draft (`update_instruction` with
   `isDraft: false`) in the same write. A promoted entry is not a draft; a
   proposed one is.
4. Update `<prefix>/SKILL.md`: the family moves from the proposed table to the
   promoted one.
5. Hand back a fresh download bundle (`onboard.md` step 9). It is the only
   history of what the entry said before today, so say that when handing it
   over.

**Pruning, in conversation.** Same as Housekeeping above, with one difference:
before `delete_instruction` on anything, hand the user the body as a download
and get an explicit yes for that path. A deleted instruction on a site with no
repository is unrecoverable.

**What is given up, and say it every time.** No pull request means no second
reader, no diff, no revert, and no history beyond the entry's own `## Decisions`
and changelog sections. The compensations are the ones onboarding named: an
explicit confirmation per write, proposed families kept as drafts, and the
download bundle as the backup. If the team later gets a repository, adopt it by
pulling the store into it (`sync.md`, "Sites onboarded without a repository")
rather than starting a new catalog.
