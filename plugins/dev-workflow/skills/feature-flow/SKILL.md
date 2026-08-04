---
name: feature-flow
description: Orchestrate a feature end-to-end — frame → plan → build → review → fix-loop → acceptance check → hand back — by dispatching the available specialist agents (the plugin-provided architect / feature-builder / senior-developer / code-reviewer, plus any extras in `.claude/agents/` or `~/.claude/agents/`), tracking state in artifacts under `.claude/{plans,reviews,lifecycle}/`. Frames observable acceptance criteria up front (skipped for clear-cut requests) and resolves them before calling the feature done. Matches each step to an agent by its description, not a fixed name. Use when the user wants to implement a feature end-to-end, chain plan + build + review, resume a feature in progress ("continue feature X"), or execute a prepared story file — "run story 2.1", "next story", "implémente la story 2.1" (the story seeds the slug and the acceptance criteria). NOT for a one-shot task one specialist handles (call it directly). NOT for test-first work with locked tests — use the `tdd` skill.
allowed-tools: Read, Edit, Write, Bash, Agent, Skill
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

## Story intake (product handoff)

If the request is a prepared story — a path under a `stories/` directory, a story id ("run story 2.1"), or "next story" — the story seeds the flow instead of a free-form request. (The story format is owned by the story-cutting skill — `create-stories`, `product-workflow` plugin.)

1. **Resolve it.** Explicit path or id → read that story file. "Next story" → read the product backlog (`docs/product/backlog.md`, or the product-docs root the project's `CLAUDE.md` names) and take the first `todo` row whose `depends_on` are all `done`. Nothing resolves → say so and run the normal flow.
2. **Seed the flow.** Slug = the story filename without `.md`. The story's acceptance criteria become the lifecycle `acceptance:` list verbatim (all `pending`). Step 0 (Frame) is satisfied by the story — skip it out loud.
3. **Mark it in progress.** Flip the story frontmatter `status:` to `in-progress` and its backlog row to match — a file write, reversible; committing it stays with the user.
4. **The story file is the whole product context.** Paste it into every dispatch brief (with the usual `CLAUDE.md` pointers) — never the PRD. A story that forces you to open the PRD failed its readiness checklist: tell the user and suggest re-running the story-cutting skill on it instead of compensating silently.

At handback (step 6), flip the story and its backlog row to `review` — `done` is the user's call once tests pass and the change is merged.

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
0. Frame        → this skill + user     (skip for clear-cut requests — the default; frame when the request is vague or cross-component)
1. Plan         → architect            (skip if single-file / obvious shape, or user says "no plan")
2. Build        → feature-builder (pattern work) OR senior-developer (needs judgment)
3. Review       → code-reviewer         (skip only if user says "no review")
4. Fix          → re-dispatch to the builder/senior with the review report as input
5. Re-review    → code-reviewer         (loop 3↔4 until Blockers is empty; hard cap 3 rounds)
5bis. Verify    → built-in `code-review` skill, ONCE, on the final diff (skip out loud if unavailable)
5ter. Accept    → this skill            (resolve the `acceptance:` criteria; skip out loud if none were framed)
6. Hand back    → user                  (tests, commit, push, PR — NEVER automated, NEVER skipped)
```

Routing calls to make as you go:
- **Frame or skip?** A crisp request whose expected result is self-evident (a fix, a small feature with an obvious shape) → skip out loud. Skipping is the default — don't tax small fixes with ceremony. A vague or cross-component request → ask the user 2-3 questions max, then write 2-5 **observable** acceptance criteria (things a test or a look at the running code can check, e.g. "the endpoint returns 422 on an invalid email") into the lifecycle `acceptance:` field.
- **Product-scale request?** "Build me an app", a multi-epic scope, several distinct user-facing capabilities in one ask → don't one-shot it. Say so and point to the product-planning skills (brief → spec/PRD → stories — the `product-workflow` plugin) so the work comes back here one story at a time. If they aren't installed, say that too and offer to frame the single thinnest slice instead.
- **Plan or skip?** One file with an obvious shape → skip. Multiple files or cross-component → architect required.
- **Builder or senior?** Template-shaped work (a CRUD endpoint mirroring a sibling) → builder. Anything needing judgment (perf, tricky bug, transversal refactor, ambiguous design) → senior.
- **Fix-loop budget:** cap at 3 rounds. If round 3 still has a Blocker, set the lifecycle to `blocked` and escalate to the user with the open blockers — don't loop silently.
- **Verification gate (5bis):** once the fix-loop has converged, if a built-in `code-review` skill is available in the session, invoke it (Skill tool) ONE time on the final diff. It hunts correctness bugs with independent multi-agent verification — it complements the conventions reviewer, never replaces step 3. A confirmed finding triggers one more fix round (step 4) followed by a quick re-review by the reviewer agent — **never a second `code-review` pass**; if that round fails, go `blocked` as usual. If the skill isn't available, say so and move to handback.
- **Acceptance check (5ter):** once the fix-loop and the verification gate are done, reread the lifecycle `acceptance:` list (skip out loud if it's empty). For criteria the project's test suite can verify, **offer** to run the test command (discovered from `CLAUDE.md` or the manifest scripts) — never run it unprompted; the default remains that tests belong to the handback. A failed criterion triggers one more fix round through the normal mechanics (step 4 + a ledger row). Criteria that can't be automated are listed explicitly at handback. Mark each criterion `verified` (checked, passes) or `handed-back` (left to the user, named at handback) — `done` requires that no criterion is still `pending`.
- **Every fix round is a correction:** log each one in the correction ledger (see State artifacts) before re-dispatching. This includes fix rounds opened by the verification gate — a confirmed gate finding on a specialist's diff is a ledger row (cause is usually `rule-missing`, generic correctness no written rule covered).

## State artifacts

Create under `$PWD/.claude/` (make the tree if absent). `<slug>` is kebab-case from the request (a story-seeded run uses the story filename instead, dots included) — confirm it with the user if ambiguous, so a later "continue feature X" resolves.

```
.claude/
├── plans/<slug>.md          # the planning agent's own output
├── reviews/<slug>.md        # latest review (overwritten each round)
├── reviews/<slug>-r<N>.md   # prior rounds, archived only if the loop iterated
├── lifecycle/<slug>.md      # the state machine — this skill owns it
├── lifecycle/<slug>.briefs.md  # verbatim dispatch prompts, one section per dispatch (see The dispatch contract)
└── agent-feedback.md        # correction ledger, shared across features (see below)
```

For the **plan** and **review** files, have the specialist write **its own standard output format** — don't impose a competing template. Only the **lifecycle file is owned here**; write it before the first dispatch and update it after every agent returns:

```yaml
---
feature: <slug>
description: <user request, one line>
current_step: planned|building|reviewing|fixing|done|blocked
                         # done means the review loop converged AND every acceptance
                         # criterion is verified or handed-back — never "review passed" alone
acceptance: []           # from Frame (empty if skipped); each item:
                         # - { criterion: <observable check>, status: pending|verified|handed-back }
steps_done: []
steps_skipped: []        # each with its reason
agents_invoked:
  - { agent: <name>, invoked_by: feature-flow, step: <step>, at: <ISO>, artefact: <path>, brief: <heading in the briefs file> }
blockers: []             # populated when current_step = blocked
---
## Notes
<what was observed, what the user changed mid-flow>
```

`invoked_by` records each dispatch's parent (`feature-flow` for direct dispatches; a specialist's name if it sub-dispatched), so the whole dispatch graph is reconstructible from this file alone.

### The correction ledger (`.claude/agent-feedback.md`)

Every time a specialist's output has to be corrected — the reviewer raises a Blocker on the builder's diff, a fix round is dispatched, or you adjust an agent's artifact yourself before continuing — append **one row** to `.claude/agent-feedback.md` (create it with the header if absent):

```markdown
| date | agent | symptom | correction | cause |
|---|---|---|---|---|
| <ISO> | <agent name> | <what was wrong, one clause> | <what fixed it, one clause> | rule-missing \| rule-ignored \| routing |
```

`cause` routing: **rule-missing** — no written rule covered it (the durable fix is documenting it); **rule-ignored** — the agent had the instruction and broke it (the durable fix is emphasis/wording); **routing** — wrong specialist for the task (the durable fix is a `description` tweak). A reviewer that tags findings `[rule-violated — <source>]` / `[rule-missing]` hands you the cause directly. One row per correction, no prose — this ledger is the raw material offline retros turn into durable prompt/`CLAUDE.md` fixes.

## The dispatch contract

A specialist has no memory of this conversation. Every `Agent` prompt must carry:

1. **Self-contained context** — paste the relevant slice of the user's request plus the upstream artifact (plan, review report) verbatim.
2. **The artifact path to write** — e.g. "Write your plan to `.claude/plans/<slug>.md` in your standard format."
3. **The scope fence** — "Only these files. Don't run tests. Don't commit." Align it with the agent's own limits (architect doesn't code; reviewer doesn't fix).
4. **Where upstream context lives** — point to the project `CLAUDE.md`, the plan file, the review file, as relevant.

**Persist every brief.** Before each dispatch, append the exact prompt you are sending to `.claude/lifecycle/<slug>.briefs.md` — one section per dispatch, headed `## <step> — <agent> — <ISO timestamp>` — and record that heading in the matching `agents_invoked` entry (`brief:`). The lifecycle file says *where* the flow was; the briefs file says *exactly what the agent in flight was told*. A session that dies mid-build resumes from the verbatim brief, not from a coarse step name.

After each return, **verify the artifact is at the expected path**. If the agent wrote it elsewhere or only in chat, move it into place before continuing.

## Interaction rhythm

- **Before the first dispatch**, show the chain (including whether Frame was applied or skipped) and get a go-ahead: "I'll run architect → builder → reviewer, then the `code-review` verification gate and the acceptance check. Confirm or redirect."
- **After each stage**, summarize in 1–2 sentences what came back and what's next, then dispatch or hand back.
- **At the end**, point to the trace and the acceptance status: "Full lifecycle in `.claude/lifecycle/<slug>.md`. Acceptance: 3 verified, 1 handed back (manual UI check). Tests, commit, and PR are yours."

## Resuming a feature

On "continue feature X" or a slug already under `.claude/lifecycle/`:

1. Read the lifecycle file.
2. Restate the current step, what's done, and where the `acceptance:` criteria stand.
3. Propose the next step from `current_step` (if `blocked`, list the blockers first). If the interrupted step had an agent in flight (last `agents_invoked` entry has no artifact on disk), read its section in `.claude/lifecycle/<slug>.briefs.md` and offer to re-dispatch from that exact brief.
4. Wait for confirmation before dispatching.

## Never / Always

**Never:** write application code, design a plan, or review code yourself; run `git commit` / `git push` / `git checkout -b` / `gh pr create` or any git/remote mutation; run the test suite without offering first; skip the handback (step 6); dispatch without first writing/updating the lifecycle file and persisting the brief; pretend a missing specialist is present; loop the fix-cycle past 3 rounds without escalating; mark a feature `done` while an acceptance criterion is still `pending`; quietly reopen the PRD during a story-seeded run (report the story as not self-contained instead).

**Always:** hand back to the user before any irreversible action; keep the lifecycle file current; route by description match; resolve every framed acceptance criterion (`verified` or `handed-back`) before closing; keep a seeded story's `status:` and its backlog row in sync with the lifecycle.

## When to decline

- No specialist exists at all (nothing in the `Agent` subagent types, nor either agents dir) — there's nothing to dispatch.
- No specialist covers the stack and the user rejects degraded mode — suggest creating the specialist.
- The request is a one-shot a single specialist handles — tell the user to call that specialist directly; orchestration would only add latency.
