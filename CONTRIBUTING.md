# Contributing

## Branches, pull requests, and review

Use a short-lived feature branch with any clear name (for example, `feat/`, `fix/`, or `chore/`) and open a pull request targeting `main`. Complete review and the required `ci-required` check before merging by squash. Review is required even when one maintainer handles the change; there are zero mandatory external human approvals, so a solo maintainer can complete the process. Merged branches are removed.

Merging does not publish a release. Documentation and CI-only changes do not need a version bump. Do not push directly to `main` or publish Stable automatically on merge.

## Local checks and generated files

Use Node.js and pnpm 9. Install from the frozen lockfile and run the same build and source type check used by CI:

```bash
npm exec --yes --package=pnpm@9 -- pnpm install --frozen-lockfile
npm exec --yes --package=pnpm@9 -- pnpm run build
npm exec --yes --package=pnpm@9 -- pnpm exec tsc --noEmit --skipLibCheck
```

The full type check without `--skipLibCheck` currently reports missing `react-router` declarations inside `@decky/api` 1.1.3, including on the unchanged baseline. Do not alter dependencies or `tsconfig.json` to work around that dependency issue. There are no test or lint scripts in `package.json`.

`dist/index.js` and `dist/index.js.map` are tracked release files. Rebuild after source changes and commit both generated files with the source that produced them. CI checks that committed output matches a fresh build; it does not commit generated changes for you.

## Preparing a release

Prepare a release in a dedicated PR or a PR explicitly designated for release preparation. Bump the package version by patch for fixes and minor for features, then add a matching `## [<version>]` section to `CHANGELOG.md`. Stable releases use tag `v<package.json version>` and must include rebuilt tracked dist files in that exact tagged commit. The release workflow is manually dispatched and requires the maintainer's device-test attestation; publication remains a manual decision after review and checks.

The exact future workflow files are `.github/workflows/ci.yml` and `.github/workflows/release.yml`; the shared verification action will be `.github/actions/verify/action.yml`. These files are planned implementation and are not active yet. The required check name is `ci-required`. GitHub protection and repository settings also need to be applied and verified separately; checked-in configuration alone does not activate them.

## Device check and publication

Before publishing Stable, smoke-test on a supported Linux handheld: confirm the plugin loads, settings and UI work, and reset behaves as expected. For networking changes, also verify reconnect and sleep/wake. CI cannot establish device or network correctness.

Stable checks the fork's latest GitHub release and downloads the matching `v<version>` tag. Beta reads `package.json` from this fork's `beta` branch; a GitHub pre-release does not drive the Beta updater. Maintain `beta` only when pre-release testing is needed, and update its package version for each distributable beta (for example `0.12.0-beta.1`). The installer can fall back to this fork's `main` when no release tag is available; the in-app Stable updater has no fallback. Never substitute the upstream repository.

Rollout activation order: land and verify CI on a real PR first, confirm the exact `ci-required` check context, then apply and verify GitHub protection/settings. Stable publication remains separate and requires a reviewed release commit plus the device check above.
