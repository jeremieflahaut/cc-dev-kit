---
name: laravel
description: Laravel / PHP framework patterns to apply when designing, implementing, debugging, or reviewing code in a Laravel project — Actions/FormRequests/Jobs, queues & Horizon, Eloquent vs document/cache stores, multi-service topology, vendored packages, and a Laravel correctness checklist. Use when the working repo's composer.json requires laravel/framework, or when a task involves Laravel/Eloquent/Artisan/Horizon. Supplements the project's own conventions — never overrides them. NOT a workflow driver — for a plan→build→review lifecycle use feature-flow, for test-first use tdd — this only supplies the Laravel patterns those (and the workflow agents) apply.
---

# Laravel patterns

Framework-level knowledge for Laravel/PHP work. It supplements the project you're in; it does **not** override it. Whenever a documented project convention diverges from idiomatic Laravel, **follow the convention** — and, if it's a design-level divergence, surface it (in a plan's *Risks*, or a review *Concern*) so the deviation is a conscious choice, not an accident.

## Situate the project first

Before applying anything below, learn this codebase — it overrides every default here:

1. **Confirm it's Laravel and which version.** `composer.json` → `laravel/framework` constraint, PHP version. Read the repo-root `CLAUDE.md` and the `CLAUDE.md` of the directory you're touching, then follow any pointer to a conventions doc. Those are authoritative.
2. **Map the topology.** Most projects are a single Laravel app. If it's a multi-service workspace, identify which service owns the change and read *its* `CLAUDE.md`/README. Note how services talk: Laravel events, a direct call/dispatch, or — across services — HTTP or a message broker / pub-sub.
3. **Map the data stores.** Which kind of data lives in the relational/Eloquent store vs a document/time-series store vs cache. Don't put one in another's slot. Grep config (`config/database.php`, `config/queue.php`, `docker-compose.yml`) rather than assuming.
4. **Find the queue workers.** Grep `docker-compose.yml` / supervisor configs for queue env vars and Horizon supervisors so you know which workers actually exist.
5. **Check vendored/shared packages before inventing a helper.** Projects often vendor an internal library (`vendor/`-cloned) or a `packages/` workspace. Grep them — reuse beats reimplementation.

**Read a sibling before writing anything.** The established pattern in the repo *is* the standard — namespaces, base classes, method names, return types, casts, `declare(strict_types=1)` (add it only if siblings consistently do), route grouping/naming, column naming. Mirror it exactly; don't import conventions from other projects.

## Designing a Laravel change (plan shape)

When planning a feature that touches multiple files, identify the storage layer for each piece of data, the queue worker any job will run on (if none fits, **flag that infra/compose changes are needed** — don't silently invent a worker), and reuse before new helpers. For new pieces and heavy refactors, favor a **decoupled, testable** design — depend on injected, replaceable collaborators *the way the project already wires its own* — without restructuring working code that fights the established structure.

A typical "create endpoint" plan mirrors an existing sibling:

```
### Files to create
1. `app/Actions/<Domain>/<Verb><Entity>Action.php` — handles X, takes <Request> + caller identity, returns <Type>. Mirror `app/Actions/.../<Sibling>Action.php`.
2. `app/Http/Requests/<Domain>/<Verb><Entity>Request.php` — rules: …
3. `app/Http/Controllers/<Entity>Controller.php` (edit) — add `<method>(…)`, thin: delegate to the Action.
4. `routes/api.php` (edit) — add route, named per the project's route-naming convention.
5. tests — Feature (hits the route) + Unit (exercises the Action), in the project's test layout.

**Storage:** relational tables `…` / document collections `…`
**Queue worker:** `<name>` (existing) | NEW WORKER NEEDED ← flag this
```

## Implementing

- **Match the discovered pattern exactly** — the Action/Service pattern the repo uses, controller base class & namespace, FormRequest vs inline validation, route grouping/naming, column naming, numeric style, where DTOs/Jobs/Models live.
- **Validate at the boundary** with whatever pattern the repo uses (typically FormRequests). No validation/error-handling for impossible cases.
- **Controllers stay thin** — business logic lives in the Action/Service the repo uses, not the controller.
- **Jobs target a real worker** that exists in the relevant service's config; declare the queue. Don't invent a worker.
- **Don't create new top-level layers** (`app/Services/`, `app/Domain/`…) without checking the project already uses them.
- **Tests** follow the project's layout, base traits, grouping and factory rules. Add what the pattern implies (Feature test on the route + Unit test on the logic). Mirror an existing test file.

## Debugging & tuning (operational patterns to discover, not assume)

- **Running artisan / tailing logs / inspecting queues:** check the project for helper scripts and the documented way — one-off commands are often `docker exec <container> php artisan …`; queues are inspected via Horizon. Read the `CLAUDE.md` rather than guessing container names.
- **Query tuning:** watch for N+1 (eager-load with `with()`), queries in loops, missing indexes on newly filtered columns, and the wrong data store for the access pattern. For document/time-series stores use their aggregation pipeline, not Eloquent reflexes.
- **Wiring:** confirm how pieces connect (Laravel events vs direct dispatch vs broker/HTTP across services) before chasing "where is this handled?".
- **Latent bugs:** if a code path would crash or behave wrong in production, don't hide it behind a try/catch or coverage-ignore — surface it; the fix goes in the source. If the project documents known latent bugs (e.g. a section in `tests/claude.md`), read it before touching those files.

## Reviewing — general Laravel correctness (always-on, on top of project conventions)

Flag, with `file:line` and the canonical sibling to mirror:

- Business logic leaking into controllers; fat controllers.
- Inline validation where the project uses a structured pattern (e.g. FormRequests).
- Missing type hints (params, returns, properties) — especially if CI enforces type coverage.
- Needless try/catch wrapping code that can't throw, or swallowing a real bug.
- N+1 queries, queries in loops, missing indexes on new filtered columns; wrong data-store choice for the access pattern.
- Jobs that don't declare a queue, or declare one that doesn't exist in the app's config.
- New `event()`/Listener/Policy usage where the project wires things differently (direct call/dispatch, or — across services — a broker/HTTP) — flag for confirmation.
- Reinventing a helper the project's shared/vendored packages already provide.
- New code that's needlessly hard to test or swap (a new class hard-coding a concrete dependency the project injects elsewhere). Only on the **changed** code — don't ask for a refactor of pre-existing code, and don't flag a deliberate project pattern as a defect.
- Auth: calls that won't work given the project's auth model (e.g. reading the user from the auth guard in a service that receives identity via forwarded headers) — confirm the model from the project's docs first.
- Tests: wrong folder, missing grouping, unscoped assertions (`Model::all()`/`first()` without filtering to data the test created), hardcoded unique values instead of faker, "didn't crash" assertions with no post-condition.

`declare(strict_types=1)` is a blocker only if the repo's files consistently use it. Don't suggest running the formatter/tests unless the project's conventions say to — many run them in hooks/CI.
