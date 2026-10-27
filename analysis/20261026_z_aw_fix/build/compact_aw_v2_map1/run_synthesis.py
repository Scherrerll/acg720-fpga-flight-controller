"""Same frozen compact_aw_v2 RTL: one map1 full-top elaboration/SYN, never PNR."""
from pathlib import Path
import importlib.util
import json
import os
import shutil
import traceback
import xml.etree.ElementTree as ET

O = Path(__file__).resolve().parent
R = O.parents[3]
BASE = R / 'out/z_aw_fix_20261026/compact_aw_v2'
CANON = BASE / 'canonical/source'
ATTEMPT = BASE / 'map1_synthesis_01'
SOURCE = ATTEMPT / 'source'
VERIFY = ATTEMPT / 'verification'
MAP2 = BASE / 'build_attempt_01'
HELPER = R / 'firmware/B0B4/build_candidate.py'
HELPER_SHA = 'abb5246c203b73c111f80bc91f8db6c8220463f7d4c5cf48dbfe2167ef49db84'
V2_RUNNER = O.parent / 'compact_aw_v2/run_synthesis.py'
FREEZE = O.parent / 'compact_aw_v2/source_freeze.json'
HOLD_SHA = 'afc656820788d8cbf7c61d8c4e7526bec3dceb950673de9df18cb68a7d0632f3'
OWNED = False


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def main():
    global OWNED
    assert not ATTEMPT.exists(), 'Never overwrite a previous attempt'
    helper = load_module('map1_original_gates', HELPER)
    assert helper.sha(HELPER) == HELPER_SHA
    v2 = load_module('map1_v2_audit_functions', V2_RUNNER)
    frozen = json.loads(FREEZE.read_text())
    expected = frozen['source55']
    assert len(expected) == 55 and expected['position/mtf_xyz_hold_control.v'] == HOLD_SHA
    assert v2.source55(CANON) == expected
    map2_input = MAP2 / 'verification/build_input.json'
    map2_summary = MAP2 / 'verification/synthesis_summary.json'
    map2_exit = MAP2 / 'verification/synthesis_exit.json'
    summary = json.loads(map2_summary.read_text())
    assert json.loads(map2_input.read_text())['source_sha256'] == expected
    assert summary['passed'] and summary['source_sha256'] == expected and summary['actual_p_wait'] == 0
    assert json.loads(map2_exit.read_text())['actual_p_wait'] == 0
    map2_vg = MAP2 / 'source/impl/gwsynthesis/acg720_ano_port.vg'
    map2_xml = MAP2 / 'source/impl/gwsynthesis/acg720_ano_port_syn_rsc.xml'
    assert helper.sha(map2_vg) == summary['netlist_sha256']
    references = {str(p): helper.sha(p) for p in (HELPER,V2_RUNNER,FREEZE,map2_input,map2_summary,map2_exit,map2_vg,map2_xml)}
    ATTEMPT.mkdir(parents=True); OWNED = True
    shutil.copytree(CANON,SOURCE); VERIFY.mkdir(); (VERIFY/'tmp').mkdir()
    os.environ.update(TMP=str(VERIFY/'tmp'),TEMP=str(VERIFY/'tmp'),TMPDIR=str(VERIFY/'tmp'))
    helper.CANON=CANON; helper.ATTEMPT=ATTEMPT; helper.SOURCE=SOURCE; helper.VERIFY=VERIFY
    v2.SOURCE=SOURCE; v2.VERIFY=VERIFY
    helper.check_sources(expected)
    helper.write('build_input.json',dict(scope=__doc__,started_utc=helper.utc(),source_directory=str(SOURCE),
        canonical_override=str(CANON),source_sha256=expected,runner_sha256=helper.sha(Path(__file__)),
        reference_sha256=references,synthesis_options=dict(source_map_option=2,execution_map_option=1,replicate_resources=0,global_freq=50),
        usercode='0000B0B4',period_ns=20,functional_tests_rerun=False,
        tools={str(p):helper.sha(p)for p in (helper.GOWIN,helper.IVERILOG,helper.PRIMITIVES,helper.GRAPH_READER)}))
    project=ET.parse(SOURCE/'acg720_ano_port.gprj')
    files=[f.attrib['path']for f in project.findall('.//File')if f.attrib.get('type')=='file.verilog'and f.attrib.get('enable')=='1']
    helper.run_phase('elaboration',[str(helper.IVERILOG),'-g2012','-s','acg720_ano_port','-I',str(SOURCE),'-o',str(VERIFY/'top.vvp'),*files,str(helper.PRIMITIVES)],SOURCE,expected)
    lines=(SOURCE/'build.tcl').read_text().splitlines()
    assert lines.count('set_option -map_option 2')==1 and lines.count('run all')==1 and lines.count('exit')==1
    replacements={'set_option -map_option 2':'set_option -map_option 1','run all':'run syn'}
    execution_lines=[replacements.get(line,line)for line in lines if line.strip()!='exit']
    execution_lines += ['puts SYNTHESIS_COMMAND_RETURNED_EOF','flush stdout']
    execution=ATTEMPT/'synth_only.tcl'; execution.write_text('\n'.join(execution_lines)+'\n',encoding='utf8')
    assert execution_lines.count('set_option -map_option 1')==1 and execution_lines.count('run syn')==1
    assert not any(line.startswith('run pnr')or line=='run all'for line in execution_lines)
    assert 'set_option -user_code 0000B0B4' in execution_lines and 'set_option -replicate_resources 0' in execution_lines and 'set_option -global_freq 50' in execution_lines
    helper.write('synthesis_input.json',dict(source_sha256=expected,execution_tcl_sha256=helper.sha(execution),
        source_build_tcl_sha256=helper.sha(SOURCE/'build.tcl'),runner_sha256=helper.sha(Path(__file__)),
        original_gates_sha256=HELPER_SHA,source_map_option=2,execution_map_option=1,PNR_authorized=False))
    helper.run_phase('synthesis',[str(helper.GOWIN),str(execution)],SOURCE,expected)
    assert 'SYNTHESIS_COMMAND_RETURNED_EOF' in (VERIFY/'synthesis.log').read_text(errors='replace')
    vg=SOURCE/'impl/gwsynthesis/acg720_ano_port.vg'; xml=SOURCE/'impl/gwsynthesis/acg720_ano_port_syn_rsc.xml'
    assert vg.exists()and xml.exists()
    helper.mapped_audit(vg,expected)
    v2.extended_audit(helper,vg)
    old,new=v2.resources(map2_xml),v2.resources(xml)
    comparison={name:dict(map2=old.get(name,{}),map1=new.get(name,{}),
        delta={k:new.get(name,{}).get(k,0)-old.get(name,{}).get(k,0)for k in old.get(name,{}).keys()|new.get(name,{}).keys()})for name in sorted(old.keys()|new.keys())}
    helper.write('map1_vs_map2_resources.json',dict(scope='Same RTL, actual compiler resource tree; no routing/timing claim',
        source_sha256=expected,map2_vg_sha256=helper.sha(map2_vg),map1_vg_sha256=helper.sha(vg),
        map2_xml_sha256=helper.sha(map2_xml),map1_xml_sha256=helper.sha(xml),resources=comparison))
    helper.check_sources(expected)
    assert {str(p):helper.sha(p)for p in map(Path,references)}==references
    assert not any((SOURCE/'impl/pnr').glob('*.fs'))and not any((SOURCE/'impl/pnr').glob('*.tr'))
    helper.write('synthesis_summary.json',dict(passed=True,completed_utc=helper.utc(),actual_elaboration_p_wait=0,actual_synthesis_p_wait=0,
        scope=__doc__,source_sha256=expected,source55_unchanged=True,references_unchanged=True,functional_tests_rerun=False,
        source_map_option=2,execution_map_option=1,PNR_started=False,netlist_sha256=helper.sha(vg),
        runner_sha256=helper.sha(Path(__file__)),mapped_audit_sha256=helper.sha(VERIFY/'mapped_audit.json'),
        gain_port_audit_sha256=helper.sha(VERIFY/'gain_port_audit.json'),resource_comparison_sha256=helper.sha(VERIFY/'map1_vs_map2_resources.json')))
    print(json.dumps(dict(map1_synthesis_only_pass=True,netlist_sha256=helper.sha(vg),
        resources={n:comparison[n]for n in ('acg720_ano_port','acg720_ano_port/native_navigation/controller_proof','acg720_ano_port/parameters')}),indent=2),flush=True)


if __name__=='__main__':
    try:main()
    except BaseException as exc:
        if OWNED and VERIFY.exists():
            (VERIFY/'build_failure.json').write_text(json.dumps(dict(passed=False,exception=repr(exc),traceback=traceback.format_exc()),indent=2),encoding='utf8')
        raise
