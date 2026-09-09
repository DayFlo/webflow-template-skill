#!/usr/bin/env python3
"""Lint the template catalog (references/catalog/<family>.md) and sync-state.json.

Entry format: references/catalog/README.md. The front matter is a small
`key: value` block (scalars and simple `- item` lists) parsed here with the
standard library; no YAML library is used.

Components are keyed by **name**, never by Webflow component id: the id is
resolved at run time (flows/build.md Phase 3) and recorded only in the run
manifest. A bare Webflow id in a component column is an error (rule
COMPONENT-ID).

Checks: required front-matter fields, semver version, slug equals file name,
status enum (proposed / promoted / deprecated), template model and isolation
enums, master page id and leaf slug when the model is duplicate-master or
hybrid, allowed folders start with '/', required headings (extra H2 sections
are tolerated), section outline table columns and rows, every row carries a
non-empty Component name that is not a Webflow component id, component
ownership (self / shared / borrowed), unique self-owned component names across
families, the `loose` convention for duplicate-master sections that are element
trees rather than components (Component name `loose`, Class path = the master's
class path, Owner `self`; never allowed when the model is component-recipe and
never in the shell table), `candidate:<slug>` placeholder rows for sections a
proposed family still lacks (Owner `self`; rejected once the family is
promoted), kebab-case slugs, `additionalSchemaTypes` (optional; when present a
non-empty list of extra JSON-LD types emitted beside `schemaType`, such as
`FAQPage`), changelog mentions the version, and that sync-state.json parses
with the keys siteId, lastSync, paths.

Usage:
    catalog_lint.py references/catalog [--sync-state references/sync-state.json]

Output: one JSON object {"ok": bool, "families": [...], "errors": [...]}.
Exit 0 when there are no errors, 1 otherwise, 2 when the directory is unreadable.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any

KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
# A Webflow component id: the dashed 32-hex form components use, or the 24-hex
# form pages, folders and collections use. Neither belongs in a component
# column any more (references/catalog/README.md, "Components are named").
WEBFLOW_ID = re.compile(r"\b(?:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|[0-9a-f]{24})\b", re.IGNORECASE)
TEMPLATE_MODELS = ("duplicate-master", "component-recipe", "hybrid")
ISOLATION_MODES = ("draft-main", "branch")
STATUSES = ("proposed", "promoted", "deprecated")
LOOSE = "loose"
CANDIDATE_PREFIX = "candidate:"
REQUIRED_FM = ("name", "slug", "version", "templateModel", "isolationDefault", "allowedFolders", "schemaType")
REQUIRED_HEADINGS = (
    "Purpose", "Section outline", "Shell components", "Allowed folders",
    "SEO and Open Graph defaults", "JSON-LD template", "Example pages", "Do and don't", "Changelog",
)
OUTLINE_COLUMNS = ("#", "section", "component name", "class path", "owner", "required", "props", "variants", "slots", "content guidance", "image sizes")
SHELL_COLUMNS = ("role", "component name", "owner")
FOLDER_COLUMNS = ("path", "folder id")
EXAMPLE_COLUMNS = ("page id", "slug", "note")


# ------------------------------------------------------------------ parsing

def parse_front_matter(text: str) -> tuple[dict[str, Any], str, list[str]]:
    """Return (fields, body, errors). Fields are strings or lists of strings."""
    errors: list[str] = []
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text, ["front matter must start with '---' on the first line"]
    fields: dict[str, Any] = {}
    current_list: str | None = None
    end = None
    for idx in range(1, len(lines)):
        raw = lines[idx]
        line = raw.rstrip()
        if line.strip() == "---":
            end = idx
            break
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        stripped = line.strip()
        if stripped.startswith("- "):
            if current_list is None:
                errors.append(f"line {idx + 1}: list item without a preceding 'key:' line")
                continue
            fields[current_list].append(_unquote(stripped[2:].strip()))
            continue
        if ":" not in stripped:
            errors.append(f"line {idx + 1}: expected 'key: value', got {stripped!r}")
            current_list = None
            continue
        key, _, value = stripped.partition(":")
        key = key.strip()
        value = value.strip()
        if not re.match(r"^[A-Za-z][A-Za-z0-9_-]*$", key):
            errors.append(f"line {idx + 1}: invalid key {key!r}")
            current_list = None
            continue
        if value == "":
            fields[key] = []
            current_list = key
        else:
            fields[key] = _unquote(value)
            current_list = None
    if end is None:
        return fields, "", errors + ["front matter is not closed with '---'"]
    body = "\n".join(lines[end + 1:])
    return fields, body, errors


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def parse_sections(body: str) -> dict[str, str]:
    """Map H2 heading text -> the text under it (until the next H2)."""
    sections: dict[str, str] = {}
    current: str | None = None
    buf: list[str] = []
    for line in body.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            if current is not None:
                sections[current] = "\n".join(buf)
            current = m.group(1)
            buf = []
        elif current is not None:
            buf.append(line)
    if current is not None:
        sections[current] = "\n".join(buf)
    return sections


def parse_table(text: str) -> tuple[list[str], list[dict[str, str]]]:
    """Parse the first markdown table in text. Returns (header cells lowercased, rows)."""
    rows: list[list[str]] = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            rows.append(cells)
        elif rows:
            break
    if len(rows) < 2:
        return [], []
    header = [c.lower() for c in rows[0]]
    data = []
    for cells in rows[2:]:
        if all(c == "" for c in cells):
            continue
        padded = cells + [""] * (len(header) - len(cells))
        data.append({header[i]: padded[i] for i in range(len(header))})
    return header, data


# ------------------------------------------------------------------ linting

class Linter:
    def __init__(self) -> None:
        self.errors: list[dict[str, str]] = []
        self.families: list[dict[str, Any]] = []
        self.owned: dict[str, str] = {}          # component name -> owning family slug
        self.borrowed: list[tuple[str, str, str]] = []   # (file, component name, from family)

    def err(self, file: str, rule: str, message: str) -> None:
        self.errors.append({"file": file, "rule": rule, "message": message})

    def lint_file(self, path: str) -> None:
        file = os.path.basename(path)
        stem = file[:-3]
        try:
            with open(path, "r", encoding="utf-8") as fh:
                text = fh.read()
        except OSError as exc:
            self.err(file, "READ", f"cannot read: {exc}")
            return
        fm, body, fm_errors = parse_front_matter(text)
        for e in fm_errors:
            self.err(file, "FM-PARSE", e)
        if not fm and fm_errors:
            return

        for key in REQUIRED_FM:
            if key not in fm or fm[key] in ("", []):
                self.err(file, "FM-REQUIRED", f"missing or empty front-matter field '{key}'")

        slug = fm.get("slug")
        if isinstance(slug, str) and slug:
            if not KEBAB.match(slug):
                self.err(file, "FM-SLUG", f"slug {slug!r} is not lowercase kebab-case")
            if slug != stem:
                self.err(file, "FM-SLUG", f"slug {slug!r} does not match file name {stem!r}")
        version = fm.get("version")
        if isinstance(version, str) and version and not SEMVER.match(version):
            self.err(file, "FM-VERSION", f"version {version!r} is not semver MAJOR.MINOR.PATCH")
        model = fm.get("templateModel")
        if isinstance(model, str) and model and model not in TEMPLATE_MODELS:
            self.err(file, "FM-MODEL", f"templateModel {model!r} must be one of {', '.join(TEMPLATE_MODELS)}")
        isolation = fm.get("isolationDefault")
        if isinstance(isolation, str) and isolation and isolation not in ISOLATION_MODES:
            self.err(file, "FM-ISOLATION", f"isolationDefault {isolation!r} must be one of {', '.join(ISOLATION_MODES)}")
        status = fm.get("status")
        if isinstance(status, str) and status and status not in STATUSES:
            self.err(file, "FM-STATUS", f"status {status!r} must be one of {', '.join(STATUSES)}")
        if model in ("duplicate-master", "hybrid"):
            if not fm.get("masterPageId"):
                self.err(file, "FM-MASTER", f"templateModel {model} requires masterPageId")
            mslug = fm.get("masterPageSlug")
            if not mslug:
                self.err(file, "FM-MASTER", f"templateModel {model} requires masterPageSlug")
            elif not KEBAB.match(str(mslug)):
                self.err(file, "FM-MASTER", f"masterPageSlug {mslug!r} is not lowercase kebab-case (use the leaf slug, e.g. 'mcp', not 'products/mcp'; the folder path goes in the Allowed folders table)")
        extra_types = fm.get("additionalSchemaTypes")
        schema_types: list[str] = [fm["schemaType"]] if isinstance(fm.get("schemaType"), str) and fm["schemaType"] else []
        if extra_types is not None:
            if isinstance(extra_types, str):
                self.err(file, "FM-SCHEMA", "additionalSchemaTypes must be a list ('additionalSchemaTypes:' then '- Type' lines), not a scalar")
            elif not extra_types:
                self.err(file, "FM-SCHEMA", "additionalSchemaTypes is empty; drop the key or list at least one type")
            else:
                for t in extra_types:
                    if not t.strip():
                        self.err(file, "FM-SCHEMA", "additionalSchemaTypes has an empty item")
                    elif t == fm.get("schemaType"):
                        self.err(file, "FM-SCHEMA", f"additionalSchemaTypes repeats schemaType {t!r}")
                    else:
                        schema_types.append(t)
        folders = fm.get("allowedFolders")
        folder_paths: list[str] = []
        if isinstance(folders, str):
            self.err(file, "FM-FOLDERS", "allowedFolders must be a list ('allowedFolders:' then '- /path' lines)")
        elif isinstance(folders, list):
            folder_paths = folders
            for f in folders:
                if not f.startswith("/"):
                    self.err(file, "FM-FOLDERS", f"allowed folder {f!r} must start with '/'")

        sections = parse_sections(body)
        for heading in REQUIRED_HEADINGS:
            if heading not in sections:
                self.err(file, "HEADINGS", f"missing required heading '## {heading}'")

        # Section outline
        outline_names: list[str] = []
        loose_count = 0
        candidate_count = 0
        header, rows = parse_table(sections.get("Section outline", ""))
        if "Section outline" in sections:
            missing = [c for c in OUTLINE_COLUMNS if c not in header]
            if missing:
                self.err(file, "OUTLINE-TABLE", f"section outline table is missing columns: {', '.join(missing)}")
            elif not rows:
                self.err(file, "OUTLINE-TABLE", "section outline table has no rows")
            else:
                for n, row in enumerate(rows, start=1):
                    where = f"section outline row {n}"
                    name = row.get("component name", "").strip()
                    if not name:
                        self.err(file, "OUTLINE-TABLE", f"{where}: Component name is empty")
                        continue
                    if self._check_not_an_id(file, name, where):
                        continue
                    req = row.get("required", "").lower()
                    if req not in ("required", "optional"):
                        self.err(file, "OUTLINE-TABLE", f"{where}: Required must be 'required' or 'optional', got {req!r}")
                    if name == LOOSE:
                        loose_count += 1
                        if model == "component-recipe":
                            self.err(file, "OUTLINE-LOOSE", f"{where}: 'loose' sections are not allowed when templateModel is component-recipe")
                        if not row.get("class path", "").strip():
                            self.err(file, "OUTLINE-LOOSE", f"{where}: a 'loose' row must carry the master's class path in Class path")
                        if row.get("owner", "").strip() != "self":
                            self.err(file, "OUTLINE-LOOSE", f"{where}: a 'loose' row must have Owner 'self', got {row.get('owner', '')!r}")
                        continue
                    if name.startswith(CANDIDATE_PREFIX):
                        candidate_count += 1
                        if not KEBAB.match(name[len(CANDIDATE_PREFIX):]):
                            self.err(file, "OUTLINE-CANDIDATE", f"{where}: candidate placeholder {name!r} must be 'candidate:<kebab-slug>'")
                        if row.get("owner", "").strip() != "self":
                            self.err(file, "OUTLINE-CANDIDATE", f"{where}: a candidate placeholder row must have Owner 'self', got {row.get('owner', '')!r}")
                        if (status or "promoted") == "promoted":
                            self.err(file, "OUTLINE-CANDIDATE", f"{where}: candidate placeholder {name!r} is not allowed in a promoted family; promote the component first")
                        continue
                    if row.get("class path", "").strip():
                        self.err(file, "OUTLINE-TABLE", f"{where}: Class path is only for 'loose' rows; component {name!r} names a component")
                    outline_names.append(name)
                    self._check_owner(file, stem, name, row.get("owner", ""), where)

        # Shell components
        if "Shell components" in sections:
            sheader, srows = parse_table(sections["Shell components"])
            if srows:
                missing = [c for c in SHELL_COLUMNS if c not in sheader]
                if missing:
                    self.err(file, "SHELL-TABLE", f"shell components table is missing columns: {', '.join(missing)}")
                else:
                    for n, row in enumerate(srows, start=1):
                        where = f"shell row {n}"
                        name = row.get("component name", "").strip()
                        if not name:
                            self.err(file, "SHELL-TABLE", f"{where}: Component name is empty")
                            continue
                        if self._check_not_an_id(file, name, where):
                            continue
                        if name == LOOSE:
                            self.err(file, "SHELL-TABLE", f"{where}: shell rows must name a component; 'loose' is only valid in the section outline")
                            continue
                        self._check_owner(file, stem, name, row.get("owner", ""), where)

        # Allowed folders table
        if "Allowed folders" in sections:
            fheader, frows = parse_table(sections["Allowed folders"])
            missing = [c for c in FOLDER_COLUMNS if c not in fheader]
            if missing:
                self.err(file, "FOLDERS-TABLE", f"allowed folders table is missing columns: {', '.join(missing)}")
            else:
                table_paths = {r.get("path", ""): r.get("folder id", "") for r in frows}
                for p in folder_paths:
                    if p not in table_paths:
                        self.err(file, "FOLDERS-TABLE", f"allowed folder {p!r} has no row in the Allowed folders table")
                    elif not table_paths[p]:
                        self.err(file, "FOLDERS-TABLE", f"allowed folder {p!r} has an empty Folder ID (use 'root' for '/')")

        # Example pages
        if "Example pages" in sections:
            eheader, erows = parse_table(sections["Example pages"])
            if erows:
                missing = [c for c in EXAMPLE_COLUMNS if c not in eheader]
                if missing:
                    self.err(file, "EXAMPLES-TABLE", f"example pages table is missing columns: {', '.join(missing)}")
                else:
                    for n, row in enumerate(erows, start=1):
                        pslug = row.get("slug", "")
                        if not pslug or not KEBAB.match(pslug):
                            self.err(file, "EXAMPLES-TABLE", f"example page row {n}: slug {pslug!r} is not lowercase kebab-case")
                        if not row.get("page id"):
                            self.err(file, "EXAMPLES-TABLE", f"example page row {n}: Page ID is empty")

        # Changelog mentions the version
        if "Changelog" in sections and isinstance(version, str) and version:
            if version not in sections["Changelog"]:
                self.err(file, "CHANGELOG", f"changelog does not mention the current version {version}")

        self.families.append({
            "file": file,
            "slug": slug if isinstance(slug, str) else None,
            "version": version if isinstance(version, str) else None,
            "status": status if isinstance(status, str) and status else "promoted",
            "templateModel": model if isinstance(model, str) else None,
            "schemaTypes": schema_types,
            "components": outline_names,
            "looseSections": loose_count,
            "candidateSections": candidate_count,
        })

    def _check_not_an_id(self, file: str, name: str, where: str) -> bool:
        """True (and an error) when a component column carries a Webflow id."""
        if WEBFLOW_ID.search(name):
            self.err(
                file,
                "COMPONENT-ID",
                f"{where}: {name!r} carries a Webflow component id; the catalog names components, "
                "it does not carry their ids. Use the component's exact name and let the run resolve "
                "the id (references/catalog/README.md, 'Components are named')",
            )
            return True
        return False

    def _check_owner(self, file: str, stem: str, name: str, owner: str, where: str) -> None:
        owner = owner.strip()
        if owner == "self":
            if name in self.owned and self.owned[name] != stem:
                self.err(file, "XREF-UNIQUE", f"{where}: component {name!r} is already owned by family {self.owned[name]!r}")
            else:
                self.owned[name] = stem
        elif owner == "shared":
            return
        elif owner and KEBAB.match(owner):
            self.borrowed.append((file, name, owner))
        else:
            self.err(file, "OUTLINE-TABLE", f"{where}: Owner must be 'self', 'shared', or a family slug, got {owner!r}")

    def finish(self, family_slugs: set[str]) -> None:
        for file, name, owner in self.borrowed:
            if owner not in family_slugs:
                self.err(file, "XREF-BORROW", f"component {name!r} is borrowed from unknown family {owner!r}")
            elif self.owned.get(name) != owner:
                self.err(file, "XREF-BORROW", f"component {name!r} is borrowed from {owner!r}, which does not list it as 'self'")


def lint_sync_state(path: str, linter: Linter) -> None:
    file = os.path.basename(path)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        linter.err(file, "SYNC-STATE", f"cannot parse: {exc}")
        return
    if not isinstance(data, dict):
        linter.err(file, "SYNC-STATE", "must be a JSON object")
        return
    for key in ("siteId", "lastSync", "paths"):
        if key not in data:
            linter.err(file, "SYNC-STATE", f"missing key '{key}'")
    if "paths" in data and not isinstance(data["paths"], dict):
        linter.err(file, "SYNC-STATE", "'paths' must be an object keyed by instruction path")


def lint(catalog_dir: str, sync_state: str | None = None) -> dict[str, Any]:
    linter = Linter()
    try:
        names = sorted(os.listdir(catalog_dir))
    except OSError as exc:
        raise ValueError(f"cannot list catalog directory: {exc}")
    for name in names:
        path = os.path.join(catalog_dir, name)
        if os.path.isdir(path) or not name.endswith(".md") or name.lower() == "readme.md":
            continue
        linter.lint_file(path)
    linter.finish({f["slug"] for f in linter.families if f["slug"]})
    if sync_state:
        lint_sync_state(sync_state, linter)
    return {"ok": not linter.errors, "families": linter.families, "errors": linter.errors}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lint webflow-template catalog entries and sync-state.json.")
    parser.add_argument("catalog_dir", help="directory holding <family>.md entries")
    parser.add_argument("--sync-state", help="path to sync-state.json to check")
    args = parser.parse_args(argv)
    try:
        result = lint(args.catalog_dir, args.sync_state)
    except ValueError as exc:
        print(json.dumps({"ok": False, "errors": [{"file": args.catalog_dir, "rule": "READ", "message": str(exc)}]}))
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
