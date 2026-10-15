# Delivery workflow design

Date: 2026-10-15

Status: The owner approved this spec and its implementation plan on 2026-10-15. PR #1 was squash merged into this fork's `main` as `e957c5b` and main CI passed. Remote protection/settings activation remains pending. The owner's latest reissued AGENTS.md requires `codex/<change>` branches, superseding the earlier unrestricted naming decision. The subsequent [audit-first roadmap](../../../ROADMAP.md) adds Stage 0 before the first fork Stable release; the remaining delivery mechanics below stay in effect.

## Purpose and authority

Make contribution and release decisions durable across sessions and enforce the automatable parts. The project is a root-running Decky WiFi plugin; CI can verify source and packaging but cannot establish device/network correctness.

`AGENTS.md` contains the binding session-facing policy. `CONTRIBUTING.md` will contain the contributor/release runbook. This spec records the selected design; the implementation plan describes execution, not an alternative policy. Later sessions follow the settled workflow unless the owner explicitly changes it. Concrete defects or contradictions should be reported and corrected without inventing a replacement process.

## Existing state and prerequisites

- Repository: `undefined3491/WifiOptimizer`; default branch: `main`; version: `0.11.6`.
- Existing fork URL fixes are preserved in commit `d47b65e` on `codex/delivery-workflow`.
- At inspection, Actions is enabled, but there are no workflows, rulesets, protected-main settings, release tags, or `beta` branch. The authenticated owner has administrator access.
- Installer and updater consume GitHub source archives. Stable checks `releases/latest`, then downloads `refs/tags/v<version>`; Beta reads `package.json` and downloads `refs/heads/beta`. Their expected archive roots are `WifiOptimizer-<version>` and `WifiOptimizer-beta`.
- `dist/index.js` and `dist/index.js.map` are tracked and must ship in the source archive. An Actions artifact or uploaded release asset alone is insufficient.
- Full TypeScript checking currently reports TS2307 for missing `react-router` declarations in `@decky/api` 1.1.3, including on the unmodified baseline. Project-source checking with `--skipLibCheck` succeeds.

## Chosen contribution policy

1. Changes use a short-lived `codex/<change>` branch and a PR targeting `main`, following the owner's latest reissued AGENTS.md. The original rollout allowed unrestricted names; that earlier preference is superseded for new work.
2. The required check is named exactly `ci-required`. Review is completed before squash merge. Zero mandatory human approvals allows a solo maintainer to work; it does not waive code review.
3. `main` is protected against deletion, force push, and changes that bypass the PR/check requirements. Repository merge settings allow squash merge and remove merged branches; merge commits and rebase merge are disabled.
4. Merging changes does not publish releases. Version preparation is a separate PR, or part of a PR explicitly designated for release preparation.
5. Patch versions cover fixes; minor versions cover features. Docs/CI-only changes do not independently bump the package version. The existing functional fork fixes make `0.11.7` a future candidate, not a release authorized by this rollout.
6. Add/maintain a `beta` branch only for changes needing pre-release testing. A Beta branch version changes for each distributable beta, e.g. `0.12.0-beta.1`; a GitHub pre-release alone does not drive the current Beta updater.

## CI design

Use GitHub-hosted `ubuntu-24.04`, Node `24`, pnpm `9.15.9`, and Python `3.11`. Do not change product dependencies, the lockfile, or `tsconfig.json` to introduce CI.

Trigger CI on every `pull_request` to `main` and pushes to all branches, with no branch-name or path filters on pushes that could exclude work from another development environment. Use read-only repository permissions, bounded timeouts, and concurrency cancellation for superseded runs. Never use `pull_request_target` to build contributed code.

A local composite action provides the same verification steps to CI and the release workflow:

- Check the committed source map and snapshot committed `dist` before building.
- `pnpm install --frozen-lockfile`.
- `pnpm run build`.
- `pnpm exec tsc --noEmit --skipLibCheck`.
- Parse `main.py` and `decky.pyi` as Python syntax; do not import/execute plugin lifecycle, status or setters.
- Run `bash -n` on `install.sh`, the dispatcher template, and a harmless rendering of the update-script f-string extracted through Python AST.
- Run standard-library unit tests for the delivery validators.
- Verify rebuilt JS and semantically normalized source map match the committed snapshot. Fail on stale generated artifacts; do not auto-commit fixes.

Source map normalization accepts both `decky://decky/plugin/WiFi%20Optimizer/...` and repository-relative paths by retaining each source's `src/` or `node_modules/` suffix. Normalize line endings in source text and JS. Preserve/compare mappings, names and other map fields; verify embedded repository sources against current files. A changed source/mapping must fail even when an allowed URI prefix differs. Reject ambiguous or unrecognized source paths. Add `* text=auto eol=lf` in `.gitattributes` without mass-renormalizing unrelated files.

Actions are pinned by full verified commit SHA, with readable version comments. Pins verified while planning:

- `actions/checkout`: `3d3c42e5aac5ba805825da76410c181273ba90b1` (`v7.0.1`).
- `actions/setup-node`: `949feb2413d6458794dcd2491c4babbbce0c15c1` (`v7.1.0`).
- `actions/setup-python`: `5fda3b95a4ea91299a34e894583c3862153e4b97` (`v7.0.0`).
- Install the explicitly selected pnpm version through npm in the ephemeral runner; no additional pnpm setup action is necessary.

## Stable publication design

Provide a separate `workflow_dispatch` workflow with required `version` string and `deck_tested` boolean inputs. It must reject an unchecked attestation, non-main dispatch, or a repository other than `undefined3491/WifiOptimizer`.

The workflow checks out and publishes the exact dispatch commit SHA, not a later moving branch head. It reuses the verification composite action and verifies:

- Stable version consists of exactly three non-negative numeric components, without leading zeroes or a prerelease suffix.
- Input version matches `package.json` and has a corresponding `## [<version>]` entry in `CHANGELOG.md`.
- Version is greater than the latest published Stable version, if one exists; the first release is allowed only after an explicit API 404, not an arbitrary API/network failure.
- Neither the tag nor its release already exists. Reruns refuse duplicates and never move/overwrite a published tag.
- A `git archive` of the exact target commit contains `plugin.json`, `package.json`, `main.py`, `decky.pyi`, `dist/index.js`, `dist/index.js.map`, and `defaults/dispatcher.sh.tmpl`, under `WifiOptimizer-<version>/`.

Only the publication job receives `contents: write`; validation jobs remain read-only. Pass workflow inputs as environment variables, validate them before use, and avoid interpolating untrusted expressions into shell code. Serialize release runs. After validation, create `v<version>` at the verified SHA and publish a full GitHub Release marked latest, with notes from that version's changelog entry. No automatic publication on push/merge and no automatic version-changing commits.

The checkbox records the maintainer's attestation; it is not an automated hardware test. The runbook requires checking plugin load, settings/UI, reset, and for networking changes reconnect plus sleep/wake on a supported Linux device.

## Durable files

- `AGENTS.md`: short binding policy, links and truthful rollout status.
- `CONTRIBUTING.md`: branch/PR/review flow, commands, generated artifacts, version/release steps, device checklist, beta semantics and operational activation.
- `CHANGELOG.md`: `Unreleased` notes for the existing fork fixes; future releases get explicit version sections. Do not fabricate release dates or bump `package.json` for this rollout.
- `.github/PULL_REQUEST_TEMPLATE.md`: change summary, verification and device-test evidence, with a release-preparation field.
- `.github/actions/verify/action.yml`, `.github/workflows/ci.yml`, `.github/workflows/release.yml`: shared checks and two distinct workflows.
- `scripts/check_delivery.py`, `tests/test_delivery.py`: standard-library validators and meaningful regression tests.
- `.github/rulesets/main.json`, `.github/repository-settings.json`: desired protection/merge configuration checked into the repository, with explicit application instructions. These JSON files do not configure GitHub merely by existing.
- `.gitattributes`: consistent text line endings.

## Rollout and boundaries

First review this spec/plan. Then execute on an isolated managed worktree using subagent-driven development: `gpt-6-luna` implementers at medium reasoning, task/final reviewers at high reasoning. User model selection takes precedence over skill defaults. Use one implementer at a time and a persistent execution ledger.

The implementation produces a reviewable branch/PR. Activate protections only after a successful real PR check establishes the exact `ci-required` context. Confirm remote settings through the GitHub API after applying them. Report separately what is implemented locally, pushed, checked, merged, protected and published; never describe desired configuration as active enforcement.

The rollout itself does not publish `0.11.7`, create `beta`, merge `main`, or apply remote repository protection settings without the final owner go-ahead on the reviewed result. Hardware testing and publishing a Stable release remain explicit maintainer steps.

## Acceptance checks

1. A new session can discover the settled policy from `AGENTS.md` and follow the runbook without choosing a new workflow.
2. A PR gets a real `ci-required` result; stale dist, syntax/type errors and validator regressions fail it.
3. Equivalent allowed source-map prefixes/EOL pass; modified embedded sources or mappings fail.
4. Release validation rejects malformed/mismatched versions, an untested device attestation, wrong repo/ref, duplicates, inaccessible API and incomplete source archives.
5. A validated release targets the tested SHA and is consumable by the current installer/updater. No release is created by ordinary merges.
6. Full build and checks leave product dependencies, IPC, WiFi behavior and package version unchanged.

## References

- [GitHub protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches).
- [GitHub repository rules API](https://docs.github.com/en/rest/repos/rules).
- [GitHub release API](https://docs.github.com/en/rest/releases/releases).
- [GitHub workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax).
