# meta-workflow

Toolkit for **authoring and improving Claude Code assets** — the agent/skill definitions and your own working setup, not the application code in a repo. Where `dev-workflow` ships product features, `meta-workflow` works on the tooling you build on top of Claude Code.

| Component | Type | Role |
|---|---|---|
| `agent-skill-reviewer` | agent | Reviews a Claude Code subagent or skill definition file (`.claude/agents/<name>.md`, `SKILL.md`): frontmatter, the `description`/trigger contract, internal coherence, declared-vs-used tools, and corpus-aware routing overlap with siblings. Read-only — returns a prioritized report, doesn't edit. |
| `retro` | skill | Offline retrospective ("Dream") over your past Claude Code sessions. A bundled stdlib extractor sweeps the local transcripts over a time window and distills the friction — where you corrected Claude, tool errors, permission rejections — then the skill clusters the recurring patterns and proposes durable fixes (memory notes, CLAUDE.md rules, hooks, permission pre-approvals). Applies nothing without approval. Run it weekly or whenever you want to know what keeps going wrong in how you work with Claude. |
| `memory-maintenance` | skill | Triage of your existing auto-memory corpus: per note, decide keep / migrate to a versioned file (`CLAUDE.md`, `CONVENTIONS.md`) / fold into a skill or agent / delete / merge. Verifies real coverage before acting, executes in safe→risky waves, reconciles the `MEMORY.md` index, and never commits. Complements `retro`: retro distills *new* durable context from sessions; this one triages what already exists. |

This plugin exists so that meta/authoring tooling has its own home instead of riding inside `dev-workflow`. New asset-authoring agents or skills (scaffolders, linters, retrospectives) belong here.
