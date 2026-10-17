# clean_env call-site audit (S-BE-06 mechanism fix)

Date: 2026-10-17. Baseline: `5d48ded` (main); audited file `main.py` unchanged
since baseline except the D1 default flip (`clean_env: bool = False` →
`True` at `main.py:271`). Line numbers below are post-flip (the flip shifts
no lines; it edits one default on line 271).

Method: AST walk of `main.py` — every `Call` node whose `func` is the
attribute `_run_cmd` (direct `self._run_cmd(...)` sites), plus every
`asyncio.to_thread(self._run_cmd, ...)` wrapper (flag passed positionally
as the 4th overall argument). No `clean_env=False` exists in either form
(keyword or positional, direct or wrapper); that absence is enforced by
`tests/test_clean_env.py::test_no_unjustified_false_opt_outs`.

Result: 61/61 direct sites inherit the safe default; 14/14 wrapper sites
carry an explicit positional `True` (kept deliberately — defense in depth
at the highest-risk sites AND required by
`scripts/check_delivery.py:388-395`, which asserts the literal for the
updater paths).

## Direct call sites (61)

- `main.py:315` → `/usr/bin/nmcli` (`dev status`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:327` → `/usr/bin/nmcli` (`con show --active`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:401` → `/usr/bin/systemctl` (`is-active`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:410` → `/usr/bin/systemctl` (`is-enabled`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:522` → `/usr/bin/sysctl` (`-n`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:531` → `/usr/bin/ip` (`link show`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:554` → `/usr/bin/tc` (`qdisc show`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:565` → `/usr/bin/iw` (`get power_save`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:651` → `/usr/bin/systemctl` (service op) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:668` → `/usr/bin/nmcli` (`con show uuid`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:723` → `/usr/bin/sysctl` (`-w`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:737` → `/usr/bin/ip` (`link set txqueuelen`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:762` → `/usr/bin/tc` (`qdisc del`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:775` → `/usr/bin/tc` (`qdisc replace`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:791` → `/usr/bin/iw` (`set power_save`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:907` → `/usr/bin/nmcli` (`radio wifi off`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:908` → `/usr/bin/nmcli` (`radio wifi on`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:911` → `/usr/bin/nmcli` (`con up uuid`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:938` → `/usr/bin/nmcli` (`con show --active` poll) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:1295` → `/usr/bin/sysctl` (`-w` uninstall) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:1316` → `/usr/bin/tc` (`qdisc del` uninstall) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:1336` → `/usr/bin/ip` (`link set txqueuelen 1000` uninstall) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:1528` → `/usr/bin/nmcli` (`con mod`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:1657` → `/usr/bin/iw` (`dev`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:1658` → `/usr/bin/iw` (`reg get`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:1659` → `/usr/bin/uname` (`-r`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:1815` → `/usr/bin/iw` (`get power_save`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:1822` → `/usr/bin/nmcli` (`802-11-wireless.bssid`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:1843` → `/usr/bin/nmcli` (`IP4.DNS`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:1849` → `/usr/bin/nmcli` (`ipv6.method`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:1867` → `/usr/bin/nmcli` (`802-11-wireless.band`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:1887` → `/usr/bin/sysctl` (`-n`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:1989` → `/usr/bin/iw` (`get power_save`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:1996` → `/usr/bin/iw` (`dev link`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:2016` → `/usr/bin/iw` (`dev info`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:2042` → `/usr/bin/nmcli` (`802-11-wireless.bssid`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:2065` → `/usr/bin/nmcli` (`IP4.ADDRESS`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:2076` → `/usr/bin/nmcli` (`IP4.DNS`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:2083` → `/usr/bin/nmcli` (`ipv6.method`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:2101` → `/usr/bin/nmcli` (`802-11-wireless.band`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:2123` → `/usr/bin/sysctl` (`-n`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:2201` → `/usr/bin/iw` (`set power_save`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:2283` → `/usr/bin/iw` (`set power_save on`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:2471` → `/usr/bin/iw` (`dev link`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:2707` → `/usr/bin/iw` (`dev link`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:3178` → `/usr/bin/sysctl` (`-w`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:3214` → `/usr/bin/sysctl` (`-w`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:3239` → `/usr/bin/ip` (`link set txqueuelen`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:3252` → `/usr/bin/ip` (`link set txqueuelen 256`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:3275` → `/usr/bin/ip` (`link set txqueuelen 1000`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:3308` → `/usr/bin/tc` (`qdisc show`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:3344` → `/usr/bin/modprobe` (fallback `/usr/sbin/modprobe`, `sch_cake`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:3345` → `/usr/bin/tc` (`qdisc replace ... cake`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:3358` → `/usr/bin/ip` (`link set txqueuelen 256`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:3381` → `/usr/bin/tc` (`qdisc del`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:3405` → `/usr/bin/ip` (`link set txqueuelen 2000`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:3427` → `/usr/bin/ip` (`link set txqueuelen 1000`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:3754` → `/usr/bin/sysctl` (`-w` reset) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:3776` → `/usr/bin/tc` (`qdisc del` reset) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:3796` → `/usr/bin/ip` (`link set txqueuelen 1000` reset) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:3859` → `/usr/bin/iw` (`set power_save off` reset) → inherit safe default (D1); absolute-path system binary, no bundled-env need.

## `to_thread` wrapper sites (14, all explicit positional `True` — kept)

| Site | Command | Disposition |
| ---- | ------- | ----------- |
| main.py:3960 (`check_for_update`) | `/usr/bin/curl` release check | KEEP explicit `True` (D2 addendum; `check_delivery.py:388-395` requires the literal). |
| main.py:4220 (`_update_worker`) | `curl_cmd` archive download | KEEP explicit `True` (D2 addendum; `check_delivery.py:388-395` requires the literal). |
| main.py:4343 (`_update_worker`) | `/usr/bin/systemctl restart plugin_loader` | KEEP explicit `True`; same poisoning class as S-BE-06 (restart path, latent). |
| main.py:4427 (`_backend_switch_worker`) | `BACKEND_HELPER write_config target` | KEEP explicit `True`; helper is a system-side executable. |
| main.py:4455 (`_backend_switch_worker`) | `BACKEND_HELPER write_config rb_prev` | KEEP explicit `True`; helper is a system-side executable. |
| main.py:4461 (`_backend_switch_worker`) | `BACKEND_HELPER restart_units target` | KEEP explicit `True`; helper is a system-side executable. |
| main.py:4477 (`_backend_switch_worker`) | `rb_cmd` loop (`systemctl enable/start rb_prev`, `restart NetworkManager`) | KEEP explicit `True`; absolute-path system binaries. |
| main.py:4524 (`_backend_switch_worker`) | `BACKEND_HELPER restart_units other` | KEEP explicit `True`; helper is a system-side executable. |
| main.py:4619 (`_backend_switch_worker` repair) | `BACKEND_HELPER write_config rb_prev` | KEEP explicit `True`; helper is a system-side executable. |
| main.py:4625 (`_backend_switch_worker` repair) | `BACKEND_HELPER restart_units target` | KEEP explicit `True`; helper is a system-side executable. |
| main.py:4641 (`_backend_switch_worker` repair) | `rb_cmd` loop (`systemctl enable/start rb_prev`, `restart NetworkManager`) | KEEP explicit `True`; absolute-path system binaries. |
| main.py:4778 (`_generic_backend_switch_worker`) | `cmd` loop (`systemctl stop/disable other`, `enable/start target`) | KEEP explicit `True`; absolute-path system binaries. |
| main.py:4788 (`_generic_backend_switch_worker`) | `/usr/bin/systemctl restart NetworkManager` | KEEP explicit `True`; absolute-path system binary. |
| main.py:4894 (`_generic_backend_switch_worker` rollback) | `step_cmd` loop (`systemctl enable/start prev`, `restart NetworkManager`) | KEEP explicit `True`; absolute-path system binaries. |

## Tally

Direct: nmcli 17, iw 13, ip 10, sysctl 8, tc 8, systemctl 3, uname 1,
modprobe 1 = 61/61 inherit the safe default. Wrappers: curl 2, systemctl
(incl. loop vars) 6, BACKEND_HELPER 6 = 14/14 explicit `True` kept.
`clean_env=False`: 0 in both keyword and positional forms.
