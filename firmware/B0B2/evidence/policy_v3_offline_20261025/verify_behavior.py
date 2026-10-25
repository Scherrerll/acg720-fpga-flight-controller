from pathlib import Path
import hashlib,json,os,subprocess
ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'candidate'
SIDE=ROOT.parent/'side_imu_timeout_removal_20261025'
ALIGN=ROOT.parent/'side_timeout_alignment_20261025'
IV=ROOT.parent/'.tools/iverilog/app/bin/iverilog.exe'
TEMP=ROOT/'tmp';TEMP.mkdir(exist_ok=True)
env=dict(os.environ,TMP=str(TEMP),TEMP=str(TEMP),TMPDIR=str(TEMP))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
hashes={p.relative_to(SOURCE).as_posix():sha(p)for p in SOURCE.rglob('*')if p.is_file()}
results={}
def run(label,bench,sources):
    product=TEMP/(label+'.vvp');commands=[]
    for argv in ([IV,'-g2012','-I',SOURCE,'-s',label,'-o',product,bench,*sources],[IV.with_name('vvp.exe'),'-n',product]):
        r=subprocess.run(list(map(str,argv)),capture_output=True,text=True,env=env,timeout=240)
        commands.append(dict(argv=list(map(str,argv)),returncode=r.returncode,stdout=r.stdout,stderr=r.stderr))
        (ROOT/(label+'_commands.json')).write_text(json.dumps(commands,indent=2)+'\n')
        (ROOT/(label+'.log')).write_text('\n'.join(c['stdout']+c['stderr']for c in commands),encoding='utf-8')
        r.check_returncode()
    expected='timeout_alignment'if label=='timeout_boundaries'else label
    assert 'PASS '+expected in commands[-1]['stdout'],commands[-1]['stdout']
    results[label]=dict(passed=True,commands_sha256=sha(ROOT/(label+'_commands.json')),log_sha256=sha(ROOT/(label+'.log')))
    (ROOT/'behavior_progress.json').write_text(json.dumps(results,indent=2)+'\n')
    print(commands[-1]['stdout'].strip(),flush=True)
baseline=ROOT/'baseline_simulation';baseline.mkdir(exist_ok=True)
for name in ['bmi088_reader_baseline.v','imu_checked_guard_baseline.v']:(baseline/name).write_bytes((SIDE/name).read_bytes())
text=(SIDE/'imu_pipeline_baseline.v').read_text().replace('bmi088_reader reader','bmi088_reader_baseline reader').replace('imu_temporal_check #','imu_temporal_check_baseline #')
(baseline/'imu_pipeline_baseline.v').write_text(text)
text=(ROOT.parent/'routing_closure_20261025/best176_pose_prechecked_v4/fixture/core/imu_temporal_check_pipelined.v').read_text().replace('module imu_temporal_check #','module imu_temporal_check_baseline #')
(baseline/'imu_temporal_check_baseline.v').write_text(text)
sources=sorted(SOURCE.rglob('*.v'))+sorted(baseline.glob('*.v'))
run('reader_policy',SIDE/'reader_policy.v',sources)
run('pipeline_policy',SIDE/'pipeline_policy.v',sources)
run('timeout_boundaries',ALIGN/'timeout_boundaries.v',[SOURCE/'core/rc_ppm.v',SOURCE/'sensor/mtf01p_reader.v'])
run('policy_boundaries',ROOT/'policy_boundaries.v',sorted(SOURCE.rglob('*.v')))
run('range_geometry_policy',ROOT/'range_geometry_policy.v',sorted(SOURCE.rglob('*.v'))+[ROOT/'legacy_geometry_before_removal.v'])
for name,h in hashes.items():assert sha(SOURCE/name)==h,name
result=dict(passed=True,tests=results,source_sha256=hashes,hardware_accessed=False,old_equivalence_proofs_reused=False,scope='Actual RTL behavior tests for confirmed intentional change, not flight verification')
(ROOT/'behavior_verification.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS confirmed policy behavior and retained independent limits',flush=True)
