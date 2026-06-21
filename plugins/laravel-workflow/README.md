# laravel-workflow

Laravel-specialized dev agents for Claude Code. Same philosophy as `dev-workflow` — the agents learn each project's conventions at runtime (`CLAUDE.md`, a conventions doc, sibling files) and hardcode **no specific project** — but they assume a **Laravel** codebase (Actions/FormRequests/Jobs/Eloquent, queues, multi-service workspaces).

| Component | Type | Role |
|---|---|---|
| `laravel-architect` | agent | Plans non-trivial / multi-file Laravel changes. Read-only — returns a plan, doesn't code. |
| `laravel-feature-builder` | agent | Implements a feature end-to-end (Action + FormRequest + Controller + route + tests…), matching the repo's patterns. |
| `laravel-senior-developer` | agent | Judgment work: bug investigations, query tuning, queue/broker debugging, refactors. |
| `laravel-code-reviewer` | agent | Reviews a diff against the project's own conventions + general Laravel correctness. Read-only. |

Use alongside `dev-workflow`: its `feature-flow` skill discovers whatever agents are present, so on a Laravel project it routes plan → build → review to these specialists automatically.

## Install

```bash
/plugin marketplace add https://github.com/<you>/cc-dev-kit
/plugin install laravel-workflow@cc-dev-kit
```
