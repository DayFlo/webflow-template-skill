#!/usr/bin/env python3
"""Run manifest helper for the webflow-template skill.

Subcommands:
    create     write a new manifest (references/manifest-schema.md)
    append     append a step; ids of executed steps (ok, failed) merge into "created",
               skipped steps (dry run, or already done on resume) record nothing
    set        update status, guard verdict, snapshot hashes, accepted deviations
    summarize  print a JSON summary
    ships      print the ships-at-next-publish and already-public lists

Standard library only. All output is JSON. Exit 0 on success, 1 on a rule
violation or malformed manifest, 2 on unreadable input.
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
import sys
from typing import Any

SURFACES = ("claude-ai", "claude-code", "codex")
TEMPLATE_MODELS = ("duplicate-master", "component-recipe", "hybrid")
ISOLATION_MODES = ("draft-main", "branch")
STATUSES = ("open", "verified", "failed", "cleaned")
STEP_STATUSES = ("ok", "failed", "skipped")
SCALAR_IDS = ("pageId", "branchId")
LIST_IDS = ("componentIds", "styleNames", "variableIds", "assetIds", "instructionPaths")
REQUIRED_KEYS = ("runId", "slug", "startedAt", "surface", "site", "family", "familyVersion", "templateModel", "isolationMode", "briefHash", "steps", "created", "status")


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def brief_hash(brief: Any) -> str:
    payload = json.dumps(brief, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def empty_created() -> dict[str, Any]:
    created: dict[str, Any] = {k: None for k in SCALAR_IDS}
    created.update({k: [] for k in LIST_IDS})
    return created


def create(*, slug: str, surface: str, site_id: str, family: str, family_version: str, template_model: str, isolation_mode: str,
           brief_hash_value: str, site_short_name: str | None = None, run_id: str | None = None, started_at: str | None = None) -> dict[str, Any]:
    if surface not in SURFACES:
        raise ValueError(f"surface must be one of {', '.join(SURFACES)}")
    if template_model not in TEMPLATE_MODELS:
        raise ValueError(f"template model must be one of {', '.join(TEMPLATE_MODELS)}")
    if isolation_mode not in ISOLATION_MODES:
        raise ValueError(f"isolation mode must be one of {', '.join(ISOLATION_MODES)}")
    started = started_at or now_iso()
    return {
        "runId": run_id or f"{started[:10]}-{slug}",
        "slug": slug,
        "startedAt": started,
        "surface": surface,
        "site": {"id": site_id, "shortName": site_short_name},
        "family": family,
        "familyVersion": family_version,
        "templateModel": template_model,
        "isolationMode": isolation_mode,
        "briefHash": brief_hash_value,
        "steps": [],
        "created": empty_created(),
        "preSnapshotHash": None,
        "postSnapshotHash": None,
        "guardVerdict": None,
        "acceptedDeviations": [],
        "publishActions": [],
        "status": "open",
    }


def validate_manifest(manifest: Any) -> list[str]:
    errors = []
    if not isinstance(manifest, dict):
        return ["manifest must be a JSON object"]
    for key in REQUIRED_KEYS:
        if key not in manifest:
            errors.append(f"missing required field '{key}'")
    if manifest.get("status") not in STATUSES:
        errors.append(f"status must be one of {', '.join(STATUSES)}")
    if not isinstance(manifest.get("steps"), list):
        errors.append("steps must be an array")
    if not isinstance(manifest.get("created"), dict):
        errors.append("created must be an object")
    if manifest.get("isolationMode") not in ISOLATION_MODES:
        errors.append(f"isolationMode must be one of {', '.join(ISOLATION_MODES)}")
    return errors


def append(manifest: dict[str, Any], *, tool: str, action: str, status: str = "ok", ids: dict[str, Any] | None = None,
           note: str = "", at: str | None = None) -> tuple[dict[str, Any], list[str]]:
    """Append a step. Returns (step, violations). Violations do not block recording."""
    if status not in STEP_STATUSES:
        raise ValueError(f"step status must be one of {', '.join(STEP_STATUSES)}")
    ids = ids or {}
    if not isinstance(ids, dict):
        raise ValueError("ids must be a JSON object")
    steps = manifest.setdefault("steps", [])
    step = {"seq": len(steps) + 1, "at": at or now_iso(), "tool": tool, "action": action, "ids": ids, "status": status, "note": note}
    steps.append(step)

    # A skipped step did not run in this call (dry run, or a step already completed
    # before an interruption whose ids are in "created" from the original append),
    # so it must not add to "created" or "publishActions". Failed steps do merge:
    # a create that errored may still have left a resource behind, and cleanup
    # reconciles "created" against the live site before deleting anything.
    created = manifest.setdefault("created", empty_created())
    executed = status != "skipped"
    if executed:
        for key in SCALAR_IDS:
            if ids.get(key):
                created[key] = ids[key]
        for key in LIST_IDS:
            values = ids.get(key)
            if isinstance(values, str):
                values = [values]
            if isinstance(values, list):
                bucket = created.setdefault(key, [])
                for v in values:
                    if v not in bucket:
                        bucket.append(v)

    violations: list[str] = []
    if action in ("publish_site", "publish_branch"):
        if executed:
            manifest.setdefault("publishActions", []).append({"seq": step["seq"], "action": action, "at": step["at"], "note": note})
        if action == "publish_site":
            violations.append("rule 8: publish_site must never be called; the action has been recorded")
        elif manifest.get("isolationMode") != "branch":
            violations.append("rule 8: publish_branch is only allowed in branch mode; the action has been recorded")
    return step, violations


def set_fields(manifest: dict[str, Any], *, status: str | None = None, guard_verdict: Any = None, pre_hash: str | None = None,
               post_hash: str | None = None, accept: list[str] | None = None) -> None:
    if status is not None:
        if status not in STATUSES:
            raise ValueError(f"status must be one of {', '.join(STATUSES)}")
        manifest["status"] = status
    if guard_verdict is not None:
        manifest["guardVerdict"] = guard_verdict
    if pre_hash is not None:
        manifest["preSnapshotHash"] = pre_hash
    if post_hash is not None:
        manifest["postSnapshotHash"] = post_hash
    for entry in accept or []:
        bucket = manifest.setdefault("acceptedDeviations", [])
        if entry not in bucket:
            bucket.append(entry)


def summarize(manifest: dict[str, Any]) -> dict[str, Any]:
    steps = manifest.get("steps", [])
    by_status = {s: 0 for s in STEP_STATUSES}
    for step in steps:
        by_status[step.get("status", "ok")] = by_status.get(step.get("status", "ok"), 0) + 1
    created = manifest.get("created", {})
    verdict = manifest.get("guardVerdict")
    return {
        "runId": manifest.get("runId"),
        "slug": manifest.get("slug"),
        "family": f"{manifest.get('family')}@{manifest.get('familyVersion')}",
        "templateModel": manifest.get("templateModel"),
        "isolationMode": manifest.get("isolationMode"),
        "surface": manifest.get("surface"),
        "startedAt": manifest.get("startedAt"),
        "status": manifest.get("status"),
        "steps": {"total": len(steps), **by_status},
        "lastStep": ({"seq": steps[-1].get("seq"), "action": steps[-1].get("action"), "status": steps[-1].get("status")} if steps else None),
        "created": {k: (v if k in SCALAR_IDS else len(v or [])) for k, v in created.items()},
        "guardVerdict": (verdict.get("verdict") if isinstance(verdict, dict) else "not run"),
        "publishActions": len(manifest.get("publishActions", [])),
        "acceptedDeviations": len(manifest.get("acceptedDeviations", [])),
    }


def ships(manifest: dict[str, Any]) -> dict[str, Any]:
    created = manifest.get("created", {})
    mode = manifest.get("isolationMode")
    items: list[dict[str, str]] = []
    if mode == "draft-main":
        for cid in created.get("componentIds", []) or []:
            items.append({"kind": "component", "id": cid})
        for name in created.get("styleNames", []) or []:
            items.append({"kind": "style", "id": name})
        for vid in created.get("variableIds", []) or []:
            items.append({"kind": "variable", "id": vid})
        note = "These go live site-wide at the next publish even though the page stays a draft." if items else "Nothing new ships at the next publish; the page stays a draft."
    else:
        note = f"Isolated on branch {created.get('branchId') or '(unknown)'} until merged; nothing ships at the next publish of main."
    # Uploaded assets are not on the ships list because they do not wait for a
    # publish: Webflow serves library assets from a public CDN URL from the
    # moment of upload (references/rules.md rule 19). They are reported
    # separately, in both isolation modes, because the asset library is
    # site-level and a branch does not isolate it.
    public = [{"kind": "asset", "id": aid} for aid in created.get("assetIds", []) or []]
    public_note = (
        "Already public: these files are served from Webflow's public CDN from the moment of "
        "upload, before any publish and whether or not the page is ever published. A branch does "
        "not isolate them, and deleting an asset later does not un-serve a URL someone already has."
        if public else
        "Nothing was uploaded: every image came from the existing asset library."
    )
    return {"isolationMode": mode, "shipsAtNextPublish": items, "note": note,
            "alreadyPublic": public, "alreadyPublicNote": public_note}


# ---------------------------------------------------------------- CLI plumbing

def _load(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _save(path: str, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")


def _emit(data: Any) -> None:
    print(json.dumps(data, indent=2))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create, append to, and summarize a webflow-template run manifest.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("create", help="create a new manifest")
    p.add_argument("--slug", required=True)
    p.add_argument("--surface", required=True, choices=SURFACES)
    p.add_argument("--site-id", required=True)
    p.add_argument("--site-short-name")
    p.add_argument("--family", required=True)
    p.add_argument("--family-version", required=True)
    p.add_argument("--template-model", required=True, choices=TEMPLATE_MODELS)
    p.add_argument("--isolation-mode", required=True, choices=ISOLATION_MODES)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--brief", help="brief JSON to hash")
    g.add_argument("--brief-hash", help="precomputed sha256:<hex>")
    p.add_argument("--run-id")
    p.add_argument("--started-at")
    p.add_argument("-o", "--out", help="write here instead of stdout")

    p = sub.add_parser("append", help="append a step (updates the file in place)")
    p.add_argument("manifest")
    p.add_argument("--tool", required=True)
    p.add_argument("--action", required=True)
    p.add_argument("--status", default="ok", choices=STEP_STATUSES)
    p.add_argument("--ids", default="{}", help='JSON object, e.g. \'{"pageId": "..."}\'')
    p.add_argument("--note", default="")
    p.add_argument("--at")

    p = sub.add_parser("set", help="update manifest fields in place")
    p.add_argument("manifest")
    p.add_argument("--status", choices=STATUSES)
    p.add_argument("--guard-verdict", help="path to a diff_inventory.py output file, or inline JSON")
    p.add_argument("--pre-snapshot-hash")
    p.add_argument("--post-snapshot-hash")
    p.add_argument("--accept-deviation", action="append", default=[], metavar="KIND:KEY")

    p = sub.add_parser("summarize", help="print a summary")
    p.add_argument("manifest")

    p = sub.add_parser("ships", help="print the ships-at-next-publish and already-public lists")
    p.add_argument("manifest")

    args = parser.parse_args(argv)

    try:
        if args.command == "create":
            if args.brief:
                bh = brief_hash(_load(args.brief))
            else:
                bh = args.brief_hash
            manifest = create(slug=args.slug, surface=args.surface, site_id=args.site_id, family=args.family, family_version=args.family_version,
                              template_model=args.template_model, isolation_mode=args.isolation_mode, brief_hash_value=bh,
                              site_short_name=args.site_short_name, run_id=args.run_id, started_at=args.started_at)
            if args.out:
                _save(args.out, manifest)
                _emit({"ok": True, "runId": manifest["runId"], "path": args.out})
            else:
                _emit(manifest)
            return 0

        manifest = _load(args.manifest)
        errors = validate_manifest(manifest)
        if errors:
            _emit({"ok": False, "errors": errors})
            return 1

        if args.command == "append":
            ids = json.loads(args.ids)
            step, violations = append(manifest, tool=args.tool, action=args.action, status=args.status, ids=ids, note=args.note, at=args.at)
            _save(args.manifest, manifest)
            _emit({"ok": not violations, "step": step, "violations": violations})
            return 1 if violations else 0

        if args.command == "set":
            verdict = None
            if args.guard_verdict:
                try:
                    verdict = _load(args.guard_verdict)
                except OSError:
                    verdict = json.loads(args.guard_verdict)
            set_fields(manifest, status=args.status, guard_verdict=verdict, pre_hash=args.pre_snapshot_hash, post_hash=args.post_snapshot_hash, accept=args.accept_deviation)
            _save(args.manifest, manifest)
            _emit({"ok": True, "status": manifest["status"]})
            return 0

        if args.command == "summarize":
            _emit(summarize(manifest))
            return 0

        if args.command == "ships":
            _emit(ships(manifest))
            return 0
    except (OSError, json.JSONDecodeError) as exc:
        _emit({"ok": False, "error": f"cannot read input: {exc}"})
        return 2
    except ValueError as exc:
        _emit({"ok": False, "error": str(exc)})
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
