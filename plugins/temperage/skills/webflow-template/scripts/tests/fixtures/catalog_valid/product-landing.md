---
name: Product landing
slug: product-landing
version: 1.1.0
status: promoted
templateModel: hybrid
masterPageId: 0000000000000000000000b1
masterPageSlug: product-landing-master
isolationDefault: draft-main
allowedFolders:
  - /products
  - /integrations
schemaType: WebPage
additionalSchemaTypes:
  - FAQPage
referenceImage: product-landing.png
owner: Example Co design team
---

## Purpose
Landing pages for a single product or integration, aimed at evaluating buyers.

## Section outline
| # | Section | Component name | Class path | Owner | Required | Props | Variants | Slots | Content guidance | Image sizes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | hero | Hero / Product |  | self | required | heading, subhead, ctaLabel, ctaLink | default, dark | media | H1 under 60 chars | 1600x900 |
| 2 | logo-bar | Logo bar |  | self | optional | caption | default | logos | 5 to 8 logos | 240x80 |
| 3 | feature-grid | Feature grid |  | self | required | heading, feature1, feature2, feature3 | default, icon-top |  | three features | none |
| 4 | cta-band | CTA band |  | self | required | heading, ctaLabel, ctaLink | default, dark |  | one CTA | none |

## Shell components
| Role | Component name | Owner |
| --- | --- | --- |
| nav | Site nav | shared |
| footer | Site footer | shared |

## Allowed folders
| Path | Folder ID |
| --- | --- |
| /products | 0000000000000000000000c1 |
| /integrations | 0000000000000000000000c2 |

## SEO and Open Graph defaults
Title: `<page.title> | Example Co`. Description: first 155 characters of the hero subhead. OG image: `og-default.png`.

## JSON-LD template
```json
{"@context": "https://schema.org", "@type": "WebPage", "name": "<page.title>", "url": "<page.url>"}
```

## Example pages
| Page ID | Slug | Note |
| --- | --- | --- |
| 0000000000000000000000b1 | product-landing-master | master |

## Do and don't
- Do: keep one primary CTA per page.
- Don't: add sections that are not components.

## Changelog
- 1.1.0 (2026-01-04): added `icon-top` feature-grid variant.
- 1.0.0 (2026-08-30): created at onboarding.
