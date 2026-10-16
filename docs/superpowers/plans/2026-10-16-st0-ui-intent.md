# ST0-011/012/013/015/020 UI intent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Drift repair flow, editable Custom DNS, bounded poll lifecycle, dismount-safe timers (ST0-011/012/013/015/020).

**Architecture:** New `repair_drifted()` backend (fresh-read enabled∩drifted filter, `reapply_all` shape) with isolated fixture tests; frontend draft/applied DNS state machine, `handleRepair`, bounded poll retry with working retry action, timer ids + disposed guards. Backend by fixtures; frontend by typecheck + build + line-by-line review checklist.

**Tech Stack:** Python `main.py`, React TS `src/`, `unittest` isolated fixtures on Windows, Git Bash on PATH, `tsc --noEmit --skipLibCheck`, `pnpm run build` (pnpm v9).

**Spec:** `docs/superpowers/specs/2026-10-16-st0-ui-intent-design.md`

## Global Constraints

- Windows: isolated fixtures only for backend; never import the real root plugin; never execute real setters/lifecycle/switchers. AST-extract + fail-closed builtins.
- Git Bash on PATH (`bash --version` works).
- New IPC method `repair_drifted` exactly matched in `src/backend.ts`; no other signature changes; only additive keys. Backend whitelist/NM enums untouched.
- `tsconfig.json` strict + `noUnusedLocals/Parameters`; no new deps; pnpm v9 only.
- No version bump, no Stable/beta, no Watchdog, no ST0-003 machinery, no 001/002/003/018, no v2 reconnect coalescing.

## Review Focus

- Repair must not enable the disabled — expect untouched flags and no stray radio cycles.
- Draft must survive polling and never auto-submit — expect guarded refresh, submit-free blur, pre-mounted error field.
- Poll failure must stay actionable — expect one retry, working Retry button, bounded `in_progress`, no overlap.
- Dismount must silence timers — expect id + clear + disposed guard on every listed timer/await.

---

### Task 1: Backend `repair_drifted` + `drift.dns` fixture + red tests (D1/D2)

**Files:**
- Create: `tests/test_repair_drift.py`
- Modify: none

**Interfaces:**
- Consumes: AST-extracted `repair_drifted` (to be created — test the spec'd name/signature/shape), `get_status` drift section, setters; stubbed `_run_cmd` + in-memory settings/snapshot (established patterns).
- Produces: `RepairFixture` used by Task 2.

- [ ] **Step 1: Write failing tests**: `repair_only_enabled_and_drifted`, `repair_leaves_disabled_alone`, `repair_no_radio_for_healthy`, `repair_total_zero_message` (exact `"No drifted settings"`), `repair_unknown_owner_fails_child_only`, `repair_backend_drift_excluded`, `repair_skips_auto_fix`, `repair_repairs_dns_drift`, `dns_drift_detected` (IP-set subset rule), `selection_is_read_only` (`save_count==0`, zero `_nmcli_modify`), `repair_drifted_ipc_shape` (static: method exists with 0 args + `"repair_drifted"` in `src/backend.ts`).
- [ ] **Step 2: Run to verify they fail with AssertionError (not ImportError/NameError)** Run: `python -m unittest tests.test_repair_drift -v` Expected: FAIL on behavior asserts (baseline suite stays 101 green).
- [ ] **Step 3: Add fixture only** (no production change); re-run: imports clean, behavior asserts still FAIL.
- [ ] **Step 4: Run full suite** `python -m unittest discover -s tests` Expected: new file red, all other files green.
- [ ] **Step 5: Commit** `git add tests/test_repair_drift.py; git commit -m "test: isolated repair-drift fixtures (red)"`

### Task 2: Implement `repair_drifted` + `drift.dns` (D1/D2)

**Files:**
- Modify: `main.py` (new method + drift key), `src/backend.ts` (exact-name wrapper)
- Test: `tests/test_repair_drift.py`

**Interfaces:**
- Consumes: Task 1 fixture.
- Produces: `repair_drifted()` with `reapply_all` result shape; shared drift-formula helper with `get_status` (no duplicated formulas); `drift.dns` boolean key.

- [ ] **Step 1: Verify red** Expected: FAIL on repair tests.
- [ ] **Step 2a: Implement drift-formula helper** shared by `get_status` and `repair_drifted`.
- [ ] **Step 2b: Implement `repair_drifted`** per D1 (fresh read-only selection via the shared helper, enabled∩drifted, order/aggregation like `reapply_all`, `total==0` message, child `unknown_owner` contained).
- [ ] **Step 2c: Implement `drift.dns`** per D2 + backend.ts wrapper with the exact name.
- [ ] **Step 3: Run** `python -m unittest tests.test_repair_drift -v` Expected: PASS.
- [ ] **Step 4: Run full suite + syntax** `python -m unittest discover -s tests`; preflight `bash --version`; `python -m py_compile main.py`.
- [ ] **Step 5: Commit** `git add main.py src/backend.ts tests/test_repair_drift.py; git commit -m "fix: repair-drifted flow with DNS drift detection (ST0-011)"`

### Task 3: Banner + DNS draft UI (D1-banner/D3)

**Files:**
- Modify: `src/index.tsx` (banner `onClick` → `handleRepair`, new handler, DNS draft state machine + Apply/Cancel row)
- Test: typecheck + build + review checklist (no frontend unit infra)

**Render checklist (verify by reading code):** banner calls `handleRepair` (one busy window, child→errors mapping, single reconnect wait, forced refresh before clear); outcome banner is message-aware (`"No drifted settings"` vs reapply text) with top-level catch → `actionError`; DNS row uses `getBadge("dns", ...)`; dropdown sets draft only; field mounts on draft-or-applied custom prefilled from applied servers; typing never submits; blur never submits; custom-only Apply validation then single toggle; Cancel IPC-free; refresh guarded by `!dirty && !focused && providerDraft===null`; main toggle uses applied values and drops drafts; empty-custom error renders with field mounted; draft controls honor `mutationLocked`.

- [ ] **Step 1: Implement banner + `handleRepair`** per D1.
- [ ] **Step 2: Implement DNS draft machine** per D3.
- [ ] **Step 3: Verify** `tsc --noEmit --skipLibCheck` exit 0, `pnpm run build` exit 0 (pnpm v9, frozen lockfile; record pre-build hash, confirm `dist/` diff only from this change).
- [ ] **Step 4: Run full backend suite** `python -m unittest discover -s tests` Expected: green.
- [ ] **Step 5: Commit** `git add src dist; git commit -m "fix: repair banner and editable Custom DNS (ST0-011/012/015)"`

### Task 4: Poll lifecycle + dismount safety (D4/D5)

**Files:**
- Modify: `src/index.tsx` (poll retry/reconcile/bounds/guard), `src/components/BackendToggleRow.tsx` (`canRetry` prop + enabled logic + `unknown` representation), `src/components/PanelFooter.tsx` (timeout ids + cleanup)
- Test: typecheck + build + review checklist (no timer unit harness)

**Review checklist (verify by reading code):** one bounded retry then error+lock; `canRetry = error!=null && !in_progress && !isBusy` on the Retry button independent of `mutationLocked`; retry click and next successful status reconcile the error; `in_progress` tick-bound → `unknown`; no overlapping poll ticks; reapplyTimer id + `clearTimeout` + disposed early-return; `disposedRef` checked after every listed await (poll, reconnect waits, update check, refresh status); `backendPollRef` nulled on cleanup; footer timeouts cleared on unmount; launch→dismount→fire path does zero IPC/state writes.

- [ ] **Step 1: Implement poll retry + reconciliation + bounds + guard** per D4.
- [ ] **Step 2: Implement dismount safety** per D5.
- [ ] **Step 3: Verify** `tsc` exit 0, `pnpm run build` exit 0 (record hash, `dist/` diff only from this change).
- [ ] **Step 4: Run full backend suite** green.
- [ ] **Step 5: Commit** `git add src dist; git commit -m "fix: bounded poll lifecycle and dismount safety (ST0-013/020)"`

### Task 5: Docs state update (no product behavior change)

**Files:**
- Modify: `docs/audits/2026-10-15-stage-0-findings.md` (ST0-011/012/013/015/020 evidence)
- Test: none (docs only)

- [ ] **Step 1: Update findings** correction evidence for the five findings; remaining findings stay open; Stage 0 stays open.
- [ ] **Step 2: Verify** via `git status --short` clean apart from intended files.
- [ ] **Step 3: Commit** `git add docs/...; git commit -m "docs: ST0-011/012/013/015/020 correction evidence"`
