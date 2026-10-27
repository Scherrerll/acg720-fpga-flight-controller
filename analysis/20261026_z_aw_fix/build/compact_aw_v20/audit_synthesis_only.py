"""Actual native SYN hook. A rejection prevents PNR; no invented subphase p.wait."""
from pathlib import Path
import datetime, hashlib, importlib.util, json, os, sys, traceback, xml.etree.ElementTree as ET
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;R=O.parents[3]
assert len(sys.argv)==1
A=R/'out/z_aw_fix_20261026/compact_aw_v20/build_attempt_01'
S=A/'source';V=A/'verification';C=R/'out/z_aw_fix_20261026/compact_aw_v20/canonical/source'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
def write(name,data):(V/name).write_text(json.dumps(data,indent=2)+'\n',encoding='utf8')
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
def main():
    from validation_contract import verify_contract
    assert verify_contract(check_proof=True)['passed']
    ex=read(V/'synthesis_exit.json');assert ex['normal_wait_return'] and ex['actual_p_wait']==0
    expected=read(O/'source_freeze.json')['source55']
    assert len(expected)==55 and {n:sha(S/n) for n in expected}==expected=={n:sha(C/n) for n in expected}
    assert not (V/'native_synthesis_audit.json').exists()
    files=[f.attrib for f in ET.parse(S/'acg720_ano_port.gprj').findall('.//File')]
    assert any(f.get('path')=='acg720_ano_port.v' and f.get('type')=='file.verilog' and f.get('enable')=='1' for f in files)
    assert not any(f.get('type')=='file.netlist' for f in files)
    helper_path=R/'firmware/B0B4/build_candidate.py'
    audit_path=R/'analysis/20261026_z_aw_fix/build/compact_aw_v2/run_synthesis.py'
    assert sha(helper_path)=='abb5246c203b73c111f80bc91f8db6c8220463f7d4c5cf48dbfe2167ef49db84'
    assert sha(audit_path)=='23fe046b259c6713536fc27862eb80a3b392808a77e842aac2085c3f91f3d658'
    helper=load('native_syn_original_mapped_gates',helper_path)
    helper.CANON=C;helper.ATTEMPT=A;helper.SOURCE=S;helper.VERIFY=V
    baseline=read(R/'firmware/B0B3/qualification.json')['source_sha256']
    helper.EXPECTED_CHANGES={n:h for n,h in expected.items() if h!=baseline[n]}
    assert len(helper.EXPECTED_CHANGES)==12
    helper.check_sources(expected)
    vg=S/'impl/gwsynthesis/acg720_ano_port.vg';assert vg.is_file()
    helper.mapped_audit(vg,expected)
    auditor=load('native_syn_original_gain_ports',audit_path);auditor.SOURCE=S;auditor.VERIFY=V
    auditor.extended_audit(helper,vg)
    graph_module=load('native_syn_original_clock_graph',helper.GRAPH_READER);g=graph_module.Graph(vg)
    clocks=[c['pins']['O'][0] for c in g.cells.values() if c['type']=='IBUF' and c['pins'].get('I')==['clk50']]
    assert len(clocks)==1
    bad=[{'cell':n,'CLK':p.get('CLK',[])} for n,p in g.regs.items() if len(p.get('CLK',[]))!=1 or g.find(p['CLK'][0])!=g.find(clocks[0])]
    write('strict_ff_clock_audit.json',{'passed':not bad,'FF_count':len(g.regs),'all_FF_CLK50':not bad,'bad':bad,'vg_sha256':sha(vg)})
    assert not bad
    prior=R/'out/z_aw_fix_20261026/compact_aw_v4/build_attempt_01/source/impl/gwsynthesis/acg720_ano_port_syn_rsc.xml'
    current=S/'impl/gwsynthesis/acg720_ano_port_syn_rsc.xml'
    old,new=auditor.resources(prior),auditor.resources(current)
    names=['acg720_ano_port','acg720_ano_port/native_navigation/controller_proof','acg720_ano_port/parameters']
    comparison={n:{'parent_v4_map2':old[n],'composed_guard_landing_fanout_map2':new[n],'delta':{k:new[n].get(k,0)-old[n].get(k,0) for k in old[n].keys()|new[n].keys()}} for n in names}
    write('resource_comparison.json',{'scope':'Actual v20 AZ/VY guards and landing/fanout composition synthesis versus v4; no physical timing claim.','resources':comparison,'parent_xml_sha256':sha(prior),'native_xml_sha256':sha(current)})
    helper.check_sources(expected)
    write('native_synthesis_audit.json',{'passed':True,'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'source55':expected,'netlist_sha256':sha(vg),'project_sha256':sha(S/'acg720_ano_port.gprj'),'project_filelist':files,
        'hook_pid':os.getpid(),'hook_parent_pid':os.getppid(),'hook_sha256':sha(Path(__file__)),
        'resource_comparison_sha256':sha(V/'resource_comparison.json'),
        'mapped_audit_sha256':sha(V/'mapped_audit.json'),'gain_port_audit_sha256':sha(V/'gain_port_audit.json'),
        'strict_ff_clock_audit_sha256':sha(V/'strict_ff_clock_audit.json'),
        'scope':'SYN_ONLY audit after an actual successful vendor process wait0, independently recorded in synthesis_exit.json. This audit process has its own actual exit receipt; no PNR or combined-native flow claim.'})
    print('NATIVE_SYNTHESIS_AUDIT_PASS '+sha(vg),flush=True)
if __name__=='__main__':
    try:main()
    except BaseException as error:
        if V.is_dir():write('native_synthesis_audit_failure.json',{'passed':False,'error':repr(error),'traceback':traceback.format_exc()})
        raise
