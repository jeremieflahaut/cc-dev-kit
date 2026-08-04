---
name: greenfield
description: Bootstrap a brand-new project so the rest of the kit can work on it — short interview (the product in 3 lines, MVP success criteria, stack, constraints), latest stable versions resolved from official docs, the stack's official scaffolder run with user approval, an initial CLAUDE.md written as the project's source of authority, then one thin reference slice built as the canonical sibling every later change mirrors. Use when the user wants to start a project from scratch — "start a new project", "greenfield", "scaffold a new app", "bootstrap this empty repo", "démarre un nouveau projet". NOT for a repo that already has application code or a CLAUDE.md — that's a brownfield; use `feature-flow` or a specialist directly.
allowed-tools: Read, Write, Bash, Agent, Skill, WebFetch, AskUserQuestion
---

# greenfield

The agents in this kit work by reading the project's `CLAUDE.md` and mirroring the nearest existing sibling. A brand-new repo has neither — no rulebook, no sibling, no source of authority — so the kit is unusable on it.

This skill does **not** teach the agents a greenfield mode. It converts the greenfield into a brownfield, **once**: official scaffold → written authority (`CLAUDE.md`) → one exemplary slice to mirror. When it finishes, the project behaves like any existing codebase and `feature-flow` takes over. No agent changes, no parallel mode.

## Why this must run in the main conversation

Same two load-bearing capabilities as `feature-flow`, and a subagent has neither:

- **Pausing to interview the user** — the whole first step is questions.
- **`Agent` to dispatch the builder** for the reference slice.

So invoke this skill at the top level, never from inside another agent.

## The flow (one-shot per project)

### 1. Interview — a minimal brief, not a PRD

If a product brief already exists (default `docs/product/brief.md`, or wherever the project's `CLAUDE.md` points), read it first — the interview shrinks to confirming stack and constraints.

Keep it to ~3 questions (AskUserQuestion or plain conversation):

- **What is it?** The product in 3 lines, plus 3-5 MVP success criteria — observable statements ("a visitor can register and see their dashboard"), not feature lists.
- **Which stack?** If the user hasn't imposed one, propose 2-3 candidates with one-line tradeoffs and let them pick. Never pick silently.
- **Constraints** — data store, deployment target, anything non-negotiable.

Stop there. Deeper product framing (personas, epics, backlog) is out of scope — brief + criteria is the ceiling here. If the user keeps answering at that depth, point them to the product-planning skills (the ones whose descriptions cover shaping a brief, writing a spec/PRD, and cutting stories — the `product-workflow` plugin); if none are installed, say so and keep it a separate exercise.

### 2. Resolve versions from official docs

For every major dependency (framework, language runtime, key libs), resolve the **current stable version** from official documentation — WebFetch on the official site, or a docs MCP when available. Never trust training memory for version numbers.

The greenfield rule: **latest stable + official docs are authoritative here.** Existing code elsewhere is a source of conventions, never of versions.

### 3. Scaffold with the official generator

Use the stack's own scaffolder — `laravel new`, `npm create vite@latest`, `cargo new`, `django-admin startproject`, `dotnet new`, … Never invent a directory tree by hand: the official skeleton is the first corpus of conventions, idiomatic for free.

**Show the exact command and get the user's approval before running it.** It creates files on their machine; that's their call.

### 4. Write the initial CLAUDE.md — the artifact that matters

This is the source of authority every agent in this kit reads at runtime. Keep it short and firm:

- **What this project is** — the 3-line brief and the MVP success criteria from step 1.
- **Conventions** — few but firm: layering, naming, where tests live. Prefer what the scaffold already implies; only add rules the scaffold leaves open.
- **The version rule** — "latest stable + official docs are authoritative in this repo."
- **Commands** — run, test, lint, exactly as the scaffold defines them.
- **The reference implementation** — a pointer to the slice from step 5, named as the pattern to mirror.

### 5. Build the reference slice

Dispatch the implementation agent (route by description — "writes the actual code following conventions") on **one** thin vertical micro-feature: a route → handler → test, or the stack's equivalent. Declare it the reference implementation in `CLAUDE.md`.

This slice is the canonical sibling every later change mirrors — and it validates the `CLAUDE.md` immediately: if the builder stumbles because a rule is missing, fix `CLAUDE.md` on the spot and re-dispatch.

### 6. Hand back

Never `git init`, commit, or push — the first commit belongs to the user (point to the `commit` skill). Close with the point of the whole exercise: "The project is now a brownfield — `feature-flow` takes over from here. If the product is bigger than a couple of features, run a spec + stories pass first (the product-planning skills, when installed) so feature-flow can then execute it one story at a time."

## Artifacts

- **The scaffold and the project `CLAUDE.md` are deliverables** — they belong to the repo, not to `.claude/` scratch space.
- **Stack decision and discarded alternatives** → `.claude/plans/bootstrap.md`, so a later "why not X?" has an answer.

## Never / Always

**Never:** run the scaffolder (or any generator) without showing the command and getting approval; pick a version from training memory; run `git init` / `git commit` / `git push` or any git mutation; hand-roll a directory tree when an official generator exists; expand the interview into a PRD.

**Always:** resolve versions from official docs; write the `CLAUDE.md` before dispatching the builder; build one reference slice before handing back; leave the first commit to the user.

## When to decline

- The repo already has application code or a `CLAUDE.md` — it's a brownfield; `feature-flow` or a specialist handles it.
- The user wants a full product-planning pass (personas, epics, backlog) — out of scope for this skill; do the brief + criteria here and hand the rest to the product-planning skills when installed (`product-workflow`); otherwise say so — it stays a separate exercise.
