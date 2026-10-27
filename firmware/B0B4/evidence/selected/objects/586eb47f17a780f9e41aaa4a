"""Bound actual v17/v18 component simulations; each attempt is immutable."""
from pathlib import Path
import datetime, hashlib, json, os, re, subprocess, sys, time
O=Path(__file__).resolve().parent;R=O.parents[3]
OLD=R/'out/z_aw_fix_20261026/compact_aw_v17/canonical/source'
NEW=R/'out/z_aw_fix_20261026/compact_aw_v18/canonical/source'
P=O/'vy_proofs';D=P/(sys.argv[1] if len(sys.argv)>1 else 'attempt01')
assert not D.exists();D.mkdir(parents=True);(D/'tmp').mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
utc=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
record=read(O/'VY_SOURCE_CHANGES.json');before=record['baseline_source55'];expected=record['source55']
assert len(before)==len(expected)==55
assert all(sha(OLD/n)==h for n,h in before.items()) and all(sha(NEW/n)==h for n,h in expected.items())
assert sorted(n for n in expected if expected[n]!=before[n])==record['changed_files']
assert sha(O/'source_changes.diff')==record['source_changes_diff_sha256']
IV=R.parents[1]/'.tools/iverilog/app/bin/iverilog.exe';VVP=IV.with_name('vvp.exe')
assert IV.is_file() and VVP.is_file()
for tag,root in [('old',OLD),('new',NEW)]:
    s=(root/'sensor/mtf01p_reader.v').read_text(encoding='utf8')
    for name in ['mtf_uart_rx','micolink_parser','mtf_metric_observer','mtf01p_reader']:
        assert len(re.findall(r'\bmodule\s+'+name+r'\b',s))==1
        s=re.sub(r'\b'+name+r'\b',tag+'_'+name,s)
    (D/(tag+'_reader.v')).write_text(s,encoding='utf8',newline='')
    s=(root/'sensor/mtf_shared_geometry.v').read_text(encoding='utf8')
    assert len(re.findall(r'\bmodule\s+mtf_shared_geometry\b',s))==1
    (D/(tag+'_geometry.v')).write_text(re.sub(r'\bmtf_shared_geometry\b',tag+'_mtf_shared_geometry',s),encoding='utf8',newline='')
for name in ['metric_tb.v','uart_reader_tb.v','geometry_tb.v']:
    (D/name).write_bytes((O/name).read_bytes())
bound={str(p):sha(p) for p in [Path(__file__),O/'metric_tb.v',O/'uart_reader_tb.v',O/'geometry_tb.v',O/'make_geometry_tb.py',O/'prepare_vy_source.py',O/'VY_SOURCE_CHANGES.json',O/'source_changes.diff',IV,VVP]}
bound.update({str(p):sha(p) for p in D.glob('*.v')})
inputs=dict(started_utc=utc(),baseline_source55=before,source55=expected,bound_files=bound,
    scope='Actual complete old/new metric observer, actual UART reader both diagnostic modes, old/prechecked/default complete geometry with independent real math services. Top13/FSM and reused controller/ground bindings are performed separately by root. No synthesis/physical/hardware claim.',
    arithmetic_oracle='Independent full-distance signed64 products, known-input qualification; exact published signed32 range invariant also checked for four-state payload/controls.',no_DUT_force_or_preload=True)
(D/'inputs.json').write_text(json.dumps(inputs,indent=2)+'\n',encoding='utf8')
env=dict(os.environ);env.update(TMP=str(D/'tmp'),TEMP=str(D/'tmp'),TMPDIR=str(D/'tmp'))
stages=[]
def run(name,command,timeout=180):
    a=dict(command=command,cwd=str(D),started_utc=utc(),parent_pid=os.getpid());start=time.monotonic()
    with (D/(name+'.stdout.log')).open('wb') as out,(D/(name+'.stderr.log')).open('wb') as err:
        child=subprocess.Popen(command,cwd=D,env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
        a['pid']=child.pid;(D/(name+'_process.json')).write_text(json.dumps(a,indent=2)+'\n',encoding='utf8')
        try:code=child.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            child.terminate();code=child.wait();a['terminated_after_timeout']=True
    a.update(actual_child_p_wait=code,normal_wait_return=True,elapsed_seconds=time.monotonic()-start,ended_utc=utc(),
        stdout_sha256=sha(D/(name+'.stdout.log')),stderr_sha256=sha(D/(name+'.stderr.log')))
    (D/(name+'_exit.json')).write_text(json.dumps(a,indent=2)+'\n',encoding='utf8');stages.append(a)
    print(json.dumps(dict(stage=name,actual_child_p_wait=code,elapsed_seconds=a['elapsed_seconds'])),flush=True)
    assert code==0 and not a.get('terminated_after_timeout'),(name,code,(D/(name+'.stderr.log')).read_text(errors='replace'),(D/(name+'.stdout.log')).read_text(errors='replace'))
    return (D/(name+'.stdout.log')).read_text(encoding='utf8',errors='replace')
reader=[str(D/'old_reader.v'),str(D/'new_reader.v')]
run('metric_compile',[str(IV),'-g2012','-s','metric_tb','-o',str(D/'metric.vvp'),*reader,str(D/'metric_tb.v')])
metric=run('metric_vvp',[str(VVP),str(D/'metric.vvp')]);assert 'PASS metric ' in metric
uart=[]
for mode in [0,1]:
    exe=D/f'uart_mode{mode}.vvp';name=f'uart_mode{mode}'
    run(name+'_compile',[str(IV),'-g2012','-s','uart_reader_tb','-P',f'uart_reader_tb.MODE={mode}','-o',str(exe),*reader,str(D/'uart_reader_tb.v')])
    log=run(name+'_vvp',[str(VVP),str(exe)]);assert f'PASS UART MODE={mode} ' in log;uart.append(log)
run('geometry_compile',[str(IV),'-g2012','-s','geometry_tb','-o',str(D/'geometry.vvp'),str(D/'old_geometry.v'),str(D/'new_geometry.v'),str(NEW/'sensor/mtf_native_geometry.v'),str(NEW/'position/position_math.v'),str(NEW/'nav_math_service.v'),str(D/'geometry_tb.v')])
geometry=run('geometry_vvp',[str(VVP),str(D/'geometry.vvp')]);assert 'PASS geometry ' in geometry
assert all(sha(Path(p))==h for p,h in bound.items())
assert all(sha(OLD/n)==h for n,h in before.items()) and all(sha(NEW/n)==h for n,h in expected.items())
result=dict(passed=True,finished_utc=utc(),attempt_directory=str(D),baseline_source55=before,source55=expected,
    inputs_sha256=sha(D/'inputs.json'),stages=stages,
    metric_pass_lines=[x for x in metric.splitlines() if x.startswith('PASS ')],
    uart_pass_lines=[x for log in uart for x in log.splitlines() if x.startswith('PASS ')],
    geometry_pass_lines=[x for x in geometry.splitlines() if x.startswith('PASS ')],
    fixtures_tools_sources_unchanged=True,no_DUT_force_or_preload=True,
    scope=inputs['scope'])
(D/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
assert not (P/'RESULT.json').exists()
(P/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(passed=True,attempt=str(D),metric=metric.strip(),UART=[s.strip() for s in uart],geometry=geometry.strip())),flush=True)
