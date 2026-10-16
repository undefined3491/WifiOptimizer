# Stage 0 Audit Execution Plan

> **For agentic workers:** This is a read-only audit plan, executed through `superpowers:dispatching-parallel-agents`. Product fixes require their own scoped plan and the normal implementation/review workflow; this plan does not implement them.

**Goal:** Produce a source-verified inherited-code audit and platform-relevance report before the first fork Stable release.

**Architecture:** Freeze the product baseline and run three independent `gpt-6.1-sol` review packages. The coordinator handles platform evidence, validates and deduplicates reports, and prepares a documentation-only PR. Device testing is a later owner-assisted phase.

**Tech Stack:** React/TypeScript, Python, Bash, NetworkManager, SteamOS; Git, AST/static inspection, existing delivery verification and primary-source documentation.

**Spec:** [Stage 0 audit specification](../specs/2026-10-15-stage-0-audit-design.md).

## Global constraints

- Product baseline `e957c5b49797ef456cbd8edf093eb83704aac805`; package `0.11.6`; no source/dependency/dist/version changes.
- Primary device target LCD / SteamOS Stable; installed versions unknown. Do not infer them from vendor news.
- Review model `gpt-6.1-sol`; isolated briefs, no nested agents, three parallel review seats plus coordinator.
- No backend import/execution, privileged operation, installation or device mutation on Windows.
- Use `codex/<change>` branches per the owner's latest instructions; this fork only; PR -> review + `ci-required` -> squash merge. Publication/protection activation remain separate.
- Agent scratch reports go only to unique ignored `out/audit-stage-0/` paths; the coordinator owns tracked report/docs changes.

## Review focus

- Pre-existing custom sysctl/qdisc/NM/backend state must survive operations according to a clearly described restoration contract; trace disable/reset/uninstall and failure paths.
- A timeout or failed reconnect must not become a false successful operation or a new saved intention silently masking the current state.
- Missing download files, interruption or an existing backup must not destroy the currently installed plugin without a recovery path.
- Concurrent status/reapply/update/user actions must not lose settings, block IPC indefinitely or leave the frontend permanently busy.
- SteamOS vendor fixes, driver capabilities and the actual active backend must be distinguished from assumptions and unmeasured performance claims.

## Task 1 — Freeze baseline and prepare audit

- [x] Read both checkout/worktree state and instructions; preserve existing roadmap documentation.
- [x] Confirm fork origin, `main` SHA and no current open PR; inspect actual remote rulesets.
- [x] Prepare specification and this plan; select `gpt-6.1-sol` for the owner-authorized audit.
- [x] Align active branch-policy references with the latest owner instructions, keeping past rollout events identifiable as history.
- [x] Record baseline tree/source identity and give each reviewer its exact package, evidence schema and report path.

## Task 2 — Independent review packages

**Files:** Inspect `main.py`, `defaults/dispatcher.sh.tmpl`, `install.sh`, all `src/`, `scripts/check_delivery.py`, `tests/test_delivery.py`, `.github/`, package/build metadata as applicable. No changes to these product/tooling files.

- [x] Backend reviewer: trace every system/profile mutation, settings/lifecycle/status/reapply path and restoration; write `out/audit-stage-0/backend.md`.
- [x] Delivery reviewer: trace installer/update shell, version/archive validation, backup/rollback and workflow/package assumptions; write `out/audit-stage-0/delivery.md`.
- [x] Frontend reviewer: inspect all source components/types/callables and user-visible asynchronous flows; write `out/audit-stage-0/frontend.md`.
- [x] Each report identifies coverage, concrete findings with line references and evidence, hypotheses, limitations and declined-to-judge items. Agents do not fix or commit code.

## Task 3 — Platform relevance and coordinator verification

- [x] Verify current official SteamOS notes, keeping Stable and Beta/Preview separate; inspect official NetworkManager/kernel documentation relevant to the implemented tuning.
- [x] For each optimization, record implementation, reported rationale, present evidence, tradeoffs, provisional retain/constrain/change/remove disposition and required device measurement.
- [x] Read all reviewer reports; verify claimed paths against source and safe isolated evidence where useful. Deduplicate shared root causes and record rejected candidates explicitly.
- [x] Run existing delivery unit tests with Git Bash on PATH, Python/Bash syntax checks and project/build/artifact verification as needed for the exact unchanged product baseline. Do not execute plugin runtime behavior.

## Task 4 — Consolidate and publish the audit record

**Files:** Create `docs/audits/2026-10-15-stage-0-findings.md`; update `docs/audits/2026-10-15-stage-0.md`, `docs/testing/steam-deck-lcd-stable.md`, `ROADMAP.md`, `AGENTS.md`, `CONTRIBUTING.md`, `CHANGELOG.md` and execution status as needed.

- [x] Assign stable finding IDs and severity/disposition; include exact audited SHA, reviewed coverage, source links, checks and missing device evidence.
- [x] Order proposed fixes by real impact and dependencies; give meaningful regression and device scenarios without implementing those fixes here.
- [x] Validate Markdown links, `git diff --check` and absence of product/dependency/version changes; obtain a fresh documentation/report review.
- [x] Publish the reviewed static audit through [PR #2](https://github.com/undefined3491/wifi-optimizer-tms/pull/2), squash merged as `7e3d45f60504aa53b17155136535006b7bf1e634`; the audit report records its baseline verification separately from runtime corrections.
- [x] Report static-review completion separately from Stage 0 closure and Stable readiness in the audit record and roadmap.

## Task 5 — Owner-assisted device phase (in progress)

Partial progress (2026-10-15): the owner reports LCD / SteamOS 3.8.28 Stable / Decky Loader 3.2.10 and prior Optimize Safe use without perceived benefit. The [inventory record](../../testing/results/2026-10-15-owner-inventory.md) lists missing evidence; environment/configuration capture and controlled tests remain incomplete.

Follow-up (2026-10-16): the [device inventory](../../testing/results/2026-10-16-owner-device-inventory.md) records exact installed OS/build/kernel/driver, runtime Decky/backend evidence and existing modified plugin/configuration. This is not a pristine baseline, recovery backup or candidate validation. [ST0-010](2026-10-16-stage-0-backend-reservation.md) was corrected separately through PR #6; the remaining findings and recovery implementation are pending.

- [x] Capture exact LCD / Stable environment and whether an older plugin is installed, then record existing configuration before installation/reset/optimization. File equality is recorded without asserting installation provenance.
- [ ] Review the recovery contract and prepare candidate fixes through scoped PRs with regression tests.
- [ ] Execute the LCD / Stable protocol on the named corrected candidate, recording actual results and limitations. Additional OS channels/hardware have separate coverage.
- [ ] Close Stage 0 only after report findings and device criteria are satisfied; prepare a first Stable release separately.

## Execution state

The owner-selected `gpt-6.1-sol` static audit and initial device inventory are complete. ST0-010 was corrected separately under its scoped plan; other fixes, recovery design selection and corrected-candidate device validation remain pending. Use the [continuation entry](../../audits/2026-10-15-stage-0.md#start-the-next-session) and [correction queue](../../audits/2026-10-15-stage-0-findings.md#correction-order-and-stage-0-handoff) for the next session. Do not repeat completed audit/collection tasks or mark Stage 0 complete from this plan or CI alone.
