"""Actual v18 SYN-only process and strict mapped audit; no PNR or hardware."""
from pathlib import Path
import hashlib,importlib.util,json,os,shutil,sys,traceback
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;R=O.parents[3];ROOT=R/'out/z_aw_fix_20261026/compact_aw_v18'
C=ROOT/'canonical/source';A=ROOT/'build_attempt_01';S=A/'source';V=A/'verification';OWNED=False
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
def write(name,data):(V/name).write_text(json.dumps(data,indent=2)+'\n',encoding='utf8')
def main():
    global OWNED
    assert not A.exists()
    freeze=read(O/'source_freeze.json');expected=freeze['source55'];proof=read(O/'PROOF_BINDING.json');reuse=read(O/'REUSED_BINDINGS_RECHECK.json')
    assert proof['passed'] and proof['source55']==expected and proof['actual_proof_runner_wait']==0
    vy=read(O/'VY_BINDING.json');assert vy['passed'] and vy['source55']==expected and vy['result_sha256']==sha(O/'vy_proofs/RESULT.json') and proof['vy_binding_sha256']==sha(O/'VY_BINDING.json')
    assert reuse['passed'] and reuse['source55']==expected and reuse['new_v18_proof_binding_sha256']==sha(O/'PROOF_BINDING.json')
    assert len(expected)==55 and {n:sha(C/n) for n in expected}==expected
    assert sha(O/'source_review.md')==freeze['source_review_sha256']
    original=read(R/'analysis/20261026_z_aw_fix/handoff_20261026/SOURCE_BINDINGS.json')['source_sha256']['B0B4_unpromoted_prototype']
    assert {n:sha(R/'firmware/B0B4/source'/n) for n in original}==original
    helper_path=R/'firmware/B0B4/build_candidate.py';assert sha(helper_path)=='abb5246c203b73c111f80bc91f8db6c8220463f7d4c5cf48dbfe2167ef49db84'
    spec=importlib.util.spec_from_file_location('v18_original_process_gates',helper_path);h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
    h.CANON=C;h.ATTEMPT=A;h.SOURCE=S;h.VERIFY=V
    b3=read(R/'firmware/B0B3/qualification.json')['source_sha256'];h.EXPECTED_CHANGES={n:x for n,x in expected.items() if x!=b3[n]};assert len(h.EXPECTED_CHANGES)==10
    bound={str(p):sha(p) for p in [Path(__file__),O/'audit_synthesis_only.py',O/'source_freeze.json',O/'source_review.md',O/'PROOF_BINDING.json',O/'REUSED_BINDINGS_RECHECK.json',O/'SYNTHESIS_PREPARATION.json',helper_path]}
    A.mkdir(parents=True);OWNED=True;shutil.copytree(C,S);V.mkdir();tmp=V/'tmp';tmp.mkdir();os.environ.update(TMP=str(tmp),TEMP=str(tmp),TMPDIR=str(tmp))
    shutil.copy2(Path(__file__),V/'executed_run_synthesis.py');shutil.copy2(O/'audit_synthesis_only.py',V/'executed_audit_synthesis_only.py')
    lines=(S/'build.tcl').read_text(encoding='utf8').splitlines();assert lines.count('run all')==lines.count('exit')==1
    tcl='\n'.join('run syn' if line=='run all' else line for line in lines if line.strip()!='exit')+'\nputs SYNTHESIS_COMMAND_RETURNED_EOF\nflush stdout\n'
    assert 'run pnr' not in tcl and 'run all' not in tcl
    execution=A/'synth_only.tcl';execution.write_text(tcl,encoding='utf8')
    write('build_input.json',{'scope':'Actual v18 full-top SYN_ONLY and strict post-SYN audit. No PNR.',
        'source_sha256':expected,'original_B4_source55':original,'canonical_override':str(C),'bound_inputs':bound,
        'synthesis_options':{'map_option':2,'replicate_resources':0,'max_fanout':200,'opt_goal':'area'},
        'tools':{str(p):sha(p) for p in [h.GOWIN,h.GRAPH_READER,h.PRIMITIVES]}})
    write('synthesis_input.json',{'source_sha256':expected,'execution_tcl_sha256':sha(execution),'runner_sha256':sha(Path(__file__))})
    h.run_phase('synthesis',[str(h.GOWIN),str(execution)],S,expected)
    assert 'SYNTHESIS_COMMAND_RETURNED_EOF' in (V/'synthesis.log').read_text(encoding='utf8',errors='replace')
    h.run_phase('audit',[sys.executable,'-B','-X','utf8',str(O/'audit_synthesis_only.py')],S,expected)
    audit=read(V/'native_synthesis_audit.json');assert audit['passed'] and audit['source55']==expected
    assert not (S/'impl/pnr').exists()
    assert {str(p):sha(p) for p in map(Path,bound)}==bound
    h.check_sources(expected)
    write('synthesis_summary.json',{'passed':True,'scope':'Actual SYN_ONLY and mapped/clock/radio/gain/18port audit; not physical acceptance.',
        'actual_p_wait':0,'source_sha256':expected,'netlist_sha256':audit['netlist_sha256'],
        'synthesis_exit_sha256':sha(V/'synthesis_exit.json'),'mapped_audit_sha256':sha(V/'mapped_audit.json'),
        'gain_port_audit_sha256':sha(V/'gain_port_audit.json'),'strict_ff_clock_audit_sha256':sha(V/'strict_ff_clock_audit.json'),
        'resource_comparison_sha256':sha(V/'resource_comparison.json'),'audit_actual_p_wait':read(V/'audit_exit.json')['actual_p_wait']})
    print(json.dumps({'SYN_only_passed':True,'netlist_sha256':audit['netlist_sha256'],'actual_vendor_wait':0,'actual_audit_wait':0,'PNR_started':False}))
if __name__=='__main__':
    try:main()
    except BaseException as e:
        if OWNED and V.is_dir():write('build_failure.json',{'passed':False,'error':repr(e),'traceback':traceback.format_exc()})
        raise
