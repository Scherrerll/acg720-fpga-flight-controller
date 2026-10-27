"""Prepare one isolated v18 DSP/BSRAM physical recipe; never launch vendor tools."""
from pathlib import Path
import ast,datetime,difflib,hashlib,importlib.util,json,subprocess,sys

B=Path(__file__).resolve().parent;R=B.parents[2];P=B/'compact_aw_v18';O=B/'compact_aw_v18_dsp_followup'
PROFILE='physical_p3r0_dsploc_01';ROOT=R/'out/z_aw_fix_20261026/compact_aw_v18'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
write=lambda p,j:p.write_text(json.dumps(j,indent=2,ensure_ascii=False)+'\n',encoding='utf8',newline='\n')
assert not (ROOT/PROFILE).exists()
assert sorted(p.name for p in O.iterdir())==['PREPARATION_FAILURE_01.json','portable_constraints.py'],'Only the new checker and retained first preparation failure may precede this one-shot preparation'
spec=importlib.util.spec_from_file_location('local_v18_portable_constraints',O/'portable_constraints.py');checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
validation=checker.validate(check_binding=False)
assert validation['kept']==46 and validation['DSP']==44 and validation['BSRAM']==2
(O/'source_freeze.json').write_bytes((P/'source_freeze.json').read_bytes())

def one(text,a,b):
    assert text.count(a)==1,(a,text.count(a));return text.replace(a,b,1)

names=['run_physical.py','launch_physical_hidden.py','seal_terminal.py','independent_raw_review.py','physical_snapshot.py','preflight_physical_recipe.py']
parents={n:sha(P/n) for n in names}
text=(P/'run_physical.py').read_text(encoding='utf8')
text=text.replace("sys.argv[1] in ['2','3']","sys.argv[1] in ['3']")
text=one(text,"ATTEMPT=ROOT/f'physical_p{PLACE}r0_01'",f"ATTEMPT=ROOT/'{PROFILE}'")
text=one(text,"    assert not ATTEMPT.exists(),'Never overwrite physical evidence'","    from portable_constraints import validate,combined_bytes,verify_attempt\n    constraint_check=validate()\n    assert PLACE==3\n    assert not ATTEMPT.exists(),'Never overwrite physical evidence'")
text=one(text,"evidence += [DONOR/'synthesis_freeze_manifest_final.json',donor_vg,O/'source_freeze.json']","evidence += [DONOR/'synthesis_freeze_manifest_final.json',donor_vg,O/'source_freeze.json']\n    constraint_binding=json.loads((O/'PORTABLE_CONSTRAINT_BINDING.json').read_text(encoding='utf8'))\n    evidence += [Path(p) for p in constraint_binding['bound_inputs']]\n    evidence += [O/'PORTABLE_CONSTRAINT_BINDING.json',O/'PHYSICAL_PREPARATION.json',O/'PHYSICAL_TCL_PREFLIGHT.json',O/'portable_constraints.py']\n    evidence=list(dict.fromkeys(evidence))")
text=one(text,"    project=ET.parse(SOURCE/'acg720_ano_port.gprj');","    combined=SOURCE/'physical_constraints.cst';assert not combined.exists()\n    combined.write_bytes(combined_bytes())\n    assert sha(combined)==constraint_check['combined_CST_sha256']\n    assert hash55(SOURCE,expected)==expected\n    write('portable_constraint_binding.json',{'passed':True,'binding_path':str(O/'PORTABLE_CONSTRAINT_BINDING.json'),'binding_sha256':sha(O/'PORTABLE_CONSTRAINT_BINDING.json'),'original_IO_CST_sha256':sha(SOURCE/'acg720_ano_port.cst'),'combined_CST_sha256':sha(combined),'resource_rows':46,'DSP':44,'BSRAM':2,'source55_unchanged':True})\n    project=ET.parse(SOURCE/'acg720_ano_port.gprj');")
text=one(text,"('acg720_ano_port.cst','file.cst')","('physical_constraints.cst','file.cst')")
text=one(text,"    lines=(SOURCE/'build.tcl').read_text().splitlines();","    assert verify_attempt(SOURCE)['passed']\n    lines=(SOURCE/'build.tcl').read_text().splitlines();")
text=one(text,"'run pnr' if line=='run all'","'set_option -cst_warn_to_error 1\\nrun pnr' if line=='run all'")
text=one(text,"('user_code','0000B0B4')","('user_code','0000B0B4'),('global_freq','50'),('cst_warn_to_error','1')")
text=one(text,"'project_sha256':sha(physical_project),'tcl_sha256'","'portable_constraint_binding_sha256':sha(O/'PORTABLE_CONSTRAINT_BINDING.json'),'combined_CST_sha256':sha(combined),'original_IO_CST_sha256':sha(SOURCE/'acg720_ano_port.cst'),'project_sha256':sha(physical_project),'tcl_sha256'")
text=one(text,"    result=helper.physical_audit(VG_SHA,expected);helper.check_sources(expected)","    result=helper.physical_audit(VG_SHA,expected);helper.check_sources(expected)\n    assert verify_attempt(SOURCE)['passed']\n    assert sha(combined)==constraint_check['combined_CST_sha256']")
text=text.replace('Root-authorized fresh v18 map2 v18 P2-or-P3/R0 original full physical gates physical trial','Deferred exact-v18 P3/R0 official portable DSP/BSRAM trial, original full physical gates')
text=text.replace('Fresh exact-VG v4 physical-only trial; no synthesis/hardware; source override is v4.','Fresh exact-v18 VG physical-only DSP/BSRAM trial; no synthesis/hardware; source55 and original IO CST unchanged.')
text=text.replace('compact_aw_v4 exact-VG v18 P2-or-P3/R0 original full physical gates full physical gate PASS','compact_aw_v18 P3/R0 portable DSP/BSRAM original full physical gate PASS')
(O/'run_physical.py').write_text(text,encoding='utf8',newline='\n')

text=(P/'launch_physical_hidden.py').read_text(encoding='utf8').replace("sys.argv[1] in ['2','3']","sys.argv[1] in ['3']")
text=one(text,"O=BASE/f'physical_p{PLACE}r0_01'",f"O=BASE/'{PROFILE}'")
text=one(text,"assert O.is_dir() and not receipt.exists() and not exit_receipt.exists(),'Never overwrite runner receipts'","assert O.is_dir() and not any((O/n).exists() for n in ['runner_process.json','runner_exit.json','runner.stdout.log','runner.stderr.log']),'Never overwrite runner receipts or logs'")
text=text.replace('one authorized v9 physical profile','the single deferred v18 portable DSP/BSRAM physical profile')
(O/'launch_physical_hidden.py').write_text(text,encoding='utf8',newline='\n')

text=(P/'seal_terminal.py').read_text(encoding='utf8').replace("sys.argv[1] in ['2','3']","sys.argv[1] in ['3']")
text=one(text,"label=f'physical_p{sys.argv[1]}r0_01'",f"label='{PROFILE}'")
text=one(text,"bound=read(V/'donor_evidence_binding.json')['artifacts']","from portable_constraints import verify_attempt\nassert verify_attempt(ATTEMPT/'source')['passed']\nbound=read(V/'donor_evidence_binding.json')['artifacts']")
text=one(text,"paths += [ATTEMPT/'physical.tcl',ATTEMPT/'source/physical.gprj']","paths += [ATTEMPT/'physical.tcl',ATTEMPT/'source/physical.gprj',ATTEMPT/'source/physical_constraints.cst',V/'portable_constraint_binding.json',O/'PORTABLE_CONSTRAINT_BINDING.json',O/'PHYSICAL_PREPARATION.json',O/'PHYSICAL_TCL_PREFLIGHT.json']")
(O/'seal_terminal.py').write_text(text,encoding='utf8',newline='\n')

text=(P/'independent_raw_review.py').read_text(encoding='utf8').replace("sys.argv[1] in ['2','3']","sys.argv[1] in ['3']")
text=one(text,"label=f'physical_p{sys.argv[1]}r0_01'",f"label='{PROFILE}'")
text=one(text,"import datetime, hashlib, json, math, re, sys","import datetime, hashlib, json, math, re, sys, xml.etree.ElementTree as ET")
anchor="log=(V/'physical.log').read_text(errors='replace'); files="
replacement="""binding=read(O/'PORTABLE_CONSTRAINT_BINDING.json')
portable=Path(binding['portable_constraint_path']);original=S/'acg720_ano_port.cst';combined=S/'physical_constraints.cst'
checks['portable_external_bindings']=all(sha(Path(p))==h for p,h in binding['bound_inputs'].items())
checks['original_IO_prefix_and_exact_resource_suffix']=combined.read_bytes()==original.read_bytes()+portable.read_bytes() and sha(combined)==binding['validation']['combined_CST_sha256']
entries=[(f.attrib['path'],f.attrib['type'],f.attrib.get('enable')) for f in ET.parse(S/'physical.gprj').findall('.//File')]
checks['combined_CST_selected']=entries==[('impl/gwsynthesis/acg720_ano_port.vg','file.netlist','1'),('physical_constraints.cst','file.cst','1'),('acg720_ano_port.sdc','file.sdc','1')]
tcl=(A/'physical.tcl').read_text(encoding='utf8')
checks['physical_P3_R0_constraint_warnings_are_errors']=re.findall(r'^set_option -cst_warn_to_error\\s+(\\S+)\\s*$',tcl,re.M)==['1'] and re.findall(r'^set_option -place_option\\s+(\\S+)\\s*$',tcl,re.M)==['3'] and re.findall(r'^set_option -route_option\\s+(\\S+)\\s*$',tcl,re.M)==['0']
log=(V/'physical.log').read_text(errors='replace'); files="""
text=one(text,anchor,replacement)
text=one(text,"checks['raw_log_hash']", "files.update({str(p.relative_to(R)):sha(p) for p in [combined,S/'physical.gprj',A/'physical.tcl',O/'PORTABLE_CONSTRAINT_BINDING.json']})\nchecks['raw_log_hash']")
(O/'independent_raw_review.py').write_text(text,encoding='utf8',newline='\n')

text=(P/'physical_snapshot.py').read_text(encoding='utf8')
text=one(text,"['physical_p3r0_01','physical_p2r0_01']",f"['{PROFILE}']")
(O/'physical_snapshot.py').write_text(text,encoding='utf8',newline='\n')

text=(P/'preflight_physical_recipe.py').read_text(encoding='utf8')
text=one(text,"for place in [2,3]:","for place in [3]:")
text=one(text,"('user_code','0000B0B4')","('user_code','0000B0B4'),('cst_warn_to_error','1')")
text=one(text,"    assert tcl.count('run pnr\\n')==1", "    original_options=re.findall(r'^set_option -(\\S+)\\s+(\\S+)\\s*$', '\\n'.join(lines),re.M)\n    effective_options=re.findall(r'^set_option -(\\S+)\\s+(\\S+)\\s*$',tcl,re.M)\n    assert len(dict(original_options))==len(original_options) and len(dict(effective_options))==len(effective_options)\n    assert dict(effective_options)==dict(original_options,cst_warn_to_error='1')\n    assert tcl.count('open_project physical.gprj\\n')==1\n    assert tcl.count('run pnr\\n')==1")
text=one(text,"dest=O/'PHYSICAL_TCL_PREFLIGHT.json';", "from portable_constraints import validate,combined_bytes\nconstraint=validate(check_binding=False)\nassert constraint==json.loads((O/'PORTABLE_CONSTRAINT_BINDING.json').read_text(encoding='utf8'))['validation']\nassert (O/'source_freeze.json').read_bytes()==(O.parent/'compact_aw_v18/source_freeze.json').read_bytes()\ndest=O/'PHYSICAL_TCL_PREFLIGHT.json';")
text=one(text,"'profiles':checks}","'profiles':checks,'profile_label':'physical_p3r0_dsploc_01','combined_CST_sha256':constraint['combined_CST_sha256'],'portable_rows':46,'DSP':44,'BSRAM':2}")
text=one(text,"'profiles':[2,3]","'profiles':[3]")
(O/'preflight_physical_recipe.py').write_text(text,encoding='utf8',newline='\n')

bound_paths=[checker.O/'source_freeze.json',P/'source_freeze.json',P/'PROOF_BINDING.json',P/'VY_BINDING.json',P/'SYNTHESIS_RESULT.json',P/'REUSED_BINDINGS_RECHECK.json',checker.OFFICIAL,checker.VALIDATION,checker.PORTABLE,checker.GRAPH,checker.TARGET,checker.DONOR_V4,checker.HELPER]
bound_paths += [checker.DONOR/'verification'/n for n in ['build_input.json','synthesis_summary.json','synthesis_exit.json','synthesis.log','mapped_audit.json','gain_port_audit.json','strict_ff_clock_audit.json']]
bound_paths += [checker.DONOR/'synthesis_freeze_manifest_final.json']
binding={'prepared_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Official v4 timing-failed fullroute resource placements, exact semantic name/type compatible subset for v18 only. No device legality/routability/STA acceptance implied.',
    'profile':PROFILE,'runtime_ROOT':str(ROOT),'CANON':str(checker.CANON),'DONOR':str(checker.DONOR),'runtime_attempt_created':False,
    'official_export_path':str(checker.OFFICIAL),'export_validation_path':str(checker.VALIDATION),'portable_constraint_path':str(checker.PORTABLE),
    'bound_inputs':{str(p):sha(p) for p in bound_paths},'checker_sha256':sha(O/'portable_constraints.py'),'validation':validation,
    'original_IO_rule':'Original source55 CST, including its existing observer_reset CLOCK_LOC, remains byte-exact; separate physical_constraints.cst equals the original CST bytes followed by exact portable file bytes, including comments.',
    'normalization_rule':'Remove exactly one leading Verilog lexical escape per hierarchy segment; reject collisions; no numerical generated-instance rename or CST line rewrite.',
    'effective_option_delta':{'cst_warn_to_error':'1'},'functional_binding_sha256':sha(P/'PROOF_BINDING.json'),'VY_binding_sha256':sha(P/'VY_BINDING.json'),'actual_SYN_VG_sha256':checker.VG_SHA}
write(O/'PORTABLE_CONSTRAINT_BINDING.json',binding)
(O/PROFILE).mkdir()
for n in names+['portable_constraints.py']:ast.parse((O/n).read_text(encoding='utf8'),filename=str(O/n))
process=subprocess.run([sys.executable,'-B','-X','utf8',str(O/'preflight_physical_recipe.py')],stdin=subprocess.DEVNULL,capture_output=True,text=True)
(O/'preflight.stdout.log').write_text(process.stdout,encoding='utf8',newline='\n');(O/'preflight.stderr.log').write_text(process.stderr,encoding='utf8',newline='\n')
write(O/'PREFLIGHT_EXIT.json',{'actual_completedprocess_returncode':process.returncode,'normal_return':True,'command':process.args,'stdout_sha256':sha(O/'preflight.stdout.log'),'stderr_sha256':sha(O/'preflight.stderr.log')})
assert process.returncode==0,(process.stdout,process.stderr)
new={n:sha(O/n) for n in names+['portable_constraints.py']}
diff=''
for n in names:diff+=''.join(difflib.unified_diff((P/n).read_text(encoding='utf8').splitlines(True),(O/n).read_text(encoding='utf8').splitlines(True),fromfile='v18/'+n,tofile='v18_dsp_followup/'+n))
(O/'SCRIPT_DERIVATION.diff').write_text(diff,encoding='utf8',newline='\n')
write(O/'PHYSICAL_PREPARATION.json',{'prepared_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Deferred single P3/R0 physical-only portable DSP/BSRAM follow-up. No vendor execution or runtime attempt created.',
    'profile':PROFILE,'runtime_ROOT':str(ROOT),'CANON':str(checker.CANON),'DONOR':str(checker.DONOR),'ATTEMPT':str(ROOT/PROFILE),'receipt_directory':str(O/PROFILE),
    'source55':validation['source55'],'source_freeze_byte_exact_parent':True,'source_freeze_sha256':sha(O/'source_freeze.json'),
    'parent_scripts_sha256':parents,'new_scripts_sha256':new,'script_derivation_sha256':sha(O/'SCRIPT_DERIVATION.diff'),
    'portable_constraint_binding_sha256':sha(O/'PORTABLE_CONSTRAINT_BINDING.json'),'physical_Tcl_preflight_sha256':sha(O/'PHYSICAL_TCL_PREFLIGHT.json'),
    'preflight_actual_returncode':process.returncode,'AST_parse_passed':True,'original_helper_sha256':checker.HELPER_SHA,'actual_SYN_VG_sha256':checker.VG_SHA,
    'functional_binding_sha256':sha(P/'PROOF_BINDING.json'),'VY_binding_sha256':sha(P/'VY_BINDING.json'),
    'constraint_rows':{'official':52,'kept':46,'DSP':44,'BSRAM':2,'excluded':6},'effective_physical_option_delta':{'cst_warn_to_error':1},
    'unchanged':'Exact existing v18 source55, SYN VG, logic, thresholds, clocks, SDC, IO bytes, map2, place3, route0, route_maxfan23, usercode0000B0B4; combined CST only adds the exact portable DSP/BSRAM suffix.',
    'strict_gates':['full route','real20ns/50MHz','all5 slacks nonnegative','setup/hold endpoints0','18pins and B4 identity','actual vendor0 and runner0'],
    'launch_command':[sys.executable,'-B','-X','utf8',str(O/'launch_physical_hidden.py'),'3'],
    'scheduling':'Root alone authorizes launch after the currently owned PNR ends; preparation does not start it.','vendor_started':False,'runtime_attempt_created':False,'hardware_actions':False})
assert checker.validate()['passed']
assert not (ROOT/PROFILE).exists() and not any((O/PROFILE).iterdir())
assert all(sha(P/n)==h for n,h in parents.items())
print(json.dumps({'prepared':True,'profile':PROFILE,'rows':46,'DSP':44,'BSRAM':2,'preflight_actual_returncode':process.returncode,'preparation_sha256':sha(O/'PHYSICAL_PREPARATION.json'),'vendor_started':False,'runtime_attempt_created':False,'launch_command':[sys.executable,'-B','-X','utf8',str(O/'launch_physical_hidden.py'),'3']}))
