# Stage 0 audit specification

Date: 2026-10-15. Owner direction: start the audit using `gpt-6.1-sol` reviewers and subagents. This document turns the approved [Stage 0 scope](../../audits/2026-10-15-stage-0.md) into a repeatable review contract.

## Objective and baseline

Establish what the inherited plugin changes, which failure paths can affect a player, which optimizations remain justified on current SteamOS, and what must be fixed or tested before the first fork Stable release. The audit must produce actionable findings and evidence, not a blanket quality score based on the model used.

Product-code baseline: `e957c5b49797ef456cbd8edf093eb83704aac805`, version `0.11.6`. The roadmap documentation commit `7b58d47` changes no product source or dependencies. Freeze product code during this review. Report the exact final documentation commit separately from the audited product baseline.

Primary device target: owner's Steam Deck LCD / SteamOS Stable. The [2026-10-15 owner report](../../testing/results/2026-10-15-owner-inventory.md) supplied versions and prior Optimize Safe use without perceived benefit. The [2026-10-16 inventory and runtime follow-up](../../testing/results/2026-10-16-owner-device-inventory.md) supersede its environment gaps with observed OS/build/kernel/driver, running Decky version, backend evidence, plugin file identity and existing modified state, with explicit limitations. This is not a controlled comparison or a pristine baseline. Vendor release-note versions are not installed-device evidence. Beta/Preview, OLED and other distributions receive explicitly separate coverage labels.

## Review work packages

1. **Backend state and restoration:** `main.py` helpers, settings persistence, lifecycle, hardware/backend detection, every optimization setter, status/reapply/reset/uninstall; `defaults/dispatcher.sh.tmpl`. Trace inputs, commands and writes through partial failure, disconnected operation, profile changes and concurrent entry points.
2. **Installation and updates:** `install.sh`, `main.py` update checks/application and generated shell, packaged-file expectations, release validators/workflows and dependencies. Review archive/path assumptions, shell quoting, download/version validation, interruption, backup/rollback, cleanup and success reporting.
3. **Frontend and IPC:** all `src/` source, callable signatures/types, busy/reconnect/update flows, component lifecycle and errors. Follow actual backend return shapes, panel visibility, delayed callbacks, overlapping operations and user-visible state.
4. **Platform relevance and integration:** coordinator compares each optimization against official SteamOS/NetworkManager/kernel documentation and checks interactions across the three packages. Maintain retain/constrain/change/remove decisions, distinguishing code correctness from unmeasured benefit.

All reviewers use `gpt-6.1-sol` as selected by the owner. They receive isolated, explicit briefs, do not spawn additional agents, and review the same fixed code. Parallelism is for independent read-only investigations; source edits are excluded.

## Evidence and findings

For each candidate finding, record: reviewed commit, file and one-based line(s), affected function/flow, realistic trigger, actual code behavior, consequence, severity, evidence type, minimal correction direction, regression-test idea and device follow-up where needed.

Evidence labels: **static trace confirmed**, **isolated safe reproduction**, **device confirmed**, **hypothesis requiring device evidence**, **documented design limitation**. A static trace can establish a deterministic bug without a device; it cannot establish radio performance, battery cost or actual SteamOS compatibility. Safe reproductions must describe their limits and must not be presented as execution of the plugin on a Deck.

Severity: **Critical** for demonstrated privileged compromise, destructive loss or a comparable severe impact; **Important** for plausible persistent configuration loss, broken installation/recovery, connection disruption, materially incorrect results or unhandled failure; **Minor** for lower-impact defects and documentation errors. Do not inflate unsupported exploitation scenarios or classify all missing measurements as bugs.

The coordinator validates reports against source, deduplicates root causes, records rejected candidates with reasons, and assigns stable `ST0-###` finding IDs. Preserve open questions and explicit coverage gaps; reviewers must list any considered behavior they declined to judge. Do not silently discard a finding merely because it predates the fork.

## Constraints

- Never import/execute the backend, call setters/lifecycle/status, run installer/dispatcher or issue network/system mutations on Windows. Parse source with AST and use shell syntax-only validation. Existing delivery tests are safe with Git Bash available.
- No device connection, installation, backend change, reset, OS-channel switch, release publication or repository-protection activation during this static review.
- Source, dependencies, package version, tracked dist and runtime behavior stay unchanged. Confirmed fixes get scoped implementation work and regression tests after the report, rather than being mixed into the audit.
- Follow the latest owner-supplied `AGENTS.md`: working branches use `codex/<change>`, PRs target this fork's `main`, review and `ci-required` precede squash merge. This supersedes the earlier branch-name preference. Current remote state must be checked, not inferred from that older file's rollout text.
- Read-only audit work is authorized to start now. Spec/plan preparation does not authorize future product changes or certify device behavior.

## Deliverables and acceptance

- This specification and [execution plan](../plans/2026-10-15-stage-0-audit.md), linked from the current roadmap and agent instructions.
- A consolidated report at `docs/audits/2026-10-15-stage-0-findings.md`, with coverage by package, findings, dispositions, primary sources, optimization decisions and prioritized next steps.
- Documented checks actually run, plus named missing device evidence and an updated LCD / Stable test protocol.
- A reviewed documentation PR with successful CI; no version bump or Stable release from this audit.

The **static review** is complete when all four work packages have recorded coverage and every returned finding has a coordinator disposition. **Stage 0** remains open until required fixes are reviewed and the agreed device/release-candidate tests pass. Static completion alone must never clear the first-Stable gate.
