# WiFi Optimizer TMS branding stages

Recorded: 2026-10-16. The owner selected `WiFi Optimizer TMS` for the plugin and `wifi-optimizer-tms` for the package and repository. Source branding and GitHub cutover are complete; device transition and publishing remain separate.

| Stage | Scope | Status |
| --- | --- | --- |
| 1 — Display and package | Manifest, frontend registration/title/messages, package name, installer messages, documentation and rebuilt distribution | Squash merged in [PR #4](https://github.com/undefined3491/wifi-optimizer-tms/pull/4) as `94cc9fe`; not deployed or released |
| 2 — Repository | Rename the existing fork to `undefined3491/wifi-optimizer-tms`; change canonical URLs, archive roots, release guards/fixtures and remotes together | Squash merged in [PR #5](https://github.com/undefined3491/wifi-optimizer-tms/pull/5) as `d4ade2d`; same repository identity and main CI verified |
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

Stage 2's rename, shared-origin update, review/CI and canonical archive verification are complete; observed results are recorded below. Local checkout folder names can remain unchanged. Existing linked worktrees share `origin`; unrelated clones need their own remote update. Do not repeat the rename or substitute display-name changes for device migration.

[GitHub documents redirects and remote updates](https://docs.github.com/en/repositories/creating-and-managing-repositories/renaming-a-repository), checked 2026-10-16. Do not reuse the old repository name. Redirects do not repair an old updater's hardcoded archive root; legacy updater migration is not validated by a repository rename. Do not instruct the owner to reinstall/reset through the unresolved legacy flows to complete branding.

The broader compatibility records and conditional recovery proposal are documented through [PR #3](https://github.com/undefined3491/wifi-optimizer-tms/pull/3); merging preparation documentation does not approve that engine. Stage 3 follows reviewed installation/update and restoration fixes and [device validation](testing/steam-deck-lcd-stable.md). Stable requires a published release and Beta requires a deliberate `beta` branch; missing channels are not replaced with upstream downloads or created as rename fixtures.

See the [Stage 0 findings](audits/2026-10-15-stage-0-findings.md) for current correction status. Source branding does not establish migration safety, optimization benefit, reconnect/sleep-wake correctness or readiness for the first Stable release.

## Observed cutover result — 2026-10-16

GitHub read-back confirmed `undefined3491/wifi-optimizer-tms` with unchanged node ID `R_kgDOVK96Ww` and fork relation. Shared origin is the new `.git` URL; the primary checkout was fast-forwarded to `d4ade2d848c7cc9db5b78afc436e06ab76709199`. [Main CI passed](https://github.com/undefined3491/wifi-optimizer-tms/actions/runs/38885436582).

At 10:10:58–10:11:02 UTC the canonical main archive, exact merge-commit archive and raw main installer returned HTTP 200. Roots were `wifi-optimizer-tms-main` and `wifi-optimizer-tms-d4ade2d848c7cc9db5b78afc436e06ab76709199`; installer, backend and both dist files matched the merge commit byte-for-byte. The old repository API resolved to the same new identity. Latest Stable and the Beta branch returned 404; neither was created. Raw verification metadata remains in ignored local `out/branding/cutover-verification.json`. No device writes, deployment, tag or publication occurred.
