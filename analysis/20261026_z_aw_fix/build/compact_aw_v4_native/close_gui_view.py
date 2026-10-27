"""Verify preserved failed-build bytes and restore read-only file attributes after GUI viewing."""
from pathlib import Path
import datetime, hashlib, json, os
O=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
baseline=read(O/'GUI_BASELINE.json'); A=Path(baseline['attempt']);B=Path(baseline['backup'])
assert not (O/'GUI_VIEW_RESULT.json').exists()
changes=[]
for name,record in baseline['files'].items():
    assert sha(B/name)==record['sha256']
    if not (A/name).is_file() or sha(A/name)!=record['sha256']:changes.append(name)
for name,record in baseline['protected_file_attributes'].items():
    path=Path(name);assert sha(path)==record['sha256'];path.chmod(record['original_mode'])
result={'closed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'baseline_sha256':sha(O/'GUI_BASELINE.json'),'baseline_files':len(baseline['files']),
    'changed_baseline_files':changes,'all_preserved_bytes_unchanged':not changes,
    'original_file_attributes_restored':True,'hardware_operation':False,
    'observed':'Actual native project opened and FloorPlanner read its native netlist/CST/DB. Back-annotation dialog offers Port, Port Attribute, BSRAM, DSP, PLL, DSPLite only; no ordinary FF/LUT export. Cancelled dialog, closed FloorPlanner and IDE without saving or running any build. No full-placement export claim.'}
(O/'GUI_VIEW_RESULT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps(result,indent=2));assert not changes
