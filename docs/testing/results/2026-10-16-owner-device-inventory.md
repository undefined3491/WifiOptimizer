# LCD existing-installation inventory — 2026-10-16

**Result: read-only collection completed; Stage 0 and candidate validation remain open.** This supplements the [owner's earlier report](2026-10-15-owner-inventory.md), not a controlled optimization comparison or a pristine baseline.

## Collection and evidence

- Device timestamps: `2026-10-16T09:41:17.587167+00:00` to `2026-10-16T09:41:17.747073+00:00` (UTC).
- Executed the reviewed [collector](../../../scripts/collect_deck_inventory.py) from commit `1001af2410802643c6e6956536529a6eb4fcea56` through SSH standard input as ordinary user `deck` (UID 1000), using Python `3.13.5` and explicit Decky home `/home/deck/homebrew`. No collector file was written to the Deck. SSH exited `0`; no sudo was needed and no collected source reported `permission_denied`.
- Executed collector SHA-256: `e7c9daa258fe898d849f98afda370247256fe97eddc19efc756a665c2d99a0f8`.
- Raw report SHA-256: `ec6280615408a0135863a28c84f7b7712473933ab0449a86c7f367e246770fc8`. Report and execution metadata remain in ignored local `out/device/owner-lcd-stable/`; raw device reports are not committed.
- The owner established SSH access using a Bitwarden-held key and connected the computer to the Deck's router. The server key was checked against the fingerprint supplied from the Deck before authentication. Keys, fingerprints and network addresses are omitted here.
- The collector did not call plugin IPC, change configuration, reconnect WiFi, start/stop services or install/update software. The existing plugin remained running. The owner used Steam Remote Play during setup; panel visibility and other concurrent activity were not independently controlled. The snapshot is partial and non-atomic.

## Environment

| Field | Observed value / evidence limit |
| --- | --- |
| Model | DMI `Jupiter`; consistent with the owner's LCD report |
| SteamOS | `3.8.28`, build `20260922.1`, variant `steamdeck`; Stable channel remains owner-reported |
| Kernel | `6.18.50-valve2-1-neptune-618-gc7289a96b14d` |
| WiFi driver module | `rtw88_8822ce` |
| NetworkManager | `1.52.1`; service active/running |
| systemd | `257` |
| Decky | `plugin_loader.service` active/running with `KillMode=process`; running version remains unverified, separately owner-reported as `3.2.10` |
| Backend evidence | Valve config selects `wpa_supplicant`, vendor defaults contain `iwd`; `wpa_supplicant.service` active/running and `iwd.service` inactive/disabled. These observations do not independently prove the backend attached to the active NetworkManager device. |

The observed `plugin_loader` kill mode is evidence for this installation only. It does not establish updater-worker survival under other unit versions, explicit stops or future service changes.

## Installed plugin identity

Only the legacy `WiFi Optimizer` candidate directory was found. Its manifest reports `WiFi Optimizer`, package `wifi-optimizer`, version `0.11.6`; neither TMS candidate directory was present. Stored plugin update channel is `beta`, independently of the SteamOS Stable channel.

All six collected product-file hashes exactly match Git blobs at pre-fork-fixes commit `8308d18c42637b76a39353e70c1d86f3fa6ae4bc` (`e957c5b^`): `plugin.json`, `package.json`, `main.py`, `dist/index.js`, `dist/index.js.map`, and `defaults/dispatcher.sh.tmpl`. At audited fork product baseline `e957c5b`, the manifest, package and template still match, while the backend and both bundle files differ. This establishes equality of those observed files; it does not prove the installation's source commit, authenticity, other files or running in-memory code. The fork's corrected update URLs have not been validated on this device.

## Stored intent and observed state

Stored flags enable disabled power save, wake reapply, BSSID lock, buffer tuning, CAKE and disabled IPv6; `priority_set=true`. Band preference and DNS changes are disabled. Stored band is `a`, DNS provider `cloudflare` and `supports_6ghz=false`. These are actual stored fields, not defaults merged by the collector.

| Observation | Collected value |
| --- | --- |
| WiFi power save | `off` |
| Qdisc / transmit queue | `cake`; queue length `256` (qdisc options not collected) |
| Runtime power control | `on` |
| PCIe power fields | Present L1/L1.1/L1.2 ASPM and L1.1/L1.2 PCIPM fields are `0`; L0s field absent |
| Driver parameters | `rtw88_core.disable_lps_deep=Y`, `rtw88_pci.disable_aspm=Y` |
| Buffer maxima | `rmem_max=wmem_max=16777216` |
| Buffer defaults | `rmem_default=wmem_default=1048576` |
| Network processing | `netdev_max_backlog=5000`, `netdev_budget=600`, `netdev_budget_usecs=8000` |
| TCP slow start after idle | `0` |
| Active recorded WiFi profile | Autoconnect enabled, priority `100`, band unrestricted, no BSSID value, automatic IPv4/DNS, no explicit DNS values, IPv6 disabled |
| Second, inactive recorded profile | Autoconnect enabled, priority `100`, band `a`, no BSSID value, automatic IPv4/DNS, no explicit DNS values, IPv6 disabled |
| Persistence files | Optimizer dispatcher, NetworkManager config and modprobe config present; generic optimizer backend override absent |

Both observed profiles lacked a BSSID value despite the stored lock flag. This is an observation to reconcile, not a controlled reproduction or proof of a particular cause. Profile aliases omit identity; collection alone does not establish ownership of every changed value or reconstruct previous settings. The already running plugin, external tools or earlier operations may have affected them.

## Remaining work

1. Confirm the running Decky version and effective backend through suitable read-only runtime evidence; capture AP/router, workload, power and other comparison conditions before experiments.
2. Preserve private recoverable configuration and approve the restoration contract before changing settings. This filtered report is not a backup, and current Reset/Uninstall cannot be assumed to restore pre-plugin state.
3. Correct and review the open findings, then validate a named candidate with individual-option, reconnect, sleep/wake, recovery and delivery tests under the [device protocol](../steam-deck-lcd-stable.md).

No performance, battery, reconnect, sleep/wake, rollback or candidate-install test was performed. Observing enabled tweaks does not establish their benefit or whether SteamOS fixes make them redundant. All 14 Important and 9 Minor static findings remain open; first Stable and Connection Watchdog remain gated by Stage 0.
