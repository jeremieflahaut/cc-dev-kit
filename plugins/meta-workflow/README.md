# meta-workflow

Toolkit for **authoring Claude Code assets** — the agent/skill definition files themselves, not the application code in a repo. Where `dev-workflow` ships product features, `meta-workflow` reviews the tooling you build on top of Claude Code.

| Component | Type | Role |
|---|---|---|
| `agent-skill-reviewer` | agent | Reviews a Claude Code subagent or skill definition file (`.claude/agents/<name>.md`, `SKILL.md`): frontmatter, the `description`/trigger contract, internal coherence, declared-vs-used tools, and corpus-aware routing overlap with siblings. Read-only — returns a prioritized report, doesn't edit. |

This plugin is intentionally single-asset for now; it exists so that meta/authoring tooling has its own home instead of riding inside `dev-workflow`. New asset-authoring agents or skills (scaffolders, linters) belong here.
