# ST0-005/006 — Profile ownership and observational status — design

Date: 2026-10-16. Baseline: `bcd5ac7`, version `0.11.6`. Scope: findings
`ST0-005` (`docs/audits/2026-10-15-stage-0-findings.md:48-52`) and `ST0-006`
(`:54-58`), handoff item 1 (`:191`). Stage 0 stays open; no Stable, no version
bump, no Watchdog, no recovery engine.

## Intent

- `get_status()` (`main.py:816-1034`) becomes pure observation: reports `live`
  and `drift`, never writes `settings.json`, never runs `nmcli con mod`.
- Every per-connection setting has an explicit owner UUID, recorded only on
  verified explicit success. Disablers work offline against the owner, never
  against "last seen" or foreign active profiles.
- Legacy `enabled=True` without a known owner is handled explicitly, never
  guessed.

## Non-goals / anti-goals

- No `connection.autoconnect-priority 100` anywhere automatic (not in status,
  not moved to another automatic path). Existing `100`s on profiles stay
  untouched in this package; revert belongs to ST0-004/016.
- No restoration-contract change (ST0-004/016), no reconnect-result overhaul
  (ST0-007), no backend-state change (ST0-009), no UI/API shape change.
- No guessing a profile from `last_connection_uuid`. No backfill of owners
  from it.

## Decisions (binding)

- **D1 — read-only status.** Delete `main.py:852-863` (S1/S2), `main.py:980-982`
  (S3), `main.py:1001-1004` (S4). Invariant: `get_status` contains no
  `_save_settings` and no `_nmcli_modify`. Static grep test pins it.
- **D2 — priority deprecation.** `priority_set` becomes read-compat only
  (ignored). No code sets priority. Document that pre-existing `100`s remain
  until the restoration package.
- **D3 — per-setting owners.** Keep `bssid_lock_connection_uuid`; add
  `band_owner_uuid`, `dns_owner_uuid`, `ipv6_owner_uuid` to `DEFAULT_SETTINGS`
  (`main.py:143-169`). Written only after a verified `nmcli` success, before
  reconnect; cleared only by that setting's successful disable. `last_connection_uuid`
  is deprecated: no writes; `_get_saved_connection_uuid()` (`main.py:372-375`)
  is removed and replaced by per-feature resolution. Never backfill owners
  from `last_connection_uuid`.
- **D4 — resolution.** Enablers keep requiring active WiFi (`_resolve_uuid`
  with `active_required_msg`). Disablers resolve **only** their setting's owner
  UUID and work offline. If active exists and differs from owner, modify the
  owner profile by UUID and skip `_hard_reconnect` (never cycle the radio for
  a foreign profile). Offline success returns `reconnected: False`, not `True`.
  BSSID disable prefers owner over active (ST0-005 fix).
- **D5 — transfer.** Enable on a new active profile overwrites that setting's
  owner. Best-effort clear of the same NM key on the previous owner profile if
  it still exists and differs; a clear failure is logged and reported but does
  not fail the enable. Never two owners for one setting.
- **D6 — legacy unknown-owner.** `enabled=True` + owner empty: status reports
  `drift.<setting> = "owner_unknown"`, zero mutations; any setter for it
  returns `{success: False, error: "unknown_owner", message: "…re-apply on the
  desired network."}`, preserves intent, zero `nmcli` calls. Exit path is an
  explicit re-apply. No new IPC parameters in this package.
- **D7 — failures/retries.** Failed `nmcli` → no settings write, owner
  retained, no reconnect, no `last_applied` bump, `nmcli_failed` with `detail`;
  retry stays possible (offline for disablers). DNS two-key partial is not
  success. Band→BSSID relock (`main.py:1201-1230`) runs only when
  `band_target == bssid_owner`, verifies parsed MAC, checks the relock result;
  relock failure yields `partial`, not silent success. Full reconnect-result
  contracts stay with ST0-007.
- **D8 — DNS scope.** DNS gets `dns_owner_uuid` like band/IPv6 (same per-profile
  NM keys `ipv4.dns` / `ipv4.ignore-auto-dns`), because disconnected DNS
  disable shares the removed `last-UUID` dependency.

## Acceptance

- Polling B with intent from A: zero `nmcli mod`, zero settings writes, drift
  only reported; `last_connection_uuid` untouched (deprecated).
- Active-B + owner-A disable: modifies A by UUID, preserves A's ownership on
  failure, never clears B, never reboots B's radio.
- Offline disabler with owner A + poisoned `last_connection_uuid=B`: modifies
  A.
- Legacy enabled-without-owner: `unknown_owner`, zero mutations.
- Priority `100` never written by any path in this package.
