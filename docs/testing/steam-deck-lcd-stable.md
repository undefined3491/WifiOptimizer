# Steam Deck LCD / SteamOS Stable validation

Status: Procedure prepared; no device results recorded. This protocol supports [Stage 0](../audits/2026-10-15-stage-0.md) and release preparation.

## Record the environment first

Capture the exact SteamOS version/build and Stable channel, kernel, WiFi adapter/driver, active NetworkManager backend, Decky Loader version/channel, plugin commit/package version and built bundle identity. Also record the AP/router setup, band, mesh/roaming requirements, power source, battery level, game/streaming workload and whether the plugin or older versions were already installed.

"Latest Decky" and "Stable SteamOS" alone are not reproducible version identifiers. Device screenshots or a read-only diagnostic inventory can supply the values; inspect diagnostic output before sharing it and omit network credentials.

## Establish baseline and recovery

1. Before installation or changing any option, record the current NM profile fields, relevant config files, services/backend, driver/sysfs power values, sysctl values and qdisc/queue settings identified by the audit. Keep recoverable copies of configuration the tests will modify.
2. Review the candidate's reset/uninstall behavior against that snapshot and prepare the exact recovery steps. Current reset/default constants are under audit; pressing Reset is not evidence of a pristine OS baseline.
3. Account for dispatcher files, saved-profile changes and other persistent state left by any existing installation. Label an already modified baseline accurately. Do not delete all profiles or change OS channel merely to obtain a baseline.
4. Start with observation under the same repeatable game/streaming workload before enabling additional tweaks. Record run duration, reconnect/disconnection events, latency variation, loss and workload-specific stutter where measurable.

## Controlled comparisons

Change one option at a time, record its actual system effect, compare with the baseline under comparable conditions, and restore the recorded prior state before the next comparison. Repeat comparable runs to distinguish an effect from normal RF variation. Record run counts/durations and inconclusive results; do not claim benefit from one favorable sample.

| Option | What to check |
| --- | --- |
| WiFi power save / driver fixes / PCIe ASPM and runtime PM | Observed values, responsiveness under load, idle behavior and comparable power observations. These are bundled by current code; document that confounder when attributing an effect. |
| BSSID lock | Same-AP stability, unlock while disconnected, saved-profile behavior and roaming requirements. Mesh/multiple-AP coverage is separate if that setup is unavailable. |
| Band preference | Reachability on the intended band, behavior when unavailable, interaction with BSSID lock and restoration. A Deck LCD result does not validate 6 GHz handling. |
| DNS / IPv6 | Existing custom settings, availability, error handling, reconnect and restoration of the intended profile fields. |
| Buffers / CAKE | Actual sysctl/qdisc/queue changes, responsiveness and loss under comparable traffic; interactions and restoration of prior configuration. |
| Backend switch | First review compatibility and recovery; then check service/config agreement, reconnect and interrupted-operation behavior. Test only installed supported backends and maintain local recovery access. |
| Existing optimization preset | Test only after individual operations and recovery are understood. Verify the combined result and reconnect behavior rather than extrapolating from individual passes. |

Measure battery impact only with comparable workload, brightness, frame limit and power conditions. If a useful comparison is unavailable, report battery impact as unmeasured.

## Lifecycle and delivery checks

On the named candidate and captured environment, record Pass/Fail/Not tested for:

- Fresh startup and startup with saved settings; panel open/closed and game launch behavior.
- WiFi off/on, loss/recovery of AP and disconnected changes to saved profiles; changing networks when the test setup allows it.
- Repeated short suspend/resume cycles and at least one longer sleep, recording cycle count and sleep/reconnect durations. Identify plugin-initiated reconnects separately from failures.
- Reset, disable and uninstall: compare actual state with the agreed restoration contract and recorded pre-test snapshot, including persistent profile/backend state and dispatcher cleanup.
- Installer and in-app update behavior using controlled test inputs/candidates, including failed download/interrupted operation and rollback. Do not publish a Stable release to create a test fixture; document any unexercised end-to-end path before audit closure.
- UI reporting, errors, partial success and responsiveness while operations run.

The current plugin has no continuous outage-warning feature. Do not mark Connection Watchdog or persistent in-game alerts as tested features of this candidate.

## Result record

Store dated results under `docs/testing/results/` when tests occur. Include the environment/candidate identifiers, baseline and recovery reference, steps and workload, measurements, expected/actual behavior, logs/screenshots where helpful, pass/fail/not-tested status, limitations and linked audit findings. Classify an unavailable scenario as untested, with an explicit disposition; it is not a pass.

The first validation target is the owner's LCD on Stable. Additional hardware and OS channels get separate records. Beta testing is optional compatibility work after the Stable baseline, and cannot replace it.
