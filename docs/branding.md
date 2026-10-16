# WiFi Optimizer TMS branding stages

Recorded: 2026-10-16. The owner selected `WiFi Optimizer TMS` for the plugin and `wifi-optimizer-tms` for the package and future repository. Apply these names in small reviewed changes; publishing remains separate.

| Stage | Scope | Status |
| --- | --- | --- |
| 1 — Display and package | Manifest, frontend registration/title/messages, package name, installer messages, documentation and rebuilt distribution | Prepared on `codex/tms-branding`; not merged, deployed or released |
| 2 — Repository | Rename the existing fork to `undefined3491/wifi-optimizer-tms`; change canonical URLs, archive roots, release guards/fixtures and remotes together | Pending coordinated PR, review and GitHub cutover |
| 3 — Device transition | Corrected installer/update candidate, recoverable configuration, one visible TMS entry, working IPC, preserved settings and device checks | Pending audited fixes and the LCD / Stable protocol |

The current repository is still [undefined3491/WifiOptimizer](https://github.com/undefined3491/WifiOptimizer). Stage 1 deliberately keeps its working installer/updater URLs, archive roots and repository guard. Changing the package name does not change the GitHub repository or source archive root. No version bump or Stable publication accompanies this preparation; version `0.11.6` remains provisional until release preparation after Stage 0.

## Public names and compatibility identifiers

| Surface | Value and reason |
| --- | --- |
| Manifest and frontend registration/title | `WiFi Optimizer TMS`; names must agree for Decky routing |
| Package name | `wifi-optimizer-tms` |
| Bundle/source-map plugin URI | `decky://decky/plugin/WiFi%20Optimizer%20TMS/`; follows the public plugin name |
| Installer directory key / VS Code `pluginname` | `WiFi Optimizer`; selects the existing installation directory |
| Settings/data/log directories | Continue to derive from the actual Decky plugin directory, not the new display name |
| Dispatcher, NM and modprobe files | Keep existing `99-wifi-optimizer*` identifiers |
| Temporary paths and system logger tag | Keep existing `wifi-optimizer*` identifiers |

Stage 1 does not move, merge, reset or delete settings or install another copy. It changes no networking operation or restoration behavior. Do not run Reset/Uninstall to apply branding. Existing devices keep their installed version until an explicit corrected-candidate deployment; a rebuilt repository bundle is not device evidence. Decky's name-based hidden/disabled/order preferences require observation during the later migration and are not automatically rewritten here.

Keep Arcada Labs attribution and the BSD-3-Clause license intact. Historical audit baselines and delivery records retain the names and repository identity they originally reviewed.

## Checks and next step

For Stage 1, run delivery-validator tests, frozen pnpm 9 installation, build, project type check, safe AST/Bash syntax checks and distribution reproducibility verification. Never import the root backend or execute the installer/dispatcher on Windows. Commit both rebuilt dist files with their sources. The source-map validator must accept the new plugin URI and reject another plugin's URI; retain current repository/archive validation until Stage 2.

The broader compatibility/recovery proposal is under review in [PR #3](https://github.com/undefined3491/WifiOptimizer/pull/3). Stage 2 needs a concrete URL/archive cutover PR before the external rename. Confirm the actual repository identity after renaming and before changing remotes or claiming completion. Stage 3 follows reviewed installation/update and restoration fixes and [device validation](testing/steam-deck-lcd-stable.md).

The [Stage 0 findings](audits/2026-10-15-stage-0-findings.md) remain open. Source branding does not establish migration safety, optimization benefit, reconnect/sleep-wake correctness or readiness for the first Stable release.
