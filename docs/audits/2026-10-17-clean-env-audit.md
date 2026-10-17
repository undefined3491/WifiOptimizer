# clean_env call-site audit (S-BE-06 mechanism fix)

Date: 2026-10-17. Baseline: `5d48ded` (main); audited file `main.py` unchanged
since baseline except the D1 default flip (`clean_env: bool = False` →
`True` at `main.py:271`). Line numbers below are post-flip (the flip shifts
no lines; it edits one default on line 271).

Method: AST walk of `main.py` — every `Call` node whose `func` is the
attribute `_run_cmd` (direct `self._run_cmd(...)` sites), plus every
`asyncio.to_thread(self._run_cmd, ...)` wrapper (flag passed positionally
as the 4th overall argument). Line numbers below are post docstring
generalization (docstring edit shifted post-277 lines by +2; verified by
`test_call_site_count_matches_audit`). No `clean_env=False` exists in either form
(keyword or positional, direct or wrapper); that absence is enforced by
`tests/test_clean_env.py::test_no_unjustified_false_opt_outs`.

Result: 61/61 direct sites inherit the safe default; 14/14 wrapper sites
carry an explicit positional `True` (kept deliberately — defense in depth
at the highest-risk sites AND required by
`scripts/check_delivery.py:388-395`, which asserts the literal for the
updater paths).

## Direct call sites (61)

- `main.py:317` → `/usr/bin/nmcli` (`dev status`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:329` → `/usr/bin/nmcli` (`con show --active`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:403` → `/usr/bin/systemctl` (`is-active`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:412` → `/usr/bin/systemctl` (`is-enabled`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:524` → `/usr/bin/sysctl` (`-n`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:533` → `/usr/bin/ip` (`link show`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:556` → `/usr/bin/tc` (`qdisc show`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:567` → `/usr/bin/iw` (`get power_save`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:653` → `/usr/bin/systemctl` (service op) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:670` → `/usr/bin/nmcli` (`con show uuid`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:725` → `/usr/bin/sysctl` (`-w`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:739` → `/usr/bin/ip` (`link set txqueuelen`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:764` → `/usr/bin/tc` (`qdisc del`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:777` → `/usr/bin/tc` (`qdisc replace`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:793` → `/usr/bin/iw` (`set power_save`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:909` → `/usr/bin/nmcli` (`radio wifi off`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:910` → `/usr/bin/nmcli` (`radio wifi on`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:913` → `/usr/bin/nmcli` (`con up uuid`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:940` → `/usr/bin/nmcli` (`con show --active` poll) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:1297` → `/usr/bin/sysctl` (`-w` uninstall) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:1318` → `/usr/bin/tc` (`qdisc del` uninstall) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:1338` → `/usr/bin/ip` (`link set txqueuelen 1000` uninstall) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:1530` → `/usr/bin/nmcli` (`con mod`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:1659` → `/usr/bin/iw` (`dev`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:1660` → `/usr/bin/iw` (`reg get`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:1661` → `/usr/bin/uname` (`-r`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:1817` → `/usr/bin/iw` (`get power_save`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:1824` → `/usr/bin/nmcli` (`802-11-wireless.bssid`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:1845` → `/usr/bin/nmcli` (`IP4.DNS`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:1851` → `/usr/bin/nmcli` (`ipv6.method`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:1869` → `/usr/bin/nmcli` (`802-11-wireless.band`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:1889` → `/usr/bin/sysctl` (`-n`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:1991` → `/usr/bin/iw` (`get power_save`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:1998` → `/usr/bin/iw` (`dev link`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:2018` → `/usr/bin/iw` (`dev info`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:2044` → `/usr/bin/nmcli` (`802-11-wireless.bssid`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:2067` → `/usr/bin/nmcli` (`IP4.ADDRESS`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:2078` → `/usr/bin/nmcli` (`IP4.DNS`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:2085` → `/usr/bin/nmcli` (`ipv6.method`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:2103` → `/usr/bin/nmcli` (`802-11-wireless.band`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:2125` → `/usr/bin/sysctl` (`-n`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:2203` → `/usr/bin/iw` (`set power_save`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:2285` → `/usr/bin/iw` (`set power_save on`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:2473` → `/usr/bin/iw` (`dev link`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:2709` → `/usr/bin/iw` (`dev link`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:3180` → `/usr/bin/sysctl` (`-w`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:3216` → `/usr/bin/sysctl` (`-w`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:3241` → `/usr/bin/ip` (`link set txqueuelen`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:3254` → `/usr/bin/ip` (`link set txqueuelen 256`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:3277` → `/usr/bin/ip` (`link set txqueuelen 1000`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:3310` → `/usr/bin/tc` (`qdisc show`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:3346` → `/usr/bin/modprobe` (fallback `/usr/sbin/modprobe`, `sch_cake`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:3347` → `/usr/bin/tc` (`qdisc replace ... cake`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:3360` → `/usr/bin/ip` (`link set txqueuelen 256`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:3383` → `/usr/bin/tc` (`qdisc del`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:3407` → `/usr/bin/ip` (`link set txqueuelen 2000`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:3429` → `/usr/bin/ip` (`link set txqueuelen 1000`) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:3756` → `/usr/bin/sysctl` (`-w` reset) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:3778` → `/usr/bin/tc` (`qdisc del` reset) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:3798` → `/usr/bin/ip` (`link set txqueuelen 1000` reset) → inherit safe default (D1); absolute-path system binary, no bundled-env need.
- `main.py:3861` → `/usr/bin/iw` (`set power_save off` reset) → inherit safe default (D1); absolute-path system binary, no bundled-env need.

## `to_thread` wrapper sites (14, all explicit positional `True` — kept)

| Site | Command | Disposition |
| ---- | ------- | ----------- |
| main.py:3962 (`check_for_update`) | `/usr/bin/curl` release check | KEEP explicit `True` (D2 addendum; `check_delivery.py:388-395` requires the literal). |
| main.py:4222 (`_update_worker`) | `curl_cmd` archive download | KEEP explicit `True` (D2 addendum; `check_delivery.py:388-395` requires the literal). |
| main.py:4345 (`_update_worker`) | `/usr/bin/systemctl restart plugin_loader` | KEEP explicit `True`; same poisoning class as S-BE-06 (restart path, latent). |
| main.py:4429 (`_backend_switch_worker`) | `BACKEND_HELPER write_config target` | KEEP explicit `True`; helper is a system-side executable. |
| main.py:4457 (`_backend_switch_worker`) | `BACKEND_HELPER write_config rb_prev` | KEEP explicit `True`; helper is a system-side executable. |
| main.py:4463 (`_backend_switch_worker`) | `BACKEND_HELPER restart_units target` | KEEP explicit `True`; helper is a system-side executable. |
| main.py:4479 (`_backend_switch_worker`) | `rb_cmd` loop (`systemctl enable/start rb_prev`, `restart NetworkManager`) | KEEP explicit `True`; absolute-path system binaries. |
| main.py:4526 (`_backend_switch_worker`) | `BACKEND_HELPER restart_units other` | KEEP explicit `True`; helper is a system-side executable. |
| main.py:4621 (`_backend_switch_worker` repair) | `BACKEND_HELPER write_config rb_prev` | KEEP explicit `True`; helper is a system-side executable. |
| main.py:4627 (`_backend_switch_worker` repair) | `BACKEND_HELPER restart_units target` | KEEP explicit `True`; helper is a system-side executable. |
| main.py:4643 (`_backend_switch_worker` repair) | `rb_cmd` loop (`systemctl enable/start rb_prev`, `restart NetworkManager`) | KEEP explicit `True`; absolute-path system binaries. |
| main.py:4780 (`_generic_backend_switch_worker`) | `cmd` loop (`systemctl stop/disable other`, `enable/start target`) | KEEP explicit `True`; absolute-path system binaries. |
| main.py:4790 (`_generic_backend_switch_worker`) | `/usr/bin/systemctl restart NetworkManager` | KEEP explicit `True`; absolute-path system binary. |
| main.py:4896 (`_generic_backend_switch_worker` rollback) | `step_cmd` loop (`systemctl enable/start prev`, `restart NetworkManager`) | KEEP explicit `True`; absolute-path system binaries. |

## Tally

Direct: nmcli 17, iw 13, ip 10, sysctl 8, tc 8, systemctl 3, uname 1,
modprobe 1 = 61/61 inherit the safe default. Wrappers: curl 2, systemctl
(incl. loop vars) 6, BACKEND_HELPER 6 = 14/14 explicit `True` kept.
`clean_env=False`: 0 in both keyword and positional forms.
