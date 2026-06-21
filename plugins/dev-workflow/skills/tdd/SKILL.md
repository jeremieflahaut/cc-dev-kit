---
name: tdd
description: Drive a feature test-first (red → green) — write the failing tests FIRST, lock them, then loop hands-free until they pass, wiring the project's OWN test conventions and implementation agents into the loop. Use when the user says "TDD", "test-first", "test-driven", "red-green", "write a failing test then implement", "build/develop X test-first", "faire du TDD", "développe X en TDD". This skill WRITES application code to make the tests pass. NOT for raising coverage on code that already exists — for that, use an after-the-fact testing/coverage skill if the project provides one (it writes tests against existing source and never edits it).
tools: Read, Edit, Write, Glob, Grep, Bash, Agent, AskUserQuestion
---

# TDD loop — test-first, hands-free to green

Drive a feature with the **red → green** cycle: write the tests **first**, watch them fail, then let
the loop write the implementation until every test passes — **without ever editing the tests**.

This skill is **rails, not the solver.** It does not "implement the feature" in one clever pass. It
sets up the playground (failing tests + a locked target + a stop condition) and hands the actual
problem-solving to **a loop of attempts** that converges on green. If you solved it in one shot you
wouldn't need a loop at all — the iteration *is* the mechanism.

## Core principles — read before acting

- **Integration, not substitution.** Plug into the project's existing workflow; introduce no
  conventions of your own. Discover and reuse: the project's **test runner + test conventions** for
  the red phase, the project's **implementation agents** for the green phase, the project's **commit
  skill** for the handoff. The only thing this skill adds is two *temporary* guardrails (a test-lock
  and an until-green gate), removed at the end.
- **Two kinds of cheating, blocked two ways.** (1) *Editing the tests* to make them pass → blocked
  deterministically by a `PreToolUse` hook. (2) *Hard-coding the expected answers* without really
  implementing the feature (overfitting) → caught by an adversarial review in a fresh context.
- **Hands-free until green.** Once set up, it runs without interaction. A `Stop` hook re-runs the
  tests and refuses to end the turn while they are red. There is a built-in safety valve (Claude Code
  releases the stop after ~8 consecutive blocks), so a genuinely unreachable green stops and reports
  instead of looping forever.
- **The tests are the spec.** A test must fail for the *right* reason (assertion / missing symbol),
  never a syntax error or a wrong test command.
- **Run from the main conversation.** This skill asks one setup question and dispatches subagents —
  both need the top-level thread. Don't run it from inside a subagent.

---

## Step 0 — Discover the stack's existing test workflow

Detect the **test command** from the project, in this order — stop at the first that fits:

- A documented test convention in the repo (e.g. a `tests/`-level doc, or a `## Testing` section in
  `CLAUDE.md`) → read it and use the exact command + any container/invocation it specifies (including
  a `docker exec <container> ./vendor/bin/pest`-style wrapper). Honor its conventions for the red
  tests too.
- `composer.json` (script `test`) / `phpunit.xml` → Pest/PHPUnit.
- `package.json` (script `test`, or vitest/jest dep) → `npm test` / `pnpm test` / `yarn test`.
- `pytest.ini` / `pyproject.toml` / `tox.ini` → `pytest`.
- `go.mod` → `go test ./...`. · `Cargo.toml` → `cargo test`. · `.rspec` / `Gemfile` → `rspec`.
- A `Makefile` with a `test` target → `make test`.

Also note the project's **test file location** (where tests live), which becomes the lock target.

If the command is **ambiguous or undetectable**, ask — this is the **only** interaction point, before
the autonomous run starts. Use it to also confirm you may run the suite repeatedly during the loop
(this satisfies any "ask before running the tests" project rule — one confirmation covers the run):

```
AskUserQuestion → "Which command runs this project's tests?"
  options: <best-guess command>, "Other"  (header: "Test command")
```

State the detected command and the feature you're about to drive, then proceed.

## Step 1 — RED: write the failing tests

From the user's feature description, write tests describing the expected behaviour — concrete
input/output pairs and the edge cases — **following the project's existing test conventions** (the
documented convention / framework style from Step 0). No house style of your own.

Be explicit that this is TDD: **write no implementation, and no stub that fakes a pass.** Then run the
test command and **confirm the tests fail for the right reason** (assertion or missing symbol — not a
syntax error, not a wrong command). Show the red output as evidence.

Record the **exact list of test files you wrote/touched** — this is the **locked set**.

## Step 2 — Lock the tests + arm the loop (the guardrails)

Create a small, self-contained guard kit under `.claude/tdd/` and wire two hooks into the project's
`.claude/settings.local.json` (the *local*, gitignored settings — never `settings.json`, we don't
commit guardrails).

**`.claude/tdd/locked-tests.txt`** — one locked test path per line. Use **sufficiently-qualified**
paths (e.g. `tests/Feature/FooTest.php`, not a bare `FooTest.php`) so the suffix match below can't
deny edits to an unrelated same-named file.

**`.claude/tdd/lock-tests.sh`** — deny any edit to a locked test:

```bash
#!/usr/bin/env bash
set -euo pipefail
dir="$(cd "$(dirname "$0")" && pwd)"
file="$(jq -r '.tool_input.file_path // empty')"
[ -z "$file" ] && exit 0
while IFS= read -r locked; do
  [ -z "$locked" ] && continue
  if [ "$file" = "$locked" ] || [[ "$file" == *"$locked" ]]; then
    jq -n '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",
      permissionDecisionReason:"TDD green phase: the tests are locked. Implement the code to satisfy them; do not modify the tests."}}'
    exit 0
  fi
done < "$dir/locked-tests.txt"
exit 0
```

**`.claude/tdd/check-green.sh`** — re-run the suite; block the stop while red. Substitute the Step 0
command into `TEST_CMD`:

```bash
#!/usr/bin/env bash
dir="$(cd "$(dirname "$0")" && pwd)"
TEST_CMD='<DETECTED TEST COMMAND FROM STEP 0>'
if eval "$TEST_CMD" >"$dir/green.out" 2>&1; then
  exit 0   # green → allow the stop
fi
jq -n --rawfile out "$dir/green.out" \
  '{decision:"block", reason:("Tests are still red — keep implementing (never edit the locked tests) until they pass.\n\nLatest output:\n" + $out)}'
exit 0
```

`chmod +x` both scripts. Then **merge** (do not overwrite) into `.claude/settings.local.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Edit|Write",
        "hooks": [ { "type": "command", "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/tdd/lock-tests.sh\"" } ] }
    ],
    "Stop": [
      { "hooks": [ { "type": "command", "command": "bash \"$CLAUDE_PROJECT_DIR/.claude/tdd/check-green.sh\"" } ] }
    ]
  }
}
```

Read the file first and splice these in alongside any existing `hooks`; keep everything else intact.
Remember exactly what you added so Step 5 can remove only that.

## Step 3 — GREEN: hand the work to the loop

Now the loop runs the show. The instruction to follow each iteration:

> Write the **minimal** implementation that satisfies the locked tests. Run the tests. Iterate.
> **Never** touch the locked tests.

The `Stop` hook keeps the turn alive until the suite is green; the `PreToolUse` hook makes editing a
test impossible. **This is where the problem gets solved — by the loop, not by this skill.**

**Delegate the implementation to the project's own coding agent** when one exists — always
**discover what's actually available** via the `Agent` tool / `.claude/agents` first. As an
illustration, in a Laravel repo with the `laravel-workflow` plugin installed that resolves to
`laravel-feature-builder` (new code) or `laravel-senior-developer` (cases needing reasoning); in a
stack-agnostic repo with `dev-workflow` it's `feature-builder` / `senior-developer`; in another
project it will be whatever specialist exists there. Fall back to implementing inline only when no
specialist agent fits. The guardrails apply to delegated work too — a subagent's edits go through the
same `PreToolUse` lock, and the `Stop` gate fires when the **main** agent tries to finish, so the loop
runs *through* the delegation (main → delegate → return → run tests → still red? continue/re-delegate).
*If a `PreToolUse` hook turns out not to fire inside a subagent on this Claude Code build, also pass
"do not modify the tests" explicitly in the delegation prompt as a belt-and-suspenders.*

## Step 4 — Anti-overfitting review (the second kind of cheating)

Once green, the lock stops anyone editing the tests — but the implementation could still have
**hard-coded the test inputs** instead of implementing the feature. Dispatch a subagent in a **fresh
context** (e.g. a code-reviewer / senior agent) that sees only the **diff + the feature description**
and answers: *does this genuinely implement the feature, or does it overfit the specific test cases?*
Tell it to report only **correctness / requirement** gaps, not style. A real gap → add a test for it
(back to Step 1, red) and let the loop close again. Otherwise, done.

## Step 5 — Teardown + handoff

- **Disarm:** remove the two hooks you added from `.claude/settings.local.json` (leave any pre-existing
  hooks untouched) and delete `.claude/tdd/`. The tests are unlocked again.
- **Recap:** tests written, green status (show the passing output), review verdict.
- **Commit (propose, never automatic):** offer to commit the **tests first, then the code** via the
  project's `commit` skill. Do not run git directly.

---

## Loop engines (reference)

This skill defaults to the **`Stop` + `PreToolUse` hooks** above because they give hands-free
execution *and* a deterministic no-cheat guarantee. Two alternatives, if the context calls for them:

- **`/goal "all tests pass"`** — session-only, no files to clean up; a separate evaluator re-checks
  after each turn. Lighter, but the no-cheat rule rests on model discipline, not a hard block.
- **`claude -p` in a shell loop** — fully scripted / out-of-session, each iteration in a *fresh*
  context (strongest anti-bias): `until <test-cmd>; do claude -p "Tests are red — fix the CODE, never
  the tests" --allowedTools "Edit,Bash(<test-cmd>)"; done`. Scope `--allowedTools` to exclude the test
  files.

## Not this skill

For **raising coverage on code that already exists** (write tests after the fact, never edit the
source) — use whatever after-the-fact testing/coverage skill the project provides, if any. This skill
is the opposite direction: tests first, then write the code.
