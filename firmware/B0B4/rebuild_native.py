"""Replay a qualified native RTL-project build in a new directory; no hardware actions."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,shutil,subprocess,sys,traceback,xml.etree.ElementTree as ET
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[1]
FLOW='native_RTL_project_SYN_audit_PNR_one_vendor_process'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
def setup_helper(a,qualification):
    helper_path=ROOT/'build_candidate.py'
    assert sha(helper_path)=='abb5246c203b73c111f80bc91f8db6c8220463f7d4c5cf48dbfe2167ef49db84'
    helper=load('native_replay_original_gates',helper_path)
    helper.CANON=ROOT/'source';helper.ATTEMPT=a;helper.SOURCE=a/'source';helper.VERIFY=a/'verification'
    replay=qualification['replay_support']
    helper.RUNTIME=ROOT/replay['runtime_reference_root'];helper.GRAPH_READER=ROOT/replay['graph_reader']
    assert sha(helper.GRAPH_READER)==replay['graph_sha256']
    baseline=helper.RUNTIME/'candidates/idle_gain_integral_ce/source/impl/gwsynthesis/acg720_ano_port_syn_rsc.xml'
    assert sha(baseline)==replay['reference_resource_sha256']
    assert sha(ROOT/replay['gain_auditor'])==replay['gain_auditor_sha256']
    assert sha(ROOT/replay['parent_resource_xml'])==replay['parent_resource_sha256']
    return helper
def audit_phase(a):
    q=read(ROOT/'qualification.json');assert q['passed'] and q['workflow']==FLOW
    helper=setup_helper(a,q);s=helper.SOURCE;v=helper.VERIFY;expected=q['source_sha256']
    helper.check_sources(expected)
    project=s/'acg720_ano_port.gprj';files=[f.attrib for f in ET.parse(project).findall('.//File')]
    assert any(f.get('type')=='file.verilog' and f.get('enable')=='1' for f in files)
    assert not any(f.get('type')=='file.netlist' for f in files)
    vg=s/'impl/gwsynthesis/acg720_ano_port.vg';assert vg.is_file()
    helper.mapped_audit(vg,expected)
    auditor=load('native_replay_original_gain_ports',ROOT/q['replay_support']['gain_auditor'])
    auditor.SOURCE=s;auditor.VERIFY=v;auditor.extended_audit(helper,vg)
    graph_module=load('native_replay_original_clock_graph',helper.GRAPH_READER);g=graph_module.Graph(vg)
    clocks=[c['pins']['O'][0] for c in g.cells.values() if c['type']=='IBUF' and c['pins'].get('I')==['clk50']]
    assert len(clocks)==1
    bad=[{'cell':n,'CLK':p.get('CLK',[])} for n,p in g.regs.items() if len(p.get('CLK',[]))!=1 or g.find(p['CLK'][0])!=g.find(clocks[0])]
    (v/'strict_ff_clock_audit.json').write_text(json.dumps({'passed':not bad,'all_FF_CLK50':not bad,'bad':bad,'FF_count':len(g.regs),'vg_sha256':sha(vg)},indent=2)+'\n')
    assert not bad
    helper.check_sources(expected)
    result={'passed':True,'source55':expected,'netlist_sha256':sha(vg),'project_sha256':sha(project),'project_filelist':files,
        'scope':'Executed native replay mapped-artefact audit. No standalone compiler process wait is claimed.',
        'mapped_audit_sha256':sha(v/'mapped_audit.json'),'gain_port_audit_sha256':sha(v/'gain_port_audit.json'),
        'strict_ff_clock_audit_sha256':sha(v/'strict_ff_clock_audit.json'),'hook_sha256':sha(Path(__file__))}
    (v/'native_synthesis_audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print('NATIVE_REPLAY_SYNTHESIS_AUDIT_PASS '+sha(vg),flush=True)
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path,help='A new directory beneath repository out/')
    parser.add_argument('--verify-only',action='store_true',help='Check saved replay inputs without compiling or creating a directory')
    parser.add_argument('--audit-phase',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args();a=args.output.resolve()
    assert a.is_relative_to((REPO/'out').resolve()) and a!=(REPO/'out').resolve()
    if args.audit_phase:audit_phase(a);return
    subprocess.run([sys.executable,'-B',str(ROOT/'verify_release.py')],cwd=REPO,check=True)
    q=read(ROOT/'qualification.json');assert q['passed'] and q['workflow']==FLOW
    assert not a.exists(),'Never overwrite an existing implementation'
    expected=q['source_sha256'];assert len(expected)==55
    helper=setup_helper(a,q)
    selected=ROOT/'evidence/selected';terminal=read(selected/'TERMINAL_MANIFEST.json');review=read(selected/'INDEPENDENT_RAW_REVIEW.json')
    assert terminal['passed'] and terminal['vendor_actual_p_wait']==terminal['runner_actual_p_wait']==0
    assert review['passed'] and all(review['checks'].values()) and terminal['source55']==expected
    tcl=(selected/'physical.tcl').read_text(encoding='utf8')
    lines=tcl.splitlines();indices=[i for i,line in enumerate(lines) if line.startswith('if {[catch {exec ') and 'audit_failure' in line]
    assert len(indices)==1 and 'run syn' in lines and 'run pnr' in lines
    py=Path(sys.executable).as_posix();script=Path(__file__).as_posix();output=a.as_posix()
    assert not any(c in py+script+output for c in '{}\r\n')
    lines[indices[0]]=f'if {{[catch {{exec {{{py}}} -B -X utf8 {{{script}}} --output {{{output}}} --audit-phase}} audit_failure]}} {{'
    replay_tcl='\n'.join(lines)+'\n'
    if args.verify_only:
        print(json.dumps({'verified':True,'workflow':FLOW,'source_files':55,'replay_dependencies_checked':True,
                          'new_compilation_or_PNR_performed':False,'output_created':False,'hardware_operation':False}));return
    assert sha(helper.GOWIN)==q['tools'][str(helper.GOWIN)],'Install the qualified Gowin binary before replay'
    a.mkdir(parents=True);shutil.copytree(ROOT/'source',a/'source');v=a/'verification';v.mkdir();tmp=v/'tmp';tmp.mkdir()
    os.environ.update(TMP=str(tmp),TEMP=str(tmp),TMPDIR=str(tmp))
    shutil.copy2(Path(__file__),v/'executed_rebuild_native.py')
    execution=a/'physical.tcl';execution.write_text(replay_tcl,encoding='utf8')
    (v/'replay_input.json').write_text(json.dumps({'workflow':FLOW,'source55':expected,'qualification_sha256':sha(ROOT/'qualification.json'),
        'archived_recipe_sha256':sha(selected/'physical.tcl'),'execution_recipe_sha256':sha(execution),
        'recipe_change':'Only the audit-hook exec line uses this replay hook with packaged original dependencies. All compiler and physical options remain from the archived actual recipe.',
        'scope':'New source implementation; all gates must pass again. The published bitstream and hardware are untouched.'},indent=2)+'\n')
    try:
        helper.run_phase('physical',[str(helper.GOWIN),str(execution)],a/'source',expected)
        syn=read(v/'native_synthesis_audit.json');assert syn['passed'] and syn['source55']==expected
        auditor=load('native_replay_physical_gates',selected/'native_physical_audit.py')
        auditor.SOURCE=a/'source';auditor.VERIFY=v;auditor.ATTEMPT=a
        result=auditor.physical_audit(syn['netlist_sha256'],expected);helper.check_sources(expected)
        (v/'rebuild_result.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({'physical_gate_passed':result['passed'],'fmax_mhz':result['fmax_mhz'],'hardware_operation':False,
                          'scope':'This new implementation result needs its own independent raw review; no release promotion performed.'}))
    except BaseException as error:
        (v/'rebuild_failure.json').write_text(json.dumps({'passed':False,'error':repr(error),'traceback':traceback.format_exc()},indent=2)+'\n');raise
if __name__=='__main__':main()
