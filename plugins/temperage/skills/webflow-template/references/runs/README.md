# Run archive

Manifests and briefs of build runs that a maintainer chose to keep, archived by
`flows/maintain.md` (Housekeeping) or pulled from Webflow by `flows/sync.md`
(pull). Nothing in this folder is read by a build run; the live record of an
open run is the Webflow instruction `<prefix>/runs/<yyyy-mm-dd>-<slug>.md`
(default prefix `page-templates`; see `../webflow-conventions.md`, "Toolkit
settings") or, when the instruction store is not writable (HTTP 403), the local
file the run handed to the user.

This folder ships empty. It fills up as runs happen.

On Claude Code and Codex a live build also writes its working files here while
the run is `open` (`<yyyy-mm-dd>-<slug>.brief.json`, `.manifest.json`,
`.outline.html`, `.pre.snapshot.json`, later `.post.snapshot.json` and
`.guard.verdict.json`), which matters most when the Webflow instruction store
returns 403 for the connector user and the local files are the only record. The
build flow's Phase 0 step 4 checks this folder for an `open` manifest with the
same slug before starting a duplicate build.

What lands here:

- `<yyyy-mm-dd>-<slug>.manifest.json`: the run manifest
  (`../manifest-schema.md`), status `verified`, `failed`, or `cleaned`. Open
  runs are not archived; resume or clean them up first.
- `<yyyy-mm-dd>-<slug>.brief.json`: the approved brief the manifest's
  `briefHash` refers to.
- `<yyyy-mm-dd>-<slug>.md`: a run record pulled verbatim from Webflow by the
  sync flow, when the instruction store is readable.

Why keep them: the `created.componentIds` lists are how the sync flow tells
run-created components (whose description it may rewrite) from the pre-existing
library (which it never touches), and the manifests are the audit trail for
what shipped at each publish.

Snapshots (`*.pre.snapshot.json`, `*.post.snapshot.json`) are bulk captures of
the site and are gitignored; regenerate them with `scripts/build_snapshot.py`.

The worked example under `../../assets/examples/` is **not** a run: every step
in its manifest is `skipped`, `created` is empty, and it exists to show the
manifest shape. Never offer to resume or clean it up; the tests depend on it
staying as it is.
