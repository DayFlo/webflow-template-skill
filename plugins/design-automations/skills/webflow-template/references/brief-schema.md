# Brief schema

The brief is the single object the outline is rendered from and the build is
executed from. What the user approved is what gets built. Format: JSON.
Example: `../assets/brief.example.json` (it passes `validate_brief.py`).
Validator: `python3 scripts/validate_brief.py brief.json` (add
`--require-approval` before Phase 5 to insist on `approvedAt`; add
`--branching unavailable` on a site without branching so a `branch` brief is
rejected).

## Fields

Type notation: `string`, `int`, `bool`, `object`, `array<...>`, `enum(...)`,
`| null`. "Required" means the validator fails without it.

### Top level

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `site` | object | yes | `id` (string, required), `shortName` (string, optional; used in Designer links) |
| `family` | string | yes | Family slug, lowercase kebab-case, matches a catalog entry |
| `familyVersion` | string | yes | Semver `MAJOR.MINOR.PATCH` of the entry used |
| `templateModel` | enum(`duplicate-master`, `component-recipe`, `hybrid`) | yes | Family default or the per-run override |
| `isolationMode` | enum(`draft-main`, `branch`) | yes | `branch` only when `webflow-conventions.md` says branching is available |
| `sources` | array<object> | no (default `[]`) | Each: `type` (string, e.g. `claude-design-html`, `claude-design-zip`, `dc-html`, `html`, `figma-export`, `screenshot`, `pdf`, `link`, `copy-doc`), `location` (string), `observed` (array<string>), `assumed` (array<string>) |
| `answers` | object | no | Keyed by interview topic: `purpose`, `primaryAction`, `pageIdentity`, `seo`, `shell`, `sections`, `contentStatus`, `images`, `forms`, `responsive`, `localization`, `schema`, `launchOwner`, plus `usedFamilyDefaults` (bool) |
| `page` | object | yes | See below |
| `sections` | array<object> | yes, non-empty | See below |
| `tokens` | object | no | `substitutions`: array of `{observed, token, match: enum(exact, near)}`; `unresolved`: array of `{observed, note}` |
| `unsupported` | array<object> | no | Each `{item, handoff}`; see `unsupported.md` |
| `decisions` | array<object> | no | Each `{id, question, status: enum(open, resolved), resolution}` |
| `approvedAt` | string (ISO 8601) \| null | no | Set when the user approves the outline; required before Phase 5 |

### `page`

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `title` | string | yes | Non-empty |
| `slug` | string | yes | Lowercase kebab-case: `^[a-z0-9]+(-[a-z0-9]+)*$` |
| `folder` | object | yes | `path` (string, starts with `/`; `/` is root), `id` (string \| null; null allowed only for root). Folder IDs come from the family entry |
| `seo` | object | no | `title`, `description` |
| `openGraph` | object | no | `title`, `description`, `imageUrl` or `imageAssetName` |
| `schemaType` | string | no | JSON-LD type, e.g. `WebPage`, `Product`, `FAQPage` |

### `sections[]`

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `order` | int | yes | Unique across sections; build order |
| `familySection` | string | yes | Section name from the family entry, or the proposed name for a New section |
| `designSection` | string | no | Which digest section this came from |
| `reuseLevel` | enum(`reused`, `adapted`, `new`) | yes | Drives outline label, guard, report |
| `componentName` | string | required if `reused` or `adapted` | The component's **exact Webflow name**, from the family entry's `Component name` column, resolved to an id at run time (`flows/build.md` Phase 3). Never a Webflow id: the catalog names components and the id is recorded only in the run manifest. Two special values: `loose` for a master section that a duplicate-master or hybrid build copies as an element tree (reused only; `classPath` then carries the master's class path from the catalog row, e.g. `section.l-section.l-bg--surface-1`); `candidate:<slug>` for a component a live run has not created yet (see check 14) |
| `classPath` | string | required if `componentName` is `loose` | The master's class path for a loose section root, tag first, classes joined with dots |
| `masterSection` | int | no | For `loose` sections: the 1-based position of the copied section inside `main` on the master, so the build can find it after `create_page` (catalog row `#`) |
| `variant` | string \| null | no | Existing variant to use |
| `adaptation` | object | required if `adapted` | At least one of `newVariant` (string) or `newProps` (array<string>) |
| `newComponentSpec` | object | required if `new` | `name` (string, required), `description`, `structure` (string or array<string>), `props` (array<string>) |
| `layout` | object | no | `columns` (int 1 to 6, default 1), `align`, `density`, `breakpoints` (`{"991": int, "767": int, "479": int}` overrides for the outline) |
| `slots` | array<object> | yes (may be empty) | Each `{name (string), content (string \| null), status: enum(final, draft, missing, manual)}`; `final`, `draft` and `manual` need non-empty content. `manual` means the value is decided but the build cannot write it, so the publisher enters it in the Designer. Which slots those are is measured per site and recorded in `webflow-conventions.md`, "Rate limits and response sizes"; on a site whose element reads exceed the request budget it is text, links and images inside loose sections and every slot child, and on a small site it may be nothing at all (see `rules.md` rule 10) |
| `images` | array<object> | no | Each has `url` or `assetName` (one required) and `alt` (string, non-empty) |

## Validation checklist

`validate_brief.py` implements exactly this list. Run it by hand when scripts
are unavailable; report each failing line as a violation.

1. Top-level required keys present: `site`, `family`, `familyVersion`,
   `templateModel`, `isolationMode`, `page`, `sections`.
2. `site` is an object with a non-empty string `id`.
3. `family` is non-empty lowercase kebab-case.
4. `familyVersion` matches `^\d+\.\d+\.\d+$`.
5. `templateModel` is one of `duplicate-master`, `component-recipe`, `hybrid`.
6. `isolationMode` is one of `draft-main`, `branch`. With
   `--branching unavailable` (the value `webflow-conventions.md` records for a
   site whose `list_branches` returned 403 `not_enterprise_plan_site`),
   `branch` is a violation: the option is never offered on such a site. Pass
   the flag that matches what onboarding measured for your site; omit it only
   when branching is available.
7. `page.title` is a non-empty string.
8. `page.slug` matches `^[a-z0-9]+(-[a-z0-9]+)*$`.
9. `page.folder` is present and is an object; `path` is a string starting with
   `/`; `id` is a string or null; `id` may be null only when `path` is `/`.
10. `sections` is a non-empty array.
11. Every `sections[].order` is an integer and orders are unique.
12. Every `sections[].familySection` is a non-empty string.
13. Every `sections[].reuseLevel` is one of `reused`, `adapted`, `new`.
14. A `reused` or `adapted` section has a non-empty string `componentName`; a
    `new` section has a `newComponentSpec` object with a non-empty `name`.
    `componentName` is never a Webflow id (the dashed 32-hex component form or
    a 24-hex string is a violation): the catalog and the brief name components
    and the run resolves the name, so a deleted-and-recreated component does
    not invalidate the brief. `componentName` = `loose` is valid only when
    `templateModel` is `duplicate-master` or `hybrid`, only with `reuseLevel`
    `reused`, and only with a non-empty `classPath`. `componentName` =
    `candidate:<kebab-slug>` is a placeholder for a component a run has not
    created yet (a promoted-in-waiting candidate); it validates without
    `--require-approval` and fails with it, because a build cannot start
    against a component that does not exist. A live run replaces the
    placeholder with the created component's name before approval.
15. An `adapted` section has an `adaptation` object with `newVariant`
    (non-empty string) or `newProps` (non-empty array).
16. Every section has a `slots` array; every slot has a non-empty `name` and a
    `status` in `final`, `draft`, `missing`, `manual`; slots with status
    `final`, `draft` or `manual` have non-empty string `content`.
17. Every image has `url` or `assetName` (non-empty string) and a non-empty
    `alt`.
18. Every decision has `status` in `open`, `resolved`.
19. Every token substitution has `match` in `exact`, `near`.
20. `approvedAt`, if present and not null, is a string. With
    `--require-approval`, it must be a non-null string.

Output of the script: one JSON line per violation
(`{"path": "sections[2].componentName", "check": 14, "message": "..."}`), exit
code 1 if there is at least one; on success a single line
`{"ok": true, "sections": N, "slots": M}` and exit code 0. Exit code 2 for
unreadable input.

## Brief hash

`sha256` of the brief serialized as JSON with sorted keys and no extra
whitespace (`json.dumps(brief, sort_keys=True, separators=(",", ":"))`).
Recorded in the manifest as `briefHash`.
