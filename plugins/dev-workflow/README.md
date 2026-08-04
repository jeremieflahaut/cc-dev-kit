# dev-workflow

Stack-agnostic dev workflow toolkit for Claude Code. The agents learn each project's conventions at runtime (by reading its `CLAUDE.md` and sibling files) instead of hardcoding any path or framework.

| Component | Type | Role |
|---|---|---|
| `architect` | agent | Plans non-trivial / multi-file changes. Read-only — returns a plan, doesn't code. |
| `feature-builder` | agent | Implements a feature end-to-end, matching the repo's patterns. |
| `senior-developer` | agent | Judgment work: investigations, tuning, refactors. |
| `code-reviewer` | agent | Reviews a diff against the project's own conventions. Read-only. |
| `feature-flow` | skill | Orchestrates frame → plan → build → review → fix-loop → acceptance check over the agents above. Frames 2-5 observable acceptance criteria up front (skipped for clear-cut requests); `done` means the review converged **and** every criterion was verified or explicitly handed back. Can be seeded by a story file from `product-workflow` — "run story 2.1", "next story". |
| `greenfield` | skill | Bootstraps a brand-new project: short interview → latest stable versions from official docs → the stack's official scaffolder (user-approved) → initial `CLAUDE.md` → one reference slice as the canonical sibling. Converts the greenfield into a brownfield, once — then the components above work as usual. Hands deep product framing to `product-workflow` when installed. |
| `tdd` | skill | Drives a feature test-first (red → green): writes the failing tests, locks them, loops hands-free until they pass. Can be seeded by a story file from `product-workflow` — each acceptance criterion becomes a locked failing test. |
| `commit` | skill | Atomic git commits grouped by intent. |
| `pr` | skill | Push + open a PR (GitHub) / MR (GitLab), platform auto-detected. |
| `laravel` | skill | Stack pack: Laravel/PHP patterns (Actions/FormRequests/Jobs, queues & Horizon, Eloquent vs document stores, a correctness checklist). The agents above invoke it on demand when the repo is Laravel. |

`feature-flow` discovers whatever agents are present, so dropping a project-local specialist into `.claude/agents/` automatically extends what it can route to.

Stack specialization lives in **skills**, not in duplicate agents: the four generic agents stay stack-agnostic and pull in a stack pack (e.g. `laravel`) when the project matches. Adding support for another stack is a new skill (`django`, `astro`, …), not a new family of agents.
