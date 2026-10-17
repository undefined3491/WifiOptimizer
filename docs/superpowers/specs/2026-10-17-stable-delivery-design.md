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
  `update_channel` enum narrowed but old `"beta"` values recorded raw with a
  migration note (never silently dropped while the field installation exists).
  KEEP: ex-beta version rule (`"-beta" in current` comparison) until the known
  beta-channel field installation migrates; `tests/test_delivery.py` beta
  asserts (they are stable-guards); `install.sh` (already Stable/main-fallback
  only). `scripts/check_delivery.py` updater guards + `SyntaxTests` are REWRITTEN
  to the new contract (no fixed `/tmp` script path, no detached `Popen` for
  copying, checked curl results, per-file `os.replace` commit, no live-dir
  unlink) — the old f-string/script-shape assertions are replaced, not kept
  (rewrite happens in Task 3; Task 2 keeps them green since beta removal does
  not change the updater shape).
- **D2 — single update job + cross-exclusion.** In-memory `_update_job`
  `{in_progress, phase, target, started_at, result}` reserved before the first
  await (backend-switch reservation pattern). Phase enum (exact vocabulary):
  `idle | resolving | downloading | validating | committing | restart_requested | failed | done_unknown`.
  Start rejects with `{accepted: False, reason: "in_progress"}` when busy,
  `"switch_in_progress"` when the backend switch runs — and `start_backend_switch`
  symmetrically rejects on `update_in_progress` (touches the ST0-010 reservation
  site; reservation tests re-run). Rejection restores previous state; no
  transient fields leak. Job progress is observable via a read-only
  `update_job` summary inside `get_status` (observation only — no writes, no new
  IPC method, ST0-005/006 read-only rule kept).
- **D3 — staging without a missing-dir window.** Stage dir is a sibling of the
  live plugin dir on the same filesystem (`stat -c %d` equality gate, else
  `stage_failed`), private name, `0700`. Per-job private script path (never the
  fixed `/tmp/wifi-optimizer-update.sh`). The live directory is never removed
  or renamed; commit is per-file `os.replace` in fixed order (non-version files
  first, version-bearing `package.json` + `plugin.json` LAST together):
  `defaults/dispatcher.sh.tmpl → decky.pyi → dist/index.js → dist/index.js.map → main.py → package.json → plugin.json`
  + `py_modules/.keep` touch + one directory `fsync`. A mid-loop failure →
  `commit_failed:{file}` + detail, restart WITHHELD, partial counts reported,
  stage RETAINED for retry. Boot re-offer rule: `_main` verifies the shipped
  allowlist exists; any missing file forces `check_for_update` to report
  `update_available: True` (version-compare OR missing-file), so a
  crash-during-commit can never strand a mixed tree without a re-offer.
- **D4 — validated transfer and identity.** `curl -fsSL --proto =https --connect-timeout 5 --max-time 60 --max-filesize 50M --retry 0` via `_run_cmd(clean_env=True)`; `--fail` mandatory. Failures → `download_failed` + stderr, stage removed, live untouched. Identity before first live write: single expected root (`wifi-optimizer-tms-{ver}`), no absolute/`..`/dup/link/device entries, allowlist copy only (7 files), `plugin.json` name+root+api, `package.json` name+`version==target`, `dist/*` present non-empty with parseable map. Failures → `archive_invalid`/`identity_mismatch`, stop, live untouched, stage removed.
- **D5 — truthful restart + health.** Exactly one `systemctl restart plugin_loader` after a successful commit (in-worker, `clean_env`). Report split triple: `file_commit {committed, version, channel: "stable", files: N/N}`, `restart {requested, rc, stderr}`, `health: "load_unconfirmed"`; confirmation only via next boot's `check_for_update` + `get_status.version`. Legacy `{success: True, "Updating..."}` immediate shape is replaced by the accepted/start shape (only intentional breaking change, required by truthfulness). UI 60 s timeout means `unknown`, never success. Error codes: `resolve_failed`, `download_failed`, `archive_invalid`, `identity_mismatch`, `stage_failed`, `commit_failed`, `restart_failed` in additive `errors[]`.
- **D6 — install.sh rescue.** Same staging/validation/commit rules: sibling stage dir under the plugin base (`mktemp -d "$PLUGIN_BASE/.wifi-otp-stage.XXXXXX"`, never bare `/tmp` — different fs degrades rename to copy) + dev gate, `curl -fsSL --proto =https --connect-timeout 5 --max-time 120 --fail`, identity checks before first write, NO `rm -rf` of live (fresh install with live absent: single `mv -n` stage→live; upgrade: validated per-file `mv` renames, which are atomic on the same fs — never truncating `cp`; `rm -rf` only ever touches the stage dir), truthful stdout (`FILE_COMMIT`, `RESTART_RC`, `NEXT_HEALTH`) + non-zero exit on any failure. `main`-fallback kept but explicitly labeled `UNRELEASED-FALLBACK` in log (or flag-gated).
- **D7 — frontend exclusion.** `Update Now` disabled while `backendSwitch.in_progress || isBusy`; backend toggle disabled while `updating`; `setBusy(true)` on accepted start; terminal/fail/timeout paths clear busy only after forced `refreshStatus(true)`. Heartbeat/dedupe/timeout/retry-on-reconnect stay (Stable API pressure + hang protection, not Beta-specific). No new global gate.
- **D8 — docs.** Decision-doc status amendment (A1 deferred, custom retained+hardened, Beta dropped, Store after 0+1+2); findings handoff item 2 rewritten; ROADMAP Stable-only + Store-after-0+1+2 note; AGENTS.md/CONTRIBUTING.md/README.md/branding beta lines removed or rewritten Stable-only; recovery/identity specs' beta points cut; Beta-identity finding marked MOOT; inventory `"beta"` line annotated, not altered.

## Acceptance

- Two concurrent update starts → second `{accepted: False, reason: "in_progress"}`; update-during-switch (and reverse) → cross rejection.
- Corrupt tarball / wrong name/version / symlink traversal → live `main.py`+`dist` byte-identical, named `errors[0]`, stage removed.
- Live plugin dir exists through the whole upgrade (no unlink/rename of it in any step).
- Curl timeout/404 → `download_failed`, no loader restart.
- Successful commit → exactly one restart request; result carries the triple, never bare installed+loaded.
