"""Retain failed attempt01 and reuse its successful new top13; fix fixture keyword only."""
from pathlib import Path
import datetime,hashlib,json,shutil
O=Path(__file__).resolve().parent;D=O/'proofs'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
assert not (O/'PROOF_BINDING.json').exists() and not (O/'proofs_retry02').exists()
root=read(D/'functional_runner_exit.json');top=read(D/'top13_runner_exit.json');bad=read(D/'integration_compile_exit.json')
assert root['actual_p_wait']==bad['actual_p_wait']==1 and top['actual_p_wait']==0
assert all(j['normal_wait_return'] for j in [root,top,bad])
snapshots={}
for name in ['guard_integration_tb.v','validation_contract.py']:
    source=O/name;saved=D/(source.stem+'_attempt01'+source.suffix);assert not saved.exists();shutil.copyfile(source,saved)
    snapshots[str(source)]={'preserved_path':str(saved),'sha256':sha(saved)}
tb=(O/'guard_integration_tb.v').read_text(encoding='utf8')
assert tb.count('input [31:0] dist;')==1 and tb.count('distance=dist;')==1
tb=tb.replace('input [31:0] dist;','input [31:0] distance_value;').replace('distance=dist;','distance=distance_value;')
(O/'guard_integration_tb.v').write_text(tb,encoding='utf8',newline='\n')
text=(O/'validation_contract.py').read_text(encoding='utf8')
def one(s,a,b):assert s.count(a)==1,(a,s.count(a));return s.replace(a,b,1)
text=one(text,"D=O/'proofs';root=read(D/'functional_runner_exit.json')","D=Path(p['proof_directory']);assert D.resolve().is_relative_to(O.resolve());root=read(D/'functional_runner_exit.json')")
text=one(text,"assert sha(D/'top13/top_safety_tb.v')==sha(O.parent/'v4_release_proofs/top_safety_tb.v')","T=Path(p['fresh_top13']['directory']);assert T.resolve().is_relative_to(O.resolve())\n        assert sha(T/'top_safety_tb.v')==sha(O.parent/'v4_release_proofs/top_safety_tb.v')")
text=one(text,"top_root=read(D/'top13_runner_exit.json')\n        for stream in ['stdout','stderr']:assert sha(D/f'top13_runner.{stream}.log')==top_root[f'{stream}_sha256']","top_path=Path(p['fresh_top13']['root_exit_path']);top_root=read(top_path)\n        for stream in ['stdout','stderr']:assert sha(top_path.parent/f'top13_runner.{stream}.log')==top_root[f'{stream}_sha256']")
(O/'validation_contract.py').write_text(text,encoding='utf8',newline='\n')

text=(O/'run_proofs.py').read_text(encoding='utf8')
text=one(text,"D=O/'proofs'","D=O/'proofs_retry02'")
text=one(text,"T=D/'top13';T.mkdir();(D/'tmp').mkdir()","T=O/'proofs/top13';(D/'tmp').mkdir()")
text=one(text,"driver=T/'run_top13.py';driver.write_bytes(raw.replace(b'compact_aw_v19/canonical',b'compact_aw_v20/canonical'))","driver=T/'run_top13.py';assert driver.read_bytes()==raw.replace(b'compact_aw_v19/canonical',b'compact_aw_v20/canonical')")
text=one(text,"bound_files=[Path(__file__),","bound_files=[Path(__file__),O/'FUNCTIONAL_CORRECTION_02.json',")
text=one(text,"top=run('top13_runner',[sys.executable,'-B','-X','utf8',str(driver)])","top_path=O/'proofs/top13_runner_exit.json';top=read(top_path);assert top['actual_p_wait']==0 and top['normal_wait_return']\nexits.append({'path':str(top_path),'sha256':sha(top_path),'actual_wait_field':'actual_p_wait','normal_field':'normal_wait_return'})\nprint(json.dumps({'top13_reused_from_actual_attempt01_root0':True,'new_top13_runs_in_retry':0}),flush=True)")
text=one(text,"'fresh_top13':{'passed':True,","'proof_directory':str(D),'fresh_top13':{'directory':str(T),'root_exit_path':str(top_path),'candidate_top13_total_actual_runs':1,'reused_in_retry_after_exact_hash_check':True,'passed':True,")
(O/'run_proofs_retry02.py').write_text(text,encoding='utf8',newline='\n')
text=(O/'launch_functional_hidden.py').read_text(encoding='utf8')
text=one(text,"D=O/'proofs'","D=O/'proofs_retry02'")
text=one(text,"runner=O/'run_proofs.py'","runner=O/'run_proofs_retry02.py'")
text=one(text,"'functional_root_exit_sha256':sha(D/'functional_runner_exit.json')","'proof_directory':str(D),'historical_failed_functional_root':{'path':str(O/'proofs/functional_runner_exit.json'),'sha256':sha(O/'proofs/functional_runner_exit.json'),'actual_p_wait':read(O/'proofs/functional_runner_exit.json')['actual_p_wait']},'functional_root_exit_sha256':sha(D/'functional_runner_exit.json')")
(O/'launch_functional_retry02_hidden.py').write_text(text,encoding='utf8',newline='\n')
record={'prepared_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Fixture-only retry; no candidate source edit and no second top13 run',
    'original_root':{'path':str(D/'functional_runner_exit.json'),'sha256':sha(D/'functional_runner_exit.json'),'actual_p_wait':root['actual_p_wait']},
    'original_compile_failure':{'path':str(D/'integration_compile_exit.json'),'sha256':sha(D/'integration_compile_exit.json'),'actual_p_wait':bad['actual_p_wait'],'stderr_sha256':sha(D/'integration_compile.stderr.log')},
    'successful_new_v20_top13':{'path':str(D/'top13_runner_exit.json'),'sha256':sha(D/'top13_runner_exit.json'),'actual_p_wait':top['actual_p_wait'],'original_v4_TB_byte_exact':sha(D/'top13/top_safety_tb.v')==sha(O.parent/'v4_release_proofs/top_safety_tb.v')},
    'error':'SystemVerilog keyword dist used as task formal name in integration testbench',
    'fixture_fix':'Rename that formal to distance_value and its single reference, without changing assertions/stimulus or source55',
    'changed_original_input_snapshots':snapshots,'candidate_source55_unchanged':read(D/'inputs.json')['source55'],
    'new_scripts':{n:sha(O/n) for n in ['run_proofs_retry02.py','launch_functional_retry02_hidden.py','validation_contract.py','guard_integration_tb.v']}}
dest=O/'FUNCTIONAL_CORRECTION_02.json';assert not dest.exists();dest.write_text(json.dumps(record,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps({'retry02_prepared':True,'original_functional_root_wait':1,'original_new_top13_root_wait':0,'candidate_top13_actual_runs':1,'source55_changed':False}))
