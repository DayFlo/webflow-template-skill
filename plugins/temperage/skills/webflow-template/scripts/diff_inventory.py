#!/usr/bin/env python3
"""Shared-defaults guard: diff a pre-build and a post-build inventory snapshot.

Snapshot shape (both files):
    {
      "styles":     { "<class name>":   <hash string or definition object> },
      "components": { "<component id>": { "name": ..., "base": ..., "props": {...}, "variants": {...}, ... } },
      "variables":  { "<variable id>":  <hash string or definition object> }
    }

Inside a component, the maps "props" and "variants" are compared key by key,
so a variant or prop ADDED by the run counts as created (Adapted sections are
allowed), while a change to a pre-existing variant, prop, or any other field of
a pre-existing component counts as a change to a shared definition. Volatile
bookkeeping fields that every build legitimately moves (instanceCount,
propCount, variantCount, lastUpdated, updatedOn, capturedAt) are ignored inside
component records; inserting an instance of FAQ section is not an edit to it.
The snapshot shape for real inventory data is documented in
references/manifest-schema.md ("Snapshot shape").

Verdict: "pass" when nothing pre-existing changed or disappeared; otherwise
"fail". Accepted deviations (--accept kind:key) are reported separately and do
not fail the verdict. Exit 0 on pass, 1 on fail, 2 on unreadable input.

Usage:
    diff_inventory.py pre.json post.json [--accept styles:hero_title] [--accept variant:comp1/dark]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from typing import Any

TOP_KINDS = ("styles", "components", "variables")
COMPONENT_SUBMAPS = {"props": "prop", "variants": "variant"}
VOLATILE_COMPONENT_FIELDS = frozenset({"instanceCount", "propCount", "variantCount", "lastUpdated", "updatedOn", "capturedAt"})


def canonical_hash(value: Any) -> str:
    """Stable hash for a definition: strings are hashed as-is, objects via sorted JSON."""
    if isinstance(value, str):
        payload = value
    else:
        payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _as_map(snapshot: dict[str, Any], kind: str) -> dict[str, Any]:
    value = snapshot.get(kind, {})
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"snapshot field '{kind}' must be an object keyed by name or id")
    return value


def _diff_component(cid: str, pre: Any, post: Any, out: dict[str, list]) -> None:
    """Compare one pre-existing component, treating props and variants as sub-maps."""
    if not isinstance(pre, dict) or not isinstance(post, dict):
        if canonical_hash(pre) != canonical_hash(post):
            out["changedPreExisting"].append({"kind": "components", "key": cid, "preHash": canonical_hash(pre), "postHash": canonical_hash(post)})
        return
    # everything except the sub-maps and the volatile counters is the component's own definition
    pre_core = {k: v for k, v in pre.items() if k not in COMPONENT_SUBMAPS and k not in VOLATILE_COMPONENT_FIELDS}
    post_core = {k: v for k, v in post.items() if k not in COMPONENT_SUBMAPS and k not in VOLATILE_COMPONENT_FIELDS}
    if canonical_hash(pre_core) != canonical_hash(post_core):
        changed_fields = sorted(k for k in set(pre_core) | set(post_core) if canonical_hash(pre_core.get(k)) != canonical_hash(post_core.get(k)))
        out["changedPreExisting"].append({"kind": "components", "key": cid, "fields": changed_fields, "preHash": canonical_hash(pre_core), "postHash": canonical_hash(post_core)})
    for submap, kind in COMPONENT_SUBMAPS.items():
        pre_sub = pre.get(submap) or {}
        post_sub = post.get(submap) or {}
        if not isinstance(pre_sub, dict) or not isinstance(post_sub, dict):
            raise ValueError(f"components['{cid}'].{submap} must be an object keyed by id or name")
        for key in sorted(set(pre_sub) | set(post_sub)):
            full = f"{cid}/{key}"
            if key in pre_sub and key not in post_sub:
                out["removed"].append({"kind": kind, "key": full})
            elif key in post_sub and key not in pre_sub:
                out["created"].append({"kind": kind, "key": full})
            elif canonical_hash(pre_sub[key]) != canonical_hash(post_sub[key]):
                out["changedPreExisting"].append({"kind": kind, "key": full, "preHash": canonical_hash(pre_sub[key]), "postHash": canonical_hash(post_sub[key])})


def diff(pre: dict[str, Any], post: dict[str, Any], accept: list[str] | None = None) -> dict[str, Any]:
    """Compute the guard verdict. Raises ValueError on malformed snapshots."""
    if not isinstance(pre, dict) or not isinstance(post, dict):
        raise ValueError("snapshots must be JSON objects")
    out: dict[str, Any] = {"changedPreExisting": [], "created": [], "removed": []}
    for kind in TOP_KINDS:
        pre_map = _as_map(pre, kind)
        post_map = _as_map(post, kind)
        for key in sorted(set(pre_map) | set(post_map)):
            if key in pre_map and key not in post_map:
                out["removed"].append({"kind": kind, "key": key})
            elif key in post_map and key not in pre_map:
                out["created"].append({"kind": kind, "key": key})
            elif kind == "components":
                _diff_component(key, pre_map[key], post_map[key], out)
            elif canonical_hash(pre_map[key]) != canonical_hash(post_map[key]):
                out["changedPreExisting"].append({"kind": kind, "key": key, "preHash": canonical_hash(pre_map[key]), "postHash": canonical_hash(post_map[key])})

    accepted_set = set(accept or [])
    accepted: list[dict[str, Any]] = []
    remaining_changed = []
    for entry in out["changedPreExisting"]:
        if f"{entry['kind']}:{entry['key']}" in accepted_set:
            accepted.append({**entry, "accepted": True})
        else:
            remaining_changed.append(entry)
    remaining_removed = []
    for entry in out["removed"]:
        if f"{entry['kind']}:{entry['key']}" in accepted_set:
            accepted.append({**entry, "accepted": True})
        else:
            remaining_removed.append(entry)

    verdict = "pass" if not remaining_changed and not remaining_removed else "fail"
    return {
        "verdict": verdict,
        "changedPreExisting": remaining_changed,
        "created": out["created"],
        "removed": remaining_removed,
        "acceptedDeviations": accepted,
        "counts": {
            "changedPreExisting": len(remaining_changed),
            "created": len(out["created"]),
            "removed": len(remaining_removed),
            "accepted": len(accepted),
        },
    }


def _load(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pre/post inventory diff; fails when any pre-existing style, component, or variable definition changed.")
    parser.add_argument("pre", help="pre-build snapshot JSON")
    parser.add_argument("post", help="post-build snapshot JSON")
    parser.add_argument("--accept", action="append", default=[], metavar="KIND:KEY", help="accept a deviation (e.g. styles:hero_title, variant:comp1/dark); repeatable")
    args = parser.parse_args(argv)
    try:
        pre = _load(args.pre)
        post = _load(args.post)
        result = diff(pre, post, accept=args.accept)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"verdict": "error", "message": str(exc)}))
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result["verdict"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
