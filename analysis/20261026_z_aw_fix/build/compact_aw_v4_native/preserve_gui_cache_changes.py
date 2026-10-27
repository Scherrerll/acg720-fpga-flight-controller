"""Preserve actual GUI cache changes, then restore the exact sealed pre-view bytes."""
from pathlib import Path
import datetime,difflib,hashlib,json,shutil
O=Path(__file__).resolve().parent;R=O.parents[3]
read=lambda p:json.loads(p.read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
baseline=read(O/'GUI_BASELINE.json');view=read(O/'GUI_VIEW_RESULT.json')
A=Path(baseline['attempt']);B=Path(baseline['backup']);D=O/'gui_cache_changes'
assert not D.exists();D.mkdir();items={};diff=''
assert view['changed_baseline_files']==['source/acg720_ano_port.gprj.user','source/impl/pnr/device.cfg']
for name in view['changed_baseline_files']:
    before=B/name;current=A/name;copy=D/name
    assert sha(before)==baseline['files'][name]['sha256']
    copy.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(current,copy)
    assert sha(copy)==sha(current)
    diff+=''.join(difflib.unified_diff(before.read_text(encoding='utf8').splitlines(True),current.read_text(encoding='utf8').splitlines(True),fromfile='sealed/'+name,tofile='GUI-generated/'+name))
    items[name]={'original_sha256':sha(before),'actual_GUI_generated_sha256':sha(copy),'preserved':str(copy.relative_to(R))}
    current.write_bytes(before.read_bytes());assert sha(current)==sha(before)
(D/'observed_changes.diff').write_text(diff,encoding='utf8')
assert all(sha(A/name)==record['sha256'] for name,record in baseline['files'].items())
record={'restored_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Official GUI automatically saved UI state and regenerated device.cfg while viewing. Both actual changed files preserved before byte-exact restoration from the verified pre-GUI copy. No route/build/device action. Original failed terminal remains failed.',
    'view_result_sha256':sha(O/'GUI_VIEW_RESULT.json'),'baseline_sha256':sha(O/'GUI_BASELINE.json'),'all_98_original_artifact_bytes_restored':True,
    'items':items,'diff_sha256':sha(D/'observed_changes.diff')}
(O/'GUI_CACHE_RESTORATION.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8')
print(json.dumps({'all_98_original_artifact_bytes_restored':True,'actual_GUI_cache_files_preserved':2,'restoration_sha256':sha(O/'GUI_CACHE_RESTORATION.json')}))
