---
name: create-stories
description: Turn one epic of the PRD into self-contained story files plus a flat ordered backlog — dispatches the product-writing agent with the PRD context, the epic section and CLAUDE.md pasted inline, enriches each story with concrete code pointers (canonical sibling found by grep), then runs the story-ready checklist (self-contained, testable criteria, sized for one feature-flow run, dependencies declared). Writes docs/product/stories/<epic>.<n>-<slug>.md and updates docs/product/backlog.md. The contract — executing a story must need ONLY the story file plus CLAUDE.md; if feature-flow has to reopen the PRD, the story failed its checklist. Use when a PRD with epics exists and the user wants stories — "create the stories", "break epic 2 into stories", "prepare the backlog", "crée les stories", "découpe l'epic en stories", "prépare le backlog". One epic at a time. NOT for writing the PRD (use product-spec), NOT for implementing a story (hand the story file to feature-flow).
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, Agent, AskUserQuestion
---

# create-stories

**The contract, before anything else: a story file is the *entire product context* of one feature-flow run.** Whoever executes it needs the story file plus the project's `CLAUDE.md` — nothing more. If executing a story requires reopening the PRD, the story failed this skill's checklist.

One epic at a time, never two.

## Why this must run in the main conversation

Same load-bearing capabilities as the sibling skills: confirming the epic with the user, and `Agent` to dispatch the writer. Invoke at the top level, never from inside another agent.

## Where the artifacts live

Resolve the root once at the start, announce it, then use it everywhere below as `<product-root>`:

- **Default: `docs/product/` at the target repo's root** — versioned, because a fresh clone needs these documents (the rule: describes the product → `docs/`; describes one run → `.claude/`).
- **Override:** if the project's `CLAUDE.md` names a product-docs location, that wins.

This section is the only place the root is defined — if the default ever changes, it changes here and nowhere else.

## Situate yourself first

1. Read `<product-root>/prd.md`. **No PRD → decline** and point to `product-spec`.
2. Read `<product-root>/backlog.md` if it exists — which epics are already cut? If the requested epic already has stories, propose **completing/updating** them; **never duplicate an id**, never renumber existing stories silently.
3. Read the project's `CLAUDE.md` — it travels in the dispatch AND in every downstream execution; it's the other half of the contract.
4. **Determine the working language** (user's explicit choice > existing docs under `<product-root>` > conversation language) and announce it.
5. Pick the epic: the one the user names, otherwise propose the first epic with no stories yet.

## The story file format

The canonical definition — **owned here**; other skills reference it, never redefine it:

```
<product-root>/stories/<epic>.<n>-<slug>.md

---
id: <epic>.<n>              # e.g. 2.1
epic: <epic number>
status: todo                # todo | in-progress | review | done — feature-flow moves it
depends_on: []              # story ids that must be done before this one
---

# <id> — <title>

## Context
Why this story exists and the user outcome — self-contained, no "see the PRD".

## Scope
**In:** …
**Out:** …

## Acceptance criteria
2-5 observable checks — a test or a look at the running product decides each one.

## Implementation notes
<!-- filled by create-stories -->
```

## Dispatch the writer

Route by description (the non-interactive product-writing agent). Everything inline:

1. The PRD's intro and non-goals — **not the whole PRD**.
2. The **full epic section verbatim**.
3. The project's `CLAUDE.md` (or its relevant slice).
4. **The story template above, pasted verbatim** — "follow it exactly".
5. `Working language: <x>`.
6. The target directory — `<product-root>/stories/` — and the fence: "only that directory; leave `## Implementation notes` on the placeholder; all statuses `todo`; no code, no git."

After the return, verify each story file is at its expected path.

## Enrich with code pointers (this skill's own pass)

For each story, grep/glob the repo for the **canonical sibling** — the existing route/handler/module/test closest to the story's work. On a repo bootstrapped by `greenfield`, that's the reference slice named in `CLAUDE.md`. Replace the placeholder with **2-5 concrete pointers**:

```
- `path/to/thing` — why it's the pattern to mirror
```

No code yet in the repo? Say so and write "no sibling yet — the reference slice (or the first story) will become it". **Boundary: pointers to what exists, never a design** — no "create file X with…"; that's the architect's job during the run.

## The story-ready checklist (per story, visibly)

- [ ] **Self-contained** — concrete test: grep the story for dangling references ("as described in the PRD", "see epic", a term defined nowhere in the file).
- [ ] 2-5 **observable, testable** acceptance criteria.
- [ ] **Sized for one feature-flow run** — one coherent vertical slice; too big → cut it in two and renumber *before* going further.
- [ ] `depends_on` declared and pointing at real ids.
- [ ] Placeholder replaced; language conforms.

Any failure → **one** re-dispatch max per story, carrying only the failed items; then hand back with what's left.

## Update the backlog

`<product-root>/backlog.md` — a flat markdown table, created with this header if absent:

```
| id | title | epic | status | depends_on |
|---|---|---|---|---|
```

Top-to-bottom order = intended execution order. Add this epic's stories; never reorder other epics' rows silently. **This table is the only tracker — no sprints, no sprint-status file.**

## Hand back

Recap: N stories, their paths, the backlog. The commit belongs to the user (`commit` skill when present). Next: feed a story to the feature lifecycle — "run story <id>" or just "next story". If no such orchestrator is installed (dev-workflow absent), say so — the story files stand on their own.

## Never / Always

**Never:** cut two epics in one run; invent sprints or a status file; write outside `<product-root>`; create a story with a status other than `todo`; put technical design in the implementation notes; duplicate or renumber existing ids silently; commit or push.

**Always:** verify the self-containment contract with a real grep; keep the backlog in sync with the story files; paste the template verbatim into the dispatch; announce epic, root, and language before dispatching.

## When to decline

- No PRD → `product-spec`.
- The input is a feature spec (≈ one story's worth) → skip cutting; hand it to `feature-flow` directly.
- "Implement the story" → `feature-flow`.
