# ST0-009 — Backend desired vs effective state — design

Date: 2026-10-16. Baseline: `d091a2c` (= `42c7bb9` + truthful-results), version `0.11.6`.
Scope: finding `ST0-009` (`docs/audits/2026-10-15-stage-0-findings.md`). Stage 0
stays open; no Stable, no version bump, no Watchdog. Job ownership/exclusion
(ST0-003) and the delivery transaction (001/002/003/018) are separate packages;
no retry timers here. Service-state restoration stays out (diagnosis only).

## Intent

- Configuration and reality are never conflated: every backend answer carries
  both the desired (config files) and the effective (systemd services) value.
- A failed transition step fails the switch — no tautological success from
  re-reading the just-written config.
- Divergence is repairable: same-target retry is accepted as repair, rejected
  only as a true no-op (`already_set`) or before a required reboot
  (`needs_reboot`). Failed repair rolls back to the previous backend.

## Non-goals / anti-goals

- No NM-merge parser rewrite (lexical order, `/run`, main file): conf reading
  keeps today's file order; section-awareness is not required in this package.
- No D-Bus/journal effective detection (inventory-grade signals stay in the
  collector); effective = both services' `is-active` (+ `is-enabled` in status).
- No auto-repair without user action; no retry timers; no ST0-003 machinery.

## Decisions (binding)

- **D1 — split reads.** `_read_desired_backend() -> (value, source_path) | (None, None)`:
  today's conf-file loop, unchanged order, plus which file won. Never touches
  services. The service fallback is REMOVED from this path (it enabled the
  conflation; D1 requires separation).
  `_read_effective_backend() -> (value, services)`: `systemctl
  is-active iwd` + `is-active wpa_supplicant` (both, distinguishing
  `active/inactive/failed/unknown`); value is the target iff exactly its service
  is `active` (both-active or none-active → `None` with services reported).
  Never reads conf files. `_get_current_backend()` becomes a thin wrapper over
  `_read_desired_backend()` (fallback deleted) and is documented as
  configured-only; all 4 callers are re-pointed in Task 2 (workers' final reads →
  effective; status `wifi_backend` → desired; `_main` sanity → both).
- **D2 — converged gate.** `start_backend_switch` accepts as `already_set`
  (rejected no-op) only when desired==target AND effective==target. Desired==
  target but effective!=target → accepted as repair (`accepted: True, repair:
  True`, worker runs the transition again). Outstanding-reboot definition:
  `outstanding := _backend_switch.result has needs_reboot True AND no later
  terminal success` (in-memory only; after a reboot the boot-sanity drift
  re-detects an unhealed state). While outstanding → rejected with `reason:
  "needs_reboot"`, never `already_set`. Missing/None
  desired → normal switch (unchanged). The ST0-010 `already_set` tests are
  updated to script desired+effective (agreement→no-op, desired-only→repair).
- **D3 — checked transition steps.** Generic worker checks every `systemctl`
  step (`stop/disable other`, `enable/start target`) and fails fast with named
  codes: `backend_stop_failed`, `backend_disable_failed`, `backend_enable_failed`,
  `backend_start_failed`, `nm_restart_failed`, and `effective_mismatch` for the
  final check; each carries the step name + `stderr` in `detail` and lands in the
  worker result's additive `errors[]`. A failed target `start` fails before the NM
  restart. SteamOS worker keeps its existing checks. Step results use the
  truthful-results `errors[]` convention (additive).
- **D4 — effective verification.** Final verification compares effective (D1)
  against target, not the just-written conf. `success: True` requires all steps
  green AND effective==target. `reconnect_timed_out` stays a connectivity flag
  (ST0-007 territory): it never flips a backend-true transition to false, and a
  backend-false transition never hides behind it — both reported side by side
  (`reconnect` detail per truthful-results).
- **D5 — repair and rollback.** Repair = full worker re-run under the accepted
  repair flag. If repair fails, roll back: restore the previous conf (per route:
  generic → snapshot `file_backend_conf` bytes, else delete the generic conf to
  uncover the prior layer; steamos → helper `write_config <previous-target>` +
  `restart_units`, previous target from the `backend` snapshot slot) +
  `enable/start` the previous service + NM restart + effective verification;
  rollback itself best-effort with each step reported. Rollback never runs blind
  from conf alone. Result carries `repair_of` and, on rollback, `rolled_back:
  True/False`. Contract note (amends 004/016 narrowly): the "services never
  restored" rule governs pre-plugin restoration (reset/uninstall — unchanged);
  rollback re-applies a state the machine held minutes ago inside the user's own
  requested transition, which is why it is safe here. The 5 diagnosis-only
  comment/doc sites (`_restore_slot("backend")`, `file_backend_conf` handler,
  both worker capture notes, reset/uninstall backend notes) are updated to cite
  this distinction. Start accept carries `repair: True/False`; worker/status
  results carry `repair_of`, `rolled_back`, `errors[]` (types updated in Task 4:
  `BackendSwitchStartResult` gains `repair`, `BackendSwitchResult` gains
  `repair_of`/`rolled_back`/`errors`).
- **D6 — status exposes both.** `get_status().live` gains `backend_desired`,
  `backend_effective` (`"unknown"` on the wire when `None`), and
  `backend_services` (`{iwd: {active, enabled}, wpa_supplicant: {...}}`);
  `drift.backend` is set when desired!=effective. `live.wifi_backend` stays
  (desired, backward-compat) and is documented as configured-only.
  `get_diagnostic_info` gains the same backend triple (additive keys;
  absent/failed reads render as `"unknown"`, covered by a failure-path test).
- **D7 — UI divergence (no IPC methods changed).** `BackendToggleRow` renders
  three states: agreement (`effective X`), divergence (`configured X ·
  effective Y`), unknown (`configured X · effective unknown`); never silent
  `"" → iwd` (the `|| "iwd"` default goes behind an explicit unknown branch,
  including `backend_tool_available === false`). While diverged, the toggle offers
  retry-same-target (allowed by D2) and stays out of the optimistic `checked`
  position; retry clears `wifi_backend`/`backendSwitch.error` pre-start and stays
  blocked while `in_progress` (update-job exclusion unchanged, owned by ST0-003);
  `backendSwitch.error` exclusion (package B) is otherwise reused. `types.ts`
  extended (`LiveStatus`: new keys; `BackendSwitchStartResult.repair`;
  `BackendSwitchResult`: `repair_of`/`rolled_back`/`errors`); `getBadge` untouched.
- **D8 — boot sanity surfaces.** Mechanism: `_main` keeps its log-only check
  (rewritten to compare the D1 pair), and `get_status` recomputes
  `drift.backend` live every poll — no new persisted state; the drift, not the
  log, is the surfaced signal. No auto-repair at boot.

## Acceptance

- Conf=target + dead target service + NM restart ok → `success: False`
  (`diverged`), never tautological success; same-target retry accepted as
  repair, not `already_set`.
- True agreement → `already_set` no-op preserved; `needs_reboot` outstanding →
  `needs_reboot` rejection.
- Status on divergence: `backend_desired=X`, `backend_effective=Y/unknown`,
  `drift.backend` set; UI shows divergence with retry action.
- Failed repair: previous conf + service restored best-effort, reported with
  `rolled_back`.
- Repo-wide grep: no success path reading only the just-written conf for
  verification.
- Residual risks disclosed (not fixed here): conf parsing keeps today's file
  order (no NM lexical-order/`/run`/main-file merge); both routes (steamos
  helper, generic systemctl) require separate candidate device evidence.
