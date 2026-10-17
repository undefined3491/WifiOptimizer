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
| Decky | `plugin_loader.service` active/running with `KillMode=process`; follow-up confirms running process reports `v3.2.10` (method below) |
| Backend evidence | Initial config/service observations alone were inconclusive. Follow-up supports active `wpa_supplicant` through correlated NetworkManager runtime evidence (method below). |

The observed `plugin_loader` kill mode is evidence for this installation only. It does not establish updater-worker survival under other unit versions, explicit stops or future service changes.

## Installed plugin identity

Only the legacy `WiFi Optimizer` candidate directory was found. Its manifest reports `WiFi Optimizer`, package `wifi-optimizer`, version `0.11.6`; neither TMS candidate directory was present. Stored plugin update channel is `beta`, independently of the SteamOS Stable channel. This is a pre-decision observation; the Beta channel is dropped and 'update_channel' is to be removed, with existing 'beta' values migrated to Stable.

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

## Runtime follow-up — Decky and backend

Additional bounded read-only probes ran through SSH standard input as `deck` between `09:48:21` and `09:50:50` UTC on 2026-10-16. These were separate probes, not new capabilities or a privileged rerun of the standalone collector. No device files, settings or service configuration were changed.

**Decky: running process reports `v3.2.10`.** Read `plugin_loader.service` MainPID, its direct children, a bounded prefix of their `/proc/<pid>/cmdline`, and their unit cgroups. A direct child in `plugin_loader.service` matched the `Decky Loader v3.2.10 (` prefix; MainPID was unchanged before/after. The main process itself had no matching title, consistent with the PyInstaller bootloader/child layout. Only the version match and unit membership were emitted, not the remaining command line or environment. Loader [main()](https://github.com/SteamDeckHomebrew/decky-loader/blob/v3.2.10/backend/decky_loader/main.py#L246-L259) sets this title using [get_loader_version()](https://github.com/SteamDeckHomebrew/decky-loader/blob/v3.2.10/backend/decky_loader/helpers.py#L64-L82); [PyInstaller packaging](https://github.com/SteamDeckHomebrew/decky-loader/blob/v3.2.10/backend/pyinstaller.spec#L3-L9) bundles that metadata. This confirms the living process's declared version, not a cryptographic binary attestation or a guessed version from system Python.

**Backend: correlated runtime evidence supports `wpa_supplicant` on the active WiFi interface.** NetworkManager's D-Bus device reports WiFi type `2`, managed `true`, state `100`, and `nmcli` reports that same interface connected. The `fi.w1.wpa_supplicant1` bus name has an owner; `net.connman.iwd` does not. Direct supplicant `GetInterface`/`Interfaces` reads were denied to `deck`, so failed lookups were not interpreted as absence. A bounded `sudo -n` read attempt also refused because a password was required; no elevated command ran and no password or policy change was requested.

The successful alternative read NetworkManager's current-boot journal, restricted to its current MainPID and entries after that process's `ExecMainStartTimestampMonotonic`. It matched the supplicant state messages for the same active interface. The newest matched transition was to `completed` at `09:50:08.129878` UTC; the interface was still connected and NetworkManager's PID/start identity remained unchanged at `09:50:50`. The supplicant-backed [NM 1.52.1 device implementation](https://github.com/NetworkManager/NetworkManager/blob/1.52.1/src/core/devices/wifi/nm-device-wifi.c#L2245-L2261) emits these messages; the [iwd device implementation](https://github.com/NetworkManager/NetworkManager/blob/1.52.1/src/core/devices/wifi/nm-device-iwd.c) is separate. The conclusion is an inference from correlated runtime observations, rather than configuration precedence or service existence alone. The bounded journal subset is not a complete outage history or a stability test. Raw journal messages and network identifiers were discarded on-device; only selected state transitions/timestamps were returned.

Read-only D-Bus methods/properties follow the [supplicant API](https://w1.fi/wpa_supplicant/devel/dbus.html), [NetworkManager device API](https://networkmanager.dev/docs/api/1.52.0/gdbus-org.freedesktop.NetworkManager.Device.html) and [interface lookup API](https://networkmanager.dev/docs/api/1.52.0/gdbus-org.freedesktop.NetworkManager.html). Calls used `busctl --auto-start=no` ([systemd 257 source](https://github.com/systemd/systemd/blob/v257/man/busctl.xml)) to avoid service activation. No plugin IPC, WebSocket authentication, scans, reconnects or suspend requests were used.

Probe scripts and filtered JSON remain in ignored local `out/device/owner-lcd-stable/`. SHA-256 evidence identifiers:

| Local probe stem | Script SHA-256 | Filtered result SHA-256 |
| --- | --- | --- |
| `runtime-probe` | `c9a384ad13e486ff052c39b242dac9650a4c535e059443988f7141b8c2d8868b` | `06e7e9ad4fc1c24ac77005159d0480ca0d6455ad515dc2f81b4d15b9aadb9d8d` |
| `backend-dbus-probe` | `9ba8a295c6a5f5682f78e6afaa39210a329562b22fa1974e34c58e5b5897d2dd` | `564739f9de3f290aef45793e3dd0914e190814dbfeb0012bb1aaec61c9dea898` |
| `backend-privileged-read-probe` | `0dfd88c71c1a86ac8e03eeeeb28b02814aed482523c7d95c8e0582e9e9c4259f` | `0c959a4dd7195d2a5519fcecf552f5d6a38b18cd09b39a80309c474b1f55264c` |
| `backend-corroboration-probe` | `0545b63d2f14d1f8b8443ef14570469b2e3ede2daead6304cdd7f7d02ee22fbf` | `b737a9425d4710fefcac0c684e7795ae4b91bdf56609f17f4d05438b5ebedd76` |

## Remaining work

1. Capture AP/router, workload, power and other comparison conditions before experiments. Recheck version/backend evidence when the system or candidate changes; this follow-up concerns the existing installation only.
2. Preserve private recoverable configuration and approve the restoration contract before changing settings. This filtered report is not a backup, and current Reset/Uninstall cannot be assumed to restore pre-plugin state.
3. Correct and review the open findings, then validate a named candidate with individual-option, reconnect, sleep/wake, recovery and delivery tests under the [device protocol](../steam-deck-lcd-stable.md).

No performance, battery, reconnect, sleep/wake, rollback or candidate-install test was performed. Observing enabled tweaks does not establish their benefit or whether SteamOS fixes make them redundant. At collection time all 14 Important and 9 Minor findings were open; subsequent source corrections are tracked in the [audit report](../../audits/2026-10-15-stage-0-findings.md#correction-progress--2026-10-16), not established by this inventory. First Stable and Connection Watchdog remain gated by Stage 0.
