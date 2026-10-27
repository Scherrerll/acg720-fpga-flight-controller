"""One isolated full-top elaboration/SYN for compact_aw_v2; never PNR."""
from pathlib import Path
import collections
import datetime
import hashlib
import importlib.util
import json
import os
import re
import shutil
import traceback
import xml.etree.ElementTree as ET

O = Path(__file__).resolve().parent
R = O.parents[3]
ROOT = R / 'out/z_aw_fix_20261026/compact_aw_v2'
CANON = ROOT / 'canonical/source'
ATTEMPT = ROOT / 'build_attempt_01'
SOURCE = ATTEMPT / 'source'
VERIFY = ATTEMPT / 'verification'
PRIOR = R / 'out/z_aw_fix_20261026/compact_aw_v1'
ORIGINAL = R / 'firmware/B0B4/source'
HELPER = R / 'firmware/B0B4/build_candidate.py'
HELPER_SHA = 'abb5246c203b73c111f80bc91f8db6c8220463f7d4c5cf48dbfe2167ef49db84'
V1_RUNNER = R / 'analysis/20261026_z_aw_fix/build/compact_aw/run_synthesis.py'
HOLD_SHA = 'afc656820788d8cbf7c61d8c4e7526bec3dceb950673de9df18cb68a7d0632f3'
OWNED = False
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
utc = lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()


def write(name, value):
    (VERIFY / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf8')


def source55(path):
    return {p.relative_to(path).as_posix(): sha(p) for p in path.rglob('*') if p.is_file()}


def resources(path):
    result = {}
    def walk(node, prefix=''):
        name = prefix + node.attrib['name']
        result[name] = {k: int(re.match(r'\d+', v)[0]) for k, v in node.attrib.items() if k.startswith('T_')}
        for child in node:
            walk(child, name + '/')
    walk(ET.parse(path).getroot())
    return result


def extended_audit(helper, vg):
    spec = importlib.util.spec_from_file_location('compact_v2_graph', helper.GRAPH_READER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    graph = module.Graph(vg)
    mapped_text = vg.read_text(errors='replace')
    expected_ports = set(re.findall(r'IO_LOC\s+"([^"]+)"', (SOURCE / 'acg720_ano_port.cst').read_text()))
    top_ports = graph.modules['acg720_ano_port'][0]
    assert len(expected_ports) == len(top_ports) == 18 and set(top_ports) == expected_ports
    assert all(len(bits) == 1 for bits in top_ports.values())
    gains = {}
    for axis, default in [('p', 1000), ('i', 350)]:
        cells = {n: c for n, c in graph.cells.items()
                 if re.fullmatch(r'parameters/active_' + axis + r'_\d+_s\d+', n)}
        indices = {int(re.search(r'active_[pi]_(\d+)_', n)[1]) for n in cells}
        assert len(cells) == 16 and indices == set(range(16))
        init = 0
        for name, cell in cells.items():
            assert cell['type'].startswith('DFF') and cell['pins'].get('D') and cell['pins'].get('Q')
            index = int(re.search(r'active_[pi]_(\d+)_', name)[1])
            bits = re.findall(r'defparam\s+' + re.escape(name.rsplit('/', 1)[-1]) + r"\.INIT=1'b([01]);", mapped_text)
            assert len(bits) == 1
            init |= int(bits[0]) << index
        assert init == default
        gains[axis] = dict(ff_count=16, init_wire=init, mapped_cells=cells)
    histogram = collections.Counter(c['type'] for c in graph.cells.values())
    write('gain_port_audit.json', dict(passed=True, netlist_sha256=sha(vg),
        scope='Actual mapped top18scalar ports and live16bit gain FF/INIT; no functional or physical-timing claim',
        top_ports=top_ports, gains=gains, primitive_histogram=dict(sorted(histogram.items()))))


def main():
    global OWNED
    assert not ATTEMPT.exists(), 'Never overwrite an existing attempt'
    assert sha(HELPER) == HELPER_SHA
    freeze = json.loads((O / 'source_freeze.json').read_text())
    expected = freeze['source55']
    prior = source55(PRIOR / 'canonical/source')
    original = source55(ORIGINAL)
    assert len(expected) == len(prior) == len(original) == 55
    assert expected['position/mtf_xyz_hold_control.v'] == HOLD_SHA
    assert [n for n in expected if expected[n] != prior[n]] == ['position/mtf_xyz_hold_control.v']
    assert source55(CANON) == expected
    assert sha(O.parent / 'sign_step_bound.md') == freeze['proof_sha256']
    spec = importlib.util.spec_from_file_location('compact_v2_original_gates', HELPER)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    helper.CANON = CANON
    helper.ATTEMPT = ATTEMPT
    helper.SOURCE = SOURCE
    helper.VERIFY = VERIFY
    helper.EXPECTED_CHANGES = {**helper.EXPECTED_CHANGES, 'position/mtf_xyz_hold_control.v': HOLD_SHA}
    baseline = json.loads((R / 'firmware/B0B3/qualification.json').read_text())['source_sha256']
    assert expected.keys() == baseline.keys()
    assert {n: expected[n] for n in expected if expected[n] != baseline[n]} == helper.EXPECTED_CHANGES
    ATTEMPT.mkdir(parents=True)
    OWNED = True
    shutil.copytree(CANON, SOURCE)
    VERIFY.mkdir()
    temporary = VERIFY / 'tmp'
    temporary.mkdir()
    os.environ.update(TMP=str(temporary), TEMP=str(temporary), TMPDIR=str(temporary))
    write('build_input.json', dict(scope='Independent compact_aw_v2 full-top elaboration and SYN only; no PNR',
        started_utc=utc(), canonical_override=str(CANON), source_directory=str(SOURCE),
        source_sha256=expected, baseline_B3_source_sha256=baseline,
        compact_v1_source_sha256=prior, original_B4_source_sha256=original,
        changed_from_compact_v1=['position/mtf_xyz_hold_control.v'],
        runner_sha256=sha(Path(__file__)), imported_helper_sha256=HELPER_SHA,
        reference_v1_runner_sha256=sha(V1_RUNNER), source_freeze_sha256=sha(O / 'source_freeze.json'),
        proof_sha256=freeze['proof_sha256'], usercode='0000B0B4',
        synthesis_options=dict(map_option=2, replicate_resources=0),
        tools={str(p): sha(p) for p in [helper.GOWIN, helper.IVERILOG, helper.PRIMITIVES, helper.GRAPH_READER]}))
    helper.check_sources(expected)
    project = ET.parse(SOURCE / 'acg720_ano_port.gprj')
    files = [f.attrib['path'] for f in project.findall('.//File')
             if f.attrib.get('type') == 'file.verilog' and f.attrib.get('enable') == '1']
    helper.run_phase('elaboration', [str(helper.IVERILOG), '-g2012', '-s', 'acg720_ano_port',
        '-I', str(SOURCE), '-o', str(VERIFY / 'top.vvp'), *files, str(helper.PRIMITIVES)], SOURCE, expected)
    lines = (SOURCE / 'build.tcl').read_text().splitlines()
    assert lines.count('run all') == 1 and lines.count('exit') == 1
    tcl = '\n'.join('run syn' if line == 'run all' else line for line in lines if line.strip() != 'exit')
    tcl += '\nputs SYNTHESIS_COMMAND_RETURNED_EOF\nflush stdout\n'
    execution = ATTEMPT / 'synth_only.tcl'
    execution.write_text(tcl, encoding='utf8')
    assert 'run pnr' not in tcl and 'run all' not in tcl
    write('synthesis_input.json', dict(source_sha256=expected, canonical_override=str(CANON),
        execution_tcl_sha256=sha(execution), runner_sha256=sha(Path(__file__)),
        imported_helper_sha256=HELPER_SHA, tool_sha256=sha(helper.GOWIN)))
    receipt = helper.run_phase('synthesis', [str(helper.GOWIN), str(execution)], SOURCE, expected)
    assert receipt['actual_p_wait'] == 0
    assert 'SYNTHESIS_COMMAND_RETURNED_EOF' in (VERIFY / 'synthesis.log').read_text(errors='replace')
    vg = SOURCE / 'impl/gwsynthesis/acg720_ano_port.vg'
    assert vg.is_file()
    helper.mapped_audit(vg, expected)
    extended_audit(helper, vg)
    current_xml = SOURCE / 'impl/gwsynthesis/acg720_ano_port_syn_rsc.xml'
    prior_xml = PRIOR / 'build_attempt_01/source/impl/gwsynthesis/acg720_ano_port_syn_rsc.xml'
    old, new = resources(prior_xml), resources(current_xml)
    selected = ['acg720_ano_port', 'acg720_ano_port/native_navigation/controller_proof', 'acg720_ano_port/parameters']
    comparison = {n: dict(compact_v1=old[n], compact_v2=new[n],
        delta={k: new[n].get(k, 0) - old[n].get(k, 0) for k in old[n].keys() | new[n].keys()}) for n in selected}
    write('resource_comparison.json', dict(scope='Actual mapped resources only; no route/timing claim',
        compact_v1_xml_sha256=sha(prior_xml), compact_v2_xml_sha256=sha(current_xml),
        compact_v1_vg_sha256=sha(PRIOR / 'build_attempt_01/source/impl/gwsynthesis/acg720_ano_port.vg'),
        compact_v2_vg_sha256=sha(vg), resources=comparison))
    helper.check_sources(expected)
    assert source55(PRIOR / 'canonical/source') == prior and source55(ORIGINAL) == original
    assert sha(HELPER) == HELPER_SHA
    write('synthesis_summary.json', dict(passed=True, completed_utc=utc(), actual_p_wait=0,
        scope='Full-top elaboration/SYN/mapped clock-radio-gain-port audit only; PNR requires separate root authorization',
        canonical_override=str(CANON), source_sha256=expected, netlist_sha256=sha(vg),
        original_B4_source55_unchanged=True, compact_v1_source55_unchanged=True,
        compact_v2_source55_unchanged=True, runner_sha256=sha(Path(__file__)),
        imported_helper_sha256=HELPER_SHA, synthesis_exit_sha256=sha(VERIFY / 'synthesis_exit.json'),
        mapped_audit_sha256=sha(VERIFY / 'mapped_audit.json'), gain_port_audit_sha256=sha(VERIFY / 'gain_port_audit.json'),
        resource_comparison_sha256=sha(VERIFY / 'resource_comparison.json'), resources=comparison))
    print(json.dumps(dict(synthesis_only_pass=True, netlist_sha256=sha(vg), resources=comparison), indent=2), flush=True)


if __name__ == '__main__':
    try:
        main()
    except BaseException as exc:
        if OWNED and VERIFY.exists():
            write('build_failure.json', dict(passed=False, utc=utc(), exception=repr(exc), traceback=traceback.format_exc()))
        raise
