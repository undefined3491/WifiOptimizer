# ST0-007/008 + 014/017/019 — Truthful mutation and reconnect results — design

Date: 2026-10-16. Baseline: `42c7bb9` (= `24811a7` + ST0-004/016), version `0.11.6`.
Scope: findings `ST0-007` (`docs/audits/2026-10-15-stage-0-findings.md:60-64`),
`ST0-008` (`:66-70`), `ST0-014` (`:102-106`), `ST0-017` (`:118-122`),
`ST0-019` (`:128-130`), plus the minimal poll-reject recovery of `ST0-013`
(`:96-100`, reject path only — race/bounded-retry machinery excluded). Stage 0
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

- **D1 — structured reconnect.** `_hard_reconnect(uuid) -> dict` with per-stage
  `{ok, stderr}` for `radio_off`, `radio_on`, `activation` (`None` when no uuid),
  plus `verified: bool` (`radio_on` ok + activation ok when requested + live
  active UUID equals the requested uuid after a short poll of 1–3 tries) and
  `active_uuid_after`. Never throws (`_run_cmd` never throws). A
  `radio-on` failure after a successful `radio-off` is reported distinctly
  (`radio_off_without_on`) since the radio may be dead.
- **D2 — honest `reconnected`.** `reconnected: True` only when `verified` is true.
  Otherwise `reconnected: False` plus an additive `reconnect` detail: skipped
  (`{"skipped": "offline" | "foreign_owner"}` — never attempted) vs attempted
  (stage results). Profile intent already written stays written: `success`
  reflects the mutation, `reconnected` reflects the verification. Aggregates
  (`optimize_safe`, `reapply_all`) compute top-level `reconnected` from children
  (any verified) and set `did_reconnect` only when a child actually attempted;
  no hardcoded `True`.
- **D3 — failed writes block intent.** Generalized rule, new error codes:
  sysctl loop → `sysctl_failed`; txqueuelen (all sites) → `txqueuelen_failed`
  without saving the queue owner's intent and without clearing its slot;
  CAKE `del` → `qdisc_failed`, except idempotent del (`No such qdisc/file` in
  stderr counts as success); dispatcher install/remove → `dispatcher_failed`
  instead of `isfile`-success; modprobe/sysfs/PCIe → `modprobe_failed` /
  `sysfs_failed` / `pcie_failed` with `success: False` (today's silent
  `success: True` ends); NM-conf write → `nm_conf_failed`. Each returns `detail`
  and preserves owner + prior intent for retry.
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
  backend-poll reject clears `in_progress` and sets `errors.wifi_backend`
  (ST0-013 reject path only); `refreshStatus` checks `s.success`, keeps last
  known status with `statusError` + `stale` flag + timestamp, renders
  error-with-retry when no status yet and a stale banner otherwise — never
  `setStatus(errorObj)`; `transfer_warnings`, per-setter `errors[]` and
  `unknown_owners` are appended/rendered (banner for unknown owners).
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
