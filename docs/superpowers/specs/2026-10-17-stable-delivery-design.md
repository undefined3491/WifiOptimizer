# Stable-only hardened delivery (keep custom updater, drop Beta) — design

Date: 2026-10-17. Baseline: `0c6997a`. Supersedes the A1 direction of
`docs/superpowers/specs/2026-10-17-update-delivery-decision.md` (A1 DEFERRED by
owner 2026-10-17: early release, single user; custom updater RETAINED +
hardened; Beta DROPPED; Store after Stage 0+1+2 — that doc gets a status
amendment, not a rewrite).
Scope: findings ST0-001, ST0-002, ST0-003, ST0-018 (delivery half of handoff
item 2, rewritten). Stage 0 stays open; no Stable, no version bump, no Watchdog.

## Intent

- The retained in-app Stable updater cannot mix versions, strand jobs, or lie
  about restarts: staged payload, validated identity, one job with exclusion,
  truthful file-commit/restart/health reporting.
- No Beta channel exists anywhere: no branch, no `update_channel` Beta value,
  no moving-branch downloads, no beta UI. Stored `"beta"` migrates to Stable
  automatically (unknown keys are stripped on settings merge).
- `install.sh` is rescue/bootstrap only, never a parallel writer.

## Non-goals / anti-goals

- No transaction engine (no `renameat2`/exchange, `systemd-run`, journal,
  lock-files, `active.json`); no durable delivery state. Crash-before-commit =
  live untouched; crash-during-commit = restart withheld + partial report + retry.
- No Store work, no testing feed, no pre-release assets.
- No backend service-state restoration, no NM/profile changes in the updater.

## Decisions (binding)

- **D1 — Beta dropped.** Remove: `update_channel` Beta value + branch-download
  logic (`check_for_update`/`apply_update` always Stable: `releases/latest` →
  `tag vX.Y.Z` → tag-tarball), `set_update_channel()` + `DEFAULT_SETTINGS` key
  (frontend first, then backend; old stored `"beta"` stripped automatically),
  channel dropdown/handler/wrapper + `types.ts` channel fields, collector
  `update_channel` enum narrowed with read-tolerance for old `"beta"`.
  KEEP: ex-beta version rule (`"-beta" in current` comparison) until the known
  beta-channel field installation migrates; `tests/test_delivery.py` beta
  asserts (they are stable-guards); `install.sh` (already Stable/main-fallback
  only); full `SyntaxTests`/`check_delivery.py` updater guards.
- **D2 — single update job + cross-exclusion.** In-memory `_update_job`
  `{in_progress, phase, target, started_at, result}` reserved before the first
  await (backend-switch reservation pattern). Start rejects with
  `{accepted: False, reason: "in_progress"}` when busy, `"switch_in_progress"`
  when the backend switch runs — and `start_backend_switch` symmetrically
  rejects on `update_in_progress`. Rejection restores previous state; no
  transient fields leak.
- **D3 — staging without a missing-dir window.** Stage dir is a sibling of the
  live plugin dir on the same filesystem (`stat -c %d` equality gate, else
  `stage_failed`), private name, `0700`. Per-job private script path (never the
  fixed `/tmp/wifi-optimizer-update.sh`). The live directory is never removed
  or renamed; commit is per-file `os.replace` in fixed order
  (`dispatcher.sh.tmpl → decky.pyi → package.json → dist/* → main.py → plugin.json`)
  + `py_modules/.keep` touch + one directory `fsync`. A mid-loop failure →
  `commit_failed:{file}` + detail, restart WITHHELD, partial counts reported.
- **D4 — validated transfer and identity.** `curl -fsSL --proto =https --connect-timeout 5 --max-time 60 --retry 0` via `_run_cmd(clean_env=True)`; `--fail` mandatory. Failures → `download_failed` + stderr, stage removed, live untouched. Identity before first live write: single expected root (`wifi-optimizer-tms-{ver}`), no absolute/`..`/dup/link/device entries, allowlist copy only (7 files), `plugin.json` name+root+api, `package.json` name+`version==target`, `dist/*` present non-empty with parseable map. Failures → `archive_invalid`/`identity_mismatch`, stop, live untouched, stage removed.
- **D5 — truthful restart + health.** Exactly one `systemctl restart plugin_loader` after a successful commit (in-worker, `clean_env`). Report split triple: `file_commit {committed, version, channel: "stable", files: N/N}`, `restart {requested, rc, stderr}`, `health: "load_unconfirmed"`; confirmation only via next boot's `check_for_update` + `get_status.version`. Legacy `{success: True, "Updating..."}` immediate shape is replaced by the accepted/start shape (only intentional breaking change, required by truthfulness). UI 60 s timeout means `unknown`, never success. Error codes: `resolve_failed`, `download_failed`, `archive_invalid`, `identity_mismatch`, `stage_failed`, `commit_failed`, `restart_failed` in additive `errors[]`.
- **D6 — install.sh rescue.** Same staging/validation/commit rules: sibling stage dir + dev gate, `curl -fsSL --proto =https --connect-timeout 5 --max-time 120 --fail`, identity checks before first write, NO `rm -rf` of live (fresh install: single `mv -n` stage→live; upgrade: validated per-file copy), truthful stdout (`FILE_COMMIT`, `RESTART_RC`, `NEXT_HEALTH`) + non-zero exit on any failure. `main`-fallback kept but explicitly labeled `UNRELEASED-FALLBACK` in log (or flag-gated).
- **D7 — frontend exclusion.** `Update Now` disabled while `backendSwitch.in_progress || isBusy`; backend toggle disabled while `updating`; `setBusy(true)` on accepted start; terminal/fail/timeout paths clear busy only after forced `refreshStatus(true)`. Heartbeat/dedupe/timeout/retry-on-reconnect stay (Stable API pressure + hang protection, not Beta-specific). No new global gate.
- **D8 — docs.** Decision-doc status amendment (A1 deferred, custom retained+hardened, Beta dropped, Store after 0+1+2); findings handoff item 2 rewritten; ROADMAP Stable-only + Store-after-0+1+2 note; AGENTS.md/CONTRIBUTING.md/README.md/branding beta lines removed or rewritten Stable-only; recovery/identity specs' beta points cut; Beta-identity finding marked MOOT; inventory `"beta"` line annotated, not altered.

## Acceptance

- Two concurrent update starts → second `{accepted: False, reason: "in_progress"}`; update-during-switch (and reverse) → cross rejection.
- Corrupt tarball / wrong name/version / symlink traversal → live `main.py`+`dist` byte-identical, named `errors[0]`, stage removed.
- Live plugin dir exists through the whole upgrade (no unlink/rename of it in any step).
- Curl timeout/404 → `download_failed`, no loader restart.
- Successful commit → exactly one restart request; result carries the triple, never bare installed+loaded.
