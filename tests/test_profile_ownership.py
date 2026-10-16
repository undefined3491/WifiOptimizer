"""Isolated ST0-005/006 profile-ownership tests; never import the real plugin.

Pattern: tests/test_backend_reservation.py AST-extract + fail-closed builtins.
The fixture execs get_status/setters/_resolve_uuid/_require_wifi from main.py
against an in-memory stub namespace (no system, no filesystem, no NM).
"""

import ast
import os as _real_os
import re
import unittest
from pathlib import Path
from types import SimpleNamespace

UUID_A = "UUID-A-1111"
UUID_B = "UUID-B-2222"

METHOD_NAMES = {
    "get_status",
    "set_bssid_lock",
    "set_band_preference",
    "set_dns",
    "set_ipv6",
    "_resolve_uuid",
    "_clear_transferred_profile",
    "_require_wifi",
    "_unexpected_response",
    "_get_support_tier",
    "_get_cake_status",
}

ASSIGN_NAMES = {
    "DEFAULT_SETTINGS",
    "DRIVER_PROFILES",
    "DNS_PROVIDERS",
    "DISPATCHER_PATH",
    "ENFORCED_FILE",
}

SOURCE = Path(__file__).resolve().parents[1] / "main.py"
TEMPLATE = Path(__file__).resolve().parents[1] / "defaults" / "dispatcher.sh.tmpl"

FIXED_TIME = 1234567890
UNKNOWN_OWNER_MESSAGE = (
    "Setting is enabled but its network profile is unknown. "
    "Re-apply on the desired network."
)


def _blocked_open(*args, **kwargs):
    raise FileNotFoundError("filesystem blocked in isolated fixture")


def _ok(stdout=""):
    return {"success": False is False, "stdout": stdout, "stderr": "", "returncode": 0}


class ProfileFixture:
    """AST-extracted plugin methods over scriptable in-memory stubs."""

    def __init__(self):
        self.iface = "wlan0"
        self.active_uuid = UUID_A
        self.link_bssid = "AA:BB:CC:DD:EE:FF"
        self.power_save_off = True
        self.channel_raw = "channel 36 (5180 MHz), width: 80 MHz, center1: 5210 MHz"
        self.ip4_address = "IP4.ADDRESS[1]:192.168.1.100/24"
        self.ip4_dns = "IP4.DNS[1]:1.1.1.1"
        self.sysctl_rmem = "16777216"
        self.cake_active = False
        self.backend_available = False
        self.backend_current = None
        self.nm_profiles = {}
        self.nmcli_fail_keys = set()
        self.nmcli_stderr = "simulated nmcli failure"
        self.nmcli_calls = []
        self.run_cmd_calls = []
        self.reconnects = []
        self.sleep_calls = []
        self.save_count = 0

        tree = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
        plugin = next(
            node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Plugin"
        )
        methods = [
            node
            for node in plugin.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name in METHOD_NAMES
        ]
        assert {node.name for node in methods} == METHOD_NAMES
        assigns = sorted(
            (
                node
                for node in ast.walk(tree)
                if isinstance(node, ast.Assign)
                and any(
                    isinstance(target, ast.Name) and target.id in ASSIGN_NAMES
                    for target in node.targets
                )
            ),
            key=lambda node: node.lineno,
        )
        assert {t.id for node in assigns for t in node.targets} == ASSIGN_NAMES
        self._tree = tree

        fixture = self

        def _load_settings():
            return dict(fixture.settings)

        def _save_settings(data):
            fixture.save_count += 1
            fixture.settings = dict(data)

        def _save_settings_with_timestamp(data):
            data["last_applied"] = FIXED_TIME
            _save_settings(data)

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
                "Exception": Exception,
                "ValueError": ValueError,
                "RuntimeError": RuntimeError,
                "open": _blocked_open,
            },
            "decky": SimpleNamespace(
                logger=SimpleNamespace(
                    info=lambda *args, **kwargs: None,
                    error=lambda *args, **kwargs: None,
                ),
                DECKY_PLUGIN_VERSION="0.0.0-test",
                DECKY_PLUGIN_SETTINGS_DIR="/tmp/wifi-optimizer-test",
                DECKY_PLUGIN_DIR="/tmp/wifi-optimizer-test",
            ),
            "os": SimpleNamespace(
                path=SimpleNamespace(
                    isfile=lambda path: False,
                    join=_real_os.path.join,
                )
            ),
            "time": SimpleNamespace(
                sleep=lambda seconds: fixture.sleep_calls.append(seconds),
                time=lambda: FIXED_TIME,
            ),
            "_load_settings": _load_settings,
            "_save_settings": _save_settings,
            "_save_settings_with_timestamp": _save_settings_with_timestamp,
        }
        exec(
            compile(ast.Module(body=[*assigns, *methods], type_ignores=[]), str(SOURCE), "exec"),
            namespace,
        )
        self.settings = dict(namespace["DEFAULT_SETTINGS"])
        self.plugin = type(
            "IsolatedProfilePlugin", (), {name: namespace[name] for name in METHOD_NAMES}
        )()
        self.plugin._run_cmd = self._stub_run_cmd
        self.plugin._nmcli_modify = self._stub_nmcli_modify
        self.plugin._hard_reconnect = self._stub_hard_reconnect
        self.plugin._get_wifi_interface = lambda: self.iface
        self.plugin._get_active_connection_uuid = lambda: self.active_uuid
        self.plugin._has_backend_tool = lambda: self.backend_available
        self.plugin._get_current_backend = lambda: self.backend_current

    # ---- stubs ----

    def _stub_run_cmd(self, cmd, timeout=5, clean_env=False):
        self.run_cmd_calls.append(list(cmd))
        cmd = list(cmd)
        if cmd[0] == "/usr/bin/iw":
            sub = cmd[2 + 1:] if len(cmd) > 3 else []
            # cmd: /usr/bin/iw dev <iface> <sub...>
            sub = cmd[3:]
            if sub == ["get", "power_save"]:
                return _ok(f"Power save: {'off' if self.power_save_off else 'on'}")
            if sub == ["link"]:
                if self.link_bssid:
                    return _ok(
                        f"Connected to {self.link_bssid} (on {self.iface})\n"
                        "\tsignal: -50 dBm"
                    )
                return _ok("Not connected.")
            if sub == ["info"]:
                return _ok(f"Interface {self.iface}\n\t{self.channel_raw}")
            return _ok("")
        if cmd[0] == "/usr/bin/nmcli":
            try:
                field = cmd[cmd.index("-f") + 1]
            except (ValueError, IndexError):
                return _ok("")
            rest = cmd[cmd.index("-f") + 2:]
            if rest[:2] == ["con", "show"] and len(rest) > 3 and rest[2] == "uuid":
                uuid = rest[3]
                value = self.nm_profiles.get(uuid, {}).get(field, "")
                if field == "802-11-wireless.bssid" and value:
                    value = value.replace(":", "\\:")
                return _ok(f"{field}:{value}")
            if rest[:2] == ["dev", "show"]:
                if field == "IP4.ADDRESS":
                    return _ok(self.ip4_address)
                if field == "IP4.DNS":
                    return _ok(self.ip4_dns)
                return _ok("")
            return _ok("")
        if cmd[:3] == ["/usr/bin/sysctl", "-n", "net.core.rmem_max"]:
            return _ok(self.sysctl_rmem)
        if cmd[:3] == ["/usr/bin/tc", "qdisc", "show"]:
            if self.cake_active:
                return _ok("qdisc cake 8001: root refcnt 2 unlimited diffserv4 nat ack-filter")
            return _ok("")
        return _ok("")

    def _stub_nmcli_modify(self, uuid, key, value, timeout=5):
        self.nmcli_calls.append((uuid, key, value))
        if key in self.nmcli_fail_keys:
            return {
                "success": False,
                "stdout": "",
                "stderr": self.nmcli_stderr,
                "returncode": 1,
            }
        self.nm_profiles.setdefault(uuid, {})[key] = value
        return {"success": True, "stdout": "", "stderr": "", "returncode": 0}

    def _stub_hard_reconnect(self, uuid=None):
        self.reconnects.append(uuid)

    # ---- static source access ----

    def method_source(self, name):
        plugin = next(
            node for node in self._tree.body if isinstance(node, ast.ClassDef) and node.name == "Plugin"
        )
        node = next(
            child
            for child in plugin.body
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name == name
        )
        return ast.get_source_segment(SOURCE.read_text(encoding="utf-8"), node)


def _code_lines(path):
    return [
        (lineno, line)
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1)
        if not line.strip().startswith("#")
    ]


class ProfileOwnershipTests(unittest.IsolatedAsyncioTestCase):
    def fixture(self):
        return ProfileFixture()

    async def test_polling_B_never_writes_or_modifies(self):
        f = self.fixture()
        f.active_uuid = UUID_B
        f.settings.update(
            {
                "bssid_lock_enabled": True,
                "bssid_lock_connection_uuid": UUID_A,
                "band_preference_enabled": True,
                "band_preference": "a",
                "band_owner_uuid": UUID_A,
                "dns_enabled": True,
                "dns_owner_uuid": UUID_A,
                "ipv6_disabled": True,
                "ipv6_owner_uuid": UUID_A,
                "last_connection_uuid": UUID_A,
                "priority_set": True,
            }
        )
        f.nm_profiles[UUID_B] = {
            "802-11-wireless.bssid": "",
            "802-11-wireless.band": "bg",
            "ipv6.method": "auto",
        }
        f.power_save_off = False
        before = dict(f.settings)
        status = await f.plugin.get_status()
        self.assertTrue(status["success"])
        self.assertEqual(f.nmcli_calls, [])
        self.assertEqual(f.save_count, 0)
        self.assertEqual(f.settings, before)
        self.assertEqual(status.get("unknown_owners"), [])
        for key in ("power_save", "bssid_lock", "ipv6", "band_preference"):
            self.assertIs(status["drift"].get(key), True)

    async def test_active_B_owner_A_disable_targets_A(self):
        f = self.fixture()
        f.active_uuid = UUID_B
        f.settings.update(
            {
                "band_preference_enabled": True,
                "band_preference": "a",
                "band_owner_uuid": UUID_A,
                "last_connection_uuid": UUID_B,
            }
        )
        result = await f.plugin.set_band_preference(False)
        self.assertTrue(result["success"])
        self.assertFalse(result["reconnected"])
        self.assertEqual(f.reconnects, [])
        self.assertTrue(f.nmcli_calls)
        for uuid, key, value in f.nmcli_calls:
            self.assertEqual(uuid, UUID_A)
        self.assertIn((UUID_A, "802-11-wireless.band", ""), f.nmcli_calls)
        self.assertFalse(f.settings["band_preference_enabled"])
        self.assertEqual(f.settings["band_owner_uuid"], "")

    async def test_offline_disable_uses_owner_not_last(self):
        f = self.fixture()
        f.iface = None
        f.active_uuid = None
        f.settings.update(
            {
                "ipv6_disabled": True,
                "ipv6_owner_uuid": UUID_A,
                "last_connection_uuid": UUID_B,
            }
        )
        result = await f.plugin.set_ipv6(False)
        self.assertTrue(result["success"])
        self.assertFalse(result["reconnected"])
        self.assertEqual(f.reconnects, [])
        self.assertEqual(f.nmcli_calls, [(UUID_A, "ipv6.method", "auto")])
        self.assertFalse(f.settings["ipv6_disabled"])

    async def test_legacy_status_reports_unknown_owners(self):
        f = self.fixture()
        f.active_uuid = UUID_A
        f.settings.update(
            {
                "bssid_lock_enabled": True,
                "bssid_lock_connection_uuid": "",
                "band_preference_enabled": True,
                "band_preference": "a",
                "dns_enabled": True,
                "ipv6_disabled": True,
            }
        )
        f.nm_profiles[UUID_A] = {
            "802-11-wireless.bssid": "",
            "802-11-wireless.band": "bg",
            "ipv6.method": "auto",
        }
        status = await f.plugin.get_status()
        self.assertTrue(status["success"])
        self.assertEqual(
            status.get("unknown_owners"),
            ["bssid_lock", "band_preference", "dns", "ipv6"],
        )
        for key in ("bssid_lock", "band_preference", "ipv6"):
            self.assertIs(status["drift"].get(key), True)
        self.assertEqual(f.nmcli_calls, [])
        self.assertEqual(f.save_count, 0)

    async def test_legacy_enable_rejects_unknown_owner(self):
        f = self.fixture()
        f.active_uuid = UUID_A
        f.settings.update({"ipv6_disabled": True, "ipv6_owner_uuid": ""})
        result = await f.plugin.set_ipv6(True)
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "unknown_owner")
        self.assertEqual(result["message"], UNKNOWN_OWNER_MESSAGE)
        self.assertEqual(f.nmcli_calls, [])
        self.assertEqual(f.save_count, 0)
        self.assertTrue(f.settings["ipv6_disabled"])

    async def test_legacy_disable_clears_intent_only(self):
        f = self.fixture()
        f.iface = None
        f.active_uuid = None
        f.settings.update(
            {
                "ipv6_disabled": True,
                "ipv6_owner_uuid": "",
                "last_connection_uuid": "",
            }
        )
        result = await f.plugin.set_ipv6(False)
        self.assertTrue(result["success"])
        self.assertFalse(result["reconnected"])
        self.assertEqual(f.nmcli_calls, [])
        self.assertEqual(f.reconnects, [])
        self.assertFalse(f.settings["ipv6_disabled"])
        self.assertEqual(f.save_count, 1)

    async def test_failed_nmcli_preserves_owner_and_intent(self):
        f = self.fixture()
        f.active_uuid = UUID_A
        f.settings.update(
            {
                "band_preference_enabled": True,
                "band_preference": "a",
                "band_owner_uuid": UUID_A,
            }
        )
        f.nmcli_fail_keys = {"802-11-wireless.band"}
        last_applied_before = f.settings["last_applied"]
        result = await f.plugin.set_band_preference(True, "bg")
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "nmcli_failed")
        self.assertTrue(result["detail"])
        self.assertEqual(f.reconnects, [])
        self.assertEqual(f.save_count, 0)
        self.assertEqual(f.settings["last_applied"], last_applied_before)
        self.assertTrue(f.settings["band_preference_enabled"])
        self.assertEqual(f.settings["band_preference"], "a")
        self.assertEqual(f.settings["band_owner_uuid"], UUID_A)

        # Retry stays possible: the retained owner allows an offline disable.
        f.iface = None
        f.active_uuid = None
        f.nmcli_fail_keys = set()
        retry = await f.plugin.set_band_preference(False)
        self.assertTrue(retry["success"])
        self.assertFalse(retry["reconnected"])
        self.assertEqual(f.reconnects, [])
        self.assertIn((UUID_A, "802-11-wireless.band", ""), f.nmcli_calls)
        self.assertFalse(f.settings["band_preference_enabled"])
        self.assertEqual(f.settings["band_owner_uuid"], "")

    async def test_dns_partial_is_failure(self):
        f = self.fixture()
        f.active_uuid = UUID_A
        f.settings.update({"dns_enabled": False})
        f.nmcli_fail_keys = {"ipv4.ignore-auto-dns"}
        result = await f.plugin.set_dns(True, "cloudflare")
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "dns_partial")
        self.assertIn("ipv4.ignore-auto-dns", result["message"])
        self.assertEqual(result["detail"], f.nmcli_stderr)
        self.assertFalse(f.settings["dns_enabled"])
        self.assertFalse(f.settings.get("dns_owner_uuid"))
        self.assertEqual(f.reconnects, [])

    async def test_relock_skipped_on_owner_mismatch(self):
        f = self.fixture()
        f.active_uuid = UUID_B
        f.link_bssid = "11:22:33:44:55:66"
        f.settings.update(
            {
                "bssid_lock_enabled": True,
                "bssid_lock_value": "AA:BB:CC:DD:EE:FF",
                "bssid_lock_connection_uuid": UUID_A,
                "band_preference_enabled": False,
            }
        )
        result = await f.plugin.set_band_preference(True, "a")
        self.assertTrue(result["success"])
        bssid_mods = [call for call in f.nmcli_calls if call[1] == "802-11-wireless.bssid"]
        self.assertEqual(bssid_mods, [])
        self.assertIn((UUID_B, "802-11-wireless.band", "a"), f.nmcli_calls)
        self.assertEqual(f.settings["band_owner_uuid"], UUID_B)

    def test_status_has_no_save_or_modify(self):
        f = self.fixture()
        src = f.method_source("get_status")
        for pattern in (
            r"_save_settings_with_timestamp\b",
            r"_save_settings\b",
            r"_nmcli_modify\b",
            r"os\.replace\b",
        ):
            self.assertNotRegex(src, pattern)
        # Write-mode opens only; the read-only last_enforced observation stays.
        self.assertNotRegex(src, r"open\([^)]*['\"]w['\"]")

    def test_priority_never_written(self):
        hits = []
        for path in (SOURCE, TEMPLATE):
            for lineno, line in _code_lines(path):
                if "autoconnect-priority" in line:
                    hits.append(f"{path.name}:{lineno}:{line.strip()}")
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
