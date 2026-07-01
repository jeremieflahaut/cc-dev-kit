---
name: tdd
description: Drive a feature test-first (red → green) — write the failing tests FIRST, lock them, then loop hands-free until they pass, wiring the project's OWN test conventions and implementation agents into the loop. Use when the user says "TDD", "test-first", "test-driven", "red-green", "write a failing test then implement", "build/develop X test-first", "faire du TDD", "développe X en TDD". This skill WRITES application code to make the tests pass. It gets you to green with locked tests — reviewing the result (overfit check) and committing are handed back, not orchestrated here. NOT for raising coverage on code that already exists — for that, use an after-the-fact testing/coverage skill if the project provides one (it writes tests against existing source and never edits it). For a plan → build → review feature lifecycle that is NOT test-first, use the `feature-flow` skill.
tools: Read, Edit, Write, Glob, Grep, Bash, Agent, AskUserQuestion
---

# TDD (red → green, locked tests)

## What this is

This skill is **rails, not the solver.** It does not itself figure out the implementation. It sets up three things — (1) a suite of **failing tests** that pin the target behaviour, (2) a **lock** so those tests cannot be edited, and (3) a **stop condition** that only releases once every test passes — and then hands the actual problem-solving to a loop of implementation attempts that converge on green.

The discipline it enforces is the one thing humans and models both cheat on under pressure: **the spec (the tests) is frozen before the code exists, and the code is what moves.** Weakening a test to make it pass is the failure mode this skill exists to prevent.

Scope ends at **green + clean teardown.** Reviewing the diff for overfit and committing are explicitly handed back to the user, not orchestrated here.

## Integration, not substitution

Do not invent a test framework, a coding style, or a commit flow. Reuse what the project already has:

- **Red phase** → the project's own test runner and test conventions.
- **Green phase** → the project's own implementation agents.
- **Handoff** → the project's own commit skill.

The only things this skill *adds* are **two temporary guardrails** (a lock hook + a stop hook), and it **removes them at teardown.** Nothing it installs survives the session.

## Must run in the main conversation

Run this skill in the **top-level thread.** It asks a setup question (AskUserQuestion) and dispatches subagents — a subagent can do neither. If invoked from inside a subagent, stop and report that it must be run from the main conversation.

---

## Step 0 — Discover the test command

Find how this project runs its tests, in this order of authority (first hit wins):

1. **Documented convention** — `CLAUDE.md`, `CONTRIBUTING.md`, `tests/claude.md`, a `README` "Testing" section.
2. **PHP** — `composer.json` scripts (`test`, `test-unit`); else `phpunit`/`pest` (`vendor/bin/pest`, `vendor/bin/phpunit`).
3. **JS/TS** — `package.json` scripts (`test`); else `vitest`/`jest`.
4. **Python** — `pytest` / `pytest -q`.
5. **Go / Rust / Ruby** — `go test ./...` / `cargo test` / `bundle exec rspec`.
6. **Makefile** — a `test` target.

Also determine, and hold onto:

- The **exact command** to run the suite (and, if the runner supports it, the narrower command to run only the new tests — faster loops).
- The **test file location + naming convention** (e.g. `tests/Feature/`, `*.test.ts`, `*_test.go`). This becomes the **lock target**.

If the runner is genuinely ambiguous (multiple plausible commands, no documented default), **ask via AskUserQuestion** — and in the same question confirm you may **run the suite repeatedly** during the loop (some projects gate on slow/expensive suites). Otherwise proceed with the discovered command.

## Step 1 — RED: write the failing tests first

Write tests that **describe the expected behaviour**, following the project's conventions (structure, naming, assertion style, fixtures/factories). **No implementation, no stubs, no scaffolding of the code under test** — only the tests.

Run them. Confirm they **fail for the right reason**: an assertion failure or a missing-symbol / undefined-class error — *not* a syntax error in the test, *not* a wrong test command, *not* a misconfigured harness. A test that errors out before it can assert is not a red test; fix it until the failure is a genuine "behaviour absent" failure.

Record the **exact set of test files** you wrote — the locked set.

Then **PAUSE at a RED checkpoint.** Present to the user:

- the list of locked test files,
- the red run output (showing the right-reason failures).

**Get explicit sign-off before arming the guardrails.** The spec freezes on approval — this is the user's chance to correct the target before the code is written against it. Do not proceed to Step 2 unattended.

## Step 2 — Lock + arm the guardrails

On approval, create a guard kit under `.claude/tdd/` and wire two hooks into **`.claude/settings.local.json`** — the **local, gitignored** settings file. **Never** touch `.claude/settings.json` (shared/committed): these guardrails are temporary and personal.

### 2a. Record the locked test paths

Write one locked test file path per line to `.claude/tdd/locked-tests.txt` (paths relative to the repo root, as the runner reports them).

### 2b. The lock hook — `PreToolUse` on Edit|Write

Deny any edit whose `file_path` matches a locked test path. Match by **exact-or-suffix** so an unrelated same-named file elsewhere is not wrongly denied.

Write `.claude/tdd/guard-lock.sh`:

```bash
#!/usr/bin/env bash
# PreToolUse hook (Edit|Write): deny edits to locked test files.
set -euo pipefail

payload="$(cat)"
locked_file="$(cd "$(dirname "$0")" && pwd)/locked-tests.txt"
[ -f "$locked_file" ] || exit 0

target="$(printf '%s' "$payload" | jq -r '.tool_input.file_path // empty')"
[ -n "$target" ] || exit 0

while IFS= read -r locked; do
  [ -n "$locked" ] || continue
  # Match exact path or suffix (so repo-relative locked paths match absolute targets),
  # anchored on a path boundary so "Foo.php" can't match "OtherFoo.php".
  if [ "$target" = "$locked" ] || [ "${target%"/$locked"}" != "$target" ]; then
    jq -n --arg reason "TDD lock: '$locked' is a locked test file and cannot be edited during the red→green loop. Change the implementation instead. (Remove the lock via the tdd skill's teardown if the spec genuinely needs to change.)" \
      '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "deny", permissionDecisionReason: $reason}}'
    exit 0
  fi
done < "$locked_file"

exit 0
```

### 2c. The stop hook — `Stop` re-runs the suite

Re-run the detected test command. **Block** the stop while red (surfacing the latest output so the loop knows what still fails); **allow** it (exit 0) once green.

Write `.claude/tdd/guard-stop.sh` — substitute `<TEST_COMMAND>` with the command from Step 0:

```bash
#!/usr/bin/env bash
# Stop hook: block stopping while tests are red; allow once green.
set -uo pipefail

cd "$(dirname "$0")/../.." || exit 0   # repo root (.claude/tdd -> repo root)

output="$(<TEST_COMMAND> 2>&1)"
status=$?

if [ "$status" -eq 0 ]; then
  exit 0   # green — release the stop
fi

reason="TDD stop-guard: tests are still RED — keep implementing (do NOT edit the locked tests). Latest output:
$output"
jq -n --arg reason "$reason" '{decision: "block", reason: $reason}'
exit 0
```

> **Safety valve:** Claude Code releases a blocked stop after ~8 consecutive `block` decisions. So an unreachable green does **not** loop forever — it eventually stops and reports still-red, which then flows into teardown (Step 4). This is intended: it prevents an infinite spin on an impossible spec.

### 2d. Arm the hooks (chmod + merge)

Make both scripts executable, then **merge** the hook config into `.claude/settings.local.json` **without clobbering existing hooks**. Use `jq` so a hand-written merge can't drop a pre-existing entry:

```bash
chmod +x .claude/tdd/guard-lock.sh .claude/tdd/guard-stop.sh

SETTINGS=.claude/settings.local.json
[ -f "$SETTINGS" ] || echo '{}' > "$SETTINGS"

tmp="$(mktemp)"
jq '
  .hooks //= {} |
  .hooks.PreToolUse = ((.hooks.PreToolUse // []) + [{
    matcher: "Edit|Write",
    hooks: [{ type: "command", command: "\"$CLAUDE_PROJECT_DIR\"/.claude/tdd/guard-lock.sh" }]
  }]) |
  .hooks.Stop = ((.hooks.Stop // []) + [{
    hooks: [{ type: "command", command: "\"$CLAUDE_PROJECT_DIR\"/.claude/tdd/guard-stop.sh" }]
  }])
' "$SETTINGS" > "$tmp" && mv "$tmp" "$SETTINGS"
```

**Remember exactly what you added** (the two entries above), so teardown removes *only* those and leaves any pre-existing hooks intact. Hook changes take effect on the next turn — the guardrails are live for the green loop that follows.

## Step 3 — GREEN: hand the work to the loop

Hand the problem to an implementation loop with a single mandate:

> Write the **minimal** implementation to satisfy the locked tests. Run the tests. Iterate until they all pass. **Never touch the locked tests.**

**Delegate to the project's own coding agent** when one fits. Discover it first — check the Agent tool's available agent types and `.claude/agents/` (and `~/.claude/agents/`). With the `dev-workflow` plugin present, that's **`feature-builder`** (template-shaped, the design is clear) or **`senior-developer`** (needs judgment — bug-shaped, cross-cutting, or non-obvious). Fall back to writing the implementation **inline** only if no project agent fits.

The guardrails apply to delegated work too (hooks are session-global). But **also pass "do not modify the tests" in the delegation prompt** as belt-and-suspenders — `PreToolUse` may not fire inside every subagent context, so the instruction is a second line of defence.

The Stop hook keeps re-running the suite and blocking until green, so the loop is effectively hands-free once dispatched.

## Step 4 — Teardown + handoff

**Always tear down — even if it ended red via the safety valve.** Never leave guardrails armed.

1. **Remove the two added hooks** from `.claude/settings.local.json` — and *only* those two (leave any pre-existing hooks). Then **delete `.claude/tdd/`.**

   ```bash
   SETTINGS=.claude/settings.local.json
   tmp="$(mktemp)"
   jq '
     .hooks.PreToolUse = [ .hooks.PreToolUse[]? | select(
       (.hooks[]?.command // "") | test("/.claude/tdd/guard-lock.sh") | not) ] |
     .hooks.Stop = [ .hooks.Stop[]? | select(
       (.hooks[]?.command // "") | test("/.claude/tdd/guard-stop.sh") | not) ] |
     if (.hooks.PreToolUse | length) == 0 then del(.hooks.PreToolUse) else . end |
     if (.hooks.Stop | length) == 0 then del(.hooks.Stop) else . end |
     if (.hooks | length) == 0 then del(.hooks) else . end
   ' "$SETTINGS" > "$tmp" && mv "$tmp" "$SETTINGS"

   rm -rf .claude/tdd
   ```

2. **Recap** the locked tests and the final green output (or the still-red output if the safety valve fired — in which case say so plainly and hand back the remaining failures).

3. **Flag the overfit risk.** Green proves the tests pass — it does **not** prove the implementation generalises. It may be hard-coded to the fixtures. Hand back to the user to **review the diff** (e.g. dispatch `code-reviewer`, or run the `feature-flow` review step). If review surfaces a gap, the fix is *another red test* — add it and loop again (re-arm from Step 1). Do not patch the code silently to cover a case no test pins.

4. **Offer to commit** tests-first-then-code via the project's **commit skill**. Never run `git` directly.

---

## Alternative loop engines (reference)

The Stop-hook loop above is the default. Two alternatives exist for the GREEN phase — same red-first setup, different engine:

- **`/goal "all tests pass"`** — session-only loop, no cleanup to undo. Lighter, but the no-cheat guarantee rests on **model discipline** rather than a hard lock; there's no `PreToolUse` denial, so a stray edit to a test isn't blocked.
- **`claude -p` in a shell loop** — spawn a fresh headless run each iteration (`while ! <TEST_COMMAND>; do claude -p "make the tests pass without editing them"; done`). Fresh context each pass is the **strongest anti-overfit bias** (no memory of prior hacks). Scope `--allowedTools` to **exclude Edit/Write on the test files** so the loop physically cannot touch the spec.

Use the default hook loop unless the user asks for one of these; mention them if the suite is expensive (headless) or if a hard lock is unwanted (`/goal`).

## Boundaries

- **Not** for raising coverage on code that already exists → use an after-the-fact testing/coverage skill (it writes tests against existing source and never edits it).
- **Not** for a plan → build → review lifecycle that isn't test-first → use `feature-flow`.
