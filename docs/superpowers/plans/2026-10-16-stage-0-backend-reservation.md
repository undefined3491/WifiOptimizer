# Stage 0 Backend Reservation Implementation Plan

> **For agentic workers:** Use `superpowers:executing-plans` for this single fix and independent `gpt-6.1-sol` review before integration. Checkboxes record execution evidence.

**Goal:** Resolve ST0-010: accept at most one backend-switch worker when IPC start requests overlap.

**Architecture:** Reserve the existing in-memory switch state before the first await in `start_backend_switch`. Restore its previous terminal state if preflight returns, fails or is cancelled; after task creation the existing worker owns completion. Preserve the public result/status shapes and both worker routes.

**Tech Stack:** Python asyncio, standard-library unittest and AST-isolated fixtures; existing delivery CI.

**Spec:** [ST0-010 in the inherited-code findings](../../audits/2026-10-15-stage-0-findings.md#st0-010--backend-switch-reservation-occurs-after-an-await).

## Constraints and review focus

- Base: `d4ade2d848c7cc9db5b78afc436e06ab76709199`; branch: `codex/stage-0-backend-reservation`.
- Never import the real plugin or execute production setters, workers, lifecycle hooks or shell scripts on Windows. Execute only the two extracted entry/state methods with inert effects and restricted builtins.
- Hold the first current-backend lookup while sending the second same-target request; only one lookup and worker may run. Cover SteamOS and generic routes.
- Lookup/route/task-creation failure, cancellation and `already_set` must release the reservation and preserve the previous result. Close an unlaunched coroutine if task creation fails.
- Invalid/missing-tool/busy requests must preserve the current job/task. Once task creation succeeds, later logging failure must not release the worker's reservation.
- Effective backend detection (ST0-009), worker/thread cancellation semantics, cross-operation exclusion (ST0-003), profile ownership and recovery are separate work. This change establishes no device compatibility or optimization benefit.
- Preserve version `0.11.6`, technical paths and distribution bytes. No device deployment or Stable publication.

## Task 1 — Serialize switch entry and verify cleanup

**Files:** Modify `main.py` (`Plugin.start_backend_switch`); create `tests/test_backend_reservation.py`; update audit progress, roadmap, AGENTS and Unreleased notes without rewriting baseline evidence.

**Interface:** `async start_backend_switch(self, backend: str) -> dict` keeps its existing accepted/reason fields. `get_backend_switch_status` keeps its existing shape and `switching` phase.

- [x] Write nine isolated tests covering the overlap, pending status, failure/cancellation/retry, terminal-state preservation, rejection and handoff cases above.
- [x] Run `python -m unittest discover -s tests -p test_backend_reservation.py -v` before the fix: nine tests ran, with five failing subcases (two accepted workers on both routes, late reservation, and stuck state on route/task-creation failure).
- [x] Reserve before yielding; track reservation and worker handoff; restore on unlaunched exits in `finally` and close the unlaunched coroutine.
- [x] Repeat focused tests: all nine pass. Independent `gpt-6.1-sol` review reproduced that result and found no blockers; limitations above remain explicit.
- [x] Run all 23 unit tests, Python/Bash syntax checks, pnpm 9.15.9 frozen dependency install, build, project types (`--skipLibCheck`), distribution comparison and `git diff --check`: all passed; tracked distribution unchanged.
- [ ] Commit and push the branch; create/attach a PR to `main`, require `ci-required` success and review before squash merge. Verify main CI after merge.

## Device follow-up

Do not race live WiFi backend services to reproduce this defect. The fixture is the race regression. A future reviewed candidate still needs the existing LCD / SteamOS Stable protocol, including ordinary backend switching/reconnect and sleep/wake with recovery prepared. Passing this task's checks does not close Stage 0 or its other findings.
