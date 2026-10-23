"""Readiness diagnostics enumerate blockers without executing native components."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location('runtime_report', ROOT / 'tools/runtime_report.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class RuntimeReadiness(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.backend = Path(self.temp.name)
        self.manifest = b'synthetic source manifest\n'
        self.io = b'raise AssertionError("must never import this fixture")\n'
        self.codec = b'not an executable\n'
        self.sha = lambda value: hashlib.sha256(value).hexdigest()
        self.pins = {'runtime_io.py': self.sha(self.io), 'codec': self.sha(self.codec)}

    def write_components(self):
        for name, data in [('SOURCE_MANIFEST.json', self.manifest),
                           ('runtime_io.py', self.io), ('codec', self.codec)]:
            (self.backend / name).write_bytes(data)

    def inspect(self, find_tool=lambda name: '/synthetic-private-path/' + name):
        return MODULE.component_readiness(self.backend, self.sha(self.manifest), self.pins, find_tool)

    def test_all_missing_components_are_reported_without_fail_fast(self):
        result = self.inspect()
        self.assertEqual(result['status'], 'blocked')
        self.assertEqual([item['status'] for item in result['components']], ['missing'] * 3)

    def test_matching_files_are_only_prerequisites_not_native_success(self):
        self.write_components()
        result = self.inspect()
        self.assertEqual(result['status'], 'prerequisites-matched')
        self.assertFalse(result['codec_executed'])
        self.assertFalse(result['native_workflow_verified'])

    def test_changed_component_does_not_hide_other_results(self):
        self.write_components()
        (self.backend / 'codec').write_bytes(b'changed')
        result = self.inspect()
        self.assertEqual([item['status'] for item in result['components']],
                         ['matched', 'matched', 'hash-mismatch'])
        self.assertEqual(result['status'], 'blocked')

    def test_symlink_is_rejected_even_when_bytes_would_match(self):
        self.write_components()
        (self.backend / 'codec').rename(self.backend / 'alternate')
        (self.backend / 'codec').symlink_to(self.backend / 'alternate')
        item = self.inspect()['components'][-1]
        self.assertEqual(item['status'], 'symlink-rejected')
        self.assertNotIn('actual_sha256', item)

    def test_directory_is_not_hashed_as_a_component(self):
        self.write_components()
        (self.backend / 'codec').unlink()
        (self.backend / 'codec').mkdir()
        self.assertEqual(self.inspect()['components'][-1]['status'], 'not-a-regular-file')

    def test_missing_media_tool_blocks_prerequisites(self):
        self.write_components()
        result = self.inspect(lambda name: None if name == 'ffprobe' else '/private/tool')
        self.assertEqual(result['status'], 'blocked')
        self.assertEqual(result['media_tools_available'], {'ffmpeg': True, 'ffprobe': False})

    def test_report_does_not_include_private_paths(self):
        self.write_components()
        result = json.dumps(self.inspect())
        self.assertNotIn(str(self.backend), result)
        self.assertNotIn('/synthetic-private-path', result)

    def test_component_mutated_during_read_is_not_reported_as_a_stable_hash(self):
        self.write_components()
        original_sha256 = hashlib.sha256
        codec_path, codec_bytes = self.backend / 'codec', self.codec

        class MutatingHash:
            def __init__(self):
                self.value = original_sha256()
                self.changed = False

            def update(self, block):
                self.value.update(block)
                if block == codec_bytes and not self.changed:
                    self.changed = True
                    with codec_path.open('ab') as stream:
                        stream.write(b'concurrent synthetic change\n')

            def hexdigest(self):
                return self.value.hexdigest()

        with patch.object(MODULE.hashlib, 'sha256', MutatingHash):
            result = MODULE.component_readiness(self.backend, original_sha256(self.manifest).hexdigest(),
                                                self.pins, lambda name: '/synthetic/tool')
        self.assertEqual(result['components'][-1]['status'], 'changed-during-inspection')
        self.assertEqual(result['status'], 'blocked')


if __name__ == '__main__':
    unittest.main()
