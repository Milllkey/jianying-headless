#!/usr/bin/env python3
"""Read-only, bounded runtime report: no account data, media paths or program uploads."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import plistlib
import shutil
import stat
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'engine'))
from runtime_profiles import PROFILES, validate_identity
from headless_runtime import BACKEND, IO_MANIFEST_SHA, PINS


def component_readiness(backend=BACKEND, manifest_sha=IO_MANIFEST_SHA, pins=None, find_tool=None):
    """Inspect independent prerequisites without importing or executing the codec.

    This is a diagnostic snapshot, not an authorization for a native operation.
    The runtime's existing doctor/validate_runtime checks remain authoritative.
    """
    pins = PINS if pins is None else pins
    find_tool = shutil.which if find_tool is None else find_tool
    components = []
    for name, expected in {'SOURCE_MANIFEST.json': manifest_sha, **pins}.items():
        entry = {'name': name, 'expected_sha256': expected}
        path = Path(backend) / name
        try:
            initial = path.lstat()
            if stat.S_ISLNK(initial.st_mode):
                entry['status'] = 'symlink-rejected'
            elif not stat.S_ISREG(initial.st_mode):
                entry['status'] = 'not-a-regular-file'
            else:
                # Do not follow a file replaced with a symlink after lstat.
                fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
                with os.fdopen(fd, 'rb') as stream:
                    opened = os.fstat(stream.fileno())
                    digest = hashlib.sha256()
                    for block in iter(lambda: stream.read(1024 * 1024), b''):
                        digest.update(block)
                    finished = os.fstat(stream.fileno())
                final = path.lstat()
                identity = lambda item: (item.st_dev, item.st_ino, item.st_mode,
                                         item.st_size, item.st_mtime_ns, item.st_ctime_ns)
                entry.update(actual_sha256=digest.hexdigest(), bytes=finished.st_size)
                if not all(identity(item) == identity(initial) for item in (opened, finished, final)):
                    entry['status'] = 'changed-during-inspection'
                else:
                    entry['status'] = ('matched' if entry['actual_sha256'] in (expected if isinstance(expected, tuple) else (expected,))
                                       else 'hash-mismatch')
        except FileNotFoundError:
            entry['status'] = 'missing'
        except OSError as error:
            entry.update(status='unreadable', reason=type(error).__name__)
        components.append(entry)
    media_tools = {name: bool(find_tool(name)) for name in ('ffmpeg', 'ffprobe')}
    return {'schema': 'jianying-headless-component-readiness/v1',
            'status': ('prerequisites-matched' if all(item['status'] == 'matched' for item in components)
                       and all(media_tools.values()) else 'blocked'),
            'components': components, 'media_tools_available': media_tools,
            'codec_executed': False, 'native_workflow_verified': False,
            'read_only': True, 'network_called': False,
            'next_step': 'Keep the existing pins. Resolve missing or mismatched components, then run doctor '
                         'and validate_runtime before a synthetic native workflow.'}


def report(app):
    result = {'schema': 'jianying-headless-runtime-report/v1', 'system': platform.system(),
              'macos': platform.mac_ver()[0], 'architecture': platform.machine(),
              'python': platform.python_version(), 'read_only': True, 'network_called': False}
    result['native_prerequisites'] = component_readiness()
    try:
        info = plistlib.loads((app / 'Contents/Info.plist').read_bytes())
        if not isinstance(info, dict) or any(
                info.get(key) is not None and not isinstance(info[key], str)
                for key in ('CFBundleShortVersionString', 'CFBundleVersion', 'CFBundleIdentifier')):
            raise ValueError('Malformed application identity')
        result.update(app_version=info.get('CFBundleShortVersionString'),
                      app_build=info.get('CFBundleVersion'), bundle_id=info.get('CFBundleIdentifier'))
        library = app / 'Contents/Frameworks/libvideoeditor.dylib'
        sha = hashlib.sha256()
        with library.open('rb') as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                sha.update(block)
        result['library_sha256'] = sha.hexdigest()
        result['expected_library_sha256'] = PROFILES.get(result['app_version'])
    except (OSError, ValueError) as error:
        result.update(status='unavailable', reason=type(error).__name__,
                      next_step='Check the official Jianying installation; no personal paths are included.')
        return result
    try:
        validate_identity(info, result['library_sha256'])
        result['identity_matched'] = True
    except ValueError:
        result['identity_matched'] = False
    try:
        env = {'PATH': '/usr/bin:/bin:/usr/sbin:/sbin', 'LC_ALL': 'C'}
        verified = subprocess.run(['/usr/bin/codesign', '--verify', '--deep', '--strict', str(app)],
                                  env=env, capture_output=True, timeout=180)
        details = subprocess.run(['/usr/bin/codesign', '-dv', '--verbose=4', str(app)],
                                 env=env, capture_output=True, text=True, timeout=30)
        team = [line.split('=', 1)[1] for line in details.stderr.splitlines()
                if line.startswith('TeamIdentifier=')]
        result['team_identifier'] = team[0] if len(team) == 1 else None
        result['official_signature_verified'] = (verified.returncode == details.returncode == 0
                                                 and team == ['X2JNK7LY8J'])
    except (OSError, subprocess.SubprocessError):
        result['official_signature_verified'] = False
    result['status'] = ('identity-verified' if result['identity_matched']
                        and result['official_signature_verified'] else 'review-required')
    result['next_step'] = ('Run doctor and the documented first-draft workflow.'
                           if result['status'] == 'identity-verified' else
                           'Share this report and the official download source, not application binaries. '
                           'Native writes remain blocked until this exact build is reviewed.')
    result['codec_or_native_workflow_verified'] = False
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app', type=Path, default=Path('/Applications/VideoFusion-macOS.app'))
    parser.add_argument('--components-only', action='store_true',
                        help='Inspect pinned files and media tool availability; do not open the app or run a native program.')
    args = parser.parse_args()
    value = component_readiness() if args.components_only else report(args.app)
    print(json.dumps(value, ensure_ascii=False, indent=2))
    raise SystemExit(0 if value['status'] in ('identity-verified', 'prerequisites-matched') else 1)
