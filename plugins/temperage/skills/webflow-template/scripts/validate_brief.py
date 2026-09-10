#!/usr/bin/env python3
"""Validate a webflow-template brief.

Implements the checklist in references/brief-schema.md, one numbered check per
rule. Standard library only.

Sections name their component: `componentName` carries the component's exact
Webflow name, never a Webflow component id (the id is resolved at run time and
recorded only in the run manifest). Two special values (check 14): "loose"
marks a master section that duplicate-master or hybrid copies as an element
tree (reused only; `classPath` then carries the master's class path);
"candidate:<slug>" is a placeholder for a component a live run has not created
yet and is rejected under --require-approval.

Usage:
    validate_brief.py brief.json [--require-approval] [--branching available|unavailable]

Output: one JSON line per violation on stdout, exit 1 if any. On success one
line {"ok": true, "sections": N, "slots": M}, exit 0. Exit 2 if the input
cannot be read or is not a JSON object.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any

KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
# A Webflow id (dashed 32-hex component form, or the 24-hex page/folder form).
# Components are named, not identified: references/catalog/README.md.
WEBFLOW_ID = re.compile(r"\b(?:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|[0-9a-f]{24})\b", re.IGNORECASE)
TEMPLATE_MODELS = ("duplicate-master", "component-recipe", "hybrid")
ISOLATION_MODES = ("draft-main", "branch")
REUSE_LEVELS = ("reused", "adapted", "new")
SLOT_STATUSES = ("final", "draft", "missing", "manual")
DECISION_STATUSES = ("open", "resolved")
TOKEN_MATCHES = ("exact", "near")
REQUIRED_TOP = ("site", "family", "familyVersion", "templateModel", "isolationMode", "page", "sections")
LOOSE = "loose"                       # a master section copied as an element tree (duplicate-master, hybrid)
CANDIDATE_PREFIX = "candidate:"       # a component that a live run has not created yet
LOOSE_MODELS = ("duplicate-master", "hybrid")
BRANCHING = ("available", "unavailable")   # what webflow-conventions.md records for the site


def _nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and value.strip() != ""


def validate(brief: Any, require_approval: bool = False, branching: str | None = None) -> list[dict[str, Any]]:
    """Return a list of violations. An empty list means the brief is valid."""
    violations: list[dict[str, Any]] = []

    def fail(path: str, check: int, message: str) -> None:
        violations.append({"path": path, "check": check, "message": message})

    if not isinstance(brief, dict):
        fail("$", 1, "brief must be a JSON object")
        return violations

    # 1. required top-level keys
    for key in REQUIRED_TOP:
        if key not in brief:
            fail(key, 1, f"required field '{key}' is missing")

    # 2. site.id
    site = brief.get("site")
    if "site" in brief:
        if not isinstance(site, dict):
            fail("site", 2, "site must be an object")
        elif not _nonempty_str(site.get("id")):
            fail("site.id", 2, "site.id must be a non-empty string")

    # 3. family
    if "family" in brief and not (_nonempty_str(brief["family"]) and KEBAB.match(brief["family"])):
        fail("family", 3, "family must be a non-empty lowercase kebab-case slug")

    # 4. familyVersion
    if "familyVersion" in brief and not (isinstance(brief["familyVersion"], str) and SEMVER.match(brief["familyVersion"])):
        fail("familyVersion", 4, "familyVersion must be semver MAJOR.MINOR.PATCH")

    # 5. templateModel
    if "templateModel" in brief and brief["templateModel"] not in TEMPLATE_MODELS:
        fail("templateModel", 5, f"templateModel must be one of {', '.join(TEMPLATE_MODELS)}")

    # 6. isolationMode
    if "isolationMode" in brief and brief["isolationMode"] not in ISOLATION_MODES:
        fail("isolationMode", 6, f"isolationMode must be one of {', '.join(ISOLATION_MODES)}")
    elif brief.get("isolationMode") == "branch" and branching == "unavailable":
        fail("isolationMode", 6, "isolationMode 'branch' is not allowed: webflow-conventions.md records branching as unavailable for this site, so the option is never offered")

    # 7-9. page
    page = brief.get("page")
    if "page" in brief:
        if not isinstance(page, dict):
            fail("page", 7, "page must be an object")
        else:
            if not _nonempty_str(page.get("title")):
                fail("page.title", 7, "page.title must be a non-empty string")
            slug = page.get("slug")
            if not (isinstance(slug, str) and KEBAB.match(slug)):
                fail("page.slug", 8, "page.slug must be lowercase kebab-case (^[a-z0-9]+(-[a-z0-9]+)*$)")
            folder = page.get("folder")
            if folder is None:
                fail("page.folder", 9, "page.folder is required")
            elif not isinstance(folder, dict):
                fail("page.folder", 9, "page.folder must be an object with path and id")
            else:
                path = folder.get("path")
                if not (isinstance(path, str) and path.startswith("/")):
                    fail("page.folder.path", 9, "page.folder.path must be a string starting with '/'")
                fid = folder.get("id", None)
                if fid is not None and not _nonempty_str(fid):
                    fail("page.folder.id", 9, "page.folder.id must be a non-empty string or null")
                if fid is None and path != "/":
                    fail("page.folder.id", 9, "page.folder.id may be null only for the root folder '/'")

    # 10-17. sections
    sections = brief.get("sections")
    slot_count = 0
    if "sections" in brief:
        if not isinstance(sections, list) or not sections:
            fail("sections", 10, "sections must be a non-empty array")
            sections = []
        seen_orders: dict[Any, int] = {}
        for i, section in enumerate(sections):
            p = f"sections[{i}]"
            if not isinstance(section, dict):
                fail(p, 10, "section must be an object")
                continue
            order = section.get("order")
            if not isinstance(order, int) or isinstance(order, bool):
                fail(f"{p}.order", 11, "order must be an integer")
            elif order in seen_orders:
                fail(f"{p}.order", 11, f"order {order} duplicates sections[{seen_orders[order]}]")
            else:
                seen_orders[order] = i
            if not _nonempty_str(section.get("familySection")):
                fail(f"{p}.familySection", 12, "familySection must be a non-empty string")
            level = section.get("reuseLevel")
            if level not in REUSE_LEVELS:
                fail(f"{p}.reuseLevel", 13, f"reuseLevel must be one of {', '.join(REUSE_LEVELS)}")
            name = section.get("componentName")
            if level in ("reused", "adapted") and not _nonempty_str(name):
                fail(f"{p}.componentName", 14, f"a '{level}' section must have a non-empty componentName")
            if _nonempty_str(name) and WEBFLOW_ID.search(name):
                fail(f"{p}.componentName", 14, f"componentName {name!r} is a Webflow id; briefs name components and the run resolves the id, which is recorded only in the run manifest")
            elif _nonempty_str(name) and name == LOOSE:
                # a loose section is a copied element tree: only under a model that duplicates a master,
                # only reused (there is no component to add a variant or prop to), and named by class path
                if brief.get("templateModel") not in LOOSE_MODELS:
                    fail(f"{p}.componentName", 14, f"componentName 'loose' is only valid when templateModel is one of {', '.join(LOOSE_MODELS)}")
                if level != "reused":
                    fail(f"{p}.componentName", 14, "a 'loose' section must be reused; adapt or replace it with a component instead")
                if not _nonempty_str(section.get("classPath")):
                    fail(f"{p}.classPath", 14, "a 'loose' section must carry the master's class path in classPath")
            elif _nonempty_str(name) and name.startswith(CANDIDATE_PREFIX):
                if not KEBAB.match(name[len(CANDIDATE_PREFIX):]):
                    fail(f"{p}.componentName", 14, "a candidate placeholder must be 'candidate:<kebab-slug>'")
                if require_approval:
                    fail(f"{p}.componentName", 14, f"componentName {name!r} is a placeholder; the build cannot start until the candidate is promoted and the created component's name is filled in (--require-approval)")
            if level == "new":
                spec = section.get("newComponentSpec")
                if not isinstance(spec, dict) or not _nonempty_str(spec.get("name")):
                    fail(f"{p}.newComponentSpec", 14, "a 'new' section must have newComponentSpec with a non-empty name")
            if level == "adapted":
                adaptation = section.get("adaptation")
                ok = isinstance(adaptation, dict) and (
                    _nonempty_str(adaptation.get("newVariant"))
                    or (isinstance(adaptation.get("newProps"), list) and len(adaptation["newProps"]) > 0)
                )
                if not ok:
                    fail(f"{p}.adaptation", 15, "an 'adapted' section must declare adaptation.newVariant or a non-empty adaptation.newProps")
            slots = section.get("slots")
            if not isinstance(slots, list):
                fail(f"{p}.slots", 16, "slots must be an array (may be empty)")
            else:
                for j, slot in enumerate(slots):
                    sp = f"{p}.slots[{j}]"
                    slot_count += 1
                    if not isinstance(slot, dict):
                        fail(sp, 16, "slot must be an object")
                        continue
                    if not _nonempty_str(slot.get("name")):
                        fail(f"{sp}.name", 16, "slot name must be a non-empty string")
                    status = slot.get("status")
                    if status not in SLOT_STATUSES:
                        fail(f"{sp}.status", 16, f"slot status must be one of {', '.join(SLOT_STATUSES)}")
                    elif status in ("final", "draft", "manual") and not _nonempty_str(slot.get("content")):
                        fail(f"{sp}.content", 16, f"a '{status}' slot must have non-empty content")
            images = section.get("images", [])
            if images is not None:
                if not isinstance(images, list):
                    fail(f"{p}.images", 17, "images must be an array")
                else:
                    for k, image in enumerate(images):
                        ip = f"{p}.images[{k}]"
                        if not isinstance(image, dict):
                            fail(ip, 17, "image must be an object")
                            continue
                        if not (_nonempty_str(image.get("url")) or _nonempty_str(image.get("assetName"))):
                            fail(ip, 17, "image must have url or assetName")
                        if not _nonempty_str(image.get("alt")):
                            fail(f"{ip}.alt", 17, "every image needs non-empty alt text")

    # 18. decisions
    decisions = brief.get("decisions", [])
    if decisions is not None:
        if not isinstance(decisions, list):
            fail("decisions", 18, "decisions must be an array")
        else:
            for i, decision in enumerate(decisions):
                if not isinstance(decision, dict) or decision.get("status") not in DECISION_STATUSES:
                    fail(f"decisions[{i}].status", 18, f"decision status must be one of {', '.join(DECISION_STATUSES)}")

    # 19. token substitutions
    tokens = brief.get("tokens")
    if isinstance(tokens, dict):
        subs = tokens.get("substitutions", [])
        if not isinstance(subs, list):
            fail("tokens.substitutions", 19, "tokens.substitutions must be an array")
        else:
            for i, sub in enumerate(subs):
                if not isinstance(sub, dict) or sub.get("match") not in TOKEN_MATCHES:
                    fail(f"tokens.substitutions[{i}].match", 19, f"token match must be one of {', '.join(TOKEN_MATCHES)}")
    elif tokens is not None and "tokens" in brief:
        fail("tokens", 19, "tokens must be an object")

    # 20. approvedAt
    approved = brief.get("approvedAt")
    if approved is not None and not _nonempty_str(approved):
        fail("approvedAt", 20, "approvedAt must be an ISO 8601 string or null")
    if require_approval and not _nonempty_str(approved):
        fail("approvedAt", 20, "approvedAt is required before the build phase (--require-approval)")

    return violations


def count_slots(brief: Any) -> int:
    total = 0
    if isinstance(brief, dict) and isinstance(brief.get("sections"), list):
        for section in brief["sections"]:
            if isinstance(section, dict) and isinstance(section.get("slots"), list):
                total += len(section["slots"])
    return total


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a webflow-template brief against references/brief-schema.md.")
    parser.add_argument("brief", help="path to the brief JSON file ('-' for stdin)")
    parser.add_argument("--require-approval", action="store_true", help="also require a non-null approvedAt (use before the build phase)")
    parser.add_argument("--branching", choices=BRANCHING, help="site branching per webflow-conventions.md; with 'unavailable' an isolationMode of 'branch' is a violation (check 6)")
    args = parser.parse_args(argv)

    try:
        if args.brief == "-":
            brief = json.load(sys.stdin)
        else:
            with open(args.brief, "r", encoding="utf-8") as fh:
                brief = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"path": "$", "check": 0, "message": f"cannot read brief: {exc}"}))
        return 2

    violations = validate(brief, require_approval=args.require_approval, branching=args.branching)
    if violations:
        for v in violations:
            print(json.dumps(v))
        return 1
    sections = len(brief.get("sections", [])) if isinstance(brief, dict) else 0
    print(json.dumps({"ok": True, "sections": sections, "slots": count_slots(brief)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
