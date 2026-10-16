# WiFi Optimizer TMS branding stages

Recorded: 2026-10-16. The owner selected `WiFi Optimizer TMS` for the plugin and `wifi-optimizer-tms` for the package and future repository. Apply these names in small reviewed changes; publishing remains separate.

| Stage | Scope | Status |
| --- | --- | --- |
| 1 — Display and package | Manifest, frontend registration/title/messages, package name, installer messages, documentation and rebuilt distribution | Squash merged in [PR #4](https://github.com/undefined3491/wifi-optimizer-tms/pull/4) as `94cc9fe`; not deployed or released |
| 2 — Repository | Rename the existing fork to `undefined3491/wifi-optimizer-tms`; change canonical URLs, archive roots, release guards/fixtures and remotes together | Source changes prepared on `codex/repository-rename`; GitHub rename/read-back coordinated before merge |
| 3 — Device transition | Corrected installer/update candidate, recoverable configuration, one visible TMS entry, working IPC, preserved settings and device checks | Pending audited fixes and the LCD / Stable protocol |

The canonical repository for the cutover is [undefined3491/wifi-optimizer-tms](https://github.com/undefined3491/wifi-optimizer-tms). This is a rename of the existing fork with repository node ID `R_kgDOVK96Ww`, not a new repository. Stage 1 kept the old URLs while Stage 2 changes installer/updater/report URLs, archive assumptions and the release guard together. No version bump or Stable publication accompanies this work; version `0.11.6` remains provisional until release preparation after Stage 0.

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

Run delivery-validator tests, frozen pnpm 9 installation, build, project type check, safe AST/Bash syntax checks and distribution reproducibility verification. Never import the root backend or execute the installer/dispatcher on Windows. Commit both rebuilt dist files with their sources. The source-map validator accepts the TMS plugin URI and rejects another plugin's URI. Release validation accepts only `undefined3491/wifi-optimizer-tms` and its exact version archive root.

Stage 2 retains the existing branch/tag download protocol: main archive root `wifi-optimizer-tms-main`, Beta root `wifi-optimizer-tms-beta`, Stable `vX.Y.Z` tag archive root `wifi-optimizer-tms-X.Y.Z`. The manual release fixture uses the same version root. A SHA archive has a different root and must not be substituted for a version/branch fixture. Resolve/download pinning and recovery behavior remain proposed audit work, not fixes included in this rename.

Before external rename, review the cutover PR and require successful `ci-required`. Rename the same fork, read back its canonical full name and unchanged node ID, update shared `origin` to `https://github.com/undefined3491/wifi-optimizer-tms.git`, and recheck the PR base/head and CI before squash merge. Then verify main CI and actual canonical main source archive. Local checkout folder names can remain unchanged. Existing linked worktrees share `origin`; unrelated clones need their own remote update. Record observed cutover results in the PR.

[GitHub documents redirects and remote updates](https://docs.github.com/en/repositories/creating-and-managing-repositories/renaming-a-repository), checked 2026-10-16. Do not reuse the old repository name. Redirects do not repair an old updater's hardcoded archive root; legacy updater migration is not validated by a repository rename. Do not instruct the owner to reinstall/reset through the unresolved legacy flows to complete branding.

The broader compatibility/recovery proposal remains under review in [PR #3](https://github.com/undefined3491/wifi-optimizer-tms/pull/3). Stage 3 follows reviewed installation/update and restoration fixes and [device validation](testing/steam-deck-lcd-stable.md). Stable requires a published release and Beta requires a deliberate `beta` branch; missing channels are not replaced with upstream downloads or created as rename fixtures.

The [Stage 0 findings](audits/2026-10-15-stage-0-findings.md) remain open. Source branding does not establish migration safety, optimization benefit, reconnect/sleep-wake correctness or readiness for the first Stable release.
