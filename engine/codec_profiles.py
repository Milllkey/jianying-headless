"""Exact reviewed codec builds, separate from editor/export ABI authorization."""
import hashlib
import json
import os
import stat
from pathlib import Path

PROFILE_MANIFEST_SHA = 'ba943c1203a7fac988817ef125fcdb9dd094ee9000f64236120cba1594e08cc4'
CODEC_FILENAME = 'jy14_codec_hardened_11_4'
MANIFEST = Path(__file__).resolve().parent.parent / 'bridge/CODEC_PROFILES.json'


def load_profiles(path=MANIFEST, expected_sha=PROFILE_MANIFEST_SHA):
    path = Path(path)
    initial = path.lstat()
    if not stat.S_ISREG(initial.st_mode):
        raise ValueError('Codec profile manifest must be a regular file')
    identity = lambda s: (s.st_dev, s.st_ino, s.st_mode, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as stream:
        opened = os.fstat(stream.fileno())
        if not stat.S_ISREG(opened.st_mode) or opened.st_size > 65536:
            raise ValueError('Codec profile manifest must be a bounded regular file')
        raw = stream.read(65537)
        finished = os.fstat(stream.fileno())
    if any(identity(s) != identity(initial) for s in (opened, finished, path.lstat())):
        raise ValueError('Codec profile manifest changed while reading')
    if len(raw) > 65536 or hashlib.sha256(raw).hexdigest() != expected_sha:
        raise ValueError('Codec profile manifest fingerprint differs')
    value = json.loads(raw)
    if value.get('schema') != 'jianying-headless-codec-profiles/v1' or value.get('codec_filename') != CODEC_FILENAME:
        raise ValueError('Unexpected codec profile manifest')
    return value['profiles']


def profile_for_hash(fingerprint, profiles=None):
    profiles = load_profiles() if profiles is None else profiles
    matches = [(name, value) for name, value in profiles.items() if value['codec_sha256'] == fingerprint]
    if len(matches) != 1:
        raise ValueError('Codec fingerprint is not a reviewed build')
    return matches[0]


def validate_codec_runtime(fingerprint, version, library_sha):
    name, profile = profile_for_hash(fingerprint)
    if profile['runtime_libraries'].get(version) != library_sha:
        raise ValueError('Codec build has no reviewed ABI for this exact editor library')
    return name


def choose_build_profile(select_toolchain, explicit=None, developer_dir=None, version=None, library_sha=None):
    profiles = load_profiles()
    if explicit is not None and explicit not in profiles:
        raise ValueError('Unknown codec build profile: ' + explicit)
    failures = []
    for name, profile in profiles.items():
        if explicit is not None and name != explicit:
            continue
        if version is not None and profile['runtime_libraries'].get(version) != library_sha:
            failures.append(name + ': no reviewed ABI for this editor'); continue
        try:
            environment, identity = select_toolchain(profile['reproduction_environment'], developer_dir)
            return name, profile, environment, identity
        except (OSError, ValueError) as error:
            failures.append(name + ': ' + str(error))
    raise ValueError('No exact reviewed codec build profile matched.\n' + '\n'.join(failures))
