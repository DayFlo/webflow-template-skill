---
name: Integration page
slug: integration-page
version: 1.0.0
templateModel: component-recipe
isolationDefault: draft-main
allowedFolders:
  - /integrations
schemaType: SoftwareApplication
---

## Purpose
Partner integration pages built from section components; no master page.

## Section outline
| # | Section | Component name | Class path | Owner | Required | Props | Variants | Slots | Content guidance | Image sizes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | hero | Hero / Product |  | product-landing | required | heading, subhead | default | media | borrowed hero | 1600x900 |
| 2 | steps | Setup steps |  | self | required | heading, steps | default |  | three to five steps | none |

## Shell components
| Role | Component name | Owner |
| --- | --- | --- |
| nav | Site nav | shared |

## Allowed folders
| Path | Folder ID |
| --- | --- |
| /integrations | 0000000000000000000000c2 |

## SEO and Open Graph defaults
Title: `<partner> integration | Example Co`.

## JSON-LD template
```json
{"@context": "https://schema.org", "@type": "SoftwareApplication", "name": "<page.title>"}
```

## Example pages
| Page ID | Slug | Note |
| --- | --- | --- |

## Do and don't
- Do: reuse the product-landing hero.

## Changelog
- 1.0.0 (2026-08-30): created at onboarding.
