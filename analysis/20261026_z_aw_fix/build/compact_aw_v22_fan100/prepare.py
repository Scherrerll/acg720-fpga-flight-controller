"""One-time metadata binding and pure preflight for same55 fan100; never starts SYN."""
from pathlib import Path
import ast,datetime,hashlib,json,subprocess,sys
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;R=O.parents[3];STANDARD=O.parent/'compact_aw_v22'
ROOT=R/'out/z_aw_fix_20261026/compact_aw_v22_fan100';C=R/'out/z_aw_fix_20261026/compact_aw_v22/canonical/source'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
write=lambda p,j:p.write_text(json.dumps(j,indent=2)+'\n',encoding='utf8')
assert not ROOT.exists() and not (O/'SOURCE_REUSE_BINDING.json').exists()
(O/'source_freeze.json').write_bytes((STANDARD/'source_freeze.json').read_bytes())
from input_contract import validate
base=validate(require_binding=False)
scripts=['input_contract.py','effective_recipe.py','mapped_fanout.py','run_synthesis.py','audit_synthesis_only.py','launch_synthesis_hidden.py','seal_synthesis.py','preflight.py','prepare.py']
for n in scripts:ast.parse((O/n).read_text(encoding='utf8'))
bound=dict(base['bound_inputs'])
for n in ['PROOF_BINDING.json','COMPONENT_REUSE_BINDING.json','source_freeze.json','SYNTHESIS_RESULT.json','physical_input_contract.py','PHYSICAL_PREPARATION.json','PHYSICAL_INPUT_BINDING.json']:
    bound[str(STANDARD/n)]=sha(STANDARD/n)
bound[str(O/'source_freeze.json')]=sha(O/'source_freeze.json')
write(O/'SOURCE_REUSE_BINDING.json',{'passed':True,'source55':base['source55'],'canonical_source_root':str(C),'standard_source_proof_origin':str(STANDARD),
 'parent_VG_sha256':base['VG_sha256'],'standard_proof_binding_sha256':sha(STANDARD/'PROOF_BINDING.json'),'guard_binding_sha256':base['guard_binding_sha256'],
 'bound_inputs':bound,'whole55_byte_identical_to_STD22':True,'copied_source_build_Tcl_remains_max200':True,'no_RTL_tests_rerun':True,
 'actual_parent_proof_history':{'original_TEMP_compile':1,'original_suite_root':1,'alias_retry_root':0,'completion_root':0,'successful_fresh_receipts':22},
 'scope':base['scope'],'component_scope':base['component_scope'],'top13_force_and_component_acceleration_limits_retained':base['controller_scope']})
cmd=[sys.executable,'-B','-X','utf8',str(O/'preflight.py')]
with (O/'preflight.stdout.log').open('xb') as out,(O/'preflight.stderr.log').open('xb') as err:
    p=subprocess.Popen(cmd,stdout=out,stderr=err,stdin=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW);code=p.wait(timeout=60)
write(O/'PREFLIGHT_EXIT.json',{'command':cmd,'normal_wait_return':True,'actual_p_wait':code,'pid':p.pid,'script_sha256':sha(O/'preflight.py'),'stdout_sha256':sha(O/'preflight.stdout.log'),'stderr_sha256':sha(O/'preflight.stderr.log')})
assert code==0,(O/'preflight.stderr.log').read_text()
write(O/'SYNTHESIS_PREPARATION.json',{'prepared_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Dormant SYN_ONLY same-source STD22 max_fanout option trial. No runtime attempt, vendor launch, RTL tests or physical preparation.',
 'source55':base['source55'],'canonical_source_root':str(C),'standard_source_proof_origin':str(STANDARD),'parent_VG_sha256':base['VG_sha256'],
 'source_reuse_binding_sha256':sha(O/'SOURCE_REUSE_BINDING.json'),'source_freeze_sha256':sha(O/'source_freeze.json'),'scripts_sha256':{n:sha(O/n) for n in scripts},
 'unchanged_original_helper_sha256':'abb5246c203b73c111f80bc91f8db6c8220463f7d4c5cf48dbfe2167ef49db84','unchanged_gain18pin_helper_sha256':'23fe046b259c6713536fc27862eb80a3b392808a77e842aac2085c3f91f3d658',
 'effective_option_delta':{'max_fanout':{'from':200,'to':100}},'source_build_Tcl_unchanged':True,'preflight_result_sha256':sha(O/'PREFLIGHT_RESULT.json'),'preflight_exit_sha256':sha(O/'PREFLIGHT_EXIT.json'),'actual_preflight_wait':code,
 'mapped_effect_measurement':'Actual resource differences versus sealed STD22 and actual estimator index FF/direct LUT/n8507 named-family pin loads; no benefit presumed and no fanout<=100 gate.',
 'strict_gates':['actual vendor/audit/root normal exact-int0','SYN-only EOF/noPNR','whole55 source unchanged/B3-relative12','original mapped CLK50/radio','allFF actualCLK50','original live gain1000/350 and18scalar pins'],
 'launch_command':[sys.executable,'-B','-X','utf8',str(O/'launch_synthesis_hidden.py')],'vendor_started':False,'runtime_attempt_created':False,'PNR_prepared':False})
write(O/'REVIEW_REQUIREMENTS.json',{'scope':'Main and independent agent review these exact hashes before the root creates SYN_REVIEW_GATE.json. This requirements file does not authorize a launch.',
 'preparation_sha256':sha(O/'SYNTHESIS_PREPARATION.json'),'source_reuse_binding_sha256':sha(O/'SOURCE_REUSE_BINDING.json'),'reviewed_scripts_sha256':{n:sha(O/n) for n in scripts},'required_true_fields':['main_review_passed','independent_agent_review_passed'],'actual_gate_path':str(O/'SYN_REVIEW_GATE.json'),'vendor_started':False})
assert validate()['source55']==base['source55'] and not ROOT.exists()
print(json.dumps({'prepared':True,'single_option_delta':True,'actual_preflight_wait':code,'preparation_sha256':sha(O/'SYNTHESIS_PREPARATION.json'),'review_requirements_sha256':sha(O/'REVIEW_REQUIREMENTS.json'),'vendor_started':False,'PNR_prepared':False}))
