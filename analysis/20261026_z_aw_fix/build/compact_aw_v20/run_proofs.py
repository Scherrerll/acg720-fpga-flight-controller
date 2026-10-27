"""Fresh full original top13 and ordinary-input merged-guard integration; no vendor."""
from pathlib import Path
import datetime,hashlib,json,os,re,subprocess,sys,xml.etree.ElementTree as ET
from validation_contract import verify_contract
O=Path(__file__).resolve().parent;R=O.parents[3];D=O/'proofs';S=R/'out/z_aw_fix_20261026/compact_aw_v20/canonical/source'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
write=lambda p,j:p.write_text(json.dumps(j,indent=2)+'\n',encoding='utf8',newline='\n')
utc=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
contract=verify_contract();expected=contract['source55']
assert D.is_dir() and not (D/'inputs.json').exists() and not (O/'PROOF_BINDING.json').exists()
T=D/'top13';T.mkdir();(D/'tmp').mkdir()
parent=O.parent/'compact_aw_v19/az_proofs/run_top13.py';raw=parent.read_bytes();assert raw.count(b'compact_aw_v19/canonical')==1
driver=T/'run_top13.py';driver.write_bytes(raw.replace(b'compact_aw_v19/canonical',b'compact_aw_v20/canonical'))
tb=O/'guard_integration_tb.v';assert not re.search(r'\bforce\b',tb.read_text(encoding='utf8'))
IV=R.parents[1]/'.tools/iverilog/app/bin/iverilog.exe';VVP=IV.with_name('vvp.exe');primitive=Path('C:/Gowin/Gowin_V1.9.12.04_x64/IDE/simlib/gw5a/prim_sim.v')
bound_files=[Path(__file__),O/'validation_contract.py',O/'source_freeze.json',O/'source_review.md',O/'SOURCE_EQUIVALENCE_BASIS.json',O/'SOURCE_COMPOSITION.json',O/'COMPONENT_REUSE_BINDING.json',parent,driver,tb,O.parent/'v4_release_proofs/top_safety_tb.v',R/'firmware/B0B4/xy_pi_cli.py',IV,VVP,primitive]
bound={str(p):sha(p) for p in bound_files}
write(D/'inputs.json',{'source55':expected,'bound_inputs':bound,'scope':'Fresh exact full-top13 controlled-force fixture plus actual AZ/metric producers and merged/default navigation gates driven only through ordinary module inputs; parent component/core evidence rehashed separately'})
env=dict(os.environ,TMP=str(D/'tmp'),TEMP=str(D/'tmp'),TMPDIR=str(D/'tmp'))
exits=[]
def run(name,command,timeout=240):
    assert not (D/f'{name}_exit.json').exists()
    j={'command':command,'cwd':str(R),'started_utc':utc()}
    with (D/f'{name}.stdout.log').open('wb') as out,(D/f'{name}.stderr.log').open('wb') as err:
        p=subprocess.Popen(command,cwd=R,stdin=subprocess.DEVNULL,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
        j['pid']=p.pid;write(D/f'{name}_process.json',j)
        try:code=p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:p.terminate();code=p.wait();j['terminated_after_timeout']=True
    j.update(actual_p_wait=code,normal_wait_return=True,ended_utc=utc(),stdout_sha256=sha(D/f'{name}.stdout.log'),stderr_sha256=sha(D/f'{name}.stderr.log'))
    path=D/f'{name}_exit.json';write(path,j);exits.append({'path':str(path),'sha256':sha(path),'actual_wait_field':'actual_p_wait','normal_field':'normal_wait_return'})
    print(json.dumps({'stage':name,'actual_p_wait':code}),flush=True)
    assert code==0 and not j.get('terminated_after_timeout'),(name,code)
    return j
top=run('top13_runner',[sys.executable,'-B','-X','utf8',str(driver)])
result=read(T/'top_safety_results.json');assert result['passed'] and result['cases']==13
assert sha(T/'top_safety_tb.v')==sha(O.parent/'v4_release_proofs/top_safety_tb.v')
for name in ['compile','vvp']:
    path=T/f'{name}_exit.json';j=read(path);assert j['normal_return'] and j['actual_completedprocess_returncode']==0
    exits.append({'path':str(path),'sha256':sha(path),'actual_wait_field':'actual_completedprocess_returncode','normal_field':'normal_return'})
files=[S/f.attrib['path'] for f in ET.parse(S/'acg720_ano_port.gprj').findall('.//File') if f.attrib.get('type')=='file.verilog' and f.attrib.get('enable')=='1']
run('integration_compile',[str(IV),'-g2012','-s','guard_integration_tb','-I',str(S),'-o',str(D/'integration.vvp'),str(tb),*map(str,files),str(primitive)])
run('integration_vvp',[str(VVP),str(D/'integration.vvp')])
log=(D/'integration_vvp.stdout.log').read_text(encoding='utf8');lines=[line for line in log.splitlines() if line.startswith('PASS combined_guard ')]
assert len(lines)==1 and 'combinations=1111' in lines[0] and 'default_wrong_flags_ignored=1' in lines[0]
assert all(sha(Path(p))==h for p,h in bound.items()) and {n:sha(S/n) for n in expected}==expected
assert verify_contract()['passed']
write(D/'RESULT.json',{'passed':True,'source55':expected,'inputs_sha256':sha(D/'inputs.json'),'fresh_actual_exit_receipts':exits,
    'fresh_top13':{'passed':True,'cases':13,'actual_root_wait':top['actual_p_wait'],'original_v4_TB_byte_exact':True,'top_TB_sha256':sha(T/'top_safety_tb.v'),'controlled_private_forces':result['scope'],'result_sha256':sha(T/'top_safety_results.json')},
    'fresh_integration':{'passed':True,'pass_line':lines[0],'no_DUT_force_or_preload':True,'scope':'Actual independent AZ adapter + metric producer and merged navigation consumers, all four predicate combinations, deliberately wrong flags on default callers, reset/cancel/busy-fault/link-loss hold/full32 invalid distance. It checks tuple and consumer-gate composition, not unforced full-flight or physical timing.'},
    'guard_binding_sha256':contract['guard_binding_sha256'],'new_private_same_publication_predicate_bits':2,'legacy_public_output_cycle_change':0,'core_FSM_rerun':False})
print(json.dumps({'passed':True,'fresh_top13':13,'integration':lines[0],'core_FSM_rerun':False}),flush=True)
