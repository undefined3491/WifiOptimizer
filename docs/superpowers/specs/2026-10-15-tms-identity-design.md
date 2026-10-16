# WiFi Optimizer TMS identity and repository rename

Date: 2026-10-15. Product baseline: `7e3d45f60504aa53b17155136535006b7bf1e634` (inherited product code audited at `e957c5b`).

**Status updated 2026-10-16:** Public display/package names were implemented and squash merged in [PR #4](https://github.com/undefined3491/wifi-optimizer-tms/pull/4) (`94cc9fe`). Repository/URL/archive cutover was completed through [PR #5](https://github.com/undefined3491/wifi-optimizer-tms/pull/5) (`d4ade2d`), retaining the same fork node ID; canonical archives/raw installer and [main CI](https://github.com/undefined3491/wifi-optimizer-tms/actions/runs/38885436582) were verified. The [staged branding record](../../branding.md) is the current implementation record. Device migration, recovery/pinning/duplicate-install mechanics below and first Stable remain pending; this status update does not approve or implement the recovery-engine proposal.

## Intent and approved names

Establish the fork's identity before its first Stable release and community growth. Keep existing settings and a single active optimizer while updating the installer, updater and delivery checks together.

| Surface | Selected value |
| --- | --- |
| Plugin display name, manifest and frontend registration | `WiFi Optimizer TMS` |
| GitHub repository slug | `wifi-optimizer-tms` |
| Canonical repository | `https://github.com/undefined3491/wifi-optimizer-tms` |
| `package.json` name | `wifi-optimizer-tms` |

The live repository is `undefined3491/wifi-optimizer-tms`; `undefined3491/WifiOptimizer` is its former name. The completed branding/cutover did not bump `0.11.6`, publish a package, create a Stable release or close Stage 0. Preserve Arcada Labs attribution, original copyright notices and the BSD-3-Clause license.

## Implemented source identifiers; device migration pending

The source retains `WiFi Optimizer` as the installation-directory identifier for both existing and fresh installs through this fork's installer and development deployment. Distinguish that identifier from the public plugin name in variable names and documentation.

Consequently, the standard paths remain `$DECKY_HOME/plugins/WiFi Optimizer`, `$DECKY_HOME/settings/WiFi Optimizer`, and the corresponding Decky data/log directories. Obtain runtime paths from Decky's environment rather than rebuilding them from the display name. Do not copy, reset, merge or delete settings as part of rebranding. An existing installation updated in place receives the new manifest and frontend name after restarting Decky.

Keep the existing dispatcher path and system-configuration filenames (`99-wifi-optimizer*`). They are compatibility identifiers for the same optimizer. Regenerating the dispatcher must continue to use the actual settings/plugin paths. Do not run Reset or Uninstall to accomplish the rename: audit findings ST0-004 and ST0-016 leave restoration behavior unresolved.

Decky source inspected on 2026-10-15 at commit `75563316f9119ee7e36be7f43885be65e877fad0` and rechecked at tag `v3.2.10` separates the manifest name from `plugin_directory`, derives settings/data/log paths from that directory and discovers the uninstall directory by reading manifests. These traces support the retained source identifiers. The [existing-installation inventory and runtime follow-up](../../testing/results/2026-10-16-owner-device-inventory.md) confirm a live Decky process reporting v3.2.10 and legacy installed files; migration to the renamed candidate has not been exercised.

Decky's own hidden/disabled/order preferences use plugin names in some paths. Do not rewrite Decky's global settings automatically. Record the old enabled/hidden state before migration and verify the new entry afterward; do not claim these UI preferences migrate automatically.

Alternatives considered: moving all directories to a new TMS identifier would require an additional settings/data/dispatcher migration without improving the public branding; changing only the GitHub name would leave application URLs and archive assumptions inconsistent. Retaining the directory is implemented in the branding source; device compatibility remains to be validated. A later directory migration would need a separate design.

## Implemented branding and pending migration requirements

- **Implemented in PR #4/#5:** manifest/package, frontend registration/title/messages, footer/report links and current user-facing documentation. Manifest and frontend names agree. **Pending device evidence:** IPC under the renamed installation.
- **Implemented in PR #5:** installer and backend Stable/Beta API/download URLs use the canonical fork. Keep the existing manual-installer main fallback and the existing separate Stable/Beta channel semantics. Do not introduce an upstream fallback or a new release source.
- **Pending recovery proposal:** apply the [recovery design's](2026-10-15-delivery-recovery-design.md) pinned-candidate contract: resolve main/Beta/Stable selection to a full commit and download that SHA archive, validating root `wifi-optimizer-tms-<commit-SHA>`. Branch/tag archive fixtures have distinct roots (`wifi-optimizer-tms-main`, `wifi-optimizer-tms-beta`, `wifi-optimizer-tms-X.Y.Z`); the release workflow's tag/version archive remains a separate packaging check. Do not use a branch/tag fixture root to validate a runtime SHA archive or infer that GitHub redirects preserve old root names. Validate required files before replacing an installation.
- **Implemented in PR #4/#5:** exact repository guard/archive root, release-workflow prefix, delivery fixtures, generated bundle/source-map identity and tracked rebuilt dist files. Reproducibility and source checks passed.
- Keep the VS Code deployment directory setting at `WiFi Optimizer`; explain that it is a directory key, not the displayed plugin name. Existing ignored local settings need inspection before a deployment, not automatic replacement.
- **Pending migration behavior:** before installation, inspect relevant plugin manifests for an existing legacy/TMS copy. The supported transition updates the one legacy directory. If another active copy or a conflicting target exists, stop with the paths and recovery instructions; do not silently overwrite it or leave both optimizers active. Do not scan or delete unrelated plugins or settings.
- Update current agent/contributor instructions and installation/clone examples at cutover. Preserve historical audit baselines, findings and rollout records as history rather than mass-replacing old names. List intentionally retained technical identifiers so future sessions do not rename them accidentally.

The already installed old updater cannot be repaired by changing repository metadata. Its hardcoded archive root may fail after a GitHub rename even if the URL redirects. Document the first transition through the corrected manual installer; do not promise that every old build can self-update across this rename. Repeated installation of the same new candidate must preserve settings and avoid duplicate entries.

## Audit dependencies and scope boundaries

This branding work stays within Stage 0. Installer/updater execution on the owner's device depends on reviewed fixes for ST0-001, ST0-002, ST0-003 and ST0-018: validated staging, recoverable replacement, checked copy outcomes, bounded/exclusive update work and truthful restart/error reporting. Their implementation requires a scoped recovery design and regression tests; a URL/string edit does not resolve them. Prepare the branding changes alongside that work or apply them after it, before asking the owner to run the migration.

Other networking behavior and remaining findings remain in the audit backlog. Do not fold unrelated optimization changes or Connection Watchdog into this rename. First Stable still requires all Critical/Important findings resolved, reviewed and supported by candidate-specific LCD / Stable evidence.

## Coordinated GitHub cutover

The source/GitHub portions of this procedure completed on 2026-10-16. Device installation in step 5 remains a later gated action; the source cutover did not execute installer/update hooks or implement recovery.

1. Prepare and review the implementation PR against the current fork's `main`, on a `codex/<change>` branch, with successful `ci-required`. Test the future identity using local archive fixtures before live URLs exist. Keep publishing paused during cutover.
2. Once the reviewed identity/URL/archive cutover PR is ready, rename the same GitHub repository in Settings to `wifi-optimizer-tms`. This is a rename of the existing fork, not creation of a replacement repository. The owner may do this in the UI; selecting the name alone is not evidence that the external rename has occurred.
3. Read back the canonical repository identity, open PR/base/head and Git remotes. Set `origin` to `https://github.com/undefined3491/wifi-optimizer-tms.git` in local clones as needed; linked worktrees share repository configuration. Existing local folder names can remain unchanged. Do not reuse the old GitHub repository name because that breaks its redirects.
4. Verify the reviewed PR still targets the same fork and head. Re-run required CI if necessary after the rename and squash merge only after review and successful `ci-required`. There is a short coordinated interval between rename and merge; do not direct users to install during it.
5. Verify main CI, canonical download/API URLs and actual main archive layout. Install only the corrected candidate under the device protocol. The source/GitHub cutover can be complete while migration remains pending; validate migration and fresh installation separately before claiming device compatibility.

Stable publication and any Beta branch update remain separate manual decisions under the existing delivery policy. Do not dispatch the release workflow to test the rename. An absent fork Stable release remains an expected state until Stage 0 closes.

## Source acceptance and pending device/recovery evidence

- Frozen pnpm 9 installation, build, project type check, safe AST/Bash syntax checks, delivery tests and committed bundle/source-map verification pass. No backend imports or system mutations on Windows.
- Renamed release repository/version-root fixtures and actual canonical main/commit archive layout were checked. **Pending recovery/migration acceptance:** failed staging/copy/restart, duplicate-install refusal and preservation of an existing installation/settings, plus isolated Linux installer execution. The new URLs and static fixtures do not certify those runtime behaviors.
- Capture exact LCD / SteamOS Stable, kernel, driver, effective WiFi backend and Decky versions. Back up existing plugin/settings/dispatcher evidence before installation. On the selected candidate, verify one visible `WiFi Optimizer TMS` entry, working IPC, unchanged settings, correct dispatcher paths, reconnect, sleep/wake and an explicit recovery procedure.
- Check new updater behavior without publishing a placeholder Stable release. A missing release is reported honestly. Beta installation/update coverage remains pending until a deliberate Beta candidate exists; archive-fixture coverage is recorded separately from a real channel update.
- Record the final candidate SHA, old/new manifest/package identity, canonical GitHub identity, CI links and device outcome. Keep the audit report's original findings/baseline and add targeted re-review evidence for changed flows.

## Primary references

- [GitHub repository rename behavior and remote updates](https://docs.github.com/en/repositories/creating-and-managing-repositories/renaming-a-repository), checked 2026-10-15.
- [Decky manifest name and directory handling](https://github.com/SteamDeckHomebrew/decky-loader/blob/75563316f9119ee7e36be7f43885be65e877fad0/backend/decky_loader/plugin/plugin.py#L18-L38).
- [Decky settings, data, log and plugin paths](https://github.com/SteamDeckHomebrew/decky-loader/blob/75563316f9119ee7e36be7f43885be65e877fad0/backend/decky_loader/plugin/sandboxed_plugin.py#L75-L79).
- [The same directory-based paths in Decky 3.2.10](https://github.com/SteamDeckHomebrew/decky-loader/blob/v3.2.10/backend/decky_loader/plugin/sandboxed_plugin.py#L75-L79), rechecked 2026-10-15.
- [Decky discovery of a plugin's uninstall directory and name-based UI preferences](https://github.com/SteamDeckHomebrew/decky-loader/blob/75563316f9119ee7e36be7f43885be65e877fad0/backend/decky_loader/browser.py#L98-L149).
- [Stage 0 findings](../../audits/2026-10-15-stage-0-findings.md) and [LCD / Stable device protocol](../../testing/steam-deck-lcd-stable.md).
