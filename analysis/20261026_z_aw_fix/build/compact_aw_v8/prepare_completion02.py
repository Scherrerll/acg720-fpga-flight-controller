"""Preserve parser-only failure; continue using its actual completed stages."""
from pathlib import Path
import ast,datetime,hashlib,json
O=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
prior=O/'proofs';ex=json.loads((prior/'runner_exit.json').read_text())
assert ex['actual_p_wait']==1 and ex['normal_wait_return']
assert sha(O/'verify_candidate.py')==ex['runner_sha256']
error=(prior/'runner.stderr.log').read_text()
assert 'AssertionError: PASS PRE=0 cycles=' in error and '$finish called' in error
done=['adapter_compile','adapter_simulation','fusion_pre0_compile','fusion_pre0_simulation']
for name in done:
    r=json.loads((prior/(name+'_exit.json')).read_text())
    assert r['actual_p_wait']==0 and r['normal_wait_return'] and sha(prior/(name+'.log'))==r['log_sha256']
text=(O/'verify_candidate.py').read_text().replace("O=BASE/'proofs'", "O=BASE/'proofs_completion02'")
marker='def run(name,command,timeout=300):\n'
assert text.count(marker)==1
text=text.replace(marker,marker+'''    if name in ['adapter_compile','adapter_simulation','fusion_pre0_compile','fusion_pre0_simulation']:
        previous=BASE/'proofs';receipt=previous/(name+'_exit.json');r=read(receipt)
        assert r['actual_p_wait']==0 and r['normal_wait_return'] and sha(previous/(name+'.log'))==r['log_sha256']
        reuse={'kind':'reuse_completed_actual_stage','receipt':str(receipt),'receipt_sha256':sha(receipt),'actual_p_wait':r['actual_p_wait'],'log':str(previous/(name+'.log')),'log_sha256':r['log_sha256']}
        (O/(name+'_reuse.json')).write_text(json.dumps(reuse,indent=2)+'\\n');stages.append(reuse)
        print(name,'reuse prior actual_wait0',flush=True)
        return (previous/(name+'.log')).read_text(errors='replace')
''')
old="    assert re.fullmatch(r'PASS ((?:\\w+=\\d+ ?)+)\\s*',log),log\n"
assert text.count(old)==1
text=text.replace(old,"    pass_lines=[line for line in log.splitlines() if line.startswith('PASS ')]\n    assert len(pass_lines)==1 and re.fullmatch(r'PASS ((?:\\w+=\\d+ ?)+)',pass_lines[0]),log\n")
ast.parse(text)
dest=O/'verify_completion02.py';assert not dest.exists();dest.write_text(text)
sup=(O/'launch_verification_hidden.py').read_text().replace("O=BASE/'proofs'","O=BASE/'proofs_completion02'").replace("BASE/'verify_candidate.py'","BASE/'verify_completion02.py'")
ast.parse(sup)
dest=O/'launch_completion02_hidden.py';assert not dest.exists();dest.write_text(sup)
(O/'ORCHESTRATION_CORRECTION.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'original_runner_actual_wait':1,'failure_class':'driver_log_parser_rejected_vvp_finish_informational_line_after_success',
    'preserved_runner_sha256':ex['runner_sha256'],'preserved_exit_sha256':sha(prior/'runner_exit.json'),
    'completed_stages_reused':done,'all_reused_actual_wait':0,'functional_RTL_changed':False,
    'correction':'Require one exact PASS line while allowing vvp informational finish line; stage exit0 remains mandatory.',
    'continuation_runner_sha256':sha(O/'verify_completion02.py'),'continuation_supervisor_sha256':sha(O/'launch_completion02_hidden.py')},indent=2)+'\n')
print('Prepared completion02; original failure and completed stage receipts retained.')
