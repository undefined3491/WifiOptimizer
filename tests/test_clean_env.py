"""Isolated clean-env default tests (red first) for the S-BE-06 mechanism fix.

Never import the real root plugin; never spawn subprocesses. Pattern:
tests/test_backend_state.py (AST-extract + fail-closed builtins + mocked
subprocess.run capturing the env kwarg).

`CleanEnvFixture` AST-extracts `Plugin._run_cmd` from main.py and execs it
against fail-closed builtins with a stubbed `os.environ` (poisoned with
`LD_LIBRARY_PATH`, as inherited from Decky's PyInstaller bundle) and a
mocked `subprocess.run`. Static tests parse main.py with `ast`: the
signature default must be `True`, no unjustified `clean_env=False`
opt-outs may exist (keyword or positional, direct or `to_thread`
wrappers), and the direct call-site count must match the audit (61).
"""

import ast
import re
import unittest
from pathlib import Path
from types import SimpleNamespace

SOURCE = Path(__file__).resolve().parents[1] / "main.py"

AUDIT = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "audits"
    / "2026-10-17-clean-env-audit.md"
)

EXPECTED_DIRECT_CALL_SITES = 61

POISONED_ENV = {
    "LD_LIBRARY_PATH": "/tmp/_MEI0000",
    "PATH": "/usr/bin:/bin",
    "CLEAN_ENV_SENTINEL": "keep-me",
}


class _TimeoutExpired(Exception):
    """Stand-in for subprocess.TimeoutExpired (never spawn real children)."""


class CleanEnvFixture:
    """AST-extracted `_run_cmd` over a poisoned env and capturing run mock."""

    def __init__(self):
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
        plugin_node = next(
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "Plugin"
        )
        run_cmd_node = next(
            node
            for node in plugin_node.body
            if isinstance(node, ast.FunctionDef) and node.name == "_run_cmd"
        )
        self.calls = []
        fixture = self

        def _fake_run(cmd, **kwargs):
            fixture.calls.append((list(cmd), dict(kwargs)))
            return SimpleNamespace(returncode=0, stdout="  ok  ", stderr="")

        namespace = {
            "__builtins__": {
                "str": str,
                "int": int,
                "bool": bool,
                "list": list,
                "dict": dict,
                "Exception": Exception,
                "FileNotFoundError": FileNotFoundError,
            },
            "os": SimpleNamespace(environ=dict(POISONED_ENV)),
            "subprocess": SimpleNamespace(
                run=_fake_run,
                TimeoutExpired=_TimeoutExpired,
            ),
        }
        exec(
            compile(
                ast.Module(body=[run_cmd_node], type_ignores=[]),
                str(SOURCE),
                "exec",
            ),
            namespace,
        )
        self.probe_self = SimpleNamespace()
        self.run_cmd = namespace["_run_cmd"].__get__(self.probe_self)

    def last_env(self):
        return self.calls[-1][1].get("env")


def _is_false(node):
    return isinstance(node, ast.Constant) and node.value is False


def _false_opt_outs(tree):
    """Find unjustified `clean_env=False` in keyword and positional forms.

    Direct `self._run_cmd(cmd, timeout, clean_env)`: flag is the 3rd
    positional argument. `asyncio.to_thread(self._run_cmd, cmd, timeout,
    clean_env)` wrappers: flag is the 4th overall positional argument.
    """
    found = []

    class _Visitor(ast.NodeVisitor):
        def __init__(self):
            self.stack = []

        def visit_FunctionDef(self, node):
            self.stack.append(node.name)
            self.generic_visit(node)
            self.stack.pop()

        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_Call(self, node):
            func = node.func
            enclosing = self.stack[-1] if self.stack else "<?>"
            if isinstance(func, ast.Attribute) and func.attr == "_run_cmd":
                for kw in node.keywords:
                    if kw.arg == "clean_env" and _is_false(kw.value):
                        found.append((node.lineno, "keyword", enclosing))
                if len(node.args) >= 3 and _is_false(node.args[2]):
                    found.append((node.lineno, "positional-direct", enclosing))
            elif isinstance(func, ast.Attribute) and func.attr == "to_thread":
                idx = next(
                    (
                        i
                        for i, arg in enumerate(node.args)
                        if isinstance(arg, ast.Attribute) and arg.attr == "_run_cmd"
                    ),
                    None,
                )
                if idx is not None:
                    for kw in node.keywords:
                        if kw.arg == "clean_env" and _is_false(kw.value):
                            found.append((node.lineno, "keyword-to_thread", enclosing))
                    if len(node.args) > idx + 3 and _is_false(node.args[idx + 3]):
                        found.append(
                            (node.lineno, "positional-to_thread", enclosing)
                        )
            self.generic_visit(node)

    _Visitor().visit(tree)
    return found


def _direct_call_lines(tree):
    return {
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "_run_cmd"
    }


def _direct_call_count(tree):
    return len(_direct_call_lines(tree))


def _audit_direct_lines():
    section = AUDIT.read_text(encoding="utf-8").split(
        "## Direct call sites (61)", 1
    )[1].split("## ", 1)[0]
    return {
        int(m.group(1))
        for m in re.finditer(r"^-\s+`main\.py:(\d+)`", section, re.MULTILINE)
    }


def _parse_main():
    return ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))


def _run_cmd_signature_default(tree):
    plugin_node = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "Plugin"
    )
    run_cmd_node = next(
        node
        for node in plugin_node.body
        if isinstance(node, ast.FunctionDef) and node.name == "_run_cmd"
    )
    args = run_cmd_node.args
    names = [a.arg for a in args.args[-len(args.defaults):]]
    return dict(zip(names, args.defaults)).get("clean_env")


class CleanEnvTests(unittest.TestCase):
    def test_default_strips_ld_library_path(self):
        fx = CleanEnvFixture()
        result = fx.run_cmd(["/usr/bin/systemctl", "is-active", "plugin_loader"])
        self.assertTrue(result["success"])
        env = fx.last_env()
        self.assertIsNotNone(env)
        self.assertNotIn("LD_LIBRARY_PATH", env)
        self.assertEqual(env.get("CLEAN_ENV_SENTINEL"), "keep-me")

    def test_explicit_true_strips(self):
        fx = CleanEnvFixture()
        fx.run_cmd(["/usr/bin/curl", "--version"], clean_env=True)
        self.assertNotIn("LD_LIBRARY_PATH", fx.last_env())
        fx.run_cmd(["/usr/bin/curl", "--version"], 5, True)
        env = fx.last_env()
        self.assertIsNotNone(env)
        self.assertNotIn("LD_LIBRARY_PATH", env)
        self.assertEqual(env.get("CLEAN_ENV_SENTINEL"), "keep-me")

    def test_explicit_false_passes_through(self):
        fx = CleanEnvFixture()
        fx.run_cmd(["/usr/bin/curl", "--version"], clean_env=False)
        self.assertIsNone(fx.last_env())

    def test_positional_false_detected(self):
        snippet = (
            "import asyncio\n"
            "class Plugin:\n"
            "    async def worker(self, cmd):\n"
            "        a = self._run_cmd(cmd, 5, False)\n"
            "        b = await asyncio.to_thread(self._run_cmd, cmd, 5, False)\n"
            "        c = self._run_cmd(cmd, timeout=5, clean_env=False)\n"
        )
        found = _false_opt_outs(ast.parse(snippet))
        forms = sorted(form for _, form, _ in found)
        self.assertEqual(
            forms, ["keyword", "positional-direct", "positional-to_thread"]
        )

    def test_signature_default_is_true(self):
        default = _run_cmd_signature_default(_parse_main())
        self.assertIsInstance(default, ast.Constant)
        self.assertTrue(default.value)

    def test_no_unjustified_false_opt_outs(self):
        self.assertEqual(_false_opt_outs(_parse_main()), [])

    def test_call_site_count_matches_audit(self):
        tree = _parse_main()
        self.assertEqual(_direct_call_count(tree), EXPECTED_DIRECT_CALL_SITES)
        self.assertEqual(_audit_direct_lines(), _direct_call_lines(tree))


if __name__ == "__main__":
    unittest.main()
