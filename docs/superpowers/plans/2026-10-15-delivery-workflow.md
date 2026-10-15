# Delivery Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preserve the owner's delivery policy across sessions and add verifiable PR checks plus a separate manually triggered Stable release workflow.

**Architecture:** `AGENTS.md` and `CONTRIBUTING.md` define the settled workflow. A shared composite action performs checks for both PR CI and a manually dispatched release workflow; standard-library Python validators check generated artifacts and publication prerequisites. Repository settings are declared in JSON and applied only after real CI has run and the owner approves activation.

**Tech Stack:** GitHub Actions, Ubuntu 24.04, Node 24, pnpm 9.15.9, Python 3.11, Bash, GitHub CLI; no new product dependencies.

**Spec:** [Delivery workflow design](../specs/2026-10-15-delivery-workflow-design.md).

**Status:** Prepared for owner review; implementation tasks have not started.

## Global Constraints

- Repository: `undefined3491/WifiOptimizer`; default branch: `main`; version remains `0.11.6` during this rollout.
- Short-lived `codex/<change>` branch -> PR -> required `ci-required` check and review -> squash merge. Stable publication is separate and manual.
- No product dependency, lockfile, `tsconfig.json`, IPC or WiFi behavior changes. Never execute/import plugin runtime methods to validate CI.
- CI: `ubuntu-24.04`, Node `24`, pnpm `9.15.9`, Python `3.11`; use `tsc --noEmit --skipLibCheck` for the documented dependency-declaration issue.
- Use the three exact action SHA pins in the spec, read-only permissions by default and write permissions only in the release publication job.
- Preserve all earlier fork fixes in `d47b65e`. Never replace/publish upstream files or remove original attribution.
- Execute through isolated-context Luna subagents: implementers `gpt-6-luna`/medium; reviewers `gpt-6-luna`/high. No worker spawns subagents. One implementation task at a time.
- No merge, Stable publication, creation of `beta`, or remote protection/settings changes without final owner approval of the reviewed result.

## Review Focus

- A Windows-generated map with Decky versus relative source URIs must not falsely fail Linux CI; changed source/mapping content must fail (Task 2 tests).
- A release dispatched from another branch/repository or without device attestation must fail before any write (Task 3 tests/workflow review).
- An API outage must not be mistaken for the first release; duplicate release/tag must not overwrite a published version (Task 3 tests).
- A successful build with stale committed `dist` must still fail CI, and missing shipped files must block publication (Tasks 2 and 3 tests).
- Desired protection JSON is not active GitHub enforcement; documentation and final report must distinguish them (Tasks 1 and 3 review/API checks).

## Setup and recovery

- [ ] Read the spec and this plan; verify branch/history, existing commits, local instructions and any plan ledger before dispatching work.
- [ ] Use `using-git-worktrees` and the native managed-worktree tool to isolate execution from the planning checkout, starting from the reviewed `codex/delivery-workflow` state. Install with pnpm 9 and establish the documented build/typecheck baseline.
- [ ] Use the SDD skill's workspace script for this plan; initialize its ledger and record preflight task/interface conflicts. User approval of this plan includes the described isolated workspace setup.
- [ ] Record the spec/plan approval and exact execution branch/base SHA. Each implementation task gets its extracted task brief and a report path, followed by an independent task review.

### Task 1: Contributor runbook and durable delivery policy

**Files:** Modify `AGENTS.md`, `README.md`; create `CONTRIBUTING.md`, `CHANGELOG.md`, `.github/PULL_REQUEST_TEMPLATE.md`, `.gitattributes`.

**Interfaces:** Consumes the agreed spec and existing fork fixes. Produces policy/runbook links, changelog release-heading convention `## [<version>]`, and LF text policy consumed by Tasks 2/3. Reference future workflow/check filenames exactly; clearly mark unactivated remote settings.

- [ ] Write `CONTRIBUTING.md` covering PR/squash/review, pnpm 9 checks, committed dist, version preparation, manual device checklist, Stable/Beta updater semantics, and activation order. Use the spec's exact workflow/check names; zero mandatory external approvals for solo maintenance.
- [ ] Add changelog `Unreleased` notes for the existing fork URL fixes. No release date/version section is invented and `package.json` stays `0.11.6`.
- [ ] Add the PR template and `* text=auto eol=lf`. Do not run mass-renormalization. Update README links and AGENTS authority/runbook links while retaining architecture gotchas and truthful rollout status.
- [ ] Verify every local documentation link points to an existing file, except explicitly labelled future implementation files. Check policy consistency against all spec sections and run `git diff --check`.
- [ ] Commit only task-owned files; report commit SHA, verification and any limitations. Dispatch independent task review; fix confirmed Important/Critical findings through the implementer.

### Task 2: Shared CI verification and required PR check

**Files:** Create `scripts/check_delivery.py`, `tests/test_delivery.py`, `.github/actions/verify/action.yml`, `.github/workflows/ci.yml`.

**Interfaces:** Python CLI subcommands `snapshot --output PATH`, `verify-dist --snapshot PATH`, and `check-syntax`. Snapshot stores normalized committed bundle/map and validates embedded repository sources before the build. `check-syntax` invokes `check_python_and_shell`. Task 3 reuses `./.github/actions/verify` after checkout. Required job display name is exactly `ci-required`.

Public helper contracts (raise `ValueError` with actionable messages on invalid inputs):

- `normalize_source_map(data: dict) -> dict`: compare all fields; normalize only allowed source URI prefixes and LF/CRLF text according to the spec.
- `check_source_map_sources(root: Path, data: dict) -> None`: validate embedded repository sources against current files, requiring `src/index.tsx` and rejecting missing/ambiguous repo sources.
- `snapshot_dist(root: Path, output: Path) -> None`: validate/snapshot committed artifacts before building.
- `verify_dist(root: Path, snapshot: Path) -> None`: reject changed bundle/map after semantic normalization.
- `check_python_and_shell(root: Path) -> None`: AST-parse backend/stub, extract/render only the known update-script f-string with harmless values, and run Bash syntax parsing without executing scripts.

- [ ] Add standard-library `unittest` cases for equivalent Decky/relative map prefixes and CRLF, changed mappings/source contents/JS, unsupported paths, missing bundle/map and stale embedded sources. Add a malformed generated-update-script fixture for the syntax validator. Run `python -m unittest discover -s tests -v`; first observe failures for missing functionality.
- [ ] Implement the specified CLI/helpers using standard libraries. Validate snapshot/map structure and return nonzero actionable CLI errors; avoid plugin imports, backend execution and broad directory changes.
- [ ] Add the composite action using the spec's pinned checkout-independent setup-node/setup-python actions, Node 24, Python 3.11 and pnpm 9.15.9. Run snapshot before build, frozen install, build, typecheck, validators/tests, and verify-dist. Temporary files go under `RUNNER_TEMP`; no generated fixes are committed automatically.
- [ ] Add the read-only `ci.yml`: all PRs to main and pushes to main/codex branches, job `ci-required`, bounded timeout, cancellation of superseded branch runs, no path filter and no `pull_request_target`. Checkout uses the spec's pinned action.
- [ ] Run all validator tests and local build/typecheck. Verify the committed baseline passes artifact checks, deliberately stale temporary fixtures fail, workflow YAML parses, and the required job name/triggers/permissions match the spec. Account for source-map URI/EOL portability instead of blindly comparing raw map bytes.
- [ ] Commit task-owned files and complete independent task review before Task 3 starts. Keep `package.json`, lockfile and product logic unchanged.

### Task 3: Manual Stable release and protection configuration

**Files:** Create `.github/workflows/release.yml`, `.github/rulesets/main.json`, `.github/repository-settings.json`; extend `scripts/check_delivery.py`, `tests/test_delivery.py`; finalize operational status/instructions in `CONTRIBUTING.md`, `AGENTS.md`.

**Interfaces:** Consumes Task 2's composite check and helpers plus Task 1's changelog convention. Add CLI `validate-release --version VERSION --ref REF --repository REPOSITORY --deck-tested BOOL`, `verify-archive --archive PATH --version VERSION`, `release-history --version VERSION --repository REPOSITORY`, and `release-notes --version VERSION --output PATH`. Remote queries use GitHub CLI authentication without printing secrets; distinguish explicit 404 from other API failures. The publication job checks out the same validated SHA and extracts notes locally, without requiring uploaded intermediate artifacts.

Helper contracts:

- `validate_release(root: Path, version: str, ref: str, repository: str, deck_tested: bool) -> str`: return exact `v<version>` tag only for canonical repo/main, true device attestation, valid stable numeric version, matching package and changelog entry.
- `validate_release_history(version: str, latest_version: str | None, existing_tag: bool, existing_release: bool) -> None`: reject duplicate tag/release or a non-increasing/invalid Stable version. `None` is supplied only after an explicitly handled API 404.
- `get_release_history(repository: str, version: str) -> tuple[str | None, bool, bool]`: query latest Stable release, candidate tag and candidate release through `gh api`; return history only for successful responses or explicit not-found statuses, otherwise fail. Test this boundary with stubbed subprocess responses; make no real remote changes in tests.
- `verify_archive(archive: Path, version: str) -> None`: inspect tar entries without extracting/executing them; require the exact archive root and all seven shipped files named by the spec, rejecting missing/duplicate/unsafe paths.
- `release_notes(changelog: str, version: str) -> str`: return only that version's nonempty changelog section for publication.

- [ ] First add/run failing tests for malformed/leading-zero/prerelease/mismatched versions, wrong repo/ref, false attestation, absent changelog section, duplicate tag/release, non-increasing versions, non-404 API failures, missing/duplicate/unsafe archive entries and notes-section boundaries.
- [ ] Implement validators/CLI and extend tests to green. Use environment variables for workflow inputs; never evaluate untrusted shell expressions. Keep remote release creation outside the validators and make validation read-only.
- [ ] Add `release.yml` with only manual dispatch, required `version`/`deck_tested`, exact dispatch-SHA checkout, serialized release concurrency, shared verification, release-history/archive checks, and a dependent publication job. Only publication has `contents: write`. Create tag/release at the tested SHA and extract notes from the changelog; refuse duplicates and never retag. No hardware-test claims beyond the maintainer attestation.
- [ ] Add desired main ruleset JSON: PR required, zero required human approvals, resolved conversations, strict `ci-required`, no deletion/force push or routine bypass. Add settings JSON enabling squash only and merged-branch deletion. Validate against current official GitHub API schema; do not apply either file remotely yet.
- [ ] Finalize runbook commands and activation checklist: first successful actual PR CI, verify check context, owner-reviewed merge/settings activation, read-back remote configuration. Mark local implementation and remote activation as separate states. No version bump, beta creation or release during rollout.
- [ ] Run complete unit suite, build/typecheck, Python/Bash/workflow syntax checks, generated-artifact validation and `git diff --check`. Review the exact publication SHA propagation and token permission boundaries. Commit and complete independent task review.

## Final verification and handoff

- [ ] Dispatch a fresh `gpt-6-luna`/high whole-branch reviewer using the SDD final-review package and ledger; resolve confirmed blocking findings via one implementer fix wave plus scoped re-review.
- [ ] Verify tracked archive contents for the implementation commit, documentation links, unchanged product version/dependencies/lockfile, and settled policy consistency.
- [ ] Prepare a PR-ready branch and concise description with validation evidence, known full-tsc limitation, device-test requirements and inactive protection status. Do not describe local checks as successful hosted Actions runs.
- [ ] Present the reviewed result for the final owner decision on pushing/merging and remote protection activation. Stable release remains a separate future maintainer action.
- [ ] Preserve required execution rulings in the handoff and clean only this plan's ignored SDD workspace after its final review is clean, following the skill's path-safety rules.
