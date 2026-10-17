import json
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.check_delivery import (
    check_python_and_shell,
    check_source_map_sources,
    check_updater_contract,
    normalize_source_map,
    snapshot_dist,
    verify_dist,
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
        self.assertEqual(validate_release(self.root, "1.2.3", "refs/heads/main", "undefined3491/wifi-optimizer-tms", True), "v1.2.3")
        for version, ref, repository, tested in (("01.2.3", "refs/heads/main", "undefined3491/wifi-optimizer-tms", True), ("1.x.3", "refs/heads/main", "undefined3491/wifi-optimizer-tms", True), ("1.2.3-beta.1", "refs/heads/main", "undefined3491/wifi-optimizer-tms", True), ("1.2.4", "refs/heads/main", "undefined3491/wifi-optimizer-tms", True), ("1.2.3", "refs/heads/feature", "undefined3491/wifi-optimizer-tms", True), ("1.2.3", "refs/tags/main", "undefined3491/wifi-optimizer-tms", True), ("1.2.3", "main", "undefined3491/wifi-optimizer-tms", True), ("1.2.3", "refs/heads/main", "other/repo", True), ("1.2.3", "refs/heads/main", "undefined3491/WifiOptimizer", True), ("1.2.3", "refs/heads/main", "undefined3491/wifi-optimizer-tms", False)):
            with self.subTest(version=version, ref=ref, repository=repository, tested=tested), self.assertRaises(ValueError):
                validate_release(self.root, version, ref, repository, tested)
        (self.root / "CHANGELOG.md").write_text("# Changelog\n\n## Unreleased\n\n- Work\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "changelog"):
            validate_release(self.root, "1.2.3", "refs/heads/main", "undefined3491/wifi-optimizer-tms", True)

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
        prefix = "wifi-optimizer-tms-1.2.3/"
        write([prefix + item for item in required])
        verify_archive(archive, "1.2.3")
        for wrong_root in ("WifiOptimizer-1.2.3/", "wifi-optimizer-tms-main/", "wifi-optimizer-tms-beta/", "wifi-optimizer-tms-" + "a" * 40 + "/"):
            write([wrong_root + item for item in required])
            with self.subTest(root=wrong_root), self.assertRaisesRegex(ValueError, "exact release root"):
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
            self.assertEqual(get_release_history("undefined3491/wifi-optimizer-tms", "1.2.3"), ("1.2.2", False, False))
        with patch("scripts.check_delivery.subprocess.run", side_effect=[result(404), result(404), result(404)]):
            self.assertEqual(get_release_history("undefined3491/wifi-optimizer-tms", "1.2.3"), (None, False, False))
        for failure in (result(500), result(403), subprocess.CompletedProcess([], 0, stdout='{"message":"no status"}', stderr=""), subprocess.TimeoutExpired("gh api", 10)):
            with patch("scripts.check_delivery.subprocess.run", side_effect=[failure]):
                with self.subTest(failure=failure), self.assertRaises(ValueError):
                    get_release_history("undefined3491/wifi-optimizer-tms", "1.2.3")


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


class UpdaterContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "defaults").mkdir()
        (self.root / "decky.pyi").write_text("class Plugin: ...\n", encoding="utf-8")
        (self.root / "install.sh").write_text("#!/bin/bash\ntrue\n", encoding="utf-8")
        (self.root / "defaults/dispatcher.sh.tmpl").write_text("#!/bin/bash\ntrue\n", encoding="utf-8")
        source = Path(__file__).resolve().parents[1] / "main.py"
        self.conforming = source.read_text(encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def write_main(self, text):
        (self.root / "main.py").write_text(text, encoding="utf-8")

    def test_accepts_hardened_updater(self):
        self.write_main(self.conforming)
        check_updater_contract(self.root)

    def test_rejects_missing_updater_method(self):
        self.write_main("class Plugin:\n    pass\n")
        with self.assertRaisesRegex(ValueError, "missing updater methods"):
            check_updater_contract(self.root)

    def test_rejects_fixed_tmp_script_path(self):
        mutated = self.conforming.replace(
            "archive_path = os.path.join(stage_dir, \"update.tar.gz\")",
            "archive_path = os.path.join(stage_dir, \"update.tar.gz\")\n            script_path = \"/tmp/wifi-optimizer-update.sh\"",
        )
        self.assertNotEqual(mutated, self.conforming)
        self.write_main(mutated)
        with self.assertRaisesRegex(ValueError, "detached script"):
            check_updater_contract(self.root)

    def test_rejects_detached_popen_copy(self):
        mutated = self.conforming.replace(
            "restart_result = await asyncio.to_thread(",
            "subprocess.Popen([\"true\"])\n            restart_result = await asyncio.to_thread(",
        )
        self.assertNotEqual(mutated, self.conforming)
        self.write_main(mutated)
        with self.assertRaisesRegex(ValueError, "detached script"):
            check_updater_contract(self.root)

    def test_rejects_unchecked_curl_transfer(self):
        mutated = self.conforming.replace('                "--fail",\n', "")
        self.assertNotEqual(mutated, self.conforming)
        self.write_main(mutated)
        with self.assertRaisesRegex(ValueError, "--fail"):
            check_updater_contract(self.root)

    def test_rejects_relaxed_clean_env(self):
        mutated = self.conforming.replace(
            "self._run_cmd, curl_cmd, _UPDATE_CURL_TIMEOUT, True",
            "self._run_cmd, curl_cmd, _UPDATE_CURL_TIMEOUT, False",
        )
        self.assertNotEqual(mutated, self.conforming)
        self.write_main(mutated)
        with self.assertRaisesRegex(ValueError, "clean_env"):
            check_updater_contract(self.root)

    def test_rejects_wrong_commit_order(self):
        head, sep, tail = self.conforming.partition("_UPDATE_COMMIT_ORDER = (")
        self.assertTrue(sep)
        mutated_tail = tail.replace(
            '    "main.py",\n    "package.json",\n    "plugin.json",\n)',
            '    "plugin.json",\n    "package.json",\n    "main.py",\n)',
            1,
        )
        self.assertNotEqual(mutated_tail, tail)
        self.write_main(head + sep + mutated_tail)
        with self.assertRaisesRegex(ValueError, "commit order"):
            check_updater_contract(self.root)

    def test_rejects_copy_outside_ordered_loop(self):
        mutated = self.conforming.replace(
            "os.replace(os.path.join(payload_dir, rel), dest)",
            "shutil.copy(os.path.join(payload_dir, rel), dest)",
        )
        self.assertNotEqual(mutated, self.conforming)
        self.write_main(mutated)
        with self.assertRaisesRegex(ValueError, "os.replace"):
            check_updater_contract(self.root)

    def test_rejects_live_dir_removal(self):
        mutated = self.conforming.replace(
            "shutil.rmtree(stage_dir, ignore_errors=True)\n            restart_result",
            "os.rename(stage_dir, plugin_dir)\n            restart_result",
        )
        self.assertNotEqual(mutated, self.conforming)
        self.write_main(mutated)
        with self.assertRaisesRegex(ValueError, "never remove or rename"):
            check_updater_contract(self.root)

    def test_rejects_stage_only_but_wrong_target(self):
        mutated = self.conforming.replace(
            "shutil.rmtree(stage_dir, ignore_errors=True)",
            "shutil.rmtree(base_dir, ignore_errors=True)",
        )
        self.assertNotEqual(mutated, self.conforming)
        self.write_main(mutated)
        with self.assertRaisesRegex(ValueError, "only ever remove the stage dir"):
            check_updater_contract(self.root)

    def test_rejects_missing_error_code(self):
        mutated = self.conforming.replace('"restart_failed"', '"restart_broken"')
        self.assertNotEqual(mutated, self.conforming)
        self.write_main(mutated)
        with self.assertRaisesRegex(ValueError, "restart_failed"):
            check_updater_contract(self.root)

    def test_rejects_missing_phase(self):
        mutated = self.conforming.replace('"done_unknown"', '"done_maybe"')
        self.assertNotEqual(mutated, self.conforming)
        self.write_main(mutated)
        with self.assertRaisesRegex(ValueError, "done_unknown"):
            check_updater_contract(self.root)


if __name__ == "__main__":
    unittest.main()
