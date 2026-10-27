"""Fresh exact top13 with real child waits; no vendor build or hardware access."""
from pathlib import Path
import datetime,hashlib,json,subprocess,sys

O=Path(__file__).resolve().parent;R=O.parents[3];D=O/'az_proofs'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
utc=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
write=lambda p,j:p.write_text(json.dumps(j,indent=2,ensure_ascii=False)+'\n',encoding='utf8',newline='\n')
composition=read(O/'AZ_SOURCE_COMPOSITION.json');S=Path(composition['source_root']);expected=composition['source55']
assert {p:sha(S/p) for p in expected}==expected
assert not D.exists();D.mkdir()
parent=O.parent/'compact_aw_v17/proofs/run_top13.py'
original=parent.read_bytes();old=b'compact_aw_v17/canonical';new=b'compact_aw_v19/canonical'
assert original.count(old)==1
driver=D/'run_top13.py';driver.write_bytes(original.replace(old,new))
original_tb=O.parent/'v4_release_proofs/top_safety_tb.v'
assert sha(original_tb)==sha(O.parent/'compact_aw_v17/proofs/top_safety_tb.v')
tools=Path('C:/Users/ScherrerL/Desktop/apple/.tools/iverilog/app/bin')
primitive=Path('C:/Gowin/Gowin_V1.9.12.04_x64/IDE/simlib/gw5a/prim_sim.v')
bound={str(p):sha(p) for p in [Path(__file__),O/'AZ_SOURCE_COMPOSITION.json',O/'GUARD_REUSE_RECHECK.json',parent,driver,original_tb,R/'firmware/B0B4/xy_pi_cli.py',tools/'iverilog.exe',tools/'vvp.exe',primitive]}
write(D/'inputs.json',{'source55':expected,'bound_files':bound,'driver_derivation':'Exact parent v17 bytes, only compact_aw_v17/canonical -> compact_aw_v19/canonical changed once',
    'scope':'Original controlled-force top13; fresh combined source compile/simulation, no standalone unforced full-flight claim'})
command=[sys.executable,'-B','-X','utf8',str(driver)]
receipt={'command':command,'cwd':str(R),'started_utc':utc(),'runner_sha256':sha(driver),'supervisor_sha256':sha(Path(__file__)),'create_no_window':True,'stdin':'DEVNULL'}
with (D/'runner.stdout.log').open('wb') as output,(D/'runner.stderr.log').open('wb') as errors:
    p=subprocess.Popen(command,cwd=R,stdin=subprocess.DEVNULL,stdout=output,stderr=errors,creationflags=0x08000000)
    receipt['pid']=p.pid;write(D/'runner_process.json',receipt)
    code=p.wait()
receipt.update(actual_p_wait=code,normal_wait_return=True,ended_utc=utc(),stdout_sha256=sha(D/'runner.stdout.log'),stderr_sha256=sha(D/'runner.stderr.log'))
write(D/'runner_exit.json',receipt)
try:
    assert code==0,('top13 root failed',code)
    compile_exit=read(D/'compile_exit.json');vvp_exit=read(D/'vvp_exit.json');top=read(D/'top_safety_results.json')
    assert all(j['actual_completedprocess_returncode']==0 and j['normal_return'] for j in [compile_exit,vvp_exit])
    assert top['passed'] and top['cases']==13
    assert sha(D/'top_safety_tb.v')==sha(original_tb),'original top13 TB bytes changed'
    assert driver.read_bytes()==original.replace(old,new),'path-only driver derivation changed'
    assert {p:sha(S/p) for p in expected}==expected,'candidate source changed during top13'
    for parent_info in composition['parents'].values():
        root=Path(parent_info['root']);assert {rel:sha(root/rel) for rel in parent_info['source55']}==parent_info['source55']
    reuse=read(O/'GUARD_REUSE_RECHECK.json')
    for item in reuse['actual_producer_fusion_stages']:
        assert sha(Path(item['receipt_path']))==item['receipt_sha256'] and sha(Path(item['log_path']))==item['log_sha256']
    assert sha(Path(reuse['v8_results_path']))==reuse['v8_results_sha256']
    assert sha(Path(reuse['v9_results_path']))==reuse['v9_results_sha256']
    actual_top={'passed':True,'cases':13,'actual_root_p_wait':code,'compile_actual_returncode':compile_exit['actual_completedprocess_returncode'],
        'vvp_actual_returncode':vvp_exit['actual_completedprocess_returncode'],'original_v4_tb_byte_exact':True,'top_tb_sha256':sha(D/'top_safety_tb.v'),
        'driver_path_label_only':True,'scope':top['scope'],'receipts':{str(D/f):sha(D/f) for f in ['runner_exit.json','compile_exit.json','vvp_exit.json','top_safety_results.json','top_safety.compile.log','top_safety.log','inputs.json']}}
    write(O/'RESULT.json',{'passed':True,'completed_utc':utc(),'source55':expected,'source55_unchanged':True,'all_parent_source55_unchanged':True,
        'composition_path':str(O/'AZ_SOURCE_COMPOSITION.json'),'composition_sha256':sha(O/'AZ_SOURCE_COMPOSITION.json'),
        'guard_reuse_bindings':{'path':str(O/'GUARD_REUSE_RECHECK.json'),'sha256':sha(O/'GUARD_REUSE_RECHECK.json'),'v8_results_sha256':reuse['v8_results_sha256'],'v9_results_sha256':reuse['v9_results_sha256'],'roots':reuse['roots'],'scope':reuse['scope']},
        'top13':actual_top,'scope':'Exact guard composition plus fresh original top13 only. Main owns final source freeze, combined core/FSM review, SYN and full real50MHz physical qualification. DO_NOT_PROGRAM.'})
    print(json.dumps({'passed':True,'source_files':55,'fresh_top13':13,'root_actual_p_wait':code,'compile_actual_returncode':0,'vvp_actual_returncode':0,'original_v4_tb_byte_exact':True,'result_sha256':sha(O/'RESULT.json')}))
except BaseException as e:
    write(O/'AZ_PROOF_FAILURE.json',{'failed_utc':utc(),'type':type(e).__name__,'error':str(e),'actual_root_p_wait':code,'source55':{rel:sha(S/rel) for rel in expected},'scope':'Failure retained; no source modified by proof supervisor'})
    raise
