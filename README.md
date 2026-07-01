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
- `laravel` (skill) — stack pack: Laravel/PHP patterns (Actions/FormRequests/Jobs, queues & Horizon, Eloquent vs document stores, a correctness checklist). The four agents invoke it on demand when the repo is Laravel — stack specialization lives in a skill, not a duplicate family of agents. Adding another stack is a new skill (`django`, `astro`, …), not new agents.

### `meta-workflow` — Claude Code asset authoring & improvement

For building and improving the tooling itself, not application code.

- `retro` (skill) — offline retrospective ("Dream") over your past sessions: a bundled extractor sweeps the local transcripts and distills recurring friction (your corrections, tool errors, permission rejections), then proposes durable fixes (memory notes, CLAUDE.md rules, hooks). Applies nothing without approval. Good as a weekly habit.

## Install (any machine)

```bash
# add this repo as a marketplace
/plugin marketplace add https://github.com/<you>/cc-dev-kit

# install the plugin(s) you want
/plugin install dev-workflow@cc-dev-kit
/plugin install meta-workflow@cc-dev-kit
```

To update later: `/plugin marketplace update cc-dev-kit`.
