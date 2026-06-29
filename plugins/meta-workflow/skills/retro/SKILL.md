---
name: retro
description: Offline retrospective on your past Claude Code sessions ("Dream") — sweeps the local transcripts over a time window, distills the friction (where the user corrected Claude, tool errors, permission rejections), extracts the recurring patterns, and proposes durable fixes (feedback memories, CLAUDE.md rules, skill/agent tweaks, hooks, permission pre-approvals). Run it periodically (e.g. weekly) or when the user wants to understand what keeps going wrong in how they work with Claude. Triggers — "/retro", "run a retro", "what went wrong this week", "analyse my sessions", "how can I improve my Claude Code usage", "fais une rétro", "analyse mes sessions", "qu'est-ce qui n'a pas marché".
tools: Read, Edit, Write, Glob, Grep, Bash, AskUserQuestion
---

# Session retrospective ("Dream")

An offline reflection loop: instead of improving behaviour only in-the-moment, replay recent
sessions *after the fact*, detect the friction, and turn it into **durable, legible improvements**.
Claude Code has no fine-tuning — the output is versioned context (memories, CLAUDE.md rules, skill
tweaks, hooks, permission settings), not weights. That makes it more actionable than a fine-tune,
not less: every change is readable and reversible.

## Step 1 — Extract the signals

Run the extractor (stdlib only; it emits a distilled JSON, never the raw transcripts):

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/retro/extract_frictions.py" --days 7 --out <scratchpad>/retro.json
```

- Default window: **7 days**. Match `--days` to what the user asks ("this month" → 30, "since the
  last retro" → compute the gap).
- `--root` defaults to `~/.claude/projects` (where Claude Code stores session transcripts). Override
  only if transcripts live elsewhere.
- Write the output to the session scratchpad, never into a project.
- The JSON contains: `meta`; `corrections` (the ore: the user's natural-language pushbacks/
  disagreements + a snippet of what Claude was doing just before); `tool_errors` (technical errors
  aggregated by tool + signature); `rejections` (Claude attempted an action the user blocked — a
  signal of either misjudgement on Claude's part or a permission worth pre-approving).

If `corrections_found` is 0 or very low, widen the window before concluding anything.

## Step 2 — Read and cluster (do not recite)

Read the JSON. **Do not dump the raw list** at the user — synthesising is the whole point of a retro.
Cluster into **recurring themes**:

- The same correction recurring in different words = a strong pattern (e.g. language conventions,
  privacy/persona rules, "you're going too fast", "this is over-engineered", tool/workflow
  preferences).
- Repeated `tool_errors` = a fixable behavioural pattern (e.g. `Edit` "File has not been read yet"
  in bulk → Claude must Read before Edit; a missing binary → an environment gap to document).
- Frequent `rejections` on one tool = either Claude proposes unwanted actions (fix the behaviour) or
  a safe tool worth pre-approving.

For each theme, separate what is **Claude's behaviour** (fix via memory / CLAUDE.md / hook) from what
is the **user's environment/config** (permissions, missing binaries, token scopes).

### Precision caveat

The detection heuristic favours recall over precision. In a learning/Socratic context (e.g. a
mentor-style project), the user's *questions* ("why not a getter here?", "wouldn't that raise an
error?") look like corrections but are not friction — discard them. It is the analysing model's job
to filter residual noise by judgement, not the extractor's.

## Step 3 — Produce the report

Short and actionable, **3 to 6 frictions max**, ranked by frequency/impact. For each:

- **The pattern** in one sentence + occurrence count/evidence (quote 1-2 short verbatims).
- **The cause**: Claude's behaviour, a missing convention, or a setting.
- **The proposed fix**, concrete and typed:
  - *`feedback` memory* (recurring guidance on how Claude should work — with **Why** / **How to apply**),
  - *CLAUDE.md rule* (project, or workspace root),
  - *skill/agent tweak* (description, trigger, body),
  - *hook* (automatic guardrail, e.g. block a dangerous pattern),
  - *permission pre-approval* (via the `update-config` skill / settings.json),
  - *environment gap* (to install/document).

## Step 4 — Apply (only on approval)

**Apply nothing automatically.** Present the report, then ask which fixes to apply. When applying:

- memories → write to the user's memory directory if memory is enabled (typically
  `~/.claude/projects/<project>/memory/`), and add the one-line pointer to its `MEMORY.md`. Check an
  existing memory doesn't already cover it — update rather than duplicate.
- hooks / permissions → go through the `update-config` skill.
- CLAUDE.md rules → edit the right file (workspace root vs project).

Honour any confidentiality rules the user has set (in their memories or CLAUDE.md): never write
protected names (employer, private projects) into files the user has marked as public.

## Notes

- Everything is local and read-only over the transcripts; nothing is sent anywhere.
- To automate weekly: this skill can be driven by the `schedule` skill or a cron that opens a PR of
  proposed fixes — suggest it only if the user asks.
