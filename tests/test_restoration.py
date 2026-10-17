"""Isolated ST0-004/016 snapshot/restore/reset tests.

Never import the real root plugin; never execute real setters, lifecycle,
installer or dispatcher code. Pattern: tests/test_profile_ownership.py +
tests/test_backend_reservation.py (AST-extract + fail-closed builtins).

The fixture execs the snapshot helpers, setters, reset_settings, _uninstall
and _main from main.py against scriptable in-memory stubs (no system calls,
no real filesystem, no NM). Snapshot helpers missing on the pre-Task-2
baseline degrade gracefully so this file imports cleanly and the behavior
asserts FAIL (red) instead of erroring.
"""

import ast
import io
import json
import os as _real_os
import posixpath as _posixpath
import unittest
from pathlib import Path
from types import SimpleNamespace

UUID_A = "UUID-A-1111"
UUID_B = "UUID-B-2222"
IFACE = "wlan0"
FIXED_TIME = 1234567890

# Split so this file never contains the guarded literal consecutively.
PRIORITY_LITERAL = "autoconnect" + "-priority"

SOURCE = Path(__file__).resolve().parents[1] / "main.py"
TEMPLATE = Path(__file__).resolve().parents[1] / "defaults" / "dispatcher.sh.tmpl"

METHOD_NAMES = {
    "set_power_save",
    "set_auto_fix",
    "set_bssid_lock",
    "set_band_preference",
    "set_dns",
    "set_ipv6",
    "set_buffer_tuning",
    "set_cake",
    "reset_settings",
    "_uninstall",
    "_main",
    "_resolve_uuid",
    "_require_wifi",
    "_clear_transferred_profile",
    "_clear_owned_profiles",
    "_apply_driver_fixes",
    "_apply_pcie_aspm_fix",
    "_install_dispatcher",
    "_remove_dispatcher",
    "_rotate_logs",
    "_ensure_backend_switch_state",
    "_get_backend_method",
    "_get_current_backend",
    "_detect_distro",
    "_unexpected_response",
    "_capture_slot",
    "_restore_slot",
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
    "SETTINGS_FILE",
    "ENFORCED_FILE",
    "SNAPSHOT_FILE",
}

SNAPSHOT_METHODS = {"_capture_slot", "_restore_slot"}
SNAPSHOT_FUNCS = {"_load_snapshot", "_save_snapshot"}

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
PCIE_LINK_FILES = [
    "l0s_aspm",
    "l1_aspm",
    "l1_1_aspm",
    "l1_2_aspm",
    "l1_1_pcipm",
    "l1_2_pcipm",
]

FOREIGN_NM_CONF = "[connection]\n# foreign custom powersave\n"
FOREIGN_MODPROBE = "# foreign custom driver options\n"
FOREIGN_DISPATCHER = "#!/bin/bash\n# foreign dispatcher\n"
FOREIGN_BACKEND_CONF = "[device]\n# foreign backend conf\n"
SEED_QDISC = "qdisc cake 8001: root refcnt 2 unlimited diffserv4 nat ack-filter"
PRIOR_QDISC = (
    "qdisc fq_codel 0: dev wlan0 root refcnt 0 limit 10240p flows 1024 "
    "quantum 1514 target 5ms interval 100ms"
)


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


class RestorationFixture:
    """AST-extracted plugin methods over scriptable in-memory stubs."""

    def __init__(self):
        self.iface = IFACE
        self.active_uuid = UUID_A
        self.link_bssid = "AA:BB:CC:DD:EE:FF"
        self.power_save_off = False
        self.sysctl = dict(CUSTOM_SYSCTL)
        self.txq = {IFACE: "3000"}
        self.qdisc_output = SEED_QDISC
        self.nm_profiles = {}
        self.nmcli_fail_keys = set()
        self.nmcli_fail_uuid = None
        self.nmcli_stderr = "simulated nmcli failure"
        self.pcie_present = True
        self.pcie_device = PCIE_DEVICE
        self.backend_current = None
        self.backend_svc = {}
        self.device_info = {
            "model": "lcd",
            "driver": "rtw88",
            "device_family": "deck_lcd",
            "device_label": "Steam Deck LCD",
            "chip_label": "WiFi 5 (RTL8822CE)",
            "supports_6ghz": False,
        }
        self.fs = {}
        self.dirs = set()
        self.info_logs = []
        self.error_logs = []
        self.run_calls = []
        self.nmcli_calls = []
        self.reconnects = []
        self.sleep_calls = []
        self.makedirs_calls = []
        self.remove_calls = []
        self.replace_calls = []
        self.chmod_calls = []
        self.write_counts = {}
        self.template_text = TEMPLATE.read_text(encoding="utf-8")
        # Emulated device paths always use POSIX separators (production runs
        # on Linux; ntpath joins would never match real main.py path logic).
        self.posix_template = _posixpath.join(
            "/tmp/wifi-optimizer-test", "defaults", "dispatcher.sh.tmpl"
        )

        tree = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
        plugin = next(
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "Plugin"
        )
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
        self.present_assigns = {
            target.id for node in found_assigns for target in node.targets
            if isinstance(target, ast.Name)
        }

        found_funcs = [
            node
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name in MODULE_FUNCS
        ]
        self.present_funcs = {node.name for node in found_funcs}

        self.snapshot_supported = (
            SNAPSHOT_METHODS <= self.present_methods
            and SNAPSHOT_FUNCS <= self.present_funcs
            and "SNAPSHOT_FILE" in self.present_assigns
        )
        self.missing_snapshot = sorted(
            (SNAPSHOT_METHODS - self.present_methods)
            | (SNAPSHOT_FUNCS - self.present_funcs)
            | ({"SNAPSHOT_FILE"} - self.present_assigns)
        )

        fixture = self

        def _stub_open(path, mode="r", *args, **kwargs):
            p = str(path)
            if "r" in mode and "+" not in mode:
                if p == str(TEMPLATE) or p == fixture.posix_template:
                    return io.StringIO(fixture.template_text)
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
            fixture.makedirs_calls.append(str(path))
            fixture.dirs.add(str(path))

        def _remove(path):
            fixture.remove_calls.append(str(path))
            try:
                del fixture.fs[str(path)]
            except KeyError:
                raise FileNotFoundError(f"isolated fs missing: {path}")

        def _replace(src, dst):
            fixture.replace_calls.append((str(src), str(dst)))
            fixture.fs[str(dst)] = fixture.fs.pop(str(src))

        def _chmod(path, mode):
            fixture.chmod_calls.append((str(path), mode))

        os_stub = SimpleNamespace(
            path=SimpleNamespace(
                isfile=_isfile,
                isdir=_isdir,
                join=_posixpath.join,
                dirname=_posixpath.dirname,
                basename=_posixpath.basename,
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
        self.SNAPSHOT_FILE = namespace.get(
            "SNAPSHOT_FILE",
            _real_os.path.join(
                _real_os.path.dirname(namespace["SETTINGS_FILE"]),
                "system_snapshot.json",
            ),
        )
        self.NM_CONF_PATH = namespace["NM_CONF_PATH"]
        self.MODPROBE_CONF_PATH = namespace["MODPROBE_CONF_PATH"]
        self.GENERIC_BACKEND_CONF = namespace["GENERIC_BACKEND_CONF"]
        self.DISPATCHER_PATH = namespace["DISPATCHER_PATH"]
        self.SYSCTL_DEFAULTS = dict(namespace["SYSCTL_DEFAULTS"])
        self.DEFAULT_SETTINGS = dict(namespace["DEFAULT_SETTINGS"])

        self.plugin = type(
            "IsolatedRestorationPlugin",
            (),
            {name: namespace[name] for name in self.present_methods},
        )()
        self.plugin._run_cmd = self._stub_run_cmd
        self.plugin._nmcli_modify = self._stub_nmcli_modify
        self.plugin._hard_reconnect = self._stub_hard_reconnect
        self.plugin._get_wifi_interface = lambda: self.iface
        self.plugin._get_active_connection_uuid = lambda: self.active_uuid
        self.plugin._get_current_backend = lambda: self.backend_current

        async def _stub_device_info(*args, **kwargs):
            return dict(fixture.device_info)

        self.plugin.get_device_info = _stub_device_info
        self.seed_settings()

    # ---- seed/read helpers ----

    def seed_settings(self, **overrides):
        merged = dict(self.DEFAULT_SETTINGS)
        merged.update(overrides)
        self.fs[self.SETTINGS_FILE] = json.dumps(merged)

    def get_settings(self):
        return self.ns["_load_settings"]()

    def read_snapshot(self):
        raw = self.fs.get(self.SNAPSHOT_FILE)
        if raw is None:
            return None
        return json.loads(raw)

    def read_file(self, path):
        return self.fs.get(str(path))

    def seed_foreign_state(self):
        """Seed foreign custom state the plugin never enabled."""
        self.sysctl = dict(CUSTOM_SYSCTL)
        self.txq = {IFACE: "3000"}
        self.qdisc_output = SEED_QDISC
        self.power_save_off = False
        self.fs[self.NM_CONF_PATH] = FOREIGN_NM_CONF
        self.fs[self.MODPROBE_CONF_PATH] = FOREIGN_MODPROBE
        self.fs[self.DISPATCHER_PATH] = FOREIGN_DISPATCHER
        self.fs[self.GENERIC_BACKEND_CONF] = FOREIGN_BACKEND_CONF
        for sysfs_path in self.ns["DRIVER_PROFILES"]["rtw88"][
            "sysfs_power_fixes"
        ]:
            self.fs[sysfs_path] = "N"
        self.fs[self.pcie_device + "/link/" + "l0s_aspm"] = "1"
        for name in PCIE_LINK_FILES[1:]:
            self.fs[self.pcie_device + "/link/" + name] = "1"
        self.fs[self.pcie_device + "/power/control"] = "auto"
        self.nm_profiles[UUID_A] = {
            "802-11-wireless.bssid": "11:22:33:44:55:66",
            "802-11-wireless.band": "bg",
            "ipv4.dns": "9.9.9.9",
            "ipv4.ignore-auto-dns": "no",
            "ipv6.method": "auto",
        }
        self.nm_profiles[UUID_B] = {
            "802-11-wireless.bssid": "",
            "802-11-wireless.band": "",
            "ipv4.dns": "",
            "ipv4.ignore-auto-dns": "no",
            "ipv6.method": "auto",
        }

    def foreign_paths(self):
        paths = [
            self.NM_CONF_PATH,
            self.MODPROBE_CONF_PATH,
            self.DISPATCHER_PATH,
            self.GENERIC_BACKEND_CONF,
            *self.ns["DRIVER_PROFILES"]["rtw88"]["sysfs_power_fixes"],
            *(self.pcie_device + "/link/" + name for name in PCIE_LINK_FILES),
            self.pcie_device + "/power/control",
        ]
        return {p: self.fs.get(p) for p in paths}

    def mutating_run_calls(self):
        mutating = []
        for cmd in self.run_calls:
            if not cmd:
                continue
            if cmd[0] == "/usr/bin/sysctl" and len(cmd) > 1 and cmd[1] == "-w":
                mutating.append(cmd)
            elif cmd[0] == "/usr/bin/iw" and "set" in cmd:
                mutating.append(cmd)
            elif cmd[0] == "/usr/bin/ip" and "set" in cmd:
                mutating.append(cmd)
            elif cmd[0] == "/usr/bin/tc" and any(
                part in ("del", "replace") for part in cmd
            ):
                mutating.append(cmd)
            elif "modprobe" in cmd[0]:
                mutating.append(cmd)
        return mutating

    def logged_fallback(self):
        return [m for m in self.info_logs if "fallback" in m.lower()]

    # ---- stubs ----

    def _stub_run_cmd(self, cmd, timeout=5, clean_env=True):
        self.run_calls.append(list(cmd))
        cmd = list(cmd)
        if cmd[0] == "/usr/bin/nmcli":
            if cmd[1:4] == ["radio", "wifi", "off"]:
                return _ok("")
            if cmd[1:4] == ["radio", "wifi", "on"]:
                return _ok("")
            if cmd[1:3] == ["con", "up"]:
                return _ok("")
            if "-f" in cmd:
                field = cmd[cmd.index("-f") + 1]
                rest = cmd[cmd.index("-f") + 2 :]
                if rest[:2] == ["dev", "status"]:
                    if self.iface:
                        return _ok(f"{self.iface}:wifi")
                    return _ok("")
                if rest[:2] == ["con", "show"] and "--active" in rest:
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
                        return _ok("IP4.DNS[1]:9.9.9.9")
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
                # [..., "set", iface, "txqueuelen", value]
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
        if cmd[0] == "/usr/bin/systemctl" and len(cmd) == 3:
            return _ok(self.backend_svc.get((cmd[1], cmd[2]), "unknown"))
        if "modprobe" in cmd[0]:
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
        if key in self.nmcli_fail_keys and uuid_match:
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
        # Mirrors the D1 success shape: reconnect attempted and verified.
        stage = {"ok": True, "stderr": ""}
        return {
            "stages": {
                "radio_off": dict(stage),
                "radio_on": dict(stage),
                "activation": dict(stage) if uuid else None,
            },
            "verified": True,
            "active_uuid_after": uuid,
            "radio_off_without_on": False,
        }

    def method_source(self, name):
        tree = ast.parse(
            SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE)
        )
        plugin = next(
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "Plugin"
        )
        node = next(
            child
            for child in plugin.body
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            and child.name == name
        )
        return ast.get_source_segment(SOURCE.read_text(encoding="utf-8"), node)


def _code_lines(path):
    return [
        (lineno, line)
        for lineno, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        )
        if not line.strip().startswith("#")
    ]


class RestorationTests(unittest.IsolatedAsyncioTestCase):
    def fixture(self):
        return RestorationFixture()

    def require_snapshot(self, f):
        self.assertTrue(
            f.snapshot_supported,
            f"snapshot helpers missing: {f.missing_snapshot}",
        )

    async def test_all_flags_false_leaves_custom_state(self):
        f = self.fixture()
        f.seed_settings(
            power_save_disabled=False,
            auto_fix_on_wake=False,
            bssid_lock_enabled=False,
            band_preference_enabled=False,
            dns_enabled=False,
            ipv6_disabled=False,
            buffer_tuning_enabled=False,
            cake_enabled=False,
            driver="rtw88",
        )
        f.seed_foreign_state()
        before = f.foreign_paths()
        before_profiles = json.loads(json.dumps(f.nm_profiles))

        await f.plugin.set_power_save(False)
        await f.plugin.set_buffer_tuning(False)
        await f.plugin.set_cake(False)
        await f.plugin.set_bssid_lock(False)
        await f.plugin.set_band_preference(False)
        await f.plugin.set_dns(False)
        await f.plugin.set_ipv6(False)
        await f.plugin.set_auto_fix(False)
        await f.plugin._main()

        self.assertEqual(f.mutating_run_calls(), [])
        self.assertEqual(f.nmcli_calls, [])
        self.assertEqual(f.remove_calls, [])
        self.assertEqual(f.chmod_calls, [])
        self.assertEqual(f.foreign_paths(), before)
        self.assertEqual(f.nm_profiles, before_profiles)
        self.assertEqual(f.sysctl, CUSTOM_SYSCTL)
        self.assertEqual(f.txq, {IFACE: "3000"})
        self.assertEqual(f.qdisc_output, SEED_QDISC)
        self.assertFalse(f.power_save_off)

    async def test_roundtrip_sysctl_txq(self):
        f = self.fixture()
        self.require_snapshot(f)
        f.seed_settings(driver="rtw88")

        enabled = await f.plugin.set_buffer_tuning(True)
        self.assertTrue(enabled["success"])
        self.assertEqual(f.sysctl, f.ns["SYSCTL_PARAMS"])
        self.assertEqual(f.txq.get(IFACE), "2000")

        disabled = await f.plugin.set_buffer_tuning(False)
        self.assertTrue(disabled["success"])
        self.assertEqual(disabled.get("errors"), [])
        self.assertEqual(f.sysctl, CUSTOM_SYSCTL)
        self.assertEqual(f.txq.get(IFACE), "3000")

    async def test_roundtrip_power_nmconf(self):
        f = self.fixture()
        self.require_snapshot(f)
        f.seed_settings(driver="rtw88")
        f.seed_foreign_state()

        enabled = await f.plugin.set_power_save(True)
        self.assertTrue(enabled["success"])
        self.assertTrue(f.power_save_off)
        self.assertEqual(
            f.read_file(f.NM_CONF_PATH), "[connection]\nwifi.powersave = 2\n"
        )

        disabled = await f.plugin.set_power_save(False)
        self.assertTrue(disabled["success"])
        self.assertEqual(disabled.get("errors"), [])
        self.assertFalse(f.power_save_off)
        self.assertEqual(f.read_file(f.NM_CONF_PATH), FOREIGN_NM_CONF)
        self.assertEqual(f.read_file(f.MODPROBE_CONF_PATH), FOREIGN_MODPROBE)
        for sysfs_path in f.ns["DRIVER_PROFILES"]["rtw88"][
            "sysfs_power_fixes"
        ]:
            self.assertEqual(f.read_file(sysfs_path), "N")
        for name in PCIE_LINK_FILES:
            self.assertEqual(
                f.read_file(f.pcie_device + "/link/" + name), "1"
            )
        self.assertEqual(
            f.read_file(f.pcie_device + "/power/control"), "auto"
        )

    async def test_roundtrip_qdisc_best_effort(self):
        f = self.fixture()
        self.require_snapshot(f)
        f.qdisc_output = ""
        f.txq = {IFACE: "1500"}
        f.seed_settings()

        enabled = await f.plugin.set_cake(True)
        self.assertTrue(enabled["success"])
        self.assertEqual(f.txq.get(IFACE), "256")

        disabled = await f.plugin.set_cake(False)
        self.assertTrue(disabled["success"])
        self.assertEqual(disabled.get("errors"), [])
        dels = [
            cmd
            for cmd in f.run_calls
            if cmd[:4] == ["/usr/bin/tc", "qdisc", "del", "dev"]
        ]
        self.assertTrue(dels)
        self.assertEqual(f.txq.get(IFACE), "1500")

        g = self.fixture()
        self.require_snapshot(g)
        g.qdisc_output = PRIOR_QDISC
        g.txq = {IFACE: "1500"}
        g.seed_settings()
        self.assertTrue((await g.plugin.set_cake(True))["success"])
        self.assertTrue((await g.plugin.set_cake(False))["success"])
        replaces = [
            cmd
            for cmd in g.run_calls
            if cmd[:4] == ["/usr/bin/tc", "qdisc", "replace", "dev"]
        ]
        self.assertTrue(replaces)
        tokens = PRIOR_QDISC.split()
        expected = (
            ["/usr/bin/tc", "qdisc", "replace", "dev", IFACE, "root"]
            + tokens[tokens.index("root") + 1 :]
        )
        self.assertEqual(replaces[-1], expected)

    async def test_roundtrip_profile_key(self):
        f = self.fixture()
        self.require_snapshot(f)
        f.active_uuid = UUID_A
        f.nm_profiles[UUID_A] = {"802-11-wireless.band": "bg"}
        f.seed_settings()

        enabled = await f.plugin.set_band_preference(True, "a")
        self.assertTrue(enabled["success"])
        self.assertEqual(f.nm_profiles[UUID_A]["802-11-wireless.band"], "a")

        disabled = await f.plugin.set_band_preference(False)
        self.assertTrue(disabled["success"])
        self.assertEqual(disabled.get("errors"), [])
        self.assertEqual(f.nm_profiles[UUID_A]["802-11-wireless.band"], "bg")

    async def test_transfer_clear_uses_snapshot(self):
        f = self.fixture()
        self.require_snapshot(f)
        f.active_uuid = UUID_A
        f.nm_profiles[UUID_A] = {"802-11-wireless.band": "bg"}
        f.nm_profiles[UUID_B] = {"802-11-wireless.band": ""}
        f.seed_settings()

        first = await f.plugin.set_band_preference(True, "a")
        self.assertTrue(first["success"])
        self.assertEqual(first.get("transfer_warnings"), [])

        f.active_uuid = UUID_B
        second = await f.plugin.set_band_preference(True, "a")
        self.assertTrue(second["success"])
        self.assertEqual(second.get("transfer_warnings"), [])
        self.assertEqual(f.nm_profiles[UUID_B]["802-11-wireless.band"], "a")
        self.assertEqual(f.nm_profiles[UUID_A]["802-11-wireless.band"], "bg")

    async def test_legacy_missing_slot_falls_back_logged(self):
        f = self.fixture()
        self.require_snapshot(f)
        f.active_uuid = UUID_A
        f.nm_profiles[UUID_A] = {"802-11-wireless.band": "a"}
        f.seed_settings(
            band_preference_enabled=True,
            band_preference="a",
            band_owner_uuid=UUID_A,
        )
        self.assertIsNone(f.read_snapshot())

        result = await f.plugin.set_band_preference(False)
        self.assertTrue(result["success"])
        self.assertEqual(f.nm_profiles[UUID_A]["802-11-wireless.band"], "")
        self.assertEqual(
            result.get("errors"),
            [f"fallback:profile_{UUID_A}_802-11-wireless.band"],
        )
        self.assertTrue(f.logged_fallback())

    async def test_reset_reconciles_live_dispatcher_profiles(self):
        f = self.fixture()
        self.require_snapshot(f)
        f.active_uuid = UUID_A
        f.power_save_off = True
        f.seed_foreign_state()
        f.fs[f.DISPATCHER_PATH] = FOREIGN_DISPATCHER
        f.fs.pop(f.NM_CONF_PATH, None)
        f.nm_profiles[UUID_A] = {
            "802-11-wireless.bssid": "AA:BB:CC:DD:EE:FF",
            "802-11-wireless.band": "a",
            "ipv6.method": "disabled",
        }
        f.nm_profiles[UUID_B] = {
            "ipv4.dns": "1.1.1.1 1.0.0.1",
            "ipv4.ignore-auto-dns": "yes",
        }
        f.seed_settings(
            power_save_disabled=False,
            auto_fix_on_wake=False,
            buffer_tuning_enabled=True,
            cake_enabled=True,
            bssid_lock_enabled=True,
            bssid_lock_connection_uuid=UUID_A,
            band_preference_enabled=True,
            band_owner_uuid=UUID_A,
            dns_enabled=True,
            dns_owner_uuid=UUID_B,
            ipv6_disabled=True,
            ipv6_owner_uuid=UUID_A,
            driver="rtw88",
        )

        result = await f.plugin.reset_settings()
        # Fallback reset (no snapshot slots): errors non-empty, so success
        # is False — defaults were applied but the true priors are unknown.
        self.assertFalse(result["success"])
        self.assertTrue(result.get("errors"))
        self.assertIn("errors", result)

        iw_sets = [
            cmd
            for cmd in f.run_calls
            if cmd[:3] == ["/usr/bin/iw", "dev", IFACE]
            and cmd[3:5] == ["set", "power_save"]
        ]
        self.assertTrue(iw_sets)
        self.assertEqual(iw_sets[-1][5], "off")
        self.assertEqual(
            f.read_file(f.NM_CONF_PATH), "[connection]\nwifi.powersave = 2\n"
        )
        dispatcher = f.read_file(f.DISPATCHER_PATH)
        self.assertIsNotNone(dispatcher)
        self.assertNotEqual(dispatcher, FOREIGN_DISPATCHER)
        self.assertIn(f.SETTINGS_FILE, dispatcher)

        cleared = [
            (UUID_A, "802-11-wireless.bssid", ""),
            (UUID_A, "802-11-wireless.band", ""),
            (UUID_B, "ipv4.dns", ""),
            (UUID_B, "ipv4.ignore-auto-dns", "no"),
            (UUID_A, "ipv6.method", "auto"),
        ]
        for entry in cleared:
            self.assertIn(entry, f.nmcli_calls)
        self.assertEqual(f.reconnects, [UUID_A])

        fresh = f.get_settings()
        self.assertTrue(fresh["power_save_disabled"])
        self.assertTrue(fresh["auto_fix_on_wake"])
        self.assertFalse(fresh["buffer_tuning_enabled"])
        self.assertNotEqual(fresh["last_applied"], 0)
        self.assertIsNotNone(f.read_file(f.GENERIC_BACKEND_CONF))

    async def test_reset_clean_success_true(self):
        # Clean reset (every slot captured by prior enables): no errors,
        # success stays True.
        f = self.fixture()
        self.require_snapshot(f)
        f.seed_settings(driver="rtw88")
        self.assertTrue((await f.plugin.set_power_save(True))["success"])
        self.assertTrue((await f.plugin.set_auto_fix(True))["success"])
        self.assertTrue((await f.plugin.set_buffer_tuning(True))["success"])
        self.assertTrue((await f.plugin.set_cake(True))["success"])
        self.assertTrue((await f.plugin.set_bssid_lock(True))["success"])
        self.assertTrue(
            (await f.plugin.set_band_preference(True, "a"))["success"]
        )
        self.assertTrue(
            (await f.plugin.set_dns(True, "cloudflare"))["success"]
        )
        self.assertTrue((await f.plugin.set_ipv6(True))["success"])

        result = await f.plugin.reset_settings()
        self.assertEqual(result.get("errors"), [])
        self.assertTrue(result["success"])

        fresh = f.get_settings()
        self.assertTrue(fresh["power_save_disabled"])
        self.assertTrue(fresh["auto_fix_on_wake"])
        self.assertFalse(fresh["buffer_tuning_enabled"])

    async def test_uninstall_restores_iw_and_removes(self):
        f = self.fixture()
        self.require_snapshot(f)
        # Live power save already off: enable captures "off" as baseline.
        f.power_save_off = True
        f.seed_settings(power_save_disabled=False, driver="rtw88")
        self.assertTrue((await f.plugin.set_power_save(True))["success"])
        # Simulate later live drift: something turned power save back on.
        f.power_save_off = False
        self.assertIn(f.SNAPSHOT_FILE, f.fs)

        await f.plugin._uninstall()

        iw_sets = [
            cmd
            for cmd in f.run_calls
            if cmd[:3] == ["/usr/bin/iw", "dev", IFACE]
            and cmd[3:5] == ["set", "power_save"]
        ]
        self.assertTrue(iw_sets)
        self.assertEqual(iw_sets[-1][5], "off")
        for path in (
            f.DISPATCHER_PATH,
            f.NM_CONF_PATH,
            f.MODPROBE_CONF_PATH,
            f.GENERIC_BACKEND_CONF,
            f.SETTINGS_FILE,
            f.SNAPSHOT_FILE,
        ):
            self.assertNotIn(path, f.fs)
        self.assertEqual(f.reconnects, [])

    async def test_uninstall_clears_owned_profiles_conditional_reconnect(self):
        # Active profile owns keys: cleared to literals + single reconnect.
        f = self.fixture()
        self.require_snapshot(f)
        f.active_uuid = UUID_A
        f.nm_profiles[UUID_A] = {
            "802-11-wireless.bssid": "AA:BB:CC:DD:EE:FF",
            "802-11-wireless.band": "a",
            "ipv6.method": "disabled",
        }
        f.nm_profiles[UUID_B] = {
            "ipv4.dns": "1.1.1.1 1.0.0.1",
            "ipv4.ignore-auto-dns": "yes",
        }
        f.seed_settings(
            bssid_lock_enabled=True,
            bssid_lock_connection_uuid=UUID_A,
            band_preference_enabled=True,
            band_owner_uuid=UUID_A,
            dns_enabled=True,
            dns_owner_uuid=UUID_B,
            ipv6_disabled=True,
            ipv6_owner_uuid=UUID_A,
            driver="rtw88",
        )

        await f.plugin._uninstall()

        for entry in (
            (UUID_A, "802-11-wireless.bssid", ""),
            (UUID_A, "802-11-wireless.band", ""),
            (UUID_B, "ipv4.dns", ""),
            (UUID_B, "ipv4.ignore-auto-dns", "no"),
            (UUID_A, "ipv6.method", "auto"),
        ):
            self.assertIn(entry, f.nmcli_calls)
        self.assertEqual(f.reconnects, [UUID_A])
        for path in (f.SETTINGS_FILE, f.SNAPSHOT_FILE):
            self.assertNotIn(path, f.fs)

        # Foreign active profile: owners still cleared, no reconnect.
        g = self.fixture()
        self.require_snapshot(g)
        g.active_uuid = UUID_B
        g.nm_profiles[UUID_A] = {
            "802-11-wireless.bssid": "AA:BB:CC:DD:EE:FF",
            "802-11-wireless.band": "a",
            "ipv6.method": "disabled",
        }
        g.seed_settings(
            bssid_lock_enabled=True,
            bssid_lock_connection_uuid=UUID_A,
            band_preference_enabled=True,
            band_owner_uuid=UUID_A,
            dns_enabled=False,
            ipv6_disabled=True,
            ipv6_owner_uuid=UUID_A,
            driver="rtw88",
        )

        await g.plugin._uninstall()

        for entry in (
            (UUID_A, "802-11-wireless.bssid", ""),
            (UUID_A, "802-11-wireless.band", ""),
            (UUID_A, "ipv6.method", "auto"),
        ):
            self.assertIn(entry, g.nmcli_calls)
        self.assertEqual(g.reconnects, [])

        # Offline live restore is logged as fallback, never silent.
        h = self.fixture()
        self.require_snapshot(h)
        h.iface = None
        h.active_uuid = None
        h.seed_settings(driver="rtw88")

        await h.plugin._uninstall()

        self.assertTrue(h.logged_fallback())

    def test_priority_never_written_restoration(self):
        hits = []
        for path in (SOURCE, TEMPLATE):
            for lineno, line in _code_lines(path):
                if PRIORITY_LITERAL in line:
                    hits.append(f"{path.name}:{lineno}:{line.strip()}")
        self.assertEqual(hits, [])

    def test_snapshot_never_in_settings(self):
        f = self.fixture()
        self.require_snapshot(f)
        self.assertNotEqual(f.SNAPSHOT_FILE, f.SETTINGS_FILE)
        self.assertEqual(
            f.SNAPSHOT_FILE.rsplit("/", 1)[0]
            if "/" in f.SNAPSHOT_FILE
            else "",
            f.SETTINGS_FILE.rsplit("/", 1)[0]
            if "/" in f.SETTINGS_FILE
            else "",
        )

        seeded = dict(f.DEFAULT_SETTINGS)
        seeded["bogus_snapshot_key"] = {"sysctl": {}}
        seeded["system_snapshot"] = {"sysctl": {}}
        f.fs[f.SETTINGS_FILE] = json.dumps(seeded)
        merged = f.get_settings()
        self.assertNotIn("bogus_snapshot_key", merged)
        self.assertNotIn("system_snapshot", merged)

        before = f.fs[f.SETTINGS_FILE]
        f.ns["_save_snapshot"]({"sysctl": {"net.core.rmem_max": "1"}})
        self.assertEqual(f.fs[f.SETTINGS_FILE], before)
        self.assertEqual(
            json.loads(f.fs[f.SNAPSHOT_FILE]),
            {"sysctl": {"net.core.rmem_max": "1"}},
        )


if __name__ == "__main__":
    unittest.main()
