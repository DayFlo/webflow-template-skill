#!/usr/bin/env python3
"""Structural and disclosure checks for this repository.

Two halves:

1. Structure. The plugin and marketplace manifests parse and carry the keys
   Claude Code and Codex need, the documented command form is the namespaced
   one, and the skill version agrees with the changelog.
2. The public-exposure guarantee. The "What this can and cannot make public"
   section exists in README.md and SKILL.md, the rulebook still forbids
   publish_site, and the uploaded-asset warning is still in the rulebook and
   the build flow, so none of it can be quietly deleted later.
3. Disclosure. Nothing in the tree may carry a Designer Bridge App launch link
   (it embeds a per-account app token; references/rules.md rule 15), any other
   long secret-shaped token, a machine-specific path, a branch staging domain,
   or a Webflow-shaped identifier outside this repository's synthetic set. The
   last of those is the main defence against a contributor pasting real site
   data into an example.

Usage: python3 checks/repo_check.py [repo-root]
       REPO_CHECK_LIVE=1 python3 checks/repo_check.py   # also runs `claude plugin validate`
Exit codes: 0 all PASS (WARN and SKIP allowed), 1 at least one FAIL.

Python 3 standard library only; PyYAML is used when present and a small
block-YAML subset parser otherwise. No network, no git, no writes.
"""

import json
import os
import re
import shutil
import subprocess
import sys

EXPECTED_URL = "https://mcp.webflow.com/mcp"
EXPECTED_VERSION = "1.0.0"
EXPECTED_SKILL = "webflow-template"
EXPECTED_PLUGIN = "temperage"
EXPECTED_MARKET = "webflow-template-skill"

QUOTES = ('"', "'")

# --------------------------------------------------------------- reporting

class Report:
    def __init__(self):
        self.fails = 0

    def ok(self, msg):
        print(f"PASS  {msg}")

    def bad(self, msg):
        print(f"FAIL  {msg}")
        self.fails += 1

    def warn(self, msg):
        print(f"WARN  {msg}")

    def skip(self, msg):
        print(f"SKIP  {msg}")

    def verdict(self, ok, ok_msg, bad_msg):
        self.ok(ok_msg) if ok else self.bad(bad_msg)

# ------------------------------------------------------------------- yaml

def _uncomment(line):
    quote = None
    for i, c in enumerate(line):
        if quote:
            if c == quote:
                quote = None
        elif c in QUOTES:
            quote = c
        elif c == "#" and (i == 0 or line[i - 1] in " \t"):
            return line[:i]
    return line

def _scalar(s):
    s = s.strip()
    if not s:
        return None
    if len(s) > 1 and s[0] in QUOTES and s[-1] == s[0]:
        return s[1:-1]
    low = s.lower()
    if low in ("true", "yes", "on"):
        return True
    if low in ("false", "no", "off"):
        return False
    if low in ("null", "~"):
        return None
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    return s

def yaml_subset_load(text):
    """Mappings, sequences of mappings or scalars, quoted and plain scalars,
    comments. Enough for agents/openai.yaml and SKILL.md frontmatter."""
    rows = []
    for raw in text.splitlines():
        line = _uncomment(raw).rstrip()
        if line.strip():
            rows.append([len(line) - len(line.lstrip(" ")), line.strip()])
    at = [0]

    def node(indent):
        if rows[at[0]][1].startswith("-"):
            seq = []
            while at[0] < len(rows) and rows[at[0]][0] == indent and rows[at[0]][1].startswith("-"):
                item = rows[at[0]][1][1:].strip()
                key, sep, _ = item.partition(":")
                if sep and item[0] not in QUOTES and key.strip():
                    rows[at[0]] = [indent + 2, item]  # re-read the item as a mapping row
                    seq.append(node(indent + 2))
                else:
                    at[0] += 1
                    seq.append(_scalar(item) if item else None)
            return seq
        mapping = {}
        while at[0] < len(rows) and rows[at[0]][0] == indent and not rows[at[0]][1].startswith("-"):
            key, sep, val = rows[at[0]][1].partition(":")
            if not sep or not key.strip():
                raise ValueError(f"expected 'key: value', got {rows[at[0]][1]!r}")
            at[0] += 1
            if val.strip():
                mapping[key.strip()] = _scalar(val)
            elif at[0] < len(rows) and (rows[at[0]][0] > indent or rows[at[0]][1].startswith("-")):
                mapping[key.strip()] = node(rows[at[0]][0])
            else:
                mapping[key.strip()] = None
        return mapping

    if not rows:
        return {}
    result = node(rows[0][0])
    if at[0] != len(rows):
        raise ValueError(f"unparsed content at {rows[at[0]][1]!r}")
    return result

def yaml_load(text):
    try:
        import yaml  # type: ignore
        return yaml.safe_load(text), "pyyaml"
    except ImportError:
        return yaml_subset_load(text), "subset"

def frontmatter(text):
    """The leading --- block, with '>-' and '|' block scalars folded to one line."""
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", text, re.S)
    if not m:
        return None
    src = m.group(1).splitlines()
    flat, i = [], 0
    while i < len(src):
        block = re.match(r"^(\s*)([A-Za-z0-9_-]+):\s*([>|])-?\s*$", src[i])
        if not block:
            flat.append(src[i])
            i += 1
            continue
        indent, key, style = len(block.group(1)), block.group(2), block.group(3)
        i += 1
        parts = []
        while i < len(src) and (not src[i].strip() or len(src[i]) - len(src[i].lstrip(" ")) > indent):
            parts.append(src[i].strip())
            i += 1
        joiner = " " if style == ">" else "\n"
        flat.append(f"{block.group(1)}{key}: {json.dumps(joiner.join(p for p in parts if p))}")
    return yaml_load("\n".join(flat))[0]

# ------------------------------------------------------------------- files

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv"}
TEXT_SUFFIXES = (".md", ".py", ".json", ".yaml", ".yml", ".html", ".sh", ".txt", ".toml", ".cfg", ".ini")
SELF = {os.path.join("checks", "repo_check.py"), os.path.join("checks", "repo-check.sh")}

def tracked_files(root):
    """Every text file in the tree. Deliberately not `git ls-files`: this script
    must run in a checkout that is not a git repository."""
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            if name.endswith(TEXT_SUFFIXES) or name in ("LICENSE", ".gitignore"):
                found.append(os.path.join(dirpath, name))
    return found

def read_json(path):
    """(object, error). Missing, malformed, and "parses but is not an object" are
    all errors rather than exceptions, so every caller can assume a mapping."""
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        return None, f"missing at {path}"
    except Exception as exc:  # malformed JSON, unreadable file
        return None, f"does not parse: {exc}"
    if not isinstance(data, dict):
        return None, f"is not a JSON object (top level is {type(data).__name__})"
    return data, None

def read_text(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read(), None
    except FileNotFoundError:
        return None, f"missing at {path}"
    except OSError as exc:
        return None, f"unreadable: {exc}"

# --------------------------------------------------------------- structure

def check_mcp_json(paths, report):
    """.mcp.json parses; mcpServers.webflow.url matches; type http; only the
    mcpServers top-level key (the Codex ingestion validator rejects others)."""
    data, err = read_json(paths["mcp"])
    if err:
        return report.bad(f".mcp.json {err}")
    servers = data.get("mcpServers")
    if not isinstance(servers, dict):
        return report.bad(".mcp.json has no mcpServers object")
    webflow = servers.get("webflow")
    if not isinstance(webflow, dict):
        return report.bad(".mcp.json mcpServers has no webflow entry")

    report.verdict(
        webflow.get("url") == EXPECTED_URL,
        f".mcp.json parses; mcpServers.webflow.url == {EXPECTED_URL}",
        f".mcp.json mcpServers.webflow.url is {webflow.get('url')!r}, expected {EXPECTED_URL}")
    if webflow.get("type") == "http":
        report.ok('.mcp.json mcpServers.webflow.type == http')
    else:
        report.warn('.mcp.json mcpServers.webflow has no "type": "http"')
    extra = sorted(set(data) - {"mcpServers"})
    report.verdict(
        not extra,
        ".mcp.json has mcpServers as its only top-level key (Codex ingestion contract)",
        f".mcp.json has top-level keys the Codex ingestion validator rejects: {','.join(extra)}")

def check_skill_frontmatter(paths, report):
    """SKILL.md frontmatter: name matches the directory, disable-model-invocation
    true, description within the Agent Skills spec limit, file length."""
    text, err = read_text(paths["skill_md"])
    if err:
        return report.bad(f"SKILL.md {err}")
    try:
        fm = frontmatter(text)
    except Exception as exc:
        return report.bad(f"SKILL.md frontmatter does not parse: {exc}")
    if fm is None:
        return report.bad("SKILL.md has no YAML frontmatter block")
    if not isinstance(fm, dict):
        return report.bad("SKILL.md frontmatter is not a mapping")

    name, dmi, desc = fm.get("name"), fm.get("disable-model-invocation"), fm.get("description")
    report.verdict(
        name == EXPECTED_SKILL,
        f"SKILL.md frontmatter name: {EXPECTED_SKILL} (matches the directory)",
        f"SKILL.md frontmatter name is {name!r}, expected {EXPECTED_SKILL}")
    report.verdict(
        dmi is True,
        "SKILL.md frontmatter disable-model-invocation: true",
        f"SKILL.md frontmatter disable-model-invocation is {dmi!r}, expected true")
    report.verdict(
        isinstance(desc, str) and 0 < len(desc.strip()) <= 1024,
        "SKILL.md frontmatter description is 1 to 1024 characters",
        "SKILL.md frontmatter description missing or over 1024 characters")
    lines = text.count("\n") + 1
    if lines > 500:
        report.warn(f"SKILL.md is {lines} lines; the Agent Skills spec recommends under 500")

def check_openai_yaml(paths, report):
    """agents/openai.yaml: parses; only interface/policy/dependencies at the top;
    interface.display_name and short_description; default_prompt names the
    $skill; policy.allow_implicit_invocation is boolean false (the Codex
    counterpart of disable-model-invocation); the Webflow MCP dependency."""
    text, err = read_text(paths["openai"])
    if err:
        return report.bad(f"agents/openai.yaml {err} (Codex would treat the skill as implicitly invocable)")
    try:
        data, how = yaml_load(text)
    except Exception as exc:
        return report.bad(f"agents/openai.yaml does not parse as YAML: {exc}")
    if not isinstance(data, dict):
        return report.bad("agents/openai.yaml does not parse as YAML: top level is not a mapping")

    extra = sorted(set(data) - {"interface", "policy", "dependencies"})
    report.verdict(
        not extra,
        f"agents/openai.yaml parses ({how}); top-level keys within interface/policy/dependencies",
        f"agents/openai.yaml has top-level keys the Codex validator rejects: {','.join(extra)}")

    iface = data.get("interface")
    if not isinstance(iface, dict):
        report.bad("agents/openai.yaml interface is not a mapping")
        report.bad("agents/openai.yaml interface.default_prompt does not name the skill")
    else:
        known = {"display_name", "short_description", "icon_small", "icon_large", "brand_color", "default_prompt"}
        unknown = sorted(set(iface) - known)
        named = all(isinstance(iface.get(k), str) and iface[k].strip()
                    for k in ("display_name", "short_description"))
        detail = f"unknown keys {','.join(unknown)}" if unknown else "display_name/short_description missing"
        report.verdict(
            not unknown and named,
            "agents/openai.yaml interface has display_name and short_description, known keys only",
            f"agents/openai.yaml interface: {detail}")
        prompt = iface.get("default_prompt")
        report.verdict(
            isinstance(prompt, str) and EXPECTED_SKILL in prompt,
            f"agents/openai.yaml interface.default_prompt names ${EXPECTED_SKILL}",
            "agents/openai.yaml interface.default_prompt does not name the skill")

    policy = data.get("policy")
    valid_policy = (isinstance(policy, dict)
                    and not set(policy) - {"allow_implicit_invocation"}
                    and policy.get("allow_implicit_invocation") is False)
    report.verdict(
        valid_policy,
        "agents/openai.yaml policy.allow_implicit_invocation is boolean false",
        f"agents/openai.yaml policy is {policy!r}, expected only allow_implicit_invocation: false")

    deps = data.get("dependencies")
    if not isinstance(deps, dict) or set(deps) - {"tools"}:
        return report.bad(f"agents/openai.yaml dependencies is {deps!r}, expected only tools")
    tools = deps.get("tools")
    if not isinstance(tools, list):
        return report.bad(
            f"agents/openai.yaml dependencies.tools is not a list (got {type(tools).__name__})")
    webflow = [t for t in tools
               if isinstance(t, dict) and t.get("type") == "mcp" and t.get("value") == "webflow"]
    if not webflow:
        return report.bad("agents/openai.yaml dependencies.tools has no mcp tool with value webflow")
    tool = webflow[0]
    report.verdict(
        tool.get("url") == EXPECTED_URL and tool.get("transport") == "streamable_http",
        f"agents/openai.yaml dependencies.tools has mcp/webflow with transport streamable_http and url {EXPECTED_URL}",
        f"agents/openai.yaml mcp/webflow has transport {tool.get('transport')!r} "
        f"and url {tool.get('url')!r}")

def check_plugin_json(paths, report):
    """plugin.json: name and version equal the expected literals."""
    data, err = read_json(paths["plugin_json"])
    if err:
        return report.bad(f"plugin.json {err}")
    version, name = str(data.get("version", "")), data.get("name", "")
    report.verdict(
        version == EXPECTED_VERSION,
        f"plugin.json version == {EXPECTED_VERSION}",
        f"plugin.json version is {version!r}, expected {EXPECTED_VERSION}")
    report.verdict(
        name == EXPECTED_PLUGIN,
        f"plugin.json name == {EXPECTED_PLUGIN}",
        f"plugin.json name is {name!r}, expected {EXPECTED_PLUGIN}")

def check_versions_agree(paths, report):
    """SKILL.md metadata.version matches the newest CHANGELOG heading."""
    skill_text, skill_err = read_text(paths["skill_md"])
    changelog, log_err = read_text(paths["changelog"])
    if skill_err or log_err:
        return  # SKILL.md is reported elsewhere; a missing changelog cannot be compared
    try:
        fm = frontmatter(skill_text) or {}
    except Exception:
        return  # already reported by check_skill_frontmatter
    meta = fm.get("metadata") if isinstance(fm, dict) else None
    skill_version = str(meta.get("version", "")) if isinstance(meta, dict) else ""
    heading = re.search(r"^## \[(\d+\.\d+\.\d+)\]", changelog, re.M)
    newest = heading.group(1) if heading else ""
    report.verdict(
        skill_version and skill_version == newest,
        f"SKILL.md metadata.version == newest CHANGELOG heading ({newest})",
        f"SKILL.md metadata.version and CHANGELOG disagree: skill={skill_version!r} changelog={newest!r}")

def _marketplace_entry(path, label, report):
    """(data, entry) for a marketplace manifest, or (None, None) once reported."""
    data, err = read_json(path)
    if err:
        return report.bad(f"{label} {err}") or (None, None)
    plugins = data.get("plugins", [])
    if not isinstance(plugins, list):
        return report.bad(
            f"{label} plugins is not a JSON array (got {type(plugins).__name__})"
        ) or (None, None)
    entry = next((p for p in plugins
                  if isinstance(p, dict) and p.get("name") == EXPECTED_PLUGIN), None)
    if entry is None:
        return report.bad(f"{label} does not list {EXPECTED_PLUGIN}") or (None, None)
    if data.get("name") != EXPECTED_MARKET:
        report.bad(f"{label} name is {data.get('name')!r}, expected {EXPECTED_MARKET}")
        return None, None
    return data, entry

def check_claude_marketplace(paths, report):
    """Claude marketplace: expected name, lists the plugin with a relative ./ source."""
    label = ".claude-plugin/marketplace.json"
    _, entry = _marketplace_entry(paths["market"], label, report)
    if entry is None:
        return
    source = entry.get("source")
    expected_source = f"./plugins/{EXPECTED_PLUGIN}"
    report.verdict(
        source == expected_source,
        f"{label} is '{EXPECTED_MARKET}' and lists {EXPECTED_PLUGIN} with source ./plugins/{EXPECTED_PLUGIN}",
        f"{label} source is {source!r}, expected {expected_source}")

def check_codex_marketplace(paths, report):
    """Native Codex marketplace: same marketplace name, source {local,
    ./plugins/<plugin>}, documented policy enums, and a category."""
    label = ".agents/plugins/marketplace.json"
    _, entry = _marketplace_entry(paths["codex_market"], label, report)
    if entry is None:
        return
    source, raw_policy = entry.get("source"), entry.get("policy")
    policy = raw_policy if isinstance(raw_policy, dict) else {}
    expected_path = f"./plugins/{EXPECTED_PLUGIN}"
    good_source = (isinstance(source, dict) and source.get("source") == "local"
                   and source.get("path") == expected_path)
    good_policy = (isinstance(raw_policy, dict)
                   and policy.get("installation") in ("NOT_AVAILABLE", "AVAILABLE", "INSTALLED_BY_DEFAULT")
                   and policy.get("authentication") in ("ON_INSTALL", "ON_USE"))
    report.verdict(
        good_source and good_policy,
        f"{label} is '{EXPECTED_MARKET}'; entry has source "
        f"{{local, ./plugins/{EXPECTED_PLUGIN}}} and documented policy values",
        f"{label} entry shape is wrong: {json.dumps({'source': source, 'policy': raw_policy})}")
    category = entry.get("category")
    report.verdict(
        isinstance(category, str) and category.strip(),
        f"{label} entry carries a category",
        f"{label} entry has no category")

def check_catalog_ships_empty(paths, report):
    """The catalog ships empty: onboarding generates it per site."""
    catalog = os.path.join(paths["skill"], "references", "catalog")
    families = [n for n in sorted(os.listdir(catalog))
                if n.endswith(".md") and n.lower() != "readme.md"] if os.path.isdir(catalog) else []
    report.verdict(
        not families,
        "references/catalog/ ships empty; flows/onboard.md generates it per site",
        f"references/catalog/ carries {', '.join(families)}; the public skill ships without a catalog")

PUBLIC_HEADING = "What this can and cannot make public"
# The sentence the asset warning turns on. Both the rulebook and the build flow
# must keep saying it: an uploaded asset is public before any publish, which is
# the one way this skill can put a file on the internet.
ASSET_PHRASE = "from the moment of upload"
NO_PUBLISH = "Never call `publish_site`"


def check_public_exposure(paths, report):
    """The public-exposure guarantee cannot be quietly deleted.

    Four things have to stay true: the section exists in README.md and in
    SKILL.md, the rulebook still forbids publish_site, and the uploaded-asset
    warning is still in both the rulebook and the build flow. Each is a
    sentence a well-meaning edit could drop without noticing.
    """
    for key, label in (("readme", "README.md"), ("skill_md", "SKILL.md")):
        text, err = read_text(paths[key])
        if err:
            report.bad(f"{label} {err}")
            continue
        heading = re.search(rf"^#+ .*{re.escape(PUBLIC_HEADING)}", text, re.M)
        report.verdict(
            bool(heading),
            f'{label} carries the "{PUBLIC_HEADING}" section',
            f'{label} has no "{PUBLIC_HEADING}" section; the public-exposure '
            "guarantee must be stated in both README.md and SKILL.md")

    rules, err = read_text(paths["rules"])
    if err:
        return report.bad(f"references/rules.md {err}")
    report.verdict(
        NO_PUBLISH in rules,
        f"references/rules.md still says {NO_PUBLISH.lower()}",
        f"references/rules.md no longer says {NO_PUBLISH!r}; publishing must stay forbidden")

    build, build_err = read_text(paths["build"])
    missing = [label for label, text in (("references/rules.md", rules),
                                         ("flows/build.md", build if not build_err else ""))
               if ASSET_PHRASE not in text]
    report.verdict(
        not missing,
        f'the uploaded-asset warning ("{ASSET_PHRASE}") is in references/rules.md and flows/build.md',
        f"the uploaded-asset warning is missing from {', '.join(missing) or 'a file that could not be read'}; "
        "an upload is public before any publish and the skill must keep saying so")


def check_license(paths, report):
    """LICENSE is MIT and carries a copyright line. A filled holder and the
    leftover '<copyright holder>' placeholder both pass; only a missing or
    altered licence fails."""
    text, err = read_text(paths["license"])
    if err or "MIT License" not in text or not re.search(r"^Copyright \(c\) [0-9]{4} .+", text, re.M):
        return report.bad("LICENSE is missing, is not MIT, or has no copyright line")
    if "<copyright holder>" in text:
        report.ok("LICENSE is MIT; the copyright holder is still the placeholder, fill it in before publishing")
    else:
        report.ok("LICENSE is MIT with a copyright holder filled in")

# ------------------------------------------- command form and disclosure

# \x60 backtick, \x22 double quote, \x27 single quote.
BRIDGE = re.compile(r"design\.webflow\.com[^\s\x60\x22\x27)]*[?&]app=[0-9a-fA-F]{16,}")
TOKEN = re.compile(r"(?<![0-9a-fA-F:])[0-9a-fA-F]{40,}(?![0-9a-fA-F])")
BARE_CMD = re.compile(rf"(?<![:A-Za-z0-9_./-])/({EXPECTED_SKILL}|{EXPECTED_PLUGIN})(?![:A-Za-z0-9_-])")
HOME_PATH = re.compile(r"/Users/")
BRANCH_DOMAIN = re.compile(r"branch--[A-Za-z0-9-]+\.webflow\.io")
UUID = re.compile(r"(?<![0-9A-Za-z_-])[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}"
                  r"-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}(?![0-9A-Za-z])")
HEXRUN = re.compile(r"(?<![0-9A-Za-z_-])[0-9a-fA-F]{20,39}(?![0-9A-Za-z])")
SYNTHETIC_UUID = re.compile(r"^1111aaaa-0000-4000-8000-0{9}[0-9a-f]{3}$")
SYNTHETIC_HEX = re.compile(r"^0{22}[0-9a-f]{2}$")

def scan_tree(root):
    """One walk, four verdicts. Splitting these apart only duplicated the
    read-and-enumerate loop.

    cmd  bare command form           cred  credential-shaped strings
    leak machine or site specifics   ids   identifiers outside the synthetic set
    """
    hits = {"cmd": [], "cred": [], "leak": [], "ids": []}
    for path in tracked_files(root):
        rel = os.path.relpath(path, root)
        # These files spell out the patterns they hunt for, so they are exempt
        # from everything but the credential scan, which they can never trip.
        checker = rel in SELF
        text, err = read_text(path)
        if err:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            where = f"{rel}:{n}"
            if BRIDGE.search(line):
                hits["cred"].append(f"{where} (bridge app link)")
            elif TOKEN.search(line) and "sha256" not in line.lower():
                hits["cred"].append(f"{where} (long token)")
            if checker:
                continue
            if "/scripts/tests/" not in rel.replace(os.sep, "/") and BARE_CMD.search(line):
                hits["cmd"].append(where)
            if HOME_PATH.search(line):
                hits["leak"].append(f"{where} (home path)")
            if BRANCH_DOMAIN.search(line):
                hits["leak"].append(f"{where} (branch staging domain)")
            for token in UUID.findall(line):
                if not SYNTHETIC_UUID.match(token):
                    hits["ids"].append(f"{where} {token}")
            for token in HEXRUN.findall(UUID.sub(" ", line)):
                if not SYNTHETIC_HEX.match(token):
                    hits["ids"].append(f"{where} {token}")
    return hits

def check_tree_scan(paths, report):
    hits = scan_tree(paths["root"])

    def shown(key):
        found = hits[key]
        extra = " ..." if len(found) > 8 else ""
        return f"{' '.join(found[:8])}{extra}"

    report.verdict(
        not hits["cmd"],
        f"no bare /{EXPECTED_SKILL} or /{EXPECTED_PLUGIN} command in the tree (namespaced form only)",
        f"bare command form found (use /{EXPECTED_PLUGIN}:<skill>): {shown('cmd')}")
    report.verdict(
        not hits["cred"],
        "no Bridge App launch link and no long secret-shaped token in any file (rules.md rule 15)",
        f"credential-shaped string found: {shown('cred')}")
    report.verdict(
        not hits["leak"],
        "no home-directory path and no branch staging domain in any file",
        f"machine or site-specific string found: {shown('leak')}")
    report.verdict(
        not hits["ids"],
        "every Webflow-shaped identifier is from the synthetic set "
        "(0000000000000000000000xx, 1111aaaa-0000-4000-8000-000000000xxx)",
        f"identifier outside the synthetic set: {shown('ids')}")

# -------------------------------------------------------------------- live

def check_live_validate(paths, report):
    """Optional (REPO_CHECK_LIVE=1): Claude Code's own validator on the plugin
    directory and the marketplace root. Read-only."""
    if os.environ.get("REPO_CHECK_LIVE", "0") != "1":
        return report.skip("claude plugin validate (set REPO_CHECK_LIVE=1 to run it locally)")
    if not shutil.which("claude"):
        return report.skip("REPO_CHECK_LIVE=1 but claude is not on PATH")
    for target in (paths["plugin"], paths["root"]):
        done = subprocess.run(["claude", "plugin", "validate", target],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        report.verdict(done.returncode == 0,
                       f"claude plugin validate {target}",
                       f"claude plugin validate {target} reported errors")

CHECKS = (
    check_mcp_json,
    check_skill_frontmatter,
    check_openai_yaml,
    check_plugin_json,
    check_versions_agree,
    check_claude_marketplace,
    check_codex_marketplace,
    check_catalog_ships_empty,
    check_public_exposure,
    check_license,
    check_tree_scan,
    check_live_validate,
)

def main(argv):
    root = os.path.abspath(argv[1] if len(argv) > 1
                           else os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    plugin = os.path.join(root, "plugins", EXPECTED_PLUGIN)
    skill = os.path.join(plugin, "skills", EXPECTED_SKILL)
    if not os.path.isdir(skill):
        print(f"FAIL  {skill} does not exist")
        return 1
    paths = {
        "root": root,
        "plugin": plugin,
        "skill": skill,
        "mcp": os.path.join(plugin, ".mcp.json"),
        "plugin_json": os.path.join(plugin, ".claude-plugin", "plugin.json"),
        "market": os.path.join(root, ".claude-plugin", "marketplace.json"),
        "codex_market": os.path.join(root, ".agents", "plugins", "marketplace.json"),
        "openai": os.path.join(skill, "agents", "openai.yaml"),
        "skill_md": os.path.join(skill, "SKILL.md"),
        "changelog": os.path.join(skill, "CHANGELOG.md"),
        "license": os.path.join(root, "LICENSE"),
        "readme": os.path.join(root, "README.md"),
        "rules": os.path.join(skill, "references", "rules.md"),
        "build": os.path.join(skill, "flows", "build.md"),
    }
    report = Report()
    for check in CHECKS:
        check(paths, report)
    print()
    if report.fails:
        print(f"RESULT  {report.fails} check(s) failed")
        return 1
    print("RESULT  all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
