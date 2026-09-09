# Worked example: brief, outline, manifest (fictional site)

The build-time half of the worked example. Same fictional site as
`../../references/examples/`: **Example Co**, which does not exist. Nothing
here is a run; nothing here is read by a build run.

| File | What it shows |
| --- | --- |
| `example.brief.json` | An approved brief for one page of the `product-landing` family: ten sections covering all three reuse levels, a `loose` section with its class path, a New section with its `newComponentSpec`, and slots in all four statuses (`final`, `draft`, `manual`, `missing`). Passes `validate_brief.py --require-approval`. |
| `example.outline.html` | What `render_outline.py` produced from that brief: one self-contained file, four breakpoint frames, no external assets, the reuse labels, the token substitutions, the open decisions, and the manual handoff panel. |
| `example.manifest.json` | The run manifest the build **would** write. Every step is `skipped` with a `dry-run: not executed` note, so `created` is empty and the ships-at-next-publish list is empty. It carries a passing guard verdict built from the fixtures in `../../scripts/tests/fixtures/example/`. |

Regenerate the outline after editing the brief:

```
python3 scripts/render_outline.py assets/examples/example.brief.json -o assets/examples/example.outline.html
```

`scripts/tests/test_example.py` checks all three, and the guard fixtures in
`scripts/tests/fixtures/example/` that the manifest's verdict came from.
