"""Create a bounded progress manifest and explicit Git pathspec; no hardware/network."""
from pathlib import Path
import datetime,hashlib,json,subprocess

ROOT=Path(__file__).resolve().parents[1]
PREFIXES=['firmware/B0B1','firmware/B0B2','firmware/B0B3',
          'validation/20261025_p005_i0','validation/20261025_26_offline']
EXPLICIT=['.gitignore','.gitattributes','README.md','docs/STATUS.md','docs/TIMELINE.md',
          'docs/WORK_20261025_26.md','tools/prepare_progress_20261025_26.py',
          'tools/verify_progress_20261025_26.py','support/monitor_control.py','support/server.py',
          'web/flight-console/local/attitude_tracking.py','web/flight-console/local/receiver_setpoints.py',
          'web/flight-console/local/test_attitude_tracking.py','web/flight-console/local/test_receiver_setpoints.py']
M=ROOT/'docs/WORK_ARCHIVE_20261025_26.json'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()

def omit(p,n):
 if n.startswith('firmware/B0B3/'):return None # Prevalidated exact curated manifest below.
 if any(x in p.parts for x in ['__pycache__','impl','.git']):return 'Generated implementation/cache directory'
 if p.suffix.lower()in{'.vvp','.pyc','.pyo','.exe','.dll','.p'}:return 'Compiled intermediate/tool binary'
 if '/verified_timing_20261025/evidence/blobs/'in n:return 'Original full-package content-addressed blob store; local complete package retained'
 if p.suffix.lower()in{'.mp4','.mov','.webm','.avi','.zip'}:return 'Full recording or original package retained locally'
 if p.suffix.lower()=='.bin'and '/tests/'not in n:return 'Raw byte stream retained locally'
 if '/hardware/'in n and p.suffix.lower()=='.jsonl':return 'Full hardware telemetry retained locally'
 if '/hardware/'in n and p.suffix.lower()=='.csv'and(p.stat().st_size>1048576 or p.stem.lower().startswith(('raw','snapshots','recent','telemetry','decoded','frames'))):return 'Full hardware sample table retained locally'
 if p.suffix.lower()in{'.json','.log','.txt'}and p.stat().st_size>5*1048576:return 'Large raw evidence retained locally; summaries published'
 if p.suffix.lower()=='.fs'and not(n.startswith('firmware/B0B3/release/')or n=='firmware/B0B2/verified_timing_20261025/bitstream/acg720_ano_port.fs'):return 'Unselected/duplicate historical bitstream retained locally'
 if p.name.startswith('.env')or p.suffix.lower()in{'.pem','.key','.token'}:return 'Local secret/configuration, never exported'
 return None

def main():
 assert(ROOT/'firmware/B0B3/export_manifest.json').is_file(),'Wait for complete B0B3 export'
 candidates={ROOT/n for n in EXPLICIT}
 for prefix in PREFIXES:
  d=ROOT/prefix;assert d.is_dir(),prefix
  if prefix=='firmware/B0B3':
   exported=json.loads((d/'export_manifest.json').read_text(encoding='utf8'))
   names=set(exported['files'])|set(exported['manifest_self_exclusions'])
   assert {p.relative_to(d).as_posix()for p in d.rglob('*')if p.is_file()}==names
   candidates.update(d/n for n in names);continue
  candidates.update(p for p in d.rglob('*')if p.is_file())
 files={};omitted={}
 for p in sorted(candidates):
  assert p.is_file()and p.resolve().is_relative_to(ROOT)
  n=p.relative_to(ROOT).as_posix();reason=omit(p,n)
  if reason:
   # Cache is mutable and carries no research/build provenance.
   if '__pycache__'not in p.parts and p.suffix not in{'.vvp','.pyc','.pyo'}:
    omitted[n]=dict(bytes=p.stat().st_size,sha256=sha(p),reason=reason)
   continue
  assert p.stat().st_size<100*1048576,('Git-host size limit',n)
  files[n]=dict(bytes=p.stat().st_size,sha256=sha(p))
 ignored=subprocess.run(['git','check-ignore','--stdin','-z'],input=b'\0'.join(n.encode()for n in files)+b'\0',cwd=ROOT,capture_output=True)
 assert ignored.returncode in{0,1}and not ignored.stdout,('Selected paths ignored',ignored.stdout.decode())
 ref=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
 data=dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),timezone='Asia/Shanghai',
  parent_commit=ref,scope='2026-10-25/26 bounded firmware, monitoring and evidence archive; not a new build or hardware test',
  source_bytes_preserved=True,files=files,omitted_local_files=omitted,
  omission_note='Historical full-package manifests/readmes retain their original scope; excluded inputs remain local. B0B3 has a separate self-contained export verifier. No full original-archive replay is claimed.',
  hardware_accessed=False,git_commit_dates_backdated=False)
 M.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
 M.with_suffix('.sha256').write_text(sha(M)+'  '+M.name+'\n',encoding='utf8')
 names=list(files)+['docs/WORK_ARCHIVE_20261025_26.json','docs/WORK_ARCHIVE_20261025_26.sha256']
 out=ROOT/'out/progress_20261025_26';out.mkdir(parents=True,exist_ok=True)
 (out/'stage_paths.nul').write_bytes(b'\0'.join(n.encode('utf8')for n in names)+b'\0')
 print(json.dumps(dict(selected_files=len(files),selected_bytes=sum(v['bytes']for v in files.values()),
  omitted_files=len(omitted),omitted_bytes=sum(v['bytes']for v in omitted.values()),
  manifest_sha256=sha(M),pathspec='out/progress_20261025_26/stage_paths.nul'),indent=2))
if __name__=='__main__':main()
