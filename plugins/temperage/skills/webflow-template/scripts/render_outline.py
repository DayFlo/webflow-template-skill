#!/usr/bin/env python3
"""Render the visual outline (references/outline-spec.md) from a brief.

Input: brief JSON. Output: one self-contained HTML file on stdout (or -o),
inline CSS and JS, no external assets. Uses assets/outline.template.html when
present (placeholders like {{FRAMES}}), otherwise an embedded fallback
template, so the script also works when copied on its own.

Usage:
    render_outline.py brief.json [-o outline.html] [--template path.html]

Exit 0 on success, 2 when the brief cannot be read or is not an object.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import os
import re
import sys
from typing import Any

BREAKPOINTS = (
    ("desktop", "Desktop", "992 and up"),
    ("991", "Tablet", "991"),
    ("767", "Mobile landscape", "767"),
    ("479", "Mobile portrait", "479"),
)
REUSE_LABEL = {"reused": "Reused", "adapted": "Adapted", "new": "New"}
PREVIEW_CHARS = 80

FALLBACK_TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{TITLE}}</title>
<style>
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;margin:0;padding:24px;background:#f6f6f4;color:#1c1c1a}
h1{font-size:22px;margin:0 0 4px}h2{font-size:16px;margin:32px 0 8px}
.meta{color:#5a5a55;font-size:13px}
.frames{display:grid;grid-template-columns:1440fr 991fr 767fr 479fr;gap:12px;margin-top:16px}
.frame{background:#fff;border:1px solid #d9d9d4;border-radius:6px;padding:8px;min-width:0}
.frame h3{font-size:12px;margin:0 0 8px;color:#5a5a55;font-weight:600}
.section{border-top:1px solid #e6e6e1;padding:8px 0}.section:first-of-type{border-top:0}
.pill{display:inline-block;font-size:10px;padding:1px 6px;border-radius:9px;border:1px solid transparent;vertical-align:middle}
.pill-reused{background:#e3f4e8;color:#1d6b35}.pill-adapted{background:#fdf1d8;color:#8a5a00}.pill-new{background:#ece4fb;color:#5a2ea6}
.pill-final{background:#e3f4e8;color:#1d6b35}.pill-draft{background:#fdf1d8;color:#8a5a00}.pill-missing{background:#fbe3e1;color:#a12a22}.pill-manual{background:#e6e6f5;color:#3b3b7a}
.cols{display:grid;gap:4px;margin:6px 0}.col{background:#eeeeea;border:1px dashed #c8c8c2;height:26px;border-radius:3px}
.slot{font-size:11px;margin:2px 0}.slot-content{color:#5a5a55}
.bp-767 .slot-content,.bp-479 .slot-content{display:none}
table{border-collapse:collapse;width:100%;font-size:13px;background:#fff}th,td{border:1px solid #d9d9d4;padding:6px 8px;text-align:left;vertical-align:top}
.open{background:#fdf1d8}.controls button{margin-right:6px}
.hidden{display:none}
footer{margin-top:32px;font-size:12px;color:#5a5a55}
</style></head><body>
{{HEADER}}
<div class="controls" id="controls"></div>
<div class="frames" id="frames">{{FRAMES}}</div>
<h2>Section mapping</h2>{{MAPPING}}
<h2>Decisions</h2>{{DECISIONS}}
<h2>Token substitutions</h2>{{TOKENS}}
<h2>Manual handoff</h2>{{HANDOFF}}
<footer>Generated {{GENERATED_AT}} · brief {{BRIEF_HASH}} · no external assets</footer>
<script>{{SCRIPT}}</script>
</body></html>
"""

TOGGLE_SCRIPT = """(function(){
var frames=document.querySelectorAll('.frame');var wrap=document.getElementById('frames');var ctl=document.getElementById('controls');
var names=[['all','All'],['desktop','Desktop'],['991','Tablet 991'],['767','Mobile L 767'],['479','Mobile P 479']];
names.forEach(function(n){var b=document.createElement('button');b.textContent=n[1];b.onclick=function(){show(n[0]);};ctl.appendChild(b);});
function show(which){frames.forEach(function(f){var bp=f.getAttribute('data-bp');f.classList.toggle('hidden',!(which==='all'||which===bp));});
wrap.style.gridTemplateColumns=(which==='all')?'1440fr 991fr 767fr 479fr':'1fr';}
})();"""


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def brief_hash(brief: Any) -> str:
    payload = json.dumps(brief, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def columns_at(section: dict[str, Any], bp: str) -> int:
    layout = section.get("layout") or {}
    try:
        cols = int(layout.get("columns", 1))
    except (TypeError, ValueError):
        cols = 1
    cols = max(1, min(6, cols))
    if bp == "desktop":
        return cols
    overrides = layout.get("breakpoints") or {}
    if str(bp) in overrides:
        try:
            return max(1, min(6, int(overrides[str(bp)])))
        except (TypeError, ValueError):
            pass
    if bp in ("991", "767"):
        return min(cols, 2)
    return 1


def sorted_sections(brief: dict[str, Any]) -> list[dict[str, Any]]:
    sections = [s for s in brief.get("sections", []) if isinstance(s, dict)]
    return sorted(sections, key=lambda s: (s.get("order") if isinstance(s.get("order"), int) else 10**6))


def component_line(section: dict[str, Any]) -> str:
    level = section.get("reuseLevel")
    if level == "new":
        spec = section.get("newComponentSpec") or {}
        return f"{esc(spec.get('name') or 'new component')} · candidate"
    # loose sections show the master's class path; everything else shows the
    # component name (the catalog key; ids never reach the brief).
    name = section.get("classPath") or section.get("componentName") or "component"
    parts = [esc(name)]
    if section.get("variant"):
        parts.append(f"variant {esc(section['variant'])}")
    if level == "adapted":
        adaptation = section.get("adaptation") or {}
        if adaptation.get("newVariant"):
            parts.append(f"new variant {esc(adaptation['newVariant'])}")
        if adaptation.get("newProps"):
            parts.append("new props " + esc(", ".join(str(p) for p in adaptation["newProps"])))
    return " · ".join(parts)


def render_section(section: dict[str, Any], bp: str) -> str:
    level = section.get("reuseLevel", "reused")
    label = REUSE_LABEL.get(level, esc(level))
    cols = columns_at(section, bp)
    boxes = "".join('<div class="col"></div>' for _ in range(cols))
    slots_html = []
    for slot in section.get("slots", []) or []:
        if not isinstance(slot, dict):
            continue
        status = slot.get("status", "missing")
        if status == "missing":
            preview = f"TODO: {esc(slot.get('name'))}"
        elif status == "manual":
            content = str(slot.get("content") or "")
            preview = ("publisher enters in the Designer: "
                       + esc(content[:PREVIEW_CHARS] + ("…" if len(content) > PREVIEW_CHARS else "")))
        else:
            content = str(slot.get("content") or "")
            preview = esc(content[:PREVIEW_CHARS] + ("…" if len(content) > PREVIEW_CHARS else ""))
        slots_html.append(
            f'<div class="slot"><strong>{esc(slot.get("name"))}</strong> '
            f'<span class="pill pill-{esc(status)}">{esc(status)}</span> '
            f'<span class="slot-content">{preview}</span></div>'
        )
    images = [i for i in (section.get("images") or []) if isinstance(i, dict)]
    img_line = ""
    if images:
        alt_ok = all(str(i.get("alt") or "").strip() for i in images)
        img_line = f'<div class="slot">{len(images)} image{"s" if len(images) != 1 else ""} · {"alt ok" if alt_ok else "alt missing"}</div>'
    from_line = f'<div class="slot meta">from: {esc(section["designSection"])}</div>' if section.get("designSection") else ""
    return (
        f'<div class="section">'
        f'<div><strong>#{esc(section.get("order"))} {esc(section.get("familySection"))}</strong> '
        f'<span class="pill pill-{esc(level)}">{label}</span></div>'
        f'<div class="meta">{component_line(section)}</div>'
        f'<div class="cols" style="grid-template-columns:repeat({cols},1fr)">{boxes}</div>'
        f'{"".join(slots_html)}{img_line}{from_line}'
        f'</div>'
    )


def render_frames(brief: dict[str, Any]) -> str:
    sections = sorted_sections(brief)
    frames = []
    for bp, label, width in BREAKPOINTS:
        body = "".join(render_section(s, bp) for s in sections)
        frames.append(f'<div class="frame bp-{bp}" data-bp="{bp}"><h3>{label} ({width})</h3>{body}</div>')
    return "".join(frames)


def render_header(brief: dict[str, Any]) -> str:
    page = brief.get("page") or {}
    folder = page.get("folder") or {}
    approved = brief.get("approvedAt")
    status = f"Approved {esc(approved)}" if approved else "Not yet approved"
    return (
        f'<h1>{esc(page.get("title") or "Untitled page")}</h1>'
        f'<div class="meta">{esc(brief.get("family"))}@{esc(brief.get("familyVersion"))} · '
        f'{esc(brief.get("templateModel"))} · {esc(brief.get("isolationMode"))}</div>'
        f'<div class="meta">slug <code>{esc(page.get("slug"))}</code> · folder <code>{esc(folder.get("path") or "/")}</code>'
        f'{" · site " + esc(brief["site"].get("shortName") or brief["site"].get("id")) if isinstance(brief.get("site"), dict) else ""}</div>'
        f'<div class="meta">{status}</div>'
    )


def render_mapping(brief: dict[str, Any]) -> str:
    rows = []
    for s in sorted_sections(brief):
        slots = [x for x in (s.get("slots") or []) if isinstance(x, dict)]
        counts = {k: sum(1 for x in slots if x.get("status") == k) for k in ("final", "draft", "missing", "manual")}
        rows.append(
            f'<tr><td>{esc(s.get("order"))}</td><td>{esc(s.get("designSection") or "")}</td><td>{esc(s.get("familySection"))}</td>'
            f'<td>{component_line(s)}</td><td><span class="pill pill-{esc(s.get("reuseLevel"))}">{REUSE_LABEL.get(s.get("reuseLevel"), esc(s.get("reuseLevel")))}</span></td>'
            f'<td>{counts["final"]} / {counts["draft"]} / {counts["missing"]} / {counts["manual"]}</td><td>{len(s.get("images") or [])}</td></tr>'
        )
    return (
        '<table><thead><tr><th>#</th><th>Design section</th><th>Family section</th><th>Component / variant</th>'
        '<th>Reuse</th><th>Slots final / draft / missing / manual</th><th>Images</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table>'
    )


def render_decisions(brief: dict[str, Any]) -> str:
    decisions = [d for d in (brief.get("decisions") or []) if isinstance(d, dict)]
    if not decisions:
        return '<p class="meta">No open decisions.</p>'
    ordered = sorted(decisions, key=lambda d: 0 if d.get("status") == "open" else 1)
    rows = []
    for d in ordered:
        cls = ' class="open"' if d.get("status") == "open" else ""
        rows.append(f'<tr{cls}><td>{esc(d.get("id"))}</td><td>{esc(d.get("status"))}</td><td>{esc(d.get("question"))}</td><td>{esc(d.get("resolution") or "")}</td></tr>')
    return f'<table><thead><tr><th>ID</th><th>Status</th><th>Question</th><th>Resolution</th></tr></thead><tbody>{"".join(rows)}</tbody></table>'


def render_tokens(brief: dict[str, Any]) -> str:
    tokens = brief.get("tokens") or {}
    subs = [t for t in (tokens.get("substitutions") or []) if isinstance(t, dict)]
    unresolved = [t for t in (tokens.get("unresolved") or []) if isinstance(t, dict)]
    parts = []
    if subs:
        rows = "".join(f'<tr><td>{esc(t.get("observed"))}</td><td><code>{esc(t.get("token"))}</code></td><td>{esc(t.get("match"))}</td></tr>' for t in subs)
        parts.append(f'<table><thead><tr><th>Observed</th><th>Token</th><th>Match</th></tr></thead><tbody>{rows}</tbody></table>')
    else:
        parts.append('<p class="meta">No token substitutions.</p>')
    if unresolved:
        items = "".join(f'<li>{esc(t.get("observed"))}: {esc(t.get("note") or "no matching token")}</li>' for t in unresolved)
        parts.append(f'<p><strong>Unresolved</strong></p><ul>{items}</ul>')
    return "".join(parts)


def manual_slots(brief: dict[str, Any]) -> list[tuple[Any, Any, Any]]:
    """Every slot the publisher fills by hand, as (section order, section name, slot name)."""
    out = []
    for section in sorted_sections(brief):
        for slot in section.get("slots") or []:
            if isinstance(slot, dict) and slot.get("status") == "manual":
                out.append((section.get("order"), section.get("familySection"), slot.get("name")))
    return out


def render_handoff(brief: dict[str, Any]) -> str:
    items = [u for u in (brief.get("unsupported") or []) if isinstance(u, dict)]
    manual = manual_slots(brief)
    parts = []
    if manual:
        rows = "".join(
            f'<li>section {esc(order)} <strong>{esc(section)}</strong>: {esc(name)}</li>'
            for order, section, name in manual
        )
        parts.append(
            f'<p><strong>{len(manual)} slot{"s" if len(manual) != 1 else ""} the publisher fills in the '
            f'Designer</strong> (the build does not write these):</p><ul>{rows}</ul>'
        )
    if items:
        parts.append(
            "<ul>"
            + "".join(f'<li><strong>{esc(u.get("item"))}</strong>: {esc(u.get("handoff"))}</li>' for u in items)
            + "</ul>"
        )
    if not parts:
        return '<p class="meta">Nothing to hand off.</p>'
    return "".join(parts)


def render(brief: dict[str, Any], template: str | None = None, generated_at: str | None = None) -> str:
    if not isinstance(brief, dict):
        raise ValueError("brief must be a JSON object")
    tpl = template if template is not None else FALLBACK_TEMPLATE
    page = brief.get("page") or {}
    values = {
        "TITLE": f"Outline: {esc(page.get('title') or brief.get('family') or 'page')}",
        "HEADER": render_header(brief),
        "FRAMES": render_frames(brief),
        "MAPPING": render_mapping(brief),
        "DECISIONS": render_decisions(brief),
        "TOKENS": render_tokens(brief),
        "HANDOFF": render_handoff(brief),
        "GENERATED_AT": esc(generated_at or dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")),
        "BRIEF_HASH": esc(brief_hash(brief)),
        "SCRIPT": TOGGLE_SCRIPT,
    }
    return re.sub(r"\{\{([A-Z_]+)\}\}", lambda m: values.get(m.group(1), m.group(0)), tpl)


def default_template_path() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "outline.template.html")


def load_template(path: str | None) -> str | None:
    candidate = path or default_template_path()
    try:
        with open(candidate, "r", encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        if path:
            raise
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render the self-contained HTML outline from a webflow-template brief.")
    parser.add_argument("brief", help="brief JSON ('-' for stdin)")
    parser.add_argument("-o", "--out", help="write HTML here instead of stdout")
    parser.add_argument("--template", help="template HTML with {{PLACEHOLDER}} tokens (default: assets/outline.template.html, else embedded)")
    args = parser.parse_args(argv)
    try:
        brief = json.load(sys.stdin) if args.brief == "-" else json.load(open(args.brief, "r", encoding="utf-8"))
        template = load_template(args.template)
        output = render(brief, template)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        return 2
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(output)
        print(json.dumps({"ok": True, "path": args.out, "bytes": len(output.encode("utf-8"))}))
    else:
        sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
