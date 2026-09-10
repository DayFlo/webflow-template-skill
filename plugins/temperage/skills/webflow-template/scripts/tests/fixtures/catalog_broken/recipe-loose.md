---
name: Recipe with loose rows
slug: recipe-loose
version: 1.0.0
status: draft
templateModel: component-recipe
isolationDefault: draft-main
allowedFolders:
  - /recipes
schemaType: WebPage
---

## Purpose
Broken on purpose: a component-recipe family cannot have loose sections, and the shell table cannot either.

## Section outline
| # | Section | Component name | Class path | Owner | Required | Props | Variants | Slots | Content guidance | Image sizes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | hero | loose | header.l-section--header | self | required |  |  |  |  |  |
| 2 | band | loose |  | shared | optional |  |  |  | missing class path and wrong owner |  |

## Shell components
| Role | Component name | Owner |
| --- | --- | --- |
| nav | loose | self |

## Allowed folders
| Path | Folder ID |
| --- | --- |
| /recipes | 0000000000000000000000c4 |

## SEO and Open Graph defaults
none

## JSON-LD template
none

## Example pages
| Page ID | Slug | Note |
| --- | --- | --- |

## Do and don't
- nothing

## Changelog
- 1.0.0: created.
