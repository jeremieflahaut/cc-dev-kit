---
name: commit
description: Create one or more git commits from the working tree changes, grouped by intent. Use when the user asks to commit ("commit this", "fais un commit", "commite ces changements", "commit my changes"). Always propose the commit split BEFORE committing and wait for validation. Composable with the `pr` skill, which pushes and opens the pull/merge request.
---

# commit

Turn the working tree changes into one or more git commits, **grouped by intent**. Always propose the split and wait for the user's go-ahead before committing.

## Core principle: atomic commits by intent

The unit of a commit is **the coherent logical change (the intent)** — never the file.

- **1 intent → 1 commit**, whatever the file count. A feature is its code + wiring + tests = **one** commit.
- **Never "one commit per file".** Splitting by file breaks atomicity (each commit must be checkout-able on its own without breaking the build — code and its tests belong together), and it wrecks revert, cherry-pick, `git bisect`, and `git blame`.
- Many files in one commit is fine. Many **intents** in one commit is a grab-bag to avoid.
- Good-intent test: the commit is describable **in one sentence without "and"**. If the sentence needs an "and", it is probably two commits.

## Flow

1. **Inspect** the working tree:
   - `git status` and `git diff` for tracked modified files.
   - The list of **untracked** files — they are commit candidates too.
   - `git log --oneline -15 --no-merges` to read the repo's existing commit-message language and style.
2. **Group by intent.** Classify every tracked-modified **and** untracked file into logical changes. Detect whether the tree holds one intent or several.
3. **Propose the split BEFORE committing.** Present each planned commit with its file list and its proposed message. **Wait for validation.** Never commit without agreement — even for a single intent.
4. **Commit.** For each approved commit, stage its precise files, then `git commit`.

## Staging

- Stage the **exact files** of each commit: `git add <path> <path>`.
- **Never** `git add -A`, `git add .`, or `git add -u` — they sweep in files that belong to a different intent or nowhere at all.
- **Untracked files are candidates like any other.** A new file is often integral to an intent and goes in the same commit as the related tracked files — classify it by intent, don't skip it.
- Because the split is always proposed and confirmed first, the user sees exactly which files (including untracked ones) will be staged and can exclude any. That confirmation is the guardrail, not a blanket exclusion.
- Watch for untracked files that belong in **no** commit — secrets / `.env`, build artifacts, scratch files, unrelated WIP. Don't bundle them; flag them to the user.

## Guardrails

- Keep the user in control of git: show the split and **ask before every mutating operation**.
- **If on the default branch (`main` / `master`), branch first** — don't commit onto it. Allowed prefixes: `fix/`, `feature/`, `docs/`, `refactor/`, `chore/`. **Confirm the rest of the branch name with the user; don't invent it.**

## Message

- **Format: conventional commits** — `type(scope): subject`. Keep this format even when the repo's history doesn't (match the language, not the format).
- **Language: follow the repo's existing human-written history** (from the `git log` in step 1). Write in the dominant language of recent messages, ignoring merge and bot commits (dependabot, release bots). Never mix languages within one repo. Default to **English** when the history is empty or has no clear majority.
- **Use the scope** — e.g. `feat(auth): add login route`, `fix(billing): arrondit les montants`, `docs(readme): …`.
- Short subject, lowercase after the `:`.
- **Body only when it earns its place**: explain the **why** (the problem solved), not the *what* already visible in the diff.
- **Base the message on the commit's *actual* diff** — `git diff HEAD` of the staged files — not a cumulative feature diff remembered from earlier. On a branch already ahead of `main`, don't describe the whole `origin/main...branch` delta; this commit may be just a small `fix` on top of an already-committed `feat`.
- **Never a `Co-Authored-By` trailer.**
- **No ticket reference** in the message.

## Composability

This skill stops once the commits exist. Pushing and opening the pull/merge request is the `pr` skill's job — hand off to it when the user wants the change published.
