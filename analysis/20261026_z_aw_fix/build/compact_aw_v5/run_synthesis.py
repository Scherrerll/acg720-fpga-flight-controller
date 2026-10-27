"""Fresh compact-AW-v5 map2 full-top elaboration/SYN only; never PNR."""
from pathlib import Path
import hashlib,importlib.util,json,os,re,shutil,traceback,xml.etree.ElementTree as ET
O=Path(__file__).resolve().parent;R=O.parents[3];ROOT=R/'out/z_aw_fix_20261026/compact_aw_v5'
CANON=ROOT/'canonical/source';ATTEMPT=ROOT/'build_attempt_01';SOURCE=ATTEMPT/'source';VERIFY=ATTEMPT/'verification'
PRIOR=R/'out/z_aw_fix_20261026/compact_aw_v4';ORIGINAL=R/'firmware/B0B4/source'
HELPER=R/'firmware/B0B4/build_candidate.py';AUDIT_HELPER=R/'analysis/20261026_z_aw_fix/build/compact_aw_v2/run_synthesis.py'
HELPER_SHA='abb5246c203b73c111f80bc91f8db6c8220463f7d4c5cf48dbfe2167ef49db84'
AUDIT_SHA='23fe046b259c6713536fc27862eb80a3b392808a77e842aac2085c3f91f3d658'
HOLD_SHA='04e75ada52551d5622af060efe38fda9aa66ff25199bfb67651f9ec5315ed873'
OWNED=False
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,value):(VERIFY/name).write_text(json.dumps(value,indent=2)+'\n')
def hash55(root,paths):return {p:sha(root/p) for p in paths}
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def main():
    global OWNED
    assert not ATTEMPT.exists(),'Never overwrite stage evidence'
    assert sha(HELPER)==HELPER_SHA and sha(AUDIT_HELPER)==AUDIT_SHA
    freeze=json.loads((O/'source_freeze.json').read_text());expected=freeze['source55']
    assert len(expected)==55 and expected['position/mtf_xyz_hold_control.v']==HOLD_SHA
    prior=hash55(PRIOR/'canonical/source',expected);original=hash55(ORIGINAL,expected)
    assert prior['position/mtf_xyz_hold_control.v']=='ffddb029cb34a8d2ac8995cc43d85866e273d3d147bb650cfd5d3c66c580b642'
    assert [p for p in expected if expected[p]!=prior[p]]==['position/mtf_xyz_hold_control.v']
    assert hash55(CANON,expected)==expected
    pinput=json.loads((PRIOR/'build_attempt_01/verification/build_input.json').read_text())
    psummary=json.loads((PRIOR/'build_attempt_01/verification/synthesis_summary.json').read_text())
    pexit=json.loads((PRIOR/'build_attempt_01/verification/synthesis_exit.json').read_text())
    assert pinput['synthesis_options']=={'map_option':2,'replicate_resources':0}
    assert psummary['passed'] is True and psummary['actual_p_wait']==pexit['actual_p_wait']==0 and psummary['source_sha256']==prior
    helper=load('v5_original_vendor_gates',HELPER)
    helper.CANON=CANON;helper.ATTEMPT=ATTEMPT;helper.SOURCE=SOURCE;helper.VERIFY=VERIFY
    helper.EXPECTED_CHANGES={**helper.EXPECTED_CHANGES,'position/mtf_xyz_hold_control.v':HOLD_SHA}
    baseline=json.loads((R/'firmware/B0B3/qualification.json').read_text())['source_sha256']
    assert expected.keys()==baseline.keys() and {p:expected[p] for p in expected if expected[p]!=baseline[p]}==helper.EXPECTED_CHANGES
    ATTEMPT.mkdir(parents=True);OWNED=True;shutil.copytree(CANON,SOURCE);VERIFY.mkdir()
    tmp=VERIFY/'tmp';tmp.mkdir();os.environ.update(TMP=str(tmp),TEMP=str(tmp),TMPDIR=str(tmp))
    write('build_input.json',{'scope':'Independent compact_aw_v5 fulltop/map2 SYN only; no PNR or hardware.',
      'canonical_override':str(CANON),'source_directory':str(SOURCE),'source_sha256':expected,'baseline_v4_map2_source55':prior,
      'original_B4_source55':original,'changed_from_v4':['position/mtf_xyz_hold_control.v'],'source_freeze_sha256':sha(O/'source_freeze.json'),
      'source_review_sha256':sha(O/'source_review.md'),'runner_sha256':sha(Path(__file__)),'imported_helper_sha256':HELPER_SHA,
      'imported_gain_port_audit_sha256':AUDIT_SHA,'reference_v4_map2_build_input_sha256':sha(PRIOR/'build_attempt_01/verification/build_input.json'),
      'synthesis_options':{'map_option':2,'replicate_resources':0},'usercode':'0000B0B4',
      'tools':{str(p):sha(p) for p in [helper.GOWIN,helper.IVERILOG,helper.PRIMITIVES,helper.GRAPH_READER]}})
    helper.check_sources(expected)
    project=ET.parse(SOURCE/'acg720_ano_port.gprj')
    files=[f.attrib['path'] for f in project.findall('.//File') if f.attrib.get('type')=='file.verilog' and f.attrib.get('enable')=='1']
    helper.run_phase('elaboration',[str(helper.IVERILOG),'-g2012','-s','acg720_ano_port','-I',str(SOURCE),'-o',str(VERIFY/'top.vvp'),*files,str(helper.PRIMITIVES)],SOURCE,expected)
    lines=(SOURCE/'build.tcl').read_text().splitlines();assert lines.count('run all')==1 and lines.count('exit')==1
    tcl='\n'.join('run syn' if line=='run all' else line for line in lines if line.strip()!='exit')+'\nputs SYNTHESIS_COMMAND_RETURNED_EOF\nflush stdout\n'
    assert re.findall(r'^set_option -map_option\s+(\S+)\s*$',tcl,re.M)==['2']
    assert re.findall(r'^set_option -replicate_resources\s+(\S+)\s*$',tcl,re.M)==['0']
    assert 'run pnr' not in tcl and 'run all' not in tcl
    execution=ATTEMPT/'synth_only.tcl';execution.write_text(tcl,encoding='utf8')
    write('synthesis_input.json',{'source_sha256':expected,'canonical_override':str(CANON),'execution_tcl_sha256':sha(execution),
      'runner_sha256':sha(Path(__file__)),'imported_helper_sha256':HELPER_SHA,'tool_sha256':sha(helper.GOWIN)})
    receipt=helper.run_phase('synthesis',[str(helper.GOWIN),str(execution)],SOURCE,expected)
    assert receipt['actual_p_wait']==0 and 'SYNTHESIS_COMMAND_RETURNED_EOF' in (VERIFY/'synthesis.log').read_text(errors='replace')
    vg=SOURCE/'impl/gwsynthesis/acg720_ano_port.vg';assert vg.is_file()
    helper.mapped_audit(vg,expected)
    auditor=load('v5_imported_v2_gain_port_audit',AUDIT_HELPER);auditor.SOURCE=SOURCE;auditor.VERIFY=VERIFY
    auditor.extended_audit(helper,vg)
    gm=load('v5_strict_clock_graph',helper.GRAPH_READER);g=gm.Graph(vg)
    clocks=[c['pins']['O'][0] for c in g.cells.values() if c['type']=='IBUF' and c['pins'].get('I')==['clk50']];assert len(clocks)==1
    bad=[{'cell':n,'CLK':p.get('CLK',[])} for n,p in g.regs.items() if len(p.get('CLK',[]))!=1 or g.find(p['CLK'][0])!=g.find(clocks[0])]
    write('strict_ff_clock_audit.json',{'passed':not bad,'FF_count':len(g.regs),'all_FF_CLK50':not bad,'bad':bad,'vg_sha256':sha(vg)})
    assert not bad
    current=SOURCE/'impl/gwsynthesis/acg720_ano_port_syn_rsc.xml';priorxml=PRIOR/'build_attempt_01/source/impl/gwsynthesis/acg720_ano_port_syn_rsc.xml'
    old,new=auditor.resources(priorxml),auditor.resources(current)
    names=['acg720_ano_port','acg720_ano_port/native_navigation/controller_proof','acg720_ano_port/parameters']
    comparison={n:{'baseline_v4_map2':old[n],'candidate_v5_map2':new[n],'delta':{k:new[n].get(k,0)-old[n].get(k,0) for k in old[n].keys()|new[n].keys()}} for n in names}
    write('resource_comparison.json',{'scope':'Actual map2 vs map2 resources only; no route/STA claim.','baseline_v4_xml_sha256':sha(priorxml),'candidate_v5_xml_sha256':sha(current),
      'reference_v4_map2_build_input_sha256':sha(PRIOR/'build_attempt_01/verification/build_input.json'),'candidate_v5_vg_sha256':sha(vg),'resources':comparison})
    helper.check_sources(expected);assert hash55(PRIOR/'canonical/source',expected)==prior and hash55(ORIGINAL,expected)==original
    assert sha(HELPER)==HELPER_SHA and sha(AUDIT_HELPER)==AUDIT_SHA
    write('synthesis_summary.json',{'passed':True,'scope':'Elaboration/SYN/clock-radio-gain-18ports only; no PNR qualification.',
      'actual_p_wait':0,'canonical_override':str(CANON),'source_sha256':expected,'netlist_sha256':sha(vg),
      'v4_canonical_source55_unchanged':True,'original_B4_source55_unchanged':True,'variant_source55_unchanged':True,
      'synthesis_exit_sha256':sha(VERIFY/'synthesis_exit.json'),'mapped_audit_sha256':sha(VERIFY/'mapped_audit.json'),
      'gain_port_audit_sha256':sha(VERIFY/'gain_port_audit.json'),'strict_ff_clock_audit_sha256':sha(VERIFY/'strict_ff_clock_audit.json'),
      'resource_comparison_sha256':sha(VERIFY/'resource_comparison.json'),'resources':comparison})
    print(json.dumps({'synthesis_only_pass':True,'vg_sha256':sha(vg),'resources':comparison},indent=2),flush=True)
if __name__=='__main__':
    try:main()
    except BaseException as exc:
        if OWNED and VERIFY.exists():write('build_failure.json',{'passed':False,'exception':repr(exc),'traceback':traceback.format_exc()})
        raise
