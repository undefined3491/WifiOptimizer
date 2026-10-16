# ST0-004/016 — Ownership snapshot and restoration semantics — design

Date: 2026-10-16. Baseline: `24811a7` (= `bcd5ac7` + ST0-005/006), version `0.11.6`.
Scope: findings `ST0-004` (`docs/audits/2026-10-15-stage-0-findings.md:42-46`) and
`ST0-016` (`:114-116`), handoff item 2 first half. Stage 0 stays open; no Stable,
no version bump, no Watchdog. Delivery findings 001/002/003/018 and the
native-vs-custom updater decision are a separate package gated on an owner
decision; this package does not select it.

## Intent

- The plugin restores only state it changed. First mutation of each domain
  captures the prior value into a snapshot; disable/reset/uninstall restore
  from the snapshot instead of writing assumed defaults.
- `reset_settings()` becomes a full reconciliation to the saved defaults
  (option R1): what it declares (`power_save_disabled=True`,
  `auto_fix_on_wake=True`, rest `False`/empty) is what it applies to live
  state, NM files, dispatcher and owned profiles.
- Custom state the plugin never enabled is never touched (proven by an
  all-flags-false test).

## Non-goals / anti-goals

- No pre-plugin baseline recovery on already-modified machines: the first
  snapshot on a legacy-modified installation records current (modified) values
  as the baseline. This is disclosed, not hidden. The pre-plugin baseline is
  unrecoverable and must not be claimed.
- No ST0-008 overhaul (per-write result checking stays as-is except restore
  steps, which check and report). No ST0-007 reconnect contracts. No backend
  effective-state work (ST0-009). No UI rendering of aggregates (ST0-014).
- No new `autoconnect-priority` writes anywhere; pre-existing `100`s stay
  untouched (see D7). No backfill of ST0-005/006 owner UUIDs.

## Decisions (binding)

- **D1 — snapshot store.** Separate file `SETTINGS_DIR/system_snapshot.json`
  (same dir as `settings.json`), atomic write (`.tmp` + `os.replace`, same
  pattern as `_save_settings`). Never inside `settings.json`: `_load_settings`
  strips unknown keys, so in-settings slots would be silently dropped. Slots are
  captured once: slot present → never overwrite. Slot missing at restore time →
  today's assumed-default behavior as fallback, logged.
- **D2 — slot contents.** `sysctl`: current `sysctl -n` for all 8 `SYSCTL_PARAMS`
  keys. `txqueuelen`: current per-iface value + iface name. `qdisc`: raw
  `tc qdisc show dev <iface>` output. `power_save`: `iw … get power_save` result
  or `iface_absent` marker. `pcie`: raw contents of the 6 `link/*` files +
  `power/control` + resolved device path. `driver_sysfs`: raw content per
  existing path + `missing` marker per absent path. `files`: existence + full
  bytes for `NM_CONF_PATH`, `MODPROBE_CONF_PATH`, `GENERIC_BACKEND_CONF`,
  `DISPATCHER_PATH`. `backend`: `_get_current_backend()` + `is-enabled`/`is-active`
  for `iwd`/`wpa_supplicant`. `profiles`: per-UUID map of prior values for exactly
  the keys each setter touches (`802-11-wireless.bssid`, `802-11-wireless.band`,
  `ipv4.dns`, `ipv4.ignore-auto-dns`, `ipv6.method`), read via `nmcli` before modify.
- **D3 — capture points.** Enabling setters/workers capture their domain slots
  before the first write of that domain: `set_power_save(True)` → power/NM-conf/
  pcie/driver-sysfs/modprobe slots; `set_buffer_tuning(True)` → sysctl + txq;
  `set_cake(True)` → qdisc + txq interplay; backend workers → backend slot;
  each per-profile enable → that key's prior value on the target UUID.
  `optimize_safe`/`reapply_all`/`_main` funnel through the same setters and get
  no separate logic, except: `_main` re-apply must not treat an already-mutated
  boot state as clean — capture still applies slot-present-never-overwrite, so a
  reboot can never clobber the snapshot.
- **D4 — restore rules.** A disabler restores only domains this version enabled
  (per settings flags) from the snapshot; anything else is left untouched.
  Shared `txqueuelen` (buffer vs CAKE) is one slot with ordered restore: qdisc
  before txq, mirroring apply order. qdisc restore is best-effort re-add from the
  snapshot output; if re-add fails it is logged and reported — exact qdisc-option
  fidelity is an accepted limitation pending device validation.
- **D5 — reset semantics (R1).** `reset_settings()` reconciles to the saved
  defaults: (a) volatile/system domains restored from snapshot (fallback
  defaults); (b) live `iw` and `NM_CONF_PATH` brought to the state matching
  saved `power_save_disabled=True` (`iw off` + conf written, not deleted);
  (c) dispatcher installed to match saved `auto_fix_on_wake=True`;
  (d) all per-profile NM keys on known owner UUIDs cleared **before** wiping
  `settings.json` (owners read first), reconnect only where owner==active;
  (e) fresh settings saved with `last_applied=now` (timestamped, like setters).
  Backend (`WIFI_BACKEND_CONF`/services) is explicitly out of reset scope.
- **D6 — uninstall semantics.** Same restoration as reset, plus dispatcher
  removal, settings-files removal (no fresh write), generic backend conf removal
  (current behavior kept), and best-effort restore of `iwd`/`wpa_supplicant`
  service enablement from the snapshot (failures logged). Live `iw` restored to
  the snapshot value (no longer left in `off`).
- **D7 — legacy priority `100`s.** Profiles already carrying
  `connection.autoconnect-priority 100` from the old version are not modified by
  any path in this package. Documented leftover; removal is forget/rejoin or a
  future explicit repair, not silent automation.
- **D8 — dispatcher role.** The dispatcher keeps its enable-only writers and
  gains no snapshot role; capture happens exclusively in `main.py` setters.
- **D9 — transfer-clear consults the snapshot.** Clearing the previous owner
  profile on transfer restores that profile's snapshotted prior value when
  present, else the assumed default. (Refines the ST0-005/006 transfer rule;
  no owner-model change.)
- **D10 — truthful restore results.** Every restore step checks its result;
  failures are logged and returned in the operation's errors (no silent
  success). UI rendering of aggregates stays with ST0-014.

## Acceptance

- All optional flags false against custom state: zero writes, zero deletes,
  zero `nmcli mod` (new test with pre-seeded foreign values).
- Enable/disable round-trip per domain restores the recorded baseline exactly
  (sysctl bytes, txq, qdisc presence, `iw`, NM conf bytes, sysfs contents,
  profile keys).
- Legacy install without snapshot: fallback path runs today's behavior and logs it.
- Reset ends with live `iw` off, NM conf present with `wifi.powersave = 2`,
  dispatcher installed, owned profiles cleared, `last_applied != 0`.
- No `autoconnect-priority` write on any path in this package.
