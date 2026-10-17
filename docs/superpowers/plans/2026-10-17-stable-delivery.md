# Stable-only hardened delivery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Beta-free, single-job, staged, truthfully-reported Stable updater + rescue-only installer (ST0-001/002/003/018).

**Architecture:** Settings/channel Beta removal (frontend first, backend second, migration automatic); in-memory update job with cross-exclusion; same-filesystem staging + identity validation + per-file `os.replace` commit; one restart + split-triple reporting; install.sh rescue rules; frontend busy integration. Backend by isolated fixtures; shell paths by `check-syntax` + review.

**Tech Stack:** Python `main.py`, Bash `install.sh`, React TS `src/`, `unittest` isolated fixtures on Windows, Git Bash on PATH.

**Spec:** `docs/superpowers/specs/2026-10-17-stable-delivery-design.md`

## Global Constraints

- Windows: isolated fixtures only; never import the real root plugin; never execute real setters/lifecycle/switchers/installer/updater/dispatcher. AST-extract + fail-closed builtins (established patterns).
- Git Bash on PATH (`bash --version` works). Shell changes verified by `scripts/check_delivery.py check-syntax` + review (no live runs).
- No `connection.autoconnect-priority 100` writes; snapshot/owner/reconnect/backend semantics unchanged (consulted only).
- No new IPC methods except none — `apply_update`/`check_for_update` keep names; only result-shape change is start→`accepted` + additive `errors[]`/triple (documented breaking fix).
- `tsconfig.json` strict + `noUnusedLocals/Parameters`; no new deps; pnpm v9 only for builds.
- No version bump, no Stable/beta branch, no Watchdog, no transaction engine (`renameat2`, `systemd-run`, journal, lock-files, `active.json`), no Store work.

## Review Focus

- A second concurrent update must be refused — expect `in_progress` rejection, never two writers.
- A corrupt archive must not touch live — expect byte-identical live files, named error, stage removed.
- The live dir must never disappear — expect no unlink/rename of it in any step.
- A failed commit must withhold restart — expect partial report, no restart request.
- Beta must be gone from code paths — expect no `beta` branch reads, no channel selector; ex-beta migration rule kept.

---

### Task 0: Docs (D8)

**Files:** decision-doc status + findings handoff + ROADMAP note + AGENTS.md/CONTRIBUTING.md/README.md/branding beta lines + recovery/identity beta points + findings Beta-identity MOOT + inventory footnote. SteamOS-Beta mentions stay untouched: `AGENTS.md:20-21` (OS coverage), `ROADMAP.md:13`, `stage-0.md:32,43,69,71`, `findings:256,259`, `steam-deck-lcd-stable.md:55`. Rollout history (`delivery-workflow-design.md`, `plans/2026-10-15-delivery-workflow.md`) is immutable history — leave, do not beta-scrub.

- [ ] **Step 1: Implement** (exact wordings):
  - decision-doc header status → `Status: **SUPERSEDED 2026-10-17 by owner decision: A1 DEFERRED, custom updater RETAINED + hardened, Beta DROPPED, Store AFTER 2–3 roadmap goals (Stage 0+1+2). A1 analysis below retained as reference.**`
  - decision-doc: append `## Owner decision 2026-10-17` section (A1 deferred rationale; custom retained+hardened scope; Beta dropped + stored-`"beta"`-migrates note; Store after 0+1+2); P1 → drop-Beta + harden-Stable-updater (replaces retire-the-updater); P4 → Store DEFERRED phrasing; sign-off item 3 → `[DECIDED 2026-10-17] Beta channel dropped; Stable-only until Store (see P4)`; add item 7 for the deferral decision.
  - findings handoff item 2 → hardened-Stable-only wording + `Update 2026-10-17: delivery direction decided — A1 deferred, custom Stable-only updater retained + hardened, Beta dropped; item 2 rewritten accordingly.`; open question `**Beta identity**` → append `[DROPPED with the Beta channel — no action]` + moot rationale.
  - ROADMAP `## Versions and delivery` += Stable-only distribution paragraph (GitHub releases + in-app Stable updater + `install.sh` rescue; no Beta; Store deferred until Stage 0 + Stage 1 + Stage 2 closed).
  - `AGENTS.md:10` → `No 'beta' branch or channel is maintained; Stable-only distribution. The in-app updater consumes Stable GitHub releases only.`; `AGENTS.md:36` → `Stable updates use this fork's latest published GitHub release, tagged 'v<version>' with a matching 'package.json' version. No Beta channel exists; never fall back to the upstream repository.`
  - `CONTRIBUTING.md` beta paragraph → `Stable checks the fork's latest GitHub release and downloads the matching 'v<version>' tag. There is no Beta channel or 'beta' branch. The installer can fall back to this fork's 'main' when no release tag is available; the in-app Stable updater has no fallback. Never substitute the upstream repository.`
  - `README.md` update paragraph → `In-app Stable updates require a published GitHub release with a 'v<version>' tag. There is no Beta channel.`
  - `docs/branding.md` archive-roots entry → drop the `wifi-optimizer-tms-beta` root + beta-branch sentence.
  - recovery spec → cut the Beta point (`:41,48`-area); identity spec → cut the `wifi-optimizer-tms-beta` point (`:38`-area). Both stay conditional proposals otherwise.
  - inventory `results/2026-10-16-owner-device-inventory.md:31` → append (no fact change): `This is a pre-decision observation; the Beta channel is dropped and 'update_channel' is to be removed, with existing 'beta' values migrated to Stable.`
- [ ] **Step 2: Verify** `grep -ri "beta" <each file>` shows only the SteamOS-Beta contexts listed above + the historical inventory fact + the MOOT note.
- [ ] **Step 3: Commit** `git add <docs>; git commit -m "docs: Stable-only delivery direction (drop Beta)"`

### Task 1: Fixture + red tests (job/staging/identity/exclusion)

**Files:**
- Create: `tests/test_delivery_update.py`
- Modify: none

**Interfaces:**
- Consumes: AST-extracted `start_update`-equivalent entry, job guard, staging/commit helpers (names from implementation Task 3 — test against the spec'd phase names and error codes); scripted `_run_cmd` (curl/tar/systemctl), in-memory settings/stage-fs log, `os.replace` spy.
- Produces: `DeliveryFixture` used by Tasks 3-4.

- [ ] **Step 1: Write failing tests**: `concurrent_update_rejected`, `update_during_switch_rejected_and_reverse`, `corrupt_archive_leaves_live_identical`, `identity_mismatch_stops_before_commit`, `live_dir_never_removed`, `curl_timeout_no_restart`, `commit_failure_withholds_restart_with_partial`, `beta_channel_gone`.
- [ ] **Step 2: Run to verify they fail with AssertionError (not ImportError/NameError)** Run: `python -m unittest tests.test_delivery_update -v` Expected: FAIL on behavior asserts (baseline suite stays 112 green).
- [ ] **Step 3: Add fixture only** (no production change); re-run: imports clean, behavior asserts still FAIL.
- [ ] **Step 4: Run full suite** `python -m unittest discover -s tests` Expected: new file red, all other files green.
- [ ] **Step 5: Commit** `git add tests/test_delivery_update.py; git commit -m "test: isolated delivery fixtures (red)"`

### Task 2: Beta removal (D1)

**Files:**
- Modify: `main.py` (Stable-only branches; `set_update_channel` + key last), `src/UpdatesSection.tsx` or equivalent, `src/index.tsx` (handler/props), `src/backend.ts` (wrapper), `src/types.ts` (channel fields), `scripts/collect_deck_inventory.py` (enum tolerance)
- Test: typecheck + build + backend suite

**Interfaces:**
- Consumes: Task 1 fixture (beta-gone test).
- Produces: no beta branch reads/downloads; no channel selector; key removed with automatic strip-migration; ex-beta version rule kept; collector tolerates old `"beta"`.

- [ ] **Step 1: Verify red** Expected: FAIL on `beta_channel_gone` (+ typecheck for removed props).
- [ ] **Step 2a: Frontend selector removal first** (keeps every intermediate state green): dropdown/handler/`setUpdateChannel`-wrapper export/props in `UpdatesSection` + `index.tsx` + `backend.ts` (stable `checkForUpdate`/`applyUpdate` wrappers stay — only the channel wrapper goes) + `types.ts` channel fields.
- [ ] **Step 2b: Backend branches → Stable-only** (keep ex-beta version rule + docstrings updated with code).
- [ ] **Step 2c: `set_update_channel` + key removal + collector record-raw-with-note.**
- [ ] **Step 3: Run** `python -m unittest tests.test_delivery_update -v` Expected: beta test PASS. `tsc --noEmit --skipLibCheck` exit 0. `pnpm run build` exit 0.
- [ ] **Step 4: Run full suite** green + `py_compile`.
- [ ] **Step 5: Commit** `git add main.py src types tests scripts; git commit -m "fix: drop Beta channel, Stable-only updates"`

### Task 3: Hardened updater (D2-D5)

**Files:**
- Modify: `main.py` (job, staging, validated transfer/identity, per-file commit, split-triple results, cross-exclusion both directions incl. `start_backend_switch` guard)
- Test: `tests/test_delivery_update.py`

**Interfaces:**
- Consumes: Task 1 fixture.
- Produces: accepted/reject shapes, phase machine, private script path, same-fs staging gate, identity checks, ordered `os.replace` commit, withheld restart on partial, error codes per D5.

- [ ] **Step 1: Verify red** Expected: FAIL on job/staging/identity/exclusion tests.
- [ ] **Step 2a: Implement job + cross-exclusion** per D2 (phase enum + reason vocabulary; guard both directions incl. the ST0-010 reservation site).
- [ ] **Step 2b: Implement staging + validated transfer/identity** per D3/D4.
- [ ] **Step 2c: Implement commit + restart/reporting** per D3/D5 (no live-dir removal anywhere) + typed start/result shapes in `src/types.ts` (`UpdateStartResult {accepted, target, reason, job_id}`, `get_status.update_job` summary, triple/result keys) + rewrite `scripts/check_delivery.py` updater guards + `SyntaxTests` to the new contract.
- [ ] **Step 3: Run** `python -m unittest tests.test_delivery_update -v` Expected: PASS.
- [ ] **Step 4: Run full suite + syntax** `python -m unittest discover -s tests` (must include green `tests/test_backend_reservation.py` + `tests/test_backend_state.py` — the reservation-pattern net D2 reuses, before the full run); `check-syntax`; `py_compile`.
- [ ] **Step 5: Commit** `git add main.py src/types.ts tests/test_delivery_update.py scripts/check_delivery.py tests/test_delivery.py; git commit -m "fix: staged single-job Stable updater with truthful results"`

### Task 4: install.sh rescue (D6)

**Files:**
- Modify: `install.sh`
- Test: `check-syntax` + review (no live runs) + `tests/test_delivery.py` still green

- [ ] **Step 1: Implement** sibling staging + dev gate, validated transfer, identity checks, no `rm -rf` (fresh `mv -n` / upgrade per-file cp), truthful stdout + exit codes, labeled main-fallback.
- [ ] **Step 2: Verify** `check-syntax` exit 0; backend suite green; review checklist (no live-dir removal, no silent fallback, no unvalidated copy).
- [ ] **Step 3: Commit** `git add install.sh; git commit -m "fix: install.sh as validated rescue installer"`

### Task 5: Frontend exclusion wiring (D7) + dist rebuild

**Files:**
- Modify: `src/index.tsx` (`handleApplyUpdate` rewritten for the accepted/start shape per D5, `handleCheckForUpdate`, 60 s timeout copy as "status unknown — verify version after restart", retry-after-timeout path yielding `in_progress` rejection copy; Update Now disabled during switch; backend toggle disabled while updating; busy on accepted; terminal/fail/timeout clear after forced refresh)
- Test: typecheck + build + review checklist (timeout copy + accepted-shape branches covered)

- [ ] **Step 1: Implement** per D7 (no new global gate).
- [ ] **Step 2: Verify** `tsc` exit 0, build exit 0 (record hash, `dist/` diff only from this package).
- [ ] **Step 3: Run full backend suite** green.
- [ ] **Step 4: Commit** `git add src dist; git commit -m "fix: update/switch mutual exclusion in UI"`

### Task 6: Docs state update

**Files:**
- Modify: `docs/audits/2026-10-15-stage-0-findings.md` (ST0-001/002/003/018 evidence; remaining: none — see note)
- Test: none (docs only)

Note: this package closes the last open findings (3 Important + 1 Minor). The findings doc must then record Stage 0 code-complete pending candidate device validation (NOT Stage 0 closure — validation + release still required). Also mark the two designed-out open questions (fixed-`/tmp` script path, shell interpolation in the updater) as gone with this package, while leaving event-loop blocking, dispatcher races, and adapter coverage explicitly open.

- [ ] **Step 1: Update findings** correction evidence for ST0-001/002/003/018; record code-complete pending device validation.
- [ ] **Step 2: Verify** via `git status --short`.
- [ ] **Step 3: Commit** `git commit -m "docs: ST0-001/002/003/018 correction evidence"`
