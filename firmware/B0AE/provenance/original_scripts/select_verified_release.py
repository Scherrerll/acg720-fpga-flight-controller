"""Select and independently verify an offline image. Never access hardware."""
from pathlib import Path
import datetime,difflib,hashlib,json,re,subprocess,sys
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
accepted=[]
for candidate in [R,R/'variants/place4',R/'variants/route2',R/'variants/reset_global',R/'variants/reset_global_route2',R/'variants/snapshot_global_route2',R/'variants/storage_r2']:
 manifest=candidate/'fixture/build_manifest.json'
 if not manifest.is_file():continue
 m=json.loads(manifest.read_text())
 if not m.get('verified'):continue
 baseline=json.loads((candidate/'baseline.json').read_text())
 assert sha(Path(baseline['parent'])/'fixture/acg720_ano_port.cst')==baseline['baseline_sources']['acg720_ano_port.cst'],'Parent pin constraints changed'
 p=subprocess.run([sys.executable,str(candidate/'fixture/build_project.py'),'--verify-existing'],cwd=candidate,capture_output=True,text=True,encoding='utf8')
 (candidate/'independent_verification.log').write_text(p.stdout+p.stderr,encoding='utf8')
 if p.returncode:raise RuntimeError('Independent verification failed: '+str(candidate)+'\n'+p.stdout+p.stderr)
 subprocess.run([sys.executable,str(candidate/'finalize_release.py')],cwd=candidate,check=True)
 accepted.append((float(m['fmax_mhz']),candidate,m))
assert accepted,'No independently verified offline build exists'
_,winner,m=max(accepted,key=lambda row:row[0])
q=json.loads((winner/'qualification.json').read_text())
parent=Path(json.loads((winner/'baseline.json').read_text())['parent'])
names=set(json.loads((winner/'baseline.json').read_text())['baseline_sources'])|set(q['sources_sha256'])|{'build_project.py'}
patch=[]
for name in sorted(names):
 old=parent/'fixture'/name;new=winner/'fixture'/name
 if not new.is_file():continue
 a=old.read_text(encoding='utf8',errors='replace') if old.is_file() else ''
 b=new.read_text(encoding='utf8',errors='replace')
 if a!=b:patch.extend(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='B0AD/'+name,tofile='B0AE/'+name))
(winner/'source_diff.patch').write_text(''.join(patch),encoding='utf8')
selection=dict(candidate='B0AE',selected_root=str(winner),selected_project=str(winner/'fixture/acg720_ano_port.gprj'),
 selected_build_script=str(winner/'fixture/build_project.py'),bitstream=m['bitstream'],fmax_mhz=m['fmax_mhz'],
 offline_release_sha256=sha(winner/'offline_release.json'),source_diff_sha256=sha(winner/'source_diff.patch'),
 verified_candidates=[dict(root=str(c),fmax_mhz=f) for f,c,_ in accepted],
 created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),hardware_programmed=False,flash_changed=False,flight_ready=False)
(R/'selected_release.json').write_text(json.dumps(selection,indent=2),encoding='utf8')
(R/'选用工程.txt').write_text('B0AE 离线编译验收通过的选用工程\n\n工程：'+selection['selected_project']+'\n重编译入口：'+selection['selected_build_script']+'\n镜像：'+m['bitstream']['path']+'\nSHA256：'+m['bitstream']['sha256']+'\nFmax：'+str(m['fmax_mhz'])+' MHz；未通网络0；建立/保持时间违例0。\n\n重编译以 build_project.py 调用的 build.tcl 为准；不得只凭 GUI 默认选项复现。\n本轮没有下载 FPGA、没有写 Flash、没有切换实时网页。新版还需拆桨实物验收。\n控制行为、硬件适配差异见该目录的说明.txt 和 CONTROL_CONTRACT.txt。\n',encoding='utf8')
print(json.dumps(selection,indent=2),flush=True)
