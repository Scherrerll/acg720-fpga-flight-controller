"""One actual same-source STD22 SYN-only option trial; never prepares or runs PNR."""
from pathlib import Path
import hashlib,importlib.util,json,os,shutil,sys,traceback
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;R=O.parents[3];STANDARD=O.parent/'compact_aw_v22'
ROOT=R/'out/z_aw_fix_20261026/compact_aw_v22_fan100';C=R/'out/z_aw_fix_20261026/compact_aw_v22/canonical/source'
A=ROOT/'build_attempt_01';S=A/'source';V=A/'verification';OWNED=False
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
def write(n,j):(V/n).write_text(json.dumps(j,indent=2)+'\n',encoding='utf8')
def main():
    global OWNED
    from input_contract import validate,review_gate
    from effective_recipe import make_recipe
    base=validate();review_gate();expected=base['source55']
    assert not A.exists() and not (ROOT/'canonical').exists()
    helper=R/'firmware/B0B4/build_candidate.py';assert sha(helper)=='abb5246c203b73c111f80bc91f8db6c8220463f7d4c5cf48dbfe2167ef49db84'
    spec=importlib.util.spec_from_file_location('unchanged_SYN_process_helper',helper);h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
    h.CANON=C;h.ATTEMPT=A;h.SOURCE=S;h.VERIFY=V
    b3=read(R/'firmware/B0B3/qualification.json')['source_sha256'];h.EXPECTED_CHANGES={n:x for n,x in expected.items() if x!=b3[n]};assert len(h.EXPECTED_CHANGES)==12
    bound={str(p):sha(p) for p in [helper,O/'SOURCE_REUSE_BINDING.json',O/'source_freeze.json',O/'SYNTHESIS_PREPARATION.json',O/'SYN_REVIEW_GATE.json',*[O/n for n in read(O/'SYNTHESIS_PREPARATION.json')['scripts_sha256']]]}
    bound.update(read(O/'SOURCE_REUSE_BINDING.json')['bound_inputs'])
    A.mkdir(parents=True);OWNED=True;shutil.copytree(C,S);V.mkdir();tmp=V/'tmp';tmp.mkdir();os.environ.update(TMP=str(tmp),TEMP=str(tmp),TMPDIR=str(tmp))
    shutil.copy2(Path(__file__),V/'executed_run_synthesis.py');shutil.copy2(O/'audit_synthesis_only.py',V/'executed_audit_synthesis_only.py')
    execution=A/'synth_only.tcl';execution.write_text(make_recipe(S/'build.tcl'),encoding='utf8',newline='\n')
    write('build_input.json',{'scope':'Actual same55 STD22 SYN_ONLY; sole option delta max_fanout200->100; original copied build.tcl stays byte-exact200. No RTL rerun, PNR or hardware.',
        'canonical_override':str(C),'standard_source_proof_origin':str(STANDARD),'source_sha256':expected,'guard_binding_sha256':base['guard_binding_sha256'],
        'parent_VG_sha256':base['VG_sha256'],'effective_option_delta':{'max_fanout':{'from':200,'to':100}},'bound_inputs':bound,
        'synthesis_options':{'map_option':2,'replicate_resources':0,'max_fanout':100,'opt_goal':'area'},'tools':{str(p):sha(p) for p in [h.GOWIN,h.GRAPH_READER,h.PRIMITIVES]}})
    write('synthesis_input.json',{'source_sha256':expected,'execution_tcl_sha256':sha(execution),'runner_sha256':sha(Path(__file__))})
    h.run_phase('synthesis',[str(h.GOWIN),str(execution)],S,expected)
    assert 'SYNTHESIS_COMMAND_RETURNED_EOF' in (V/'synthesis.log').read_text(errors='replace')
    h.run_phase('audit',[sys.executable,'-B','-X','utf8',str(O/'audit_synthesis_only.py')],S,expected)
    audit=read(V/'native_synthesis_audit.json');assert audit['passed'] and audit['source55']==expected
    assert not (S/'impl/pnr').exists();h.check_sources(expected);assert validate()['source55']==expected
    for p,d in bound.items():assert sha(Path(p))==d,p
    hashes={n:sha(V/n) for n in ['synthesis_exit.json','audit_exit.json','native_synthesis_audit.json','mapped_audit.json','gain_port_audit.json','strict_ff_clock_audit.json','resource_comparison.json','mapped_fanout_comparison.json']}
    write('synthesis_summary.json',{'passed':True,'source_sha256':expected,'netlist_sha256':audit['netlist_sha256'],'parent_VG_sha256':base['VG_sha256'],
         'actual_vendor_wait':read(V/'synthesis_exit.json')['actual_p_wait'],'actual_audit_wait':read(V/'audit_exit.json')['actual_p_wait'],
         'effective_option_delta':{'max_fanout':{'from':200,'to':100}},'artifacts_sha256':hashes,'PNR_started':False,
         'scope':'Actual completed SYN and strict mapped/source/clock/radio/gain18pin audit only. Resource and pin-load deltas are measured, no benefit/50MHz/routing prediction.'})
    print(json.dumps({'passed_SYN_only':True,'VG':audit['netlist_sha256'],'vendor_wait':0,'audit_wait':0,'PNR_started':False}),flush=True)
if __name__=='__main__':
    try:main()
    except BaseException as e:
        if OWNED and V.is_dir():write('build_failure.json',{'passed':False,'error':repr(e),'traceback':traceback.format_exc()})
        raise
