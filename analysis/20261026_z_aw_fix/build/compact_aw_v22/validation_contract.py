"""Read-only v22 exact one-file scope and actual fresh-proof contract."""
from pathlib import Path
import hashlib,importlib.util,json,re,sys
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;R=O.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def check_receipt(path,h):
 assert sha(path)==h,path;j=read(path)
 if 'actual_p_wait' in j:assert j['normal_wait_return'] and j['actual_p_wait']==0
 else:assert j['normal_return'] and j['actual_completedprocess_returncode']==0
 assert not j.get('terminated_after_timeout')
 return j
def verify_contract(check_proof=False):
 f=read(O/'source_freeze.json');expected=f['source55'];C=Path(f['source_root']);s=read(O/'SOURCE_CHANGES.json')
 assert len(expected)==55 and {n:sha(C/n) for n in expected}==expected==s['source55']
 assert sorted(p.relative_to(C).as_posix() for p in C.rglob('*') if p.is_file())==sorted(expected)
 for n in expected:
  p=C/n;assert not p.is_symlink() and p.resolve().is_relative_to(C.resolve()) and not p.name.lower().startswith('.env')
 parent=O.parent/'compact_aw_v20';old=Path(s['parent_source_root']);old55=s['parent_source55']
 assert len(old55)==55 and {n:sha(old/n) for n in old55}==old55==read(parent/'source_freeze.json')['source55']
 assert read(parent/'SYNTHESIS_RESULT.json')['passed_SYN_only'] and read(parent/'SYNTHESIS_RESULT.json')['source55']==old55
 assert sha(parent/'source_freeze.json')==f['parent_source_freeze_sha256'] and sha(parent/'SYNTHESIS_RESULT.json')==f['parent_SYNTHESIS_RESULT_sha256']
 for n,key in [('SOURCE_CHANGES.json','source_changes_sha256'),('source_review.md','source_review_sha256'),('source_changes.diff','source_diff_sha256')]:assert sha(O/n)==f[key]
 assert s['changed_files']==[n for n in expected if expected[n]!=old55[n]]==['position/mtf_xyz_hold_control.v']
 n=s['changed_files'][0];raw=(C/n).read_bytes()
 for e in reversed(s['exact_reversible_edits']):
  a,b=bytes.fromhex(e['old_hex']),bytes.fromhex(e['new_hex']);assert raw.count(b)==1;raw=raw.replace(b,a,1)
 assert raw==(old/n).read_bytes()
 assert s['legacy_public_output_cycle_change']==s['new_state_bits']==s['new_clock_edges']==0
 assert s['function_unchanged'] and s['pending_actual_synthesis_hint_effect']
 assert sha(Path(s['official_document']))==s['official_document_sha256']
 b3=read(R/'firmware/B0B3/qualification.json')['source_sha256'];changes={n:h for n,h in expected.items() if h!=b3[n]}
 assert len(changes)==12 and changes==f['B3_relative_changes']
 assert {n:sha(R/'firmware/B0B3/source'/n) for n in b3}==b3
 sdc=[x.strip() for x in (C/'acg720_ano_port.sdc').read_text().splitlines() if x.strip() and not x.strip().startswith('#')]
 assert sdc==['create_clock -name clk50 -period 20.000 [get_ports {clk50}]','set_false_path -from [get_ports {radio_rx}]']
 reuse=read(O/'COMPONENT_REUSE_BINDING.json');assert reuse['passed'] and reuse['source55']==expected
 assert reuse['new_controller_requires_fresh_proof'] and not reuse['old_six_controller_hashes_claimed_current']
 assert {p:sha(Path(p)) for p in reuse['bound_inputs']}==reuse['bound_inputs']
 for group,dependency in reuse['unchanged_dependency_sets'].items():
  for n,h in dependency.items():assert expected[n]==h==old55[n],(group,n)
 out={'passed':True,'source55':expected,'B3_relative_changes':changes,'guard_binding_sha256':sha(O/'COMPONENT_REUSE_BINDING.json'),'component_binding_sha256':sha(O/'COMPONENT_REUSE_BINDING.json'),'legacy_public_output_cycle_change':0}
 if check_proof:
  p=read(O/'PROOF_BINDING.json');assert p['passed'] and p['source55']==expected and p['guard_binding_sha256']==out['guard_binding_sha256']
  D=Path(p['proof_directory']);assert D.resolve().is_relative_to(O.resolve())
  assert sha(D/'RESULT.json')==p['result_sha256'];j=read(D/'RESULT.json');assert j['passed'] and j['source55']==expected
  assert sha(D/'inputs.json')==j['inputs_sha256']
  for path,h in read(D/'inputs.json')['bound_inputs'].items():assert sha(Path(path))==h,path
  A=Path(j['fresh_proof_directory']);assert A.resolve().is_relative_to(O.resolve()) and A!=D
  assert j['artifact_base']==j['exit_receipts_base']==str(A)
  for path,h in j['artifacts'].items():assert sha(A/path)==h,path
  for path,h in j['exit_receipts'].items():check_receipt(A/path,h)
  root=check_receipt(D/'functional_runner_exit.json',p['functional_root_exit_sha256'])
  assert root['actual_p_wait']==p['actual_proof_runner_wait']==0 and sha(Path(root['command'][-1]))==root['runner_sha256']
  for stream in ['stdout','stderr']:assert sha(D/f'functional_runner.{stream}.log')==root[f'{stream}_sha256']
  for path,h in p['additional_bound_inputs'].items():assert sha(Path(path))==h,path
  assert j['original_attempt_root_actual_wait']==p['original_attempt_root_actual_wait']==1
  original=read(A/'functional_runner_exit.json');assert original['normal_wait_return'] and original['actual_p_wait']==1
  assert sha(A/'functional_runner_exit.json')==p['original_functional_root_exit_sha256']==j['original_root_receipt_sha256']
  assert j['original_failed_alias_compile_wait']==1 and read(A/'alias_compile_exit.json')['actual_p_wait']==1
  assert j['actual_alias_retry_root_wait']==0
  B=Path(j['alias_retry_directory']);assert B.resolve().is_relative_to(O.resolve())
  assert read(B/'runner_exit.json')['normal_wait_return'] and read(B/'runner_exit.json')['actual_p_wait']==0
  for name in ['actual_functions.v','alias_tb.v','STRUCTURAL_IDENTITY.json']:assert (B/name).read_bytes()==(A/'alias'/name).read_bytes()
  assert read(A/'alias/STRUCTURAL_IDENTITY.json')['actual_function_byte_identical']
  n='position/mtf_xyz_hold_control.v';assert read(A/'alias/STRUCTURAL_IDENTITY.json')['source_controller_sha256']=={'v20':old55[n],'v22':expected[n]}
  assert (A/'top13/top_safety_tb.v').read_bytes()==(O.parent/'v4_release_proofs/top_safety_tb.v').read_bytes()
  assert p['fresh_top13']['actual_root_wait']==0 and p['fresh_top13']['cases']==13
  assert j['fresh_controller_dependency_hashes']['position/mtf_xyz_hold_control.v']==expected['position/mtf_xyz_hold_control.v']
  out['proof_binding_sha256']=sha(O/'PROOF_BINDING.json')
 return out
def verify_syn_review():
 gate=read(O/'SYN_REVIEW_GATE.json');assert gate['main_review_passed'] and gate['independent_agent_review_passed']
 assert gate['source_freeze_sha256']==sha(O/'source_freeze.json') and gate['proof_binding_sha256']==sha(O/'PROOF_BINDING.json')
 for n in ['run_synthesis.py','audit_synthesis_only.py','seal_synthesis.py','launch_synthesis_hidden.py','validation_contract.py']:
  assert gate['reviewed_scripts_sha256'][n]==sha(O/n)
 return gate
