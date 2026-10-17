# Candidate record — `a3bb26b` (2026-10-17)

Status: **PENDING** — code-complete, **device validation not started**.
Stage 0 remains **open**. This file is a DOCS-ONLY validation-prep record.
No version bump, no tag, no release publication implied.

## 1. Candidate identity

| Field | Value |
| --- | --- |
| Candidate commit (short / full) | `a3bb26b` / `a3bb26be01812189edebb66a932d40965f3d17bd` |
| Commit subject | `Stable-only hardened delivery (drop Beta, ST0-001/002/003/018) (#14)` |
| Commit date | 2026-10-17 09:41:26 +0200 |
| Branch merged to | `main` (squash merge of `codex/` branch via PR #14) |
| `package.json` version | `0.11.6` (unchanged — provisional; **no bump in this record**) |
| Baseline audited | `e957c5b49797ef456cbd8edf093eb83704aac805` (2026-10-15, PR #1) |
| Tags / releases | **None** — no `vX.Y.Z` tag created, no GitHub release published |

### Identity verification (run on the validation checkout — do not copy hashes by hand)

```bash
git rev-parse HEAD
# expected: a3bb26be01812189edebb66a932d40965f3d17bd

git log -1 --format="%H %ad %s" --date=iso

git ls-files -s dist/index.js dist/index.js.map
# worktree-observed blob ids (re-verify, do not trust this file):
# dist/index.js     a89bb5e98522c44ad16a41b238020e9ccbcc1f8e
# dist/index.js.map b01566f45a86cc3a968e50e29d4f52c1bea4d5ff

sha256sum dist/index.js dist/index.js.map
# TO-FILL on device checkout (record actual output here)

git tag --list
# expected: empty (no tag for this candidate)

grep '"version"' package.json
# expected: "0.11.6"
```

`dist/index.js` and `dist/index.js.map` are tracked release files and are
present in this candidate. CI checks that committed output matches a fresh
build (`pnpm run build`); the device record must confirm the deployed bundle
matches the named commit before any validation result counts.

## 2. What this candidate contains — merged PRs #7–#14

All corrections below are **source + isolated-test verified only**.
Candidate-specific **device validation is pending** for every item.
Source of correction detail: `docs/audits/2026-10-15-stage-0-findings.md`
("Correction progress — 2026-10-16/17" section).

| PR | Merge commit | One-liner (corrected finding) |
| --- | --- | --- |
| #7 | `24811a7` 2026-10-16 — ST0-005/006 profile ownership and observational status | `get_status()` is read-only (no settings writes, no NM profile/priority mutations); BSSID/band/DNS/IPv6 carry explicit owner UUIDs recorded only on verified explicit success; disconnected disablers resolve the owner offline; legacy enabled-without-owner splits into enable→`unknown_owner` vs disable→intent-only clear; 16 isolated tests red→green. |
| #8 | `42c7bb9` 2026-10-16 — ST0-004/016 ownership snapshot and restoration semantics | First mutation per domain snapshots the prior value into `SETTINGS_DIR/system_snapshot.json` (separate file, atomic, slot-once); disablers restore only owned domains; `reset_settings()` is a full reconciliation to saved defaults; `_uninstall` restores plus dispatcher/files/snapshot removal; 12 isolated tests red→green. |
| #9 | `d091a2c` 2026-10-16 — ST0-007/008 truthful mutation results + 014/017/019 UI consumption | `_hard_reconnect` returns per-stage verified results; failed writes block intent with named errors; UI consumes all results (child mapping, counts banner, reset/update/diagnostic checks); 17 isolated tests red→green, rebuilt tracked `dist`. |
| #10 | `c86c486` 2026-10-16 — ST0-009 backend desired vs effective state | Desired config readers split from systemd effective-state readers; `already_set` only on true convergence; failed repair rolls back per route; status shows `backend_desired`/`backend_effective`/`backend_services` triple; 10 isolated tests red→green, ST0-010 reservation tests extended. |
| #11 | `674820b` 2026-10-16 — ST0-021/022 truthful copy + ST0-023 toolchain triage | Band row promises only NM `"a"` (5 GHz); CAKE described as local egress queue with no power over other devices/AP/ISP; build audit reduced via scoped `pnpm.overrides` on `brace-expansion` (1 residual `braces` GHSA documented, not forced); frozen install / build / `tsc --skipLibCheck` / 101-test suite green. |
| #12 | `ff10680` 2026-10-16 — ST0-011/012/013/015/020 repair flow, DNS draft, poll lifecycle | New `repair_drifted()` repairs only enabled-and-drifted settings (drift banner no longer calls preset-enabling Optimize Safe); custom DNS draft/applied separated; backend poll bounded retry with working Retry action; all timers/awaits dismount-guarded; 11 isolated tests red→green (`test_repair_drift.py`). |
| #13 | `0c6997a` 2026-10-17 — Update delivery decision: native Decky ZIP (A1) | Decision/design record for the delivery direction (evaluate native Decky ZIP lifecycle before committing to a custom recovery engine). Decision input to #14, not a runtime fix by itself. |
| #14 | `a3bb26b` 2026-10-17 — Stable-only hardened delivery (drop Beta, ST0-001/002/003/018) | Beta channel dropped (Stable-only updater + installer, stored `"beta"` migrates automatically); single update job with phase machine and cross-exclusion against backend switches; same-filesystem sibling staging; validated transfer/identity; per-file commit with version files last; truthful restart/result reporting; `install.sh` as validated rescue; 10 isolated tests red→green, full suite 132 OK. The two designed-out open questions (fixed-`/tmp` updater script, updater shell interpolation) are gone with the detached script; event-loop blocking, dispatcher races, adapter coverage stay explicitly open. |

Earlier, already in `main` before this candidate range and referenced for
completeness: PR #6 (`18bf6e1`, ST0-010 entry reservation race — reserve
before first await, 9 isolated tests) and PRs #4/#5 (TMS display/package
branding and repository cutover to `undefined3491/wifi-optimizer-tms`).

Result: **all 14 Important and 9 Minor Stage 0 findings are corrected in
source with isolated verification** (per the findings report). No Critical
finding was established by the static review. This is code-completeness, not
closure.

## 3. Stage 0 status

- **Static review:** completed 2026-10-15 (owner-selected `gpt-6.1-sol`
  subagents; coordinator report in `docs/audits/2026-10-15-stage-0-findings.md`).
- **Corrections:** code-complete for all numbered findings (PRs #6–#12, #14);
  isolated regression suites green (132 tests OK on Linux; 3 inventory cases
  skip on Windows for FIFO/pipe/symlink support — Linux CI must run them).
- **Pending (blocks Stage 0 closure and first Stable):**
  candidate-specific **LCD / SteamOS Stable device validation** per
  `docs/testing/steam-deck-lcd-stable.md`, plus the first Stable release
  through the manual process.
- Explicitly **not** established by static checks: optimization benefit,
  reconnect/sleep-wake behavior, reset/uninstall recovery on real state,
  installer/update end-to-end on device, battery/throughput comparisons.
- Prior device evidence (`docs/testing/results/2026-10-16-owner-device-inventory.md`)
  observes the already-modified legacy installation — it is **not** a
  corrected-candidate validation and must not be cited as one.

## 4. Release policy applicable to this candidate

Per `AGENTS.md` and `CONTRIBUTING.md` (summarized — normative text lives there):

- Merging does **not** publish. No auto-Stable on merge; no Beta channel.
- Stable publication is a **manual decision** after review, `ci-required`
  check, and a **smoke test on a supported device** (for networking changes:
  including reconnect and sleep/wake).
- Release preparation happens in a dedicated (or explicitly designated) PR:
  bump `package.json` (patch = fixes, minor = features; docs/CI-only needs no
  bump), add a matching `## [<version>]` section to `CHANGELOG.md`, rebuild
  and commit **both tracked `dist` files in the exact tagged commit**.
- Stable releases use tag **`v<package.json version>`**, created by the manual
  **Stable release** workflow dispatched from `main` with the device-test
  attestation. Existing tags/releases are refused; rerun after tag creation
  intentionally stops.
- This candidate record performs **none** of those steps: no bump, no
  `CHANGELOG` entry, no tag, no dispatch.

## 5. Validation scope for this candidate

Execute `docs/testing/steam-deck-lcd-stable.md` against the exact commit in
§1, after recording environment + baseline + recovery per that protocol:

1. Environment capture (SteamOS version/build/channel, kernel, adapter/driver,
   active NM backend, Decky version, plugin commit/version/bundle identity,
   AP/router/band setup, power conditions, prior-install state).
2. Baseline + recoverable snapshot (NM profiles, config files, services,
   driver/sysfs power, sysctls, qdisc/queue) **before** changing any option.
3. Controlled single-option comparisons (power save/ASPM, BSSID, band,
   DNS/IPv6, buffers/CAKE, backend switch, then preset last).
4. Lifecycle: startup (fresh + saved), WiFi off/on, AP loss/recovery,
   disconnected edits, short + long suspend/resume with counts/durations,
   reset/disable/uninstall vs restoration contract, installer/update behavior
   (no Stable publication as a test fixture), UI truthfulness under failure.
5. Store the dated result under `docs/testing/results/` with
   Pass/Fail/Not-tested per item; untested stays untested, never a pass.

Target: owner LCD on SteamOS Stable. OLED / other handhelds / other distros /
Beta are separate records, not substitutes.

## 6. DRAFT release notes (version placeholder — DO NOT PUBLISH)

> **DRAFT — `WiFi Optimizer TMS vX.Y.Z` (placeholder; version assigned only
> at release preparation). PENDING device validation; Stage 0 open.**

### What would be in this release (from Stage 0 correction work)

- Truthful status and profile ownership: `get_status()` no longer writes
  settings or mutates NM profiles; per-profile owner UUIDs with offline
  disablers and legacy `unknown_owner` handling (ST0-005/006).
- Owned restoration: pre-change snapshot, restore-only-owned semantics,
  reconciled reset and uninstall paths (ST0-004/016).
- Honest results: verified reconnect reporting, named per-write errors, UI
  surfacing of child/top-level/diagnostic failures (ST0-007/008/014/017/019).
- Backend desired-vs-effective separation with divergence repair/rollback
  (ST0-009) and pre-await switch reservation (ST0-010).
- Repair-instead-of-preset drift flow, usable custom-DNS editor, bounded
  backend polling with retry, dismount-safe timers (ST0-011/012/013/015/020).
- Corrected band/CAKE wording and triaged build toolchain
  (ST0-021/022/023).
- Stable-only hardened delivery: Beta channel removed, single update job
  with backend-switch exclusion, staged validated install, truthful
  restart/result reporting, `install.sh` rescue path (ST0-001/002/003/018).

### Known limitations (must stay in the notes until device evidence says otherwise)

- No candidate-specific LCD / Stable validation yet — benefit, reconnect,
  sleep/wake, recovery and update end-to-end are unproven for this code.
- Event-loop blocking/backlog, dispatcher races, and adapter/capability
  coverage remain explicitly open (see findings report §"Open questions").
- `priority 100` pre-existing values and pre-plugin baselines are untouched
  and disclosed (ST0-004/016 scope note).
- One residual build advisory (`braces` GHSA via `micromatch@4.0.8`) is
  documented, not forced (major bump would break semver/build).
- No Connection Watchdog feature exists in this candidate; do not list it.

## 7. Fields requiring completion on device (TO-FILL)

- [ ] `sha256sum dist/index.js dist/index.js.map` on the validation checkout
      (command in §1) — record output here.
- [ ] Installed environment: SteamOS version/build/channel, kernel, WiFi
      adapter/driver, active NM backend, Decky version/channel.
- [ ] Deployed bundle identity on Deck matches §1 (commit + dist hashes).
- [ ] Baseline snapshot reference (recoverable copies) + existing-install
      state label (modified vs pristine).
- [ ] AP/router/band setup, power source/level, workload definition,
      run counts/durations.
- [ ] Per-item Pass/Fail/Not-tested table + logs/screenshots, linked to
      ST0 finding IDs.
- [ ] Reconnect + sleep/wake results (required: networking changes present).
- [ ] Reset/disable/uninstall vs restoration-contract comparison.
- [ ] Installer/update behavior exercised (document any unexercised path).
- [ ] Device-test attestation (name/date) — required before any Stable
      dispatch; dispatch itself is a separate manual step, not this file.
