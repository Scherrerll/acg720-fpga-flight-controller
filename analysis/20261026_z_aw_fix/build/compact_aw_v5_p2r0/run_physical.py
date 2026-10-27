"""One fresh compact_aw_v5 map2 P2R0 physical-only trial from the audited B4 attempt01 VG.

No synthesis, canonical edits, serial, programmer, service, or Git operations.
Never reuses/overwrites physical_p2r0_01; the audited physical gates are reused intact.
"""
from pathlib import Path
import importlib.util
import json
import os
import shutil
import traceback
import xml.etree.ElementTree as ET

REPO = Path(__file__).resolve().parents[4]
ORIGINAL_RUNNER = REPO / 'firmware/B0B4/build_candidate.py'
ORIGINAL_RUNNER_SHA = 'abb5246c203b73c111f80bc91f8db6c8220463f7d4c5cf48dbfe2167ef49db84'
DONOR = REPO / 'out/z_aw_fix_20261026/compact_aw_v5/build_attempt_01'
ATTEMPT = REPO / 'out/z_aw_fix_20261026/compact_aw_v5/physical_p2r0_01'
SOURCE = ATTEMPT / 'source'
VERIFY = ATTEMPT / 'verification'
VG_SHA = '2d670218e97041bb3d4cc7c67218f4bef12e5bf96261225b9b97203ce3b4a1c9'
OWNED_ATTEMPT = False
SPEC = importlib.util.spec_from_file_location('b4_original_physical_gates', ORIGINAL_RUNNER)
BUILD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD)
BUILD.CANON = REPO / 'out/z_aw_fix_20261026/compact_aw_v5/canonical/source'
BUILD.EXPECTED_CHANGES = {**BUILD.EXPECTED_CHANGES, 'position/mtf_xyz_hold_control.v': '04e75ada52551d5622af060efe38fda9aa66ff25199bfb67651f9ec5315ed873'}

# Imported functions look up these globals at call time. The canonical path
# deliberately remains the immutable source tree used by attempt01.
BUILD.ATTEMPT = ATTEMPT
BUILD.SOURCE = SOURCE
BUILD.VERIFY = VERIFY
assert BUILD.ATTEMPT != DONOR and BUILD.SOURCE == SOURCE and BUILD.VERIFY == VERIFY


def main():
    global OWNED_ATTEMPT
    assert BUILD.sha(ORIGINAL_RUNNER) == ORIGINAL_RUNNER_SHA, 'original physical gates changed'
    assert not ATTEMPT.exists(), 'Use a fresh attempt; never overwrite evidence'
    donor_input = DONOR / 'verification/build_input.json'
    donor_audit = DONOR / 'verification/mapped_audit.json'
    donor_exit = DONOR / 'verification/synthesis_exit.json'
    donor_vg = DONOR / 'source/impl/gwsynthesis/acg720_ano_port.vg'
    expected = json.loads(donor_input.read_text(encoding='utf8'))['source_sha256']
    audit = json.loads(donor_audit.read_text(encoding='utf8'))
    synthesis_exit = json.loads(donor_exit.read_text(encoding='utf8'))
    assert len(expected) == 55
    canonical = {p.relative_to(BUILD.CANON).as_posix(): BUILD.sha(p)
                 for p in BUILD.CANON.rglob('*') if p.is_file()}
    assert canonical == expected, 'canonical differs from audited donor source55'
    assert expected['position/mtf_xyz_hold_control.v'] == BUILD.EXPECTED_CHANGES['position/mtf_xyz_hold_control.v']
    assert audit['passed'] is True and audit['source_sha256'] == expected
    assert audit['netlist_sha256'] == VG_SHA == BUILD.sha(donor_vg)
    assert synthesis_exit['actual_p_wait'] == 0 and synthesis_exit['normal_wait_return'] is True

    donor_freeze = DONOR / 'synthesis_freeze_manifest_final.json'
    assert BUILD.sha(donor_freeze) == '677dcfbdcc9fc448e3313b83cfef6f43729c521f738676d46cef2ad1a92a9b12'
    frozen = json.loads(donor_freeze.read_text())
    assert frozen['source55_unchanged'] and frozen['netlist_sha256'] == VG_SHA
    assert frozen['all_FF_clock_is_clk50'] and frozen['gain_init_wire'] == {'p': 1000, 'i': 350}
    for rel, item in frozen['artifacts'].items():
        assert BUILD.sha(DONOR / rel) == item['sha256'] and (DONOR / rel).stat().st_size == item['bytes']
    donor_summary = DONOR / 'verification/synthesis_summary.json'
    donor_gains = DONOR / 'verification/gain_port_audit.json'
    donor_ff = DONOR / 'verification/strict_ff_clock_audit.json'
    for p in (donor_summary, donor_gains, donor_ff):
        assert json.loads(p.read_text())['passed'] is True
    evidence_paths = (donor_input, donor_audit, donor_exit, donor_vg, donor_freeze, donor_summary, donor_gains, donor_ff)
    ATTEMPT.mkdir(parents=True)
    OWNED_ATTEMPT = True
    shutil.copytree(BUILD.CANON, SOURCE)
    VERIFY.mkdir()
    temporary = VERIFY / 'tmp'
    temporary.mkdir()
    os.environ.update(TMP=str(temporary), TEMP=str(temporary), TMPDIR=str(temporary))
    BUILD.check_sources(expected)
    copied_vg = SOURCE / 'impl/gwsynthesis/acg720_ano_port.vg'
    copied_vg.parent.mkdir(parents=True)
    shutil.copy2(donor_vg, copied_vg)
    assert BUILD.sha(copied_vg) == VG_SHA

    donor_evidence = {
        str(p.relative_to(DONOR)): BUILD.sha(p)
        for p in evidence_paths
    }
    provenance = VERIFY / 'donor_provenance'
    provenance.mkdir()
    for path in [p for p in evidence_paths if p.suffix == '.json']:
        shutil.copy2(path, provenance / path.name)

    project = ET.parse(SOURCE / 'acg720_ano_port.gprj')
    root = project.getroot()
    files = root.find('FileList')
    assert files is not None
    files.clear()
    selected = [('impl/gwsynthesis/acg720_ano_port.vg', 'file.netlist'),
                ('acg720_ano_port.cst', 'file.cst'),
                ('acg720_ano_port.sdc', 'file.sdc')]
    for path, kind in selected:
        ET.SubElement(files, 'File', dict(path=path, type=kind, enable='1'))
    physical_project = SOURCE / 'physical.gprj'
    physical_project.write_bytes(b'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE gowin-fpga-project>\n'
                                 + ET.tostring(root, encoding='utf-8'))
    assert [(f.attrib['path'], f.attrib['type']) for f in ET.parse(physical_project).findall('.//File')] == selected
    assert physical_project.read_bytes().count(b'<?xml') == 1

    lines = (SOURCE / 'build.tcl').read_text(encoding='utf8').splitlines()
    assert lines.count('open_project acg720_ano_port.gprj') == 1
    assert lines.count('set_option -place_option 3') == 1
    assert lines.count('set_option -route_option 0') == 1
    assert lines.count('set_option -map_option 2') == 1
    assert lines.count('set_option -replicate_resources 0') == 1
    assert lines.count('set_option -user_code 0000B0B4') == 1
    assert lines.count('run all') == 1 and lines.count('exit') == 1
    replacements = {'open_project acg720_ano_port.gprj': 'open_project physical.gprj',
                    'set_option -place_option 3': 'set_option -place_option 2',
                    'run all': 'run pnr'}
    physical_lines = [replacements.get(line, line) for line in lines if line.strip() != 'exit']
    physical_lines += ['puts PHYSICAL_COMMAND_RETURNED_EOF', 'flush stdout']
    physical_tcl = ATTEMPT / 'physical.tcl'
    physical_tcl.write_text('\n'.join(physical_lines) + '\n', encoding='utf8')
    assert 'run syn' not in physical_tcl.read_text() and physical_lines.count('run pnr') == 1
    assert physical_lines.count('set_option -map_option 2') == 1
    assert physical_lines.count('set_option -place_option 2') == 1 and physical_lines.count('set_option -route_option 0') == 1
    assert physical_lines.count('set_option -timing_driven 1') == 1
    assert 'inc_pnr' not in physical_tcl.read_text()

    common = dict(mode='physical-only exact-netlist PNR; no synthesis rerun',
        started_utc=BUILD.utc(), canonical_source=str(BUILD.CANON), source_directory=str(SOURCE),
        source_sha256=expected, donor_directory=str(DONOR), donor_netlist_sha256=VG_SHA,
        donor_evidence_sha256=donor_evidence, helper_sha256=BUILD.sha(Path(__file__)),
        original_runner_sha256=ORIGINAL_RUNNER_SHA,
        reused_functions=['check_sources', 'run_phase', 'physical_audit'],
        mapped_audit_reused_without_rebuilding=True,
        tools={str(BUILD.GOWIN): BUILD.sha(BUILD.GOWIN)},
        physical_options=dict(place=2, route=0, map_option=2, replicate_resources=0),
        usercode='0000B0B4', a591_feature='0000B0B4', period_ns=20.0,
        project_sha256=BUILD.sha(physical_project), tcl_sha256=BUILD.sha(physical_tcl))
    BUILD.write('build_input.json', common)
    BUILD.write('physical_input.json', common)
    BUILD.check_sources(expected)
    BUILD.run_phase('physical', [str(BUILD.GOWIN), str(physical_tcl)], SOURCE, expected)
    result = BUILD.physical_audit(VG_SHA, expected)
    BUILD.check_sources(expected)
    assert BUILD.sha(donor_vg) == VG_SHA
    assert {str(p.relative_to(DONOR)): BUILD.sha(p) for p in evidence_paths} == donor_evidence
    BUILD.write('build_result.json', dict(passed=True,
        scope='Exact-VG compact_v5 map2 P2R0 physical qualification; functional and hardware acceptance remain separate',
        completed_utc=BUILD.utc(), source_inputs_unchanged=True, source_sha256=expected,
        physical_options=common['physical_options'], helper_sha256=BUILD.sha(Path(__file__)),
        original_runner_sha256=ORIGINAL_RUNNER_SHA, donor_evidence_unchanged=True,
        physical_audit_sha256=BUILD.sha(VERIFY / 'physical_audit.json'),
        netlist_sha256=VG_SHA, bitstream_sha256=BUILD.sha(SOURCE / 'impl/pnr/acg720_ano_port.fs'),
        checks=result['checks'], fmax_mhz=result['fmax_mhz']))
    print('B0B4 exact-VG compact_v5 map2 P2R0 physical qualification PASS', flush=True)


if __name__ == '__main__':
    try:
        main()
    except BaseException as exc:
        if OWNED_ATTEMPT and VERIFY.exists():
            BUILD.write('build_failure.json', dict(passed=False, utc=BUILD.utc(),
                exception=repr(exc), traceback=traceback.format_exc(),
                scope='Qualification not established; inspect actual exit/cancellation evidence for cause',
                helper_sha256=BUILD.sha(Path(__file__)), original_runner_sha256=ORIGINAL_RUNNER_SHA))
        raise
