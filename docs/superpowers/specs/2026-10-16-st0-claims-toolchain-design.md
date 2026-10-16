# ST0-021/022/023 — Accurate claims and toolchain triage — design

Date: 2026-10-16. Baseline: `c86c486` (= `d091a2c` + ST0-009), version `0.11.6`.
Scope: findings `ST0-021`, `ST0-022`, `ST0-023`
(`docs/audits/2026-10-15-stage-0-findings.md`). Stage 0 stays open; no Stable,
no version bump, no Watchdog. No backend behavior change in this package.

## Intent

- The band toggle promises only what it submits: NM `802-11-wireless.band`
  `"a"` (5 GHz). No 6 GHz choice is implied, offered, or sent.
- CAKE is described as a local egress queue with no power over other devices,
  the AP, or the ISP bottleneck.
- Build-tool advisories are triaged with a reproducible lockfile update, not an
  automatic fix or speculative override.

## Non-goals / anti-goals

- No `"6GHz"` enum support (requires capability detection + device evidence —
  a separate future change, not this package).
- No `tc cake` flag changes; no dispatcher/template changes.
- No `pnpm audit --fix`, no hand-edited lockfile versions, no dependency
  changes to silence the known `react-router` TS2307 in `@decky/api`.
- No mixing toolchain changes with product fixes in one commit.

## Decisions (binding)

- **D1 — band label (ST0-021).** `src/index.tsx` band `InfoRow`: static label;
  delete the now-unused `const supports6GHz` line (this is not a plumbing change:
  `supports_6ghz` field, `types.ts`, backend detection/whitelist and
  `s?.band_preference` stay untouched). Keep the LCD antennas clause (factual,
  keeps `isDeckLcd` used). Exact new texts:
  - label: `Force 5 GHz band`
  - subtitle: `Lock this profile to 5 GHz (NM band "a")`
  - explanation: `Sets NetworkManager 802-11-wireless.band to "a" on this saved profile. "a" means 5 GHz only — it will not use 2.4 GHz or 6 GHz for this network.` + the existing Bluetooth/LCD sentences unchanged + the existing 2.4-GHz-only warning unchanged + ` 6 GHz ("6GHz") is a separate NM value and is not offered here.`
- **D2 — CAKE copy (ST0-022).** Exact new `explanation` in `src/index.tsx`:
  `Replaces the egress qdisc on this device with CAKE "unlimited diffserv4 nat ack-filter" (no bandwidth limit set). It only orders packets leaving this device; it cannot control other devices, the access point, or the ISP bottleneck, and any effect needs measurement under load.` + the existing
  reboot/auto-fix sentence unchanged. Exact new `README.md` table row:
  `| Traffic shaping (CAKE) | Local egress qdisc ("cake unlimited ...", no bandwidth limit set). No control over other devices or external bottleneck. | Replaces your system's default qdisc; resets on reboot |`
  Also update the now-stale `README.md` sentences about the inherited 6 GHz
  claim (the two notes near the feature table) to past tense / remove them —
  same commit, no new claims.
- **D3 — toolchain triage (ST0-023).** Reproduce with `pnpm audit --json || true`
  (baseline 2026-10-15: 13 entries / 7 GHSAs across `brace-expansion@1.1.14/2.1.0`,
  `braces@3.0.3` via `@decky/rollup` → `rollup-plugin-delete`/`@rollup/plugin-commonjs`;
  record dated counts against this baseline — audit is registry-dependent and not
  a CI gate). Attempt order: (1) direct range bumps in `package.json` (`^` only,
  no `*`); (2) targeted update restricted to the `brace-expansion`/`braces` chain
  (never bare `pnpm update` / `--depth Infinity`, which would churn
  `react-icons`/`tslib`/`rollup`); (3) `pnpm.overrides` only with per-package
  justification, never breaking semver/build — and never deleting
  `pnpm.peerDependencyRules.ignoreMissing: [react, react-dom]`. One-time lockfile
  regen (`--no-frozen-lockfile`); `git diff pnpm-lock.yaml` must show intended
  bumps only. Residual = still-listed GHSA after 1–3 without breaking semver/build:
  stop forcing, document in the commit body + findings ST0-023. Commit
  `package.json` + `pnpm-lock.yaml` (+ rebuilt `dist/` iff the build output
  changed). Verification gate (all green): frozen install → build →
  `tsc --skipLibCheck` → `unittest` → `check-syntax` → `verify-dist`.

## Acceptance

- Band row: the band `InfoRow` block has no `6 GHz` in label/subtitle (scoped grep
  on that block); explanation names `"a"` and the un-offered `"6GHz"`;
  `StatsGrid` frequency readouts are observation, out of scope; no new enum
  reaches `nmcli` (whitelist unchanged).
- CAKE row + README: no device-starvation claim (grep for `another device`);
  unlimited described as no-limit-set, scope local.
- Audit: zero matching advisories, or a documented residual list; lockfile
  reproducible (`--frozen-lockfile` green); build/types/tests/syntax/dist-verify
  green with no unrelated diff.
