# ST0-007/008 + 014/017/019 — Truthful mutation and reconnect results — design

Date: 2026-10-16. Baseline: `42c7bb9` (= `24811a7` + ST0-004/016), version `0.11.6`.
Scope: findings `ST0-007`, `ST0-008`, `ST0-014`, `ST0-017`, `ST0-019`,
plus the minimal poll-reject recovery of `ST0-013` (reject path only — race and
bounded-retry machinery excluded, coordinated with the delivery package). Stage 0
stays open; no Stable, no version bump, no Watchdog. Backend effective-state
(ST0-009) and the delivery transaction (001/002/003/018) are separate packages.

## Intent

- Every reconnect reports what actually happened: per-stage results plus
  verification against the live state. `reconnected: True` means verified.
- Every failed write blocks its intent: no saved flag, no cleared owner, a
  named error with detail, and a possible retry.
- The UI never drops a result: rejections, resolved failures, aggregate
  children, `errors[]`, warnings and status failures all render. Stale data is
  labeled stale, never presented as fresh; backend errors are never presented
  as "disconnected".

## Non-goals / anti-goals

- No ST0-009 (configured vs effective backend), no 001/002/003/018 transaction,
  no ST0-013 race/bounded-retry design beyond the minimal reject recovery.
- No new IPC methods; no signature changes. Only additive result keys.
- No healing or auto-retry of failed stages; report, don't mask.

## Decisions (binding)

- **D1 — structured reconnect.** `_hard_reconnect(uuid) -> dict` with exact shape:
  `{"stages": {"radio_off": {"ok": bool, "stderr": str}, "radio_on": {...},
  "activation": {...} | None when no uuid}, "verified": bool,
  "active_uuid_after": str | None, "radio_off_without_on": bool}`.
  `verified` = `radio_on` ok + activation ok when requested + live active UUID
  equals the requested uuid after verification polling: up to 2 checks, 2s
  command timeout each (status quantum), one `time.sleep(1)` between tries
  (sync def, same mechanism as the existing band-relock pause), total budget
  ≈5s; timeout yields `verified: False`, never an error. Never throws
  (`_run_cmd` never throws). A `radio-on` failure after a successful `radio-off`
  sets `radio_off_without_on: True` since the radio may be dead. No radio
  recovery attempts: report, don't mask (findings ask for recovery; this package
  establishes truthful reporting first, recovery belongs to a follow-up).
- **D2 — honest `reconnected` and aggregate `success`.** `reconnected: True`
  only when `verified` is true. Otherwise `reconnected: False` plus an additive
  `reconnect` detail with exact shape: skipped → `{"attempted": False,
  "skipped": "offline" | "foreign_owner"}` (never attempted); attempted →
  `{"attempted": True, "stages": {...}, "verified": bool,
  "active_uuid_after": ..., "radio_off_without_on": bool}` (stages and flag per D1). Profile intent already written
  stays written: `success` reflects the mutation, `reconnected` reflects the
  verification. Aggregates (`optimize_safe`, `reapply_all`): top-level `success`
  is `False` when any child `success` is `False` (counts `applied/total` kept);
  top-level `reconnected` is computed from children (any verified) and
  `did_reconnect` is set only when a child actually attempted; no hardcoded `True`.
- **D3 — failed writes block intent.** Generalized rule, new error codes:
  sysctl loop → `sysctl_failed`; txqueuelen (all sites) → `txqueuelen_failed`
  without saving that setting's intent flag and without clearing its snapshot
  slot (settings without owner UUIDs still have intent flags — the rule covers
  flags, owners where present, and slots);
  CAKE `del` → `qdisc_failed`, except idempotent del (`No such qdisc/file` in
  stderr counts as success); dispatcher install/remove → `dispatcher_failed`
  instead of `isfile`-success; modprobe/sysfs/PCIe → `modprobe_failed` /
  `sysfs_failed` / `pcie_failed` with `success: False` (today's silent
  `success: True` ends); NM-conf write → `nm_conf_failed`. Each returns `detail`
  and preserves owner + prior intent for retry. Partial sysctl application
  (first keys written, later key fails) needs no rollback: writes are
  idempotent, retry re-applies all keys and converges; the failure names the
  failing key in `detail`.
- **D4 — paired-write atomicity (DNS).** On second-key failure, roll back the
  first key to its snapshot prior (else clear) before returning the existing
  `dns_partial` (enable) / `nmcli_failed` (disable); intent never saved on
  divergence. Disable-loop retry stays convergent (slot-once snapshot: retry
  only re-attempts the outstanding key).
- **D5 — band pre-clear and relock reporting.** The BSSID pre-clear before a
  band change is checked and reported (into `relock`/`errors`, never discarded).
  Band-enable responses carry separate `reconnect: {...}` and
  `relock: {"attempted": bool, "ok": bool, ...}` so "reconnect ok, relock fail"
  is distinguishable from "reconnect fail".
- **D6 — buffer status checks all 8 sysctl keys.** `get_status` compares every
  `SYSCTL_PARAMS` key, not just `rmem_max`; any mismatch sets drift. (txqueuelen
  stays out: iface-dependent with CAKE interplay.)
- **D7 — frontend consumes everything (no IPC change).** `handleToggle` gains
  `catch` setting `errors[key]` (covers all toggles, dropdown, text blur since
  they funnel through it); `handleOptimize` catch sets a visible error; Force
  Reapply gets its own handler reading `results[child]` into existing
  `errors[child]` keys plus an applied/total/failed banner (`total==0` renders
  as info, the `reapply` error key is retired); reset reads `result.errors[]`
  into a warning banner and catches rejections; channel/update/diagnostic
  handlers check resolved `success` and catch rejections into visible errors;
  `PanelFooter` checks both diagnostic `success` flags before `done`/`saved`;
  backend-poll reject clears `in_progress` but sets an additive
  `backendSwitch.error` that keeps mutation controls disabled until the next
  successful `getBackendSwitchStatus` reconciles (exclusion preserved per
  ST0-003; no retry timers — retry machinery belongs to the delivery package);
  `refreshStatus` checks `s.success`, keeps last known status with `statusError`
  + `stale` flag + timestamp, renders error-with-retry when no status yet and a
  stale banner otherwise — never `setStatus(errorObj)`; `transfer_warnings`,
  per-setter `errors[]` and `unknown_owners` are appended/rendered (banner for
  unknown owners). `handleChannelChange` gains result check + `catch` (no
  busy-guard change — channel switches are serialization-exempt like today).
- **D8 — result-shape compatibility.** Existing keys keep shapes; only additive
  keys appear (`reconnect` object, `errors` entries, `relock` object). One
  intentional value change: `reset_settings` returns `success: False` when its
  `errors[]` is non-empty (retry possible, defaults not masked) — the frontend
  is updated in this same package to render it (ST0-014/017 row).

## Acceptance

- Radio-on failure: `success` reflects the saved profile, `reconnected: False`,
  `reconnect` names the dead-radio stage — never bare `True`.
- Each newly-checked write failing: intent unsaved, owner retained, named error
  with detail, retry converges.
- Force Reapply with a failed child: child error rendered, banner counts
  applied/total/failed.
- Rejected status before first load: error + retry rendered; rejected poll later:
  last-known data labeled stale; resolved backend error: error rendered, never
  "Not connected".
- Repo-wide grep: no `reconnected": True` literal outside verified-true
  construction; no `handleToggle`-family handler without `catch`.
