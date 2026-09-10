# Run manifest schema

The run manifest is the record of everything a build run wrote to Webflow. It
exists so an interrupted run can be resumed or cleaned up, so the guard can
compare before and after, and so the report can say what ships at the next
publish. Rule 9: every write is appended **before** the next write.

Storage: a Webflow Agent Instruction at `<prefix>/runs/<yyyy-mm-dd>-<slug>.md`
(the instruction prefix is set once in `webflow-conventions.md`, "Toolkit
settings"; the default is `page-templates`)
with `isDraft: true`, body starting with "This is a run record, not guidance."
followed by the brief and the manifest in fenced JSON blocks; and the same JSON
offered to the user as a download. Script: `../scripts/manifest.py`.

## Fields

| Field | Type | Notes |
| --- | --- | --- |
| `runId` | string | `<yyyy-mm-dd>-<slug>` by default |
| `slug` | string | Page slug |
| `startedAt` | string (ISO 8601) | |
| `surface` | enum(`claude-ai`, `claude-code`, `codex`) | Where the run happened |
| `site` | object | `id`, `shortName` |
| `family`, `familyVersion` | string | From the brief |
| `templateModel` | enum | From the brief |
| `isolationMode` | enum(`draft-main`, `branch`) | From the brief |
| `briefHash` | string | `sha256:<hex>` of the approved brief (see `brief-schema.md`) |
| `resolvedComponents` | object | Optional. The `<component name>: <component id>` map `flows/build.md` Phase 3 resolved for the chosen family. This is the **only** place a build writes a component id down: the catalog and the brief name components, and the manifest is a run record (kept with the run, archived under `references/runs/`), not guidance. Absent on a run that reached no further than template selection; a resumed run re-resolves rather than trusting it |
| `steps` | array<object> | One per Webflow write; see below |
| `created` | object | `pageId` (string \| null), `branchId` (string \| null), `componentIds`, `styleNames`, `variableIds`, `assetIds`, `instructionPaths` (arrays of strings) |
| `preSnapshotHash`, `postSnapshotHash` | string \| null | `sha256:<hex>` of the snapshot JSON used by the guard (shape below) |
| `guardVerdict` | object \| null | The output of `diff_inventory.py` |
| `normativeChecklist` | array<object> \| null | Optional. The Phase 6 checklist (`flows/build.md`) as filled: one entry per row; see below. `null` until Phase 6 records it |
| `acceptedDeviations` | array<string> | `kind:key` entries the user accepted after a failed guard |
| `publishActions` | array<object> | Must stay empty except explicit staging `publish_branch` in branch mode |
| `status` | enum(`open`, `verified`, `failed`, `cleaned`) | |

### `steps[]`

| Field | Type | Notes |
| --- | --- | --- |
| `seq` | int | 1-based, increasing |
| `at` | string (ISO 8601) | |
| `tool` | string | e.g. `data_pages_tool` |
| `action` | string | e.g. `create_page` |
| `ids` | object | IDs created or touched: `pageId`, `branchId`, `componentIds`, `styleNames`, `variableIds`, `assetIds`, `instructionPaths`, or anything else useful (`elementId`) |
| `status` | enum(`ok`, `failed`, `skipped`) | `skipped` is used by resume for steps already done |
| `note` | string | Short free text |

### `normativeChecklist[]`

The Phase 6 table, recorded so Phase 7 and a resumed run print the same rows.
All six rows, in the Phase 6 order; the script sorts them into it.

| Field | Type | Notes |
| --- | --- | --- |
| `id` | enum(`outline-match`, `family-rules`, `cta`, `seo`, `guard`, `tracking`) | Each id exactly once |
| `verdict` | enum(`pass`, `warn`, `fail`, `handoff`) | `tracking` may not be `fail`: a missing UTM key or custom attribute is a HANDOFF, never a failed run (`references/rules.md` rule 14) |
| `evidence` | string | What was read — the call, the node or field, the value returned. Required and non-empty |
| `handoff` | string | Required on a `handoff` verdict, the Designer work in `unsupported.md` wording; omitted otherwise |

A `fail` row does not by itself set `status`: the guard sets `failed` as it
always did, and a `tracking` HANDOFF leaves the status alone.

## Script commands

```
manifest.py create --slug S --surface claude-ai --site-id ID [--site-short-name N]
    --family F --family-version V --template-model M --isolation-mode I
    (--brief brief.json | --brief-hash sha256:...) [--run-id R] [--started-at ISO] [-o manifest.json]
manifest.py append manifest.json --tool T --action A [--status ok|failed|skipped]
    [--ids '{"pageId": "..."}'] [--note TEXT] [--at ISO]
manifest.py set manifest.json [--status S] [--guard-verdict verdict.json]
    [--pre-snapshot-hash H] [--post-snapshot-hash H] [--accept-deviation kind:key]
    [--normative-checklist checklist.json]
manifest.py summarize manifest.json
manifest.py ships manifest.json
```

`append` merges `ids` into `created` (scalars `pageId` and `branchId` are set;
list keys are extended without duplicates) and records `publish_branch` under
`publishActions`, but only for steps that ran: status `ok` or `failed`. A
`skipped` step (a dry run, or a step already completed before an interruption
whose ids entered `created` when it originally ran) records nothing beyond the
step itself, so `created` never lists a resource that this run did not make
and a dry-run manifest has an empty `created`. A failed step still merges,
because a create that errored may have left a resource behind; cleanup
reconciles `created` against the live site before deleting. An `append` with
action `publish_site` is recorded (the manifest must stay truthful) and the
script exits 1 with a rule 8 violation whatever the status.

## Snapshot shape (the guard's input)

`diff_inventory.py pre.json post.json` compares two snapshots of the same
shape. The build takes the pre-snapshot in Phase 5 step 2 and the
post-snapshot in Phase 6 with the same scope, then records
`sha256:<hex>` of each file as `preSnapshotHash` and `postSnapshotHash`. Scope:
every style, component, and variable the run may touch (the family's
components with props and variants, the classes the catalog rows name, the
variables in the token reconciliation table) plus, cheaply, the full
component list without props. A trimmed worked example is
`scripts/tests/fixtures/example/pre.snapshot.json` (with `post.pass.json` and
`post.fail.json` beside it, which the guard tests diff against each other).

```json
{
  "capturedAt": "<ISO 8601>",
  "siteId": "<site_id>",
  "scope": {"styles": "<how the classes were chosen>", "components": "...", "variables": "..."},
  "styles": {
    "<class name>": {"properties": {"<css property>": "<value>", "...": "..."}},
    "<class name>": "names-only"
  },
  "components": {
    "<component id>": {
      "name": "<name>", "group": "<Webflow group>", "description": "<description or null>",
      "props": {"<prop id>": {"name": "<prop name>", "type": "<prop type>", "group": "<prop group or null>"}},
      "variants": {"<variant name>": "present"}
    }
  },
  "variables": {
    "<variable id>": {"name": "<name>", "type": "<type>", "cssName": "<css name>", "collection": "<collection id>",
                      "value": "<value or alias object>", "modeValues": [{"modeId": "<mode>", "value": "..."}]}
  }
}
```

`scripts/build_snapshot.py` performs this mapping from the saved tool results
(`--components`, `--variables`, `--styles --classes ...`) and prints the file's
sha256 for the manifest; the rules it applies are the ones below.

How real tool output maps onto it:

- **styles**: `data_style_tool > get_style` (or `query_styles` with properties)
  per class; the value is an object holding the properties as returned, per
  breakpoint if the tool returns them. When only names were read (onboarding
  sampled names with `query_styles`), store the string `names-only`; the guard
  then detects removal and any later change of representation, not property
  edits. A live build must read properties for the classes it names.
- **components**: `get_all_components` with `includeProps` and
  `includeVariants`. Convert the props list to a map keyed by prop **id** (prop
  names repeat, e.g. `Col 1/Slot` twice on `Two column layout section`)
  and the variants list to a map keyed by variant name; without
  `set_variant_styles` output the value is `present`. For the cheap full list
  (no props), store name, group, and description only. Do **not** copy
  `instanceCount` or `propCount` into the record; the guard ignores those
  fields when present, because inserting an instance is not an edit.
- **variables**: `get_variables` per collection; keep `name`, `type`,
  `cssName`, `value`, `modeValues`, and the collection id.

Verdict semantics: a key present in `pre` and absent in `post` is `removed`
(fails); a key only in `post` is `created` (allowed, and reported as
ships-at-next-publish); a key in both whose canonical JSON differs is
`changedPreExisting` (fails). Inside a component, `props` and `variants` are
compared entry by entry, so a new variant or prop is `created` while an edit
to an existing one fails. `--accept kind:key` records a deliberate deviation.

## Manual procedures (no scripts)

**Create.** Write the JSON skeleton above with `steps: []`, empty `created`
lists, `status: "open"`, and the brief hash computed as in `brief-schema.md`
(if hashing is impossible by hand, record `"briefHash": "unavailable"` and say
so in the report).

**Append.** After each Webflow write, add a step object with the next `seq`,
the current time, tool, action, the IDs the tool returned, and `ok` or
`failed`. Copy any new IDs into `created`. Then update the Webflow instruction
(`update_instruction` on the run record) with the new JSON. Do this before the
next write, even when it feels slow.

**Summarize.** Report: run id, slug, family@version, model, isolation, started
at, number of steps by status, the last step (seq, action, status), each
non-empty `created` list with counts, guard verdict (`pass`, `fail`, or
`not run`), publish actions (must be none, or the explicit staging publish),
current status.

**Ships at next publish.** When `isolationMode` is `draft-main`: list
`created.componentIds`, `created.styleNames`, `created.variableIds`. These go
live site-wide at the next publish even though the page is a draft. When
`isolationMode` is `branch`: the list is empty and the report says the changes
are isolated on the branch until merge.

**Already public.** `created.assetIds`, in **both** isolation modes. Uploaded
assets are deliberately not on the ships list: they do not wait for a publish.
Webflow serves library assets from a public CDN URL from the moment of upload,
before any publish and whether or not the page is ever published, and the asset
library is site-level so a branch does not isolate it
(`references/rules.md` rule 19). The report prints this list first, ahead of
ships-at-next-publish; when it is empty, say so ("every image came from the
existing asset library") rather than omitting the line.
