---
name: Partner page
slug: partner-page
version: 0.1.0
status: proposed
templateModel: duplicate-master
masterPageId: 0000000000000000000000b2
masterPageSlug: acme
masterPagePath: /partners/acme
isolationDefault: draft-main
allowedFolders:
  - /partners
schemaType: SoftwareApplication
owner: Example Co design team
---

## Purpose
Proposed by onboarding: partner pages duplicated from the Acme master, whose body is mostly loose sections.

## Audience
Users of the partner tool. This extra section is tolerated by the linter.

## Section outline
| # | Section | Component name | Class path | Owner | Required | Props | Variants | Slots | Content guidance | Image sizes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | hero | loose | header.l-section--header.l-mode--dark | self | required |  |  |  | H1 with partner name; copied from the master and edited in place | 1600x900 |
| 2 | steps | Setup steps |  | integration-page | required | heading, steps | default |  | borrowed | none |
| 3 | benefit-a | loose | section.l-section.l-bg--surface-1 | self | optional |  |  |  | fresh builds may use `Hero / Product` instead | none |
| 4 | install-steps | candidate:partner-install-steps |  | self | optional | overline, heading, steps |  |  | Proposed name `Install steps`. placeholder: no component exists yet; the first run that builds it creates the candidate | none |

## Shell components
| Role | Component name | Owner |
| --- | --- | --- |
| nav | Site nav | shared |

## Allowed folders
| Path | Folder ID |
| --- | --- |
| /partners | 0000000000000000000000c3 |

## SEO and Open Graph defaults
Title: `Example Co for <Partner> | Example Co`.

## JSON-LD template
```json
{"@context": "https://schema.org", "@type": "SoftwareApplication", "name": "<page.title>"}
```

## Reference image
Empty (Designer was closed). Extra section, tolerated.

## Example pages
| Page ID | Slug | Note |
| --- | --- | --- |
| 0000000000000000000000b2 | acme | master |

## Do and don't
- Do: say in the report that this family is proposed and unconfirmed.

## Changelog
- 0.1.0 (2026-01-05): proposed by onboarding.
