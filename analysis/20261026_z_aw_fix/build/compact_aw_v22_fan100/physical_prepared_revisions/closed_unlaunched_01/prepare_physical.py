"""One-time offline preparation of a standard P3/R0 trial on the sealed fan100 VG."""
from pathlib import Path
import ast,datetime,hashlib,json,subprocess,sys
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;R=O.parents[3];STANDARD=O.parent/'compact_aw_v22'
ROOT=R/'out/z_aw_fix_20261026/compact_aw_v22_fan100';PROFILE='physical_p3r0_01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
write=lambda p,j:p.write_text(json.dumps(j,indent=2)+'\n',encoding='utf8')
assert not (ROOT/PROFILE).exists() and not (O/PROFILE).exists() and not (O/'PHYSICAL_PREPARATION.json').exists()
# Existing successful SYN-bound inputs must not change while adding physical metadata.
old_files={Path(p):h for p,h in read(ROOT/'build_attempt_01/verification/build_input.json')['bound_inputs'].items()}
for n in ['SYNTHESIS_RESULT.json','runner_exit.json','runner_process.json','runner.stdout.log','runner.stderr.log','source_freeze.json','SOURCE_REUSE_BINDING.json','SYNTHESIS_PREPARATION.json','SYN_REVIEW_GATE.json']:
    old_files[O/n]=sha(O/n)
for p,h in old_files.items():assert sha(p)==h,p
from physical_input_contract import validate_physical
base=validate_physical(require_preparation=False)
names=['physical_recipe.py','physical_input_contract.py','run_physical.py','launch_physical_hidden.py','seal_terminal.py','physical_snapshot.py','independent_raw_review.py','preflight_physical.py','prepare_physical.py']
for n in names:ast.parse((O/n).read_text(),filename=str(O/n))
write(O/'PHYSICAL_INPUT_BINDING.json',{'passed':True,'validation':base,'protected_existing_SYN_inputs':{str(p):h for p,h in old_files.items()},'scope':'Whole55/proof ownership remains STD22; donor fan100 VG and its actual successful complete SYN seal verified. Physical metadata is additive only.'})
cmd=[sys.executable,'-B','-X','utf8',str(O/'preflight_physical.py')]
with (O/'physical_preflight.stdout.log').open('xb') as out,(O/'physical_preflight.stderr.log').open('xb') as err:
    p=subprocess.Popen(cmd,stdout=out,stderr=err,stdin=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW);code=p.wait(timeout=60)
write(O/'PHYSICAL_PREFLIGHT_EXIT.json',{'command':cmd,'actual_p_wait':code,'normal_wait_return':True,'pid':p.pid,'script_sha256':sha(O/'preflight_physical.py'),'stdout_sha256':sha(O/'physical_preflight.stdout.log'),'stderr_sha256':sha(O/'physical_preflight.stderr.log')})
assert code==0,(O/'physical_preflight.stderr.log').read_text()
(O/PROFILE).mkdir()
write(O/'PHYSICAL_PREPARATION.json',{'prepared_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Additive deferred standard P3/R0 fan100-VG physical-only preparation; no vendor launch or DSP locations. Main controls single slot after current owned physical ends.',
 'profile':PROFILE,'ROOT':str(ROOT),'CANON':base['canonical_source_root'],'DONOR':base['DONOR'],'ATTEMPT':str(ROOT/PROFILE),'receipt_directory':str(O/PROFILE),
 'source55':base['source55'],'standard_source_proof_origin':base['standard_source_proof_origin'],'VG_sha256':base['VG_sha256'],'guard_binding_sha256':base['guard_binding_sha256'],'local_hint_effect_audit_sha256':base['local_hint_effect_audit_sha256'],
 'input_binding_sha256':sha(O/'PHYSICAL_INPUT_BINDING.json'),'new_scripts_sha256':{n:sha(O/n) for n in names},
 'source_build_Tcl_max_fanout':200,'effective_physical_max_fanout':100,'PNR_must_skip_synthesis':True,'CST_SDC':'Complete original byte-exact STD22 constraints; no DSPLOC, no new directives.',
 'physical_options':{'place':3,'route':0,'map_option':2,'replicate_resources':0,'max_fanout':100,'route_maxfan':23,'global_freq':50,'user_code':'0000B0B4'},
 'preflight_actual_wait':code,'physical_Tcl_preflight_sha256':sha(O/'PHYSICAL_TCL_PREFLIGHT.json'),'preflight_exit_sha256':sha(O/'PHYSICAL_PREFLIGHT_EXIT.json'),'strict_gates':['fullroute/EOF/skipsynthesis','20ns/50MHz','all5 finite nonnegative slacks','setup_hold0endpoints','18pins/B4','original mapped CLK50/radio/gain18','actual vendor/root normal exact-int0'],
 'launch_command':[sys.executable,'-B','-X','utf8',str(O/'launch_physical_hidden.py'),'3'],'vendor_started':False,'runtime_attempt_created':False,'hardware_actions':False})
write(O/'PHYSICAL_REVIEW_REQUIREMENTS.json',{'scope':'Main plus independent review of these exact physical-only preparation hashes before creating PHYSICAL_REVIEW_GATE.json; this file does not authorize launch.',
 'preparation_sha256':sha(O/'PHYSICAL_PREPARATION.json'),'input_binding_sha256':sha(O/'PHYSICAL_INPUT_BINDING.json'),'reviewed_scripts_sha256':{n:sha(O/n) for n in names},'required_true_fields':['main_review_passed','independent_agent_review_passed'],'actual_gate_path':str(O/'PHYSICAL_REVIEW_GATE.json'),'vendor_started':False})
assert validate_physical()['passed'] and not (ROOT/PROFILE).exists() and not any((O/PROFILE).iterdir())
for p,h in old_files.items():assert sha(p)==h,p
print(json.dumps({'prepared_physical_only':True,'VG':base['VG_sha256'],'preflight_actual_wait':code,'preparation_sha256':sha(O/'PHYSICAL_PREPARATION.json'),'review_requirements_sha256':sha(O/'PHYSICAL_REVIEW_REQUIREMENTS.json'),'protected_existing_SYN_inputs_unchanged':True,'vendor_started':False,'runtime_attempt_created':False}))
