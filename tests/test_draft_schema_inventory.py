import importlib.util
import json
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location('draft_schema_inventory', Path(__file__).resolve().parents[1] / 'tools' / 'inspect_draft_schema.py')
inventory = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inventory)


class InventoryTests(unittest.TestCase):
    def test_counts_schema_features_without_leaking_content_paths_or_identity(self):
        document = {'new_version': '189.0.0', 'version': 360000,
                    'materials': {'videos': [{'id': 'private-identity', 'path': '/private/source.mov'}],
                                  'texts': [{'id': 'secret-text', 'content': json.dumps({'text': 'SECRET CONTENT', 'styles': [{}, {}]})}],
                                  'drafts': [{'id': 'nested', 'draft_file_path': '/private/child.json'}]},
                    'tracks': [{'type': 'video', 'segments': [{'id': 'private-segment', 'material_id': 'private-identity',
                        'source_timerange': {'start': 1_000_000, 'duration': 2_000_000},
                        'target_timerange': {'start': 0, 'duration': 1_000_000}, 'speed': 2,
                        'clip': {'rotation': 20, 'alpha': .5}, 'common_keyframes': [{'id': 'private-keyframe'}]}]}]}
        report = inventory.inspect(document)
        self.assertTrue(report['reviewed_schema'])
        self.assertEqual(report['features']['source-trim-segments'], 1)
        self.assertEqual(report['features']['constant-speed-segments'], 1)
        self.assertEqual(report['features']['multistyle-text-materials'], 1)
        self.assertEqual(report['features']['external-draft-sidecars-not-followed'], 1)
        self.assertEqual(report['unreferenced_material_count'], 2)
        serialized = json.dumps(report)
        for secret in ['private-identity', '/private', 'SECRET CONTENT', 'private-segment', 'private-keyframe']:
            self.assertNotIn(secret, serialized)

    def test_duplicate_keys_and_nonfinite_input_are_rejected(self):
        for source in ['{"id":1,"id":2}', '{"value":NaN}', '{"value":Infinity}', '{"value":1e309}']:
            with self.assertRaises(ValueError):
                inventory.strict_json(source)

    def test_unknown_schema_and_invalid_time_references_remain_visible(self):
        report = inventory.inspect({'new_version': 'future', 'version': 1, 'materials': {},
                                    'tracks': [{'type': 'video', 'segments': [{'id': 's', 'material_id': 'missing',
                                                'target_timerange': {'duration': 1.5}}]}]})
        self.assertFalse(report['reviewed_schema'])
        self.assertEqual({item['code'] for item in report['issues']}, {'dangling-material-reference', 'noninteger-microsecond-range'})


if __name__ == '__main__':
    unittest.main()
