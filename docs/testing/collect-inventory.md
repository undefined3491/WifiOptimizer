# Collect the existing Deck configuration

The standalone [collector](../../scripts/collect_deck_inventory.py) supports the [LCD / Stable protocol](steam-deck-lcd-stable.md). It observes the already installed device without importing the plugin, calling its API, changing profiles, scanning WiFi, downloading anything, or starting/stopping services. The collector itself prints JSON to standard output; the shell command below saves that report locally.

## Run on the Deck

This procedure requires neither SSH nor CEF/React debugging. The [verified Decky workflow](decky-development-workflow.md) explains those complementary tools; the inventory can run directly in Konsole.

1. Copy the reviewed `scripts/collect_deck_inventory.py` file to the Deck. It does not need installation as a plugin. Open Konsole in the directory containing that file.
2. Use the actual Decky home directory. On a standard installation for the logged-in Deck user this is `$HOME/homebrew`; a custom installation needs its actual absolute path. Expand this argument in the user's shell before `sudo`; the collector does not guess a username or use root's home directory.
3. Close the WiFi Optimizer panel and avoid applying settings, starting games or deliberately reconnecting during collection. Collection does not freeze other system/plugin activity, so it is explicitly a non-atomic snapshot.
4. Run:

```bash
umask 077
sudo /usr/bin/python3 ./collect_deck_inventory.py --decky-home "$HOME/homebrew" > "$HOME/wifi-optimizer-inventory.json"
```

Sudo allows observing root-readable plugin settings/configuration; the script does not request elevated privileges itself. A run without sudo can still be useful but may report `permission_denied`. No OS channel change, Reset, Uninstall or new optimization is needed. The installed plugin keeps running; no connection/recovery behavior is tested by this command.

Inspect the report locally before sharing it. Keep it outside the Git repository; do not commit device reports automatically. If the command fails or produces an unexpected error, preserve the error and partial output rather than changing configuration to obtain a successful report. Running the collector on Windows returns `unsupported_platform` without device reads/queries; Windows unit tests use controlled fixtures instead.

## What the report means

- Captures allowlisted OS/build fields, kernel/model, NetworkManager and systemd versions, selected service states, plugin identity/file hashes, actual stored option flags, selected profile observations and current power/queue/sysctl values.
- Uses per-run interface/profile aliases. Omits SSID, BSSID/MAC, UUID, DNS/IP values, user paths, credentials, raw logs and configuration contents. It still contains device/software/configuration metadata and hashes; it is not a guarantee of anonymity.
- Marks missing/unreadable/invalid/oversized/failed/timed-out sources separately. Missing settings are not filled with the plugin's defaults. Missing flag fields mean unknown/unrecognized values, not disabled options. Collection limits expose omitted observation counts.
- A config's `wifi.backend` and service state are evidence, not proof of NetworkManager's effective backend. The report leaves effective backend and running Decky version unverified; retain the owner's version report separately until suitable runtime evidence is available.
- Plugin hashes identify observed files, not their source commit or trustworthiness. A field showing power save off or a CAKE qdisc is an observation, not evidence of benefit. Qdisc collection records selected kinds, not a full restoration description.
- This is not a settings/configuration backup or an automatic recovery script. Because identifying profile/config values are omitted, exact restoration requires separate private records and a reviewed procedure. Prior Optimize Safe use means the observed state cannot establish the device's unknown pre-plugin baseline.

## Follow-up

The first collection and separate runtime follow-up are recorded in the [device inventory](results/2026-10-16-owner-device-inventory.md). For a new evidence gap or changed system, record collection time, collector commit/hash and any concurrent reconnect/suspend or other changes. Keep raw local evidence separate from a concise reviewed result committed to `docs/testing/results/`.

Inventory output does not authorize installation, resets or live failure injection. Follow the [current correction queue](../audits/2026-10-15-stage-0-findings.md#correction-order-and-stage-0-handoff) for the next source package; the [recovery design](../superpowers/specs/2026-10-15-delivery-recovery-design.md) remains conditional later work. Candidate-specific device validation is pending.
