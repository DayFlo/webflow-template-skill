# Candidates

Reusable additions made by build runs, waiting for a maintainer's review. A
build run that creates a **New** section (a new component), a new variant, or a
new variable writes one record per addition to Webflow Agent Instructions at
`<prefix>/candidates/<slug>.md` with `isDraft: true` (default prefix
`page-templates`; see `../../webflow-conventions.md`, "Toolkit settings").
`flows/sync.md` (pull) copies those records into this folder. When the
instruction store is not writable (HTTP 403), the run hands the record to the
user as a local file with its report, and the maintainer copies it here by hand
before promotion. Nothing in this folder is used by a build run; runs read
promoted entries only.

This folder ships empty. It fills up as runs happen.

## Record format

```markdown
---
slug: orbit-setup-steps
runId: 2026-01-05-orbit
family: product-landing
familyVersion: 1.1.0
kind: component
componentId: 1111aaaa-0000-4000-8000-000000000010
componentName: Setup steps section
createdAt: 2026-01-05T18:40:00Z
status: candidate
---
This is a run record, not guidance.

## What it is
One paragraph: what the section does and why the family did not already cover it.

## Props and slots
| Kind | Name | Type | Notes |

## Where it is used
| Page ID | Slug |

## Snapshot
Asset name or "pending (Designer was closed)".

## Notes for review
Naming, responsive behavior observed, anything the run had to work around.
```

`kind` is `component`, `variant` (then `componentId` and `variantName`), or
`variable` (then `variableId` and `collection`). The file name is the slug. The
ids in the skeleton above are synthetic; a real record carries whatever Webflow
returned.

A candidate record is a **run record**, so it may carry the id Webflow returned
for the thing the run created; that is the same exemption the run manifest has
(`../README.md`, "Components are named"). What reaches the family entry at
promotion is the `componentName`, never the `componentId`: the catalog names
components and `catalog_lint.py` rejects an id in a component column.

## Promotion

1. A maintainer runs `flows/maintain.md` (Promote a candidate): reviews the
   component (Designer or snapshot), checks instance count, fixes naming and
   metadata, adds it to the family entry, bumps the version, lints, opens a PR.
2. After merge, `flows/sync.md` pushes the family entry and rewrites the
   component `description` to `<family>@<version> | promoted`.
3. The candidate record is deleted from Webflow and from this folder by the
   maintain flow's Housekeeping path (it is now covered by the family entry).

## Rejection

Zero instances: the component is unregistered (with confirmation) and the
record deleted. Instances exist: the component stays, `description` becomes
`<family>@<version> | rejected`, the family entry's "Do and don't" gets a line
so no run picks it again, and the record is deleted at the next housekeeping.
