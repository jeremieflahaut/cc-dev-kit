---
name: pr
description: Push the current branch to origin and open a pull request (GitHub) or merge request (GitLab) targeting the default branch. Auto-detects the platform from the origin remote. Use when the user asks to open/create a PR/MR ("open the PR", "push and open the merge request", "fais une PR/MR"). Composable with `commit`: assumes commits are already in place.
---

# pr

Push the current branch to `origin` and open a **pull request (GitHub)** or **merge request (GitLab)** targeting the default branch. Detect which platform from the `origin` remote.

## Prerequisites

- Commits already exist (see the `commit` skill). `git push` only pushes committed history: uncommitted changes stay local and **will be absent from the PR**.
- We're on a **dedicated branch**, not on the default branch (branch creation/naming belongs to the `commit` skill). `pr` only **reuses the current branch name** (for the title).

## Detect the platform & default branch

```bash
git remote get-url origin            # github.com → GitHub ; gitlab.* → GitLab
git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@'   # default branch; fall back to main/master
```

Pick the CLI accordingly: **`gh`** for GitHub, **`glab`** for GitLab. If the matching CLI isn't installed, say so and stop (don't fall back to a half-working path).

## Flow

1. **Check state**: current branch ≠ default branch, commits present. Run `git status --porcelain`; if **not empty**, don't push silently:
   - list the uncommitted changes, distinguishing **tracked modified files** (often an oversight that should be in the PR → flag clearly) from **untracked files** (often WIP left aside → flag without alarm);
   - **ask**: commit first (skill `commit`) **or** push the committed state as-is. No hard block — the user decides.
2. **Ask for ticket number(s)** if the user's workflow uses them (optional — skip if they don't).
3. **Build the title**: branch name, optionally prefixed with `[<tickets>]` if given. e.g. branch `fix/login`, ticket 1234 → `[1234] fix/login`; no ticket → `fix/login`.
4. **Write a short free-form description** (a few lines: the gist of what/why). Personal convention is **French** — keep it French unless the user asks otherwise.
5. **Show the recap** (platform, target branch, title, description, draft on/off) and **ask for confirmation** before pushing/creating.
6. **Push, then create the PR/MR:**

   **GitHub:**
   ```bash
   git push -u origin <branch>
   gh pr create --base <default-branch> --head <branch> \
     --title "<title>" --body "<description>" --draft
   ```

   **GitLab** (via push options, single command):
   ```bash
   DESC='Line 1.\n\nLine 2.\n\n- bullet\n- bullet'   # literal \n, NOT real newlines
   git push -u origin <branch> \
     -o merge_request.create \
     -o merge_request.target=<default-branch> \
     -o merge_request.title="<title>" \
     -o "merge_request.description=$DESC" \
     -o merge_request.draft \
     -o merge_request.remove_source_branch 2>&1
   ```
   ⚠️ **GitLab push options reject real newlines** (`fatal: push options must not have new line characters`). Encode line breaks as literal `\n` inside a **single-quoted** bash string — GitLab renders them server-side. Capture stderr too (GitLab messages come back as `remote:`).

7. **Read the output and report** the PR/MR URL:
   - `gh` prints the PR URL directly.
   - GitLab returns the URL in the push output. A `…/-/merge_requests/<NNN>` URL **with** "already exists" → "MR already existed" + URL (new commits were pushed to it). **Without** it → "MR created" + URL. Only a `…/new?...` URL → no MR created → flag it.

## Defaults

- Target = the repo's default branch.
- **Draft** by default.
- Remove source branch after merge (GitLab `remove_source_branch`); on GitHub this is a repo setting, not a create flag.
- No assignee / reviewer / labels unless explicitly asked.

## Guardrails

- Always show the recap and **ask before** `git push` and PR/MR creation.
