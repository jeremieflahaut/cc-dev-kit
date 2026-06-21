---
name: pr
description: Push the current branch to origin and open a pull request (GitHub) or merge request (GitLab) targeting the default branch. Auto-detects the platform from the origin remote. Use when the user asks to open/create a PR/MR ("open the PR", "push and open the merge request", "fais une PR/MR"). Composable with `commit` — assumes commits are already in place.
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

Pick the tool accordingly:

- **GitHub**: prefer **`gh`**. If `gh` isn't installed, fall back to the **GitHub MCP server** (`create_pull_request` tool) when it's connected — see step 5.
- **GitLab**: **`glab`**, or the `git push -o merge_request.*` options below (no `glab` needed).

Only stop if **no working path** exists for the platform (no CLI **and** no MCP). Never substitute a non-creating shortcut (e.g. a prefilled `…/compare?…` or `…/merge_requests/new?…` URL) for actually opening the PR/MR — that just hands the work back to the user.

## Flow

1. **Check state**: current branch ≠ default branch, commits present. Run `git status --porcelain`; if **not empty**, don't push silently:
   - list the uncommitted changes, distinguishing **tracked modified files** (often an oversight that should be in the PR → flag clearly) from **untracked files** (often WIP left aside → flag without alarm);
   - **ask**: commit first (skill `commit`) **or** push the committed state as-is. No hard block — the user decides.
2. **Build the title** from the current branch name (e.g. branch `fix/login` → title `fix/login`).
3. **Write a short free-form description** (a few lines: the gist of what/why). In **French** by default (personal convention), unless the user asks otherwise — deliberately independent of the commit-message language, which follows the repo history (see `commit`).
4. **Show the recap** (platform, target branch, title, description, draft on/off) and **ask for confirmation** before pushing/creating.
5. **Push, then create the PR/MR:**

   **GitHub — with `gh`:**
   ```bash
   git push -u origin <branch>
   gh pr create --base <default-branch> --head <branch> \
     --title "<title>" --body "<description>" --draft
   ```

   **GitHub — without `gh` (MCP fallback):** push the branch with `git` first (the MCP tool only references an already-pushed branch), then create the PR via the GitHub MCP `create_pull_request` tool.
   ```bash
   git push -u origin <branch>
   ```
   Then call `mcp__github__create_pull_request` with `owner` + `repo` (parsed from the `origin` URL), `head=<branch>`, `base=<default-branch>`, `title`, `body`, `draft`. Load the tool first with ToolSearch `select:mcp__github__create_pull_request` if it isn't already available. It returns JSON `{"url": "...", "id": ...}` — report that `url`.

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

6. **Read the output and report** the PR/MR URL:
   - `gh` prints the PR URL directly.
   - GitHub MCP `create_pull_request` returns JSON `{"url": ...}` → report that `url`.
   - GitLab returns the URL in the push output. A `…/-/merge_requests/<NNN>` URL **with** "already exists" → "MR already existed" + URL (new commits were pushed to it). **Without** it → "MR created" + URL. Only a `…/new?...` URL → no MR created → flag it.

## Defaults

- Target = the repo's default branch.
- **Draft** by default.
- Remove source branch after merge (GitLab `remove_source_branch`); on GitHub this is a repo setting, not a create flag.
- No assignee / reviewer / labels unless explicitly asked.

## Guardrails

- Always show the recap and **ask before** `git push` and PR/MR creation.
