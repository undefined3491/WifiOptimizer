# Roadmap

Updated: 2026-10-15. Statuses describe work completed in this fork, not upstream feature claims. No delivery dates are promised.

The fork's next product goal is to make a loss of connectivity visible during gameplay without opening the Decky Quick Access Menu. Establish a reviewed and tested foundation before adding that monitoring.

## Stage 0 — Audit and establish a baseline

**Status: In progress — scope, initial observations and SteamOS release-note research recorded; full code audit and device validation pending.**

- Review the inherited Python backend, shell installer/dispatcher and React frontend, including privileged writes, error handling, reconnects, update/install recovery, reset and uninstall.
- Reassess every optimization against current SteamOS, drivers and measured behavior. Record a decision to retain, constrain, change or remove it, with evidence and tradeoffs.
- Compare the unmodified device baseline with individual optimizations on the owner's **Steam Deck LCD / SteamOS Stable**. Record exact OS, kernel, driver and Decky versions. Beta testing is an optional later compatibility exercise.
- Correct unsupported claims about universal benefit, battery cost and hardware coverage. Add regression tests for confirmed defects as fixes are made.

The first Stable release of this fork and implementation of Connection Watchdog follow Stage 0. Close this stage only after the audit covers the selected commit, all Critical/Important findings are fixed and reviewed, device results are recorded for the release candidate, and a remaining-limitations list supports the claimed hardware/OS coverage. Repeat affected checks if subsequent changes invalidate that evidence.

Scope, sources and findings: [Stage 0 audit record](docs/audits/2026-10-15-stage-0.md). Device procedure: [LCD / Stable validation](docs/testing/steam-deck-lcd-stable.md).

## Stage 1 — Connection Watchdog

**Status: Planned; depends on Stage 0.**

- Monitor independently of whether the QAM panel has ever opened. Observation must not modify network configuration or trigger reconnects.
- Distinguish loss of the WiFi link from unavailable Internet and from an unknown result. Account for suspend/resume and reconnects deliberately initiated by the plugin.
- Notify on loss and recovery. Keep a visible warning throughout a confirmed outage during gameplay.
- Prototype the persistent in-game warning on the Deck before committing to its implementation or claiming support. Decky notifications are a known building block; the persistent presentation mechanism remains unverified.
- Define detection delay, false-alarm handling and resource-budget acceptance criteria in this feature's spec. A failed request to one public endpoint alone must not be presented as proof of a total Internet outage.

## Stage 2 — Connection history

**Status: Planned.**

Record outage start/end, duration, observed cause, suspend gaps and uncertainty. Bound retention and provide diagnostic export. Record what the monitor observed; do not imply it can reconstruct outages that happened while monitoring was unavailable.

## Stage 3 — Optional diagnostics

**Status: Planned.**

Add targeted router/DNS/Internet checks, latency, jitter and packet loss when they help investigate a real problem. Keep detailed diagnostics in QAM. Evaluate Network Sentinel as an implementation reference; review any reused code and preserve its license notices.

## Stage 4 — Steam session context

**Status: Exploratory.**

Investigate reliable Steam online/offline signals and association of outages with game sessions. Restored Internet does not establish that Steam has synchronized achievements, saves or playtime. Do not promise correction of achievement timestamps or block game exit.

## Versions and delivery

Use the established [PR, CI, review and release workflow](CONTRIBUTING.md). The current package remains `0.11.6`. `0.11.7` is a possible first fork patch release after Stage 0; choose its final scope and version from the reviewed changes. A feature such as Connection Watchdog normally warrants a minor version, without resetting the existing version sequence to `0.1`.

README describes current behavior, this roadmap records future work, and CHANGELOG records implemented changes. A roadmap status never substitutes for test evidence or authorizes a Stable publication.
