import ast
import json
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.check_delivery import (
    check_source_map_sources,
    normalize_source_map,
    snapshot_dist,
    verify_dist,
    check_python_and_shell,
    _render_update_fstring,
    get_release_history,
    release_notes,
    validate_release,
    validate_release_history,
    verify_archive,
)


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "package.json").write_text('{"version":"1.2.3"}\n', encoding="utf-8")
        (self.root / "CHANGELOG.md").write_text("# Changelog\n\n## Unreleased\n\n- Work\n\n## [1.2.3]\n\n- Stable notes\n\n## [1.2.2]\n\n- Old notes\n", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_release_validation_accepts_only_attested_canonical_release(self):
        self.assertEqual(validate_release(self.root, "1.2.3", "refs/heads/main", "undefined3491/WifiOptimizer", True), "v1.2.3")
        for version, ref, repository, tested in (("01.2.3", "refs/heads/main", "undefined3491/WifiOptimizer", True), ("1.x.3", "refs/heads/main", "undefined3491/WifiOptimizer", True), ("1.2.3-beta.1", "refs/heads/main", "undefined3491/WifiOptimizer", True), ("1.2.4", "refs/heads/main", "undefined3491/WifiOptimizer", True), ("1.2.3", "refs/heads/feature", "undefined3491/WifiOptimizer", True), ("1.2.3", "refs/tags/main", "undefined3491/WifiOptimizer", True), ("1.2.3", "main", "undefined3491/WifiOptimizer", True), ("1.2.3", "refs/heads/main", "other/repo", True), ("1.2.3", "refs/heads/main", "undefined3491/WifiOptimizer", False)):
            with self.subTest(version=version, ref=ref, repository=repository, tested=tested), self.assertRaises(ValueError):
                validate_release(self.root, version, ref, repository, tested)
        (self.root / "CHANGELOG.md").write_text("# Changelog\n\n## Unreleased\n\n- Work\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "changelog"):
            validate_release(self.root, "1.2.3", "refs/heads/main", "undefined3491/WifiOptimizer", True)

    def test_release_history_rejects_duplicates_invalid_and_non_increasing(self):
        for latest, tag, release in ((None, True, False), (None, False, True), ("1.2.3", False, False), ("1.2.4", False, False), ("bad", False, False)):
            with self.subTest(latest=latest, tag=tag, release=release), self.assertRaises(ValueError):
                validate_release_history("1.2.3", latest, tag, release)
        validate_release_history("1.2.3", "1.2.2", False, False)

    def test_release_notes_stop_at_next_changelog_section(self):
        text = "# Changelog\n\n## [1.2.3]\n\n- Keep\n\n## [1.2.2]\n\n- Exclude\n"
        self.assertEqual(release_notes(text, "1.2.3"), "- Keep")
        with self.assertRaises(ValueError):
            release_notes(text, "1.2.4")
        with self.assertRaisesRegex(ValueError, "empty"):
            release_notes("## [1.2.3]\n\n## [1.2.2]\n", "1.2.3")

    def test_archive_requires_exact_safe_unique_shipped_paths(self):
        required = ["plugin.json", "package.json", "main.py", "decky.pyi", "dist/index.js", "dist/index.js.map", "defaults/dispatcher.sh.tmpl"]
        archive = self.root / "bundle.tar"
        def write(entries):
            with tarfile.open(archive, "w") as tar:
                for name in entries:
                    info = tarfile.TarInfo(name)
                    data = b"x"
                    info.size = len(data)
                    import io
                    tar.addfile(info, io.BytesIO(data))
        prefix = "WifiOptimizer-1.2.3/"
        write([prefix + item for item in required])
        verify_archive(archive, "1.2.3")
        for entries in ([prefix + item for item in required[:-1]], [prefix + item for item in required] + [prefix + required[0]], [prefix + "../escape"] + [prefix + item for item in required]):
            write(entries)
            with self.subTest(entries=entries), self.assertRaises(ValueError):
                verify_archive(archive, "1.2.3")

    def test_api_history_only_treats_explicit_404_as_absent(self):
        def result(status, payload="{}"):
            return subprocess.CompletedProcess(
                [], 0 if status == 200 else 1,
                stdout=f"HTTP/2.0 {status} Response\r\ncontent-type: application/json\r\n\r\n{payload}",
                stderr="",
            )
        responses = [result(200, '{"tag_name":"v1.2.2","body":"Fix HTTP 404 handling in updater"}'), result(404), result(404)]
        with patch("scripts.check_delivery.subprocess.run", side_effect=responses):
            self.assertEqual(get_release_history("undefined3491/WifiOptimizer", "1.2.3"), ("1.2.2", False, False))
        with patch("scripts.check_delivery.subprocess.run", side_effect=[result(404), result(404), result(404)]):
            self.assertEqual(get_release_history("undefined3491/WifiOptimizer", "1.2.3"), (None, False, False))
        for failure in (result(500), result(403), subprocess.CompletedProcess([], 0, stdout='{"message":"no status"}', stderr=""), subprocess.TimeoutExpired("gh api", 10)):
            with patch("scripts.check_delivery.subprocess.run", side_effect=[failure]):
                with self.subTest(failure=failure), self.assertRaises(ValueError):
                    get_release_history("undefined3491/WifiOptimizer", "1.2.3")


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
        decky = source_map("decky://decky/plugin/WiFi%20Optimizer%20TMS/")
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
        for path in ("https://example.test/src/index.tsx", "../src/../secret.ts", "decky://decky/plugin/WiFi%20Optimizer/src/index.tsx"):
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
        equivalent = source_map("decky://decky/plugin/WiFi%20Optimizer%20TMS/")
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
