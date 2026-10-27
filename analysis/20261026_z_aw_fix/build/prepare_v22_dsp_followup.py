"""Prepare a new thin v22 official DSP/BSRAM placement option; never run vendor."""
from pathlib import Path
import ast,datetime,difflib,hashlib,importlib.util,json,subprocess,sys
B=Path(__file__).resolve().parent;R=B.parents[2];O=B/'compact_aw_v22_dsp_followup';P=B/'compact_aw_v22'
ROOT=R/'out/z_aw_fix_20261026/compact_aw_v22';PROFILE='physical_p3r0_dsploc_01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
write=lambda p,j:p.write_text(json.dumps(j,indent=2,ensure_ascii=False)+'\n',encoding='utf8',newline='\n')
assert sorted(p.name for p in O.iterdir())==['STANDARD22_STABILITY.json','portable_constraints.py'] and not (ROOT/PROFILE).exists()
spec=importlib.util.spec_from_file_location('new_v22_portable_filter',O/'portable_constraints.py');checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
report,base=checker.measure();vg=base['VG_sha256']
names=['run_physical.py','launch_physical_hidden.py','seal_terminal.py','independent_raw_review.py','physical_snapshot.py','preflight_physical_recipe.py']
parents={n:sha(P/n) for n in names}
(O/'source_freeze.json').write_bytes((P/'source_freeze.json').read_bytes())
checker.PORTABLE.write_bytes(checker.portable_bytes(report))
write(O/'PORTABLE_FILTER_VALIDATION.json',{'verified_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'New read-only portability computation over original official52 and actual sealed v22 VG; exact instance/type only, no generated-number renames. Does not establish device legality/routability/STA.','report':report})

def one(s,a,b):assert s.count(a)==1,(a,s.count(a));return s.replace(a,b,1)
def add_standard(s):
    lines=s.splitlines(True);matches=[i for i,line in enumerate(lines) if 'O=Path(__file__).resolve().parent' in line];assert len(matches)==1
    lines.insert(matches[0]+1,"STANDARD=O.parent/'compact_aw_v22'\n");return ''.join(lines)
def standard_refs(s):
    for n in ['PROOF_BINDING.json','SYNTHESIS_RESULT.json','runner_exit.json','PHYSICAL_INPUT_BINDING.json','COMPONENT_REUSE_BINDING.json']:
        s=s.replace("O/'"+n+"'","STANDARD/'"+n+"'")
    return s

text=add_standard((P/'run_physical.py').read_text(encoding='utf8'))
text=one(text,"ATTEMPT=ROOT/'physical_p3r0_01'",f"ATTEMPT=ROOT/'{PROFILE}'")
text=one(text,'from physical_input_contract import validate22','from portable_constraints import validate,combined_bytes,verify_attempt')
text=one(text,'functional_contract=validate22(require_preparation=True)',"constraint_check=validate();functional_contract=constraint_check['standard_contract']")
text=one(text,"evidence += [O/'physical_input_contract.py',O/'PHYSICAL_INPUT_BINDING.json',O/'PHYSICAL_PREPARATION.json',O/'PHYSICAL_TCL_PREFLIGHT.json']","evidence += [STANDARD/'physical_input_contract.py',STANDARD/'PHYSICAL_INPUT_BINDING.json',STANDARD/'PHYSICAL_PREPARATION.json',STANDARD/'PHYSICAL_TCL_PREFLIGHT.json',O/'portable_constraints.py',O/'PORTABLE_FILTER_VALIDATION.json',O/'PORTABLE_CONSTRAINT_BINDING.json',O/'portable_v22_dsp_bsram.cst',O/'PHYSICAL_PREPARATION.json',O/'PHYSICAL_TCL_PREFLIGHT.json']\n    evidence += [Path(p) for p in json.loads((O/'PORTABLE_CONSTRAINT_BINDING.json').read_text(encoding='utf8'))['bound_inputs']]")
text=standard_refs(text)
text=one(text,"'input_binding_sha256':sha(STANDARD/'PHYSICAL_INPUT_BINDING.json')","'input_binding_sha256':sha(STANDARD/'PHYSICAL_INPUT_BINDING.json'),'thin_portable_constraint_binding_sha256':sha(O/'PORTABLE_CONSTRAINT_BINDING.json')")
text=one(text,"    project=ET.parse(SOURCE/'acg720_ano_port.gprj');","    combined=SOURCE/'physical_constraints.cst';assert not combined.exists();combined.write_bytes(combined_bytes())\n    assert sha(combined)==constraint_check['filter']['combined_CST_sha256'] and hash55(SOURCE,expected)==expected\n    write('portable_constraint_binding.json',{'passed':True,'standard_source_proof_origin':str(STANDARD),'standard_proof_binding_sha256':sha(STANDARD/'PROOF_BINDING.json'),'binding_sha256':sha(O/'PORTABLE_CONSTRAINT_BINDING.json'),'filter_validation_sha256':sha(O/'PORTABLE_FILTER_VALIDATION.json'),'original_baseline_CST_sha256':sha(SOURCE/'acg720_ano_port.cst'),'combined_CST_sha256':sha(combined),'resource_rows':constraint_check['filter']['kept'],'DSP':constraint_check['filter']['DSP'],'BSRAM':constraint_check['filter']['BSRAM'],'source55_unchanged':True})\n    project=ET.parse(SOURCE/'acg720_ano_port.gprj');")
text=one(text,"('acg720_ano_port.cst','file.cst')","('physical_constraints.cst','file.cst')")
text=one(text,"    lines=(SOURCE/'build.tcl').read_text().splitlines();","    assert verify_attempt(SOURCE)['passed']\n    lines=(SOURCE/'build.tcl').read_text().splitlines();")
text=one(text,"'run pnr' if line=='run all'","'set_option -cst_warn_to_error 1\\nrun pnr' if line=='run all'")
text=one(text,"('user_code','0000B0B4')","('user_code','0000B0B4'),('global_freq','50'),('cst_warn_to_error','1')")
text=one(text,"'project_sha256':sha(physical_project),'tcl_sha256'","'portable_constraint_binding_sha256':sha(O/'PORTABLE_CONSTRAINT_BINDING.json'),'combined_CST_sha256':sha(combined),'original_baseline_CST_sha256':sha(SOURCE/'acg720_ano_port.cst'),'project_sha256':sha(physical_project),'tcl_sha256'")
text=one(text,"    assert validate22(require_preparation=True)['passed']","    assert validate()['passed'] and verify_attempt(SOURCE)['passed']\n    assert sha(combined)==constraint_check['filter']['combined_CST_sha256']")
assert 'validate22(' not in text and 'VG_SHA=json.loads' in text
text=text.replace('Deferred sealed exact-v22 map2 P3/R0 original full physical gates trial','Deferred exact standard-v22 P3/R0 official portable DSP/BSRAM physical-only option')
(O/'run_physical.py').write_text(text,encoding='utf8',newline='\n')

text=(P/'launch_physical_hidden.py').read_text(encoding='utf8');text=one(text,"O=BASE/'physical_p3r0_01'",f"O=BASE/'{PROFILE}'")
text=text.replace('single deferred v19 P3/R0 profile','single deferred standard-v22 portable DSP/BSRAM profile')
(O/'launch_physical_hidden.py').write_text(text,encoding='utf8',newline='\n')

text=add_standard((P/'seal_terminal.py').read_text(encoding='utf8'));text=one(text,"label='physical_p3r0_01'",f"label='{PROFILE}'")
text=one(text,"read(O/'SYNTHESIS_RESULT.json')","read(STANDARD/'SYNTHESIS_RESULT.json')")
text=one(text,'from physical_input_contract import validate22','from portable_constraints import validate,verify_attempt')
text=one(text,"assert validate22(require_preparation=True)['passed']","assert validate()['passed'] and verify_attempt(ATTEMPT/'source')['passed']")
text=one(text,"'donor_evidence_binding.json','functional_evidence_binding.json'","'donor_evidence_binding.json','functional_evidence_binding.json','portable_constraint_binding.json'")
text=one(text,"paths += [ATTEMPT/'physical.tcl',ATTEMPT/'source/physical.gprj']","paths += [ATTEMPT/'physical.tcl',ATTEMPT/'source/physical.gprj',ATTEMPT/'source/physical_constraints.cst',O/'PORTABLE_FILTER_VALIDATION.json',O/'PORTABLE_CONSTRAINT_BINDING.json',O/'portable_v22_dsp_bsram.cst',O/'PHYSICAL_PREPARATION.json',O/'PHYSICAL_TCL_PREFLIGHT.json']")
(O/'seal_terminal.py').write_text(text,encoding='utf8',newline='\n')

text=standard_refs(add_standard((P/'independent_raw_review.py').read_text(encoding='utf8')))
text=one(text,"label='physical_p3r0_01'",f"label='{PROFILE}'")
text=one(text,"read(O/'PHYSICAL_PREPARATION.json')['local_hint_effect_audit_sha256']","read(STANDARD/'PHYSICAL_PREPARATION.json')['local_hint_effect_audit_sha256']")
text=one(text,'import datetime, hashlib, json, math, re, sys','import datetime, hashlib, json, math, re, sys, xml.etree.ElementTree as ET')
anchor="log=(V/'physical.log').read_text(errors='replace'); files="
replacement="""portable_binding=read(O/'PORTABLE_CONSTRAINT_BINDING.json');portable=O/'portable_v22_dsp_bsram.cst';combined=S/'physical_constraints.cst';original=S/'acg720_ano_port.cst'
checks['thin_family_standard_proof_origin']=portable_binding['standard_source_proof_origin']==str(STANDARD) and portable_binding['source55']==expected
checks['portable_bound_inputs_unchanged']=all(sha(Path(p))==h for p,h in portable_binding['bound_inputs'].items())
checks['complete_original_prefix_exact_and_portable_suffix']=combined.read_bytes()==original.read_bytes()+portable.read_bytes() and sha(combined)==portable_binding['combined_CST_sha256']
entries=[(f.attrib['path'],f.attrib['type'],f.attrib.get('enable')) for f in ET.parse(S/'physical.gprj').findall('.//File')]
checks['combined_CST_selected']=entries==[('impl/gwsynthesis/acg720_ano_port.vg','file.netlist','1'),('physical_constraints.cst','file.cst','1'),('acg720_ano_port.sdc','file.sdc','1')]
tcl=(A/'physical.tcl').read_text(encoding='utf8')
checks['constraint_warnings_errors_P3_R0']=re.findall(r'^set_option -cst_warn_to_error\\s+(\\S+)\\s*$',tcl,re.M)==['1'] and re.findall(r'^set_option -place_option\\s+(\\S+)\\s*$',tcl,re.M)==['3'] and re.findall(r'^set_option -route_option\\s+(\\S+)\\s*$',tcl,re.M)==['0']
log=(V/'physical.log').read_text(errors='replace'); files="""
text=one(text,anchor,replacement)
text=one(text,"checks['raw_log_hash']","files.update({str(p.relative_to(R)):sha(p) for p in [combined,S/'physical.gprj',A/'physical.tcl',portable,O/'PORTABLE_FILTER_VALIDATION.json',O/'PORTABLE_CONSTRAINT_BINDING.json']})\nchecks['raw_log_hash']")
(O/'independent_raw_review.py').write_text(text,encoding='utf8',newline='\n')
text=(P/'physical_snapshot.py').read_text(encoding='utf8');text=one(text,"['physical_p3r0_01']",f"['{PROFILE}']")
(O/'physical_snapshot.py').write_text(text,encoding='utf8',newline='\n')

text=(P/'preflight_physical_recipe.py').read_text(encoding='utf8')
text=one(text,"('user_code','0000B0B4')","('user_code','0000B0B4'),('cst_warn_to_error','1')")
text=one(text,'assert dict(effective_options)==dict(original_options)',"assert dict(effective_options)==dict(original_options,cst_warn_to_error='1')")
text=one(text,"dest=O/'PHYSICAL_TCL_PREFLIGHT.json';","from portable_constraints import validate\ncheck=validate(check_preparation=False);measured=check['filter']\ndest=O/'PHYSICAL_TCL_PREFLIGHT.json';")
text=one(text,"'profiles':checks}","'profiles':checks,'profile_label':'physical_p3r0_dsploc_01','combined_CST_sha256':measured['combined_CST_sha256'],'measured_kept_rows':measured['kept'],'measured_DSP':measured['DSP'],'measured_BSRAM':measured['BSRAM']}")
(O/'preflight_physical_recipe.py').write_text(text,encoding='utf8',newline='\n')

primary=[O/'STANDARD22_STABILITY.json',*map(Path,read(O/'STANDARD22_STABILITY.json')['bound_inputs']),checker.DONOR/'verification/local_hint_effect_audit.json',checker.OFFICIAL,checker.OLD_VALIDATION,checker.DONOR_V4,checker.TARGET,checker.GRAPH,O/'source_freeze.json',O/'PORTABLE_FILTER_VALIDATION.json',checker.PORTABLE,P/'physical_input_contract.py',P/'PHYSICAL_INPUT_BINDING.json',P/'PHYSICAL_PREPARATION.json',P/'PHYSICAL_TCL_PREFLIGHT.json']
bound=dict(base['bound_inputs']);bound.update({str(p):sha(p) for p in primary})
ref_dir=B/'compact_aw_v18_dsp_followup/physical_p3r0_dsploc_01';ref=read(ref_dir/'TERMINAL_MANIFEST.json');raw_ref=read(ref_dir/'INDEPENDENT_RAW_REVIEW.json')
assert ref['classification']=='completed_full_route_timing_failure' and ref['vendor_actual_p_wait']==0 and ref['runner_actual_p_wait']==1 and not ref['passed'] and not raw_ref['passed']
for p in [ref_dir/'TERMINAL_MANIFEST.json',ref_dir/'INDEPENDENT_RAW_REVIEW.json']:bound[str(p)]=sha(p)
reference={'candidate':'v18','profile':PROFILE,'manifest_path':str(ref_dir/'TERMINAL_MANIFEST.json'),'manifest_sha256':sha(ref_dir/'TERMINAL_MANIFEST.json'),'independent_review_sha256':sha(ref_dir/'INDEPENDENT_RAW_REVIEW.json'),'classification':ref['classification'],'fmax_mhz':ref['fmax_mhz'],'vendor_actual_p_wait':0,'runner_actual_p_wait':1,'scope':'Separate v18 physical result demonstrates this placement route can fully route; it failed50MHz and transfers no timing/routability acceptance to v22.'}
write(O/'PORTABLE_CONSTRAINT_BINDING.json',{'prepared_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Thin physical-only resource-location layer over exact standard v22. No new source/proof identity and no qualification claim.',
    'standard_source_proof_origin':str(P),'source55':base['source55'],'standard_proof_binding_sha256':sha(P/'PROOF_BINDING.json'),'standard_guard_binding_sha256':base['guard_binding_sha256'],'standard_stability_sha256':sha(O/'STANDARD22_STABILITY.json'),'local_hint_effect_audit_sha256':base['local_hint_effect_audit_sha256'],'standard_physical_contract_sha256':sha(P/'physical_input_contract.py'),
    'VG_sha256':vg,'filter_validation_sha256':sha(O/'PORTABLE_FILTER_VALIDATION.json'),'checker_sha256':sha(O/'portable_constraints.py'),'bound_inputs':bound,
    'combined_CST_sha256':report['combined_CST_sha256'],'portable_CST_sha256':report['portable_CST_sha256'],'original_baseline_CST_sha256':report['original_baseline_CST_sha256'],
    'original_prefix_rule':'Complete frozen original CST bytes, including existing observer_reset CLOCK_LOC, followed by the exact new portable file bytes/comments. No new IO/clock/SDC directive.',
    'measured_counts':{k:report[k] for k in ['official_export_rows','kept','excluded','DSP','BSRAM']},'route_reference':reference})
(O/PROFILE).mkdir()
for name in names+['portable_constraints.py']:ast.parse((O/name).read_text(encoding='utf8'),filename=str(O/name))
cp=subprocess.run([sys.executable,'-B','-X','utf8',str(O/'preflight_physical_recipe.py')],stdin=subprocess.DEVNULL,capture_output=True,text=True)
(O/'preflight.stdout.log').write_text(cp.stdout,encoding='utf8',newline='\n');(O/'preflight.stderr.log').write_text(cp.stderr,encoding='utf8',newline='\n')
write(O/'PREFLIGHT_EXIT.json',{'actual_completedprocess_returncode':cp.returncode,'normal_return':True,'command':cp.args,'stdout_sha256':sha(O/'preflight.stdout.log'),'stderr_sha256':sha(O/'preflight.stderr.log')})
assert cp.returncode==0,(cp.stdout,cp.stderr)
diff=''
for name in names:diff+=''.join(difflib.unified_diff((P/name).read_text(encoding='utf8').splitlines(True),(O/name).read_text(encoding='utf8').splitlines(True),fromfile='standard_v22/'+name,tofile='v22_dsp_followup/'+name))
(O/'SCRIPT_DERIVATION.diff').write_text(diff,encoding='utf8',newline='\n')
write(O/'PHYSICAL_PREPARATION.json',{'prepared_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Deferred thin physical-only standard-v22 official DSP/BSRAM follow-up, no new candidate source or functional proof. Main controls slot scheduling after standard PNR ends.',
    'profile':PROFILE,'ROOT':str(ROOT),'CANON':str(checker.CANON),'DONOR':str(checker.DONOR),'ATTEMPT':str(ROOT/PROFILE),'receipt_directory':str(O/PROFILE),
    'standard_source_proof_origin':str(P),'source55':base['source55'],'source_freeze_byte_exact_standard':True,'VG_sha256':vg,'B3_relative_change_count':12,'baseline_source55':base['baseline_source55'],'protected_v4_source55':base['protected_v4_source55'],'local_hint_effect_audit_sha256':base['local_hint_effect_audit_sha256'],'actual_DSP_delta_vs_v20':-1,'fresh_successful_proof_receipt_count':len(base['successful_fresh_exit_receipts']),'original_TEMP_compile1_root1_preserved':True,'alias_retry0_completion0':True,
    'standard_proof_binding_sha256':sha(P/'PROOF_BINDING.json'),'standard_guard_binding_sha256':base['guard_binding_sha256'],'portable_constraint_binding_sha256':sha(O/'PORTABLE_CONSTRAINT_BINDING.json'),
    'filter_validation_sha256':sha(O/'PORTABLE_FILTER_VALIDATION.json'),'measured_counts':{k:report[k] for k in ['official_export_rows','kept','excluded','DSP','BSRAM']},'route_reference':reference,
    'parent_scripts_sha256':parents,'new_scripts_sha256':{n:sha(O/n) for n in names+['portable_constraints.py']},'derivation_sha256':sha(O/'SCRIPT_DERIVATION.diff'),'physical_Tcl_preflight_sha256':sha(O/'PHYSICAL_TCL_PREFLIGHT.json'),'preflight_actual_returncode':cp.returncode,'AST_parse_passed':True,
    'effective_option_delta':{'cst_warn_to_error':1},'strict_gates':['fullroute','real20ns/50MHz','all5 slacks nonnegative','setup and hold endpoints0','18pins and B4 identity','actual vendor and runner normal waits0'],
    'launch_command':[sys.executable,'-B','-X','utf8',str(O/'launch_physical_hidden.py'),'3'],'qualification_at_preparation':'Unqualified: no runtime attempt or vendor started; prior v18 fullroute48.148MHz was a timing failure, not v22 acceptance.',
    'diagnostic_PASS_requires':"build_result.passed is True AND actual vendor/root dict receipts normal_wait_return is True and exact int actual_p_wait==0",'vendor_started':False,'runtime_attempt_created':False,'hardware_actions':False})
assert checker.validate()['passed'] and not (ROOT/PROFILE).exists() and not any((O/PROFILE).iterdir())
assert all(sha(P/n)==h for n,h in parents.items())
assert not any((O/n).exists() for n in ['PROOF_BINDING.json','COMPONENT_REUSE_BINDING.json','SYNTHESIS_RESULT.json'])
print(json.dumps({'prepared':True,'profile':PROFILE,'measured_kept':report['kept'],'DSP':report['DSP'],'BSRAM':report['BSRAM'],'excluded':report['excluded'],'preflight_actual_returncode':cp.returncode,'preparation_sha256':sha(O/'PHYSICAL_PREPARATION.json'),'vendor_started':False,'runtime_attempt_created':False}))
