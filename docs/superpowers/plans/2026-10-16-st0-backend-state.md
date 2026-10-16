# ST0-009 backend effective-state Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Separate backend desired-config from effective-state with verified transitions, repair acceptance, and rollback (ST0-009).

**Architecture:** Split conf readers from service readers; gate `already_set` on convergence; check every transition step; verify effective at the end; expose both in status/diagnostics; render divergence in `BackendToggleRow` with retry. Backend covered by isolated fixtures (scripted conf bytes + `systemctl` outputs); frontend by typecheck + build + review.

**Tech Stack:** Python `main.py`, React TS `src/`, `unittest` isolated fixtures on Windows, Git Bash on PATH, `tsc --noEmit --skipLibCheck`, `pnpm run build` (pnpm v9).

**Spec:** `docs/superpowers/specs/2026-10-16-st0-backend-state-design.md`

## Global Constraints

- Windows: isolated fixtures only; never import the real root plugin; never execute real setters/lifecycle/switchers/installer/dispatcher. AST-extract + fail-closed builtins (established patterns). Conf-file reads via allow-listed scripted `open` fixtures.
- Git Bash on PATH (`bash --version` works).
- No `connection.autoconnect-priority 100` writes; owner-model/snapshot/reconnect-reporting semantics unchanged (consulted only).
- No new IPC methods; no signature changes; only additive keys (`backend_desired`, `backend_effective`, `backend_services`, `repair`, `repair_of`, `rolled_back`, `errors` entries). `live.wifi_backend` shape unchanged.
- `tsconfig.json` strict + `noUnusedLocals/Parameters`; no new deps.
- No version bump, no Stable/beta, no Watchdog, no ST0-003 machinery/retry timers, no 001/002/003/018, no service-state restoration beyond D5 rollback.

## Review Focus

- A dead target service must read as failed/diverged — expect step-named failure, never conf-echo success.
- A converged backend must stay a cheap no-op — expect `already_set` preserved for true agreement.
- A diverged backend must offer repair — expect same-target accepted with `repair: True`.
- A failed repair must attempt rollback — expect previous conf + service restored best-effort and reported.
- Status must show both values — expect desired/effective/services/drift keys with exact names.

---

### Task 1: Backend fixture + red tests (desired/effective/guard/verify/repair)

**Files:**
- Create: `tests/test_backend_state.py`
- Modify: none

**Interfaces:**
- Consumes: canonical names from spec (helpers `_read_desired_backend`, `_read_effective_backend`; status keys; `repair`/`repair_of`/`rolled_back`/`errors[]`; step codes per D3).
- Extracted methods (AST, fail-closed builtins): `_read_desired_backend`, `_read_effective_backend`, `start_backend_switch` guard section, `_backend_switch_worker`, `_generic_backend_switch_worker` (whole workers — sections are not separately extractable).
- Stub namespace: `open` allow-listed for the 4 conf paths with scripted bytes; `os` spies; `asyncio` real with `sleep` no-op spy (reconnect polls must not burn 15s); `_run_cmd` scripted per command (`systemctl is-active/is-enabled`, helper, NM restart, `nmcli`) + `run_calls` log; in-memory settings/snapshot; `decky` null; `time` real.
- Produces: `BackendStateFixture` used by Tasks 2-3.

- [ ] **Step 1: Write failing tests**: `dead_target_service_is_failed_not_success`, `conf_echo_never_verifies`, `true_agreement_stays_already_set`, `diverged_accepts_repair`, `needs_reboot_rejects_not_already_set`, `every_systemctl_step_checked`, `final_verification_reads_effective`, `failed_repair_rolls_back_reported`, `status_shows_both_with_drift`, `diagnostics_has_backend_triple`.
- [ ] **Step 2: Run to verify they fail with AssertionError (not ImportError/NameError)** Run: `python -m unittest tests.test_backend_state -v` Expected: FAIL on behavior asserts. Then full suite: new file red, all other files green (`discover` exits non-zero overall — that is the red signal, not a regression).
- [ ] **Step 3: Add fixture only** (no production change); re-run: imports clean, behavior asserts still FAIL.
- [ ] **Step 4: Run full suite** `python -m unittest discover -s tests` Expected: new file red, all other files green.
- [ ] **Step 5: Commit** `git add tests/test_backend_state.py; git commit -m "test: isolated ST0-009 backend-state fixtures (red)"`

### Task 2: Split reads + converged gate + status (D1/D2/D6/D8)

**Files:**
- Modify: `main.py` (new readers, guard, `get_status`, `get_diagnostic_info`, `_main` sanity feed, `tests/test_backend_reservation.py` already_set cases)
- Test: `tests/test_backend_state.py`

**Caller re-pointing (all 4):** workers' final reads → `_read_effective_backend`; `get_status().wifi_backend` → `_read_desired_backend` (plus new effective keys); `_main` sanity → D1 pair (log-only kept); `get_diagnostic_info` → backend triple.

**Interfaces:**
- Consumes: Task 1 fixture.
- Produces: exact helper names `_read_desired_backend`, `_read_effective_backend`; gate outcomes (`already_set` / `repair: True` / `needs_reboot`); status keys `backend_desired`, `backend_effective`, `backend_services`, `drift.backend`; `live.wifi_backend` unchanged.

- [ ] **Step 1: Verify red** Expected: FAIL on read/guard/status tests.
- [ ] **Step 2a: Implement readers** per D1 (conf order unchanged + source path; services both with four-state distinction).
- [ ] **Step 2b: Implement gate** per D2 (converged no-op, repair accept, reboot reject with in-memory outstanding rule). Update `tests/test_backend_reservation.py` already_set cases to script desired+effective (agreement→no-op, desired-only→repair-accept); add needs_reboot set→reject→clear→accept fixture case.
- [ ] **Step 2c: Implement status/diagnostics/boot feed** per D6/D8 (wire `"unknown"`, `drift.backend`, diagnostics triple + failure-path test).
- [ ] **Step 3: Run** `python -m unittest tests.test_backend_state -v` Expected: read/guard/status tests PASS.
- [ ] **Step 4: Run full suite** `python -m unittest discover -s tests` Expected: no regressions (89 + new).
- [ ] **Step 5: Commit** `git add main.py tests/test_backend_state.py; git commit -m "fix: backend desired/effective split with converged gate (ST0-009)"`

### Task 3: Checked steps + effective verification + repair/rollback (D3/D4/D5)

**Files:**
- Modify: `main.py` (generic worker steps, both workers' final verification, repair path, rollback)
- Test: `tests/test_backend_state.py`

**Interfaces:**
- Consumes: Task 2 readers/gate.
- Produces: step-named failures, effective-based success, `repair_of`, `rolled_back`, `errors[]` entries; `reconnect_timed_out` stays connectivity-only.

- [ ] **Step 1: Verify red** Expected: FAIL on step/verify/repair tests.
- [ ] **Step 2a: Implement step checks** per D3 (generic each-command; SteamOS kept).
- [ ] **Step 2b: Implement effective verification** per D4.
- [ ] **Step 2c: Implement repair + rollback** per D5 (per-route: generic conf bytes/delete, steamos helper with previous target; update the 5 diagnosis-only comment/doc sites to cite the transition-scoped distinction; per-route tests).
- [ ] **Step 3: Run** `python -m unittest tests.test_backend_state -v` Expected: PASS.
- [ ] **Step 4: Run full suite + syntax** `python -m unittest discover -s tests`; preflight `bash --version`; `python -m py_compile main.py`.
- [ ] **Step 5: Commit** `git add main.py tests/test_backend_state.py; git commit -m "fix: verified backend transitions with repair and rollback (ST0-009)"`

### Task 4: Divergence UI (D7)

**Files:**
- Modify: `src/components/BackendToggleRow.tsx`, `src/index.tsx` (only as needed), `src/types.ts` (LiveStatus new keys; `BackendSwitchStartResult.repair`; `BackendSwitchResult`: `repair_of`/`rolled_back`/`errors`; ERROR_MESSAGES for D3 codes)
- Test: typecheck + build + review checklist (no frontend unit infra)

**Render checklist (verify by reading code):** agreement shows effective; divergence shows `configured X · effective Y/unknown` with retry action and no optimistic checked; retry clears error pre-start, blocked while `in_progress`; `""`/tool-unavailable goes to explicit unknown branch; `backendSwitch.error` exclusion reused; `getBadge` untouched.

- [ ] **Step 1: Implement divergence states + retry** per D7.
- [ ] **Step 2: Verify** `tsc --noEmit --skipLibCheck` exit 0, `pnpm run build` exit 0 (pnpm v9, frozen lockfile). Record pre-build `git rev-parse HEAD` + `dist/index.js` hash; confirm post-build `dist/` diff only from this change.
- [ ] **Step 3: Run full backend suite** `python -m unittest discover -s tests` Expected: green.
- [ ] **Step 4: Commit** `git add src dist; git commit -m "fix: backend divergence display with retry (ST0-009)"`

### Task 5: Docs state update (no product behavior change)

**Files:**
- Modify: `docs/audits/2026-10-15-stage-0-findings.md` (ST0-009 correction evidence)
- Test: none (docs only)

- [ ] **Step 1: Update findings** correction evidence for ST0-009 only; remaining findings stay open; Stage 0 stays open.
- [ ] **Step 2: Verify** `git log --stat -5` shows only this package's commits and `git status` is clean apart from intended files (post-commit diff is empty by design — never use it as evidence).
- [ ] **Step 3: Commit** `git add docs/...; git commit -m "docs: ST0-009 correction evidence"`
