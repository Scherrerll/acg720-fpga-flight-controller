"""Fresh exact-v9-VG P3/R0 or P2/R0; frozen abb physical gates; never SYN."""
from pathlib import Path
import datetime,hashlib,importlib.util,json,os,re,shutil,sys,traceback,xml.etree.ElementTree as ET
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;R=O.parents[3];ROOT=R/'out/z_aw_fix_20261026/compact_aw_v9'
assert len(sys.argv)==2 and sys.argv[1] in ['2','3'];PLACE=int(sys.argv[1])
LABEL=f'physical_p{PLACE}r0_01';CANON=ROOT/'canonical/source';DONOR=ROOT/'build_attempt_01'
ATTEMPT=ROOT/LABEL;SOURCE=ATTEMPT/'source';VERIFY=ATTEMPT/'verification'
ORIGINAL=R/'firmware/B0B4/source';PRIOR=R/'out/z_aw_fix_20261026/compact_aw_v4/canonical/source';HELPER=R/'firmware/B0B4/build_candidate.py'
HELPER_SHA='abb5246c203b73c111f80bc91f8db6c8220463f7d4c5cf48dbfe2167ef49db84'
VG_SHA='e99d1ec0928fa9c1650cbc6a7ac9c08d4b2ef0758cdb3a9eec11b04af5d0eb20';OWNED=False
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,data):(VERIFY/name).write_text(json.dumps(data,indent=2)+'\n',encoding='utf8')
def hash55(root,paths):return {p:sha(root/p) for p in paths}

def main():
    global OWNED
    assert not ATTEMPT.exists(),'Never overwrite physical evidence'
    assert sha(HELPER)==HELPER_SHA
    freeze=json.loads((O/'source_freeze.json').read_text());expected=freeze['source55']
    assert len(expected)==55 and expected['position/mtf_xyz_hold_control.v']=='ffddb029cb34a8d2ac8995cc43d85866e273d3d147bb650cfd5d3c66c580b642'
    din=json.loads((DONOR/'verification/build_input.json').read_text());original=din['original_B4_source55'];prior=din['baseline_v4_map2_source55']
    assert hash55(CANON,expected)==expected and hash55(ORIGINAL,expected)==original and hash55(PRIOR,expected)==prior
    assert prior==freeze['baseline_source55'] and sorted(p for p in expected if expected[p]!=prior[p])==sorted(freeze['changed_files'])
    summary=json.loads((DONOR/'verification/synthesis_summary.json').read_text());ex=json.loads((DONOR/'verification/synthesis_exit.json').read_text())
    mapped=json.loads((DONOR/'verification/mapped_audit.json').read_text());gain=json.loads((DONOR/'verification/gain_port_audit.json').read_text());clock=json.loads((DONOR/'verification/strict_ff_clock_audit.json').read_text())
    assert summary['passed'] is True and summary['actual_p_wait']==ex['actual_p_wait']==0 and ex['normal_wait_return'] is True and summary['source_sha256']==expected
    for name,key in [('synthesis_exit.json','synthesis_exit_sha256'),('mapped_audit.json','mapped_audit_sha256'),('gain_port_audit.json','gain_port_audit_sha256'),('strict_ff_clock_audit.json','strict_ff_clock_audit_sha256'),('resource_comparison.json','resource_comparison_sha256')]:assert sha(DONOR/'verification'/name)==summary[key]
    assert sha(DONOR/'verification/synthesis.log')==ex['log_sha256']
    assert mapped['passed'] is True and mapped['source_sha256']==expected and mapped['netlist_sha256']==VG_SHA
    assert gain['passed'] is True and gain['netlist_sha256']==VG_SHA and len(gain['top_ports'])==18
    assert gain['gains']['p']['init_wire']==1000 and gain['gains']['i']['init_wire']==350
    assert clock['passed'] is True and clock['all_FF_CLK50'] is True and not clock['bad'] and clock['vg_sha256']==VG_SHA
    assert din['synthesis_options']=={'map_option':2,'replicate_resources':0} and din['source_sha256']==expected and hash55(DONOR/'source',expected)==expected
    syn_runner_exit=json.loads((O/'runner_exit.json').read_text());assert syn_runner_exit['actual_p_wait']==0 and syn_runner_exit['normal_wait_return'] is True
    donor_vg=DONOR/'source/impl/gwsynthesis/acg720_ano_port.vg';assert sha(donor_vg)==summary['netlist_sha256']==VG_SHA
    evidence=[DONOR/'verification'/n for n in ['build_input.json','synthesis_summary.json','synthesis_exit.json','synthesis.log','mapped_audit.json','gain_port_audit.json','strict_ff_clock_audit.json','resource_comparison.json']]
    evidence += [O/'source_freeze.json',O/'runner_exit.json',donor_vg]
    proof=json.loads((O/'proofs_retry02/results.json').read_text());px=json.loads((O/'proofs_retry02/runner_exit.json').read_text())
    assert proof['passed'] and proof['source55']==expected and px['actual_p_wait']==0 and px['normal_wait_return']
    evidence += [O/'proofs_retry02/results.json',O/'proofs_retry02/runner_exit.json']
    bound={str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in evidence}
    spec=importlib.util.spec_from_file_location(f'v9_p{PLACE}_exact_original_physical_gate',HELPER);helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    helper.CANON=CANON;helper.ATTEMPT=ATTEMPT;helper.SOURCE=SOURCE;helper.VERIFY=VERIFY
    ATTEMPT.mkdir(parents=True);OWNED=True;shutil.copytree(CANON,SOURCE);VERIFY.mkdir()
    shutil.copy2(Path(__file__),VERIFY/'executed_run_physical.py')
    tmp=VERIFY/'tmp';tmp.mkdir();os.environ.update(TMP=str(tmp),TEMP=str(tmp),TMPDIR=str(tmp))
    provenance=VERIFY/'donor_provenance';provenance.mkdir()
    for p in evidence:
        if p.suffix=='.json':shutil.copy2(p,provenance/(p.parent.name+'__'+p.name))
    write('donor_evidence_binding.json',{'passed':True,'artifacts':bound,'source55':expected,'vg_sha256':VG_SHA})
    vg=SOURCE/'impl/gwsynthesis/acg720_ano_port.vg';vg.parent.mkdir(parents=True);shutil.copy2(donor_vg,vg);assert sha(vg)==VG_SHA
    project=ET.parse(SOURCE/'acg720_ano_port.gprj');root=project.getroot();filelist=root.find('FileList');filelist.clear()
    entries=[('impl/gwsynthesis/acg720_ano_port.vg','file.netlist'),('acg720_ano_port.cst','file.cst'),('acg720_ano_port.sdc','file.sdc')]
    for path,kind in entries:ET.SubElement(filelist,'File',dict(path=path,type=kind,enable='1'))
    physical_project=SOURCE/'physical.gprj';physical_project.write_bytes(b'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE gowin-fpga-project>\n'+ET.tostring(root,encoding='utf-8'))
    raw=physical_project.read_bytes();assert raw.count(b'<?xml')==1
    assert [(f.attrib['path'],f.attrib['type']) for f in ET.fromstring(raw).find('FileList')]==entries
    write('project_serialization_check.json',{'passed':True,'xml_declarations':1,'exact_netlist_constraints_project':True,'project_sha256':sha(physical_project)})
    lines=(SOURCE/'build.tcl').read_text().splitlines();assert lines.count('run all')==1 and lines.count('exit')==1
    replacements={'run all':'run pnr','open_project acg720_ano_port.gprj':'open_project physical.gprj','set_option -place_option 3':f'set_option -place_option {PLACE}'}
    tcl='\n'.join(replacements.get(line,line) for line in lines if line.strip()!='exit')+'\nputs PHYSICAL_COMMAND_RETURNED_EOF\nflush stdout\n'
    for option,value in [('place_option',str(PLACE)),('route_option','0'),('timing_driven','1'),('map_option','2'),('replicate_resources','0'),('user_code','0000B0B4')]:assert re.findall(r'^set_option -'+option+r'\s+(\S+)\s*$',tcl,re.M)==[value]
    assert 'run syn' not in tcl and 'run all' not in tcl and 'inc_pnr' not in tcl
    execution=ATTEMPT/'physical.tcl';execution.write_text(tcl,encoding='utf8')
    common={'scope':'Fresh exact-VG v9 physical-only trial; no synthesis/hardware; source override is v9.',
      'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'canonical_override':str(CANON),'source_sha256':expected,
      'original_B4_source55':original,'v4_source55':prior,'source_freeze_sha256':sha(O/'source_freeze.json'),'runner_sha256':sha(Path(__file__)),
      'imported_helper_sha256':HELPER_SHA,'donor':str(DONOR),'donor_netlist_sha256':VG_SHA,'donor_evidence':bound,
      'physical_options':{'place':PLACE,'route':0,'map_option':2,'replicate_resources':0,'timing_driven':1},'period_ns':20,'usercode':'0000B0B4',
      'project_sha256':sha(physical_project),'tcl_sha256':sha(execution),'tools':{str(helper.GOWIN):sha(helper.GOWIN)}}
    write('build_input.json',common);write('physical_input.json',common)
    helper.run_phase('physical',[str(helper.GOWIN),str(execution)],SOURCE,expected)
    result=helper.physical_audit(VG_SHA,expected);helper.check_sources(expected)
    assert hash55(ORIGINAL,expected)==original and hash55(PRIOR,expected)==prior and sha(donor_vg)==VG_SHA and sha(HELPER)==HELPER_SHA
    assert {str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in evidence}==bound
    write('build_result.json',{'passed':True,'scope':'Physical artifact gate only; functional equivalence/hardware acceptance separate.',
      'source_sha256':expected,'canonical_override':str(CANON),'netlist_sha256':VG_SHA,'original_B4_source55_unchanged':True,'v4_source55_unchanged':True,
      'physical_options':common['physical_options'],'physical_audit_sha256':sha(VERIFY/'physical_audit.json'),'donor_evidence_unchanged':True,
      'physical_exit_sha256':sha(VERIFY/'physical_exit.json'),'bitstream_sha256':sha(SOURCE/'impl/pnr/acg720_ano_port.fs'),'checks':result['checks'],'fmax_mhz':result['fmax_mhz']})
    print(f'compact_aw_v9 exact-VG P{PLACE}/R0 full physical gate PASS',flush=True)
if __name__=='__main__':
    try:main()
    except BaseException as exc:
        if OWNED and VERIFY.exists():write('build_failure.json',{'passed':False,'exception':repr(exc),'traceback':traceback.format_exc()})
        raise
