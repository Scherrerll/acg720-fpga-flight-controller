"""Fresh native RTL-project SYN/audit/PNR in one real gw_sh process; no hardware."""
from pathlib import Path
import hashlib, importlib.util, json, os, shutil, sys, traceback, xml.etree.ElementTree as ET
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;R=O.parents[3]
assert len(sys.argv)==2 and sys.argv[1] in ['2','3'];PLACE=int(sys.argv[1]);LABEL=f'physical_p{PLACE}r0_01'
ROOT=R/'out/z_aw_fix_20261026/compact_aw_v4_native';CANON=ROOT/'canonical/source'
A=ROOT/LABEL;S=A/'source';V=A/'verification';ORIGINAL=R/'firmware/B0B4/source'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
def write(name,data):(V/name).write_text(json.dumps(data,indent=2)+'\n',encoding='utf8')
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
OWNED=False
def build_tcl(lines,place):
    assert lines.count('run all')==lines.count('exit')==1 and lines.count('open_project acg720_ano_port.gprj')==1
    py=Path(sys.executable).as_posix();hook=(O/'audit_synthesis.py').as_posix()
    assert not any(c in py+hook for c in '{}\r\n')
    stage='\n'.join(['run syn','puts SYNTHESIS_COMMAND_RETURNED_EOF','flush stdout',
        f'if {{[catch {{exec {{{py}}} -B -X utf8 {{{hook}}} {place}}} audit_failure]}} {{',
        '  puts stderr "NATIVE_SYNTHESIS_AUDIT_REJECTED $audit_failure"','  exit 97','}',
        'puts SYNTHESIS_AUDIT_RETURNED_EOF','flush stdout','run pnr',
        'puts PHYSICAL_COMMAND_RETURNED_EOF','flush stdout'])
    tcl='\n'.join(stage if line=='run all' else f'set_option -place_option {place}' if line=='set_option -place_option 3' else line
                  for line in lines if line.strip()!='exit')+'\n'
    assert 'open_project physical.gprj' not in tcl and 'run all' not in tcl and 'set_option -global_freq 50' in tcl
    return tcl
def main():
    global OWNED
    assert not A.exists(),'Never overwrite build evidence'
    freeze=read(O/'source_freeze.json');expected=freeze['source55']
    assert len(expected)==55 and {n:sha(CANON/n) for n in expected}==expected
    assert sha(O/'source_review.md')==freeze['source_review_sha256']
    proof=read(O/'PROOF_BINDING.json');parent=O.parent/'v4_release_proofs/RESULT.json'
    assert proof['passed'] and proof['source55']==expected and proof['actual_proof_runner_wait']==0
    assert proof['parent_proof_sha256']==sha(parent) and read(parent)['source55']==expected
    bindings=read(R/'analysis/20261026_z_aw_fix/handoff_20261026/SOURCE_BINDINGS.json')
    original=bindings['source_sha256']['B0B4_unpromoted_prototype']
    assert {n:sha(ORIGINAL/n) for n in original}==original
    b3=read(R/'firmware/B0B3/qualification.json')['source_sha256']
    assert {n:sha(R/'firmware/B0B3/source'/n) for n in b3}==b3
    helper_path=R/'firmware/B0B4/build_candidate.py'
    assert sha(helper_path)=='abb5246c203b73c111f80bc91f8db6c8220463f7d4c5cf48dbfe2167ef49db84'
    helper=load('native_project_original_process_and_source_gates',helper_path)
    helper.CANON=CANON;helper.ATTEMPT=A;helper.SOURCE=S;helper.VERIFY=V
    helper.EXPECTED_CHANGES={n:h for n,h in expected.items() if h!=b3[n]}
    assert len(helper.EXPECTED_CHANGES)==3
    evidence=[O/name for name in ['source_freeze.json','source_review.md','PROOF_BINDING.json','audit_synthesis.py',
                                'native_physical_audit.py','GATE_ADAPTATION.json','run_physical.py']]
    evidence += [parent,helper_path]
    bound={str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in evidence}
    A.mkdir(parents=True);OWNED=True;shutil.copytree(CANON,S);V.mkdir()
    for name in ['run_physical.py','audit_synthesis.py','native_physical_audit.py']:shutil.copy2(O/name,V/('executed_'+name))
    tmp=V/'tmp';tmp.mkdir();os.environ.update(TMP=str(tmp),TEMP=str(tmp),TMPDIR=str(tmp))
    assert not (S/'impl').exists(),'Fresh source copy must not contain cached SYN/PNR outputs'
    helper.check_sources(expected)
    files=[f.attrib for f in ET.parse(S/'acg720_ano_port.gprj').findall('.//File')]
    assert any(f.get('type')=='file.verilog' and f.get('enable')=='1' for f in files)
    assert not any(f.get('type')=='file.netlist' for f in files)
    write('project_serialization_check.json',{'passed':True,'native_original_RTL_project':True,'rewritten_FileList':False,
        'project_sha256':sha(S/'acg720_ano_port.gprj'),'files':files})
    lines=(S/'build.tcl').read_text(encoding='utf8').splitlines()
    tcl=build_tcl(lines,PLACE)
    execution=A/'physical.tcl';execution.write_text(tcl,encoding='utf8')
    common={'scope':'Native original RTL project SYN, successful audit hook, PNR in one real vendor process. No standalone SYN p.wait is claimed.',
        'workflow':'native_RTL_project_SYN_audit_PNR_one_vendor_process','source_sha256':expected,'original_B4_source55':original,
        'canonical_override':str(CANON),'source_freeze_sha256':sha(O/'source_freeze.json'),'runner_sha256':sha(Path(__file__)),
        'project_sha256':sha(S/'acg720_ano_port.gprj'),'tcl_sha256':sha(execution),'period_ns':20,'usercode':'0000B0B4',
        'physical_options':{'place':PLACE,'route':0,'map_option':2,'replicate_resources':0,'timing_driven':1},
        'bound_inputs':bound,'tools':{str(helper.GOWIN):sha(helper.GOWIN)}}
    write('build_input.json',common);write('physical_input.json',common)
    write('donor_evidence_binding.json',{'passed':True,'source55':expected,'artifacts':bound,
        'scope':'Functional/source/runner binding only. New SYN VG is bound by the native audit hook.'})
    helper.run_phase('physical',[str(helper.GOWIN),str(execution)],S,expected)
    syn=read(V/'native_synthesis_audit.json');assert syn['passed'] and syn['source55']==expected
    vg=S/'impl/gwsynthesis/acg720_ano_port.vg';assert sha(vg)==syn['netlist_sha256']
    auditor=load('native_project_physical_gates',O/'native_physical_audit.py')
    auditor.SOURCE=S;auditor.VERIFY=V;auditor.ATTEMPT=A
    result=auditor.physical_audit(sha(vg),expected)
    helper.check_sources(expected)
    assert {n:sha(ORIGINAL/n) for n in original}==original and {n:sha(R/'firmware/B0B3/source'/n) for n in b3}==b3
    assert {str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in evidence}==bound
    write('build_result.json',{'passed':True,'workflow':common['workflow'],'source_sha256':expected,
        'netlist_sha256':sha(vg),'physical_audit_sha256':sha(V/'physical_audit.json'),
        'native_synthesis_audit_sha256':sha(V/'native_synthesis_audit.json'),'bitstream_sha256':sha(S/'impl/pnr/acg720_ano_port.fs'),
        'combined_vendor_actual_wait':0,'checks':result['checks'],'fmax_mhz':result['fmax_mhz'],
        'scope':'Offline native full-flow gate only; independent raw review and hardware acceptance separate.'})
    print('PASS native RTL-project full physical gate',flush=True)
if __name__=='__main__':
    try:main()
    except BaseException as error:
        if OWNED and V.exists():write('build_failure.json',{'passed':False,'error':repr(error),'exception':repr(error),'traceback':traceback.format_exc()})
        raise
