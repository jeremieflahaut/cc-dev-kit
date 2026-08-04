---
name: product-brief
description: Socratic product-framing interview run in the main conversation — problem, target users, jobs-to-be-done, constraints, non-goals, success signals — condensed into a right-sized brief at docs/product/brief.md (one page for a small feature, a full brief for a product). Use when the user has an idea to shape before any spec exists — "I have an idea", "help me think through this project", "frame this need", "j'ai une idée de projet", "aide-moi à cadrer ce besoin", "réfléchissons à ce produit". Optional step — product-spec can start without it. NOT for writing the requirements document itself (use product-spec), NOT for cutting stories (use create-stories), NOT for scaffolding code (use greenfield).
allowed-tools: Read, Write, Grep, Glob, Bash, Agent, AskUserQuestion
---

# product-brief

Elicitation lives here; drafting is dispatched. This skill interviews the user and condenses what it learns into a faithful digest — the product-writing agent turns that digest into the brief. Never write the brief yourself when that agent is available.

This step is **optional** in the pipeline (the equivalent of BMAD's Analysis phase): `product-spec` knows how to start without a brief.

## Why this must run in the main conversation

Two capabilities are load-bearing, and a subagent has neither:

- **Pausing to interview the user** — the whole skill is questions.
- **`Agent` to dispatch the writer.**

So invoke this skill at the top level, never from inside another agent.

## Where the artifacts live

Resolve the root once at the start, announce it, then use it everywhere below as `<product-root>`:

- **Default: `docs/product/` at the target repo's root** — versioned, because a fresh clone needs these documents (the rule: describes the product → `docs/`; describes one run → `.claude/`).
- **Override:** if the project's `CLAUDE.md` names a product-docs location, that wins.

This section is the only place the root is defined — if the default ever changes, it changes here and nowhere else.

## Situate yourself first

1. `pwd`; read the project's `CLAUDE.md` if it exists.
2. Check whether `<product-root>/brief.md` already exists. If it does, propose **update** vs **rewrite** — never overwrite silently.
3. Note whether the repo already has code — if so, the questions anchor in what exists instead of a blank page.
4. **Determine the working language** and announce it: the user's explicit choice > the language of existing docs under `<product-root>` > the conversation's language. The kit being in English is never a reason to write the brief in English.

## The interview — one question at a time

Six themes to cover, **in dependency order** (each answer shapes the next question):

1. **The problem** — and who has it, today, concretely.
2. **Users & jobs-to-be-done** — who they are, what job they hire this for.
3. **Existing alternatives** — how the job gets done today, and why that isn't enough.
4. **Constraints** — time, money, platform, anything non-negotiable.
5. **Non-goals** — what this deliberately won't do.
6. **Success signals** — observable statements that would prove it works.

Rules of the interview:

- **One question per turn, never a battery.** Ask it with AskUserQuestion and always put a **proposed answer on the table** (the "(Recommended)" option, built from everything already said) — the user reacts to a proposal instead of facing a blank page.
- **Dig into the previous answer** rather than marching through the list — the themes are a coverage check, not a script.
- **Restate to validate** — after a dense answer, reflect it back in one sentence before moving on.
- **Challenge a solution disguised as a need** — "you named a tool; what's the job it does?".
- **Stop** when every theme has substance, or when the user says stop. Partial coverage is fine — the gaps become `## Assumptions` for the writer.

## Right-size, then dispatch

Announce the depth before dispatching, based on what the interview revealed:

- **One-pager** — a small feature or a narrow tool: the five brief sections, one page.
- **Full brief** — product scale: several capabilities or user types.

Build the **interview digest**: faithful bullets per theme, keeping the user's exact words on the problem statement. Then dispatch the product-writing agent — **route by description**: the agent whose description says it drafts product documents from a complete inline brief, never interviews. The dispatch prompt carries:

1. The digest verbatim, gaps included.
2. The chosen depth (one-pager / full brief).
3. `Working language: <x>`.
4. The target path — `<product-root>/brief.md` — and the scope fence: "write only that file, under that root; no code, no git."
5. Pointers to the project `CLAUDE.md` and any existing product docs.

After the return, **verify the artifact is at the expected path**; if it landed elsewhere or only in chat, move it into place.

## Review with the user

Present the brief, walk the `## Assumptions` section explicitly and have the user settle each one. One corrective re-dispatch max — beyond that, iterate by hand with the user in the document.

## Hand back

Point to `<product-root>/brief.md`. The commit belongs to the user (point to the `commit` skill when present). Next step: a spec/PRD pass turns this into requirements (`product-spec`) — or `greenfield` first if the repo is empty and the user wants to scaffold (`greenfield` ships with the dev-workflow plugin; if it isn't installed, say so instead of failing hard).

## Never / Always

**Never:** draft the brief yourself when the writing agent is available; write outside `<product-root>`; commit or push; march through the six themes like a form; ask more than one question per turn; default to English for the document.

**Always:** announce root, language, and depth; keep the digest faithful to the user's words; put a proposed answer on the table with every question; verify the artifact path after dispatch.

## When to decline

- Requirements are already clear → `product-spec` directly.
- The user wants code → `greenfield` (empty repo) or `feature-flow` — dev-workflow skills; if they aren't installed, say so.
- The user wants stories → `create-stories` (needs a PRD first).
