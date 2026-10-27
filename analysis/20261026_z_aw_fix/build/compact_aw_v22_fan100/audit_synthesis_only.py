"""Strict original mapped gates after real SYN0; fanout effect is measured only."""
from pathlib import Path
import datetime,hashlib,importlib.util,json,os,sys,traceback,xml.etree.ElementTree as ET
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;R=O.parents[3];STANDARD=O.parent/'compact_aw_v22'
A=R/'out/z_aw_fix_20261026/compact_aw_v22_fan100/build_attempt_01';S=A/'source';V=A/'verification'
C=R/'out/z_aw_fix_20261026/compact_aw_v22/canonical/source';PARENT=C.parent.parent/'build_attempt_01/source/impl/gwsynthesis'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
def write(n,j):(V/n).write_text(json.dumps(j,indent=2)+'\n',encoding='utf8')
def load(n,p):
    spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def main():
    from input_contract import validate
    from effective_recipe import make_recipe
    from mapped_fanout import measure
    base=validate();expected=base['source55'];ex=read(V/'synthesis_exit.json')
    assert ex['normal_wait_return'] is True and type(ex['actual_p_wait']) is int and ex['actual_p_wait']==0
    assert sha(V/'synthesis.log')==ex['log_sha256'] and 'SYNTHESIS_COMMAND_RETURNED_EOF' in (V/'synthesis.log').read_text(errors='replace')
    assert {n:sha(S/n) for n in expected}=={n:sha(C/n) for n in expected}==expected
    assert (A/'synth_only.tcl').read_text()==make_recipe(S/'build.tcl')
    assert read(V/'build_input.json')['synthesis_options']=={'map_option':2,'replicate_resources':0,'max_fanout':100,'opt_goal':'area'}
    files=[f.attrib for f in ET.parse(S/'acg720_ano_port.gprj').findall('.//File')]
    assert any(f.get('path')=='acg720_ano_port.v' and f.get('type')=='file.verilog' and f.get('enable')=='1' for f in files)
    assert not any(f.get('type')=='file.netlist' for f in files)
    helper_path=R/'firmware/B0B4/build_candidate.py';gain_path=STANDARD.parent/'compact_aw_v2/run_synthesis.py'
    assert sha(helper_path)=='abb5246c203b73c111f80bc91f8db6c8220463f7d4c5cf48dbfe2167ef49db84'
    assert sha(gain_path)=='23fe046b259c6713536fc27862eb80a3b392808a77e842aac2085c3f91f3d658'
    helper=load('fan100_original_mapped_gates',helper_path);helper.CANON=C;helper.ATTEMPT=A;helper.SOURCE=S;helper.VERIFY=V
    b3=read(R/'firmware/B0B3/qualification.json')['source_sha256'];helper.EXPECTED_CHANGES={n:h for n,h in expected.items() if h!=b3[n]};assert len(helper.EXPECTED_CHANGES)==12
    helper.check_sources(expected)
    vg=S/'impl/gwsynthesis/acg720_ano_port.vg';assert vg.is_file();helper.mapped_audit(vg,expected)
    auditor=load('fan100_original_gain_18port_gates',gain_path);auditor.SOURCE=S;auditor.VERIFY=V;auditor.extended_audit(helper,vg)
    graph=load('fan100_original_clock_graph',helper.GRAPH_READER);g=graph.Graph(vg)
    clocks=[c['pins']['O'][0] for c in g.cells.values() if c['type']=='IBUF' and c['pins'].get('I')==['clk50']];assert len(clocks)==1
    bad=[{'cell':n,'CLK':p.get('CLK',[])} for n,p in g.regs.items() if len(p.get('CLK',[]))!=1 or g.find(p['CLK'][0])!=g.find(clocks[0])]
    write('strict_ff_clock_audit.json',{'passed':not bad,'FF_count':len(g.regs),'all_FF_CLK50':not bad,'bad':bad,'vg_sha256':sha(vg)});assert not bad
    parent_vg=PARENT/'acg720_ano_port.vg';assert sha(parent_vg)==base['VG_sha256']
    parent_xml=PARENT/'acg720_ano_port_syn_rsc.xml';current_xml=vg.with_name('acg720_ano_port_syn_rsc.xml')
    before,after=auditor.resources(parent_xml),auditor.resources(current_xml)
    names=['acg720_ano_port','acg720_ano_port/native_navigation/controller_proof','acg720_ano_port/parameters']
    changes={n:{'sealed_STD22_max200':before[n],'same_source_fan100':after[n],'delta':{k:after[n].get(k,0)-before[n].get(k,0) for k in before[n].keys()|after[n].keys()}} for n in names}
    write('resource_comparison.json',{'scope':'Actual same-source200/100 mapped resource measurement; no expected improvement or physical timing claim.','source55':expected,'parent_VG_sha256':sha(parent_vg),'current_VG_sha256':sha(vg),'parent_xml_sha256':sha(parent_xml),'current_xml_sha256':sha(current_xml),'resources':changes})
    write('mapped_fanout_comparison.json',{'scope':'Actual index FF and LUT pin loads; named decoder family counts are descriptive. No STA or equivalent-copy inference. No load<=100 success requirement.','source55':expected,'graph_reader_sha256':sha(helper.GRAPH_READER),'parent_max200':measure(parent_vg),'same_source_max100':measure(vg)})
    helper.check_sources(expected);assert not (S/'impl/pnr').exists()
    artifacts={n:sha(V/n) for n in ['mapped_audit.json','gain_port_audit.json','strict_ff_clock_audit.json','resource_comparison.json','mapped_fanout_comparison.json']}
    write('native_synthesis_audit.json',{'passed':True,'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source55':expected,'netlist_sha256':sha(vg),'parent_VG_sha256':base['VG_sha256'],'project_sha256':sha(S/'acg720_ano_port.gprj'),'project_filelist':files,'hook_sha256':sha(Path(__file__)),'hook_pid':os.getpid(),'hook_parent_pid':os.getppid(),'effective_option_delta':{'max_fanout':{'from':200,'to':100}},'artifacts_sha256':artifacts,'scope':'Actual successful SYN process followed by actual strict audit process; no standalone physical or flight claim.'})
    print('NATIVE_SYNTHESIS_AUDIT_PASS '+sha(vg),flush=True)
if __name__=='__main__':
    try:main()
    except BaseException as e:
        if V.is_dir():write('native_synthesis_audit_failure.json',{'passed':False,'error':repr(e),'traceback':traceback.format_exc()})
        raise
