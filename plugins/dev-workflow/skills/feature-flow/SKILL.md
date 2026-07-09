---
name: feature-flow
description: Orchestrate a feature end-to-end — plan → build → review → fix-loop → hand back — by dispatching the available specialist agents (the plugin-provided architect / feature-builder / senior-developer / code-reviewer, plus any extras found in `.claude/agents/` or `~/.claude/agents/`) in the right order and tracking state in artifacts under `.claude/{plans,reviews,lifecycle}/`. Match each step to an agent by its description, not a fixed name, so it works on any stack. Use when the user wants to implement a feature end-to-end, chain plan + build + review, have the next step picked automatically, or resume a feature already in progress ("continue feature X"). NOT for a one-shot task one specialist handles (e.g. "review this file" → call the reviewer directly). NOT for test-first/red-green work where tests are locked before the code — use the `tdd` skill.
tools: Read, Write, Bash, Agent
---

# feature-flow

Run the feature lifecycle: break the request down, route each stage to the specialist that fits it, carry state between stages in files, and **hand control back to the user before anything irreversible** (tests, commit, push, PR).

This is a **coordinator, not a doer**. Writing plans, writing code, and reviewing code each belong to a specialist agent — never do them here. The value added is *ordering the specialists, threading their outputs together, and stopping to ask the user when a stage needs a decision.*

## Why this must run in the main conversation

Two capabilities are load-bearing, and a subagent has neither:

- **`Agent` to dispatch specialists** — a subagent can't spawn other agents.
- **Pausing mid-flow to ask the user** — a subagent returns one final message and can't wait for confirmation between stages.

So invoke this skill at the top level, never from inside another agent.

## Situate yourself first (project-agnostic)

Assume nothing about the framework. What can be orchestrated depends only on which specialists exist.

1. Run `pwd`; identify the stack from whatever manifest is present (`composer.json`, `package.json`, `Cargo.toml`, `go.mod`, `pyproject.toml`, …). The point is to map stages to specialists, not to hard-code a framework.
2. Read the project root `CLAUDE.md` (or the nearest nested one). Surface what matters — dispatched agents start with no memory and will need it passed to them.
3. Enumerate the available specialists from **three** sources:
   - **Plugin-provided** (`architect`, `feature-builder`, `senior-developer`, `code-reviewer`): these ship with this kit and are callable by name through the `Agent` tool **even though no file for them exists under either agents dir**. They appear in the `Agent` tool's subagent-type list. Never conclude they're missing just because `ls` doesn't show them.
   - `ls .claude/agents/*.md 2>/dev/null` (project-local)
   - `ls ~/.claude/agents/*.md 2>/dev/null` (global)
   - Read each one's `name` + `description`; note its specialty so routing stays deliberate.
4. If no specialist covers the project's stack, say so plainly and let the user choose: create the missing specialist, or proceed in degraded mode (avoid this — it means executing the work yourself, which defeats the skill).

## Route by description, not by name

Match a stage to an agent on the **semantics of its description** — role *and* the area of the files touched. The plugin names below are only the common case.

| Stage | Look for a description that says… | Typical agent |
|---|---|---|
| Plan a multi-file / cross-component change | "returns an implementation plan", "does NOT write code" | `architect` |
| Implement, following existing patterns | "writes the actual code following conventions" | `feature-builder` |
| Investigate / judgment refactor / gnarly bug | "explains tradeoffs", "surfaces latent bugs" | `senior-developer` |
| Review pending changes, read-only | "returns a prioritized list of violations" | `code-reviewer` |
| Domain-specific work (frontend, infra, data…) | check its description | varies |

Prefer a domain specialist over the generic builder when the files fall in that domain. If a stage's role has no matching agent, **skip it out loud** — tell the user, don't quietly absorb the responsibility.

## The default chain

```
1. Plan         → architect            (skip if single-file / obvious shape, or user says "no plan")
2. Build        → feature-builder (pattern work) OR senior-developer (needs judgment)
3. Review       → code-reviewer         (skip only if user says "no review")
4. Fix          → re-dispatch to the builder/senior with the review report as input
5. Re-review    → code-reviewer         (loop 3↔4 until Blockers is empty; hard cap 3 rounds)
6. Hand back    → user                  (tests, commit, push, PR — NEVER automated, NEVER skipped)
```

Routing calls to make as you go:
- **Plan or skip?** One file with an obvious shape → skip. Multiple files or cross-component → architect required.
- **Builder or senior?** Template-shaped work (a CRUD endpoint mirroring a sibling) → builder. Anything needing judgment (perf, tricky bug, transversal refactor, ambiguous design) → senior.
- **Fix-loop budget:** cap at 3 rounds. If round 3 still has a Blocker, set the lifecycle to `blocked` and escalate to the user with the open blockers — don't loop silently.

## State artifacts

Create under `$PWD/.claude/` (make the tree if absent). `<slug>` is kebab-case from the request — confirm it with the user if ambiguous, so a later "continue feature X" resolves.

```
.claude/
├── plans/<slug>.md          # the planning agent's own output
├── reviews/<slug>.md        # latest review (overwritten each round)
├── reviews/<slug>-r<N>.md   # prior rounds, archived only if the loop iterated
└── lifecycle/<slug>.md      # the state machine — this skill owns it
```

For the **plan** and **review** files, have the specialist write **its own standard output format** — don't impose a competing template. Only the **lifecycle file is owned here**; write it before the first dispatch and update it after every agent returns:

```yaml
---
feature: <slug>
description: <user request, one line>
current_step: planned|building|reviewing|fixing|done|blocked
steps_done: []
steps_skipped: []        # each with its reason
agents_invoked:
  - { agent: <name>, invoked_by: feature-flow, step: <step>, at: <ISO>, artefact: <path> }
blockers: []             # populated when current_step = blocked
---
## Notes
<what was observed, what the user changed mid-flow>
```

`invoked_by` records each dispatch's parent (`feature-flow` for direct dispatches; a specialist's name if it sub-dispatched), so the whole dispatch graph is reconstructible from this file alone.

## The dispatch contract

A specialist has no memory of this conversation. Every `Agent` prompt must carry:

1. **Self-contained context** — paste the relevant slice of the user's request plus the upstream artifact (plan, review report) verbatim.
2. **The artifact path to write** — e.g. "Write your plan to `.claude/plans/<slug>.md` in your standard format."
3. **The scope fence** — "Only these files. Don't run tests. Don't commit." Align it with the agent's own limits (architect doesn't code; reviewer doesn't fix).
4. **Where upstream context lives** — point to the project `CLAUDE.md`, the plan file, the review file, as relevant.

After each return, **verify the artifact is at the expected path**. If the agent wrote it elsewhere or only in chat, move it into place before continuing.

## Interaction rhythm

- **Before the first dispatch**, show the chain and get a go-ahead: "I'll run architect → builder → reviewer. Confirm or redirect."
- **After each stage**, summarize in 1–2 sentences what came back and what's next, then dispatch or hand back.
- **At the end**, point to the trace: "Full lifecycle in `.claude/lifecycle/<slug>.md`. Tests, commit, and PR are yours."

## Resuming a feature

On "continue feature X" or a slug already under `.claude/lifecycle/`:

1. Read the lifecycle file.
2. Restate the current step and what's done.
3. Propose the next step from `current_step` (if `blocked`, list the blockers first).
4. Wait for confirmation before dispatching.

## Never / Always

**Never:** write application code, design a plan, or review code yourself; run `git commit` / `git push` / `git checkout -b` / `gh pr create` or any git/remote mutation; skip the handback (step 6); dispatch without first writing/updating the lifecycle file; pretend a missing specialist is present; loop the fix-cycle past 3 rounds without escalating.

**Always:** hand back to the user before any irreversible action; keep the lifecycle file current; route by description match.

## When to decline

- No specialist exists at all (nothing in the `Agent` subagent types, nor either agents dir) — there's nothing to dispatch.
- No specialist covers the stack and the user rejects degraded mode — suggest creating the specialist.
- The request is a one-shot a single specialist handles — tell the user to call that specialist directly; orchestration would only add latency.
