#!/usr/bin/env python3
"""Partial, non-atomic observations; stdout only. Never a backup or recovery plan.

Run on the Deck with Python 3 and an explicit Decky home. No plugin imports,
scans, writes, network requests, or privilege escalation. Inspect before sharing.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import stat
import subprocess
import sys
import time

LIMIT = 65536
IFACE = re.compile(r'[A-Za-z0-9_-]{1,15}\Z')
UUID = re.compile(r'[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}\Z')
PROFILE_FIELDS = 'connection.autoconnect,connection.autoconnect-priority,802-11-wireless.band,802-11-wireless.bssid,ipv4.method,ipv4.ignore-auto-dns,ipv4.dns,ipv6.method'
UNITS = ('NetworkManager.service', 'iwd.service', 'wpa_supplicant.service', 'plugin_loader.service')
PROPERTIES = 'LoadState,ActiveState,SubState,UnitFileState,KillMode'
FLAGS = ('supports_6ghz', 'power_save_disabled', 'auto_fix_on_wake', 'bssid_lock_enabled', 'band_preference_enabled', 'dns_enabled', 'ipv6_disabled', 'buffer_tuning_enabled', 'cake_enabled', 'priority_set')
ENUMS = {'band_preference': ('', 'a', 'bg'), 'dns_provider': ('cloudflare', 'google', 'quad9', 'custom')}
SYSCTLS = ('net.core.rmem_max', 'net.core.wmem_max', 'net.core.rmem_default', 'net.core.wmem_default', 'net.core.netdev_max_backlog', 'net.core.netdev_budget', 'net.core.netdev_budget_usecs', 'net.ipv4.tcp_slow_start_after_idle')
CONFIGS = ('/etc/NetworkManager/dispatcher.d/99-wifi-optimizer', '/etc/NetworkManager/conf.d/99-wifi-optimizer.conf', '/etc/NetworkManager/conf.d/99-wifi-optimizer-backend.conf', '/etc/NetworkManager/conf.d/99-valve-wifi-backend.conf', '/usr/lib/NetworkManager/conf.d/10-steamos-defaults.conf', '/etc/NetworkManager/conf.d/iwd.conf', '/etc/modprobe.d/99-wifi-optimizer.conf')


def read_file(path, root, limit=LIMIT):
    """Resolve within root, reject special files, and bound the actual read."""
    fd = None
    try:
        path = Path(path).resolve()
        path.relative_to(Path(root).resolve())
        if not stat.S_ISREG(path.stat().st_mode):
            return {'state': 'invalid'}
        fd = os.open(str(path), os.O_RDONLY | getattr(os, 'O_NONBLOCK', 0) | getattr(os, 'O_NOFOLLOW', 0))
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            return {'state': 'invalid'}
        # sysfs reports page-sized st_size for tiny values. Bound bytes read,
        # and handle short reads before calling a fingerprint complete.
        data = bytearray()
        while len(data) <= limit:
            chunk = os.read(fd, min(65536, limit + 1 - len(data)))
            if not chunk:
                return {'state': 'ok', 'data': bytes(data)}
            data.extend(chunk)
        return {'state': 'oversize'}
    except FileNotFoundError:
        return {'state': 'absent'}
    except PermissionError:
        return {'state': 'permission_denied'}
    except (ValueError, RuntimeError):
        return {'state': 'invalid'}
    except OSError:
        return {'state': 'failed'}
    finally:
        if fd is not None:
            os.close(fd)


def allowed(args):
    if args in (['/usr/bin/nmcli', '--version'], ['/usr/bin/systemctl', '--version'], ['/usr/bin/nmcli', '-t', '-f', 'DEVICE,TYPE', 'device', 'status'], ['/usr/bin/nmcli', '-t', '-f', 'UUID,TYPE', 'connection', 'show', '--active']):
        return True
    if len(args) == 7 and args[:6] == ['/usr/bin/nmcli', '-g', PROFILE_FIELDS, 'connection', 'show', 'uuid']:
        return bool(UUID.fullmatch(args[6]))
    if len(args) == 5 and args[:2] == ['/usr/bin/iw', 'dev'] and args[3:] == ['get', 'power_save']:
        return bool(IFACE.fullmatch(args[2]))
    if len(args) == 6 and args[:5] == ['/usr/bin/tc', '-j', 'qdisc', 'show', 'dev']:
        return bool(IFACE.fullmatch(args[5]))
    return len(args) == 6 and args[:5] == ['/usr/bin/systemctl', 'show', '--no-pager', '--property=' + PROPERTIES, '--'] and args[5] in UNITS


def query(args):
    """Only allowlisted queries; bounded stdout, discarded stderr, sanitized errors."""
    if not allowed(args):
        return {'state': 'invalid'}
    process = None
    try:
        process = subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, shell=False, env={'PATH': '/usr/bin:/bin', 'LC_ALL': 'C', 'LANG': 'C', 'SYSTEMD_PAGER': 'cat', 'SYSTEMD_COLORS': '0'})
        deadline = time.monotonic() + 4
        data = bytearray()
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return {'state': 'timeout'}
                if not selector.select(remaining):
                    return {'state': 'timeout'}
                chunk = os.read(process.stdout.fileno(), min(4096, LIMIT + 1 - len(data)))
                if not chunk:
                    break
                data.extend(chunk)
                if len(data) > LIMIT:
                    return {'state': 'oversize'}
        code = process.wait(timeout=max(0.01, deadline - time.monotonic()))
        return {'state': 'ok', 'text': data.decode('utf-8')} if code == 0 else {'state': 'failed', 'exit_code': code}
    except FileNotFoundError:
        return {'state': 'absent'}
    except PermissionError:
        return {'state': 'permission_denied'}
    except subprocess.TimeoutExpired:
        return {'state': 'timeout'}
    except (OSError, UnicodeError, ValueError):
        return {'state': 'failed'}
    finally:
        if process is not None:
            if process.poll() is None:
                process.kill()
            process.wait()
            process.stdout.close()


def text_file(path, root, limit=LIMIT):
    result = read_file(path, root, limit)
    if result['state'] != 'ok':
        return result
    try:
        return {'state': 'ok', 'text': result['data'].decode('utf-8')}
    except UnicodeError:
        return {'state': 'invalid'}


def json_file(path, root):
    result = text_file(path, root)
    if result['state'] != 'ok':
        return result
    try:
        value = json.loads(result['text'])
        return {'state': 'ok', 'value': value} if isinstance(value, dict) else {'state': 'invalid'}
    except (ValueError, RecursionError):
        return {'state': 'invalid'}


def settings_view(value):
    result = {key: value[key] for key in FLAGS if type(value.get(key)) is bool}
    result.update({key: value[key] for key, choices in ENUMS.items() if isinstance(value.get(key), str) and value[key] in choices})
    # No Beta channel exists; the key is gone from DEFAULT_SETTINGS. A stored
    # pre-decision "beta" value is still recorded raw (never silently dropped
    # while the field installation exists) with a migration note.
    channel = value.get('update_channel')
    if isinstance(channel, str):
        result['update_channel'] = channel
        if channel == 'beta':
            result['update_channel_note'] = 'beta channel dropped; migrated to Stable'
    return result


def profile_view(text):
    values = text.rstrip('\n').split('\n')
    if len(values) != 8:
        return {'state': 'invalid'}
    auto, priority, band, bssid, method, ignore, dns, ipv6 = values
    if auto not in ('yes', 'no') or ignore not in ('yes', 'no') or band not in ('', 'a', 'bg') or not re.fullmatch(r'-?\d{1,10}', priority) or method not in ('auto', 'manual', 'link-local', 'shared', 'disabled') or ipv6 not in ('auto', 'manual', 'link-local', 'shared', 'disabled', 'ignore', 'dhcp'):
        return {'state': 'invalid'}
    return {'state': 'ok', 'autoconnect': auto == 'yes', 'priority': int(priority), 'band': band, 'bssid_present': bool(bssid), 'ipv4_method': method, 'ignore_auto_dns': ignore == 'yes', 'dns_count': len([x for x in re.split(r'[,;\s]+', dns) if x]), 'ipv6_method': ipv6}


def backend_view(text):
    section = ''
    values = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith('[') and line.endswith(']'):
            section = line[1:-1]
        elif section == 'device' and '=' in line:
            key, value = (x.strip() for x in line.split('=', 1))
            if key == 'wifi.backend' and value in ('iwd', 'wpa_supplicant'):
                values.append(value)
    return values


def fingerprint(path, root, limit=LIMIT):
    result = read_file(path, root, limit)
    if result['state'] != 'ok':
        return result
    return {'state': 'ok', 'sha256': hashlib.sha256(result['data']).hexdigest(), 'bytes': len(result['data'])}


def scalar(path, root, pattern=r'[0-9]+'):
    result = text_file(path, root, 256)
    if result['state'] != 'ok':
        return result
    value = result['text'].strip()
    return {'state': 'ok', 'value': value} if re.fullmatch(pattern, value) else {'state': 'invalid'}


def version(args):
    result = query(args)
    if result['state'] != 'ok':
        return result
    match = re.search(r'\b\d+(?:\.\d+){0,3}\b', result['text'])
    return {'state': 'ok', 'version': match[0]} if match else {'state': 'invalid'}


def wifi_view(iface):
    root = Path('/sys/class/net') / iface
    result = {'queue_length': scalar(root / 'tx_queue_len', '/sys/devices'), 'power_save': {'state': 'unknown'}}
    power = query(['/usr/bin/iw', 'dev', iface, 'get', 'power_save'])
    if power['state'] == 'ok':
        match = re.fullmatch(r'\s*Power save:\s*(on|off)\s*', power['text'])
        result['power_save'] = {'state': 'ok', 'value': match[1]} if match else {'state': 'invalid'}
    else:
        result['power_save'] = power
    qdisc = query(['/usr/bin/tc', '-j', 'qdisc', 'show', 'dev', iface])
    if qdisc['state'] == 'ok':
        try:
            items = json.loads(qdisc['text'])
            if not isinstance(items, list) or len(items) > 32:
                raise ValueError()
            kinds = ('cake', 'fq_codel', 'fq', 'pfifo_fast', 'noqueue', 'mq', 'pfifo', 'bfifo', 'ingress', 'clsact')
            result['qdisc'] = {'state': 'ok', 'kinds': [x['kind'] if x.get('kind') in kinds else 'other' for x in items if isinstance(x, dict)]}
        except (ValueError, TypeError, RecursionError):
            result['qdisc'] = {'state': 'invalid'}
    else:
        result['qdisc'] = qdisc
    device = root / 'device'
    result['power'] = {name: scalar(device / name, '/sys/devices', r'(on|auto|0|1)') for name in ('power/control', 'link/l0s_aspm', 'link/l1_aspm', 'link/l1_1_aspm', 'link/l1_2_aspm', 'link/l1_1_pcipm', 'link/l1_2_pcipm')}
    try:
        driver = (device / 'driver/module').resolve()
        driver.relative_to(Path('/sys/module'))
        result['driver'] = {'state': 'ok', 'module': driver.name} if re.fullmatch(r'[a-zA-Z0-9_]{1,64}', driver.name) and driver.is_dir() else {'state': 'absent'}
    except (ValueError, OSError, RuntimeError):
        result['driver'] = {'state': 'invalid'}
    return result


def collect(decky_home):
    if sys.platform != 'linux':
        return {'state': 'unsupported_platform', 'partial': True, 'atomic': False}
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    result = {'schema': 1, 'partial': True, 'atomic': False, 'started_utc': started, 'limitations': ['May already be modified; not a pristine baseline.', 'No backup, exact restoration, commit provenance or runtime behavior guarantee.', 'Identifiers omitted; keep separate private recovery records.'], 'decky': {'state': 'unverified'}, 'effective_backend': {'state': 'unverified'}}
    os_release = text_file('/etc/os-release', '/usr/lib', 8192)
    # Some systems keep a regular /etc/os-release instead of the usual symlink.
    if os_release['state'] == 'invalid':
        os_release = text_file('/etc/os-release', '/etc', 8192)
    if os_release['state'] == 'ok':
        values = {}
        for line in os_release['text'].splitlines():
            key, separator, value = line.partition('=')
            if separator and key in ('ID', 'VERSION_ID', 'BUILD_ID', 'VARIANT_ID'):
                value = value.strip('"\'')
                if re.fullmatch(r'[A-Za-z0-9._ -]{1,100}', value):
                    values[key] = value
        result['os'] = {'state': 'ok', 'fields': values}
    else:
        result['os'] = os_release
    result['kernel'] = scalar('/proc/sys/kernel/osrelease', '/proc/sys/kernel', r'[A-Za-z0-9._+~-]{1,128}')
    result['model'] = scalar('/sys/devices/virtual/dmi/id/product_name', '/sys/devices', r'(Jupiter|Galileo)')
    result['nm_version'] = version(['/usr/bin/nmcli', '--version'])
    result['systemd_version'] = version(['/usr/bin/systemctl', '--version'])
    result['plugins'] = []
    recorded = []
    for name in ('WiFi Optimizer', 'WiFi Optimizer TMS', 'wifi-optimizer-tms'):
        base = decky_home / 'plugins' / name
        entry = {'candidate': name, 'files': {}}
        for filename in ('plugin.json', 'package.json', 'main.py', 'dist/index.js', 'dist/index.js.map', 'defaults/dispatcher.sh.tmpl'):
            entry['files'][filename] = fingerprint(base / filename, decky_home, 8 * 1024 * 1024)
        for filename in ('plugin.json', 'package.json'):
            parsed = json_file(base / filename, decky_home)
            entry[filename] = {'state': parsed['state']}
            if parsed['state'] == 'ok':
                value = parsed['value']
                names = ('WiFi Optimizer', 'WiFi Optimizer TMS') if filename == 'plugin.json' else ('wifi-optimizer', 'wifi-optimizer-tms')
                valid = value.get('name') in names
                if filename == 'package.json':
                    valid = valid and isinstance(value.get('version'), str) and bool(re.fullmatch(r'\d{1,5}\.\d{1,5}\.\d{1,5}(?:-[0-9A-Za-z.-]{1,40})?', value['version']))
                entry[filename] = {'state': 'ok', 'name': value['name']} if valid else {'state': 'invalid'}
                if valid and filename == 'package.json':
                    entry[filename]['version'] = value['version']
        settings_root = decky_home / 'settings' / name
        settings = json_file(settings_root / 'settings.json', decky_home)
        entry['settings'] = {'state': settings['state']}
        if settings['state'] == 'ok':
            entry['settings']['flags'] = settings_view(settings['value'])
            for key in ('last_connection_uuid', 'bssid_lock_connection_uuid'):
                value = settings['value'].get(key)
                if isinstance(value, str) and UUID.fullmatch(value):
                    recorded.append(value)
        result['plugins'].append(entry)
    result['configs'] = {}
    for path in CONFIGS:
        item = fingerprint(path, Path(path).parent)
        if '/conf.d/' in path:
            content = text_file(path, Path(path).parent)
            if content['state'] == 'ok':
                item['backend_values'] = backend_view(content['text'])
        result['configs'][path] = item
    result['services'] = {}
    for unit in UNITS:
        item = query(['/usr/bin/systemctl', 'show', '--no-pager', '--property=' + PROPERTIES, '--', unit])
        if item['state'] == 'ok':
            fields = {}
            for line in item['text'].splitlines():
                key, separator, value = line.partition('=')
                if separator and key in PROPERTIES.split(',') and value in ('loaded', 'not-found', 'masked', 'error', 'active', 'inactive', 'failed', 'activating', 'deactivating', 'running', 'dead', 'exited', 'enabled', 'disabled', 'static', 'indirect', 'enabled-runtime', 'masked-runtime', 'control-group', 'mixed', 'process', 'none'):
                    fields[key] = value
            item = {'state': 'ok', 'fields': fields}
        result['services'][unit] = item
    result['sysctl'] = {key: scalar('/proc/sys/' + key.replace('.', '/'), '/proc/sys') for key in SYSCTLS}
    parameters = {name: r'[YNyn01]' for name in ('rtw88_core/parameters/disable_lps_deep', 'rtw88_pci/parameters/disable_aspm', 'mt7921e/parameters/disable_aspm', 'iwlwifi/parameters/power_save')}
    parameters.update({name: r'[0-9]{1,10}' for name in ('iwlwifi/parameters/uapsd_disable', 'iwlmvm/parameters/power_scheme')})
    result['module_parameters'] = {name: scalar('/sys/module/' + name, '/sys/module', pattern) for name, pattern in parameters.items()}
    devices = query(['/usr/bin/nmcli', '-t', '-f', 'DEVICE,TYPE', 'device', 'status'])
    result['wifi_state'] = devices['state']
    result['wifi'] = []
    result['wifi_omitted'] = None
    if devices['state'] == 'ok':
        interfaces = []
        for line in devices['text'].splitlines():
            iface, separator, kind = line.partition(':')
            if separator and kind == 'wifi' and IFACE.fullmatch(iface) and iface not in interfaces:
                interfaces.append(iface)
        result['wifi_omitted'] = max(0, len(interfaces) - 8)
        if result['wifi_omitted']:
            result['wifi_state'] = 'truncated'
        for iface in interfaces[:8]:
            result['wifi'].append({'alias': 'wifi-' + str(len(result['wifi']) + 1), **wifi_view(iface)})
    active = query(['/usr/bin/nmcli', '-t', '-f', 'UUID,TYPE', 'connection', 'show', '--active'])
    result['active_profiles_state'] = active['state']
    active_ids = []
    if active['state'] == 'ok':
        for line in active['text'].splitlines():
            uuid, separator, kind = line.partition(':')
            if separator and kind in ('802-11-wireless', 'wifi') and UUID.fullmatch(uuid):
                active_ids.append(uuid)
    result['profiles'] = []
    profile_ids = list(dict.fromkeys(recorded + active_ids))
    result['profiles_omitted'] = max(0, len(profile_ids) - 8)
    for uuid in profile_ids[:8]:
        profile = query(['/usr/bin/nmcli', '-g', PROFILE_FIELDS, 'connection', 'show', 'uuid', uuid])
        view = profile_view(profile['text']) if profile['state'] == 'ok' else profile
        result['profiles'].append({'alias': 'profile-' + str(len(result['profiles']) + 1), 'active': uuid in active_ids, 'recorded_in_settings': uuid in recorded, **view})
    result['ended_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--decky-home', required=True, help='Explicit existing Decky home (normally the homebrew directory); never inferred from sudo HOME.')
    args = parser.parse_args(argv)
    if sys.platform != 'linux':
        print(json.dumps({'state': 'unsupported_platform', 'partial': True, 'atomic': False}))
        return 2
    home = Path(args.decky_home)
    try:
        valid_home = home.is_absolute() and home.is_dir() and (home / 'plugins').is_dir()
    except (OSError, ValueError):
        valid_home = False
    if not valid_home:
        print(json.dumps({'state': 'invalid_decky_home', 'partial': True, 'atomic': False}))
        return 2
    print(json.dumps(collect(home), indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
