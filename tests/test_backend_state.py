"""Isolated ST0-009 backend desired/effective-state tests (red first).

Never import the real root plugin; never execute real setters, lifecycle,
switchers, installer or dispatcher code. Pattern: tests/test_restoration.py
(AST-extract + fail-closed builtins + in-memory fs + scripted _run_cmd).

Extracts the backend readers, the start gate, both switch workers,
get_status and get_diagnostic_info from main.py against scriptable stubs:
open allow-listed for the 4 backend conf paths with scripted bytes, _run_cmd
scripted per command (systemctl service commands query/mutate an in-memory
service model unless overridden) plus a run_calls log, in-memory
settings/snapshot, real asyncio with a sleep no-op spy (reconnect polls must
not burn 15s), real time, and a null decky logger.

Red-phase shims: if the D1 readers are absent from main.py, wrong-value
stubs stand in so behavior asserts FAIL with AssertionError (never
ImportError/NameError/AttributeError). Once implemented, the real methods
are extracted and the same asserts go green.
"""

import ast
import asyncio as _real_asyncio
import io
import json
import time as _real_time
import unittest
from pathlib import Path
from types import SimpleNamespace

SOURCE = Path(__file__).resolve().parents[1] / "main.py"

METHOD_NAMES = {
    "_read_desired_backend",
    "_read_effective_backend",
    "_poll_effective_backend",
    "start_backend_switch",
    "_backend_switch_worker",
    "_generic_backend_switch_worker",
    "_ensure_backend_switch_state",
    "_get_backend_method",
    "_has_backend_tool",
    "_get_current_backend",
    "_friendly_backend_error",
    "_capture_slot",
    "_unexpected_response",
    "_get_cake_status",
    "get_status",
    "_compute_drift_flags",
    "_parse_dns_ips",
    "_is_dns_drifted",
    "get_diagnostic_info",
}

MODULE_FUNCS = {
    "_load_settings",
    "_save_settings",
    "_load_snapshot",
    "_save_snapshot",
}

ASSIGN_NAMES = {
    "DEFAULT_SETTINGS",
    "SETTINGS_FILE",
    "SNAPSHOT_FILE",
    "GENERIC_BACKEND_CONF",
    "WIFI_BACKEND_CONF",
    "NM_DEFAULT_CONF",
    "BAZZITE_IWD_CONF",
    "BACKEND_HELPER",
    "DISPATCHER_PATH",
    "ENFORCED_FILE",
    "SYSCTL_PARAMS",
}

CONF_SLOTS = ("generic", "bazzite", "valve", "defaults")

IWD_SERVICE = "/usr/lib/systemd/system/iwd.service"
SYSTEMCTL = "/usr/bin/systemctl"


def _ok(stdout=""):
    return {"success": True, "stdout": stdout, "stderr": "", "returncode": 0}


def _fail(stderr="simulated failure"):
    return {"success": False, "stdout": "", "stderr": stderr, "returncode": 1}


def _iwd_conf():
    return "[device]\nwifi.backend=iwd\nwifi.iwd.autoconnect=yes\n"


def _wpa_conf():
    return "[device]\nwifi.backend=wpa_supplicant\n"


class _MemWriter(io.StringIO):
    """Commit-on-close in-memory write buffer for the stub filesystem."""

    def __init__(self, fixture, path):
        super().__init__()
        self._fixture = fixture
        self._path = path

    def close(self):
        if not self.closed:
            self._fixture.fs[self._path] = self.getvalue()
            self._fixture.writes.append(self._path)
        super().close()


class BackendStateFixture:
    """AST-extracted backend methods over scriptable in-memory stubs."""

    def __init__(self):
        self.iface = "wlan0"
        self.active_uuid = "UUID-A-1111"
        self.distro = "generic"
        self.driver = "generic"
        self.helper_present = False
        self.helper_executable = False
        self.iwd_service = True
        self.conf = {}  # slot -> content str (absent slot = missing file)
        self.services = {
            "iwd": {"active": "inactive", "enabled": "disabled"},
            "wpa_supplicant": {"active": "inactive", "enabled": "disabled"},
        }
        self.cmd_scripts = {}  # tuple(cmd) -> result or [results...] (pop per call)
        self.cmd_failures = set()  # tuple(cmd) forced to fail
        self.cmd_stderr = "simulated failure"
        self.run_calls = []
        self.sleep_calls = []
        self.makedirs_calls = []
        self.remove_calls = []
        self.chmod_calls = []
        self.replace_calls = []
        self.writes = []
        self.info_logs = []
        self.error_logs = []
        self.fs = {}
        self.device_info = {}

        tree = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
        plugin_node = next(
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "Plugin"
        )
        found_methods = [
            node
            for node in plugin_node.body
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
        assert {node.name for node in found_funcs} == MODULE_FUNCS

        fixture = self

        def _stub_open(path, mode="r", *args, **kwargs):
            p = str(path)
            if "r" in mode and "+" not in mode:
                if p in fixture.fs:
                    return io.StringIO(fixture.fs[p])
                raise FileNotFoundError(f"isolated fs missing: {p}")
            if "w" in mode or "a" in mode or "+" in mode:
                if (
                    p == fixture.GENERIC_BACKEND_CONF
                    or p in fixture.fs
                    or p.endswith(".tmp")
                ):
                    if "a" in mode and p in fixture.fs:
                        buf = _MemWriter(fixture, p)
                        buf.write(fixture.fs[p])
                        return buf
                    return _MemWriter(fixture, p)
                raise PermissionError(f"write blocked in isolated fixture: {p}")
            raise ValueError(f"unsupported mode in isolated fixture: {mode}")

        def _isfile(path):
            p = str(path)
            if p in fixture.fs:
                return True
            if p == fixture.BACKEND_HELPER:
                return fixture.helper_present
            if p == IWD_SERVICE:
                return fixture.iwd_service
            return False

        def _access(path, mode):
            return str(path) == fixture.BACKEND_HELPER and fixture.helper_executable

        def _dirname(path):
            p = str(path)
            return p.rsplit("/", 1)[0] or "/"

        os_stub = SimpleNamespace(
            path=SimpleNamespace(
                isfile=_isfile,
                isdir=lambda path: False,
                join=lambda *parts: "/".join(parts),
                dirname=_dirname,
                basename=lambda path: str(path).rsplit("/", 1)[-1],
                realpath=lambda path: str(path),
            ),
            makedirs=lambda path, exist_ok=False: fixture.makedirs_calls.append(
                str(path)
            ),
            remove=lambda path: fixture._stub_remove(str(path)),
            replace=lambda src, dst: fixture._stub_replace(str(src), str(dst)),
            chmod=lambda path, mode: fixture.chmod_calls.append((str(path), mode)),
            access=_access,
            geteuid=lambda: 0,
            environ={},
        )

        async def _noop_sleep(seconds):
            fixture.sleep_calls.append(seconds)

        asyncio_stub = SimpleNamespace(
            to_thread=_real_asyncio.to_thread,
            create_task=_real_asyncio.create_task,
            sleep=_noop_sleep,
            CancelledError=_real_asyncio.CancelledError,
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
                "sorted": sorted,
                "min": min,
                "max": max,
                "any": any,
                "all": all,
                "sum": sum,
                "repr": repr,
                "zip": zip,
                "next": next,
                "iter": iter,
                "Exception": Exception,
                "ValueError": ValueError,
                "RuntimeError": RuntimeError,
                "AttributeError": AttributeError,
                "KeyError": KeyError,
                "TypeError": TypeError,
                "FileNotFoundError": FileNotFoundError,
                "PermissionError": PermissionError,
                "OSError": OSError,
                "StopIteration": StopIteration,
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
            "time": _real_time,
            "asyncio": asyncio_stub,
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
        self.WIFI_BACKEND_CONF = namespace["WIFI_BACKEND_CONF"]
        self.NM_DEFAULT_CONF = namespace["NM_DEFAULT_CONF"]
        self.BAZZITE_IWD_CONF = namespace["BAZZITE_IWD_CONF"]
        self.BACKEND_HELPER = namespace["BACKEND_HELPER"]
        self.DEFAULT_SETTINGS = dict(namespace["DEFAULT_SETTINGS"])
        self.conf_paths = {
            "generic": self.GENERIC_BACKEND_CONF,
            "bazzite": self.BAZZITE_IWD_CONF,
            "valve": self.WIFI_BACKEND_CONF,
            "defaults": self.NM_DEFAULT_CONF,
        }

        self.plugin = type(
            "IsolatedBackendStatePlugin",
            (),
            {name: namespace[name] for name in self.present_methods},
        )()
        # Red-phase shims: stand in with wrong values so behavior asserts
        # FAIL (AssertionError) until the D1 readers are implemented.
        if "_read_desired_backend" not in self.present_methods:
            self.plugin._read_desired_backend = lambda: ("__unimplemented__", None)
        if "_read_effective_backend" not in self.present_methods:
            self.plugin._read_effective_backend = lambda: ("__unimplemented__", {})
        self.plugin._run_cmd = self._stub_run_cmd
        self.plugin._get_wifi_interface = lambda: self.iface
        self.plugin._get_active_connection_uuid = lambda: self.active_uuid
        self.plugin._get_support_tier = lambda: 2
        self.plugin._detect_distro = lambda: {"id": self.distro, "name": "Test"}

        async def _stub_device_info(*args, **kwargs):
            return dict(fixture.device_info)

        self.plugin.get_device_info = _stub_device_info
        self.plugin._ensure_backend_switch_state()
        self.seed_settings()

    # ---- stub filesystem helpers ----

    def _stub_remove(self, path):
        self.remove_calls.append(path)
        try:
            del self.fs[path]
        except KeyError:
            raise FileNotFoundError(f"isolated fs missing: {path}")

    def _stub_replace(self, src, dst):
        self.replace_calls.append((src, dst))
        self.fs[dst] = self.fs.pop(src)

    # ---- seed helpers ----

    def seed_settings(self, **overrides):
        merged = dict(self.DEFAULT_SETTINGS)
        merged.update(overrides)
        if "distro_id" not in overrides:
            merged["distro_id"] = self.distro
        if "driver" not in overrides:
            merged["driver"] = self.driver
        self.fs[self.SETTINGS_FILE] = json.dumps(merged)

    def seed_snapshot(self, snapshot):
        self.fs[self.SNAPSHOT_FILE] = json.dumps(snapshot)

    def set_conf(self, slot, backend):
        """Script one conf slot: backend 'iwd'/'wpa_supplicant'/None(missing)."""
        path = self.conf_paths[slot]
        if backend is None:
            self.fs.pop(path, None)
            self.conf.pop(slot, None)
            return
        content = _iwd_conf() if backend == "iwd" else _wpa_conf()
        self.fs[path] = content
        self.conf[slot] = content

    def clear_confs(self):
        for path in self.conf_paths.values():
            self.fs.pop(path, None)
        self.conf = {}

    def set_services(self, iwd_active, wpa_active,
                     iwd_enabled="enabled", wpa_enabled="enabled"):
        self.services["iwd"] = {"active": iwd_active, "enabled": iwd_enabled}
        self.services["wpa_supplicant"] = {
            "active": wpa_active, "enabled": wpa_enabled}

    def read_conf_file(self, slot):
        return self.fs.get(self.conf_paths[slot])

    # ---- _run_cmd stub ----

    def _stub_run_cmd(self, cmd, timeout=None, clean_env=True):
        key = tuple(cmd)
        self.run_calls.append(list(cmd))
        if key in self.cmd_scripts:
            scripted = self.cmd_scripts[key]
            if isinstance(scripted, list):
                assert scripted, f"script exhausted for {key}"
                return scripted.pop(0)
            return scripted
        if key in self.cmd_failures:
            return _fail(self.cmd_stderr)
        if len(cmd) >= 3 and cmd[0] == SYSTEMCTL and cmd[1] == "is-active":
            svc = cmd[2]
            state = self.services.get(svc, {}).get("active", "unknown")
            return _ok(state + "\n")
        if len(cmd) >= 3 and cmd[0] == SYSTEMCTL and cmd[1] == "is-enabled":
            svc = cmd[2]
            state = self.services.get(svc, {}).get("enabled", "unknown")
            return _ok(state + "\n")
        if len(cmd) >= 3 and cmd[0] == SYSTEMCTL and cmd[1] in (
                "stop", "disable", "enable", "start"):
            svc = cmd[2]
            if svc in self.services:
                if cmd[1] == "stop":
                    self.services[svc]["active"] = "inactive"
                elif cmd[1] == "start":
                    self.services[svc]["active"] = "active"
                elif cmd[1] == "enable":
                    self.services[svc]["enabled"] = "enabled"
                elif cmd[1] == "disable":
                    self.services[svc]["enabled"] = "disabled"
            return _ok("")
        return _ok("")

    def fail_command(self, *cmd, stderr="simulated failure"):
        self.cmd_failures.add(tuple(cmd))
        self.cmd_stderr = stderr

    def script_command(self, result, *cmd):
        self.cmd_scripts[tuple(cmd)] = result

    # ---- drivers ----

    async def run_generic(self, target):
        await self.plugin._generic_backend_switch_worker(target)
        return self.plugin._backend_switch["result"]

    async def run_steamos(self, target):
        await self.plugin._backend_switch_worker(target)
        return self.plugin._backend_switch["result"]

    async def run_start(self, target):
        result = await self.plugin.start_backend_switch(target)
        task = getattr(self.plugin, "_backend_switch_task", None)
        if result.get("accepted") and task is not None:
            await task
        return result

    async def status(self):
        return await self.plugin.get_status()

    async def diagnostics(self):
        return await self.plugin.get_diagnostic_info()


class BackendStateTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.fixtures = []

    def fixture(self):
        fixture = BackendStateFixture()
        self.fixtures.append(fixture)
        return fixture

    async def test_dead_target_service_is_failed_not_success(self):
        f = self.fixture()
        f.set_conf("generic", "wpa_supplicant")
        f.set_services(iwd_active="inactive", wpa_active="active")
        f.fail_command(SYSTEMCTL, "start", "iwd",
                       stderr="Job for iwd.service failed")
        result = await f.run_generic("iwd")
        self.assertFalse(result["success"])
        self.assertIn("backend_start_failed", result.get("errors") or [])

    async def test_conf_echo_never_verifies(self):
        # Conf says the target but effective reports the other backend:
        # must fail (diverged), never tautological success from the
        # just-written conf.
        f = self.fixture()
        f.set_conf("generic", "wpa_supplicant")
        f.set_services(iwd_active="inactive", wpa_active="inactive")
        f.script_command(_ok(""), SYSTEMCTL, "start", "iwd")
        f.script_command(_ok("active\n"), SYSTEMCTL, "is-active", "wpa_supplicant")
        result = await f.run_generic("iwd")
        self.assertFalse(result["success"])
        self.assertEqual(result.get("backend"), "wpa_supplicant")
        self.assertIn("effective_mismatch", result.get("errors") or [])

    async def test_true_agreement_stays_already_set(self):
        f = self.fixture()
        f.set_conf("generic", "iwd")
        f.set_services(iwd_active="active", wpa_active="inactive")
        result = await f.run_start("iwd")
        self.assertFalse(result["accepted"])
        self.assertEqual(result["reason"], "already_set")
        self.assertFalse(f.plugin._backend_switch["in_progress"])

    async def test_diverged_accepts_repair(self):
        # Desired == target but effective != target: same-target retry is
        # accepted as repair, never rejected as already_set.
        f = self.fixture()
        f.set_conf("generic", "wpa_supplicant")
        f.set_services(iwd_active="active", wpa_active="inactive")
        result = await f.run_start("wpa_supplicant")
        self.assertTrue(result["accepted"])
        self.assertTrue(result.get("repair"))
        worker_result = f.plugin._backend_switch["result"]
        self.assertTrue(worker_result["success"])
        self.assertEqual(worker_result.get("repair_of"), "wpa_supplicant")

    async def test_needs_reboot_rejects_not_already_set(self):
        f = self.fixture()
        f.set_conf("generic", "iwd")
        f.set_services(iwd_active="active", wpa_active="inactive")
        f.plugin._backend_switch["result"] = {
            "success": False, "target": "iwd", "needs_reboot": True}
        result = await f.run_start("iwd")
        self.assertFalse(result["accepted"])
        self.assertEqual(result["reason"], "needs_reboot")
        self.assertFalse(f.plugin._backend_switch["in_progress"])
        # A later terminal success clears the outstanding reboot: the same
        # target is a cheap no-op again, not a reboot rejection.
        f.plugin._backend_switch["result"] = {
            "success": True, "target": "iwd", "needs_reboot": False}
        cleared = await f.run_start("iwd")
        self.assertEqual(cleared["reason"], "already_set")

    async def test_every_systemctl_step_checked(self):
        steps = [
            ((SYSTEMCTL, "stop", "wpa_supplicant"), "backend_stop_failed"),
            ((SYSTEMCTL, "disable", "wpa_supplicant"), "backend_disable_failed"),
            ((SYSTEMCTL, "enable", "iwd"), "backend_enable_failed"),
            ((SYSTEMCTL, "start", "iwd"), "backend_start_failed"),
            ((SYSTEMCTL, "restart", "NetworkManager"), "nm_restart_failed"),
        ]
        for cmd, code in steps:
            with self.subTest(step=code):
                f = self.fixture()
                f.set_conf("generic", "wpa_supplicant")
                f.set_services(iwd_active="inactive", wpa_active="active")
                f.fail_command(*cmd)
                result = await f.run_generic("iwd")
                self.assertFalse(result["success"])
                self.assertIn(code, result.get("errors") or [])

    async def test_final_verification_reads_effective(self):
        f = self.fixture()
        f.set_conf("generic", "wpa_supplicant")
        f.set_services(iwd_active="inactive", wpa_active="active")
        f.script_command(_ok("inactive\n"), SYSTEMCTL, "is-active", "iwd")
        f.script_command(_ok("inactive\n"), SYSTEMCTL, "is-active", "wpa_supplicant")
        result = await f.run_generic("iwd")
        self.assertIn([SYSTEMCTL, "is-active", "iwd"], f.run_calls)
        self.assertFalse(result["success"])
        self.assertIn("effective_mismatch", result.get("errors") or [])

    async def test_failed_repair_rolls_back_reported(self):
        scenarios = ("generic", "steamos")
        for route in scenarios:
            with self.subTest(route=route):
                f = self.fixture()
                if route == "generic":
                    f.set_conf("generic", "iwd")
                else:
                    f.seed_settings(distro_id="steamos")
                    f.helper_present = True
                    f.helper_executable = True
                    f.set_conf("valve", "iwd")
                    f.script_command(_ok("ok"),
                                     f.BACKEND_HELPER, "write_config", "iwd")
                    f.script_command(_ok("units restarted"),
                                     f.BACKEND_HELPER, "restart_units",
                                     "wpa_supplicant")
                    f.script_command(_ok("ok"),
                                     f.BACKEND_HELPER, "write_config",
                                     "wpa_supplicant")
                    f.script_command(_ok("units restarted"),
                                     f.BACKEND_HELPER, "restart_units", "iwd")
                    f.script_command([_ok("inactive\n"), _ok("inactive\n")],
                                     SYSTEMCTL, "is-active", "iwd")
                    f.script_command([_ok("inactive\n"), _ok("active\n")],
                                     SYSTEMCTL, "is-active", "wpa_supplicant")
                f.set_services(iwd_active="inactive", wpa_active="active")
                f.seed_snapshot({
                    "backend": {"backend": "wpa_supplicant", "services": {}},
                    "file_backend_conf": {"exists": False, "content": None},
                })
                f.plugin._backend_switch["repair_of"] = "iwd"
                f.fail_command(SYSTEMCTL, "start", "iwd",
                               stderr="Job for iwd.service failed")
                if route == "generic":
                    result = await f.run_generic("iwd")
                else:
                    result = await f.run_steamos("iwd")
                self.assertFalse(result["success"])
                self.assertEqual(result.get("repair_of"), "iwd")
                self.assertTrue(result.get("rolled_back"))
                self.assertEqual(result.get("backend"), "wpa_supplicant")
                self.assertIn([SYSTEMCTL, "enable", "wpa_supplicant"],
                              f.run_calls)
                self.assertIn([SYSTEMCTL, "start", "wpa_supplicant"],
                              f.run_calls)
                if route == "generic":
                    # Previous layer uncovered: the generic conf is gone again.
                    self.assertIsNone(f.read_conf_file("generic"))
                else:
                    # Previous target restored through the helper route.
                    self.assertIn(
                        [f.BACKEND_HELPER, "write_config", "wpa_supplicant"],
                        f.run_calls)

    async def test_status_shows_both_with_drift(self):
        f = self.fixture()
        f.iface = None
        f.active_uuid = None
        f.set_conf("generic", "iwd")
        f.set_services(iwd_active="inactive", wpa_active="active")
        status = await f.status()
        live = status["live"]
        self.assertEqual(live.get("backend_desired"), "iwd")
        self.assertEqual(live.get("backend_effective"), "wpa_supplicant")
        services = live.get("backend_services") or {}
        self.assertEqual(services.get("iwd", {}).get("active"), "inactive")
        self.assertEqual(services.get("wpa_supplicant", {}).get("active"), "active")
        self.assertTrue(status["drift"].get("backend"))
        # live.wifi_backend shape unchanged (desired, backward-compat).
        self.assertEqual(live.get("wifi_backend"), "iwd")

    async def test_diagnostics_has_backend_triple(self):
        f = self.fixture()
        f.set_conf("generic", "iwd")
        f.set_services(iwd_active="active", wpa_active="inactive")
        diag = await f.diagnostics()
        self.assertEqual(diag.get("backend_desired"), "iwd")
        self.assertEqual(diag.get("backend_effective"), "iwd")
        self.assertIn("iwd", diag.get("backend_services") or {})
        # Failure path: unreadable services render as unknown, not an error.
        g = self.fixture()
        g.set_conf("generic", "iwd")
        g.set_services(iwd_active="active", wpa_active="inactive")
        g.script_command(_fail("dbus down"),
                         SYSTEMCTL, "is-active", "iwd")
        g.script_command(_fail("dbus down"),
                         SYSTEMCTL, "is-active", "wpa_supplicant")
        g.script_command(_fail("dbus down"),
                         SYSTEMCTL, "is-enabled", "iwd")
        g.script_command(_fail("dbus down"),
                         SYSTEMCTL, "is-enabled", "wpa_supplicant")
        bad = await g.diagnostics()
        self.assertEqual(bad.get("backend_effective"), "unknown")


if __name__ == "__main__":
    unittest.main()
