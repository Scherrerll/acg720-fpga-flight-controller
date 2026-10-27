"""Preserve actual failed native build bytes before opening its exact project in the IDE."""
from pathlib import Path
import hashlib,json,shutil,stat
O=Path(__file__).resolve().parent;R=O.parents[3]
A=R/'out/z_aw_fix_20261026/compact_aw_v4_native/physical_p3r0_01'
B=R/'out/z_aw_fix_20261026/native_v4_GUI_baseline_snapshot'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
terminal=read(O/'physical_p3r0_01/TERMINAL_MANIFEST.json')
assert terminal['vendor_actual_p_wait']==0 and terminal['runner_actual_p_wait']==1 and not terminal['passed']
assert not B.exists() and not (O/'GUI_BASELINE.json').exists()
files=[];excluded=[]
for path in A.rglob('*'):
    if not path.is_file():continue
    relative=path.relative_to(A)
    if 'tmp' in relative.parts or path.name.lower().startswith('.env') or '.env' in [s.lower() for s in path.suffixes]:
        excluded.append(relative.as_posix());continue
    assert not path.is_symlink() and path.resolve().is_relative_to(A.resolve())
    files.append(path)
B.mkdir();items={}
for path in files:
    relative=path.relative_to(A);dest=B/relative;dest.parent.mkdir(parents=True,exist_ok=True)
    before=sha(path);shutil.copy2(path,dest);assert sha(dest)==before==sha(path)
    items[relative.as_posix()]={'sha256':before,'bytes':path.stat().st_size}
protected={}
for name in ['acg720_ano_port.gprj','acg720_ano_port.cst']:
    path=A/'source'/name;mode=stat.S_IMODE(path.stat().st_mode)
    protected[str(path)]={'original_mode':mode,'sha256':sha(path)}
    path.chmod(stat.S_IREAD)
(O/'GUI_BASELINE.json').write_text(json.dumps({'scope':'Exact real native project, all non-temporary build evidence copied before GUI viewing. Project/CST read-only attributes protect source inputs. No data deletion or device action.',
    'attempt':str(A),'backup':str(B),'files':items,'excluded_temp_or_secret_paths':excluded,
    'protected_file_attributes':protected,'standalone_p_protection':'Never decrypt or alter protected p files; native tool may read its own layout cache.'},indent=2)+'\n',encoding='utf8')
pr=A/'source/impl/pnr/acg720_ano_port.pr';header=pr.open('rb').read(384)
print(json.dumps({'preserved_files':len(items),'protected_project':str(A/'source/acg720_ano_port.gprj'),
    'PR_header_ascii_preview':''.join(chr(c) if 32<=c<127 else '.' for c in header),'hardware_operation':False}))
