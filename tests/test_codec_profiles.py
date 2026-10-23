"""Reviewed build selection fails closed; no test executes a native library."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import plistlib
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
for part in ('engine', 'bridge', 'tools'):
    sys.path.insert(0, str(ROOT / part))
import codec_profiles as profiles
import build_toolchain as toolchain
import runtime_io
import runtime_report
from runtime_profiles import validate_export_profiles

LEGACY = 'legacy-clang-2100.1.1.101'
CURRENT = 'clt-2100.3.34.2-sdk-25F70'
SHA = lambda value: hashlib.sha256(value).hexdigest()


class CodecProfiles(unittest.TestCase):
    def test_registry_fingerprint_is_exact_and_sources_are_unchanged(self):
        values = profiles.load_profiles()
        self.assertEqual(set(values), {LEGACY, CURRENT})
        for value in values.values():
            for name, expected in value['source_files'].items():
                self.assertEqual(SHA((ROOT / 'bridge' / name).read_bytes()), expected)
        self.assertEqual(values[LEGACY]['codec_sha256'], runtime_io.REQUIRED_CODEC_SHA256)

    def test_changed_oversized_and_symlinked_manifests_are_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / 'profiles.json'
            raw = profiles.MANIFEST.read_bytes()
            file.write_bytes(raw)
            self.assertEqual(profiles.load_profiles(file), profiles.load_profiles())
            file.write_bytes(raw + b'\n')
            with self.assertRaisesRegex(ValueError, 'fingerprint'):
                profiles.load_profiles(file)
            file.write_bytes(b' ' * 65537)
            with self.assertRaisesRegex(ValueError, 'bounded'):
                profiles.load_profiles(file)
            file.unlink()
            file.symlink_to(profiles.MANIFEST)
            with self.assertRaisesRegex(ValueError, 'regular'):
                profiles.load_profiles(file)

    def test_wrong_schema_is_refused_even_with_matching_fixture_hash(self):
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / 'profiles.json'
            raw = json.dumps({'schema': 'wrong', 'codec_filename': profiles.CODEC_FILENAME}).encode()
            file.write_bytes(raw)
            with self.assertRaisesRegex(ValueError, 'Unexpected'):
                profiles.load_profiles(file, SHA(raw))

    def test_unknown_and_ambiguous_codec_hashes_are_refused(self):
        with self.assertRaisesRegex(ValueError, 'not a reviewed'):
            profiles.profile_for_hash('0' * 64)
        fixture = {'a': {'codec_sha256': 'same'}, 'b': {'codec_sha256': 'same'}}
        with self.assertRaisesRegex(ValueError, 'not a reviewed'):
            profiles.profile_for_hash('same', fixture)

    def test_new_build_requires_exact_116_library_and_never_enables_export(self):
        values = profiles.load_profiles()
        current = values[CURRENT]
        library = current['runtime_libraries']['11.6.0']
        self.assertEqual(profiles.validate_codec_runtime(current['codec_sha256'], '11.6.0', library), CURRENT)
        for version, fingerprint in [('11.6.0', '0' * 64), ('11.6.1', library),
                                     ('11.5.0', values[LEGACY]['runtime_libraries']['11.5.0'])]:
            with self.subTest(version=version), self.assertRaisesRegex(ValueError, 'no reviewed ABI'):
                profiles.validate_codec_runtime(current['codec_sha256'], version, fingerprint)
        for version, fingerprint in values[LEGACY]['runtime_libraries'].items():
            self.assertEqual(profiles.validate_codec_runtime(values[LEGACY]['codec_sha256'], version, fingerprint), LEGACY)
        with self.assertRaisesRegex(ValueError, 'No reviewed native export ABI'):
            validate_export_profiles('jy14-headless-macos-11.6.0', 'jy14-headless-macos-11.6.0')

    def test_default_selection_uses_reviewed_match_after_legacy_mismatch(self):
        with patch.object(toolchain, 'select_toolchain', side_effect=[ValueError('older toolchain missing'), ({}, {'matched': True})]) as select:
            name, _, _, identity = profiles.choose_build_profile(select)
        self.assertEqual(name, CURRENT)
        self.assertEqual(identity, {'matched': True})
        self.assertEqual(select.call_count, 2)

    def test_explicit_profile_never_falls_back_or_accepts_unknown_name(self):
        with patch.object(toolchain, 'select_toolchain', side_effect=ValueError('mismatch')) as select:
            with self.assertRaisesRegex(ValueError, 'No exact reviewed'):
                profiles.choose_build_profile(select, explicit=LEGACY)
            self.assertEqual(select.call_count, 1)
            with self.assertRaisesRegex(ValueError, 'Unknown codec build profile'):
                profiles.choose_build_profile(select, explicit='unreviewed')
            self.assertEqual(select.call_count, 1)

    def test_build_selection_cannot_pair_new_profile_with_old_library(self):
        legacy = profiles.load_profiles()[LEGACY]
        with patch.object(toolchain, 'select_toolchain') as select:
            with self.assertRaisesRegex(ValueError, 'no reviewed ABI'):
                profiles.choose_build_profile(select, explicit=CURRENT, version='11.5.0',
                                              library_sha=legacy['runtime_libraries']['11.5.0'])
            select.assert_not_called()

    def test_new_toolchain_executable_and_sdk_bytes_are_checked(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            clang, ld = directory / 'clang', directory / 'ld'
            clang.write_bytes(b'owned clang fixture'); ld.write_bytes(b'owned linker fixture')
            settings = directory / 'SDKSettings.json'; settings.write_bytes(b'owned SDK fixture')
            value = deepcopy(profiles.load_profiles()[CURRENT]['reproduction_environment'])
            value.update(compiler_sha256=SHA(clang.read_bytes()), linker_sha256=SHA(ld.read_bytes()),
                         sdk_settings_sha256=SHA(settings.read_bytes()))
            answers = [value['compiler'].replace('Apple clang ', 'Apple clang version '), str(directory),
                       '26.5', json.dumps({'version': '27037.1'}), str(clang), str(ld), '25F70']
            with patch.object(toolchain, 'run', side_effect=answers):
                self.assertEqual(toolchain.inspect(directory, value)[1]['sdk_build'], '25F70')
            clang.write_bytes(b'changed compiler')
            with patch.object(toolchain, 'run', side_effect=answers), self.assertRaisesRegex(ValueError, 'executable'):
                toolchain.inspect(directory, value)
            value['compiler_sha256'] = SHA(clang.read_bytes())
            settings.write_bytes(b'changed SDK')
            with patch.object(toolchain, 'run', side_effect=answers), self.assertRaisesRegex(ValueError, 'SDK build/settings'):
                toolchain.inspect(directory, value)


class DirectCodecBoundary(unittest.TestCase):
    def test_changed_registry_is_refused_before_codec_read_or_execution(self):
        with patch.object(runtime_io, '_read_regular_bytes', return_value=(b'changed', None, None)), \
                patch.object(runtime_io, '_hash_file') as hash_file, \
                patch.object(runtime_io.subprocess, 'Popen') as process:
            with self.assertRaisesRegex(runtime_io.ApplyError, 'manifest changed'):
                runtime_io._reviewed_codec_pin()
            hash_file.assert_not_called(); process.assert_not_called()

    def test_unknown_codec_is_refused_before_app_read_or_execution(self):
        raw = profiles.MANIFEST.read_bytes()
        with patch.object(runtime_io, '_read_regular_bytes', return_value=(raw, None, None)) as read, \
                patch.object(runtime_io, '_hash_file', return_value='0' * 64), \
                patch.object(runtime_io.subprocess, 'Popen') as process:
            with self.assertRaisesRegex(runtime_io.ApplyError, 'reviewed build'):
                runtime_io._reviewed_codec_pin()
            self.assertEqual(read.call_count, 1); process.assert_not_called()

    def test_new_codec_wrong_app_version_stops_before_library_open(self):
        raw = profiles.MANIFEST.read_bytes()
        sha = profiles.load_profiles()[CURRENT]['codec_sha256']
        info = plistlib.dumps({'CFBundleShortVersionString': '11.5.0', 'CFBundleVersion': '11.5.0',
                              'CFBundleIdentifier': 'com.lemon.lvpro'})
        with patch.object(runtime_io, '_read_regular_bytes', side_effect=[(raw, None, None), (info, None, None)]), \
                patch.object(runtime_io, '_hash_file', return_value=sha), \
                patch.object(runtime_io.os, 'access', return_value=True), \
                patch.object(runtime_io, '_open_regular_readonly') as opened:
            with self.assertRaisesRegex(runtime_io.ApplyError, 'no reviewed ABI'):
                runtime_io._reviewed_codec_pin()
            opened.assert_not_called()

    def test_readiness_reports_tuple_pins_without_executing_them(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            (directory / 'SOURCE_MANIFEST.json').write_bytes(b'owned manifest')
            (directory / 'codec').write_bytes(b'owned alternative')
            value = runtime_report.component_readiness(directory, SHA(b'owned manifest'),
                {'codec': (SHA(b'owned legacy'), SHA(b'owned alternative'))}, lambda _: '/tool')
            self.assertEqual(value['status'], 'prerequisites-matched')
            self.assertFalse(value['codec_executed'])
            (directory / 'codec').write_bytes(b'unknown')
            self.assertEqual(runtime_report.component_readiness(directory, SHA(b'owned manifest'),
                {'codec': (SHA(b'owned legacy'), SHA(b'owned alternative'))}, lambda _: '/tool')['status'], 'blocked')


if __name__ == '__main__':
    unittest.main()
