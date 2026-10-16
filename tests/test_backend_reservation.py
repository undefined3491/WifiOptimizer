"""Exercise isolated entry-method AST with inert effects; never import the plugin."""

import ast
import asyncio
import inspect
import unittest
from pathlib import Path
from types import SimpleNamespace


class SwitchFixture:
    def __init__(self, route="steamos"):
        self.route = route
        self.desired = "iwd"
        self.effective = "iwd"
        self.available = True
        self.lookup_error = False
        self.route_error = False
        self.launch_error = False
        self.info_error = False
        self.lookup_count = 0
        self.lookup_entered = asyncio.Event()
        self.lookup_release = asyncio.Event()
        self.worker_release = asyncio.Event()
        self.requests = []
        self.worker_tasks = []
        self.coroutines = []
        self.worker_starts = []

        source = Path(__file__).resolve().parents[1] / "main.py"
        tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
        plugin = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Plugin")
        names = {"_ensure_backend_switch_state", "start_backend_switch"}
        methods = [node for node in plugin.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in names]
        assert {node.name for node in methods} == names
        namespace = {
            # Fail closed on imports, file access or new unstubbed effects.
            "__builtins__": {"hasattr": hasattr, "dict": dict, "int": int, "str": str, "isinstance": isinstance, "Exception": Exception},
            "asyncio": SimpleNamespace(to_thread=self.lookup, create_task=self.launch),
            "time": SimpleNamespace(time=lambda: 1234),
            "decky": SimpleNamespace(logger=SimpleNamespace(info=self.log_info, error=lambda *_: None)),
        }
        exec(compile(ast.Module(body=methods, type_ignores=[]), str(source), "exec"), namespace)
        self.plugin = type("IsolatedSwitchEntry", (), {name: namespace[name] for name in names})()
        self.plugin._ensure_backend_switch_state()
        self.plugin._has_backend_tool = lambda: self.available
        self.plugin._read_desired_backend = lambda: (self.desired, None)
        self.plugin._read_effective_backend = lambda: (self.effective, {})
        self.plugin._get_backend_method = self.get_route
        self.plugin._backend_switch_worker = lambda target: self.worker("steamos", target)
        self.plugin._generic_backend_switch_worker = lambda target: self.worker("generic", target)

    async def lookup(self, function):
        readers = (
            self.plugin._read_desired_backend,
            self.plugin._read_effective_backend,
        )
        assert function in readers
        self.lookup_count += 1
        self.lookup_entered.set()
        await self.lookup_release.wait()
        if self.lookup_error:
            raise RuntimeError("lookup failed")
        return function()

    def get_route(self):
        if self.route_error:
            raise RuntimeError("worker selection failed")
        return self.route

    def log_info(self, *_):
        if self.info_error:
            raise RuntimeError("logging failed")

    def launch(self, coroutine):
        self.coroutines.append(coroutine)
        if self.launch_error:
            raise RuntimeError("task creation failed")
        task = asyncio.create_task(coroutine)
        self.worker_tasks.append(task)
        return task

    async def worker(self, route, target):
        try:
            self.worker_starts.append((route, target))
            await self.worker_release.wait()
        finally:
            self.plugin._backend_switch["in_progress"] = False

    def start(self, target="wpa_supplicant"):
        task = asyncio.create_task(self.plugin.start_backend_switch(target))
        self.requests.append(task)
        return task

    async def close(self):
        for task in self.requests:
            if not task.done():
                task.cancel()
        await asyncio.gather(*self.requests, return_exceptions=True)
        self.worker_release.set()
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        for coroutine in self.coroutines:
            coroutine.close()


class BackendReservationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.fixtures = []

    def fixture(self, route="steamos"):
        fixture = SwitchFixture(route)
        self.fixtures.append(fixture)
        return fixture

    async def asyncTearDown(self):
        for fixture in self.fixtures:
            await fixture.close()

    async def test_same_target_overlap_accepts_exactly_one_worker_on_both_routes(self):
        for route in ("steamos", "generic"):
            with self.subTest(route=route):
                f = self.fixture(route)
                first = f.start()
                await f.lookup_entered.wait()
                second = f.start()
                await asyncio.sleep(0)
                f.lookup_release.set()
                results = await asyncio.gather(first, second)
                await asyncio.sleep(0)
                self.assertEqual(sum(result["accepted"] for result in results), 1)
                self.assertEqual(results[1]["reason"], "in_progress")
                # The converged gate reads desired then effective (two
                # single-flight lookups); the overlap is rejected before
                # either read on the second request.
                self.assertEqual(f.lookup_count, 2)
                self.assertEqual(f.worker_starts, [(route, "wpa_supplicant")])
                self.assertEqual(len(f.worker_tasks), 1)
                self.assertIs(f.plugin._backend_switch_task, f.worker_tasks[0])
                self.assertTrue(f.plugin._backend_switch["in_progress"])

    async def test_pending_lookup_exposes_reserved_state(self):
        f = self.fixture()
        f.start()
        await f.lookup_entered.wait()
        self.assertEqual(f.plugin._backend_switch, {
            "in_progress": True, "phase": "switching", "target": "wpa_supplicant",
            "started_at": 1234, "result": None,
        })

    async def test_lookup_failure_restores_previous_result_and_allows_retry(self):
        f = self.fixture()
        previous = {"in_progress": False, "phase": "done", "target": "iwd", "started_at": 12, "result": {"success": True}}
        f.plugin._backend_switch.update(previous)
        f.lookup_error = True
        f.lookup_release.set()
        result = await f.start()
        self.assertFalse(result["accepted"])
        self.assertEqual(f.plugin._backend_switch, previous)
        self.assertEqual(f.worker_tasks, [])
        f.lookup_error = False
        self.assertTrue((await f.start())["accepted"])

    async def test_cancelled_lookup_propagates_and_restores_state_without_worker(self):
        f = self.fixture()
        previous = dict(f.plugin._backend_switch)
        request = f.start()
        await f.lookup_entered.wait()
        request.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await request
        self.assertEqual(f.plugin._backend_switch, previous)
        self.assertEqual(f.worker_tasks, [])
        f.lookup_release.set()
        self.assertTrue((await f.start())["accepted"])

    async def test_agreement_is_already_set_desired_only_is_repair(self):
        # True agreement (desired + effective) stays a cheap no-op that
        # preserves the previous terminal state and task.
        f = self.fixture()
        previous = {"in_progress": False, "phase": "failed", "target": "iwd", "started_at": 8, "result": {"success": False}}
        f.plugin._backend_switch.update(previous)
        marker = object()
        f.plugin._backend_switch_task = marker
        f.desired = "iwd"
        f.effective = "iwd"
        f.lookup_release.set()
        result = await f.start("iwd")
        self.assertEqual(result["reason"], "already_set")
        self.assertEqual(f.plugin._backend_switch, previous)
        self.assertIs(f.plugin._backend_switch_task, marker)
        self.assertEqual(f.worker_tasks, [])

    async def test_desired_only_divergence_accepts_repair(self):
        # Desired == target but effective disagrees: accepted as repair
        # (never already_set), with repair context for the worker.
        f = self.fixture()
        f.desired = "iwd"
        f.effective = "wpa_supplicant"
        f.lookup_release.set()
        result = await f.start("iwd")
        self.assertTrue(result["accepted"])
        self.assertTrue(result["repair"])
        self.assertEqual(f.plugin._backend_switch.get("repair_of"), "iwd")
        self.assertEqual(f.worker_starts, [("steamos", "iwd")])
        self.assertEqual(len(f.worker_tasks), 1)

    async def test_outstanding_reboot_rejects_until_terminal_success(self):
        f = self.fixture()
        f.desired = "iwd"
        f.effective = "iwd"
        f.lookup_release.set()
        f.plugin._backend_switch["result"] = {
            "success": False, "target": "iwd", "needs_reboot": True}
        previous = dict(f.plugin._backend_switch)
        result = await f.start("iwd")
        self.assertFalse(result["accepted"])
        self.assertEqual(result["reason"], "needs_reboot")
        self.assertEqual(f.plugin._backend_switch, previous)
        self.assertEqual(f.worker_tasks, [])
        # A later terminal success clears the outstanding reboot: the same
        # target is a cheap no-op again, not a reboot rejection.
        f.plugin._backend_switch["result"] = {
            "success": True, "target": "iwd", "needs_reboot": False}
        cleared = await f.start("iwd")
        self.assertEqual(cleared["reason"], "already_set")

    async def test_worker_selection_failure_releases_reservation(self):
        f = self.fixture()
        previous = dict(f.plugin._backend_switch)
        f.lookup_release.set()
        f.route_error = True
        self.assertFalse((await f.start())["accepted"])
        self.assertEqual(f.plugin._backend_switch, previous)
        f.route_error = False
        self.assertTrue((await f.start())["accepted"])

    async def test_task_creation_failure_closes_coroutine_and_releases_reservation(self):
        f = self.fixture()
        previous = dict(f.plugin._backend_switch)
        f.lookup_release.set()
        f.launch_error = True
        self.assertFalse((await f.start())["accepted"])
        self.assertEqual(f.plugin._backend_switch, previous)
        self.assertEqual(len(f.coroutines), 1)
        self.assertEqual(inspect.getcoroutinestate(f.coroutines[0]), inspect.CORO_CLOSED)
        self.assertEqual(f.worker_tasks, [])
        f.launch_error = False
        self.assertTrue((await f.start())["accepted"])

    async def test_rejections_preserve_existing_job_and_task(self):
        f = self.fixture()
        f.plugin._backend_switch.update(in_progress=True, phase="reconnecting", target="iwd")
        previous = dict(f.plugin._backend_switch)
        marker = object()
        f.plugin._backend_switch_task = marker
        self.assertEqual((await f.start("invalid"))["reason"], "invalid_backend")
        f.available = False
        self.assertEqual((await f.start())["reason"], "tool_missing")
        f.available = True
        self.assertEqual((await f.start())["reason"], "in_progress")
        self.assertEqual(f.plugin._backend_switch, previous)
        self.assertIs(f.plugin._backend_switch_task, marker)
        self.assertEqual(f.lookup_count, 0)

    async def test_post_handoff_error_does_not_release_worker_ownership(self):
        f = self.fixture()
        f.lookup_release.set()
        f.info_error = True
        await f.start()
        self.assertEqual(len(f.worker_tasks), 1)
        self.assertTrue(f.plugin._backend_switch["in_progress"])
        self.assertEqual((await f.start())["reason"], "in_progress")
        f.worker_release.set()
        await asyncio.gather(*f.worker_tasks)
        self.assertFalse(f.plugin._backend_switch["in_progress"])


if __name__ == "__main__":
    unittest.main()
