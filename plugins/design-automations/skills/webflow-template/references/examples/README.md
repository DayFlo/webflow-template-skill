# Worked example (fictional site)

Everything in this folder describes **Example Co**, a site that does not exist.
It is here so the catalog and conventions formats are legible before anyone has
run onboarding. Nothing here is read by a build run, and `flows/onboard.md`
does not overwrite it: onboarding writes `references/catalog/` and
`references/webflow-conventions.md`, one directory up.

| File | What it shows |
| --- | --- |
| `catalog/product-landing.md` | A promoted family entry in the format `../catalog/README.md` specifies: front matter, decisions, a section outline with one `loose` row, shell components, folders, SEO and schema defaults, example pages, changelog. `scripts/catalog_lint.py` passes on this directory. |
| `webflow-conventions.md` | The same file `../webflow-conventions.md` is a template for, filled in. Every MEASURE row has an answer and a date, including the ones a small site answers differently from a large one. |

The matching brief, rendered outline, and run manifest for the same fictional
site are in `../../assets/examples/`.

Every identifier here is synthetic and comes from two families and no others:
24-hex ids shaped `0000000000000000000000xx` for the site, pages, and folders,
and UUIDs shaped `1111aaaa-0000-4000-8000-000000000xxx` for components, props,
and variables. `checks/repo-check.sh` at the repository root fails if any other
id shape appears anywhere in the tree.

Two more synthetic catalogs live under `../../scripts/tests/fixtures/`:
`catalog_valid/` (three entries, including a `proposed` family with `loose`
rows and a `candidate:` placeholder) and `catalog_broken/` (entries that are
wrong on purpose, one lint rule at a time).
