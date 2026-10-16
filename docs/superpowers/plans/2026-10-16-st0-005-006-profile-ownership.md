# ST0-005/006 profile ownership Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `get_status()` read-only and give BSSID/band/DNS/IPv6 explicit per-profile owners (ST0-005/006).

**Architecture:** Remove all settings/NM writes from `get_status()`; add `band_owner_uuid` / `dns_owner_uuid` / `ipv6_owner_uuid` beside existing `bssid_lock_connection_uuid`; resolve disablers by owner UUID only; deprecate `last_connection_uuid` / `priority_set`; cover with isolated AST-extracted fixture tests (pattern: `tests/test_backend_reservation.py`).

**Tech Stack:** Python `main.py` backend, `unittest` isolated fixtures on Windows (no `main.py` import, no live setters), Git Bash on PATH for syntax checks.

**Spec:** `docs/superpowers/specs/2026-10-16-st0-005-006-profile-ownership-design.md`

## Global Constraints

- Windows: isolated fixtures only; never import the real root plugin; never execute real setters/lifecycle/installer/dispatcher.
- Git Bash must be on PATH for syntax checks (`bash --version` works).
- No `connection.autoconnect-priority 100` write on any path; `priority_set` read-compat only.
- IPC signatures unchanged (no new parameters); frontend untouched.
- `tsconfig.json` strict + `noUnusedLocals/Parameters` respected if TS touched (not expected).
- No version bump, no Stable/beta publication, no Watchdog, no recovery engine.

## Review Focus

- Polling a foreign active profile with intent from another must not mutate it — expect report-only drift.
- Active-B + owner-A disable must not clear or reconnect B — expect owner-UUID targeting.
- Offline disable must use the owner, not any "last seen" UUID — expect A modified with `reconnected: False`.
- Legacy enabled-without-owner must fail explicitly — expect `unknown_owner`, zero mutations, intent preserved.
- Failed `nmcli` must not persist intent or clear ownership — expect retry-able `nmcli_failed`.

---

### Task 1: Isolated fixture + red tests for status purity and ownership

**Files:**
- Create: `tests/test_profile_ownership.py`
- Modify: none

**Interfaces:**
- Consumes: AST-extracted `get_status`, `set_bssid_lock`, `set_band_preference`, `set_dns`, `set_ipv6`, `_resolve_uuid`, `_require_wifi` from `main.py`, stubbed `_run_cmd` / `_nmcli_modify` / `_get_wifi_interface` / `_get_active_connection_uuid` / settings IO (pattern: `tests/test_backend_reservation.py:31-49`, fail-closed builtins).
- Produces: `ProfileFixture` with scripted NM/settings responses and `nmcli_calls: list[(uuid,key,value)]` log used by Tasks 2-4.

- [ ] **Step 1: Write failing tests** in `tests/test_profile_ownership.py`: `polling_B_never_writes_or_modifies`, `active_B_owner_A_disable_targets_A`, `offline_disable_uses_owner_not_last`, `legacy_enabled_without_owner_is_unknown_owner`, `failed_nmcli_preserves_owner_and_intent`, `status_has_no_save_or_modify` (static grep on `get_status` source for `_save_settings` / `_nmcli_modify`), `priority_never_written`.
- [ ] **Step 2: Run to verify they fail** Run: `python -m unittest tests.test_profile_ownership -v` Expected: FAIL (methods/behavior missing).
- [ ] **Step 3: Add fixture only** (no production change): AST-extract + stubs + call log, tests still failing on behavior asserts but fixture imports cleanly.
- [ ] **Step 4: Run full suite** Run: `python -m unittest discover -s tests` Expected: new tests fail, existing 43 pass (3 Windows skips).
- [ ] **Step 5: Commit** `git add tests/test_profile_ownership.py; git commit -m "test: isolated ST0-005/006 ownership fixtures (red)"`

### Task 2: Read-only get_status + priority removal

**Files:**
- Modify: `main.py:816-863` (drop S1/S2), `main.py:980-982` (drop S3), `main.py:1001-1004` (drop S4)
- Test: `tests/test_profile_ownership.py`

**Interfaces:**
- Consumes: Task 1 fixture.
- Produces: `get_status()` with zero `_save_settings` / `_nmcli_modify`; drift is report-only including `"owner_unknown"`.

- [ ] **Step 1: Verify red** Run: `python -m unittest tests.test_profile_ownership -v` Expected: FAIL on `polling_B_never_writes_or_modifies`, `status_has_no_save_or_modify`, `priority_never_written`.
- [ ] **Step 2: Implement** delete S1/S2/S3/S4 per D1/D2; disconnected early-return unchanged; drift entries stay as reports.
- [ ] **Step 3: Run** `python -m unittest tests.test_profile_ownership -v` Expected: status/priority tests PASS.
- [ ] **Step 4: Run full suite** `python -m unittest discover -s tests` Expected: no regressions (43 baseline + new).
- [ ] **Step 5: Commit** `git add main.py tests/test_profile_ownership.py; git commit -m "fix: read-only get_status, drop automatic priority 100 (ST0-006)"`

### Task 3: Owner-UUID schema + explicit target recording + resolution

**Files:**
- Modify: `main.py:143-169` (add `band_owner_uuid`, `dns_owner_uuid`, `ipv6_owner_uuid`), `main.py:372-375` (remove `_get_saved_connection_uuid` fallback), `main.py:739-764` (owner-based `_resolve_uuid`), setters `main.py:1101-1327` (record/clear owners per D3-D5)
- Test: `tests/test_profile_ownership.py`

**Interfaces:**
- Consumes: Task 2 status.
- Produces: enablers require active + set owner; disablers use owner offline; transfer overwrites owner with best-effort old-profile clear; unknown-owner contract per D6; failures per D7.

- [ ] **Step 1: Verify red** Run: `python -m unittest tests.test_profile_ownership -v` Expected: FAIL on ownership/transfer/legacy/retry tests.
- [ ] **Step 2: Implement** schema + recording + resolution + BSSID-disable owner preference + band-relock gating (`band_target == bssid_owner`, MAC verify, partial on failure) + offline `reconnected: False`.
- [ ] **Step 3: Run** `python -m unittest tests.test_profile_ownership -v` Expected: PASS.
- [ ] **Step 4: Run full suite + syntax** `python -m unittest discover -s tests` and `bash -n` on touched shell-adjacent paths if any; `python -m py_compile main.py`.
- [ ] **Step 5: Commit** `git add main.py tests/test_profile_ownership.py; git commit -m "fix: per-profile owners, owner-based disablers, legacy unknown-owner (ST0-005/006)"`

### Task 4: Docs state update (no product behavior change)

**Files:**
- Modify: `docs/audits/2026-10-15-stage-0-findings.md` (ST0-005/006 correction evidence), `docs/audits/2026-10-15-stage-0.md` (continuation pointer if needed)
- Test: none (docs only)

**Interfaces:**
- Consumes: Tasks 1-3 commits + review verdicts.
- Produces: correction evidence with exact commits, test counts, reviewer model, remaining device-validation gap.

- [ ] **Step 1: Update findings** correction evidence for ST0-005/006 only; keep other 11 Important + 9 Minor open; Stage 0 stays open.
- [ ] **Step 2: Verify** `git diff --stat` shows only the two docs files plus Task 1-3 files already committed.
- [ ] **Step 3: Commit** `git add docs/...; git commit -m "docs: ST0-005/006 correction evidence"`
