#!/usr/bin/env python3
"""Read an explicitly supplied plaintext timeline; emit a content-redacted schema inventory.

No native libraries, private draft discovery, decryption, service calls or source writes.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import sys

MAX_BYTES = 64 * 1024 * 1024
KNOWN = {('185.0.0', 360000), ('187.0.0', 360000), ('189.0.0', 360000)}


def strict_json(data):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Duplicate JSON object key: ' + key)
            result[key] = value
        return result
    def real(value):
        result = float(value)
        if not math.isfinite(result):
            raise ValueError('Nonfinite JSON value')
        return result
    return json.loads(data, object_pairs_hook=pairs, parse_float=real,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Nonfinite JSON value')))


def inspect(document):
    if not isinstance(document, dict):
        raise ValueError('Expected a plaintext timeline JSON object')
    material_groups = document.get('materials')
    tracks = document.get('tracks')
    if not isinstance(material_groups, dict) or not isinstance(tracks, list):
        raise ValueError('Expected materials object and tracks array')
    report = {
        'schema': 'jianying-plaintext-schema-inventory/v1',
        'evidence_type': 'parsed-static-plaintext',
        'native_execution': False,
        'media_paths_followed': False,
        'content_redacted': True,
        'timeline_schema': {'new_version': document.get('new_version'), 'version': document.get('version')},
        'reviewed_schema': type(document.get('version')) is int and (document.get('new_version'), document.get('version')) in KNOWN,
        'root_fields': sorted(document),
        'track_types': {}, 'material_buckets': {}, 'segment_fields': {},
        'features': {}, 'issues': [],
    }
    features, segment_fields, track_types = Counter(), Counter(), Counter()
    materials, used, identities = {}, set(), set()
    for bucket, values in material_groups.items():
        if not isinstance(values, list):
            report['issues'].append({'code': 'material-bucket-not-array', 'bucket': bucket})
            continue
        fields = Counter()
        for node in values:
            if not isinstance(node, dict):
                report['issues'].append({'code': 'material-not-object', 'bucket': bucket})
                continue
            fields.update(node.keys())
            key = node.get('id')
            if isinstance(key, str):
                if key in materials:
                    report['issues'].append({'code': 'duplicate-material-id', 'bucket': bucket})
                materials[key] = (bucket, node)
            else:
                report['issues'].append({'code': 'missing-material-id', 'bucket': bucket})
            if bucket == 'speeds' and node.get('curve_speed'):
                features['curve-speed-materials'] += 1
            if bucket == 'drafts':
                features['nested-draft-materials'] += 1
                if isinstance(node.get('draft'), dict):
                    features['embedded-draft-materials'] += 1
                if node.get('draft_file_path'):
                    features['external-draft-sidecars-not-followed'] += 1
            if bucket == 'texts':
                try:
                    content = strict_json(node['content']) if isinstance(node.get('content'), str) else node.get('content', {})
                    styles = content.get('styles', [])
                    features['text-style-runs'] += len(styles)
                    if len(styles) > 1:
                        features['multistyle-text-materials'] += 1
                except (ValueError, TypeError, AttributeError):
                    report['issues'].append({'code': 'invalid-rich-text', 'bucket': bucket})
        report['material_buckets'][bucket] = {'count': len(values), 'fields': dict(sorted(fields.items()))}
    for ti, track in enumerate(tracks):
        if not isinstance(track, dict) or not isinstance(track.get('segments'), list):
            report['issues'].append({'code': 'invalid-track', 'track': ti})
            continue
        track_types[str(track.get('type'))] += 1
        for si, segment in enumerate(track['segments']):
            if not isinstance(segment, dict):
                report['issues'].append({'code': 'invalid-segment', 'track': ti, 'segment': si})
                continue
            segment_fields.update(segment.keys())
            key = segment.get('id')
            if not isinstance(key, str) or key in identities:
                report['issues'].append({'code': 'missing-or-duplicate-segment-id', 'track': ti, 'segment': si})
            identities.add(key if isinstance(key, str) else (ti, si))
            refs = segment.get('extra_material_refs', [])
            if not isinstance(refs, list):
                report['issues'].append({'code': 'invalid-material-refs', 'track': ti, 'segment': si})
                refs = []
            for ref in [segment.get('material_id'), *refs]:
                if not isinstance(ref, str) or ref not in materials:
                    report['issues'].append({'code': 'dangling-material-reference', 'track': ti, 'segment': si})
                else:
                    used.add(ref)
            parsed = {}
            for field in ('source_timerange', 'target_timerange'):
                value = segment.get(field)
                if value is None:
                    continue
                valid = isinstance(value, dict) and all(type(value.get(k, 0)) is int and value.get(k, 0) >= 0 for k in ('start', 'duration'))
                if not valid:
                    report['issues'].append({'code': 'noninteger-microsecond-range', 'track': ti, 'segment': si, 'field': field})
                else:
                    parsed[field] = value
            if parsed.get('source_timerange', {}).get('start', 0):
                features['source-trim-segments'] += 1
            speed = segment.get('speed', 1)
            if isinstance(speed, (int, float)) and not isinstance(speed, bool) and speed != 1:
                features['constant-speed-segments'] += 1
            source, target = parsed.get('source_timerange'), parsed.get('target_timerange')
            if source and target and type(speed) in (int, float) and speed > 0:
                if abs(source.get('duration', 0) - target.get('duration', 0) * speed) > 2:
                    features['source-target-speed-disagreement'] += 1
            for field in ('common_keyframes', 'keyframe_refs', 'reverse', 'responsive_layout'):
                if segment.get(field):
                    features[field + '-segments'] += 1
            clip = segment.get('clip', {})
            if isinstance(clip, dict):
                if clip.get('rotation', 0):
                    features['rotation-segments'] += 1
                if clip.get('alpha', 1) != 1:
                    features['alpha-segments'] += 1
                if any(clip.get('flip', {}).values()):
                    features['flip-segments'] += 1
    report['track_types'] = dict(sorted(track_types.items()))
    report['segment_fields'] = dict(sorted(segment_fields.items()))
    report['features'] = dict(sorted(features.items()))
    report['unreferenced_material_count'] = len(set(materials) - used)
    report['limitations'] = [
        'Field presence is static evidence, not execution or visual equivalence.',
        'No schema migration, default normalization or effect compatibility is asserted.',
        'Nested draft sidecars and referenced media are not opened.',
        'Counts omit text content, paths, material IDs, account metadata and source media.',
    ]
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path, help='Explicit plaintext JSON file; never an encrypted draft')
    parser.add_argument('--out', type=Path, help='New report path; existing files are refused. Default: stdout')
    args = parser.parse_args()
    try:
        if args.input.stat().st_size > MAX_BYTES:
            raise ValueError('Input exceeds 64 MiB limit')
        with args.input.open('rb') as source:
            data = source.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError('Input exceeds 64 MiB limit')
        report = inspect(strict_json(data))
        report['source_sha256'] = hashlib.sha256(data).hexdigest()
        report['source_bytes'] = len(data)
        payload = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
        if args.out:
            with args.out.open('x', encoding='utf-8') as output:
                output.write(payload)
        else:
            sys.stdout.write(payload)
        return 0
    except (OSError, ValueError, TypeError, RecursionError) as error:
        print('Schema inspection failed: ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
