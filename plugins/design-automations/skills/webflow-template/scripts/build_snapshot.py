#!/usr/bin/env python3
"""Build a guard snapshot (references/manifest-schema.md, "Snapshot shape") from
saved Webflow MCP tool results.

On a site of any size, get_all_components, get_variables, and query_styles
return tens to hundreds of kilobytes, which a chat client saves to files rather
than showing inline; assembling the snapshot by hand from those files is slow
and error-prone. This script does the mapping mechanically:

    build_snapshot.py --site-id ID
        --components components.txt [--expand-components id,id,...]
        --variables variables.txt [--variables more.txt]
        --styles styles.txt --classes l-section,c-button,...
        [--scope-note KIND=TEXT]... [--captured-at ISO] -o snapshot.json

Input files are the saved tool results, in any of the shapes the client writes:
a JSON array of {"type": "text", "text": "<json>"} items, a single JSON object,
or text with a JSON object after a preamble. Each embedded object is a tool
action result ({"label", "action", "result"}); several files or several actions
per file are merged.

Mapping (manifest-schema.md):
- components: every component gets name, group, description; the ids in
  --expand-components also get props keyed by prop id (name, type, group) and
  variants keyed by variant name with the value "present". instanceCount and
  other volatile counters are never copied.
- variables: id -> name, type, cssName, collection, value, modeValues. The
  collection id is taken from the cssName prefix when the tool does not return
  it (--color--- -> the id passed with --collection-map), else null.
- styles: only non-combo (global) classes whose name is in --classes are kept,
  keyed by class name, value {"properties": <the tool's properties object>}.
  Padding queries and combo classes are ignored. A class in --classes that no
  query returned is recorded as "missing" so the guard sees it.

Prints {"ok": true, "path": ..., "sha256": "sha256:<hex>", "counts": {...}}.
Standard library only. Exit 0 on success, 2 on unreadable input.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from typing import Any, Iterable


def _iter_action_results(path: str) -> Iterable[dict[str, Any]]:
    """Yield every {"label","action","result"} object found in a saved tool result."""
    with open(path, "r", encoding="utf-8") as fh:
        raw = fh.read()
    stripped = raw.lstrip()
    parsed: Any = None
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        # a preamble line before the JSON: start at the first array or object
        starts = [i for i in (stripped.find("["), stripped.find("{")) if i >= 0]
        if not starts:
            raise ValueError(f"{path}: no JSON found")
        parsed = json.loads(stripped[min(starts):])
    items = parsed if isinstance(parsed, list) else [parsed]
    for item in items:
        if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str):
            text = item["text"]
            start = text.find("{")
            if start < 0:
                continue
            inner = json.loads(text[start:])
            if isinstance(inner, list):
                for sub in inner:
                    if isinstance(sub, dict):
                        yield sub
            elif isinstance(inner, dict):
                yield inner
        elif isinstance(item, dict):
            yield item


def _results(paths: list[str], action: str) -> list[Any]:
    out: list[Any] = []
    for path in paths:
        for obj in _iter_action_results(path):
            if obj.get("error"):
                raise ValueError(f"{path}: action {obj.get('action')} returned an error: {obj['error']}")
            if obj.get("action") == action or ("result" in obj and action is None):
                out.append(obj.get("result"))
    return out


def components_snapshot(paths: list[str], expand: set[str]) -> dict[str, Any]:
    snap: dict[str, Any] = {}
    for result in _results(paths, "get_all_components"):
        comps = result if isinstance(result, list) else (result or {}).get("components", [])
        for c in comps:
            cid = c.get("id")
            if not cid:
                continue
            rec: dict[str, Any] = {"name": c.get("name"), "group": c.get("group"), "description": c.get("description")}
            if cid in expand:
                props: dict[str, Any] = {}
                for p in c.get("props") or []:
                    if p.get("id"):
                        props[p["id"]] = {"name": p.get("name"), "type": p.get("type"), "group": p.get("group")}
                variants: dict[str, str] = {}
                for v in c.get("variants") or []:
                    if v.get("name"):
                        variants[v["name"]] = "present"
                rec["props"] = props
                rec["variants"] = variants
            snap[cid] = rec
    return snap


def variables_snapshot(paths: list[str], collection_map: dict[str, str]) -> dict[str, Any]:
    snap: dict[str, Any] = {}
    for result in _results(paths, "get_variables"):
        variables = result if isinstance(result, list) else (result or {}).get("variables", [])
        for v in variables:
            vid = v.get("id")
            if not vid:
                continue
            css = v.get("cssName") or ""
            collection = v.get("collection") or v.get("collectionId")
            if not collection:
                for prefix, cid in collection_map.items():
                    if css.startswith(prefix):
                        collection = cid
                        break
            snap[vid] = {"name": v.get("name"), "type": v.get("type"), "cssName": css, "collection": collection,
                         "value": v.get("value"), "modeValues": v.get("modeValues")}
    return snap


def styles_snapshot(paths: list[str], classes: list[str]) -> dict[str, Any]:
    wanted = set(classes)
    snap: dict[str, Any] = {}
    for result in _results(paths, "query_styles"):
        groups = result if isinstance(result, list) else [result]
        for group in groups:
            for match in (group or {}).get("matches", []) or []:
                if match.get("isComboClass"):
                    continue
                name = match.get("name")
                if name in wanted and name not in snap:
                    snap[name] = {"properties": match.get("properties") or {}}
    for name in classes:
        snap.setdefault(name, "missing")
    return snap


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        h.update(fh.read())
    return "sha256:" + h.hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a guard snapshot from saved Webflow MCP tool results.")
    parser.add_argument("--site-id", required=True)
    parser.add_argument("--components", action="append", default=[], help="saved get_all_components result (repeatable)")
    parser.add_argument("--expand-components", default="", help="comma-separated component ids whose props and variants are expanded")
    parser.add_argument("--variables", action="append", default=[], help="saved get_variables result (repeatable)")
    parser.add_argument("--collection-map", action="append", default=[], metavar="CSSPREFIX=COLLECTIONID",
                        help="map a cssName prefix to a collection id, e.g. --color---=collection-<id>")
    parser.add_argument("--styles", action="append", default=[], help="saved query_styles result (repeatable)")
    parser.add_argument("--classes", default="", help="comma-separated class names to keep from the style results")
    parser.add_argument("--scope-note", action="append", default=[], metavar="KIND=TEXT")
    parser.add_argument("--captured-at")
    parser.add_argument("-o", "--out", required=True)
    args = parser.parse_args(argv)

    try:
        expand = {x for x in args.expand_components.split(",") if x}
        cmap = dict(x.split("=", 1) for x in args.collection_map if "=" in x)
        classes = [x for x in args.classes.split(",") if x]
        scope = {"styles": "", "components": "", "variables": ""}
        for note in args.scope_note:
            if "=" in note:
                k, v = note.split("=", 1)
                scope[k] = v
        snapshot = {
            "capturedAt": args.captured_at or dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "siteId": args.site_id,
            "scope": scope,
            "styles": styles_snapshot(args.styles, classes) if args.styles else {},
            "components": components_snapshot(args.components, expand) if args.components else {},
            "variables": variables_snapshot(args.variables, cmap) if args.variables else {},
        }
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(snapshot, fh, indent=2, sort_keys=True)
        fh.write("\n")
    missing = [k for k, v in snapshot["styles"].items() if v == "missing"]
    print(json.dumps({"ok": True, "path": args.out, "sha256": sha256_file(args.out),
                      "counts": {"styles": len(snapshot["styles"]), "components": len(snapshot["components"]), "variables": len(snapshot["variables"])},
                      "missingClasses": missing}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
