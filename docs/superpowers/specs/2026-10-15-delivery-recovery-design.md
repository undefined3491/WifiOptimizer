# Stage 0: recoverable installation and updates

Date: 2026-10-15. Product baseline: `7e3d45f60504aa53b17155136535006b7bf1e634`; runtime findings refer to audited `e957c5b`.

**Status: Proposed for owner review.** Preparation and a separate read-only inventory tool are authorized. The deployment engine, runtime changes, GitHub rename, device installation and publication described here are not implemented. This specification does not close any audit finding.

## Outcome and scope

Correct ST0-001/002/003/018: downloading or copying a bad update must not destroy the existing installation, competing updates must not overlap, and service failure must not be presented as successful installation. Include the narrowly necessary operation reservation from ST0-010 and update-specific error/status handling. Do not claim full backend-switch, settings-restoration or networking correctness from this package.

The owner selected `WiFi Optimizer TMS` and repository/package `wifi-optimizer-tms`. Follow the [identity design](2026-10-15-tms-identity-design.md): retain the installation directory `WiFi Optimizer`, settings/data/log paths and existing dispatcher/system-config filenames. Coordinate public identity, URLs, packaging and the later GitHub cutover. Keep version `0.11.6` until release preparation; all remaining first-Stable audit/device gates still apply.

## Selected architecture

Use a standalone standard-library Python recovery engine shared by manual installation and in-app updates. Keep Decky adapters small; never import `main.py` to run the engine. Replace the generated `/tmp` shell script and in-place copying. Execute a private snapshot of the engine in an independent transient **system** service, outside the `plugin_loader` cgroup and installation tree. `Popen(start_new_session=True)` alone is insufficient lifecycle isolation.

| Component | Responsibility |
| --- | --- |
| `delivery/recovery.py` | Resolve/download, stage, inspect, deploy, reconcile, explicitly restore files and expose status through a CLI |
| `delivery/manifest.py` | Pure identity, payload, archive and request/journal validation shared with delivery checks |
| `delivery/linux.py` | Bounded Linux directory-descriptor, lock, service and exchange adapters; no architecture-specific syscall numbers |
| `install.sh` | Root/prerequisite/bootstrap adapter to a pinned engine; report job identity and recovery instructions |
| `main.py` | Operation reservation, candidate/job IPC, read-only delivery status, early startup recovery guard and load acknowledgement |
| `src/backend.ts`, types and update UI | Accepted-job versus completed-job contracts, nonoverlapping polling, explicit unknown/failure/recovery states |
| Delivery checks and tests | New payload files, pure validation fixtures and isolated Linux service/filesystem failure tests |

The read-only inventory tool is independent of this engine and never deploys or invokes plugin IPC. It provides observations, not a backup capable of restoring all network state.

## Storage, authority and prerequisites

Proposed durable control root: `/var/lib/wifi-optimizer-tms-delivery`, containing a persistent `operation.lock`, atomic `active.json`, and private `jobs/<random-id>/` directories with request, versioned journal, snapshotted engine, archive, payload manifest and diagnostics. Root ownership; directories `0700`, private files `0600`. Never unlink the operation lock to clear a stale job. Refuse existing symlinks, unsafe ownership/modes or malformed state rather than recursively repairing an unknown tree.

Before target-device deployment, verify that the control root is writable and survives the supported SteamOS reboot/update lifecycle. An unavailable/unsuitable control root is a failed prerequisite; there is no `/tmp` or user-settings fallback. Read-only inventory cannot establish writable persistence by itself.

Stage payload and retain previous files under `<validated-decky-home>/.wifi-optimizer-tms-delivery/<job-id>/`, outside the `plugins` directory scanned by Decky. Require the stage and live installation to be on the same mounted local filesystem; reject mountpoints, nested mounts and ancestor/descendant layouts that invalidate the exchange contract. Check capacity before download/staging, while still handling later ENOSPC errors.

Use opened parent directory descriptors, no-follow operations, relative single-component names and directory-identity rechecks at mutation boundaries. Root-owned leaves beneath user-writable ancestors do not create a secure multi-user boundary. Document that limitation; do not infer safety from `realpath()` followed by an ordinary path write.

User-writable settings supply only validated intent such as channel. They cannot choose executable/engine path, installation or rollback path, service name, arbitrary URL, candidate provenance or executable journal instructions. Derive installation paths from validated runtime context. Scope first-device support to the owner's captured LCD / SteamOS Stable setup; no silent generic fallback when prerequisites fail.

## Candidate resolution and payload validation

Resolve each submitted candidate once to a full commit SHA. Persist repository identity, channel, release/tag identity where applicable, package version, commit SHA, archive digest and payload hashes. The digest identifies observed bytes; it is not an independent authenticity signature. Initial bootstrap trust remains the explicitly selected fork and HTTPS.

- Stable: latest published Stable release, exact valid `vX.Y.Z` tag resolved to a commit, matching package version `X.Y.Z`. Missing release is an explicit no-release/error result; no in-app fallback to main.
- Beta: resolve the existing `beta` branch to a commit, then read metadata and download from that same commit. Preserve version-based update availability; same-version republishing is outside this change.
- Manual installer: preserve the disclosed latest-release lookup fallback to main, clearly labeled unreleased fallback, and pin main to a commit. Once a release/candidate is selected, archive or staging failure cannot silently select a different source.
- Do not substitute upstream. Before cutover use the current fork identity; the coordinated branding PR changes the exact canonical identity to `undefined3491/wifi-optimizer-tms`.

Download an archive of the resolved commit, not a moving branch/tag. Runtime SHA archives have a root based on the repository slug and commit SHA; release-validator fixtures for the existing tag/version source archive have a different root contract. Validate each format explicitly rather than globally replacing one assumed root string. HTTP errors, non-HTTPS redirects, connection/total deadlines, archive/download size and member/expanded-size limits are enforced before commit. Use argument arrays and a clean environment; metadata is never interpolated into shell code.

Validate every archive entry before extracting: one expected root, no absolute/traversing/ambiguous paths, duplicates, links, devices or FIFOs. Copy only the known payload allowlist into a new private stage with checked operations. Require manifests, backend, type stub, both tracked dist files, dispatcher template and the new engine files. Validate names/version schemas, nonempty required files, hashes and expected frontend identity where statically checkable. Create `py_modules/.keep`; normalize safe ownership/modes rather than preserving archive privileges. Do not execute plugin payload code to validate it. The explicitly trusted bootstrap engine is distinct from executing a downloaded plugin lifecycle.

Inspect manifests for legacy/TMS duplicate installations before staging and immediately before deployment. Conflicts stop the job with paths and recovery instructions; do not merge settings or delete another optimizer. The old updater is not retroactively corrected by a repository rename: document the first transition using the corrected manual installer.

## Operation reservation and independent worker

Use both cross-process `flock` and a root-controlled durable reservation. The IPC adapter reserves before its first `await`; each entrant checks the reservation even when the lock is temporarily free during worker handoff. The worker verifies its matching job reservation and holds the lock through terminal processing. Launch failure/timeout is reconciled against that exact service/job; uncertainty never clears the reservation or authorizes a second writer.

Launch a fixed, private engine path through `/usr/bin/systemd-run` as a system service with a random validated unit name, `Type=exec`, `Restart=no`, `UMask=0077`, explicit clean environment and bounded runtime. Disable systemd argument environment expansion where supported, or use correctly escaped fixed arguments verified on the installed systemd version. A launch acknowledgement means accepted, not installed. Verify the required properties/capabilities on the target; do not silently use a weaker worker mechanism.

All plugin entry points that can mutate state must respect the operation gate: setters, reset, optimize/reapply, backend switching, startup and the currently mutating `get_status()`. Dedicated delivery status must be read-only and usable in recovery mode. Reservation for backend switching moves before its current initial await; full backend effectiveness/rollback remains separate work. Do not release exclusion merely because an awaiting `to_thread()` task was cancelled while its underlying subprocess may still be running.

An old installed version lacks this gate. The first manual transition therefore requires no switch/update in progress, a checked Decky stop before replacement, and observation that old loader-owned workers have ended. If quiescence cannot be established, stop before changing files. Cooperating new callers are serialized; external installers and NetworkManager events are outside the gate.

## Replacement without a missing-directory window

The existing dispatcher self-removes and deletes plugin configuration when the live directory is absent. Stopping Decky does not stop NetworkManager dispatchers. Consequently, **two renames (old out, new in) are forbidden** for an existing installation.

Require Linux `renameat2(RENAME_EXCHANGE)` for an existing installation, using a small libc adapter with declared types and errno handling. Before touching live state, probe support using private fixtures on the actual mounted filesystem. Missing entry point, unsupported operation, cross-mount layout or failed probe leaves the installation unchanged. There is no copy-in-place or two-rename fallback. A successful probe does not excuse handling failure of the actual exchange.

1. Fully stage/validate candidate and record identities of both directory trees and installed payloads.
2. Stop `plugin_loader` and verify the required inactive/quiescent state; record command intent/outcome. Preserve its pre-job active state.
3. Flush `exchange_intent` with both directory and payload identities; recheck live/stage parents and duplicates.
4. Exchange stage and live names in one checked call. Verify live is the candidate and the stage name now contains the prior installation. Retain the latter in place as the backup.
5. Flush affected directories and record `files_committed`. This gives atomic namespace visibility, not crash-proof transaction durability.
6. If Decky was active, record one checked start intent/request and its outcome; if it was intentionally inactive, leave it inactive and report installed/load-unconfirmed. Never silently enable the service.

A fresh install uses a single no-replace rename; a target created concurrently causes refusal. A pre-existing orphan dispatcher is separately reported during preflight. Exchange removes this deployment's missing-path window; it neither pauses an already-running dispatcher nor rolls back its network effects.

## Journal, acknowledgement and recovery

Use atomic-replace, flushed, schema-validated journals with monotonically increasing revision. Record intent before namespace/service mutation. Track file phase, service outcome and candidate-load observation separately:

`reserved → staging → validated → stop_requested → loader_stopped → exchange_intent → files_committed → start_requested → service_started → candidate_loaded`.

Terminal outcomes include `failed_unchanged`, `restored`, `installed_inactive`, `service_start_failed`, `load_unconfirmed` and `needs_recovery`. `needs_recovery` and unresolved outcomes keep the reservation; reaching a UI or worker deadline does not delete backups. A service start alone is not plugin-load confirmation.

Candidate startup first inspects recovery state before settings writes, dispatcher installation or volatile application. It may write one exclusive, no-follow acknowledgement file under the matching private job directory containing job/candidate and process/boot identity. It must not acquire the worker-held operation lock to acknowledge. The worker validates the acknowledgement and observed payload, finalizes durable state and clears the reservation. Startup can then acquire the ordinary gate and revalidate readiness before normal lifecycle work. Missing/uncertain finalization leaves startup in recovery mode, without an indefinite lock wait or automatic network changes.

After interruption, a read-only reconciler compares journal, exact unit/job state, directory identities and payload hashes. It does not trust a phase label or PID alone. Ambiguous/corrupt/conflicting evidence blocks new mutations as `needs_recovery`. Never automatically replay an uncertain service start, exchange or networking command at boot.

Automatic inverse exchange is allowed only while Decky is confirmed stopped, no candidate-start request was issued, and both trees match recorded identities; journal intent first. After any uncertain start request, restoration is an explicit file-only operation with the same gate, validation and checked stop/exchange. It cannot restore settings, profile changes or lifecycle/dispatcher effects. Provide CLI inspection, explicit validated file recovery/restore and a separately requested service start. Preserve evidence and previous files until explicit cleanup; the first implementation does not automatically prune retained backups.

## UI and IPC contract

Return an accepted job identifier and candidate identifier with a typed reason for refusal. Expose a dedicated read-only delivery-status method with phase/revision, stale/unknown indicators and separate installed/service/load outcomes. A 60-second UI timeout or lost IPC connection means unknown status, never success or permission to retry. Reconcile on reopen/remount; polling must not overlap. Keep conflicting controls unavailable while a job is active or unresolved. Show actionable recovery instructions and acknowledge failure responses rather than dropping them.

## Acceptance and implementation order

1. Pure identity/archive/journal validation fixtures, then isolated Linux filesystem adapter and injected copy/flush/exchange failures.
2. Independent service worker and durable reservation/reconciliation, then installer bootstrap; failure must preserve prior files and truthful status.
3. Backend gate/early lifecycle acknowledgement and update IPC/UI integration, then branding/packaging and coordinated GitHub cutover under the identity design.
4. Reviewed candidate-specific LCD / Stable inventory, recovery preparation, installation/update and reconnect/sleep-wake evidence. Publish separately only after remaining Stage 0 gates close.

Required tests cover wrong/missing payload, HTTP failures, ENOSPC, traversal/links/FIFOs, unsafe ancestors, permission errors, unsupported exchange without live mutation, repeated/same-candidate installation, conflicting copies, competing installer/update/switch calls, reservation handoff/cancellation, and termination before/after each journal/exchange/service boundary. During real Linux exchanges, repeatedly check that the live directory remains present as the dispatcher would. Crash reconciliation must handle identical payloads using directory identities and preserve ambiguity when necessary.

A systemd-capable isolated Linux test must prove the worker survives stopping/restarting a simulated loader unit and that startup acknowledgement succeeds while the worker holds its lock. Mock-only tests cannot establish either lifecycle property. Ordinary CI uses temporary roots and fake service/network boundaries; it must never mutate the CI host's actual services or `/etc`. Windows runs safe validation/collector tests only, never backend imports, installation, lifecycle or Linux mutation adapters.

First-device evidence must verify storage/capabilities, record exact candidate and environment, exercise the supported corrected transition and recovery procedure, and distinguish source fixtures from real channel tests. No placeholder Stable release is created to test updates. Remaining audit findings, external mutations, storage failure and unmeasured performance/battery effects retain explicit limitations.

## Primary references and preparation evidence

- [Stage 0 findings](../../audits/2026-10-15-stage-0-findings.md), [owner-reported environment](../../testing/results/2026-10-15-owner-inventory.md), [device protocol](../../testing/steam-deck-lcd-stable.md).
- [Linux rename/renameat2 manual](https://man7.org/linux/man-pages/man2/rename.2.html), checked 2026-10-15: exchange/no-replace semantics and filesystem failure conditions. Installed support remains a test prerequisite.
- [systemd's systemd-run documentation source](https://github.com/systemd/systemd/blob/main/man/systemd-run.xml), checked 2026-10-15: service-manager execution environment, Type=exec and argument expansion; target version capabilities remain to be verified.
- [Decky 3.2.10 directory-derived paths](https://github.com/SteamDeckHomebrew/decky-loader/blob/v3.2.10/backend/decky_loader/plugin/sandboxed_plugin.py#L75-L79), matching the owner's reported version. This source trace is not a device migration result.

Two `gpt-6.1-sol` preparation reviews covered inventory safety and recovery architecture. Coordinator review added the dispatcher missing-directory/exchange requirement; the recovery reviewer rechecked and accepted that correction. Implementation and device results remain pending.
