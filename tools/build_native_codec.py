#!/usr/bin/env python3
"""Rebuild the source-pinned local codec; never download or patch Jianying."""
from __future__ import annotations

import hashlib
import argparse
import json
import os
from pathlib import Path
import platform
import plistlib
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'engine'))
from runtime_profiles import PROFILES, validate_identity
from build_toolchain import select_toolchain, compile_command
from codec_profiles import choose_build_profile, load_profiles, validate_codec_runtime
BRIDGE = ROOT / 'bridge'
APP = Path('/Applications/VideoFusion-macOS.app')
EXPECTED_CODEC_SHA = 'b6533eb5eb1eea58dfa74fb1d16d3bb580970fe881f587605d358af1745f971d'


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(path):
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), 'Expected a regular, non-symlink file: ' + str(path))
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()


def run(command, *, env=None, timeout=180):
    result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=timeout)
    require(result.returncode == 0, 'Command failed: ' + command[0] + '\n' + result.stderr[-4000:])
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--developer-dir', help='Use this exact Xcode/CLT developer directory')
    parser.add_argument('--profile', help='Select an exact reviewed codec build profile; default matches an installed official toolchain')
    parser.add_argument('--check-toolchain', action='store_true', help='Read-only exact toolchain check')
    parser.add_argument('--rebuild-check', action='store_true',
                        help='Rebuild into retained work/ even when the installed codec is already valid')
    args = parser.parse_args(argv)
    require(platform.system() == 'Darwin' and platform.machine() == 'arm64',
            'This native bridge profile requires Apple Silicon macOS')
    require(sys.version_info >= (3, 9), 'Python 3.9 or later is required')
    manifest = json.loads((BRIDGE / 'SOURCE_MANIFEST.json').read_text(encoding='utf-8'))
    require(manifest['schema'] == 'jianying-headless-bridge-source/v1', 'Unexpected bridge source manifest')
    for name, expected in manifest['source_files'].items():
        require(Path(name).name == name, 'Bridge source names must be simple file names')
        require(digest(BRIDGE / name) == expected, 'Bridge source changed: ' + name)
    require(manifest['expected_codec_sha256'] == EXPECTED_CODEC_SHA, 'Codec fingerprint changed')
    profiles = load_profiles()
    require(args.profile is None or args.profile in profiles, 'Unknown codec build profile')
    for profile in profiles.values():
        require(all(manifest['source_files'].get(name) == expected for name, expected in profile['source_files'].items()),
                'Codec build profile source does not match the pinned source manifest')

    if args.check_toolchain:
        name, _, _, identity = choose_build_profile(select_toolchain, args.profile, args.developer_dir)
        print(json.dumps(dict(identity, status='toolchain-matched', codec_build_profile=name, compiled=False,
                              runtime_compatibility_verified=False), ensure_ascii=False))
        return

    info = plistlib.loads((APP / 'Contents/Info.plist').read_bytes())
    library = APP / 'Contents/Frameworks/libvideoeditor.dylib'
    version = validate_identity(info, digest(library))
    env = {'PATH': '/usr/bin:/bin:/usr/sbin:/sbin', 'LC_ALL': 'C'}
    run(['/usr/bin/codesign', '--verify', '--deep', '--strict', str(APP)], env=env)
    signature = run(['/usr/bin/codesign', '-dv', '--verbose=4', str(APP)], env=env)
    require('TeamIdentifier=X2JNK7LY8J' in signature.stderr.splitlines(), 'Unexpected Jianying signing identity')

    destination = BRIDGE / 'jy14_codec_hardened_11_4'
    already_installed = destination.exists() or destination.is_symlink()
    if already_installed:
        installed_sha = digest(destination)
        installed_profile = validate_codec_runtime(installed_sha, version, digest(library))
        require(os.access(destination, os.X_OK), 'Installed reviewed codec is not executable')
        require(args.profile is None or args.profile == installed_profile, 'A different reviewed codec is already installed; no file was overwritten')
        if not args.rebuild_check:
            print(json.dumps({'status': 'already-valid', 'codec_sha256': installed_sha, 'codec_build_profile': installed_profile,
                              'app_version': version, 'network_called': False}))
            return

    profile_name, profile, env, toolchain = choose_build_profile(select_toolchain,
        args.profile or (installed_profile if already_installed else None), args.developer_dir, version, digest(library))
    expected_codec = profile['codec_sha256']

    work = ROOT / 'work'
    work.mkdir(mode=0o700, exist_ok=True)
    job = Path(tempfile.mkdtemp(prefix='codec-build-', dir=work))
    compiler_temp = job / 'compiler-tmp'
    compiler_temp.mkdir(mode=0o700)
    env.update(TMPDIR=str(compiler_temp) + '/', CLANG_MODULE_CACHE_PATH=str(compiler_temp / 'modules'))
    built = job / destination.name
    frameworks = APP / 'Contents/Frameworks'
    command = compile_command(BRIDGE / 'jy14_codec.cpp', frameworks, built, toolchain)
    compiler = run(['/usr/bin/xcrun', 'clang++', '--version'], env=env).stdout
    result = run(command, env=env)
    actual = digest(built)
    report = {'schema': 'jianying-headless-codec-build/v1', 'status': 'built', 'app_version': version,
              'compiler': compiler, 'toolchain': toolchain, 'command': command, 'codec_sha256': actual,
              'expected_codec_sha256': expected_codec, 'codec_build_profile': profile_name, 'stderr': result.stderr,
              'network_called': False, 'official_library_copied': False, 'app_modified': False}
    with (job / 'build-report.json').open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    require(actual == expected_codec,
            'Compiler output differs from the reviewed codec. No runtime pin was changed; inspect ' + str(job))
    require(digest(library) == PROFILES[version], 'The native library changed while compiling')
    for name, expected in manifest['source_files'].items():
        require(digest(BRIDGE / name) == expected, 'Bridge source changed while compiling: ' + name)
    run(['/usr/bin/codesign', '--verify', '--strict', str(built)], env=env)
    if args.rebuild_check:
        print(json.dumps({'status': 'reproduced-and-verified', 'codec_sha256': actual,
                          'codec_build_profile': profile_name,
                          'audit_directory': str(job), 'installed': False, 'network_called': False}))
        return
    descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o700)
    with os.fdopen(descriptor, 'wb') as stream:
        stream.write(built.read_bytes())
        stream.flush()
        os.fsync(stream.fileno())
    require(digest(destination) == expected_codec, 'Installed local codec fingerprint differs')
    print(json.dumps({'status': 'built-and-verified', 'codec_sha256': actual, 'app_version': version,
                      'codec_build_profile': profile_name,
                      'audit_directory': str(job), 'network_called': False, 'app_modified': False}, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        raise SystemExit(str(error))
