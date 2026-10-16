# ST0-005/006 — Profile ownership and observational status — design

Date: 2026-10-16. Baseline: `bcd5ac7` (= `e957c5b` + ST0-010 correction +
PR #4/#5 branding and cutover; `main.py` line numbers re-verified on `bcd5ac7`).
Version `0.11.6`. Scope: findings
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

Labels: S1 = `last_connection_uuid` settings write (`main.py:852-855`); S2 =
priority `100` `nmcli` + `priority_set` write (`main.py:857-863`); S3 = IPv6
repair `nmcli` (`main.py:980-982`); S4 = band repair `nmcli` (`main.py:1001-1004`).
The disconnected early-return (`main.py:844-848`) stays untouched.

- **D1 — read-only status.** Delete S1/S2/S3/S4. Invariant: `get_status` contains no
  `_save_settings`, no `_save_settings_with_timestamp`, no `_nmcli_modify`, no
  `os.replace`, no `open(..., "w")`. `drift` entries stay boolean reports.
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
- **D4 — resolution.** New signature:
  `_resolve_uuid(owner_uuid: str | None, active_required_msg: str | None = None) -> tuple`
  returns `(uuid, None)` or `(None, error_dict)`. No `last_connection_uuid`
  fallback. Examples: enable → `_resolve_uuid(None, "Connect to WiFi first to …")`
  requires active WiFi (`no_wifi` otherwise); disable →
  `_resolve_uuid(owner_uuid)` with no message returns the owner or
  `{success: False, error: "unknown_owner", …}` when empty. Disablers work
  offline against the owner. If active exists and differs from owner, modify the
  owner profile by UUID and skip `_hard_reconnect` (never cycle the radio for
  a foreign profile). Offline success returns `reconnected: False`, not `True`.
  BSSID disable prefers owner over active (ST0-005 fix).
- **D5 — transfer.** Enable on a new active profile overwrites that setting's
  owner. Best-effort clear of the same NM key on the previous owner profile if
  it still exists and differs; a clear failure is logged and reported but does
  not fail the enable. Never two owners for one setting. Per-setting clear
  values (restoration-neutral, same values the disablers already write):
  band → `""`; BSSID → `""`; DNS → `ipv4.dns ""` + `ipv4.ignore-auto-dns "no"`;
  IPv6 → `auto`. Transfer never calls `_hard_reconnect` on the old UUID; only
  the new-UUID enabler reconnects.
- **D6 — legacy unknown-owner.** `enabled=True` + owner empty: status keeps
  `drift.<setting> = True` (bool, unchanged type) and additionally reports an
  additive `status["unknown_owners"]: list[str]` naming the settings whose owner
  is unknown; zero mutations. Split setter behavior per setting: enable with
  unknown owner returns `{success: False, error: "unknown_owner", message:
  "Setting is enabled but its network profile is unknown. Re-apply on the desired
  network."}`, intent preserved, zero `nmcli` calls; disable with unknown owner
  clears only the intent (`enabled False`, owner stays empty), zero `nmcli`
  calls, `{success: True, reconnected: False}`. Exit path for a real profile
  change is an explicit re-apply. No new IPC parameters; `unknown_owners` is
  additive and ignored by the current frontend, `drift` types are unchanged.
- **D7 — failures/retries.** Failed `nmcli` → no settings write, owner
  retained, no reconnect, no `last_applied` bump, `{success: False, error:
  "nmcli_failed", message: …, detail: stderr}`; retry stays possible (offline
  for disablers). DNS two-key divergence returns `{success: False, error:
  "dns_partial", message: which key failed, detail: stderr}`, intent not saved
  `True`. Band→BSSID relock (`main.py:1201-1230`) runs only when
  `band_owner_uuid == bssid_lock_connection_uuid` and both are non-empty;
  otherwise the relock is skipped entirely. When it runs, the parsed BSSID must
  be a verified non-empty MAC; relock `nmcli` failure returns `{success: False,
  error: "relock_failed", message: …, detail: stderr, band: value}` — never a
  silent band success. Full reconnect-result contracts stay with ST0-007.
- **D8 — DNS scope.** DNS gets `dns_owner_uuid` like band/IPv6 (same per-profile
  NM keys `ipv4.dns` / `ipv4.ignore-auto-dns`), because disconnected DNS
  disable shares the removed `last-UUID` dependency: `main.py:1242` resolves via
  fallback, `main.py:1284-1285` clears both keys without checking results, and
  the fallback source is `main.py:372-375`. This extends — not widens — the
  handoff's disconnected-preservation requirement.

## Acceptance

- Polling B with intent from A: zero `nmcli mod`, zero settings writes, drift
  only reported; `last_connection_uuid` untouched (deprecated).
- Active-B + owner-A disable: modifies A by UUID, preserves A's ownership on
  failure, never clears B, never reboots B's radio.
- Offline disabler with owner A + poisoned `last_connection_uuid=B`: modifies
  A.
- Legacy enabled-without-owner: enable → `unknown_owner`, zero mutations;
  disable → intent-only clear, `{success: True, reconnected: False}`;
  status adds additive `unknown_owners` list, `drift` types unchanged.
- Priority `100` never written by any path in this package.
