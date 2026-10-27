"""Single deferred fan100 donor P3/R0 netlist-only physical trial; main owns slot."""
from pathlib import Path
import datetime,hashlib,importlib.util,json,os,shutil,sys,traceback,xml.etree.ElementTree as ET
sys.dont_write_bytecode=True
assert len(sys.argv)==2 and sys.argv[1]=='3'
O=Path(__file__).resolve().parent;R=O.parents[3];ROOT=R/'out/z_aw_fix_20261026/compact_aw_v22_fan100'
CANON=R/'out/z_aw_fix_20261026/compact_aw_v22/canonical/source';DONOR=ROOT/'build_attempt_01';ATTEMPT=ROOT/'physical_p3r0_01';SOURCE=ATTEMPT/'source';VERIFY=ATTEMPT/'verification'
OWNED=False
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
def write(n,j):(VERIFY/n).write_text(json.dumps(j,indent=2)+'\n',encoding='utf8')
def main():
    global OWNED
    from physical_input_contract import validate_physical
    from physical_recipe import make_physical_recipe
    base=validate_physical(require_review=True);expected=base['source55'];VG=base['VG_sha256']
    assert not ATTEMPT.exists() and not (ROOT/'canonical').exists()
    helper_path=R/'firmware/B0B4/build_candidate.py';assert sha(helper_path)=='abb5246c203b73c111f80bc91f8db6c8220463f7d4c5cf48dbfe2167ef49db84'
    spec=importlib.util.spec_from_file_location('unchanged_original_full_physical_gates',helper_path);helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    helper.CANON=CANON;helper.ATTEMPT=ATTEMPT;helper.SOURCE=SOURCE;helper.VERIFY=VERIFY
    b3=read(R/'firmware/B0B3/qualification.json')['source_sha256'];helper.EXPECTED_CHANGES={n:h for n,h in expected.items() if h!=b3[n]};assert len(helper.EXPECTED_CHANGES)==12
    paths=list(map(Path,base['bound_inputs']))+[helper_path,O/'PHYSICAL_INPUT_BINDING.json',O/'PHYSICAL_PREPARATION.json',O/'PHYSICAL_TCL_PREFLIGHT.json',O/'PHYSICAL_REVIEW_GATE.json',*[O/n for n in read(O/'PHYSICAL_PREPARATION.json')['new_scripts_sha256']]]
    paths=list(dict.fromkeys(paths));bound={str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in paths}
    ATTEMPT.mkdir(parents=True);OWNED=True;shutil.copytree(CANON,SOURCE);VERIFY.mkdir();tmp=VERIFY/'tmp';tmp.mkdir();os.environ.update(TMP=str(tmp),TEMP=str(tmp),TMPDIR=str(tmp))
    shutil.copy2(Path(__file__),VERIFY/'executed_run_physical.py')
    write('donor_evidence_binding.json',{'passed':True,'source55':expected,'vg_sha256':VG,'artifacts':bound,'scope':base['scope']})
    write('functional_evidence_binding.json',{'passed':True,'standard_source_proof_origin':base['standard_source_proof_origin'],'guard_binding_sha256':base['guard_binding_sha256'],'whole55_STD22_unchanged':True,'original_TEMP_compile1_root1_preserved':True,'alias_retry0_completion0':True,'successful_fresh_proof_receipts':22,'scope':base['functional_scope'],'component_scope':base['component_scope'],'controller_scope':base['controller_scope']})
    vg=SOURCE/'impl/gwsynthesis/acg720_ano_port.vg';vg.parent.mkdir(parents=True);shutil.copy2(DONOR/'source/impl/gwsynthesis/acg720_ano_port.vg',vg);assert sha(vg)==VG
    project=ET.parse(SOURCE/'acg720_ano_port.gprj');root=project.getroot();files=root.find('FileList');files.clear()
    entries=[('impl/gwsynthesis/acg720_ano_port.vg','file.netlist'),('acg720_ano_port.cst','file.cst'),('acg720_ano_port.sdc','file.sdc')]
    for path,kind in entries:ET.SubElement(files,'File',dict(path=path,type=kind,enable='1'))
    p=SOURCE/'physical.gprj';p.write_bytes(b'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE gowin-fpga-project>\n'+ET.tostring(root,encoding='utf-8'))
    assert p.read_bytes().count(b'<?xml')==1 and [(f.attrib['path'],f.attrib['type']) for f in ET.fromstring(p.read_bytes()).find('FileList')]==entries
    write('project_serialization_check.json',{'passed':True,'xml_declarations':1,'exact_netlist_constraints_project':True,'project_sha256':sha(p)})
    execution=ATTEMPT/'physical.tcl';execution.write_text(make_physical_recipe(SOURCE/'build.tcl'),encoding='utf8',newline='\n')
    write('build_input.json',{'source_sha256':expected,'canonical_override':str(CANON),'donor':str(DONOR),'donor_netlist_sha256':VG,'original_B4_source55':base['original_B4_source55'],'protected_v4_source55':base['protected_v4_source55'],'baseline_v20_source55':base['baseline_v20_source55'],'imported_helper_sha256':sha(helper_path),'runner_sha256':sha(Path(__file__)),'source_build_Tcl_max_fanout':200,'effective_physical_max_fanout':100,'synthesis_must_be_skipped':True,'physical_options':{'place':3,'route':0,'map_option':2,'replicate_resources':0,'route_maxfan':23,'max_fanout':100},'period_ns':20,'usercode':'0000B0B4'})
    write('physical_input.json',{'source_sha256':expected,'canonical_override':str(CANON),'donor_netlist_sha256':VG,'project_sha256':sha(p),'tcl_sha256':sha(execution),'runner_sha256':sha(Path(__file__))})
    helper.run_phase('physical',[str(helper.GOWIN),str(execution)],SOURCE,expected)
    audit=helper.physical_audit(VG,expected);helper.check_sources(expected)
    assert validate_physical(require_review=True)['passed']
    assert {str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in paths}==bound
    write('build_result.json',{'passed':True,'source_sha256':expected,'netlist_sha256':VG,'physical_audit_sha256':sha(VERIFY/'physical_audit.json'),'physical_exit_sha256':sha(VERIFY/'physical_exit.json'),'bitstream_sha256':sha(SOURCE/'impl/pnr/acg720_ano_port.fs'),'fmax_mhz':audit['fmax_mhz'],'checks':audit['checks'],'scope':'Full original physical artifact/50MHz gate only; no hardware qualification.'})
    print('fan100 P3/R0 full original physical gate PASS',flush=True)
if __name__=='__main__':
    try:main()
    except BaseException as e:
        if OWNED and VERIFY.is_dir():write('build_failure.json',{'passed':False,'exception':repr(e),'traceback':traceback.format_exc()})
        raise
