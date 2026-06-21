# cc-dev-kit

A personal Claude Code marketplace bundling the agents and skills I reuse across projects. Nothing hardcodes a specific project — the agents learn each repo's conventions at runtime by reading its `CLAUDE.md` and existing code, then work *within* those conventions.

## Plugins

### `dev-workflow` — stack-agnostic

Assumes **no framework**. Works on any codebase.

- `architect` — designs a plan for non-trivial / multi-file changes, doesn't write code.
- `feature-builder` — implements a feature end-to-end, matching the repo's existing patterns.
- `senior-developer` — judgment work: investigations, tuning, refactors, deep answers.
- `code-reviewer` — reviews a diff against the project's own conventions, read-only.
- `feature-flow` (skill) — orchestrates plan → build → review → fix-loop across the agents above.
- `tdd` (skill) — drives a feature test-first (red → green): writes the failing tests, locks them, then loops hands-free until they pass.
- `commit` (skill) — atomic git commits grouped by intent.
- `pr` (skill) — push + open a pull request (GitHub) or merge request (GitLab), platform auto-detected.

### `laravel-workflow` — Laravel-specialized

Same philosophy, but assumes a **Laravel** codebase (Actions/FormRequests/Jobs/Eloquent, queues, multi-service workspaces). `dev-workflow`'s `feature-flow` discovers and orchestrates these automatically when present.

- `laravel-architect`, `laravel-feature-builder`, `laravel-senior-developer`, `laravel-code-reviewer`.

### `meta-workflow` — Claude Code asset authoring

For building the tooling itself, not application code.

- `agent-skill-reviewer` — reviews a Claude Code subagent / skill definition file (`.claude/agents/<name>.md`, `SKILL.md`): the `description`/trigger contract, internal coherence, declared-vs-used tools, and routing overlap with siblings. Read-only, returns a report.

## Install (any machine)

```bash
# add this repo as a marketplace
/plugin marketplace add https://github.com/<you>/cc-dev-kit

# install the plugin(s) you want
/plugin install dev-workflow@cc-dev-kit
/plugin install laravel-workflow@cc-dev-kit
/plugin install meta-workflow@cc-dev-kit
```

To update later: `/plugin marketplace update cc-dev-kit`.
