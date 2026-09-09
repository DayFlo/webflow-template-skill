# Outline rendering spec

The visual outline is the approval gate in `flows/build.md` Phase 4. It is a
rough wireframe plus the section mapping, rendered from the brief. Script:
`python3 scripts/render_outline.py brief.json > outline.html`. When scripts are
unavailable, author the HTML by hand following these rules (on Claude.ai, an
HTML artifact written directly is fine), or, if HTML is impractical, render the
same content in the same order as Markdown and say the outline is text-only.

## Output constraints

- One self-contained HTML file. **No external assets**: no `<script src>`,
  `<link href>`, `<img src>`, web fonts, or CDN references. All CSS and JS
  inline. Image URLs from the brief appear as text, never as `src`.
- System font stack. Light background. Works without JavaScript; the only JS
  is the breakpoint focus toggle.
- Everything from the brief is HTML-escaped.

## Structure, top to bottom

1. **Header.** Page title; one line `family@version · templateModel ·
   isolationMode`; slug and folder path; approval status: "Approved <ISO>" or
   "Not yet approved".
2. **Breakpoint toggle.** Buttons: All, Desktop, Tablet 991, Mobile L 767,
   Mobile P 479. "All" shows the four frames side by side; any other button
   shows that frame alone at full width.
3. **Viewport frames.** Four frames in one row with widths proportional to
   the Webflow breakpoints (CSS grid `1440fr 991fr 767fr 479fr`), labeled
   Desktop (992 and up), Tablet (991), Mobile landscape (767), Mobile
   portrait (479). Each frame stacks every section in `order`.
4. **Section mapping table.** Order, design section, family section,
   component and variant (or the New spec name), reuse label, slot counts
   (final / draft / missing), image count.
5. **Decisions panel.** Open decisions first, each highlighted, then resolved
   ones with their resolution.
6. **Token substitutions.** Table observed → token → match (`exact`, `near`);
   then the unresolved list with notes.
7. **Manual handoff list.** Every `unsupported[]` item with its handoff text.
8. **Footer.** Generated timestamp, brief hash, the words "no external
   assets".

## Section card (inside every frame)

- Title row: `#order` and `familySection`; the **reuse label** as a colored
  pill: `Reused` (green), `Adapted` (amber), `New` (violet).
- Component line: `classPath` for a loose section, otherwise `componentName`
  (the component's name, `loose`, or `candidate:<slug>`), and `variant`; for `adapted`, "new variant `<name>`" or "new props `<list>`";
  for `new`, `newComponentSpec.name` and "candidate".
- **Layout preview.** A row of equal boxes, one per column at that
  breakpoint. Columns per breakpoint: desktop = `layout.columns` (default 1);
  tablet 991 = `min(columns, 2)`; mobile landscape 767 = `min(columns, 2)`;
  mobile portrait 479 = 1. `layout.breakpoints` overrides any of the three.
- **Slots.** One line per slot: name, status pill (`final` green, `draft`
  amber, `missing` red, `manual` indigo), and a content preview (first 80
  characters). A `missing` slot shows `TODO: <name>` instead of content. A
  `manual` slot shows "publisher enters in the Designer: " before the
  preview, because the build will not write it. In the 767 and 479
  frames the content preview is hidden; name and status stay.
- **Manual handoff.** The handoff panel opens with the count of `manual`
  slots and lists them as "section <order> <family section>: <slot name>",
  then the `unsupported` items. If there are none of either, the panel says
  "Nothing to hand off."
- **Images.** Footer line: "N images" and "alt ok" or "alt missing" (any
  image without alt).
- **Design source.** If `designSection` is set, a small line "from:
  <designSection>".

## Section stacking

Sections appear in ascending `order`, full width of the frame, separated by a
thin rule. Shell sections (nav, footer) are ordinary sections and appear where
the brief places them. Nothing is reordered by the renderer.

## Hand-rendered fallback

If writing HTML by hand, keep the same eight parts in the same order and the
same labels. For the four frames, a table with four columns (one per
breakpoint) and one row per section, each cell listing the column count and
the slot statuses, is an acceptable substitute. State in the report that the
outline was hand-rendered.
