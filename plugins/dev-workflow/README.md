# dev-workflow

Stack-agnostic dev workflow toolkit for Claude Code. The agents learn each project's conventions at runtime (by reading its `CLAUDE.md` and sibling files) instead of hardcoding any path or framework.

| Component | Type | Role |
|---|---|---|
| `architect` | agent | Plans non-trivial / multi-file changes. Read-only — returns a plan, doesn't code. |
| `feature-builder` | agent | Implements a feature end-to-end, matching the repo's patterns. |
| `senior-developer` | agent | Judgment work: investigations, tuning, refactors. |
| `code-reviewer` | agent | Reviews a diff against the project's own conventions. Read-only. |
| `feature-flow` | skill | Orchestrates plan → build → review → fix-loop over the agents above. |
| `commit` | skill | Atomic git commits grouped by intent. |
| `pr` | skill | Push + open a PR (GitHub) / MR (GitLab), platform auto-detected. |

`feature-flow` discovers whatever agents are present, so dropping a project-local specialist into `.claude/agents/` automatically extends what it can route to.
