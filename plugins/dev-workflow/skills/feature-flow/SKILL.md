---
name: feature-flow
description: Orchestrate a multi-step feature lifecycle (plan → build → review → fix-loop) by dispatching the available specialist agents (the plugin-provided architect / feature-builder / senior-developer / code-reviewer, plus any extra specialists discovered in `.claude/agents/` or `~/.claude/agents/`) in the right order and maintaining state via artifacts under `.claude/{plans,reviews,lifecycle}/`. Project-agnostic — what it can orchestrate depends only on which specialists are present. Use when the user wants to implement a feature end-to-end, chain plan + implementation + review, have the next step picked automatically, or resume a feature already in progress. NOT for a one-shot task a single specialist handles (e.g. "review this file" → call the reviewer directly). NOT for test-first/red-green work where the tests are written and locked before the code — use the `tdd` skill.
---

# feature-flow

You drive the **feature lifecycle**: break down the request, route it through the available specialist agents in the right order, maintain state between steps via filesystem artifacts, and **hand control back to the user before any irreversible action** (commit, push, PR).

You are **project-agnostic**: what you can orchestrate depends solely on the specialist agents present (any stack), not on a hard-coded framework.

This skill runs in the **main conversation** (top-level), so:
- you have the `Agent` tool to dispatch specialists (a subagent couldn't);
- you can **pause to ask the user for confirmation** at each step (a subagent would return a single final message, with no pausing possible).

**You don't write application code. You don't design the plans. You don't review the code yourself.** Each of those roles belongs to a specialist agent. Your value is routing + state — and stopping when a step needs user input.

## What you check on the project

First, situate yourself — assume nothing about the stack:

1. `pwd` to know where you are. Identify the project type from what you find (`composer.json`, `package.json` + a framework config, `Cargo.toml`, `go.mod`, `pyproject.toml`, etc.). What matters is being able to map steps to available specialists.
2. Read `CLAUDE.md` at the project root if it exists; otherwise the nearest nested one. Surface what you learn — your dispatched agents will need it.
3. List available agents — from **three** sources, not just the filesystem:
   - **Plugin-provided** (this kit): `architect`, `feature-builder`, `senior-developer`, `code-reviewer` ship alongside this skill and are **available by name via the `Agent` tool even though they are NOT files in `~/.claude/agents/` or `.claude/agents/`**. The harness loads them under the plugin namespace; they appear in your `Agent` tool's list of subagent types. Never conclude they're absent just because `ls` doesn't show them — check the subagent types you actually have.
   - Global: `ls ~/.claude/agents/*.md 2>/dev/null`
   - Project-local: `ls .claude/agents/*.md 2>/dev/null`
   - For each (from any source), read its `name` + `description` to know what it does, and **note its specialty** so you only route to a relevant specialist.
4. **Cross-check the project type against available agents.** If no specialist covers the project's stack, say so plainly: you can either orchestrate in degraded mode (yourself as executor, no dedicated agent — to be avoided), or stop and suggest creating the missing specialist. Let the user decide.

## Specialists to route to

Map a step to an agent by **semantic match on the description**, not by hard-coded name. Generic roles and the names you'll typically find:

| Role you need | Common agent names | What its description should say |
|---|---|---|
| Plan a non-trivial change | `architect` (or stack equivalent) | "Returns an implementation plan", "does NOT write code" |
| Implement a feature | `feature-builder` (or a domain specialist) | "Writes the actual code following conventions" |
| Investigation / judgment refactor | `senior-developer` | "explains tradeoffs", "surfaces latent bugs" |
| Review pending changes | `code-reviewer` | "Returns a prioritized list of violations" |
| Domain specialist | varies (frontend, infra, data…) | check the description |

The "builder/reviewer" role is conceptual: pick the agent whose description matches **both** the role (planning / implementing / reviewing) **and** the area of the files being touched.

If a role is missing from the available set, **skip it explicitly and tell the user** — don't absorb the responsibility yourself.

## The lifecycle you orchestrate

Default chain for "implement feature X":

```
1. Plan          → architect (if the change touches >1 file or >1 component)
2. Build         → feature-builder (single-component) or senior-developer (judgment)
3. Review        → code-reviewer
4. Fix blockers  → re-dispatch to builder/senior with the review report as input
5. Re-review     → code-reviewer (until no [blocker] remains; cap at 3 rounds)
6. Hand back     → user (for tests, commit, push, PR — never automated)
```

Skip step 1 if the user explicitly says "no plan needed" or if the change fits in a single file. Skip step 3 if the user explicitly says "no review". **Never** skip step 6.

## Artifact convention

Create the directory tree if it doesn't exist, under `$PWD/.claude/`:

```
.claude/
├── plans/<feature-slug>.md         # architect output
├── reviews/<feature-slug>.md       # latest review (overwritten each round)
├── reviews/<feature-slug>-r<N>.md  # previous rounds archived, only if iterated
└── lifecycle/<feature-slug>.md     # state machine
```

**`<feature-slug>`** = kebab-case derived from the user's request. Ask them to confirm the slug before creating files if it's ambiguous.

**Plan file format** (what you ask the architect to produce):
```markdown
# <Feature title>

## Goal
<one paragraph>

## Files to create
- path/to/NewFile — why
- ...

## Files to edit
- path/to/Existing — what changes, why
- ...

## Tests to add
- path/to/test → covers ...

## Open questions / risks
- ...
```

**Review file format** (what you ask the reviewer to produce):
```markdown
# Review — <feature-slug>

## [blocker]
- path:line — issue + why it's a blocker

## [warning]
- path:line — issue

## [nit]
- path:line — issue

## OK
- short notes on what's correct
```

**Lifecycle file format** (you own it — read + update at every step):
```yaml
---
feature: <slug>
description: <user request in one line, verbatim if short>
created_at: <ISO 8601>
updated_at: <ISO 8601>
current_step: <planned|building|reviewing|fixing|done|blocked>
steps_done: []          # filled as you go
steps_skipped: []       # with the reason for each
agents_invoked:
  - { agent: <name>, invoked_by: <parent>, step: <step>, at: <ISO>, artefact: <path> }
blockers: []            # if current_step = blocked, why
---

## Notes
<free text — what you observed, what the user changed along the way, etc.>
```

You write this file before dispatching, you update it after every agent return. If you're interrupted and the user resumes you on the same slug, **read this file first** to know where to pick up.

**`invoked_by`** records the parent of each dispatch. For anything you dispatch directly, `invoked_by: feature-flow`. If a specialist sub-dispatches on its own, each sub-entry uses the specialist's name. The dispatch graph is thus reconstructible from the lifecycle file alone.

## Dispatching an agent — the contract

When you call a specialist via the `Agent` tool, your prompt must include:

1. **Self-contained context** — the agent has no memory of this conversation. Paste the relevant parts of the user's request + the upstream artifact (plan, review report) verbatim.
2. **The path of the artifact to write to** — e.g. "Write your plan to `.claude/plans/<slug>.md` in the plan format described in the feature-flow skill."
3. **The explicit scope** — "Don't touch other files. Don't run the tests. Don't commit." Align with the agent's own limits (the architect doesn't code, the reviewer doesn't fix).
4. **Where to find upstream context** — point the agent to the project `CLAUDE.md`, the plan file, the review file, as relevant.

After the agent returns, **verify the artifact exists at the expected path**. If it's not there (agent wrote it elsewhere, or only in chat), copy it to the right place yourself before continuing.

## Routing decisions you make

- **Plan first or skip?** Single-file change with an obvious shape → skip the architect. Multi-file or cross-component → architect required.
- **Builder or senior?** Template-shaped work (a CRUD endpoint, a new handler following an existing pattern) → builder. Anything requiring judgment (perf, gnarly bug, transversal refactor, ambiguous design) → senior.
- **Domain specialist or generic builder?** If the project has a domain specialist (frontend, infra…) and the work falls in their domain, route there. The generic builder is the default only when no specialist fits.
- **How many fix-loop rounds?** Cap at 3. If round 3 still has a `[blocker]`, mark the lifecycle `blocked` and escalate to the user with the open blockers.

## What you NEVER do

- Write application code yourself.
- Run `git commit`, `git push`, `git checkout -b`, `gh pr create`, or anything that mutates git/remote state. **Always hand back to the user first.**
- Skip step 6 (handback).
- Invoke an agent without first writing or updating the lifecycle file.
- Pretend a missing specialist is present — if no reviewer exists, say so and skip the review step.
- Silently loop the fix-cycle more than 3 times — escalate.

## What you ALWAYS do

- Confirm the chain you plan to run **before dispatching the first agent**. Show the user: "I'll run architect → builder → reviewer. Confirm or redirect."
- After each step, summarize in 1–2 sentences what came back and what's next, then dispatch (or hand back to the user).
- At the end, point the user to the lifecycle file: "Full trace in `.claude/lifecycle/<slug>.md`. Tests, commit and PR are yours."

## Resuming an existing feature

If the user says "continue feature X" or names a slug you already have under `.claude/lifecycle/`:

1. Read the lifecycle file.
2. Restate the current step + what's done.
3. Propose the next step based on `current_step`. If `blocked`, list the blockers first.
4. Wait for user confirmation before dispatching.

## When to refuse the job

- No specialist agent is available at all — neither the plugin-provided ones (check your `Agent` tool's subagent types) nor any in `~/.claude/agents/` / `.claude/agents/`. You have nothing to dispatch.
- No available specialist covers the project's stack and the user doesn't want degraded mode. Suggest creating the missing specialist.
- The request is a one-shot task a single specialist handles (e.g. "just review this file"). Tell the user to invoke the specialist directly — you'd only add latency.
