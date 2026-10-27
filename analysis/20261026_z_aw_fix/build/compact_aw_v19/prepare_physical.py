"""Prepare one dormant exact-v19 P3/R0 physical recipe from strict v18 templates."""
from pathlib import Path
import ast,datetime,difflib,hashlib,json,subprocess,sys
from validation_contract import verify_contract

O=Path(__file__).resolve().parent;R=O.parents[3];P=O.parent/'compact_aw_v18'
ROOT=R/'out/z_aw_fix_20261026/compact_aw_v19';PROFILE='physical_p3r0_01'
VG='72808bc54f1a2b6c199a109cfa6f71e35139508d1573f10abba2bcd2774ae7af'
OLDVG='64e76270fe35298e698bfe5b14b9d9e267469f746d3c2382a8a15284c5942d4f'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
write=lambda p,j:p.write_text(json.dumps(j,indent=2,ensure_ascii=False)+'\n',encoding='utf8',newline='\n')
contract=verify_contract(check_proof=True);syn=read(O/'SYNTHESIS_RESULT.json')
assert syn['passed_SYN_only'] and syn['source55']==contract['source55'] and syn['netlist_sha256']==VG
assert syn['vendor_actual_wait']==syn['runner_actual_wait']==syn['audit_actual_wait']==0
assert not (ROOT/PROFILE).exists() and not (O/PROFILE).exists()
names=['run_physical.py','launch_physical_hidden.py','seal_terminal.py','independent_raw_review.py','physical_snapshot.py','preflight_physical_recipe.py']
assert not any((O/n).exists() for n in names) and not (O/'PHYSICAL_PREPARATION.json').exists()
parents={n:sha(P/n) for n in names}
def one(s,a,b):
    assert s.count(a)==1,(a,s.count(a));return s.replace(a,b,1)

text=(P/'run_physical.py').read_text(encoding='utf8').replace('compact_aw_v18','compact_aw_v19').replace(OLDVG,VG)
text=text.replace("sys.argv[1] in ['2','3']","sys.argv[1] in ['3']")
text=one(text,"ATTEMPT=ROOT/f'physical_p{PLACE}r0_01'","ATTEMPT=ROOT/'physical_p3r0_01'")
text=one(text,"    assert not ATTEMPT.exists(),'Never overwrite physical evidence'","    from validation_contract import verify_contract\n    functional_contract=verify_contract(check_proof=True)\n    assert PLACE==3\n    assert not ATTEMPT.exists(),'Never overwrite physical evidence'")
text=one(text,"    din=json.loads((DONOR/'verification/build_input.json').read_text());","    proof=json.loads((O/'PROOF_BINDING.json').read_text(encoding='utf8'))\n    assert proof['passed'] and proof['source55']==expected and proof['guard_binding_sha256']==functional_contract['guard_binding_sha256']\n    syn_result=json.loads((O/'SYNTHESIS_RESULT.json').read_text(encoding='utf8'));syn_root=json.loads((O/'runner_exit.json').read_text(encoding='utf8'))\n    assert syn_result['passed_SYN_only'] and syn_result['source55']==expected and syn_result['netlist_sha256']==VG_SHA\n    assert syn_result['vendor_actual_wait']==syn_result['runner_actual_wait']==syn_result['audit_actual_wait']==0\n    assert syn_root['normal_wait_return'] and syn_root['actual_p_wait']==0\n    din=json.loads((DONOR/'verification/build_input.json').read_text());")
text=one(text,"evidence += [DONOR/'synthesis_freeze_manifest_final.json',donor_vg,O/'source_freeze.json']","evidence += [DONOR/'synthesis_freeze_manifest_final.json',donor_vg,O/'source_freeze.json']\n    evidence += [O/n for n in ['SYNTHESIS_RESULT.json','runner_exit.json','PROOF_BINDING.json','REUSED_BINDINGS_RECHECK.json','GUARD_REUSE_RECHECK.json','validation_contract.py','SOURCE_EQUIVALENCE_BASIS.json','source_review.md','AZ_SOURCE_COMPOSITION.json','RESULT.json','PHYSICAL_PREPARATION.json','PHYSICAL_TCL_PREFLIGHT.json']]\n    evidence += [O/'az_proofs'/n for n in ['runner_exit.json','compile_exit.json','vvp_exit.json','inputs.json','top_safety_results.json','top_safety_tb.v']]\n    evidence += [O/'proofs'/n for n in ['functional_runner_exit.json','fsm_compile_exit.json','fsm_vvp_exit.json','inputs.json','CORE_FSM_RESULT.json']]\n    evidence += [DONOR/'verification/audit_exit.json',DONOR/'verification/native_synthesis_audit.json']")
text=one(text,"    tmp=VERIFY/'tmp';","    write('functional_evidence_binding.json',{'passed':True,'schema':'v19 exact AZ guard + fresh coreFSM + earlier fresh exact-v19 top13; no flat-top13 or VY binding invented','proof_binding_sha256':sha(O/'PROOF_BINDING.json'),'guard_binding_sha256':functional_contract['guard_binding_sha256'],'actual_AZ_top13_root_wait':json.loads((O/'az_proofs/runner_exit.json').read_text())['actual_p_wait'],'actual_core_FSM_root_wait':json.loads((O/'proofs/functional_runner_exit.json').read_text())['actual_p_wait'],'new_same_publication_predicate_bits':1,'legacy_output_cycle_change':0,'scope':'Component timing accelerated and top13 controlled-force limitations remain disclosed in original proof bindings; no unforced full-flight or hardware qualification.'})\n    tmp=VERIFY/'tmp';")
text=one(text,"    result=helper.physical_audit(VG_SHA,expected);helper.check_sources(expected)","    result=helper.physical_audit(VG_SHA,expected);helper.check_sources(expected)\n    assert verify_contract(check_proof=True)['passed']")
text=text.replace('Root-authorized fresh v18 map2 v18 P2-or-P3/R0 original full physical gates physical trial','Deferred exact-v19 map2 P3/R0 original full physical gates trial')
text=text.replace('Fresh exact-VG v4 physical-only trial; no synthesis/hardware; source override is v4.','Fresh exact-v19 VG physical-only trial; standard original CST/SDC/logic unchanged; no synthesis/hardware.')
text=text.replace('compact_aw_v4 exact-VG v18 P2-or-P3/R0 original full physical gates full physical gate PASS','compact_aw_v19 exact-VG P3/R0 original full physical gate PASS')
(O/'run_physical.py').write_text(text,encoding='utf8',newline='\n')

for name in ['launch_physical_hidden.py','seal_terminal.py','independent_raw_review.py']:
    text=(P/name).read_text(encoding='utf8').replace('compact_aw_v18','compact_aw_v19').replace(OLDVG,VG)
    text=text.replace("sys.argv[1] in ['2','3']","sys.argv[1] in ['3']")
    if name=='launch_physical_hidden.py':
        text=one(text,"O=BASE/f'physical_p{PLACE}r0_01'","O=BASE/'physical_p3r0_01'")
        text=one(text,"assert O.is_dir() and not receipt.exists() and not exit_receipt.exists(),'Never overwrite runner receipts'","assert O.is_dir() and not any((O/n).exists() for n in ['runner_process.json','runner_exit.json','runner.stdout.log','runner.stderr.log']),'Never overwrite runner receipts or logs'")
        text=text.replace('one authorized v9 physical profile','the single deferred v19 P3/R0 profile')
    elif name=='seal_terminal.py':
        text=one(text,"label=f'physical_p{sys.argv[1]}r0_01'","label='physical_p3r0_01'")
        text=one(text,"expected=read(O/'source_freeze.json')['source55']","from validation_contract import verify_contract\nassert verify_contract(check_proof=True)['passed']\nexpected=read(O/'source_freeze.json')['source55']")
        text=one(text,"'project_serialization_check.json','donor_evidence_binding.json'","'project_serialization_check.json','donor_evidence_binding.json','functional_evidence_binding.json'")
    else:
        text=one(text,"label=f'physical_p{sys.argv[1]}r0_01'","label='physical_p3r0_01'")
        anchor="log=(V/'physical.log').read_text(errors='replace'); files="
        replacement="""proof=read(O/'PROOF_BINDING.json');azroot=read(O/'az_proofs/runner_exit.json');fsmroot=read(O/'proofs/functional_runner_exit.json')
checks['v19_guard_functional_binding']=proof['passed'] and proof['source55']==expected and proof['guard_binding_sha256']==sha(O/'GUARD_REUSE_RECHECK.json')
checks['actual_AZ_top13_and_coreFSM_roots']=azroot['normal_wait_return'] and fsmroot['normal_wait_return'] and azroot['actual_p_wait']==fsmroot['actual_p_wait']==0
checks['actual_AZ_compile_vvp']=all(read(O/'az_proofs'/f'{n}_exit.json')['actual_completedprocess_returncode']==0 and read(O/'az_proofs'/f'{n}_exit.json')['normal_return'] for n in ['compile','vvp'])
checks['actual_coreFSM_compile_vvp']=all(read(O/'proofs'/f'{n}_exit.json')['actual_p_wait']==0 and read(O/'proofs'/f'{n}_exit.json')['normal_wait_return'] for n in ['fsm_compile','fsm_vvp'])
log=(V/'physical.log').read_text(errors='replace'); files="""
        text=one(text,anchor,replacement)
    (O/name).write_text(text,encoding='utf8',newline='\n')

text=(P/'physical_snapshot.py').read_text(encoding='utf8').replace('compact_aw_v18','compact_aw_v19')
text=one(text,"['physical_p3r0_01','physical_p2r0_01']","['physical_p3r0_01']")
(O/'physical_snapshot.py').write_text(text,encoding='utf8',newline='\n')
text=(P/'preflight_physical_recipe.py').read_text(encoding='utf8').replace('compact_aw_v18','compact_aw_v19')
text=one(text,"for place in [2,3]:","for place in [3]:")
text=one(text,"    assert tcl.count('run pnr\\n')==1","    original_options=re.findall(r'^set_option -(\\S+)\\s+(\\S+)\\s*$', '\\n'.join(lines),re.M)\n    effective_options=re.findall(r'^set_option -(\\S+)\\s+(\\S+)\\s*$',tcl,re.M)\n    assert len(dict(original_options))==len(original_options) and len(dict(effective_options))==len(effective_options)\n    assert dict(effective_options)==dict(original_options)\n    assert tcl.count('run pnr\\n')==1")
text=one(text,"'profiles':[2,3]","'profiles':[3]")
(O/'preflight_physical_recipe.py').write_text(text,encoding='utf8',newline='\n')
(O/PROFILE).mkdir()
for name in names:ast.parse((O/name).read_text(encoding='utf8'),filename=str(O/name))
cp=subprocess.run([sys.executable,'-B','-X','utf8',str(O/'preflight_physical_recipe.py')],stdin=subprocess.DEVNULL,capture_output=True,text=True)
(O/'physical_preflight.stdout.log').write_text(cp.stdout,encoding='utf8',newline='\n');(O/'physical_preflight.stderr.log').write_text(cp.stderr,encoding='utf8',newline='\n')
write(O/'PHYSICAL_PREFLIGHT_EXIT.json',{'actual_completedprocess_returncode':cp.returncode,'normal_return':True,'command':cp.args,'stdout_sha256':sha(O/'physical_preflight.stdout.log'),'stderr_sha256':sha(O/'physical_preflight.stderr.log')})
assert cp.returncode==0,(cp.stdout,cp.stderr)
diff=''
for name in names:diff+=''.join(difflib.unified_diff((P/name).read_text(encoding='utf8').splitlines(True),(O/name).read_text(encoding='utf8').splitlines(True),fromfile='v18/'+name,tofile='v19/'+name))
(O/'PHYSICAL_SCRIPT_DERIVATION.diff').write_text(diff,encoding='utf8',newline='\n')
write(O/'PHYSICAL_PREPARATION.json',{'prepared_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Deferred standard single-slot exact-v19 P3/R0 physical-only recipe; no vendor or hardware launch during preparation',
    'profile':PROFILE,'ROOT':str(ROOT),'CANON':str(ROOT/'canonical/source'),'DONOR':str(ROOT/'build_attempt_01'),'ATTEMPT':str(ROOT/PROFILE),'receipt_directory':str(O/PROFILE),
    'source55':contract['source55'],'baseline_source55':contract['baseline_source55'],'B3_relative_change_count':10,
    'VG_sha256':VG,'actual_SYN_vendor_wait':0,'actual_SYN_runner_wait':0,'actual_audit_wait':0,'actual_SYN_result_sha256':sha(O/'SYNTHESIS_RESULT.json'),
    'functional_schema':'Real v19 az_proofs top13, proofs coreFSM, GUARD_REUSE_RECHECK producer/fusion and unchanged-six controller bindings; no invented flat-top13 or VY binding',
    'proof_binding_sha256':sha(O/'PROOF_BINDING.json'),'guard_binding_sha256':contract['guard_binding_sha256'],'reuse_recheck_sha256':sha(O/'REUSED_BINDINGS_RECHECK.json'),
    'actual_AZ_top13_root_exit_sha256':sha(O/'az_proofs/runner_exit.json'),'actual_core_FSM_root_exit_sha256':sha(O/'proofs/functional_runner_exit.json'),
    'parent_scripts_sha256':parents,'new_scripts_sha256':{n:sha(O/n) for n in names},'script_derivation_sha256':sha(O/'PHYSICAL_SCRIPT_DERIVATION.diff'),
    'preflight_actual_returncode':cp.returncode,'physical_Tcl_preflight_sha256':sha(O/'PHYSICAL_TCL_PREFLIGHT.json'),'AST_parse_passed':True,
    'original_helper_sha256':'abb5246c203b73c111f80bc91f8db6c8220463f7d4c5cf48dbfe2167ef49db84',
    'unchanged':'Exact source55, original complete CST and SDC, actual SYN VG; place3/route0/map2/replicate0/route_maxfan23/usercode0000B0B4. No DSP-location or VY changes.',
    'gates':['fullroute','real20ns/50MHz','all5 slacks nonnegative','setup and hold endpoints0','18pins and B4 identity','actual vendor and runner normal waits0'],
    'launch_command':[sys.executable,'-B','-X','utf8',str(O/'launch_physical_hidden.py'),'3'],'vendor_started':False,'runtime_attempt_created':False,'hardware_actions':False})
assert verify_contract(check_proof=True)['passed'] and not (ROOT/PROFILE).exists() and not any((O/PROFILE).iterdir())
assert all(sha(P/n)==h for n,h in parents.items())
print(json.dumps({'physical_prepared':True,'profile':PROFILE,'preflight_actual_returncode':cp.returncode,'preparation_sha256':sha(O/'PHYSICAL_PREPARATION.json'),'vendor_started':False,'runtime_attempt_created':False}))
