from pathlib import Path
import hashlib,json,shutil,datetime
R=Path(__file__).resolve().parent;F=R/'fixture';D=R/'variants/storage_r2';DF=D/'fixture'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
q=json.loads((R/'qualification.json').read_text());assert q['offline_tests_passed']
for n,h in q['sources_sha256'].items():assert sha(F/n)==h
for n,h in q['evidence_sha256'].items():assert sha(R/n)==h
study=sorted((R/'synthesis').glob('target_storage_*/study.json'))[-1]
st=json.loads(study.read_text());assert st['parent_sources_sha256']==q['sources_sha256'] and st['range_lemma']['passed']
D.mkdir(parents=True,exist_ok=False)
files=set(q['evidence_sha256'])|{'qualification.json','baseline.json','说明.txt','实物验收要点.txt','DO_NOT_PROGRAM'}
files|={str(p.relative_to(R)).replace('\\','/') for p in R.glob('*.py')}
files|={'fixture/'+n for n in q['sources_sha256']}
files|={'fixture/'+n for n in json.loads((R/'baseline.json').read_text())['baseline_sources']}
files|={'fixture/build_project.py'}
for n in files:
 p=R/n
 if p.is_file():
  dest=D/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
shutil.copy2(F/'position/mtf_xyz_hold_control.v',D/'reference/storage_before_hold.v')
shutil.copy2(Path(st['folder'])/'position/mtf_xyz_hold_control.v',DF/'position/mtf_xyz_hold_control.v')
assert sha(DF/'position/mtf_xyz_hold_control.v')==st['range_lemma']['experimental_source_sha256']
traces={}
for n in ['height_rtl.txt','xy_rtl.txt','manual_rtl.txt']:
 p=R/'tests'/n;assert sha(p)==q['evidence_sha256']['tests/'+n]
 shutil.copy2(p,D/'reference'/('storage_before_'+n));traces[n]=sha(p)
(D/'reference/storage_parent.json').write_text(json.dumps(dict(source_sha256=sha(F/'position/mtf_xyz_hold_control.v'),
 parent_qualification_sha256=sha(R/'qualification.json'),trace_sha256=traces),indent=2))
shutil.copy2(R/'storage_equivalence_test_template.py',D/'test_storage_equivalence.py')
p=DF/'build.tcl';s=p.read_text();assert s.count('set_option -route_option 1')==1
p.write_text(s.replace('set_option -route_option 1','set_option -route_option 2'),encoding='utf8')
p=DF/'build_project.py';s=p.read_text();assert s.count("'route_option':'1'")==1 and s.count("actual_pnr.get('route_option')!='1'")==1
p.write_text(s.replace("'route_option':'1'","'route_option':'2'").replace("actual_pnr.get('route_option')!='1'","actual_pnr.get('route_option')!='2'"),encoding='utf8')
p=D/'qualify.py';s=p.read_text();assert s.count(" run('test_tools.py')")==1 and s.count(" files += [p for p in (ROOT/'reference')")==1
s=s.replace(" run('test_tools.py')"," run('test_tools.py')\n run('test_storage_equivalence.py')")
s=s.replace(" files += [p for p in (ROOT/'reference')"," files += [ROOT/'test_storage_equivalence.py']\n files += [p for p in (ROOT/'reference')")
p.write_text(s,encoding='utf8')
with (D/'说明.txt').open('a',encoding='utf8') as f:f.write('\n本目录另做了有界目标高度存储优化：Q16小数位与signed64运算保持；新旧高度/XY/手动RTL轨迹必须逐字节一致，完整资格复查通过后才可编译。\n')
(D/'status.json').write_text(json.dumps(dict(phase='storage_full_requalification',hardware_programmed=False,flash_changed=False,flight_ready=False),indent=2))
print(str(D),flush=True)
