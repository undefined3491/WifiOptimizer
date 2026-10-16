# ST0-007/008 + 014/017/019 truthful results Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Verified reconnect reporting, failed-write intent blocking, and lossless UI result handling (ST0-007/008/014/017/019 + ST0-013 reject recovery).

**Architecture:** `_hard_reconnect` returns a stage dict with `verified`; setters gate `reconnected` on it; every checked write failure blocks intent with a named error; DNS rolls back paired keys; buffer status checks 8 keys; `src/index.tsx` + `PanelFooter` consume all result shapes with catch/reject paths and stale labeling. Backend covered by isolated fixtures; frontend by typecheck + build + review.

**Tech Stack:** Python `main.py`, React TS `src/`, `unittest` isolated fixtures on Windows, Git Bash on PATH, `tsc --noEmit --skipLibCheck`, `pnpm run build` (pnpm v9).

**Spec:** `docs/superpowers/specs/2026-10-16-st0-truthful-results-design.md`

## Global Constraints

- Windows: isolated fixtures only; never import the real root plugin; never execute real setters/lifecycle/installer/dispatcher. AST-extract + fail-closed builtins (patterns: `tests/test_restoration.py`, `tests/test_profile_ownership.py`).
- Git Bash on PATH (`bash --version` works).
- No `connection.autoconnect-priority 100` writes; ST0-005/006 owner model and ST0-004/016 snapshot semantics unchanged (only consulted).
- No new IPC methods; no signature changes; only additive result keys (`reconnect` object, `errors` entries, `relock` object). One intentional value change: reset `success: False` when `errors[]` non-empty (frontend updated here).
- `tsconfig.json` strict + `noUnusedLocals/Parameters`; `pnpm.peerDependencyRules.ignoreMissing: [react, react-dom]` stays; do not add deps.
- No version bump, no Stable/beta, no Watchdog, no ST0-009/013-race/001-003/018 work.

## Review Focus

- A dead radio must read as dead radio — expect stage-named failure, never bare `reconnected: True`.
- A failed write must leave intent/owner/slot untouched — expect named error + convergent retry.
- A failed aggregate child must render under its own key — expect per-child errors + counts banner.
- A rejected promise must render — expect no handler without `catch`.
- A failed status poll must not poison or fake-fresh data — expect stale labeling and error-with-retry.

---

### Task 1: Backend fixture + red tests (reconnect + failed writes)

**Files:**
- Create: `tests/test_truthful_results.py`
- Modify: none

**Interfaces:**
- Consumes: AST-extracted `_hard_reconnect`, setters, `_clear_owned_profiles`, `reset_settings`, `get_status` buffer section; stubbed `_run_cmd` with per-command scripted results + `run_calls` log, `_get_wifi_interface`/`_get_active_connection_uuid` scripted, in-memory settings/snapshot, `time.sleep` no-op.
- Produces: `TruthfulFixture` used by Tasks 2-3.

- [ ] **Step 1: Write failing tests**: `radio_on_fail_reports_dead_radio`, `reconnect_unverified_never_true`, `offline_foreign_reconnect_skipped_detail`, `aggregates_compute_reconnected_from_children`, `sysctl_fail_blocks_intent`, `txqueuelen_fail_blocks_intent`, `cake_del_idempotent_vs_real_fail`, `dispatcher_fail_blocks_intent`, `sysfs_pcie_modprobe_fail_blocks_intent`, `dns_rollback_on_second_key_fail`, `band_preclear_checked`, `buffer_status_checks_all_keys`, `reset_errors_nonempty_means_success_false`.
- [ ] **Step 2: Run to verify they fail with AssertionError (not ImportError/NameError)** Run: `python -m unittest tests.test_truthful_results -v` Expected: FAIL on behavior asserts (baseline suite stays 71 green).
- [ ] **Step 3: Add fixture only** (no production change); re-run: imports clean, behavior asserts still FAIL.
- [ ] **Step 4: Run full suite** `python -m unittest discover -s tests` Expected: baseline green, new file red.
- [ ] **Step 5: Commit** `git add tests/test_truthful_results.py; git commit -m "test: isolated ST0-007/008 truthful-results fixtures (red)"`

### Task 2: Structured reconnect (D1/D2/D5)

**Files:**
- Modify: `main.py` (`_hard_reconnect`, all setter reconnect sites, `_clear_owned_profiles`, `optimize_safe`, `reapply_all`, band relock reporting)
- Test: `tests/test_truthful_results.py`

**Interfaces:**
- Consumes: Task 1 fixture.
- Produces: stage dict + `verified` + `active_uuid_after`; `reconnected` gated; aggregates computed; `reconnect`/`relock` additive details.

- [ ] **Step 1: Verify red** Expected: FAIL on reconnect tests.
- [ ] **Step 2a: Implement `_hard_reconnect` dict** per D1 (short poll 1–3 tries, never throws, dead-radio signal).
- [ ] **Step 2b: Wire setters + `_clear_owned_profiles`** per D2 (verified-gated `reconnected`, skipped detail).
- [ ] **Step 2c: Aggregates + band relock split** per D2/D5 (computed top-level, `reconnect` vs `relock`).
- [ ] **Step 3: Run** `python -m unittest tests.test_truthful_results -v` Expected: reconnect tests PASS.
- [ ] **Step 4: Run full suite** `python -m unittest discover -s tests` Expected: no regressions (71 + new).
- [ ] **Step 5: Commit** `git add main.py tests/test_truthful_results.py; git commit -m "fix: verified reconnect reporting (ST0-007)"`

### Task 3: Failed-write intent blocking (D3/D4/D6 + reset value)

**Files:**
- Modify: `main.py` (sysctl/txqueuelen/CAKE-del/dispatcher/modprobe/sysfs/PCIe/NM-conf sites, DNS rollback, buffer status, reset `success` rule)
- Test: `tests/test_truthful_results.py`

**Interfaces:**
- Consumes: Task 2 reconnect.
- Produces: named errors, intent/owner/slot preserved, convergent retries, 8-key buffer check, reset `success: False` on non-empty `errors`.

- [ ] **Step 1: Verify red** Expected: FAIL on failed-write tests.
- [ ] **Step 2a: Implement write checks** per D3 (idempotent-del exception included).
- [ ] **Step 2b: Implement DNS rollback** per D4.
- [ ] **Step 2c: Buffer 8-key check + reset success rule** per D6/D8. Also update pinned `tests/test_restoration.py` reset asserts: clean reset (empty `errors`) stays `success: True`; fallback reset (non-empty `errors`) becomes `success: False`.
- [ ] **Step 3: Run** `python -m unittest tests.test_truthful_results -v` Expected: PASS.
- [ ] **Step 4: Run full suite + syntax** `python -m unittest discover -s tests`; preflight `bash --version`; `python -m py_compile main.py`.
- [ ] **Step 5: Commit** `git add main.py tests/test_truthful_results.py; git commit -m "fix: failed writes block intent with named errors (ST0-008)"`

### Task 4: Frontend result consumption (D7)

**Files:**
- Modify: `src/index.tsx`, `src/types.ts` (PluginStatus: `unknown_owners`, stale/error state; ERROR_MESSAGES: new backend codes), `src/components/PanelFooter.tsx`, `src/components/ActionsSection.tsx` (only as needed for error display)
- Test: typecheck + build + review checklist (no frontend unit infra in repo)

**Render checklist (verify each by reading the code, not by build):**
- every `handleToggle`-family path sets `errors[key]` on reject; Force-Reapply maps each failed child to its key + banner shows applied/total/failed (+`total==0` info); reset warning banner lists `errors[]`; update apply/check/channel surface resolved-`False` and rejections; diagnostics check both `success` flags; poll reject sets `backendSwitch.error` with controls locked; no-status shows error+retry; stale shows timestamped banner; `transfer_warnings`/`unknown_owners`/setter-`errors[]` appended to messages or bannered.

**Interfaces:**
- Consumes: Tasks 2-3 result shapes.
- Produces: catch on all handlers, Force-Reapply child mapping + banner, reset/update/diagnostic checks, poll-reject recovery, status stale/error states, warnings rendering.

- [ ] **Step 1: Implement handler catches + Force-Reapply mapping + reset/update/channel/diagnostic checks** per D7 (exact error codes per spec D3: `sysctl_failed`, `txqueuelen_failed`, `qdisc_failed`, `dispatcher_failed`, `modprobe_failed`, `sysfs_failed`, `pcie_failed`, `nm_conf_failed`; existing `dns_partial`, `relock_failed`, `nmcli_failed`, `unknown_owner` unchanged; aggregate `success` rule per D2).
- [ ] **Step 2: Implement status stale/error states + poll-reject recovery + warnings rendering** per D7.
- [ ] **Step 3: Verify** `npm exec --yes --package=pnpm@9 -- pnpm exec tsc --noEmit --skipLibCheck` Expected: exit 0. Then `pnpm run build` (frozen lockfile install if needed, pnpm v9 only) Expected: exit 0. Confirm `dist/` diff only from this change.
- [ ] **Step 4: Run full backend suite** `python -m unittest discover -s tests` Expected: green (frontend change must not break backend).
- [ ] **Step 5: Commit** `git add src dist; git commit -m "fix: lossless UI result handling (ST0-014/017/019)"`

### Task 5: Docs state update (no product behavior change)

**Files:**
- Modify: `docs/audits/2026-10-15-stage-0-findings.md` (ST0-007/008/014/017/019 + 013-reject correction evidence)
- Test: none (docs only)

- [ ] **Step 1: Update findings** correction evidence for the five findings (+013 reject note); remaining findings stay open; Stage 0 stays open.
- [ ] **Step 2: Verify** `git diff --stat` shows only docs files plus committed Tasks 1-4.
- [ ] **Step 3: Commit** `git add docs/...; git commit -m "docs: ST0-007/008/014/017/019 correction evidence"`
