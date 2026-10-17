# Device-discovered defects fix (follow-up of candidate validation) — design

Date: 2026-10-17. Baseline: `a276955` (main). Source rows:
`docs/testing/results/2026-10-17-candidate-validation-matrix.md`
(S-BE-04 FAIL, S-BE-05 FAIL, S-OPT-02 PARTIAL).
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

- **D1 — bounded effective-read retry in workers.** New helper
  `_poll_effective_backend(target, tries=3, delay=2.0) -> (value, services,
  attempts)`: re-reads via `_read_effective_backend` until the value is
  non-`None` or the budget (≈10 s) is exhausted; uses blocking `time.sleep`
  (workers already block; no new async machinery). Used by BOTH the final
  verification and the rollback verification in BOTH backend workers
  (steamos + generic). Mismatch is declared only after the budget is exhausted;
  the attempts count and interim unknowns land in `errors[]` as
  `"transient-unknown:N"` notes (never as failure codes). `reconnect_timed_out`
  stays connectivity-only. Timeout/failure shapes unchanged otherwise.
- **D2 — convergence reconciliation in `refreshStatus`.** On every successful
  `getStatus` where the backend is converged (`live.backend_desired ===
  live.backend_effective`, effective known non-`"unknown"`) AND no switch is in
  progress: delete `errors.wifi_backend` AND clear `backendSwitch.error`
  (set to the fresh status object form, preserving exclusion semantics — a
  converged backend needs no lock). Genuine divergences (`drift.backend` set,
  unknown effective, in-progress switch) keep both. This is remount-independent;
  QAM caching no longer matters.
- **D3 — per-file ASPM verify.** `_apply_pcie_aspm_fix` (and only it — driver
  sysfs keeps current behavior until observed otherwise): after attempting each
  file write, re-read the file; a file already at the desired value counts as
  OK whether or not the write succeeded (unsupported-but-unchanged =
  skip-with-note in `errors[]` as `"aspm-skip:<path>"`, not a failure code);
  only files whose content differs from desired after the attempt fail the
  operation (`pcie_failed` with the file list, intent blocked per established
  rule). Missing paths keep the current silent-skip. No change to the
  discovered-device iteration or the desired values themselves.

## Acceptance

- Verification during an NM/service restart: retried within budget, success
  when services settle; persistent mismatch still fails with `effective_mismatch`.
- A converged backend clears both error surfaces within one status poll, no
  remount, no retry click; a diverged backend keeps them.
- `l0s_aspm`-style unwritable-but-correct files: toggle succeeds with a
  skip-note; genuinely unwritable-and-wrong files still fail named.
- Repo-wide grep: no unbounded effective-read loop; no new IPC methods.
