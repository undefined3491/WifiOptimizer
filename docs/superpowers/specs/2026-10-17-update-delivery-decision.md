# Update delivery decision: native Decky ZIP (A1) vs custom updater (A2)

Date: 2026-10-17. Baseline: `ff10680`. Status: **recommended A1, awaiting owner sign-off.**
Scope: ST0-001/002/003/018 follow-up; recovery spec stays conditional until this decision.

## Evidence

- Native Decky update = `uninstall_plugin()` + `_unzip_to_plugin_dir()` + `import_plugin()` (Decky `browser.py`): no staging, no backup, no `plugin_loader` restart for plugins. Settings/data/logs outside the plugin dir survive replace AND uninstall by platform design. `_uninstall()` in the plugin is the only cleanup hook for files outside the plugin dir.
- Our in-app updater (`apply_update()`, fixed script path, unchecked curl/tar/cp, in-place copy, 60 s UI timeout not killing the worker) and `install.sh` (`rm -rf` before replacement) cannot be made safe cheaply; the recovery spec's transaction engine is unbuilt and conditional.
- Hard blocker for EITHER route: today's `_uninstall()` deletes snapshot + settings + dispatcher + confs and clears owned profiles, so a native replace starts the new version with no baseline and `_main` immediately re-applies volatile state — destructive either way. Fix first, independent of A1/A2. (`_uninstall` is the only hook *in the plugin process*; the second out-of-Decky hook is dispatcher self-removal on `up` when the plugin dir is gone.)

## Recommendation: A1 (native Decky ZIP)

Rationale: no parallel writer, no detached scripts, no version-authority skew, Store review + counters for free; custom engine cost unjustified for this plugin's size.

## Prerequisites (required before any update flows through either path)

- **P0 — update-safe `_uninstall()`.** Uninstall = full system restoration as implemented (except backend-service states, which are never restored by design — ST0-009) + removal of plugin-owned system files + dispatcher; but PRESERVE the settings dir contents (`settings.json`, `system_snapshot.json`, plus `last_enforced`/`diagnostics.json` when present), Decky-consistent (Decky never deletes `settings/`). Rationale: after a replace, the new version starts from a restored system and snapshots fresh state; nothing depends on distinguishing replace from true uninstall (Decky sends the same signal). Amends the current settings-file deletion; owner sign-off covers the "settings survive uninstall" change.
- **P1 — retire the in-app updater.** Remove `apply_update()` writer path, `check_for_update()` vs GitHub, `update_channel` + `set_update_channel`, `UpdatesSection`/heartbeat/timeout UI (replace with a Store pointer or nothing — no second channel beside the Store).
- **P2 — `install.sh` as rescue/bootstrap only (rescue-only discipline).** Staging, archive identity validation, recoverable switch, explicit recovery notes including disclosure of the `main`-branch fallback; never a parallel writer next to the Store. Needed to recover a machine if the Store path ever fails. Residual risk accepted: with no mechanical lock under A1, a simultaneous Store update + manual `install.sh` run can still interleave — procedural discipline only, documented here, not guaranteed.
- **P3 — dispatcher/replace verification.** `_uninstall` removes the dispatcher script before Decky's `rmtree`; the missing-dir self-removal race is closed ONLY when `_uninstall` runs to completion (Decky terminates the plugin process on uninstall; if the handler is killed or the process is already dead, `rmtree` proceeds anyway — exact kill timing to be verified on the candidate). Required: preflight check for an orphaned dispatcher on the candidate, plus handling of the killed-handler path (documented, not silent); verify on candidate that a Store-style replace leaves no orphaned/mixed state.
- **P4 — Store submission.** Fork `decky-plugin-database`, submodule, LICENSE, version bump per release, review. Beta channel via Store testing feed or dropped (owner call — moving beta branch has no Store equivalent).

## Explicitly out

Service-state restoration, backend effective-state changes (done in ST0-009), Watchdog, version bump now. Custom transaction engine (recovery spec) is NOT built under A1; the spec stays a reference. Decky's own `rmtree`→`extractall` window has no atomicity on the Store path — accepted residual risk (no staging possible from inside the plugin).

## First transition (before any Store update)

The first hop must NOT go through the Store: the on-device old `_uninstall` is still destructive and would wipe settings+snapshot. First transition via the corrected `install.sh`-rescue with an explicit backup of the settings dir; expectation set with the owner beforehand (what is preserved, what is re-baselined).

## Owner sign-off needed

1. A1 over A2 (custom engine not built; recovery spec stays a reference).
2. Settings/snapshot survive uninstall (P0 behavior change; file list above).
3. Beta channel fate: Store testing feed vs drop.
4. Store listing under the TMS name (public fork history, license, review).
5. First-transition method (rescue-with-backup, not Store) and its expectations.
6. Candidate validation gate before Stable: smoke test with reconnect + sleep/wake for networking changes (per delivery policy), plus observed Store-replace behavior.

After sign-off: implementation package (P0–P3 + submission prep), then candidate validation, then Stable.
