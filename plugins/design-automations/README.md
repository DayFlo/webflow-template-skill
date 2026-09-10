# design-automations

Claude Code plugin. One skill: **webflow-template**. Turns a design into an
unpublished draft page in a Webflow site, built from a reusable template family.
Never publishes.

## Installation

From the marketplace root:

```
/plugin marketplace add DayFlo/webflow-template-skill
/plugin install design-automations@webflow-template-skill
```

## Usage

```
/design-automations:webflow-template
```

Ask for a flow by name: onboard, build, maintain, sync, or resume. Onboard a
site before the first build.

See the [repository README](../../README.md) for Codex and Claude.ai install,
the public-exposure table, and the full rulebook.

## Structure

```
design-automations/
├── .claude-plugin/
│   └── plugin.json
├── .mcp.json                  # Webflow MCP server
└── skills/
    └── webflow-template/
        └── SKILL.md
```
