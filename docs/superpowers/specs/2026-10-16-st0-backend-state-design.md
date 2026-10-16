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
  services. `_read_effective_backend() -> (value, services)`: `systemctl
  is-active iwd` + `is-active wpa_supplicant` (both, distinguishing
  `active/inactive/failed/unknown`); value is the target iff exactly its service
  is `active` (both-active or none-active → `None` with services reported).
  Never reads conf files. `_get_current_backend()` stays as the desired-reader
  for backward-compat callers and is documented as configured-only.
- **D2 — converged gate.** `start_backend_switch` accepts as `already_set`
  (rejected no-op) only when desired==target AND effective==target. Desired==
  target but effective!=target → accepted as repair (`accepted: True, repair:
  True`, worker runs the transition again). Terminal `needs_reboot` outstanding
  → rejected with `reason: "needs_reboot"`, never `already_set`. Missing/None
  desired → normal switch (unchanged).
- **D3 — checked transition steps.** Generic worker checks every `systemctl`
  step (`stop/disable other`, `enable/start target`) and fails fast with the
  step name + `stderr` in `detail`; a failed target `start` fails before the NM
  restart. SteamOS worker keeps its existing checks. Step results use the
  truthful-results `errors[]` convention (additive).
- **D4 — effective verification.** Final verification compares effective (D1)
  against target, not the just-written conf. `success: True` requires all steps
  green AND effective==target. `reconnect_timed_out` stays a connectivity flag
  (ST0-007 territory): it never flips a backend-true transition to false, and a
  backend-false transition never hides behind it — both reported side by side
  (`reconnect` detail per truthful-results).
- **D5 — repair and rollback.** Repair = full worker re-run under the accepted
  repair flag. If repair fails, roll back: restore the previous conf (snapshot
  `file_backend_conf` bytes, else delete the generic conf to uncover the prior
  layer) + `enable/start` the previous service + NM restart + effective
  verification; rollback itself best-effort with each step reported. Rollback
  never runs blind from conf alone. Result carries `repair_of` and, on
  rollback, `rolled_back: True/False`.
- **D6 — status exposes both.** `get_status().live` gains `backend_desired`,
  `backend_effective` (may be `None` → `"unknown"` on the wire), and
  `backend_services` (`{iwd: {active, enabled}, wpa_supplicant: {...}}`);
  `drift.backend` is set when desired!=effective. `live.wifi_backend` stays
  (desired, backward-compat) and is documented as configured-only.
  `get_diagnostic_info` gains the same backend triple (additive).
- **D7 — UI divergence (no IPC methods changed).** `BackendToggleRow` renders
  three states: agreement (`effective X`), divergence (`configured X ·
  effective Y`), unknown (`configured X · effective unknown`); never silent
  `"" → iwd`. While diverged, the toggle offers retry-same-target (allowed by
  D2) and stays out of the optimistic `checked` position; `backendSwitch.error`
  exclusion (package B) is reused. `types.ts` extended; `getBadge` untouched.
- **D8 — boot sanity surfaces.** `_main`'s existing conf-vs-active check feeds
  the same desired/effective pair so the next `get_status` shows the drift
  instead of only a log line; no auto-repair at boot.

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
