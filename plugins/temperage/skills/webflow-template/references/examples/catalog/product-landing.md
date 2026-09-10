---
name: Product landing
slug: product-landing
version: 1.1.0
status: promoted
templateModel: hybrid
masterPageId: 0000000000000000000000b1
masterPageSlug: product-landing-master
masterPagePath: /products/product-landing-master
isolationDefault: draft-main
allowedFolders:
  - /products
  - /integrations
schemaType: WebPage
additionalSchemaTypes:
  - FAQPage
referenceImage: product-landing.png
owner: Example Co design team
audience: Evaluating buyers arriving from search and paid campaigns
---

## Purpose
Single-product and single-integration landing pages for the fictional Example
Co site. The master carries the shell, one loose benefit band, and the closing
sections; the body is assembled from section components. This entry is an
**example**: onboarding replaces `references/catalog/` with entries measured
from your own site.

## Audience
Buyers evaluating one product or one partner integration. They arrive with a
specific question and leave through one primary call to action.

## Decisions
- Taken by the Example Co design team on 2026-01-05: family kept; model hybrid; master `0000000000000000000000b1` (`product-landing-master`); folders /products, /integrations; slug is the product or partner name in kebab-case; SEO title `<Subject> | Example Co`; schema WebPage plus FAQPage; isolation draft-main; publishing by humans only (publisher: the person whose Webflow MCP connection ran the build, named in the report).

## Section outline
| # | Section | Component name | Class path | Owner | Required | Props | Variants | Slots | Content guidance | Image sizes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | hero | Hero / Product |  | self | required | Heading, Subhead; Button Text, Button Link | default, dark | media | H1 under 60 characters; exactly one CTA | 1600x900 |
| 2 | logo-bar | Logo bar |  | self | optional | Caption, Visibility | default | logos | 5 to 8 logos, one row on desktop | 240x80 each |
| 3 | media-sidebar | Media sidebar section |  | self | optional | Media; Overline, Heading, Body Copy; Card Body, Card Button Text, Card Button Link | default | media | product walkthrough beside two supporting cards | 1280x720 |
| 4 | benefit-a | loose | section.l-section.l-bg--surface-1 | self | optional |  |  |  | copied from the master and edited in place; a fresh build may use `Two column layout section` instead | 1200x800 |
| 5 | feature-grid | Feature grid |  | self | required | Heading, Feature 1, Feature 2, Feature 3 | default, icon-top |  | exactly three features, one line each | none |
| 6 | faq | FAQ section |  | shared | required | Overline, Heading; Button Text, Button Link | default | questions | four to six questions; question blocks fill the slot | none |
| 7 | cta-band | CTA band |  | self | required | Heading, Body Copy; Button Text, Button Link | default, dark |  | one CTA, repeating the hero action | none |

## Shell components
| Role | Component name | Owner | Notes |
| --- | --- | --- | --- |
| analytics | Analytics script | shared | first element inside the body on every page |
| nav | Site nav | shared | variant `default` |
| footer | Site footer | shared | variant `default` |
| faq-item | FAQ question block | shared | fills the FAQ section `questions` slot |

## Allowed folders
| Path | Folder ID |
| --- | --- |
| /products | 0000000000000000000000c1 |
| /integrations | 0000000000000000000000c2 |

## SEO and Open Graph defaults
Title `<Subject> | Example Co`, under 60 characters. Description 140 to 160
characters, taken from the hero subhead. Open Graph title and description are
copied from SEO; the default image is `og-default.png` at 1200x630.

## JSON-LD template
```json
{
  "@context": "https://schema.org",
  "@type": "WebPage",
  "name": "<page.title>",
  "description": "<page.seo.description>",
  "url": "<page.url>"
}
```

## Reference image
`product-landing.png` in the asset library (a Designer snapshot of the master).

## Example pages
| Page ID | Slug | Note |
| --- | --- | --- |
| 0000000000000000000000b1 | product-landing-master | master |
| 0000000000000000000000b4 | orbit | the worked example in `assets/examples/` |

## Do and don't
- Do: keep exactly one primary call to action, repeated in the hero and the CTA band.
- Do: leave `benefit-a` in place when the design has a supporting band; it is a loose element tree copied from the master and edited node by node.
- Don't: edit `Hero / Product`, `FAQ section`, or any other pre-existing component's base variant from a build run. Add a variant instead.
- Don't: add a section that is neither a component nor a loose row the master already carries; that is a New section and becomes a candidate.

## Changelog
- 1.1.0 (2026-01-05): added the `icon-top` feature-grid variant and the `media-sidebar` row.
- 1.0.0 (2026-01-04): created at onboarding.
