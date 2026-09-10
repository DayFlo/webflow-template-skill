# Flow: resume

Resume or clean up an interrupted build run. Entered from `build.md` Phase 0
step 4 (an `open` manifest exists for the slug) or when the user asks to finish
or undo a run. Works on every surface; the manifest is the only state it needs.

References: `../references/manifest-schema.md`, `../references/rules.md`,
`../references/webflow-conventions.md` (the instruction prefix, written
`<prefix>` below; default `page-templates`). Scripts:
`../scripts/manifest.py` (`summarize`, `append`, `set`, `ships`).

## 1. Locate the manifest

- Webflow: `data_agent_instructions_tool > search_instructions` under
  `<prefix>/runs/` for the slug, then `read_instruction`. The manifest JSON is
  in the record's fenced block. A **403 `forbidden`** means the store is not
  readable for this account; it is not an error to report as a failure. Skip to
  the local copy and, at the end, state that the run record could not be updated
  in Webflow.
- Locally (Claude Code, Codex): the file the run wrote, if the user has it, or a
  download the user re-attaches on Claude.ai. When the store is unavailable, the
  local file is the only record; ask for it by name (`<yyyy-mm-dd>-<slug>`
  manifest and its brief). On Claude Code a live run writes them to
  `references/runs/<yyyy-mm-dd>-<slug>.manifest.json` and `.brief.json`, so look
  there first. The manifest under `assets/examples/` is the worked example
  (every step `skipped`, `created` empty); it is not a live run, never offer to
  resume or clean it up, and the tests depend on it staying as it is.

If both exist and differ, the one with more steps wins; say so.

## 2. Summarize and offer the choice

`python3 scripts/manifest.py summarize manifest.json` (or the manual summary in
`manifest-schema.md`). Show: run id, slug, family and version, isolation mode,
started at, last step and its status, created resources, guard verdict if any.
Then ask one question: **resume** or **clean up**?

## 3. Resume

1. Reload the brief from the run record (the same instruction holds it) and
   confirm with the user that the approved outline still stands. If the design
   or the answers changed, this is a new run, not a resume.
2. Reconcile the created resources against the live site: `get_page_metadata`
   for `created.pageId`, `get_all_components` for `created.componentIds`. A
   resource in the manifest that no longer exists is reported and the step that
   created it is re-run.
3. Continue `build.md` Phase 5 from the first step whose manifest entry is
   missing or `failed`. **Skip completed steps**; do not re-create a page or a
   component that reads back correctly. Every new write is appended to the
   manifest as usual, at the pacing `webflow-conventions.md` records for this
   site.
4. Run Phase 6 (verify) in full, even for steps completed before the
   interruption; the guard compares against the original `preSnapshot`.
5. Report as in Phase 7, noting that the run was resumed and from which step.

## 4. Clean up

Cleanup deletes **only** resources listed under `created` in this manifest.
Nothing else on the site is a candidate, whatever the user believes was made by
the run. The order limits collateral damage:

1. List what will be removed, with instance counts for components
   (`get_all_components` with `includeInstanceCount`). A component with
   instances outside the run's page is **not** removed; it is reported.
2. Ask before **each** destructive call, one per turn if the user prefers:
   - components with zero instances outside the page:
     `data_component_tool > unregister_component`;
   - the page: `data_pages_tool > delete_page` (draft, unpublished);
   - the branch, if any: the branch deletion tool from `data_pages_tool`;
     verify it exists before promising it, and hand off to the Designer if it
     does not;
   - assets uploaded by the run: they are **already public** and have been
     since the moment of upload (rule 19), so say so and ask. Deleting one
     (in the Designer's Assets panel; this skill does not delete assets) stops
     the library serving it going forward but does not un-serve a URL somebody
     already has, so removal is damage limitation,
     not a fix; leave them if the user prefers;
   - styles and variables created by the run: report them for manual removal in
     the Designer if unused; the MCP delete tools for these are not used by this
     skill (`delete_variable` is on the never list).
3. Append each deletion to the manifest, then set `status: cleaned`
   (`manifest.py set manifest.json --status cleaned`) and update the run record
   in Webflow (`update_instruction`; skipped with a note when the store returned
   403, in which case hand the updated file back to the user).
4. Report what was removed, what was kept and why, and the leftover manual
   items.

## 5. Never

`publish_site`, `publish_branch`, deleting anything absent from `created`,
`update_style` on a pre-existing class, or resuming a run whose brief no longer
matches what the user wants built.
