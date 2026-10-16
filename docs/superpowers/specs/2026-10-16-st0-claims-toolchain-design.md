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

- **D1 — band label (ST0-021).** `src/index.tsx` band `InfoRow`: static label
  `"Force 5 GHz band"` (drop the `supports6GHz` conditional); subtitle names the
  NM value (`Lock this profile to 5 GHz (NM band "a")`); explanation states
  `"a"` means 5 GHz only — no 2.4 GHz, no 6 GHz — with the 2.4-GHz-only warning
  kept, and notes `6GHz` is a separate NM value not offered here. The
  `supports_6ghz` field, backend whitelist (`a`/`bg`), and `s?.band_preference`
  plumbing stay untouched.
- **D2 — CAKE copy (ST0-022).** `src/index.tsx` CAKE `explanation`: local egress
  queue only (`cake unlimited diffserv4 nat ack-filter`, no bandwidth limit
  set); cannot control other devices, the AP, or the ISP bottleneck; effect
  needs measurement under load; reboot/reset semantics kept. `README.md`
  feature-table CAKE row rewritten the same way (one row, no new claims).
- **D3 — toolchain triage (ST0-023).** Reproduce with `pnpm audit --json`
  (baseline: 13 entries / 7 GHSAs across `brace-expansion@1.1.14/2.1.0`,
  `braces@3.0.3` via `@decky/rollup` → `rollup-plugin-delete`/`@rollup/plugin-commonjs`).
  Attempt order: (1) direct range bumps in `package.json` (`^` only, no `*`);
  (2) targeted `pnpm update` of the transitive chain within semver; (3) `pnpm.overrides`
  only if 1–2 leave advisories. One-time lockfile regen (`--no-frozen-lockfile`),
  review the lock diff for intended bumps only, commit `package.json` +
  `pnpm-lock.yaml` (+ rebuilt `dist/` if the build output changes), then frozen
  installs only. Verification chain: audit → `install --frozen-lockfile` →
  `build` → `tsc --skipLibCheck` → `unittest` → `check-syntax` → `verify-dist`
  (same steps CI runs). Document any residual advisories with justification
  instead of forcing them clean.

## Acceptance

- Band row: no `6 GHz` string in label/subtitle (grep); explanation names `"a"`
  and the un-offered `"6GHz"`; no new enum reaches `nmcli` (whitelist unchanged).
- CAKE row + README: no device-starvation claim (grep for `another device`);
  unlimited described as no-limit-set, scope local.
- Audit: zero matching advisories, or a documented residual list; lockfile
  reproducible (`--frozen-lockfile` green); build/types/tests/syntax/dist-verify
  green with no unrelated diff.
