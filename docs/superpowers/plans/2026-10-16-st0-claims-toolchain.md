# ST0-021/022/023 claims + toolchain Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Truthful band/CAKE copy and a triaged, reproducible toolchain (ST0-021/022/023).

**Architecture:** Copy-only frontend edits (band label, CAKE explanation, README row) verified by grep + typecheck + build + review; dependency update attempted in order (direct bumps → targeted update → overrides last resort) with a one-time lockfile regen and the full CI verification chain.

**Tech Stack:** React TS `src/`, `package.json` + `pnpm-lock.yaml` (pnpm v9, lockfile v9), Git Bash on PATH.

**Spec:** `docs/superpowers/specs/2026-10-16-st0-claims-toolchain-design.md`

## Global Constraints

- No backend changes; no new NM enums sent; backend band whitelist untouched.
- No `pnpm audit --fix`, no hand-edited lockfile, no `*` ranges, no dependency changes for the known `react-router` TS2307; `pnpm.peerDependencyRules.ignoreMissing: [react, react-dom]` stays.
- `tsconfig.json` strict + `noUnusedLocals/Parameters`; pnpm v9 only (`npm exec --yes --package=pnpm@9` wrapper); lockfile work ends with `--frozen-lockfile` green.
- Copy and toolchain changes in separate commits, never mixed.
- No version bump, no Stable/beta, no Watchdog, no other findings.

## Review Focus

- No `6 GHz` promise in the band row — expect grep-clean label/subtitle with `"a"`/`"6GHz"` named in explanation.
- No starvation claim for CAKE — expect local-scope wording in UI and README.
- No speculative override — expect attempt order 1→2→3 with evidence at each step and residuals documented, not forced.

---

### Task 1: Copy fixes (D1/D2)

**Files:**
- Modify: `src/index.tsx` (band `InfoRow`, CAKE `explanation`), `README.md` (CAKE table row)
- Test: grep + typecheck + build + review checklist (no frontend unit infra)

- [ ] **Step 1: Implement** exact texts per D1/D2 (keep 2.4-GHz-only warning, reboot/reset semantics sentences).
- [ ] **Step 2: Verify** grep: no `6 GHz` in band label/subtitle; no `another device` in CAKE copy/README. `tsc --noEmit --skipLibCheck` exit 0. `pnpm run build` exit 0 (pnpm v9, frozen lockfile). Read the render checklist: label/subtitle/explanation/badge props intact.
- [ ] **Step 3: Commit** `git add src/index.tsx README.md dist/index.js dist/index.js.map; git commit -m "fix: truthful band and CAKE copy (ST0-021/022)"` (include rebuilt `dist` only if the build output changed).

### Task 2: Toolchain triage (D3)

**Files:**
- Modify: `package.json`, `pnpm-lock.yaml` (+ `dist/` only if build output changes)
- Test: full verification chain below

- [ ] **Step 1: Reproduce** `npm exec --yes --package=pnpm@9 -- pnpm audit --json`; record baseline counts. `pnpm install --frozen-lockfile` green first (proves clean baseline).
- [ ] **Step 2: Attempt (1) direct bumps** (`^` ranges only); one-time regen; inspect `git diff pnpm-lock.yaml` for intended-only bumps.
- [ ] **Step 3: If residuals, attempt (2) targeted update** of the transitive chain within semver; re-inspect lock diff.
- [ ] **Step 4: If residuals, decide (3) overrides** — only with explicit justification per package; otherwise document residuals and stop forcing.
- [ ] **Step 5: Verify chain** audit → frozen install → build → `tsc --skipLibCheck` → `python -m unittest discover -s tests` → `check-syntax` → `verify-dist` (snapshot/compare via `scripts/check_delivery.py`). All green.
- [ ] **Step 6: Commit** `git add package.json pnpm-lock.yaml [dist]; git commit -m "chore: triage build-tool advisories (ST0-023)"` (dist only if output changed; residuals documented in the commit message body).

### Task 3: Docs state update (no product behavior change)

**Files:**
- Modify: `docs/audits/2026-10-15-stage-0-findings.md` (ST0-021/022/023 evidence)
- Test: none (docs only)

- [ ] **Step 1: Update findings** correction evidence for the three findings; remaining findings stay open; Stage 0 stays open.
- [ ] **Step 2: Verify** via `git log --stat` (post-commit diff is empty by design).
- [ ] **Step 3: Commit** `git add docs/...; git commit -m "docs: ST0-021/022/023 correction evidence"`
