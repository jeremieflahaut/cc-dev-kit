# cc-dev-kit

A personal Claude Code marketplace bundling the agents and skills I reuse across projects. Nothing hardcodes a specific project — the agents learn each repo's conventions at runtime by reading its `CLAUDE.md` and existing code, then work *within* those conventions.

## Plugins

### `dev-workflow` — stack-agnostic

Assumes **no framework**. Works on any codebase — including an empty one (see `greenfield`).

- `architect` — designs a plan for non-trivial / multi-file changes, doesn't write code.
- `feature-builder` — implements a feature end-to-end, matching the repo's existing patterns.
- `senior-developer` — judgment work: investigations, tuning, refactors, deep answers.
- `code-reviewer` — reviews a diff against the project's own conventions, read-only.
- `feature-flow` (skill) — orchestrates frame → plan → build → review → fix-loop → acceptance check across the agents above. Frames observable acceptance criteria up front (skipped for clear-cut requests) and resolves each one before calling the feature done. Can also execute story files prepared by `product-workflow` — "run story 2.1", "next story".
- `greenfield` (skill) — bootstraps a brand-new project: short interview, latest stable versions from official docs, the stack's official scaffolder (user-approved), an initial `CLAUDE.md` as the source of authority, then one reference slice as the canonical sibling. Converts the greenfield into a brownfield, once — then the rest of the kit works as usual.
- `tdd` (skill) — drives a feature test-first (red → green): writes the failing tests, locks them, then loops hands-free until they pass. Can be seeded by a story file — each acceptance criterion becomes a locked failing test.
- `commit` (skill) — atomic git commits grouped by intent.
- `pr` (skill) — push + open a pull request (GitHub) or merge request (GitLab), platform auto-detected.
- `laravel` (skill) — stack pack: Laravel/PHP patterns (Actions/FormRequests/Jobs, queues & Horizon, Eloquent vs document stores, a correctness checklist). The four agents invoke it on demand when the repo is Laravel — stack specialization lives in a skill, not a duplicate family of agents. Adding another stack is a new skill (`django`, `astro`, …), not new agents.

### `product-workflow` — upstream product planning

The half of the lifecycle *before* any code. Inspired by BMAD-METHOD and AIDD, trimmed to solo-dev scale. Artifacts live under `docs/product/` in the target repo (versioned) and follow the project's working language.

- `product-manager` — non-interactive product writing engine: turns a complete inline brief into a brief / spec / PRD / stories; never interviews, states explicit assumptions instead of guessing.
- `product-brief` (skill) — socratic framing interview, one question per turn with a proposed answer to push against → right-sized `docs/product/brief.md`. Optional.
- `product-spec` (skill) — requirements document, right-sized and announced: feature spec (no epics) or product PRD (ordered epics), validated by an inline checklist.
- `create-stories` (skill) — cuts one epic into **self-contained story files** + a flat ordered backlog. The contract: executing a story needs only the story file + `CLAUDE.md` — that's what `feature-flow` runs on ("next story").

### `meta-workflow` — Claude Code asset authoring & improvement

For building and improving the tooling itself, not application code.

- `retro` (skill) — offline retrospective ("Dream") over your past sessions: a bundled extractor sweeps the local transcripts and distills recurring friction (your corrections, tool errors, permission rejections), then proposes durable fixes (memory notes, CLAUDE.md rules, hooks). Applies nothing without approval. Good as a weekly habit.
- `memory-maintenance` (skill) — triages the project's existing auto-memory notes: keep, merge duplicates, promote to a versioned file (CLAUDE.md / conventions), fold into a skill/agent, or delete — verifying real coverage before acting, executing in safe→risky waves, never committing. Complements `retro`: retro mines past sessions to propose *new* notes; this one tidies the notes that already exist.

## Install (any machine)

```bash
# add this repo as a marketplace
/plugin marketplace add https://github.com/jeremieflahaut/cc-dev-kit

# install the plugin(s) you want
/plugin install dev-workflow@cc-dev-kit
/plugin install product-workflow@cc-dev-kit
/plugin install meta-workflow@cc-dev-kit
```

To update later: `/plugin marketplace update cc-dev-kit`.
