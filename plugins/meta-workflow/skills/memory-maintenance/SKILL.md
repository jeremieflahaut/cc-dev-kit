---
name: memory-maintenance
description: Triage and tidy the current project's Claude auto-memory — decide per note whether to keep it, move it to a versioned file (CLAUDE.md / CONVENTIONS.md), fold it into a skill/agent, delete it, or merge duplicates. Verifies real coverage before acting, executes in safe→risky waves, reconciles the index, and never commits. Use when the user wants to review/clean their memory — "faire le tri / le point sur la mémoire", "nettoyer ma mémoire Claude", "triage/tidy/clean up my memory notes". Different from `retro` — this triages the notes that already exist; retro reads past sessions to propose new ones.
tools: Read, Edit, Grep, Bash, AskUserQuestion
---

# memory-maintenance

Review the current project's **auto-memory** and decide, per note, where each fact belongs. The goal is to cut noise while losing nothing: facts that pilot Claude's behaviour stay; shareable conventions and already-encoded facts move out; dead/duplicate notes go.

## Core principle

**Memory = what pilots Claude's behaviour *for this user*** (personal preference, "how to work with me" feedback, an active chantier not derivable from code, an external pointer). Anything that is a **shareable convention** (code/business/doc) or is **already encoded** in the codebase, a `CLAUDE.md`, `CONVENTIONS.md`, an agent or a skill → it should live *there*, not in memory.

## Step 0 — Locate the memory

The auto-memory of the current project is a directory holding `MEMORY.md` (the index, one line per note) + one `<slug>.md` file per note. It lives under `~/.claude/projects/<project-slug>/memory/`. If the path isn't obvious from the session, derive it from the current project slug or ask. Never touch another project's memory.

## Step 1 — Inventory

List the note files (exclude `MEMORY.md`), count them, and read `MEMORY.md`. Group by `metadata.type` (user / feedback / project / reference) to get a feel for the corpus.

## Step 2 — Classify each note (the grid)

Assign every note **one** recommendation:

- **keep** — genuine personal preference, working-style feedback, an in-progress chantier not derivable from code, or an external pointer. **This is the default.**
- **→ CONVENTIONS.md** — a stable, team-shared **code/style** convention (belongs in the versioned conventions file so every dev + agent benefits).
- **→ CLAUDE.md** — a stable **operational** instruction tied to the workspace or a specific service (layout, container names, procedures).
- **→ skill / agent** — a reusable, triggerable procedure/rule better encoded as (or already in) a skill or agent.
- **delete** — already covered (by code / a `CLAUDE.md` / `CONVENTIONS.md` / an agent / a skill / git history), a finished-or-abandoned chantier, or a one-conversation detail.
- **merge** — near-duplicate of another note.

Bias against over-migration: when torn between *keep* and a move, prefer *keep* and flag low confidence.

**Adaptive scale.** For a large corpus (>~30 notes), fan out the classification: one agent per thematic batch returning a structured `{file, recommendation, target, rationale, confidence}`, plus one **cross-check** agent over the whole set (cross-batch duplicates, wrong-looking calls, a prioritized plan). For a small corpus, classify inline.

## Step 3 — Verify before acting (load-bearing)

Never delete or migrate on the strength of a *claim* — including a classifier's own rationale. For each delete/migrate:

- **Grep the real target** (`CONVENTIONS.md`, the relevant `CLAUDE.md`, the agent/skill file, the code) to confirm the fact is actually covered there. If it isn't, downgrade the verdict.
- Before concluding anything from **code or a running container**: confirm the repo/vendor is **synced with `origin/main`** (`git fetch` + compare HEAD), and — when a container is involved — that the service is up to date **and its stack was restarted** with that code. Do **not** `git pull` or restart stacks yourself (mutations the user keeps) — surface and ask.
- Re-challenge the classification **even when merging**: folding notes together does not validate that they should stay in memory.

This step repeatedly overturns first-pass verdicts (a "covered" note whose target is stale; a "delete" whose coverage is only single-service; a periodic fact that's actually obsolete). Budget for it.

## Step 4 — Execute in waves (safe → risky)

Propose each wave and wait for validation before running it:

1. **Deletes with verified verbatim coverage** — zero-risk, do first.
2. **Migrations** — add the fact to its versioned home (respecting that file's own conventions/style/language), *then* delete the note. For a rule covered only single-service, migrate it workspace-wide (e.g. `CONVENTIONS.md`) **before** deleting.
3. **Merges** — consolidate into the **surviving original's file** (keep its slug and `metadata.type`; `Edit` its body to absorb the others, widen its `description`), then delete the redundant notes. Reusing an existing slug means Step 5 sees an in-place edit, not a new index line — don't mint a fresh file for a merge.
4. **Pending pitfalls** — anything flagged "resolve before deleting".

## Step 5 — Reconcile the index

After every add/remove, realign `MEMORY.md`: drop lines whose target file no longer exists, add one line per new note, then assert **#notes == #index-lines, zero orphans**. Reconciliation snippet (note: use **single-quoted** `python3 -c`, never double quotes — backticks in the strings would be executed by bash):

```bash
python3 -c '
import re, os
lines = open("MEMORY.md").read().splitlines()
kept = [l for l in lines if not (re.search(r"\]\(([^)]+\.md)\)", l) and not os.path.exists(re.search(r"\]\(([^)]+\.md)\)", l).group(1)))]
open("MEMORY.md", "w").write("\n".join(kept) + "\n")
'
```
New index lines are added separately (Edit or an appended list) — keep the one-line `- [Title](file.md) — hook` format.

## Guardrails

- **Never commit.** Migrations land in versioned files; the user commits them via the `commit`/`mr` skills. Flag repos where push has side effects (a plugin marketplace release, a docs Pages redeploy).
- **Don't pull or restart** repos/stacks yourself — ask.
- A note's `originSessionId`/`node_type` frontmatter is harness-managed and may be re-added; a fused note's `originSessionId` points at the *fusion* session, not the fact's origin — don't rely on it.
- Losing coverage is worse than keeping noise: a *delete* whose fact lives nowhere else is a sharp deletion — say so and confirm.
