# claude-dev-kit

A personal, **stack-agnostic** Claude Code marketplace. One plugin, `dev-workflow`, bundling the agents and skills I reuse across projects.

Unlike project-specific agents, these hardcode **no paths and no framework**. They learn each project's conventions at runtime by reading its `CLAUDE.md` and existing code, then work *within* those conventions.

## What's inside

**Agents**
- `architect` — designs a plan for non-trivial / multi-file changes, doesn't write code.
- `feature-builder` — implements a feature end-to-end, matching the repo's existing patterns.
- `senior-developer` — judgment work: investigations, tuning, refactors, deep answers.
- `code-reviewer` — reviews a diff against the project's own conventions, read-only.
- `agent-skill-reviewer` — reviews Claude Code agent/skill definition files.

**Skills**
- `feature-flow` — orchestrates plan → build → review → fix-loop across the agents above.
- `commit` — atomic git commits grouped by intent.
- `pr` — push + open a pull request (GitHub) or merge request (GitLab), platform auto-detected.

## Install (any machine)

```bash
# add this repo as a marketplace
/plugin marketplace add https://github.com/<you>/claude-dev-kit

# install the plugin
/plugin install dev-workflow@claude-dev-kit
```

To update later: `/plugin marketplace update claude-dev-kit`.
