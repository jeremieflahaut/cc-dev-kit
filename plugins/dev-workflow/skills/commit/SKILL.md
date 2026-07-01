---
name: commit
description: Create one or more git commits from the working tree changes, grouped by intent. Use when the user asks to commit ("commit this", "fais un commit", "commite ces changements"). Always propose the commit split BEFORE committing and wait for validation. Composable with the `pr` skill (which pushes + opens the pull/merge request).
---

# commit

Create one or more commits from the working tree changes, **grouped by intent**.

## Principle: atomic commits by intent

A commit's unit is **the coherent logical change (the intent)**, never the file.

- **1 intent → 1 commit**, regardless of file count (e.g. one feature = its implementation + wiring + tests = **1** commit).
- **Never "one commit per file"**: it breaks atomicity (a commit must be checkout-able on its own without breaking anything — the code and its tests go together), revert/cherry-pick, `git bisect` and `git blame`.
- Many files is **not** a problem. Many **intents** in the same commit = a grab-bag to avoid.
- Quick test for a good intent: the commit can be described **in one sentence without "and"**, and the message describes an intent (not a filename, not a vague `wip`/`update`/`misc`).

## Flow

1. **Inspect**: `git status` + `git diff` (tracked modified files) **and** the list of untracked files — all are candidates. Also `git log --oneline -15 --no-merges` to pick up the language of the repo's existing commit messages.
2. **Group by intent**: classify modified **and untracked** files by logical change. Detect whether the working tree has **multiple intents**.
3. **Propose the split BEFORE committing**: present the planned commit(s) to the user — for each one: the file list and the proposed message. **Wait for validation.** Never commit without agreement, even if there's only one intent.
4. **Commit**: for each validated commit, explicitly stage the relevant files then `git commit`.

## Staging

- Always stage the **precise files** of a commit: `git add <path> <path>`.
- **Never** `git add -A`, `git add .` or `git add -u`.
- **Untracked files are candidates like any others**: a new file is often integral to an intent, and goes in the same commit as the related tracked files. Classify them by intent just like modified ones.
- Since the split is **always proposed and confirmed** before committing, the user sees exactly which untracked files would be staged and can exclude any — that's the guardrail, not a default exclusion.
- Stay vigilant on untracked files that have no business in any commit (secrets/`.env`, build artifacts, scratch, unrelated WIP): don't bundle them and flag them if they're lying around.

## Guardrails

- Keep the user in control of git: show the split/diff and **ask before** every mutating operation.
- If on the default branch (`main`/`master`), **branch first** instead of committing on it. Naming: allowed prefixes `fix/`, `feature/`, `docs/`, `refactor/`, `chore/`; **ask/confirm** the rest of the name (don't invent it).

## Message

- Format: **conventional commits**: `type(scope): subject` — the format stays conventional even when the history isn't (adapt the language, not the format).
- **Language: follow the repo's existing commit history** (from the `git log` done at the Inspect step) — write in the dominant language of recent **human-written** messages (ignore merge and bot commits: dependabot, release bots…), never mix languages within the same repo. Default to **English** when the history is empty or has no clear majority.
- The **scope is used** (e.g. `fix(billing): arrondit les montants…`, `feat(auth): add login route`, `docs(readme): …`).
- Short, descriptive subject, lowercase after the `:`.
- **Body** when the change warrants it: explains the **why** (the problem being solved), not the "what" already visible in the diff.
- **Base the message on the commit's *actual* diff, not a cumulative one held in mind**: read `git diff` / `git diff HEAD` of the files being staged and describe *that* delta. On a branch already ahead of `main`, don't reuse an `origin/main...branch` diff remembered from an earlier review — it describes the whole feature, whereas this commit may be only a small delta (e.g. a 3-line `fix` on top of an already-committed `feat`).
- **Never a `Co-Authored-By` trailer** — no co-author.
- **No ticket reference** in the commit message.
