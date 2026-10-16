"""Isolated ST0-011 repair-drift tests (red first, then green).

Never import the real root plugin; never execute real setters, lifecycle,
installer or dispatcher code. Pattern: tests/test_truthful_results.py
(AST-extract + fail-closed builtins + in-memory fs).

The fixture execs repair_drifted, the drift selection/formula helpers,
get_status and the setters repair calls against scriptable stubs: _run_cmd
with stateful defaults plus a run_calls log, scripted
_get_wifi_interface / _get_active_connection_uuid, in-memory
settings/snapshot, and a time.sleep no-op.

Spec: docs/superpowers/specs/2026-10-16-st0-ui-intent-design.md (D1/D2).
"""

import ast
import io
import json
import unittest
from pathlib import Path
from types import SimpleNamespace

UUID_A = "UUID-A-1111"
UUID_B = "UUID-B-2222"
IFACE = "wlan0"
LINK_BSSID = "AA:BB:CC:DD:EE:FF"
FIXED_TIME = 1234567890
EXPECTED_DNS = "1.1.1.1 1.0.0.1"

SOURCE = Path(__file__).resolve().parents[1] / "main.py"
BACKEND_TS = Path(__file__).resolve().parents[1] / "src" / "backend.ts"

METHOD_NAMES = {
    "repair_drifted",
    "_select_drift_repairs",
    "_compute_drift_flags",
    "_parse_dns_ips",
    "_is_dns_drifted",
    "get_status",
    "set_power_save",
    "set_auto_fix",
    "set_bssid_lock",
    "set_band_preference",
    "set_dns",
    "set_ipv6",
    "set_buffer_tuning",
    "set_cake",
    "reapply_all",
    "_hard_reconnect",
    "_resolve_uuid",
    "_require_wifi",
    "_clear_transferred_profile",
    "_unexpected_response",
    "_capture_slot",
    "_restore_slot",
    "_apply_driver_fixes",
    "_apply_pcie_aspm_fix",
    "_install_dispatcher",
    "_remove_dispatcher",
    "_get_cake_status",
    "_get_support_tier",
    "_read_desired_backend",
    "_read_effective_backend",
}

MODULE_FUNCS = {
    "_load_settings",
    "_save_settings",
    "_save_settings_with_timestamp",
    "_load_snapshot",
    "_save_snapshot",
}

ASSIGN_NAMES = {
    "DEFAULT_SETTINGS",
    "SYSCTL_PARAMS",
    "SYSCTL_DEFAULTS",
    "DNS_PROVIDERS",
    "DRIVER_PROFILES",
    "DISPATCHER_PATH",
    "NM_CONF_PATH",
    "MODPROBE_CONF_PATH",
    "GENERIC_BACKEND_CONF",
    "WIFI_BACKEND_CONF",
    "NM_DEFAULT_CONF",
    "BAZZITE_IWD_CONF",
    "SETTINGS_FILE",
    "ENFORCED_FILE",
    "SNAPSHOT_FILE",
}

CUSTOM_SYSCTL = {  # foreign custom values, distinct per key
    "net.core.rmem_max": "70001",
    "net.core.wmem_max": "70002",
    "net.core.rmem_default": "70003",
    "net.core.wmem_default": "70004",
    "net.core.netdev_max_backlog": "70005",
    "net.core.netdev_budget": "70006",
    "net.core.netdev_budget_usecs": "70007",
    "net.ipv4.tcp_slow_start_after_idle": "70008",
}

PCIE_DEVICE = "/sys/devices/pci0000:00/0000:00:14.3"
SEED_QDISC = "qdisc cake 8001: root refcnt 2 unlimited diffserv4 nat ack-filter"


def _ok(stdout=""):
    return {"success": True, "stdout": stdout, "stderr": "", "returncode": 0}


def _fail(stderr="simulated failure"):
    return {"success": False, "stdout": "", "stderr": stderr, "returncode": 1}


class _MemWriter(io.StringIO):
    """Commit-on-close in-memory write buffer for the stub filesystem."""

    def __init__(self, fixture, path):
        super().__init__()
        self._fixture = fixture
        self._path = path

    def close(self):
        if not self.closed:
            self._fixture.fs[self._path] = self.getvalue()
            self._fixture.write_counts[self._path] = (
                self._fixture.write_counts.get(self._path, 0) + 1
            )
        super().close()


class RepairFixture:
    """AST-extracted plugin methods over scriptable in-memory stubs."""

    def __init__(self):
        self.iface = IFACE
        self.active_uuid = UUID_A
        self.link_bssid = LINK_BSSID
        self.power_save_off = False
        self.sysctl = dict(CUSTOM_SYSCTL)
        self.txq = {IFACE: "3000"}
        self.qdisc_output = ""
        self.nm_profiles = {}
        self.live_dns = "IP4.DNS[1]:9.9.9.9"
        self.nmcli_fail_keys = set()
        self.nmcli_fail_pairs = set()
        self.nmcli_fail_uuid = None
        self.nmcli_stderr = "simulated nmcli failure"
        self.radio_off_ok = True
        self.radio_on_ok = True
        self.con_up_ok = True
        self.verify_sequence = []
        self.sysctl_fail_keys = set()
        self.pcie_present = True
        self.pcie_device = PCIE_DEVICE
        self.backend_available = False
        self.backend_current = None
        self.fs = {}
        self.dirs = set()
        self.info_logs = []
        self.error_logs = []
        self.run_calls = []
        self.nmcli_calls = []
        self.sleep_calls = []
        self.remove_calls = []
        self.chmod_calls = []
        self.write_counts = {}
        self.run_script = []

        tree = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
        plugin = next(
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "Plugin"
        )
        # Lenient extraction (no hard presence assert): pre-change main.py
        # lacks repair_drifted + helpers, so this file imports clean on any
        # baseline and behavior tests fail on assertIn (AssertionError).
        found_methods = [
            node
            for node in plugin.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name in METHOD_NAMES
        ]
        self.present_methods = {node.name for node in found_methods}
        self.missing_methods = set(METHOD_NAMES) - self.present_methods

        top_assigns = []
        for node in tree.body:
            if isinstance(node, ast.Assign):
                top_assigns.append(node)
            elif isinstance(node, ast.Try):
                top_assigns.extend(
                    child for child in node.body if isinstance(child, ast.Assign)
                )
        found_assigns = [
            node
            for node in top_assigns
            if any(
                isinstance(target, ast.Name) and target.id in ASSIGN_NAMES
                for target in node.targets
            )
        ]
        found_funcs = [
            node
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name in MODULE_FUNCS
        ]

        fixture = self

        def _stub_open(path, mode="r", *args, **kwargs):
            p = str(path)
            if "r" in mode and "+" not in mode:
                if p in fixture.fs:
                    return io.StringIO(fixture.fs[p])
                raise FileNotFoundError(f"isolated fs missing: {p}")
            if "w" in mode or "a" in mode or "+" in mode:
                allowed_prefixes = (
                    "/tmp/wifi-optimizer-test",
                    "/etc/NetworkManager/",
                    "/etc/modprobe.d/",
                    "/sys/",
                )
                if p in fixture.fs or p.startswith(allowed_prefixes):
                    if "a" in mode and p in fixture.fs:
                        buf = _MemWriter(fixture, p)
                        buf.write(fixture.fs[p])
                        return buf
                    return _MemWriter(fixture, p)
                raise PermissionError(f"write blocked in isolated fixture: {p}")
            raise ValueError(f"unsupported mode in isolated fixture: {mode}")

        def _isfile(path):
            return str(path) in fixture.fs

        def _isdir(path):
            p = str(path)
            if p in fixture.dirs:
                return True
            if fixture.pcie_present and p in (
                fixture.pcie_device,
                fixture.pcie_device + "/link",
            ):
                return True
            return False

        def _realpath(path):
            p = str(path)
            if p == f"/sys/class/net/{fixture.iface}/device":
                return fixture.pcie_device
            return p

        def _makedirs(path, exist_ok=False):
            fixture.dirs.add(str(path))

        def _remove(path):
            fixture.remove_calls.append(str(path))
            try:
                del fixture.fs[str(path)]
            except KeyError:
                raise FileNotFoundError(f"isolated fs missing: {path}")

        def _replace(src, dst):
            fixture.fs[str(dst)] = fixture.fs.pop(str(src))

        def _chmod(path, mode):
            fixture.chmod_calls.append((str(path), mode))

        os_stub = SimpleNamespace(
            path=SimpleNamespace(
                isfile=_isfile,
                isdir=_isdir,
                join=__import__("posixpath").join,
                dirname=__import__("posixpath").dirname,
                basename=__import__("posixpath").basename,
                realpath=_realpath,
            ),
            makedirs=_makedirs,
            remove=_remove,
            replace=_replace,
            chmod=_chmod,
            access=lambda path, mode: False,
            listdir=lambda path: [],
            getmtime=lambda path: 0,
            environ={},
        )

        namespace = {
            "__builtins__": {
                "dict": dict,
                "list": list,
                "str": str,
                "int": int,
                "bool": bool,
                "float": float,
                "len": len,
                "tuple": tuple,
                "set": set,
                "isinstance": isinstance,
                "range": range,
                "enumerate": enumerate,
                "any": any,
                "all": all,
                "getattr": getattr,
                "hasattr": hasattr,
                "open": _stub_open,
                "Exception": Exception,
                "ValueError": ValueError,
                "RuntimeError": RuntimeError,
                "AttributeError": AttributeError,
                "KeyError": KeyError,
                "TypeError": TypeError,
                "FileNotFoundError": FileNotFoundError,
                "PermissionError": PermissionError,
                "OSError": OSError,
            },
            "decky": SimpleNamespace(
                logger=SimpleNamespace(
                    info=lambda *args, **kwargs: fixture.info_logs.append(
                        " ".join(str(a) for a in args)
                    ),
                    error=lambda *args, **kwargs: fixture.error_logs.append(
                        " ".join(str(a) for a in args)
                    ),
                ),
                DECKY_PLUGIN_VERSION="0.0.0-test",
                DECKY_PLUGIN_SETTINGS_DIR="/tmp/wifi-optimizer-test",
                DECKY_PLUGIN_DIR="/tmp/wifi-optimizer-test",
            ),
            "os": os_stub,
            "open": _stub_open,
            "json": json,
            "time": SimpleNamespace(
                sleep=lambda seconds: fixture.sleep_calls.append(seconds),
                time=lambda: FIXED_TIME,
            ),
        }
        exec(
            compile(
                ast.Module(
                    body=[*found_assigns, *found_funcs, *found_methods],
                    type_ignores=[],
                ),
                str(SOURCE),
                "exec",
            ),
            namespace,
        )
        self.ns = namespace
        self.SETTINGS_FILE = namespace["SETTINGS_FILE"]
        self.SNAPSHOT_FILE = namespace["SNAPSHOT_FILE"]
        self.GENERIC_BACKEND_CONF = namespace["GENERIC_BACKEND_CONF"]
        self.SYSCTL_PARAMS = dict(namespace["SYSCTL_PARAMS"])
        self.DEFAULT_SETTINGS = dict(namespace["DEFAULT_SETTINGS"])

        self.plugin = type(
            "IsolatedRepairPlugin",
            (),
            {name: namespace[name] for name in self.present_methods},
        )()
        self.plugin._run_cmd = self._stub_run_cmd
        self.plugin._nmcli_modify = self._stub_nmcli_modify
        self.plugin._get_wifi_interface = lambda: self.iface
        self.plugin._get_active_connection_uuid = lambda: self.active_uuid
        self.plugin._has_backend_tool = lambda: self.backend_available
        self.plugin._get_current_backend = lambda: self.backend_current
        self.seed_settings()

    # ---- seed/read helpers ----

    def seed_settings(self, **overrides):
        merged = dict(self.DEFAULT_SETTINGS)
        merged.update(overrides)
        self.fs[self.SETTINGS_FILE] = json.dumps(merged)

    def get_settings(self):
        return self.ns["_load_settings"]()

    def settings_writes(self):
        return self.write_counts.get(self.SETTINGS_FILE, 0)

    def radio_calls(self):
        return [
            cmd
            for cmd in self.run_calls
            if cmd[:3] == ["/usr/bin/nmcli", "radio", "wifi"]
            or cmd[1:3] == ["con", "up"]
        ]

    def make_healthy(self, **overrides):
        """Seed every flag enabled with owners and matching live state."""
        base = dict(
            power_save_disabled=True,
            auto_fix_on_wake=True,
            bssid_lock_enabled=True,
            bssid_lock_value=LINK_BSSID,
            bssid_lock_connection_uuid=UUID_A,
            band_preference_enabled=True,
            band_preference="a",
            band_owner_uuid=UUID_A,
            dns_enabled=True,
            dns_provider="cloudflare",
            dns_servers=EXPECTED_DNS,
            dns_owner_uuid=UUID_A,
            ipv6_disabled=True,
            ipv6_owner_uuid=UUID_A,
            buffer_tuning_enabled=True,
            cake_enabled=True,
        )
        base.update(overrides)
        self.seed_settings(**base)
        self.power_save_off = True
        self.sysctl = dict(self.SYSCTL_PARAMS)
        self.qdisc_output = SEED_QDISC
        self.nm_profiles[UUID_A] = {
            "802-11-wireless.bssid": LINK_BSSID,
            "802-11-wireless.band": "a",
            "ipv6.method": "disabled",
            "ipv4.dns": EXPECTED_DNS,
            "ipv4.ignore-auto-dns": "yes",
        }
        self.live_dns = "IP4.DNS[1]:1.1.1.1\nIP4.DNS[2]:1.0.0.1"

    # ---- stubs ----

    def _stub_run_cmd(self, cmd, timeout=5, clean_env=False):
        self.run_calls.append(list(cmd))
        cmd = list(cmd)
        for pred, res in self.run_script:
            if pred(list(cmd)):
                return res(list(cmd)) if callable(res) else dict(res)
        if cmd[0] == "/usr/bin/nmcli":
            if cmd[1:4] == ["radio", "wifi", "off"]:
                return _ok("")
            if cmd[1:4] == ["radio", "wifi", "on"]:
                return _ok("")
            if cmd[1:3] == ["con", "up"]:
                return _ok("") if self.con_up_ok else _fail("activation failed")
            if "-f" in cmd:
                field = cmd[cmd.index("-f") + 1]
                rest = cmd[cmd.index("-f") + 2 :]
                if rest[:2] == ["con", "show"] and "--active" in rest:
                    if self.verify_sequence:
                        entry = self.verify_sequence.pop(0)
                        if entry is None:
                            return _ok("")
                        return _ok(f"{entry}:802-11-wireless")
                    if self.active_uuid:
                        return _ok(f"{self.active_uuid}:802-11-wireless")
                    return _ok("")
                if rest[:2] == ["con", "show"] and "uuid" in rest:
                    uuid = rest[rest.index("uuid") + 1]
                    value = self.nm_profiles.get(uuid, {}).get(field, "")
                    if field == "802-11-wireless.bssid" and value:
                        value = value.replace(":", "\\:")
                    return _ok(f"{field}:{value}")
                if rest[:2] == ["dev", "show"]:
                    if field == "IP4.ADDRESS":
                        return _ok("IP4.ADDRESS[1]:192.168.1.100/24")
                    if field == "IP4.DNS":
                        return _ok(self.live_dns)
                    return _ok("")
            return _ok("")
        if cmd[0] == "/usr/bin/iw":
            sub = cmd[3:]
            if sub == ["get", "power_save"]:
                return _ok(
                    f"Power save: {'off' if self.power_save_off else 'on'}"
                )
            if sub[:2] == ["set", "power_save"]:
                self.power_save_off = sub[2] == "off"
                return _ok("")
            if sub == ["link"]:
                if self.link_bssid:
                    return _ok(
                        f"Connected to {self.link_bssid} (on {self.iface})\n"
                        "\tsignal: -50 dBm"
                    )
                return _ok("Not connected.")
            if sub == ["info"]:
                return _ok(
                    "Interface wlan0\n"
                    "\tchannel 36 (5180 MHz), width: 80 MHz, center1: 5210 MHz"
                )
            return _ok("")
        if cmd[0] == "/usr/bin/sysctl":
            if cmd[1] == "-n" and len(cmd) == 3:
                return _ok(self.sysctl.get(cmd[2], ""))
            if cmd[1] == "-w" and len(cmd) == 3 and "=" in cmd[2]:
                key, _, value = cmd[2].partition("=")
                if key in self.sysctl_fail_keys:
                    return _fail("simulated sysctl failure")
                self.sysctl[key] = value
                return _ok(f"{key} = {value}")
            return _ok("")
        if cmd[0] == "/usr/bin/ip":
            if cmd[1:3] == ["link", "show"]:
                txq = self.txq.get(self.iface, "1000")
                return _ok(
                    f"2: {self.iface}: <BROADCAST,MULTICAST,UP,LOWER_UP> "
                    f"mtu 1500 qdisc noqueue state UP mode DORMANT group "
                    f"default qlen {txq}"
                )
            if cmd[1:3] == ["link", "set"]:
                if "txqueuelen" in cmd:
                    self.txq[cmd[3]] = cmd[cmd.index("txqueuelen") + 1]
                return _ok("")
            return _ok("")
        if cmd[0] == "/usr/bin/tc":
            if cmd[1:3] == ["qdisc", "show"]:
                return _ok(self.qdisc_output)
            if cmd[1:3] == ["qdisc", "del"]:
                self.qdisc_output = ""
                return _ok("")
            if cmd[1:3] == ["qdisc", "replace"]:
                self.qdisc_output = SEED_QDISC
                return _ok("")
            return _ok("")
        return _ok("")

    def _stub_nmcli_modify(self, uuid, key, value, timeout=5):
        self.nmcli_calls.append((uuid, key, value))
        fail_uuid = self.nmcli_fail_uuid
        uuid_match = True
        if fail_uuid is not None:
            if isinstance(fail_uuid, (set, list, tuple)):
                uuid_match = uuid in fail_uuid
            else:
                uuid_match = uuid == fail_uuid
        pair_match = (key, value) in self.nmcli_fail_pairs
        if (key in self.nmcli_fail_keys or pair_match) and uuid_match:
            return {
                "success": False,
                "stdout": "",
                "stderr": self.nmcli_stderr,
                "returncode": 1,
            }
        self.nm_profiles.setdefault(uuid, {})[key] = value
        return {"success": True, "stdout": "", "stderr": "", "returncode": 0}


class RepairDriftTests(unittest.IsolatedAsyncioTestCase):
    def fixture(self, **overrides):
        f = RepairFixture()
        if overrides:
            f.seed_settings(**overrides)
        return f

    async def test_repair_only_enabled_and_drifted(self):
        f = self.fixture()
        self.assertIn("repair_drifted", f.present_methods)
        f.make_healthy()
        # Only the band drifted; power save is healthy; IPv6 is disabled
        # in settings but live diverges (must stay untouched).
        f.nm_profiles[UUID_A]["802-11-wireless.band"] = "bg"
        f.seed_settings(
            **{**f.get_settings(), "ipv6_disabled": False, "ipv6_owner_uuid": ""},
        )
        f.nm_profiles[UUID_A]["ipv6.method"] = "auto"
        result = await f.plugin.repair_drifted()
        self.assertTrue(result["success"])
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["applied"], 1)
        self.assertEqual(list(result["results"].keys()), ["band_preference"])
        self.assertEqual(
            f.nm_profiles[UUID_A]["802-11-wireless.band"], "a"
        )
        # Disabled IPv6 left alone: flag still False, profile untouched.
        self.assertFalse(f.get_settings()["ipv6_disabled"])
        self.assertEqual(f.nm_profiles[UUID_A]["ipv6.method"], "auto")
        self.assertNotIn("ipv6", result["results"])

    async def test_repair_leaves_disabled_alone(self):
        f = self.fixture()
        self.assertIn("repair_drifted", f.present_methods)
        f.seed_settings(
            power_save_disabled=False,
            auto_fix_on_wake=False,
            bssid_lock_enabled=False,
            band_preference_enabled=False,
            dns_enabled=False,
            ipv6_disabled=False,
            buffer_tuning_enabled=False,
            cake_enabled=False,
        )
        # Live state looks drifted everywhere, but nothing is enabled.
        f.power_save_off = False
        f.sysctl = dict(CUSTOM_SYSCTL)
        f.qdisc_output = ""
        writes_before = f.settings_writes()
        result = await f.plugin.repair_drifted()
        self.assertTrue(result["success"])
        self.assertEqual(result["total"], 0)
        self.assertEqual(result["results"], {})
        self.assertEqual(f.nmcli_calls, [])
        self.assertEqual(f.radio_calls(), [])
        self.assertEqual(f.settings_writes(), writes_before)

    async def test_repair_no_radio_for_healthy(self):
        f = self.fixture()
        self.assertIn("repair_drifted", f.present_methods)
        f.make_healthy()
        writes_before = f.settings_writes()
        result = await f.plugin.repair_drifted()
        self.assertTrue(result["success"])
        self.assertEqual(result["total"], 0)
        self.assertEqual(f.radio_calls(), [])
        self.assertEqual(f.nmcli_calls, [])
        self.assertEqual(f.settings_writes(), writes_before)

    async def test_repair_total_zero_message(self):
        f = self.fixture()
        self.assertIn("repair_drifted", f.present_methods)
        f.make_healthy()
        result = await f.plugin.repair_drifted()
        self.assertEqual(
            result,
            {
                "success": True,
                "total": 0,
                "applied": 0,
                "results": {},
                "message": "No drifted settings",
            },
        )

    async def test_repair_unknown_owner_fails_child_only(self):
        f = self.fixture()
        self.assertIn("repair_drifted", f.present_methods)
        f.make_healthy(
            bssid_lock_connection_uuid="",
            power_save_disabled=True,
        )
        # BSSID enabled without an owner and drifted; power save drifted.
        f.nm_profiles[UUID_A]["802-11-wireless.bssid"] = ""
        f.power_save_off = False
        result = await f.plugin.repair_drifted()
        self.assertFalse(result["success"])
        self.assertEqual(result["total"], 2)
        self.assertEqual(result["applied"], 1)
        self.assertEqual(
            result["results"]["bssid_lock"]["error"], "unknown_owner"
        )
        self.assertFalse(result["results"]["bssid_lock"]["success"])
        self.assertTrue(result["results"]["power_save"]["success"])
        # The contained failure never triggers a radio cycle.
        self.assertEqual(f.radio_calls(), [])

    async def test_repair_backend_drift_excluded(self):
        f = self.fixture()
        self.assertIn("repair_drifted", f.present_methods)
        self.assertIn("get_status", f.present_methods)
        f.make_healthy()
        f.backend_available = True
        f.fs[f.GENERIC_BACKEND_CONF] = "[main]\nwifi.backend=iwd\n"
        status = await f.plugin.get_status()
        self.assertTrue((status.get("drift") or {}).get("backend"))
        result = await f.plugin.repair_drifted()
        self.assertTrue(result["success"])
        self.assertEqual(result["total"], 0)
        self.assertEqual(result["message"], "No drifted settings")
        self.assertNotIn("backend", result["results"])
        self.assertEqual(f.radio_calls(), [])

    async def test_repair_skips_auto_fix(self):
        f = self.fixture()
        self.assertIn("repair_drifted", f.present_methods)
        self.assertIn("set_auto_fix", f.present_methods)
        f.make_healthy()
        f.nm_profiles[UUID_A]["802-11-wireless.band"] = "bg"
        calls = []
        orig = f.plugin.set_auto_fix

        async def _spy(enabled):
            calls.append(enabled)
            return await orig(enabled)

        f.plugin.set_auto_fix = _spy
        result = await f.plugin.repair_drifted()
        self.assertTrue(result["success"])
        self.assertNotIn("auto_fix", result["results"])
        self.assertEqual(calls, [])

    async def test_repair_repairs_dns_drift(self):
        f = self.fixture()
        self.assertIn("repair_drifted", f.present_methods)
        f.seed_settings(
            power_save_disabled=False,
            auto_fix_on_wake=False,
            bssid_lock_enabled=False,
            band_preference_enabled=False,
            dns_enabled=True,
            dns_provider="cloudflare",
            dns_servers=EXPECTED_DNS,
            dns_owner_uuid=UUID_A,
            ipv6_disabled=False,
            buffer_tuning_enabled=False,
            cake_enabled=False,
        )
        f.live_dns = "IP4.DNS[1]:9.9.9.9"
        result = await f.plugin.repair_drifted()
        self.assertTrue(result["success"])
        self.assertEqual(list(result["results"].keys()), ["dns"])
        self.assertEqual(
            f.nm_profiles[UUID_A]["ipv4.dns"], EXPECTED_DNS
        )
        self.assertEqual(
            f.nm_profiles[UUID_A]["ipv4.ignore-auto-dns"], "yes"
        )

    async def test_dns_drift_detected(self):
        f = self.fixture()
        self.assertIn("get_status", f.present_methods)
        self.assertIn("_is_dns_drifted", f.present_methods)
        f.seed_settings(
            power_save_disabled=False,
            auto_fix_on_wake=False,
            bssid_lock_enabled=False,
            band_preference_enabled=False,
            dns_enabled=True,
            dns_provider="cloudflare",
            dns_servers=EXPECTED_DNS,
            dns_owner_uuid=UUID_A,
            ipv6_disabled=False,
            buffer_tuning_enabled=False,
            cake_enabled=False,
        )
        # Subset rule: extra live servers are fine.
        f.live_dns = "IP4.DNS[1]:1.1.1.1\nIP4.DNS[2]:1.0.0.1\nIP4.DNS[3]:9.9.9.9"
        status = await f.plugin.get_status()
        self.assertNotIn("dns", status.get("drift") or {})
        # Index prefixes and whitespace are stripped before comparing.
        f.live_dns = "IP4.DNS[1]:  1.1.1.1 \nIP4.DNS[2]:1.0.0.1"
        status = await f.plugin.get_status()
        self.assertNotIn("dns", status.get("drift") or {})
        # A missing expected server is drift.
        f.live_dns = "IP4.DNS[1]:1.1.1.1\nIP4.DNS[2]:9.9.9.9"
        status = await f.plugin.get_status()
        self.assertTrue((status.get("drift") or {}).get("dns"))
        # Empty live DNS is drift.
        f.live_dns = ""
        status = await f.plugin.get_status()
        self.assertTrue((status.get("drift") or {}).get("dns"))
        # Disabled DNS never drifts.
        f.seed_settings(
            **{**f.get_settings(), "dns_enabled": False},
        )
        status = await f.plugin.get_status()
        self.assertNotIn("dns", status.get("drift") or {})
        # Disconnected DNS never drifts.
        f.seed_settings(
            **{**f.get_settings(), "dns_enabled": True},
        )
        f.iface = None
        f.active_uuid = None
        status = await f.plugin.get_status()
        self.assertFalse(status["connected"])
        self.assertNotIn("dns", status.get("drift") or {})

    async def test_selection_is_read_only(self):
        f = self.fixture()
        self.assertIn("_select_drift_repairs", f.present_methods)
        self.assertIn("_compute_drift_flags", f.present_methods)
        f.make_healthy()
        f.nm_profiles[UUID_A]["802-11-wireless.band"] = "bg"
        writes_before = f.settings_writes()
        nmcli_before = list(f.nmcli_calls)
        run_before = len(f.run_calls)
        selected = await f.plugin._select_drift_repairs()
        self.assertEqual(selected, ["band_preference"])
        # Selection performs zero settings writes and zero profile modifies.
        self.assertEqual(f.settings_writes(), writes_before)
        self.assertEqual(f.nmcli_calls, nmcli_before)
        # Selection is read-only: no radio cycles or activations either.
        new_calls = f.run_calls[run_before:]
        self.assertEqual(
            [
                cmd
                for cmd in new_calls
                if cmd[:3] == ["/usr/bin/nmcli", "radio", "wifi"]
                or cmd[1:3] == ["con", "up"]
            ],
            [],
        )
        # The shared formula helper is used by both get_status and repair
        # selection (no duplicated drift formulas).
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        plugin = next(
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "Plugin"
        )
        refs = {}
        for node in plugin.body:
            if (
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name in ("get_status", "_select_drift_repairs")
            ):
                refs[node.name] = any(
                    isinstance(child, ast.Attribute)
                    and child.attr == "_compute_drift_flags"
                    for child in ast.walk(node)
                )
        self.assertTrue(refs.get("get_status"), "get_status uses helper")
        self.assertTrue(
            refs.get("_select_drift_repairs"), "selection uses helper"
        )

    def test_repair_drifted_ipc_shape(self):
        # Backend method exists with zero args (besides self).
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        plugin = next(
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "Plugin"
        )
        method = next(
            (
                node
                for node in plugin.body
                if isinstance(node, ast.AsyncFunctionDef)
                and node.name == "repair_drifted"
            ),
            None,
        )
        self.assertIsNotNone(method, "Plugin.repair_drifted exists")
        arg_names = [a.arg for a in method.args.args]
        self.assertEqual(arg_names, ["self"])
        # Frontend wrapper name/shape matches exactly (no other changes).
        text = BACKEND_TS.read_text(encoding="utf-8")
        self.assertIn(
            'export const repairDrifted = callable<[], OptimizeSafeResult>("repair_drifted");',
            text,
        )


if __name__ == "__main__":
    unittest.main()
