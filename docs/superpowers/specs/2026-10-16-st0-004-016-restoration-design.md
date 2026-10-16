# ST0-004/016 — Ownership snapshot and restoration semantics — design

Date: 2026-10-16. Baseline: `24811a7` (= `bcd5ac7` + ST0-005/006), version `0.11.6`.
Scope: findings `ST0-004` (`docs/audits/2026-10-15-stage-0-findings.md:42-46`) and
`ST0-016` (`:114-116`), handoff item 2 first half. Stage 0 stays open; no Stable,
no version bump, no Watchdog. Delivery findings 001/002/003/018 and the
native-vs-custom updater decision are a separate package gated on an owner
decision; this package does not select it. Delivery findings 001/002/003/018
and restart-result reporting are tracked there, not here.

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

## Canonical contract (binding names)

Helpers (exact names; `_load_snapshot`/`_save_snapshot` are module-level like the
settings helpers, `_capture_slot`/`_restore_slot` are `Plugin` methods since they
need `self._run_cmd`/iface — callers guard with `try/except`, never throw):

- `_load_snapshot() -> dict` — read `SETTINGS_DIR/system_snapshot.json`, `{}` when absent/unparseable.
- `_save_snapshot(data: dict) -> None` — atomic write (`.tmp` + `os.replace`).
- `_capture_slot(name: str) -> None` — capture the slot's current value when the slot is absent; never overwrite a present slot. Value readers per slot below.
- `_restore_slot(name: str) -> str | None` — restore the slot; returns `None` on success, an error string on failure or on missing slot (caller falls back to the assumed default and logs + reports the fallback).

Slot literals: `sysctl`, `txqueuelen`, `qdisc`, `power_save`, `pcie`, `driver_sysfs`,
`file_nm_conf`, `file_modprobe_conf`, `file_backend_conf`, `file_dispatcher`,
`backend`, `profile_<uuid>_<key>` (one slot per owned profile key, e.g.
`profile_abc_802-11-wireless.band`).

Restore-failure reporting (additive, IPC-safe): operations gain an `errors:
list[str]` key (empty when clean); existing `success`/`message` keys keep their
shapes. The current frontend ignores unknown keys; rendering stays with ST0-014.

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
  With a legacy `enabled=True` + empty owner (`unknown_owner`), there is no
  slot and no UUID to guess: intent-only clear runs with zero `nmcli`/writes
  (ST0-005/006 rule kept), no snapshot involved, fallback logged.
  Shared `txqueuelen` (buffer vs CAKE) is one slot with ordered restore: qdisc
  before txq, mirroring apply order. qdisc restore: when the snapshot shows no
  qdisc → `tc qdisc del dev <iface> root`; otherwise `tc qdisc replace dev
  <iface> root <tokens after "root" from the snapshotted line>`. A failed
  re-add is logged and reported in `errors` — exact option fidelity is an
  accepted limitation pending device validation.
- **D5 — reset semantics (R1).** `reset_settings()` reconciles to the saved
  defaults: (a) volatile/system domains restored from snapshot (fallback
  defaults, each fallback logged + reported in `errors` as a warning entry);
  (b) live `iw` and `NM_CONF_PATH` brought to the state matching
  saved `power_save_disabled=True` (`iw off` + conf written, not deleted);
  (c) dispatcher installed to match saved `auto_fix_on_wake=True` (capture the
  `file_dispatcher` slot in `set_auto_fix(True)` before install; `_main`'s
  install path captures too when the slot is absent);
  (d) per-profile cleanup **before** wiping `settings.json`: for each known owner
  (`bssid_lock_connection_uuid`, `band_owner_uuid`, `dns_owner_uuid`,
  `ipv6_owner_uuid`, non-empty only) clear exactly that setting's keys —
  BSSID → `802-11-wireless.bssid ""`, band → `802-11-wireless.band ""`,
  DNS → `ipv4.dns ""` + `ipv4.ignore-auto-dns "no"`, IPv6 → `ipv6.method "auto"`;
  then a single `_hard_reconnect(active)` only if at least one cleared UUID
  equals the active UUID, else no reconnect; reconnect/result failures land in
  `errors`, never throw;
  (e) fresh settings saved with `last_applied=now` (timestamped, like setters).
  Backend is explicitly out of reset scope: reset no longer deletes
  `GENERIC_BACKEND_CONF` (that `os.remove` line is deleted); service states and
  `99-valve-wifi-backend.conf` are untouched.
- **D6 — uninstall semantics.** Same restoration as reset, plus dispatcher
  removal, settings-files removal (no fresh write, snapshot file deleted by
  `_uninstall`), and generic backend conf removal (current behavior kept).
  Service enablement (`iwd`/`wpa_supplicant`) is NOT restored — snapshot keeps
  the observed values for diagnosis only; changing service state beyond today
  belongs to the backend/delivery package (ST0-009, 001/002/003/018).
  Live `iw` is restored to the snapshot value (no longer left in `off`).
  The dispatcher template is untouched by this package: its self-removal list
  does not cover the snapshot file, which harmlessly persists across a native
  replace (slots are version-independent system state, never-overwrite guarded).
- **D7 — legacy priority `100`s.** Profiles already carrying
  `connection.autoconnect-priority 100` from the old version are not modified by
  any path in this package. Documented leftover; removal is forget/rejoin or a
  future explicit repair, not silent automation.
- **D8 — dispatcher role.** The dispatcher keeps its enable-only writers and
  gains no snapshot role; capture happens exclusively in `main.py` setters.
- **D9 — transfer-clear consults the snapshot.** Clearing the previous owner
  profile on transfer restores that profile's snapshotted prior value when
  present, else the assumed default. Transfer-clear failures use the existing
  `transfer_warnings: list[str]` channel (`"key: stderr"` entries, empty when
  clean — ST0-005/006 shape, unchanged). (Refines the ST0-005/006 transfer rule;
  no owner-model change.)
- **D10 — truthful restore results.** Every restore step checks its result via
  `_restore_slot` (returns `None` or an error string); failures are logged and
  appended to the operation's additive `errors: list[str]`. Fallback uses are
  reported there as `"fallback:<slot>"` warnings. UI rendering of aggregates
  stays with ST0-014. Before running Reset on the owner Deck as a recovery
  mechanism, capture the LCD state per `docs/testing/steam-deck-lcd-stable.md`;
  the filtered inventory report is not a backup.

## Acceptance

- All optional flags false (the six per-setting enables + `auto_fix_on_wake`,
  scope: disablers, `_main` re-apply and dispatcher `up` handling — reset and
  uninstall excluded by design since R1 reconciles to `True/True` defaults):
  zero writes, zero deletes, zero `nmcli mod` against seeded foreign custom values.
- Enable/disable round-trip per domain restores the recorded baseline exactly
  (sysctl bytes, txq, qdisc presence, `iw`, NM conf bytes, sysfs contents,
  profile keys).
- Legacy install without snapshot: fallback path runs today's behavior and logs it.
- Reset ends with live `iw` off, NM conf present with `wifi.powersave = 2`,
  dispatcher installed, owned profiles cleared, `last_applied != 0`.
- No `autoconnect-priority` write on any path in this package.
