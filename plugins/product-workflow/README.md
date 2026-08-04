# product-workflow

Upstream product workflow for Claude Code — the half of the lifecycle that happens *before* any code. Inspired by BMAD-METHOD (self-contained story files, one-question-at-a-time elicitation) and AIDD, trimmed to solo-dev scale: no sprints, no named personas, one product agent.

```
idea → product-brief → product-spec → create-stories → (dev-workflow) feature-flow, one story at a time
```

| Component | Type | Role |
|---|---|---|
| `product-manager` | agent | Non-interactive product writing engine: turns a complete inline brief into a brief / feature spec / PRD / stories. Never interviews — skills gather, it writes. States explicit assumptions instead of guessing silently. |
| `product-brief` | skill | Socratic framing interview in the main conversation — one question per turn, always with a proposed answer to push against. Condensed into a right-sized brief. Optional step. |
| `product-spec` | skill | Requirements document, right-sized and announced: feature spec (no epics) or product PRD (ordered epic list). Fills only the gaps the brief leaves, validates with an inline checklist. |
| `create-stories` | skill | Cuts ONE epic into self-contained story files + a flat ordered backlog. Enriches each story with concrete code pointers, then runs the story-ready checklist. |

## Artifacts (in the target repo, versioned)

```
docs/product/
├── brief.md              # product-brief
├── prd.md                # product-spec (product scale)
├── specs/<slug>.md       # product-spec (feature scale)
├── stories/<epic>.<n>-<slug>.md   # create-stories
└── backlog.md            # create-stories — the only tracker (no sprints)
```

The project's `CLAUDE.md` can name a different product-docs root; generated documents follow the **project's working language**, not the kit's English.

## The story contract

> **A story file is the entire product context of one feature-flow run.** Executing it must need only the story file plus the project's `CLAUDE.md`. If the executor has to reopen the PRD, the story failed its readiness checklist.

That's what makes stories resumable in a fresh session — and what keeps the PRD out of every downstream context window.

## Standalone by design

The plugin works without dev-workflow — the story files stand on their own. When dev-workflow is installed, its `feature-flow` executes stories directly ("run story 2.1", "next story") and keeps story + backlog statuses in sync. Cross-plugin references are by description and degrade out loud, never fail hard.
