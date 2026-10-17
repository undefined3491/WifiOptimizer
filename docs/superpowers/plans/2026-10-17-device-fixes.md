# Device-discovered defects fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden effective-state verification, self-clearing backend errors, and per-file ASPM verify (device rows S-BE-04, S-BE-05, S-OPT-02).

**Architecture:** Bounded retry helper for worker/rollback verification; convergence reconciliation in the status-refresh success path; verify-after-write per sysfs file. Backend by isolated fixtures; frontend by typecheck + build + line-by-line review checklist.

**Tech Stack:** Python `main.py`, React TS `src/`, `unittest` isolated fixtures on Windows, Git Bash on PATH, `tsc --noEmit --skipLibCheck`, `pnpm run build` (pnpm v9).

**Spec:** `docs/superpowers/specs/2026-10-17-device-fixes-design.md`

## Global Constraints

- Windows: isolated fixtures only; never import the real root plugin; never execute real setters/lifecycle/switchers. AST-extract + fail-closed builtins (established patterns).
- Git Bash on PATH (`bash --version` works).
- No `connection.autoconnect-priority 100` writes; snapshot/owner/reconnect/desired-effective semantics unchanged except D1-D3.
- No new IPC methods; no signature changes; only additive keys (`attempts` notes, `aspm-skip` entries).
- `tsconfig.json` strict + `noUnusedLocals/Parameters`; no new deps; pnpm v9 only.
- No version bump, no Stable/beta, no Watchdog, no ST0-003 machinery, no DNS work, no service-state restoration.

## Review Focus

- A restart-window sample must be retried, not verdict — expect budget exhaustion before mismatch.
- A converged backend must clear both error surfaces — expect deletion without remount/retry, diverged keeps them.
- An unwritable-but-correct file must not fail the toggle — expect skip-note, named failure only for wrong content.

---

### Task 1: Fixture + red tests (retry/reconcile/verify)

**Files:**
- Create: `tests/test_device_fixes.py`
- Modify: none

**Interfaces:**
- Consumes: AST-extracted `_poll_effective_backend` (to be created — spec'd name/signature), worker verify sections, `refreshStatus` converge branch (review checklist, no unit harness), `_apply_pcie_aspm_fix`; scripted `is-active` sequences (transient unknowns then converge / persistent mismatch), in-memory fs for sysfs files with per-file writability flags.
- Produces: `DeviceFixFixture` used by Tasks 2-4.

- [ ] **Step 1: Write failing tests**: `transient_unknown_retried_to_success`, `persistent_mismatch_still_fails`, `budget_exhaustion_notes_attempts`, `rollback_verify_retried`, `converged_clears_both_errors`, `diverged_keeps_errors`, `in_progress_keeps_errors`, `unwritable_but_correct_skipped_with_note`, `unwritable_and_wrong_fails_named`, `missing_path_still_skipped`.
- [ ] **Step 2: Run to verify they fail with AssertionError (not ImportError/NameError)** Run: `python -m unittest tests.test_device_fixes -v` Expected: FAIL on behavior asserts (baseline suite stays 132 green).
- [ ] **Step 3: Add fixture only** (no production change); re-run: imports clean, behavior asserts still FAIL.
- [ ] **Step 4: Run full suite** `python -m unittest discover -s tests` Expected: new file red, all other files green.
- [ ] **Step 5: Commit** `git add tests/test_device_fixes.py; git commit -m "test: isolated device-fixes fixtures (red)"`

### Task 2: Bounded effective-read retry (D1)

**Files:**
- Modify: `main.py` (new helper + both workers' final + rollback verifications)
- Test: `tests/test_device_fixes.py`

**Interfaces:**
- Consumes: Task 1 fixture.
- Produces: `_poll_effective_backend(target, tries=3, delay=2.0)`; worker/rollback verification via the helper; `transient-unknown:N` notes; unchanged failure shapes otherwise.

- [ ] **Step 1: Verify red** Expected: FAIL on retry tests.
- [ ] **Step 2: Implement** helper + 4 call sites (2 workers × final/rollback).
- [ ] **Step 3: Run** `python -m unittest tests.test_device_fixes -v` Expected: retry tests PASS.
- [ ] **Step 4: Run full suite** `python -m unittest discover -s tests` Expected: no regressions (132 + new).
- [ ] **Step 5: Commit** `git add main.py tests/test_device_fixes.py; git commit -m "fix: bounded effective-read retry in backend verification"`

### Task 3: Convergence reconciliation (D2)

**Files:**
- Modify: `src/index.tsx` (refreshStatus success path)
- Test: typecheck + build + review checklist (no frontend unit infra)

**Review checklist (verify by reading code):** converged (desired===effective, known, no in-progress) deletes `errors.wifi_backend` AND clears `backendSwitch.error` to the fresh form; diverged/unknown/in-progress keeps both; no other error keys touched; no new timers or polls.

- [ ] **Step 1: Implement** per D2.
- [ ] **Step 2: Verify** `tsc --noEmit --skipLibCheck` exit 0, `pnpm run build` exit 0 (pnpm v9, frozen lockfile; record pre-build hash, `dist/` diff only from this package).
- [ ] **Step 3: Run full backend suite** `python -m unittest discover -s tests` Expected: green.
- [ ] **Step 4: Commit** `git add src dist; git commit -m "fix: converge-reconciled backend errors"`

### Task 4: Per-file ASPM verify (D3)

**Files:**
- Modify: `main.py` (`_apply_pcie_aspm_fix` only)
- Test: `tests/test_device_fixes.py`

**Interfaces:**
- Consumes: Task 1 fixture.
- Produces: write→re-read per file; correct-content counts OK; skip-notes; named failure listing wrong-content files; missing-path skip kept.

- [ ] **Step 1: Verify red** Expected: FAIL on ASPM tests.
- [ ] **Step 2: Implement** per D3 (PCIe only; driver sysfs untouched).
- [ ] **Step 3: Run** `python -m unittest tests.test_device_fixes -v` Expected: PASS.
- [ ] **Step 4: Run full suite + syntax** `python -m unittest discover -s tests`; preflight `bash --version`; `python -m py_compile main.py`.
- [ ] **Step 5: Commit** `git add main.py tests/test_device_fixes.py; git commit -m "fix: per-file ASPM verify with skip-notes"`

### Task 5: Docs state update

**Files:**
- Modify: `docs/audits/2026-10-15-stage-0-findings.md` (device-discovered defects section: S-BE-04/S-BE-05/S-OPT-02 corrected, re-validation pending on device)
- Test: none (docs only)

- [ ] **Step 1: Update findings** with a short device-findings addendum (NOT audit ST0 findings — separate section; Stage 0 stays open).
- [ ] **Step 2: Verify** via `git status --short`.
- [ ] **Step 3: Commit** `git commit -m "docs: device-discovered defects correction evidence"`
