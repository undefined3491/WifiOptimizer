"""Isolated staged-updater tests; never import the plugin.

Covers the Stable-only single-job updater contract (spec D2-D5): job
reservation with cross-exclusion, same-filesystem staging, validated
transfer/identity, per-file commit with truthful restart reporting, plus
the Beta-removal guard (D1). The fixture AST-extracts the update entry
methods with fail-closed builtins; network/process effects are scripted.
"""

import ast
import asyncio
import io
import json
import os
import shutil
import tarfile
import tempfile
import threading
import unittest
from unittest.mock import patch
from pathlib import Path
from types import SimpleNamespace

SOURCE = Path(__file__).resolve().parents[1] / "main.py"

# Entry surface the hardened updater must expose. apply_update and
# check_for_update keep their IPC names; only the start shape changes.
ENTRY_METHODS = {
    "_ensure_update_job_state",
    "apply_update",
    "check_for_update",
    "_ensure_backend_switch_state",
    "start_backend_switch",
}

# Shipped payload allowlist and fixed per-file commit order (D3/D4).
ALLOWLIST = (
    "defaults/dispatcher.sh.tmpl",
    "decky.pyi",
    "dist/index.js",
    "dist/index.js.map",
    "main.py",
    "package.json",
    "plugin.json",
)

CURRENT_VERSION = "0.11.6"
NEXT_VERSION = "0.12.0"
REPOSITORY = "undefined3491/wifi-optimizer-tms"


class DeliveryFixture:
    """Temp live plugin dir + scripted _run_cmd + extracted update entry."""

    def __init__(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.live = self.base / "plugin"
        (self.live / "dist").mkdir(parents=True)
        (self.live / "defaults").mkdir(parents=True)
        (self.live / "py_modules").mkdir(parents=True)
        self._seed_live()
        self.settings = {}
        self.logs = []
        # Scripted transfer outcomes.
        self.curl_behavior = "ok"  # ok | corrupt | timeout | version_mismatch
        self.resolve_behavior = "ok"  # ok | no_release | no_update
        self.restart_rc = 0
        self.download_gate = None  # optional threading.Event held during curl
        self.run_calls = []
        self.systemctl_calls = []

        tree = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
        plugin = next(
            node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Plugin"
        )
        methods = [
            node
            for node in plugin.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in ENTRY_METHODS
        ]
        # Red before the hardened updater exists: fail with AssertionError
        # (never ImportError/NameError) without executing current code.
        assert {node.name for node in methods} == ENTRY_METHODS, (
            f"update entry surface missing: {ENTRY_METHODS - {node.name for node in methods}}"
        )
        namespace = {
            "__builtins__": {
                "dict": dict,
                "list": list,
                "str": str,
                "int": int,
                "bool": bool,
                "len": len,
                "isinstance": isinstance,
                "hasattr": hasattr,
                "getattr": getattr,
                "sorted": sorted,
                "enumerate": enumerate,
                "range": range,
                "open": open,
                "Exception": Exception,
                "ValueError": ValueError,
                "RuntimeError": RuntimeError,
            },
            "asyncio": asyncio,
            "time": __import__("time"),
            "os": os,
            "json": json,
            "tarfile": tarfile,
            "shutil": shutil,
            "decky": SimpleNamespace(
                logger=SimpleNamespace(
                    info=self.logs.append,
                    error=self.logs.append,
                ),
                DECKY_PLUGIN_DIR=str(self.live),
                DECKY_PLUGIN_VERSION=CURRENT_VERSION,
            ),
            "_load_settings": lambda: dict(self.settings),
        }
        exec(compile(ast.Module(body=methods, type_ignores=[]), str(SOURCE), "exec"), namespace)
        self.plugin = type("IsolatedUpdateEntry", (), {name: namespace[name] for name in ENTRY_METHODS})()
        self.plugin._run_cmd = self._fake_run_cmd
        self.plugin._unexpected_response = lambda e: {
            "accepted": False,
            "reason": "unexpected",
            "message": str(e),
        }
        self.plugin._has_backend_tool = lambda: True
        self.plugin._read_desired_backend = lambda: ("iwd", None)
        self.plugin._read_effective_backend = lambda: ("iwd", {})
        self.plugin._get_backend_method = lambda: "steamos"
        self.plugin._ensure_update_job_state()
        self.plugin._ensure_backend_switch_state()

    # -- live/stage helpers ------------------------------------------------

    def _seed_live(self):
        payload = {
            "plugin.json": json.dumps({"name": "WiFi Optimizer TMS", "api_version": 1}),
            "package.json": json.dumps({"name": "wifi-optimizer-tms", "version": CURRENT_VERSION}),
            "main.py": "# live backend\n",
            "decky.pyi": "class Plugin: ...\n",
            "dist/index.js": "console.log('live');\n",
            "dist/index.js.map": json.dumps({"version": 3, "mappings": "AAAA"}),
            "defaults/dispatcher.sh.tmpl": "#!/bin/bash\n# live\n",
        }
        for rel, text in payload.items():
            (self.live / rel).write_text(text, encoding="utf-8")

    def snapshot_live(self):
        return {
            rel: (self.live / rel).read_bytes()
            for rel in ALLOWLIST
            if (self.live / rel).is_file()
        }

    def stage_dirs(self):
        return [p for p in self.base.iterdir() if p.name.startswith(".wifi-optimizer-stage-")]

    def build_tarball(self, path, version, package_version=None, plugin_name=None, corrupt=False):
        if corrupt:
            Path(path).write_bytes(b"not a tarball")
            return
        root = f"wifi-optimizer-tms-{version}"
        files = {
            "plugin.json": json.dumps(
                {"name": "WiFi Optimizer TMS" if plugin_name is None else plugin_name, "api_version": 1}
            ),
            "package.json": json.dumps(
                {
                    "name": "wifi-optimizer-tms",
                    "version": version if package_version is None else package_version,
                }
            ),
            "main.py": "# updated backend\n",
            "decky.pyi": "class Plugin: ...\n",
            "dist/index.js": "console.log('new');\n",
            "dist/index.js.map": json.dumps({"version": 3, "mappings": "AAAA"}),
            "defaults/dispatcher.sh.tmpl": "#!/bin/bash\n# new\n",
        }
        with tarfile.open(path, "w:gz") as tar:
            for rel, text in files.items():
                data = text.encode("utf-8")
                info = tarfile.TarInfo(f"{root}/{rel}")
                info.size = len(data)
                tar.addfile(info, io.BytesIO(data))

    # -- scripted process effects ------------------------------------------

    def _fake_run_cmd(self, cmd, timeout=5, clean_env=False):
        self.run_calls.append((list(cmd), timeout, clean_env))
        if cmd[0].endswith("curl"):
            joined = " ".join(cmd)
            if "api.github.com" in joined:
                if self.resolve_behavior == "no_release":
                    return {"success": False, "stdout": "", "stderr": "boom", "returncode": 7}
                tag = CURRENT_VERSION if self.resolve_behavior == "no_update" else NEXT_VERSION
                return {
                    "success": True,
                    "stdout": json.dumps({"tag_name": f"v{tag}"}),
                    "stderr": "",
                    "returncode": 0,
                }
            if self.download_gate is not None and not self.download_gate.wait(timeout=10):
                return {"success": False, "stdout": "", "stderr": "Command timed out", "returncode": -1}
            if self.curl_behavior == "timeout":
                return {"success": False, "stdout": "", "stderr": "Command timed out", "returncode": -1}
            out_index = cmd.index("-o") + 1
            out_path = cmd[out_index]
            if self.curl_behavior == "corrupt":
                self.build_tarball(out_path, NEXT_VERSION, corrupt=True)
            elif self.curl_behavior == "version_mismatch":
                self.build_tarball(out_path, NEXT_VERSION, package_version="9.9.9")
            else:
                self.build_tarball(out_path, NEXT_VERSION)
            return {"success": True, "stdout": "", "stderr": "", "returncode": 0}
        if cmd[0].endswith("systemctl"):
            self.systemctl_calls.append(list(cmd))
            rc = self.restart_rc
            return {
                "success": rc == 0,
                "stdout": "",
                "stderr": "" if rc == 0 else "restart failed",
                "returncode": rc,
            }
        raise RuntimeError(f"unstubbed command: {cmd}")

    def curl_calls(self):
        return [call for call in self.run_calls if call[0][0].endswith("curl") and "api.github.com" not in " ".join(call[0])]

    async def close(self):
        task = getattr(self.plugin, "_update_task", None)
        if task is not None and not task.done():
            task.cancel()
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass
        self.temp.cleanup()


class DeliveryUpdateTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.fixtures = []

    def fixture(self):
        fixture = DeliveryFixture()
        self.fixtures.append(fixture)
        return fixture

    async def asyncTearDown(self):
        for fixture in self.fixtures:
            await fixture.close()

    async def test_concurrent_update_rejected(self):
        fx = self.fixture()
        fx.download_gate = threading.Event()
        first = await fx.plugin.apply_update()
        assert first.get("accepted") is True, f"first start must be accepted: {first}"
        await asyncio.sleep(0.5)
        assert fx.plugin._update_job.get("phase") == "downloading"
        second = await fx.plugin.apply_update()
        assert second.get("accepted") is False, f"overlap must be rejected: {second}"
        assert second.get("reason") == "in_progress", second
        # Rejection restores previous state: still the first job, no result.
        assert fx.plugin._update_job.get("target") == NEXT_VERSION
        assert fx.plugin._update_job.get("result") is None
        fx.download_gate.set()
        await fx.plugin._update_task
        assert fx.plugin._update_job.get("phase") == "restart_requested", fx.plugin._update_job

    async def test_update_during_switch_rejected_and_reverse(self):
        fx = self.fixture()
        fx.plugin._backend_switch.update({"in_progress": True, "phase": "switching", "target": "wpa_supplicant"})
        rejected = await fx.plugin.apply_update()
        assert rejected.get("accepted") is False, rejected
        assert rejected.get("reason") == "switch_in_progress", rejected
        assert fx.plugin._update_job.get("in_progress") is False
        assert fx.plugin._update_job.get("phase") == "idle"
        fx.plugin._backend_switch.update({"in_progress": False, "phase": "idle", "target": None})
        # Reverse: an in-progress update excludes the backend switch.
        fx.download_gate = threading.Event()
        started = await fx.plugin.apply_update()
        assert started.get("accepted") is True, started
        await asyncio.sleep(0.5)
        reverse = await fx.plugin.start_backend_switch("iwd")
        assert reverse.get("accepted") is False, reverse
        assert reverse.get("reason") == "update_in_progress", reverse
        fx.download_gate.set()
        await fx.plugin._update_task

    async def test_corrupt_archive_leaves_live_identical(self):
        fx = self.fixture()
        before = fx.snapshot_live()
        fx.curl_behavior = "corrupt"
        started = await fx.plugin.apply_update()
        assert started.get("accepted") is True, started
        await fx.plugin._update_task
        job = fx.plugin._update_job
        assert job.get("phase") == "failed", job
        assert (job.get("result") or {}).get("errors") == ["archive_invalid"], job.get("result")
        assert fx.snapshot_live() == before
        assert fx.stage_dirs() == []
        assert fx.systemctl_calls == []

    async def test_identity_mismatch_stops_before_commit(self):
        fx = self.fixture()
        before = fx.snapshot_live()
        fx.curl_behavior = "version_mismatch"
        started = await fx.plugin.apply_update()
        assert started.get("accepted") is True, started
        await fx.plugin._update_task
        job = fx.plugin._update_job
        assert job.get("phase") == "failed", job
        assert (job.get("result") or {}).get("errors") == ["identity_mismatch"], job.get("result")
        assert fx.snapshot_live() == before
        assert fx.stage_dirs() == []
        assert fx.systemctl_calls == []

    async def test_live_dir_never_removed(self):
        fx = self.fixture()
        removed = []
        real_rmtree = shutil.rmtree

        def guarded_rmtree(path, *args, **kwargs):
            if os.path.realpath(path) == os.path.realpath(fx.live):
                removed.append(path)
                raise AssertionError("live dir must never be removed")
            return real_rmtree(path, *args, **kwargs)

        replaced = []
        real_replace = os.replace

        def recording_replace(src, dst, *args, **kwargs):
            replaced.append((str(src), str(dst)))
            return real_replace(src, dst, *args, **kwargs)

        with patch.object(shutil, "rmtree", guarded_rmtree):
            with patch.object(os, "replace", recording_replace):
                started = await fx.plugin.apply_update()
                assert started.get("accepted") is True, started
                await fx.plugin._update_task
        assert removed == []
        assert fx.live.is_dir()
        assert [Path(dst).relative_to(fx.live).as_posix() for _, dst in replaced] == list(ALLOWLIST)
        job = fx.plugin._update_job
        assert job.get("phase") == "restart_requested", job
        result = job.get("result") or {}
        assert result.get("errors") == [], result
        assert result.get("file_commit", {}).get("files") == "7/7", result
        assert fx.stage_dirs() == []
        assert len(fx.systemctl_calls) == 1

    async def test_curl_timeout_no_restart(self):
        fx = self.fixture()
        before = fx.snapshot_live()
        fx.curl_behavior = "timeout"
        started = await fx.plugin.apply_update()
        assert started.get("accepted") is True, started
        await fx.plugin._update_task
        job = fx.plugin._update_job
        assert job.get("phase") == "failed", job
        assert (job.get("result") or {}).get("errors") == ["download_failed"], job.get("result")
        assert fx.snapshot_live() == before
        assert fx.stage_dirs() == []
        assert fx.systemctl_calls == []

    async def test_commit_failure_withholds_restart_with_partial(self):
        fx = self.fixture()
        before = fx.snapshot_live()
        calls = []
        real_replace = os.replace

        def failing_replace(src, dst, *args, **kwargs):
            calls.append(Path(dst).relative_to(fx.live).as_posix())
            if len(calls) == 4:
                raise OSError("disk full")
            return real_replace(src, dst, *args, **kwargs)

        with patch.object(os, "replace", failing_replace):
            started = await fx.plugin.apply_update()
            assert started.get("accepted") is True, started
            await fx.plugin._update_task
        job = fx.plugin._update_job
        assert job.get("phase") == "failed", job
        result = job.get("result") or {}
        assert result.get("errors") == ["commit_failed:dist/index.js.map"], result
        assert result.get("file_commit", {}).get("files") == "3/7", result
        # Restart withheld, stage retained for retry, partial live state.
        assert fx.systemctl_calls == []
        assert len(fx.stage_dirs()) == 1
        for rel in list(ALLOWLIST)[:3]:
            assert (fx.live / rel).read_bytes() != before[rel]
        for rel in list(ALLOWLIST)[3:]:
            assert (fx.live / rel).read_bytes() == before[rel]

    def test_beta_channel_gone(self):
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
        plugin = next(
            node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Plugin"
        )
        names = {
            node.name
            for node in plugin.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        assert "set_update_channel" not in names, "set_update_channel must be removed"
        defaults = next(
            node for node in tree.body
            if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "DEFAULT_SETTINGS" for t in node.targets)
        )
        keys = {k.value for k in defaults.value.keys if isinstance(k, ast.Constant)}
        assert "update_channel" not in keys, "DEFAULT_SETTINGS must not carry update_channel"
        update_source = "\n".join(
            ast.get_source_segment(SOURCE.read_text(encoding="utf-8"), node)
            for node in plugin.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name in {"check_for_update", "apply_update"}
        )
        # No beta branch reads/downloads, no channel plumbing — but the
        # ex-beta version rule stays until the known field installation
        # migrates (stored "beta" strips automatically via settings merge).
        for marker in ("refs/heads/beta", "ref=beta", "update_channel", "set_update_channel"):
            assert marker not in update_source, f"Stable updater must not contain {marker!r}"
        assert '"-beta" in current' in update_source, "ex-beta version rule must be kept"


if __name__ == "__main__":
    unittest.main()
