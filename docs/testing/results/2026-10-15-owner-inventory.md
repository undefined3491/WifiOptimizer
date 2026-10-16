# Owner-reported LCD environment and prior plugin use

Recorded: 2026-10-15. Evidence: the owner's conversation reply, not command output or a controlled comparison. This is a partial inventory for the [LCD / Stable protocol](../steam-deck-lcd-stable.md); it is not a candidate-validation pass.

| Field | Owner report / remaining evidence |
| --- | --- |
| Device | Steam Deck LCD |
| SteamOS | `3.8.28`, Stable channel |
| Decky Loader | `3.2.10`; channel/build not captured |
| Plugin history | Installed/used WiFi Optimizer and ran **Optimize Safe** |
| Perceived result | No real benefit noticed by the owner |
| Plugin identity | Installed package version, commit/source and bundle identity not captured |
| System details | SteamOS build, kernel, adapter/driver, NetworkManager version and effective WiFi backend not captured |
| Current configuration | Enabled options, profile fields, dispatcher/config files and volatile settings not inventoried |
| Comparison conditions | Preset-use date, OS/Decky versions at that time, workload, router/AP setup, other changes and comparable before/after measurements not captured |

The reported lack of improvement is a subjective user observation. It is neither a measured benefit nor proof of zero effect, regression or a particular root cause. Do not treat it as a controlled result on SteamOS 3.8.28: the timing of the earlier preset use is unknown.

Prior Optimize Safe use means the current device must not be described as an untouched baseline. Persistent profile/configuration changes and a dispatcher may remain; current values and ownership need observation before recovery or further tests. Reset, uninstall or reboot alone cannot be assumed to recreate the state before plugin installation (see ST0-004/016 and the protocol).

## Next evidence to collect

1. Read-only environment and configuration inventory, including plugin version, current settings and relevant system/profile values. Do not call the plugin's mutating `get_status()` as a supposedly read-only inventory.
2. Preserve the observed configuration and review a recovery procedure before changing settings. Distinguish a snapshot of the already modified device from its unknown pre-plugin state.
3. On a reviewed, corrected candidate, compare individual options under repeatable conditions before evaluating a combined preset. Record useful outcomes for the owner's workload (for example loss, latency variation, disconnects or streaming stutter) and inconclusive/no-benefit results.

No new optimization, reset, installation, backend switch, rename deployment or runtime test was performed to produce this record. Stage 0 and all audit findings remain open.

Follow-up: the [2026-10-16 read-only device inventory and runtime evidence](2026-10-16-owner-device-inventory.md) now record installed OS/build/kernel/driver, live Decky version, evidence of the active backend, observed plugin file identity and configuration. Controlled validation remains separate from this original owner report.
