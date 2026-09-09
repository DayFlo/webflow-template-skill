# Interview question bank

Used by `flows/build.md` Phase 2. The digest from Phase 1 and the catalog entry
of the likely family already answer most of these; the interview exists to
close the gaps, not to re-ask what is known.

## Rules

- **At most 3 questions per turn.** Group related questions; wait for answers.
- **Never ask what is already established** by the digest, an earlier answer,
  or the family entry. The skip condition on every question says when to skip.
- **Fast path: "use family defaults".** Once a family is likely (after the
  first topic or two), offer it in one line: "I can take SEO patterns, schema
  type, folder, nav and footer, and the slug pattern from the `<family>`
  defaults. Say 'use family defaults' or tell me what differs." Accepting it
  skips every question marked **(default-able)** below, and the brief records
  `answers.usedFamilyDefaults: true`.
- **Explain Webflow terms once** the first time they appear (slot, prop,
  variant, draft, folder).
- **Confirm a summary** of six to ten lines at the end and wait for a yes.
- Every answer is written to the brief under `answers.<topic>`, and copied into
  `page`, `sections`, or `unsupported` where it belongs.

## Topics and questions

### 1. Purpose and audience (`answers.purpose`)

- What is this page for, in one sentence? *Skip if the digest shows a clear
  hero headline and subhead that state the purpose; confirm it instead.*
- Who is the main reader (role, stage: cold visitor, evaluating, customer)?
  *Skip if the source or the design states the audience.*

### 2. Primary action (`answers.primaryAction`)

- What is the one thing a reader should do on this page? *Skip if the digest
  shows exactly one primary CTA above the fold.*
- Where does it go (page in the site, external URL, form)? *Skip if the CTA
  destination is present in the source and resolves.*

### 3. Page identity (`answers.pageIdentity`, copied to `page`)

- Page title? *Skip if the design's H1 is final and the user agrees it is the
  title.*
- Slug? Offer the family's slug pattern applied to the title
  (**default-able**). *Skip if the user gave one.*
- Folder? Offer the family's allowed folders (**default-able**). *Skip if the
  family allows exactly one folder.*

### 4. SEO and Open Graph (`answers.seo`, copied to `page.seo`, `page.openGraph`)

- SEO title and meta description? Offer the family patterns filled with the
  page title (**default-able**). *Skip if the source carries them.*
- Open Graph image: public URL, an asset already in Webflow (name), or the
  family default (**default-able**).

### 5. Shell (`answers.shell`)

- Include the site nav and footer? (**default-able**; the family says.) *Skip
  unless the design omits one of them.*

### 6. Sections (`answers.sections`)

- The family has these sections: `<required list>` and optional
  `<optional list>`. The design maps to `<mapping>`. Anything to add, drop, or
  reorder? *Ask once, after showing the mapping; skip the follow-up if the user
  says it matches.*
- For a design section with no family match: adapt an existing section (new
  variant), create a new one (becomes a candidate), or drop it? *Ask per
  unmatched section, up to three per turn.*

### 7. Content status per slot (`answers.contentStatus`, copied to `sections[].slots[].status`)

- Is the copy in `<section>` final, draft, or still missing? *Skip for slots
  whose digest text is clearly final (no lorem, no brackets, no "TBD") unless
  the user said the copy is not ready.*
- For anything missing: who supplies it and when? (Goes to the decisions
  list, not a blocker.)

### 8. Images (`answers.images`, copied to `sections[].images[]`)

- For each image in the design: public URL, or the name of an asset already in
  Webflow? *Skip for images the source already gives as public URLs.*
- Prefer an asset already in the library, and say why once: uploading a new one
  puts the file on a public CDN URL from the moment of upload, before any
  publish and whether or not the draft page is ever published (`rules.md`
  rule 19). Ask before every upload, and never upload something confidential,
  unreleased, or under embargo just to get the draft built.
- Alt text? Offer a draft from the digest; the user confirms or edits.

### 9. Forms (`answers.forms`)

- The design shows a form in `<section>`. Reuse an existing site form
  (`list_forms` names) or an approved embed? *Skip if the design has no form.
  A new form or a new embed not in the outline goes to the handoff list.*

### 10. Responsive intent (`answers.responsive`)

- Anything unusual on tablet or mobile (stacking order, hidden sections,
  different image)? *Skip unless the design includes mobile artboards that
  differ from the default collapse, or the user mentioned mobile.*

### 11. Localization (`answers.localization`)

- Will this page need other locales? *Skip if the site has one locale (from
  the inventory). Report-only in v1; the answer goes to `unsupported[]`.*

### 12. Schema (`answers.schema`, copied to `page.schemaType`)

- JSON-LD type? Offer the family default (**default-able**). *Skip if the user
  accepted defaults.*

### 13. Launch owner (`answers.launchOwner`)

- When should this page go live, and who reviews it before then? *Never skip;
  it goes in the report. The publisher is not a question: the person whose
  Webflow MCP connection runs the build is the responsible publisher
  (`webflow-conventions.md`, "Publish policy"), so on Claude.ai tell the
  submitter that is them. One short question, ask it with the summary.*

## Order and pacing

Ask topics 1 to 3 first (they decide the family), offer the fast path, then
6 and 7 (they decide the outline), then the rest. A typical interview is four
to six turns. If the digest is thin (screenshots only), expect two more turns
on topics 6 to 8.
