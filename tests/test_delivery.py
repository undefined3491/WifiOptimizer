import ast
import json
import tempfile
import unittest
from pathlib import Path

from scripts.check_delivery import (
    check_source_map_sources,
    normalize_source_map,
    snapshot_dist,
    verify_dist,
    check_python_and_shell,
    _render_update_fstring,
)


def source_map(prefix: str = "../", source_text: str = "export const value = 1;\n") -> dict:
    return {
        "version": 3,
        "file": "index.js",
        "sources": [f"{prefix}src/index.tsx", f"{prefix}node_modules/pkg/index.js"],
        "sourcesContent": [source_text, "module.exports = {};\n"],
        "names": ["value"],
        "mappings": "AAAA;AACA",
        "x_custom": {"retained": True},
    }


class SourceMapTests(unittest.TestCase):
    def test_normalizes_allowed_uri_prefix_and_crlf_only(self):
        relative = source_map()
        decky = source_map("decky://decky/plugin/WiFi%20Optimizer/")
        decky["sourcesContent"] = ["export const value = 1;\r\n", "module.exports = {};\r\n"]
        self.assertEqual(normalize_source_map(relative), normalize_source_map(decky))

    def test_preserves_mapping_and_other_fields(self):
        original = normalize_source_map(source_map())
        altered = source_map()
        altered["mappings"] = "AAAA;AACA;AACA"
        self.assertNotEqual(original, normalize_source_map(altered))
        altered = source_map()
        altered["x_custom"]["retained"] = False
        self.assertNotEqual(original, normalize_source_map(altered))

    def test_rejects_unsupported_or_ambiguous_source_paths(self):
        for path in ("https://example.test/src/index.tsx", "../src/../secret.ts"):
            data = source_map()
            data["sources"][0] = path
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, "source"):
                normalize_source_map(data)

    def test_checks_embedded_repository_sources_and_requires_entrypoint(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "src").mkdir()
            (root / "src/index.tsx").write_text("export const value = 1;\n", encoding="utf-8")
            check_source_map_sources(root, source_map())
            stale = source_map(source_text="export const value = 2;\n")
            with self.assertRaisesRegex(ValueError, "src/index.tsx"):
                check_source_map_sources(root, stale)
            missing = source_map()
            missing["sources"] = ["../src/types.ts"]
            missing["sourcesContent"] = ["type X = string;\n"]
            with self.assertRaisesRegex(ValueError, "src/index.tsx"):
                check_source_map_sources(root, missing)


class DistTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "dist").mkdir()
        (self.root / "src").mkdir()
        (self.root / "src/index.tsx").write_text("export const value = 1;\n", encoding="utf-8")
        (self.root / "dist/index.js").write_text("const value = 1;\n", encoding="utf-8")
        (self.root / "dist/index.js.map").write_text(json.dumps(source_map()), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_snapshot_and_verify_accept_semantically_equivalent_map(self):
        snapshot = self.root / "snapshot.json"
        snapshot_dist(self.root, snapshot)
        equivalent = source_map("decky://decky/plugin/WiFi%20Optimizer/")
        equivalent["sourcesContent"] = ["export const value = 1;\r\n", "module.exports = {};\r\n"]
        (self.root / "dist/index.js.map").write_text(json.dumps(equivalent), encoding="utf-8")
        (self.root / "dist/index.js").write_bytes(b"const value = 1;\r\n")
        verify_dist(self.root, snapshot)

    def test_rejects_stale_js_mapping_and_embedded_sources(self):
        snapshot = self.root / "snapshot.json"
        snapshot_dist(self.root, snapshot)
        (self.root / "dist/index.js").write_text("const value = 2;\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "index.js"):
            verify_dist(self.root, snapshot)
        (self.root / "dist/index.js").write_text("const value = 1;\n", encoding="utf-8")
        changed = source_map()
        changed["mappings"] = "AAAA;AADA"
        (self.root / "dist/index.js.map").write_text(json.dumps(changed), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "map"):
            verify_dist(self.root, snapshot)
        changed = source_map(source_text="export const value = 2;\n")
        (self.root / "dist/index.js.map").write_text(json.dumps(changed), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "src/index.tsx"):
            snapshot_dist(self.root, self.root / "stale.json")

    def test_missing_bundle_or_map_is_actionable(self):
        snapshot = self.root / "snapshot.json"
        for relative in ("dist/index.js", "dist/index.js.map"):
            target = self.root / relative
            contents = target.read_bytes()
            target.unlink()
            with self.subTest(relative=relative), self.assertRaisesRegex(ValueError, relative):
                snapshot_dist(self.root, snapshot)
            target.write_bytes(contents)


class SyntaxTests(unittest.TestCase):
    def test_rejects_unrendered_fstring_conversions_and_format_specs(self):
        for expression, message in (("value!r", "conversion"), ("value:>10", "format specifier")):
            with self.subTest(expression=expression), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                (root / "defaults").mkdir()
                main = (
                    "class Plugin:\n"
                    "    async def apply_update(self):\n"
                    "        value = 'example'\n"
                    f"        script = f'''echo {{{expression}}}\\n'''\n"
                )
                (root / "main.py").write_text(main, encoding="utf-8")
                (root / "decky.pyi").write_text("class Plugin: ...\n", encoding="utf-8")
                (root / "install.sh").write_text("#!/bin/bash\ntrue\n", encoding="utf-8")
                (root / "defaults/dispatcher.sh.tmpl").write_text("#!/bin/bash\ntrue\n", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, message):
                    _render_update_fstring(ast.parse(main, filename="main.py"))

    def test_rejects_malformed_generated_update_script(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "defaults").mkdir()
            (root / "main.py").write_text(
                'class Plugin:\n'
                '    async def apply_update(self):\n'
                '        script = f"""if then\\n"""\n',
                encoding="utf-8",
            )
            (root / "decky.pyi").write_text("class Plugin: ...\n", encoding="utf-8")
            (root / "install.sh").write_text("#!/bin/bash\ntrue\n", encoding="utf-8")
            (root / "defaults/dispatcher.sh.tmpl").write_text("#!/bin/bash\ntrue\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "generated script"):
                check_python_and_shell(root)


if __name__ == "__main__":
    unittest.main()
