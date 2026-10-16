import contextlib
import importlib.util
import io
import json
import pathlib
import os
import sys
import tempfile
import unittest
from unittest.mock import patch
from unittest.mock import MagicMock

PATH = pathlib.Path(__file__).parents[1] / 'scripts' / 'collect_deck_inventory.py'


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(PATH.exists(), 'standalone inventory collector is missing')
        spec = importlib.util.spec_from_file_location('inventory', PATH)
        self.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)

    def test_unsupported_platform_never_reads_or_runs(self):
        with patch.object(self.m.sys, 'platform', 'win32'), patch.object(self.m, 'read_file', side_effect=AssertionError), patch.object(self.m, 'query', side_effect=AssertionError), contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(self.m.main(['--decky-home', '/private/user']), 2)
        self.assertEqual(json.loads(output.getvalue())['state'], 'unsupported_platform')

    def test_missing_decky_home_does_not_collect_an_empty_false_inventory(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = str(pathlib.Path(directory) / 'missing')
            with patch.object(self.m.sys, 'platform', 'linux'), patch.object(self.m, 'collect', side_effect=AssertionError), contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(self.m.main(['--decky-home', missing]), 2)
            self.assertEqual(json.loads(output.getvalue())['state'], 'invalid_decky_home')

    @unittest.skipUnless(sys.platform == 'linux', 'Real pipe readiness requires Linux')
    def test_linux_pipe_reader_handles_real_child_and_enforces_output_limit(self):
        # Use a harmless child instead of real NM/system services. Only bypass
        # the separately tested command grammar at this process-I/O boundary.
        with patch.object(self.m, 'allowed', return_value=True):
            self.assertEqual(self.m.query([sys.executable, '-c', 'print("fixture")']), {'state': 'ok', 'text': 'fixture\n'})
            large = self.m.query([sys.executable, '-c', 'import sys; sys.stdout.write("x" * 100000)'])
            failed = self.m.query([sys.executable, '-c', 'import sys; sys.exit(7)'])
        self.assertEqual(large['state'], 'oversize')
        self.assertEqual(failed, {'state': 'failed', 'exit_code': 7})

    @unittest.skipUnless(sys.platform == 'linux', 'FIFO fixture requires Linux')
    def test_fifo_is_rejected_without_opening_a_reader(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            path = root / 'pipe'
            os.mkfifo(path)
            self.assertEqual(self.m.read_file(path, root), {'state': 'invalid'})

    def test_file_states_and_bounds(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            self.assertEqual(self.m.read_file(root / 'missing', root)['state'], 'absent')
            path = root / 'file'
            path.write_bytes(b'x' * 20)
            self.assertEqual(self.m.read_file(path, root, 10)['state'], 'oversize')
            self.assertEqual(self.m.read_file(root, root)['state'], 'invalid')
            self.assertEqual(self.m.read_file(root.parent / 'outside', root)['state'], 'invalid')
            with patch.object(self.m.os, 'open', side_effect=PermissionError('SECRET')):
                self.assertEqual(self.m.read_file(path, root)['state'], 'permission_denied')

    def test_pseudofile_size_does_not_hide_short_actual_value(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            path = root / 'power'
            path.write_bytes(b'on\n')
            metadata = list(path.stat())
            metadata[6] = 4096  # sysfs advertises a page even for a short attribute
            with patch.object(self.m.os, 'fstat', return_value=os.stat_result(metadata)):
                self.assertEqual(self.m.scalar(path, root, '(on|auto)'), {'state': 'ok', 'value': 'on'})

    def test_short_reads_are_not_reported_as_complete_fingerprints(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            path = root / 'file'
            path.write_bytes(b'abcdef')
            with patch.object(self.m.os, 'read', side_effect=[b'abc', b'def', b'']):
                self.assertEqual(self.m.read_file(path, root, 10), {'state': 'ok', 'data': b'abcdef'})

    def test_symlink_escape_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            safe = root / 'safe'
            safe.mkdir()
            outside = root / 'private'
            outside.write_text('SECRET')
            link = safe / 'escape'
            try:
                link.symlink_to(outside)
            except OSError:
                self.skipTest('Host does not permit symlink creation')
            self.assertEqual(self.m.read_file(link, safe)['state'], 'invalid')

    def test_command_grammar_and_error_privacy(self):
        for args in [ ['/usr/bin/nmcli', 'connection', 'up'], ['/bin/sh', '-c', 'true'], ['/usr/bin/iw', 'dev', '../bad', 'get', 'power_save'], ['/usr/bin/tc', 'qdisc', 'replace'] ]:
            with patch.object(self.m.subprocess, 'Popen', side_effect=AssertionError):
                self.assertEqual(self.m.query(args)['state'], 'invalid')
        with patch.object(self.m.subprocess, 'Popen', side_effect=PermissionError('SECRET-SSID')):
            result = self.m.query(['/usr/bin/nmcli', '--version'])
        self.assertEqual(result['state'], 'permission_denied')
        self.assertNotIn('SECRET', json.dumps(result))

    def test_command_timeout_and_output_limit(self):
        for chunks, ready, expected in [([b'x' * (self.m.LIMIT + 1)], True, 'oversize'), ([], False, 'timeout'), ([b'version 1.2', b''], True, 'ok')]:
            process = MagicMock()
            process.wait.return_value = 0
            process.poll.return_value = None
            selector = MagicMock()
            selector.__enter__.return_value = selector
            selector.select.return_value = [object()] if ready else []
            with patch.object(self.m.subprocess, 'Popen', return_value=process) as popen, patch.object(self.m.selectors, 'DefaultSelector', return_value=selector), patch.object(self.m.os, 'read', side_effect=chunks):
                result = self.m.query(['/usr/bin/nmcli', '--version'])
            self.assertEqual(result['state'], expected)
            self.assertIs(popen.call_args.kwargs['shell'], False)
            self.assertEqual(popen.call_args.kwargs['stdin'], self.m.subprocess.DEVNULL)
            self.assertNotIn('HOME', popen.call_args.kwargs['env'])

    def test_json_type_and_parse_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            path = root / 'settings.json'
            for text in ('[]', '{bad', 'null'):
                path.write_text(text)
                self.assertEqual(self.m.json_file(path, root)['state'], 'invalid')

    def test_real_file_collection_does_not_write(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            plugin = root / 'plugins' / 'WiFi Optimizer'
            plugin.mkdir(parents=True)
            (plugin / 'package.json').write_text('{"name":"wifi-optimizer","version":"0.11.6"}')
            settings = root / 'settings' / 'WiFi Optimizer'
            settings.mkdir(parents=True)
            (settings / 'settings.json').write_text('{"cake_enabled":true,"dns_servers":"SECRET"}')
            before = {str(path.relative_to(root)): path.read_bytes() for path in root.rglob('*') if path.is_file()}
            original = self.m.read_file
            def reader(path, boundary, limit=self.m.LIMIT):
                return original(path, boundary, limit) if str(path).startswith(str(root)) else {'state': 'absent'}
            with patch.object(self.m.sys, 'platform', 'linux'), patch.object(self.m, 'read_file', side_effect=reader), patch.object(self.m, 'query', return_value={'state': 'absent'}):
                data = self.m.collect(root)
            after = {str(path.relative_to(root)): path.read_bytes() for path in root.rglob('*') if path.is_file()}
            self.assertEqual(before, after)
            self.assertTrue(data['plugins'][0]['settings']['flags']['cake_enabled'])
            self.assertNotIn('SECRET', json.dumps(data))

    def test_settings_strict_types_and_privacy(self):
        result = self.m.settings_view({'power_save_disabled': 'false', 'cake_enabled': False, 'dns_servers': 'SECRET-IP', 'bssid_lock_value': 'SECRET-MAC', 'last_connection_uuid': 'SECRET-UUID', 'band_preference': 'SECRET-SSID'})
        self.assertEqual(result['cake_enabled'], False)
        self.assertNotIn('power_save_disabled', result)
        self.assertNotIn('SECRET', json.dumps(result))
        self.assertEqual(self.m.settings_view({}), {})
        self.assertEqual(self.m.settings_view({'dns_provider': 'custom'}), {'dns_provider': 'custom'})

    def test_unrecognized_manifest_values_cannot_leak_identifiers(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            base = root / 'plugins' / 'WiFi Optimizer'
            base.mkdir(parents=True)
            (base / 'plugin.json').write_text('{"name":"SECRET-SSID"}')
            (base / 'package.json').write_text('{"name":"wifi-optimizer","version":"SECRET-USER"}')
            original = self.m.read_file
            def reader(path, boundary, limit=self.m.LIMIT):
                return original(path, boundary, limit) if str(path).startswith(str(root)) else {'state': 'absent'}
            with patch.object(self.m.sys, 'platform', 'linux'), patch.object(self.m, 'read_file', side_effect=reader), patch.object(self.m, 'query', return_value={'state': 'absent'}):
                data = self.m.collect(root)
            self.assertNotIn('SECRET', json.dumps(data))
            self.assertEqual(data['plugins'][0]['plugin.json']['state'], 'invalid')

    def test_caps_report_omitted_observations_and_preserve_recorded_profile(self):
        recorded = 'ffffffff-0123-0123-0123-0123456789ab'
        active = [f'{i:08x}-0123-0123-0123-0123456789ab' for i in range(70)]
        def runner(args):
            if 'DEVICE,TYPE' in args:
                return {'state': 'ok', 'text': '\n'.join([f'eth{i}:ethernet' for i in range(70)] + [f'wlan{i}:wifi' for i in range(10)])}
            if '--active' in args:
                return {'state': 'ok', 'text': '\n'.join(x + ':802-11-wireless' for x in active)}
            return {'state': 'absent'}
        with patch.object(self.m.sys, 'platform', 'linux'), patch.object(self.m, 'read_file', return_value={'state': 'absent'}), patch.object(self.m, 'json_file', return_value={'state': 'ok', 'value': {'bssid_lock_connection_uuid': recorded}}), patch.object(self.m, 'query', side_effect=runner), patch.object(self.m, 'wifi_view', return_value={}):
            data = self.m.collect(pathlib.Path('/private'))
        self.assertEqual(len(data['wifi']), 8)
        self.assertEqual(data['wifi_omitted'], 2)
        self.assertEqual(data['profiles_omitted'], 63)
        self.assertTrue(data['profiles'][0]['recorded_in_settings'])

    def test_numeric_module_parameter_three_is_observed(self):
        def reader(path, root, limit=self.m.LIMIT):
            if str(path).endswith('iwlwifi/parameters/uapsd_disable'):
                return {'state': 'ok', 'data': b'3\n'}
            return {'state': 'absent'}
        with patch.object(self.m.sys, 'platform', 'linux'), patch.object(self.m, 'read_file', side_effect=reader), patch.object(self.m, 'query', return_value={'state': 'absent'}):
            data = self.m.collect(pathlib.Path('/private'))
        self.assertEqual(data['module_parameters']['iwlwifi/parameters/uapsd_disable'], {'state': 'ok', 'value': '3'})

    def test_profile_view_never_identifiers(self):
        values = ['yes', '100', 'a', 'aa:bb:cc:dd:ee:ff', 'auto', 'yes', '1.1.1.1, 8.8.8.8', 'disabled']
        result = self.m.profile_view('\n'.join(values))
        self.assertEqual(result['dns_count'], 2)
        self.assertTrue(result['bssid_present'])
        self.assertNotIn('aa:bb', json.dumps(result))
        self.assertNotIn('1.1.1.1', json.dumps(result))
        self.assertEqual(self.m.profile_view('bad')['state'], 'invalid')

    def test_backend_parser_respects_section(self):
        self.assertEqual(self.m.backend_view('[other]\nwifi.backend=iwd\n[device]\nwifi.backend=wpa_supplicant'), ['wpa_supplicant'])

    def test_disconnected_collection_and_no_raw_error(self):
        def reader(*args, **kwargs):
            return {'state': 'absent'}
        def runner(args):
            if args == ['/usr/bin/nmcli', '-t', '-f', 'DEVICE,TYPE', 'device', 'status']:
                return {'state': 'ok', 'text': 'wlan0:wifi\nwlan1:wifi\neth0:ethernet\n'}
            if '--active' in args:
                return {'state': 'ok', 'text': ''}
            return {'state': 'failed'}
        with patch.object(self.m.sys, 'platform', 'linux'), patch.object(self.m, 'read_file', side_effect=reader), patch.object(self.m, 'query', side_effect=runner):
            data = self.m.collect(pathlib.Path('/PRIVATE-USER'))
        self.assertEqual(len(data['wifi']), 2)
        self.assertEqual(data['profiles'], [])
        self.assertTrue(data['partial'])
        self.assertFalse(data['atomic'])
        self.assertNotIn('PRIVATE-USER', json.dumps(data))

    def test_active_profiles_and_settings_are_deduplicated_private(self):
        uuid = '01234567-0123-0123-0123-0123456789ab'
        def runner(args):
            if '--active' in args:
                return {'state': 'ok', 'text': uuid + ':802-11-wireless\n' + '11234567-0123-0123-0123-0123456789ab:ethernet\n'}
            if self.m.PROFILE_FIELDS in args:
                return {'state': 'ok', 'text': 'yes\n100\na\naa:bb:cc:dd:ee:ff\nauto\nyes\n1.1.1.1\ndisabled\n'}
            return {'state': 'failed'}
        with patch.object(self.m.sys, 'platform', 'linux'), patch.object(self.m, 'read_file', return_value={'state': 'absent'}), patch.object(self.m, 'json_file', return_value={'state': 'ok', 'value': {'last_connection_uuid': uuid}}), patch.object(self.m, 'query', side_effect=runner):
            data = self.m.collect(pathlib.Path('/private'))
        self.assertEqual(len(data['profiles']), 1)
        self.assertTrue(data['profiles'][0]['active'])
        self.assertTrue(data['profiles'][0]['recorded_in_settings'])
        for secret in (uuid, 'aa:bb', '1.1.1.1'):
            self.assertNotIn(secret, json.dumps(data))


if __name__ == '__main__':
    unittest.main()
