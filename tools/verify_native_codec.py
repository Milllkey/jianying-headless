#!/usr/bin/env python3
"""Sandboxed synthetic codec ABI check; never reads a user draft or contacts a service."""
import argparse
import hashlib
import json
import os
import plistlib
import shutil
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'engine'))
from codec_profiles import CODEC_FILENAME, MANIFEST, PROFILE_MANIFEST_SHA, validate_codec_runtime, load_profiles
from runtime_profiles import validate_identity

if not __debug__:
    raise SystemExit('Verification requires assertions; do not run with python -O')

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--codec', type=Path, default=ROOT / 'bridge' / CODEC_FILENAME,
                    help='An exact already-reviewed local codec; unknown bytes are refused')
args = parser.parse_args()
APP = Path('/Applications/VideoFusion-macOS.app')
env = {'PATH': '/usr/bin:/bin:/usr/sbin:/sbin', 'LC_ALL': 'C'}
def digest(path):
    if not path.is_file() or path.is_symlink(): raise ValueError('Expected a regular non-symlink file')
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''): value.update(block)
    return value.hexdigest()

library_sha = digest(APP / 'Contents/Frameworks/libvideoeditor.dylib')
info = plistlib.loads((APP / 'Contents/Info.plist').read_bytes())
version = validate_identity(info, library_sha)
codec_sha = digest(args.codec)
profile_name = validate_codec_runtime(codec_sha, version, library_sha)
codec_profile = load_profiles()[profile_name]
for name, expected in codec_profile['source_files'].items():
    if Path(name).name != name or digest(ROOT / 'bridge' / name) != expected: raise ValueError('Reviewed codec source changed')
for target in (APP, args.codec):
    subprocess.run(['/usr/bin/codesign', '--verify', '--strict', *(['--deep'] if target == APP else []), str(target)], env=env, check=True, capture_output=True, timeout=180)
details = subprocess.run(['/usr/bin/codesign', '-dv', '--verbose=4', str(APP)], env=env, check=True, capture_output=True, text=True, timeout=30)
if 'TeamIdentifier=X2JNK7LY8J' not in details.stderr.splitlines(): raise ValueError('Unexpected editor signing identity')
work = ROOT / 'work'; work.mkdir(mode=0o700, exist_ok=True)
BASE = Path(tempfile.mkdtemp(prefix='codec-verify-', dir=work)); os.chmod(BASE, 0o700)
JOB = BASE / 'sandbox'; JOB.mkdir(mode=0o700); (JOB / 'tmp').mkdir(mode=0o700)
BINARY = JOB / CODEC_FILENAME
shutil.copyfile(args.codec, BINARY); BINARY.chmod(0o700)
if digest(BINARY) != codec_sha: raise ValueError('Copied codec identity changed')
BUILD = {'app_version': version, 'library_sha256': library_sha}
FIX = Path(tempfile.mkdtemp(prefix='fixtures-', dir=JOB)); os.chmod(FIX, 0o700)
sha=lambda b:hashlib.sha256(b).hexdigest()
def lit(p):return json.dumps(str(p))
profile='''(version 1)
(allow default)
(deny network*)
(deny file-read-data (subpath "/Users") (subpath "/Volumes") (subpath "/private/var/root") (subpath "/private/var/folders") (subpath "/Library/Keychains"))
(deny file-write*)
(allow process-exec (literal %s) (literal "/bin/cat") (literal "/usr/bin/touch") (literal "/usr/bin/curl"))
(allow sysctl-read)
(allow file-read-data (subpath %s) (subpath %s) (subpath "/System") (subpath "/usr/lib") (subpath "/usr/share") (subpath "/Library/Apple") (subpath "/bin") (subpath "/usr/bin") (literal "/dev/urandom") (literal "/dev/random") (literal "/dev/null"))
(allow file-write* (subpath %s) (literal "/dev/null"))
'''%(lit(BINARY),lit(JOB),lit(APP),lit(JOB))
profile += '(allow file-read-data ' + ' '.join('(literal '+lit(p)+')' for p in JOB.parents) + ')\n'
SB=JOB/'codec.sb';SB.write_text(profile)
env={'PATH':'/usr/bin:/bin:/usr/sbin:/sbin','LC_ALL':'C','TMPDIR':str(JOB/'tmp')+'/'}
report={'schema':'jianying-headless-codec-probe/v1','status':'probing','codec_sha256':sha(BINARY.read_bytes()),'app_version':BUILD['app_version'],
 'library_sha256':BUILD['library_sha256'],'sandbox_sha256':sha(profile.encode()),'sandbox':profile,'network_permitted':False,
 'private_user_file_reads_permitted':False,'writes_limited_to_job':True,'system_ipc_restricted':False,'cases':[],'runtime_pins_changed_by_tool':False,'codec_build_profile':profile_name,'official_signature_verified':True,'synthetic_only':True,
 'codec_profile_manifest_sha256':PROFILE_MANIFEST_SHA,'source_files':codec_profile['source_files']}
def save(): (JOB/'probe-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
def command(label,args,expect=0,pass_fds=()):
 p=subprocess.run(['/usr/bin/sandbox-exec','-f',str(SB),*map(str,args)],env=env,cwd=JOB,capture_output=True,timeout=30,pass_fds=pass_fds)
 record={'name':label,'exit_code':p.returncode,'expected_exit_code':expect,'passed':p.returncode==expect,'stdout':p.stdout.decode('utf8','replace')[-4000:],'stderr':p.stderr.decode('utf8','replace')[-8000:]}
 report['cases'].append(record);save()
 if p.returncode!=expect:raise AssertionError(json.dumps(record))
 return p
payload=json.dumps({'id':'owned-synthetic-20261023','version':360000,'new_version':'189.0.0','tracks':[],
 'materials':{},'note':'自制夹具，no private draft or account'},ensure_ascii=False,separators=(',',':')).encode()
plain=FIX/'plain.json';plain.write_bytes(payload); cipher=FIX/'encrypted.bin'; decoded=FIX/'decoded.json'
try:
 command('owned-file-read',['/bin/cat',plain])
 command('encrypt',[BINARY,'encrypt',plain,cipher]);command('decrypt',[BINARY,'decrypt',cipher,decoded]);assert decoded.read_bytes()==payload
 report['roundtrip']={'source_sha256':sha(payload),'cipher_sha256':sha(cipher.read_bytes()),'decoded_sha256':sha(decoded.read_bytes()),'cipher_differs':cipher.read_bytes()!=payload,'decoded_matches':True,'output_mode':oct(decoded.stat().st_mode&0o777)}
 assert cipher.read_bytes()!=payload;assert decoded.stat().st_mode&0o777==0o600
 # Inherited file descriptors must be true pipes, and output identities stay exact.
 r,w=os.pipe();os.write(w,payload);os.close(w)
 try:command('encrypt-fd',[BINARY,'encrypt-fd',r,FIX/'pipe-encrypted.bin'],pass_fds=(r,))
 finally:os.close(r)
 r,w=os.pipe()
 try:
  command('decrypt-fd',[BINARY,'decrypt-fd',FIX/'pipe-encrypted.bin',w],pass_fds=(w,));os.close(w);w=None
  data=os.read(r,1024*1024);assert data==payload
 finally:
  os.close(r)
  if w is not None:os.close(w)
 report['pipe_roundtrip_matches']=True
 large=json.dumps({'owned':'合成 data '*40000},ensure_ascii=False).encode();largefile=FIX/'large.json';largefile.write_bytes(large)
 command('large-file-encrypt',[BINARY,'encrypt',largefile,FIX/'large-encrypted.bin'])
 command('large-file-decrypt',[BINARY,'decrypt',FIX/'large-encrypted.bin',FIX/'large-decoded.json']);assert (FIX/'large-decoded.json').read_bytes()==large
 report['large_roundtrip']={'bytes':len(large),'sha256':sha(large),'decoded_matches':True}
 oversized=FIX/'oversized-sparse.bin'
 with oversized.open('wb') as f:f.truncate(256*1024*1024+1)
 command('oversized-input-refused',[BINARY,'encrypt',oversized,FIX/'oversized-encrypted.bin'],expect=1);assert not (FIX/'oversized-encrypted.bin').exists()
 command('directory-input-refused',[BINARY,'encrypt',FIX,FIX/'directory-encrypted.bin'],expect=1)
 r,w=os.pipe()
 try:
  command('encrypt-wrong-fd-direction',[BINARY,'encrypt-fd',w,FIX/'wrong-direction.bin'],expect=1,pass_fds=(w,))
  command('decrypt-wrong-fd-direction',[BINARY,'decrypt-fd',cipher,r],expect=1,pass_fds=(r,))
 finally:os.close(r);os.close(w)
 r,w=os.pipe();os.close(w)
 try:command('empty-encrypt-pipe-refused',[BINARY,'encrypt-fd',r,FIX/'empty-pipe.bin'],expect=1,pass_fds=(r,))
 finally:os.close(r)
 command('overwrite-refused',[BINARY,'encrypt',plain,cipher],expect=1);assert decoded.read_bytes()==payload
 link=FIX/'input-symlink';link.symlink_to(plain)
 command('input-symlink-refused',[BINARY,'encrypt',link,FIX/'symlink-encrypted.bin'],expect=1);assert not (FIX/'symlink-encrypted.bin').exists()
 outlink=FIX/'output-symlink';outlink.symlink_to(decoded)
 command('output-symlink-refused',[BINARY,'encrypt',plain,outlink],expect=1);assert decoded.read_bytes()==payload
 parentlink=FIX/'parent-symlink';parentlink.symlink_to(FIX,target_is_directory=True)
 command('parent-symlink-refused',[BINARY,'encrypt',plain,parentlink/'rejected.bin'],expect=1);assert not (FIX/'rejected.bin').exists()
 for name,data in [('empty',b''),('invalid',b'owned-invalid-ciphertext'),('truncated',cipher.read_bytes()[:8])]:
  path=FIX/(name+'.bin');path.write_bytes(data);out=FIX/(name+'-decoded.json')
  command(name+'-cipher-refused',[BINARY,'decrypt',path,out],expect=1);assert not out.exists()
 command('stdout-fd-refused',[BINARY,'decrypt-fd',cipher,'1'],expect=1)
 fd=os.open(plain,os.O_RDONLY)
 try:command('regular-fd-refused',[BINARY,'encrypt-fd',fd,FIX/'regular-fd.bin'],expect=1,pass_fds=(fd,))
 finally:os.close(fd)
 sentinel=BASE/'outside-synthetic-sentinel.txt';sentinel.write_text('synthetic sentinel only')
 command('outside-user-read-denied',['/bin/cat',sentinel],expect=1)
 outside=BASE/'outside-write-must-not-exist'
 command('outside-write-denied',['/usr/bin/touch',outside],expect=1);assert not outside.exists()
 listener=socket.socket();listener.bind(('127.0.0.1',0));listener.listen();listener.settimeout(.25)
 try:
  command('loopback-network-denied',['/usr/bin/curl','--noproxy','*','--connect-timeout','1',f'http://127.0.0.1:{listener.getsockname()[1]}/'],expect=7)
  try:conn,_=listener.accept();conn.close();raise AssertionError('sandbox allowed a network connection')
  except socket.timeout:pass
 finally:listener.close()
 assert digest(APP / 'Contents/Frameworks/libvideoeditor.dylib') == library_sha
 assert plistlib.loads((APP / 'Contents/Info.plist').read_bytes()) == info
 assert digest(args.codec) == digest(BINARY) == codec_sha
 assert digest(MANIFEST) == PROFILE_MANIFEST_SHA
 for name, expected in codec_profile['source_files'].items():
  assert digest(ROOT / 'bridge' / name) == expected
 report['source_and_runtime_unchanged_after_probe']=True
 report['status']='synthetic-probe-passed';save()
 print(json.dumps({'status':report['status'],'job':str(JOB),'cases':len(report['cases']),'roundtrip':report['roundtrip'],'codec_sha256':report['codec_sha256']}))
except BaseException as exc:
 report['status']='probe-failed';report['error']=str(exc);save();raise
