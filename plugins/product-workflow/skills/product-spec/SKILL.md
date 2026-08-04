---
name: product-spec
description: Produce the requirements document for a feature or a product — reads docs/product/brief.md when present, fills the gaps by questioning the user in the main conversation, dispatches the product-writing agent to draft, then runs an inline validation checklist (every criterion testable, non-goals explicit, epics listed at product scale). Right-sizes to one of two depths and announces which — a feature spec at docs/product/specs/<slug>.md (no epics) or a product PRD at docs/product/prd.md (with an ordered epic list ready for create-stories). Use when the user wants requirements written down — "write a spec for this", "draft the PRD", "define the requirements", "rédige la spec", "fais le PRD", "définis les exigences". NOT for the upstream idea-shaping interview (use product-brief), NOT for cutting epics into stories (use create-stories), NOT for technical design (that is the architect, via feature-flow).
allowed-tools: Read, Write, Grep, Glob, Bash, Agent, AskUserQuestion
---

# product-spec

One document, two depths — a **feature spec** or a **product PRD**. This skill decides which, announces it, elicits only what's missing, dispatches the writing to the product agent, and validates the result against a checklist before handing back.

## Why this must run in the main conversation

Same two load-bearing capabilities as the sibling skills: pausing to question the user, and `Agent` to dispatch the writer. Invoke at the top level, never from inside another agent.

## Where the artifacts live

Resolve the root once at the start, announce it, then use it everywhere below as `<product-root>`:

- **Default: `docs/product/` at the target repo's root** — versioned, because a fresh clone needs these documents (the rule: describes the product → `docs/`; describes one run → `.claude/`).
- **Override:** if the project's `CLAUDE.md` names a product-docs location, that wins.

This section is the only place the root is defined — if the default ever changes, it changes here and nowhere else.

## Situate yourself first

1. Read `<product-root>/brief.md` if it exists — **never re-ask what the brief already answers**. No brief is fine: a short inline intake replaces it.
2. Read the project's `CLAUDE.md`.
3. Inventory what exists: `<product-root>/prd.md`, `<product-root>/specs/` — an existing document means **update**, not a competing new one; say which you're doing.
4. **Determine the working language** and announce it: user's explicit choice > existing docs under `<product-root>` > conversation language.

## Right-size first

Decide the depth **before** asking anything, and announce it (the user can force the other):

- **Product scale** — several independent capabilities, several user types, "an app / a platform", a full-depth brief → **PRD** at `<product-root>/prd.md`, with an ordered epic list.
- **Otherwise** — **feature spec** at `<product-root>/specs/<slug>.md`, no epics. A feature spec is roughly one story's worth: it feeds `feature-flow` directly, no story cutting needed.

## Fill the gaps

Gap analysis first: compare the available material (brief + the user's request) against the sections of the target format, and question **only the holes** — one at a time, BMAD style:

- **One question per turn**, via AskUserQuestion, always with a **proposed answer to push against** (the "(Recommended)" option built from the brief and the conversation).
- At PRD scale, **co-build the epic breakdown**: propose an ordered cut, let the user react — don't leave the cutting entirely to the writing agent.

## Dispatch the writer

Route by description (the non-interactive product-writing agent). The dispatch prompt carries:

1. The brief verbatim (or "no brief exists" stated plainly) plus the digest of the gap answers.
2. The chosen depth and target path, with the scope fence ("write only that file, under `<product-root>`; no code, no git").
3. `Working language: <x>`.
4. At PRD depth, the epic reminder: epics are **ordered outcome slices** — one-line goal and a rough story count each.
5. Pointers to `CLAUDE.md` and existing product docs.

The document format is the agent's own standard. After the return, **verify the artifact is at the expected path**.

## The validation checklist (run it inline, visibly)

Reread the returned document and check, in front of the user:

- [ ] Every requirement / criterion is **observable and testable** — a test or a look at the running product can settle it.
- [ ] **Non-goals** exist and are not empty.
- [ ] Scope in/out has no grey zone.
- [ ] PRD only — the epic list is present, **ordered**, each epic independently deliverable.
- [ ] **Zero technical solutioning** — a framework/schema/file choice in the document gets removed; that's the architect's territory.
- [ ] The document is in the working language.
- [ ] The agent's `## Assumptions` were shown to the user and settled.

Any failure → **one** re-dispatch carrying only the failed items. A second failure → hand back with the open list; never loop silently.

## Hand back

Point to the document. The commit belongs to the user (`commit` skill when present). Next: PRD → `create-stories`, one epic at a time; feature spec → `feature-flow` directly (it feeds the Frame step; `feature-flow` ships with the dev-workflow plugin — if it isn't installed, say so, the spec stands on its own).

## Never / Always

**Never:** draft the document yourself when the writing agent is available; re-ask what the brief answers; write outside `<product-root>`; let technical solutioning survive validation; commit or push; ask more than one question per turn.

**Always:** announce depth, path, and language before dispatching; run the checklist visibly; have the user settle every assumption.

## When to decline

- The idea is still fuzzy → `product-brief` first.
- "Cut it into stories" → `create-stories`.
- "Implement it" → `feature-flow` (dev-workflow plugin; if absent, say so).
