# Device-discovered defects fix (follow-up of candidate validation) — design

Date: 2026-10-17. Baseline: `a276955` (main). Source rows (pushed session branch
`origin/codex/st0-validation-run`, commits `505945f` deploy/health,
`beceef9` S-BE-04 FAIL + S-OPT-02 PARTIAL, `090b0b7` S-BE-05 FAIL + S-OPT-03 PASS):
- S-BE-04 FAIL — repair retry on converged backend; worker log `final=None` +
  `rollback incomplete` while post-hoc state converged (desired `wpa_supplicant`
  from valve conf, `is-active` wpa `active`/iwd `inactive`, internet works);
  probable cause: single 3 s-timeout sample raced the service/NM restart.
- S-BE-05 FAIL — `errors.wifi_backend` set once at terminal failure
  (`src/index.tsx:292-297`), never reconciled (`stopBackendPoll` ends polling;
  mount effect reconciles only `backendSwitch`); QAM caching may skip remount.
- S-OPT-02 PARTIAL — `l0s_aspm` EACCES as root while sibling files wrote fine;
  toggle honestly `failed`; firmware restriction, not a privilege bug.
Stage 0 stays open; no Stable, no version bump, no Watchdog. No DNS work
(separate package).

## Intent

- Effective-state verification survives restart windows: transient `unknown`
  is retried, persistent mismatch is reported — never confused.
- A converged backend clears its failure banner by itself, remount or not.
- Unsupported-but-unchanged sysfs files are skipped with a note, not failures.

## Non-goals / anti-goals

- No change to the single-sample status/diagnostics effective read (cheap poll
  stays; transient `unknown` there still reports drift honestly).
- No auto-repair, no retry timers beyond the bounded verification retry, no
  ST0-003 machinery, no service-state restoration.
- No new IPC methods; only additive keys.

## Decisions (binding)

- **D1 — bounded effective-read retry in workers.** New SYNC helper
  `_poll_effective_backend(tries=3, delay=2.0) -> (value, services, attempts)`:
  re-reads via `_read_effective_backend` until the value is non-`None` or the
  budget (≈6–8 s incl. read time) is exhausted; blocking `time.sleep` inside is
  safe because every call site invokes it via the existing `asyncio.to_thread`
  pattern (exactly like today's direct `_read_effective_backend` calls — no new
  event-loop blocking beyond the ~6 s budget, additive to the existing 15 s
  reconnect poll and 45 s restart window, all documented worst-cases, not steady
  cost). Used by BOTH the final verification and the rollback verification in
  BOTH backend workers (steamos + generic). Mismatch is declared only after the
  budget is exhausted; the attempts count and interim unknowns land in `errors[]`
  as `"transient-unknown:N"` notes (never as failure codes). `reconnect_timed_out`
  stays connectivity-only. Timeout/failure shapes unchanged otherwise.
- **D2 — convergence reconciliation in `refreshStatus`.** On every successful
  `getStatus` where the backend is converged (`live.backend_desired ===
  live.backend_effective`, effective known non-`"unknown"`) AND no switch is in
  progress AND no outstanding `needs_reboot` result exists: delete
  `errors.wifi_backend` AND set `backendSwitch` to `null` (the initial
  no-switch state, which carries no lock — a converged backend needs none).
  Genuine divergences (`drift.backend` set, unknown effective, in-progress
  switch, outstanding reboot need) keep both. This is remount-independent;
  QAM caching no longer matters.
- **D3 — per-file ASPM verify.** `_apply_pcie_aspm_fix` (and only it — driver
  sysfs keeps current behavior until observed otherwise) returns
  `(None, notes)` on full success or `(code, detail, notes)` on failure, where
  `notes` carries `"aspm-skip:<path>"` entries into the caller's existing
  additive `errors[]`. Rule per file (link files AND `power/control`): attempt
  the write (missing paths keep the current silent-skip); re-read and
  `.strip()`-compare against desired; a file already at the desired value counts
  as OK whether or not the write succeeded (unsupported-but-unchanged =
  skip-with-note, not a failure code); collect ALL files whose content differs
  after the attempt (no return-on-first-`OSError`) and fail with `pcie_failed`
  listing them, intent blocked per established rule. Read failures on a file
  count that file as failed (never assume). Fixture models EPERM-vs-ENOENT
  flags; true TOCTOU races are a documented fixture limitation (device sysfs
  is atomic per write).

## Acceptance

- Verification during an NM/service restart: retried within budget, success
  when services settle; persistent mismatch still fails with `effective_mismatch`.
- A converged backend clears both error surfaces within one status poll, no
  remount, no retry click; a diverged backend keeps them.
- `l0s_aspm`-style unwritable-but-correct files: toggle succeeds with a
  skip-note; genuinely unwritable-and-wrong files still fail named.
- Repo-wide grep: no unbounded effective-read loop; no new IPC methods.
