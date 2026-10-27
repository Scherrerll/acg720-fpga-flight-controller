"""Deferred sealed exact-v22 map2 P3/R0 original full physical gates trial; no resynthesis/hardware."""
from pathlib import Path
import datetime,hashlib,importlib.util,json,os,re,shutil,traceback,xml.etree.ElementTree as ET
import sys
assert len(sys.argv)==2 and sys.argv[1] in ['3'];PLACE=int(sys.argv[1])
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;R=O.parents[3];ROOT=R/'out/z_aw_fix_20261026/compact_aw_v22'
CANON=ROOT/'canonical/source';DONOR=ROOT/'build_attempt_01';ATTEMPT=ROOT/'physical_p3r0_01';SOURCE=ATTEMPT/'source';VERIFY=ATTEMPT/'verification'
ORIGINAL=R/'firmware/B0B4/source';PRIOR=R/'out/z_aw_fix_20261026/compact_aw_v4/canonical/source';HELPER=R/'firmware/B0B4/build_candidate.py'
HELPER_SHA='abb5246c203b73c111f80bc91f8db6c8220463f7d4c5cf48dbfe2167ef49db84'
VG_SHA=json.loads((DONOR/'verification/synthesis_summary.json').read_text(encoding='utf8'))['netlist_sha256']
OWNED=False
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,data):(VERIFY/name).write_text(json.dumps(data,indent=2)+'\n')
def hash55(root,paths):return {p:sha(root/p) for p in paths}
def main():
    global OWNED
    from physical_input_contract import validate22
    functional_contract=validate22(require_preparation=True)
    assert PLACE==3
    assert not ATTEMPT.exists(),'Never overwrite physical evidence'
    assert sha(HELPER)==HELPER_SHA
    freeze=json.loads((O/'source_freeze.json').read_text());expected=freeze['source55']
    assert len(expected)==55
    proof=json.loads((O/'PROOF_BINDING.json').read_text(encoding='utf8'))
    assert proof['passed'] and proof['source55']==expected and proof['guard_binding_sha256']==functional_contract['guard_binding_sha256']
    syn_result=json.loads((O/'SYNTHESIS_RESULT.json').read_text(encoding='utf8'));syn_root=json.loads((O/'runner_exit.json').read_text(encoding='utf8'))
    assert syn_result['passed_SYN_only'] and syn_result['source55']==expected and syn_result['netlist_sha256']==VG_SHA
    assert syn_result['vendor_actual_wait']==syn_result['runner_actual_wait']==syn_result['audit_actual_wait']==0
    assert syn_root['normal_wait_return'] and syn_root['actual_p_wait']==0
    din=json.loads((DONOR/'verification/build_input.json').read_text());original=din['original_B4_source55'];prior=json.loads((O.parent/'compact_aw_v4/source_freeze.json').read_text())['source55'];baseline20=functional_contract['baseline_source55'];BASELINE20=R/'out/z_aw_fix_20261026/compact_aw_v20/canonical/source'
    assert hash55(CANON,expected)==expected and hash55(ORIGINAL,expected)==original and hash55(PRIOR,expected)==prior and hash55(BASELINE20,baseline20)==baseline20
    summary=json.loads((DONOR/'verification/synthesis_summary.json').read_text());ex=json.loads((DONOR/'verification/synthesis_exit.json').read_text())
    mapped=json.loads((DONOR/'verification/mapped_audit.json').read_text());gain=json.loads((DONOR/'verification/gain_port_audit.json').read_text());clock=json.loads((DONOR/'verification/strict_ff_clock_audit.json').read_text())
    assert summary['passed'] is True and summary['actual_p_wait']==ex['actual_p_wait']==0 and summary['source_sha256']==expected
    for name,key in [('synthesis_exit.json','synthesis_exit_sha256'),('mapped_audit.json','mapped_audit_sha256'),('gain_port_audit.json','gain_port_audit_sha256'),('strict_ff_clock_audit.json','strict_ff_clock_audit_sha256')]:assert sha(DONOR/'verification'/name)==summary[key]
    assert sha(DONOR/'verification/synthesis.log')==ex['log_sha256']
    assert mapped['passed'] is True and mapped['source_sha256']==expected and mapped['netlist_sha256']==VG_SHA
    assert gain['passed'] is True and gain['netlist_sha256']==VG_SHA and len(gain['top_ports'])==18
    assert gain['gains']['p']['init_wire']==1000 and gain['gains']['i']['init_wire']==350
    assert clock['passed'] is True and clock['all_FF_CLK50'] is True and not clock['bad'] and clock['vg_sha256']==VG_SHA
    assert din['synthesis_options']=={'map_option':2,'replicate_resources':0,'max_fanout':200,'opt_goal':'area'} and hash55(DONOR/'source',expected)==expected
    donor_vg=DONOR/'source/impl/gwsynthesis/acg720_ano_port.vg';assert sha(donor_vg)==summary['netlist_sha256']==VG_SHA
    evidence=[DONOR/'verification'/n for n in ['build_input.json','synthesis_summary.json','synthesis_exit.json','synthesis.log','mapped_audit.json','gain_port_audit.json','strict_ff_clock_audit.json']]
    evidence += [DONOR/'synthesis_freeze_manifest_final.json',donor_vg,O/'source_freeze.json',DONOR/'verification/local_hint_effect_audit.json']
    evidence += [Path(p) for p in functional_contract['bound_inputs']]
    evidence += [O/'physical_input_contract.py',O/'PHYSICAL_INPUT_BINDING.json',O/'PHYSICAL_PREPARATION.json',O/'PHYSICAL_TCL_PREFLIGHT.json']
    evidence=list(dict.fromkeys(evidence))
    bound={str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in evidence}
    spec=importlib.util.spec_from_file_location('v4_exact_original_physical_gate',HELPER);helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    helper.CANON=CANON;helper.ATTEMPT=ATTEMPT;helper.SOURCE=SOURCE;helper.VERIFY=VERIFY
    ATTEMPT.mkdir(parents=True);OWNED=True;shutil.copytree(CANON,SOURCE);VERIFY.mkdir()
    shutil.copy2(Path(__file__),VERIFY/'executed_run_physical.py')
    write('donor_evidence_binding.json',{'passed':True,'artifacts':bound,'source55':expected,'vg_sha256':VG_SHA})
    write('functional_evidence_binding.json',{'passed':True,'schema':'v22 fresh controller five/FRAC0-16/four/top13/function alias; original TEMP compile1/root1, exact-fixture alias retry0 and completion0 explicitly preserved','proof_binding_sha256':sha(O/'PROOF_BINDING.json'),'input_binding_sha256':sha(O/'PHYSICAL_INPUT_BINDING.json'),'guard_binding_sha256':functional_contract['guard_binding_sha256'],'successful_fresh_exit_receipts':functional_contract['successful_fresh_exit_receipts'],'original_attempt_root_actual_wait':1,'original_TEMP_alias_compile_actual_wait':1,'actual_alias_retry_root_wait':0,'actual_completion_runner_wait':0,'actual_top13_child_root_wait':0,'fresh_controller_six_dependencies':proof['fresh_controller_six_dependencies'],'old_controller_byte_identity_reuse_claimed':False,'scope':functional_contract['scope'],'controller_scope':functional_contract['controller_scope'],'component_scope':functional_contract['component_scope']})
    tmp=VERIFY/'tmp';tmp.mkdir();os.environ.update(TMP=str(tmp),TEMP=str(tmp),TMPDIR=str(tmp))
    vg=SOURCE/'impl/gwsynthesis/acg720_ano_port.vg';vg.parent.mkdir(parents=True);shutil.copy2(donor_vg,vg);assert sha(vg)==VG_SHA
    project=ET.parse(SOURCE/'acg720_ano_port.gprj');root=project.getroot();filelist=root.find('FileList');filelist.clear()
    entries=[('impl/gwsynthesis/acg720_ano_port.vg','file.netlist'),('acg720_ano_port.cst','file.cst'),('acg720_ano_port.sdc','file.sdc')]
    for path,kind in entries:ET.SubElement(filelist,'File',dict(path=path,type=kind,enable='1'))
    physical_project=SOURCE/'physical.gprj';physical_project.write_bytes(b'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE gowin-fpga-project>\n'+ET.tostring(root,encoding='utf-8'))
    raw=physical_project.read_bytes();assert raw.count(b'<?xml')==1
    assert [(f.attrib['path'],f.attrib['type']) for f in ET.fromstring(raw).find('FileList')]==entries
    write('project_serialization_check.json',{'passed':True,'xml_declarations':1,'exact_netlist_constraints_project':True,'project_sha256':sha(physical_project)})
    lines=(SOURCE/'build.tcl').read_text().splitlines();assert lines.count('run all')==1 and lines.count('exit')==1
    tcl='\n'.join('run pnr' if line=='run all' else 'open_project physical.gprj' if line=='open_project acg720_ano_port.gprj' else f'set_option -place_option {PLACE}' if line=='set_option -place_option 3' else line for line in lines if line.strip()!='exit')+'\nputs PHYSICAL_COMMAND_RETURNED_EOF\nflush stdout\n'
    for option,value in [('place_option',str(PLACE)),('route_option','0'),('map_option','2'),('replicate_resources','0'),('timing_driven','1'),('route_maxfan','23'),('user_code','0000B0B4')]:assert re.findall(r'^set_option -'+option+r'\s+(\S+)\s*$',tcl,re.M)==[value]
    assert 'run syn' not in tcl and 'run all' not in tcl
    execution=ATTEMPT/'physical.tcl';execution.write_text(tcl,encoding='utf8')
    write('build_input.json',{'scope':'Fresh sealed exact-v22 VG physical-only trial; standard original CST/SDC/logic unchanged; no synthesis/hardware.',
      'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'canonical_override':str(CANON),'source_sha256':expected,
      'original_B4_source55':original,'v4_source55':prior,'protected_v4_source55':prior,'baseline_v20_source55':baseline20,'local_hint_effect_audit_sha256':functional_contract['local_hint_effect_audit_sha256'],'source_freeze_sha256':sha(O/'source_freeze.json'),'runner_sha256':sha(Path(__file__)),
      'imported_helper_sha256':HELPER_SHA,'donor':str(DONOR),'donor_netlist_sha256':VG_SHA,
      'donor_synthesis_summary_sha256':sha(DONOR/'verification/synthesis_summary.json'),'donor_synthesis_exit_sha256':sha(DONOR/'verification/synthesis_exit.json'),
      'donor_mapped_audit_sha256':sha(DONOR/'verification/mapped_audit.json'),'donor_gain_port_audit_sha256':sha(DONOR/'verification/gain_port_audit.json'),
      'donor_strict_ff_clock_audit_sha256':sha(DONOR/'verification/strict_ff_clock_audit.json'),
      'physical_options':{'place':PLACE,'route':0,'map_option':2,'replicate_resources':0,'route_maxfan':23},'period_ns':20,'usercode':'0000B0B4'})
    write('physical_input.json',{'source_sha256':expected,'canonical_override':str(CANON),'donor_netlist_sha256':VG_SHA,
      'project_sha256':sha(physical_project),'tcl_sha256':sha(execution),'runner_sha256':sha(Path(__file__))})
    helper.run_phase('physical',[str(helper.GOWIN),str(execution)],SOURCE,expected)
    result=helper.physical_audit(VG_SHA,expected);helper.check_sources(expected)
    assert validate22(require_preparation=True)['passed']
    assert {str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in evidence}==bound
    assert hash55(ORIGINAL,expected)==original and hash55(PRIOR,expected)==prior and hash55(BASELINE20,baseline20)==baseline20 and sha(donor_vg)==VG_SHA and sha(HELPER)==HELPER_SHA
    write('build_result.json',{'passed':True,'scope':'v22 physical artifact gate only; functional equivalence/hardware acceptance separate.',
      'source_sha256':expected,'canonical_override':str(CANON),'netlist_sha256':VG_SHA,'original_B4_source55_unchanged':True,'v4_source55_unchanged':True,'baseline_v20_source55_unchanged':True,'local_hint_effect_audit_sha256':functional_contract['local_hint_effect_audit_sha256'],
      'physical_options':{'place':PLACE,'route':0,'map_option':2,'replicate_resources':0,'route_maxfan':23},'physical_audit_sha256':sha(VERIFY/'physical_audit.json'),
      'physical_exit_sha256':sha(VERIFY/'physical_exit.json'),'bitstream_sha256':sha(SOURCE/'impl/pnr/acg720_ano_port.fs'),'checks':result['checks'],'fmax_mhz':result['fmax_mhz']})
    print('compact_aw_v22 exact-VG P3/R0 original full physical gate PASS',flush=True)
if __name__=='__main__':
    try:main()
    except BaseException as exc:
        if OWNED and VERIFY.exists():write('build_failure.json',{'passed':False,'exception':repr(exc),'traceback':traceback.format_exc()})
        raise
