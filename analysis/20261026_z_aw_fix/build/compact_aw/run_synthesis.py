"""Independent compact-AW SYN only; no PNR/programmer/serial/Git operation."""
from pathlib import Path
import datetime,hashlib,importlib.util,json,os,re,shutil,sys,traceback,xml.etree.ElementTree as ET
O=Path(__file__).resolve().parent;R=O.parents[3]
ROOT=R/'out/z_aw_fix_20261026/compact_aw_v1'
CANON=ROOT/'canonical/source';ATTEMPT=ROOT/'build_attempt_01';SOURCE=ATTEMPT/'source';VERIFY=ATTEMPT/'verification'
ORIGINAL=R/'firmware/B0B4/source';HELPER=R/'firmware/B0B4/build_candidate.py'
V1=R/'out/z_aw_fix_20261026/build_attempt_01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def write(name,data):(VERIFY/name).write_text(json.dumps(data,indent=2)+'\n')
def resources(path):
    result={}
    def walk(node,prefix=''):
        name=prefix+node.attrib['name'];result[name]={k:int(re.match(r'\d+',v)[0]) for k,v in node.attrib.items() if k.startswith('T_')}
        for child in node:walk(child,name+'/')
    walk(ET.parse(path).getroot());return result
def main():
    assert not ATTEMPT.exists(),'Never overwrite a build attempt'
    freeze=json.loads((O/'source_freeze.json').read_text());expected=freeze['variant_source55'];base=freeze['base_source55']
    assert len(expected)==55 and [n for n in expected if expected[n]!=base[n]]==['position/mtf_xyz_hold_control.v']
    assert expected['position/mtf_xyz_hold_control.v']=='479f757149a57ac0b5f9e0334dab80cae475a5345b834fde9c5130c701057ac3'
    assert all(sha(CANON/n)==h for n,h in expected.items()) and all(sha(ORIGINAL/n)==h for n,h in base.items())
    spec=importlib.util.spec_from_file_location('compact_aw_vendor_helper',HELPER);helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    helper.CANON=CANON;helper.ATTEMPT=ATTEMPT;helper.SOURCE=SOURCE;helper.VERIFY=VERIFY
    helper.EXPECTED_CHANGES={**helper.EXPECTED_CHANGES,'position/mtf_xyz_hold_control.v':expected['position/mtf_xyz_hold_control.v']}
    baseline=json.loads((R/'firmware/B0B3/qualification.json').read_text())['source_sha256']
    assert expected.keys()==baseline.keys()
    assert {n:expected[n] for n in expected if expected[n]!=baseline[n]}==helper.EXPECTED_CHANGES
    ATTEMPT.mkdir(parents=True);shutil.copytree(CANON,SOURCE);VERIFY.mkdir()
    tmp=VERIFY/'tmp';tmp.mkdir();os.environ.update(TMP=str(tmp),TEMP=str(tmp),TMPDIR=str(tmp))
    write('build_input.json',{'scope':'Independent compact-AW variant; SYN only, functional proof owned by root separately; no physical qualification claim.',
      'started_utc':utc(),'canonical_override':str(CANON),'original_B4_canonical_untouched':str(ORIGINAL),
      'source_directory':str(SOURCE),'source_sha256':expected,'baseline_B3_source_sha256':baseline,'B4_v1_source_sha256':base,
      'changed_from_B4_v1':['position/mtf_xyz_hold_control.v'],'source_freeze_sha256':sha(O/'source_freeze.json'),
      'runner_sha256':sha(Path(__file__)),'imported_vendor_helper':str(HELPER),'imported_helper_sha256':sha(HELPER),
      'physical_options_if_separately_authorized':{'place':3,'route':0,'map_option':2,'replicate_resources':0},
      'usercode':'0000B0B4','tools':{str(p):sha(p) for p in [helper.GOWIN,helper.IVERILOG,helper.PRIMITIVES,helper.GRAPH_READER]}})
    helper.check_sources(expected)
    project=ET.parse(SOURCE/'acg720_ano_port.gprj')
    files=[f.attrib['path'] for f in project.findall('.//File') if f.attrib.get('type')=='file.verilog' and f.attrib.get('enable')=='1']
    helper.run_phase('elaboration',[str(helper.IVERILOG),'-g2012','-s','acg720_ano_port','-I',str(SOURCE),'-o',str(VERIFY/'top.vvp'),*files,str(helper.PRIMITIVES)],SOURCE,expected)
    tcl=(SOURCE/'build.tcl').read_text();assert tcl.count('run all')==1
    tcl='\n'.join(line for line in tcl.splitlines() if line.strip()!='exit')+'\n'
    tcl=tcl.replace('run all','run syn')+'puts SYNTHESIS_COMMAND_RETURNED_EOF\nflush stdout\n'
    execution=ATTEMPT/'synth_only.tcl';execution.write_text(tcl,encoding='utf8')
    write('synthesis_input.json',{'source_sha256':expected,'canonical_override':str(CANON),'execution_tcl_sha256':sha(execution),
      'runner_sha256':sha(Path(__file__)),'imported_helper_sha256':sha(HELPER),'tool_sha256':sha(helper.GOWIN)})
    receipt=helper.run_phase('synthesis',[str(helper.GOWIN),str(execution)],SOURCE,expected)
    assert receipt['actual_p_wait']==0 and 'SYNTHESIS_COMMAND_RETURNED_EOF' in (VERIFY/'synthesis.log').read_text(errors='replace')
    vg=SOURCE/'impl/gwsynthesis/acg720_ano_port.vg';assert vg.is_file()
    helper.mapped_audit(vg,expected)
    current=SOURCE/'impl/gwsynthesis/acg720_ano_port_syn_rsc.xml';prior=V1/'source/impl/gwsynthesis/acg720_ano_port_syn_rsc.xml'
    old=resources(prior);new=resources(current)
    names=['acg720_ano_port','acg720_ano_port/native_navigation/controller_proof','acg720_ano_port/parameters']
    comparison={n:{'B4_v1':old[n],'compact':new[n],'delta':{k:new[n].get(k,0)-old[n].get(k,0) for k in old[n].keys()|new[n].keys()}} for n in names}
    write('resource_comparison.json',{'passed':True,'scope':'Actual mapped resource comparison only; no route or timing claim.',
      'B4_v1_xml_sha256':sha(prior),'compact_xml_sha256':sha(current),'B4_v1_vg_sha256':sha(V1/'source/impl/gwsynthesis/acg720_ano_port.vg'),
      'compact_vg_sha256':sha(vg),'resources':comparison})
    helper.check_sources(expected);assert all(sha(ORIGINAL/n)==h for n,h in base.items())
    write('synthesis_summary.json',{'passed':True,'scope':'SYNTHESIS/MAP ONLY; PNR requires separate root authorization; functional equivalence separate.',
      'completed_utc':utc(),'actual_p_wait':receipt['actual_p_wait'],'source_sha256':expected,'canonical_override':str(CANON),
      'original_B4_source55_unchanged':True,'variant_source55_unchanged':True,'netlist_sha256':sha(vg),
      'mapped_audit_sha256':sha(VERIFY/'mapped_audit.json'),'resource_comparison_sha256':sha(VERIFY/'resource_comparison.json'),
      'synthesis_exit_sha256':sha(VERIFY/'synthesis_exit.json'),'resources':comparison})
    print(json.dumps({'synthesis_only_pass':True,'netlist_sha256':sha(vg),'resources':comparison},indent=2),flush=True)
if __name__=='__main__':
    try:main()
    except BaseException as exc:
        if VERIFY.exists():write('build_failure.json',{'passed':False,'utc':utc(),'exception':repr(exc),'traceback':traceback.format_exc()})
        raise
