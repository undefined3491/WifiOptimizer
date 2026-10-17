# WiFi Optimizer TMS v0.11.6

Public plugin name: **WiFi Optimizer TMS**; package: **`wifi-optimizer-tms`**. The canonical GitHub repository is `undefined3491/wifi-optimizer-tms`. The technical installation/settings directory remains `WiFi Optimizer`. See the [branding stages and compatibility identifiers](docs/branding.md).

This fork is maintained at [undefined3491/wifi-optimizer-tms](https://github.com/undefined3491/wifi-optimizer-tms), based on the original [Arcada Labs project](https://github.com/ArcadaLabs-Jason/WifiOptimizer).

> **Development status:** Stage 0 is open. Network/profile changes can persist across reboots, and installation/update/reset/uninstall have unresolved audit findings. Review the [current state and next steps](docs/audits/2026-10-15-stage-0.md#start-the-next-session) and prepare recovery before changing an existing installation; a reboot is not a complete rollback.

A [Decky Loader](https://decky.xyz/) plugin exposing WiFi and network settings intended to improve game streaming, including Steam Remote Play, [Moonlight](https://moonlight-stream.org/) / [Sunshine](https://app.lizardbyte.dev/Sunshine/), Parsec and Chiaki. This fork is auditing the inherited implementation and measuring its effects on current systems.

**Hardware handling inherited from upstream:** Steam Deck (LCD and OLED), Legion Go, ROG Ally, and other PC handhelds, with SteamOS, Bazzite and CachyOS paths. This fork's runtime validation is pending; the first test target is Steam Deck LCD on SteamOS Stable. See the [audit-first roadmap](ROADMAP.md) and [current audit/compatibility record](docs/audits/2026-10-15-stage-0.md).

## The problem

WiFi power management, access-point roaming and network queue behavior can affect streaming. Settings can change across reconnects, sleep/wake and OS updates, but the behavior and useful workarounds depend on the OS, driver and network. Current SteamOS releases include relevant WiFi fixes, so this fork is reassessing the inherited optimizations against a measured baseline.

WiFi Optimizer TMS exposes these settings from Game Mode and can reapply enabled options after reconnects. Effects and tradeoffs need validation for the device and workload.

## Install / Update

[Decky Loader](https://decky.xyz/) must be installed first. Then open Desktop Mode > Konsole and run:

```bash
curl -sL https://github.com/undefined3491/wifi-optimizer-tms/raw/main/install.sh -o /tmp/wifi-opt-install.sh && sudo bash /tmp/wifi-opt-install.sh
```

This requires a user password - set one with `passwd` in Konsole if you haven't already.

Switch back to Game Mode. Open the Quick Access Menu (**...** button) > Decky > WiFi Optimizer TMS.

**Updating:** The plugin checks for updates automatically when you open it. If an update is available, an update button appears at the top of the panel - tap it and the plugin updates and restarts itself. You can also update manually by running the install command above again.

Installation and updates use this fork. The installer falls back to its `main` branch when no release is available. In-app Stable updates require a published GitHub release with a `v<version>` tag. There is no Beta channel. The command above describes the existing installer; it is not a validated migration or recovery procedure for Stage 0.

> **Note:** If you're on a version before v0.6.6, the in-app updater had bugs. Please update manually using the install command above to get working auto-updates.

## Getting started

1. Open WiFi Optimizer TMS from the Decky sidebar
2. The existing **Optimize Safe** preset applies the options below. Its name is inherited; universal benefit and battery cost are under audit. Validate individual options and recovery before testing the combined preset:
   - Disables WiFi power save and PCIe power states
   - Locks your BSSID, which also constrains access-point roaming
   - Enables auto-fix on wake (reapplies settings after sleep)
   - Tunes network buffers (handles streaming traffic bursts)
3. Enabled options are reapplied through plugin startup and the reconnect dispatcher. Verify actual state and connection behavior after sleep/wake and updates.

Want to go further? The remaining optimizations are available as individual toggles - each one has an **(i)** icon you can tap for an explanation of what it does and its tradeoffs. Advanced options include a 5 GHz band restriction, custom DNS, disabling IPv6, CAKE traffic shaping, and switching between the `iwd` and `wpa_supplicant` WiFi backends. Other open runtime findings are recorded in the [Stage 0 audit](docs/audits/2026-10-15-stage-0-findings.md).

## All optimizations

**Existing Optimize Safe preset**

| Optimization | What it does |
|---|---|
| Prevent lag spikes | Disables WiFi power management and PCIe power states, aiming to reduce power-related latency. Benefit and power cost depend on the system and workload. |
| Stop background scanning | Locks to the current access point. Disable before switching access points or when a mesh/multi-AP setup requires roaming. |
| Auto-fix on wake | Installs a script that reapplies your settings every time WiFi reconnects - works even if Decky isn't running |
| Network buffer tuning | Increases kernel buffer sizes and TX queue length. Effects on buffering, loss and latency need measurement under the target workload. |

**Manual opt-in (require configuration or have tradeoffs)**

| Optimization | What it does | Why it's manual |
|---|---|---|
| Force 5 GHz | Restricts the saved WiFi profile to the 5 GHz band | Won't connect if your network is 2.4 GHz only |
| Traffic shaping (CAKE) | Local egress qdisc ("cake unlimited ...", no bandwidth limit set). No control over other devices or external bottleneck. | Replaces your system's default qdisc; resets on reboot |
| Custom DNS | Overrides your ISP's DNS with Cloudflare, Google, Quad9, or custom servers | Requires choosing a provider |
| Disable IPv6 | Forces all traffic through IPv4 | Only helps on networks with broken IPv6 - most are fine |
| WiFi backend (iwd / wpa_supplicant) | Switches between installed NetworkManager WiFi backends. The OS version and installation history determine the default; detect the actual backend. | Availability, sleep/wake behavior and compatibility with WPA3 or enterprise networks vary; review and test before switching |

## Hardware support

| Device | WiFi Chip | Driver | Notes |
|---|---|---|---|
| Steam Deck LCD | WiFi 5 (RTL8822CE) | rtw88 | Existing-installation inventory recorded; corrected-candidate validation pending |
| Steam Deck OLED | WiFi 6E (QCA206X) | ath11k_pci | Upstream handling; unverified in this fork |
| Legion Go (matching adapters) | WiFi 6E (MT7922) | mt7921e | Upstream handling; model/adapter coverage unverified |
| ROG Ally (matching adapters) | WiFi 6E (MT7922) | mt7921e | Upstream handling; model/adapter coverage unverified |
| Other PC handhelds | Varies | iwlwifi, etc. | Detected automatically; driver-specific fixes applied when available |

The plugin detects WiFi hardware at startup and uses driver-specific handling where implemented. Devices with unrecognized hardware can still expose shared settings such as power save, buffer tuning and BSSID lock. Available controls do not establish that a setting is beneficial or validated on that device.

## How it works

The plugin has two parts:

1. **The Decky plugin** runs in the Quick Access Menu. It applies optimizations when you toggle them and shows live status (signal, speed, frequency, channel). It reports detected drift after wake; the current repair action has an open audit finding (ST0-011), so it should not be assumed to repair only the existing settings.

2. **A NetworkManager dispatcher script** runs independently of Decky, outside of Steam. Every time your WiFi reconnects (including after sleep), it automatically reapplies the volatile settings (power save, PCIe power states, buffers, CAKE). If you uninstall the plugin, the script removes itself.

The visible panel polls status, and a plugin-level game-start listener reapplies volatile settings. The dispatcher runs on WiFi reconnects. Power-management changes have not yet had their battery impact measured in this fork; see the [device validation protocol](docs/testing/steam-deck-lcd-stable.md).

## Uninstall

**Before uninstalling:** review ST0-004/016 in the [audit report](docs/audits/2026-10-15-stage-0-findings.md) and preserve recoverable configuration under the [device protocol](docs/testing/steam-deck-lcd-stable.md). Current Reset/Uninstall write assumed defaults and remove configuration without restoring a recorded pre-plugin state; they are not a verified recovery procedure. Per-connection NetworkManager profile changes (BSSID lock, band preference, custom DNS, IPv6) can remain on saved networks. The WiFi backend choice is system-wide: Reset/Uninstall remove the generic optimizer backend override, while the SteamOS helper's backend configuration and systemd service state are left in place.

Then uninstall from Decky's plugin manager (Decky settings > WiFi Optimizer TMS > Uninstall), or manually:

```bash
rm -rf ~/homebrew/plugins/WiFi\ Optimizer
sudo rm -f /etc/NetworkManager/dispatcher.d/99-wifi-optimizer
sudo rm -f /etc/NetworkManager/conf.d/99-wifi-optimizer.conf
sudo rm -f /etc/NetworkManager/conf.d/99-wifi-optimizer-backend.conf
sudo rm -f /etc/modprobe.d/99-wifi-optimizer.conf
sudo systemctl restart plugin_loader
```

## Building from source

Requires Node.js and pnpm v9.

```bash
git clone https://github.com/undefined3491/wifi-optimizer-tms.git
cd wifi-optimizer-tms
pnpm i
pnpm run build
```

To deploy to your Deck, copy `.vscode/defsettings.json` to `.vscode/settings.json`, fill in your Deck's IP and password, then use the VS Code **builddeploy** task (Terminal > Run Task).

See [CONTRIBUTING.md](CONTRIBUTING.md) for the contribution, verification, and release workflow, [ROADMAP.md](ROADMAP.md) for planned work, and [CHANGELOG.md](CHANGELOG.md) for implemented fork changes. Stage 0 audit and device validation precede the first Stable release of this fork.

## License

BSD 3-Clause. See [LICENSE](LICENSE).
