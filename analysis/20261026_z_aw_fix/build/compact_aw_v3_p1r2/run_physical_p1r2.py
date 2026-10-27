"""One fresh compact_aw_v3 P1R2 routability profile; strict20ns gates unchanged.

No synthesis, canonical edits, serial, programmer, service, or Git operations.
Never reuses/overwrites physical_p1r2_01; the audited physical gates are reused intact.
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
DONOR = REPO / 'out/z_aw_fix_20261026/compact_aw_v3/build_attempt_01'
ATTEMPT = REPO / 'out/z_aw_fix_20261026/compact_aw_v3/physical_p1r2_01'
SOURCE = ATTEMPT / 'source'
VERIFY = ATTEMPT / 'verification'
VG_SHA = '4f329e5313eba5966394828734c61867a3483b3eed8c3c37c724a453285c8a0c'
OWNED_ATTEMPT = False
SPEC = importlib.util.spec_from_file_location('b4_original_physical_gates', ORIGINAL_RUNNER)
BUILD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD)

# Imported functions look up these globals at call time. The canonical path
# deliberately remains the independent compact_aw_v3 canonical source.
BUILD.ATTEMPT = ATTEMPT
BUILD.SOURCE = SOURCE
BUILD.VERIFY = VERIFY
BUILD.CANON = REPO / 'out/z_aw_fix_20261026/compact_aw_v3/canonical/source'
BUILD.EXPECTED_CHANGES = {**BUILD.EXPECTED_CHANGES, 'position/mtf_xyz_hold_control.v': '9aa6a51a6cb2168ef46f3f5a61a23e3c4db8546601be7c0e562d4d16ab2cd6aa'}
assert BUILD.ATTEMPT != DONOR and BUILD.SOURCE == SOURCE and BUILD.VERIFY == VERIFY


def main():
    global OWNED_ATTEMPT
    assert BUILD.sha(ORIGINAL_RUNNER) == ORIGINAL_RUNNER_SHA, 'original physical gates changed'
    assert not ATTEMPT.exists(), 'Use a fresh attempt; never overwrite evidence'
    donor_input = DONOR / 'verification/build_input.json'
    donor_audit = DONOR / 'verification/mapped_audit.json'
    donor_exit = DONOR / 'verification/synthesis_exit.json'
    donor_summary = DONOR / 'verification/synthesis_summary.json'
    donor_syn_input = DONOR / 'verification/synthesis_input.json'
    donor_syn_tcl = DONOR / 'synth_only.tcl'
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
    summary = json.loads(donor_summary.read_text(encoding='utf8'))
    assert summary['passed'] is True and summary['actual_p_wait'] == 0
    assert summary['source_sha256'] == expected and summary['netlist_sha256'] == VG_SHA

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
        for p in (donor_input, donor_audit, donor_exit, donor_summary, donor_syn_input, donor_syn_tcl, donor_vg)
    }
    provenance = VERIFY / 'donor_provenance'
    provenance.mkdir()
    for path in (donor_input, donor_audit, donor_exit, donor_summary, donor_syn_input, donor_syn_tcl):
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
    assert physical_project.read_bytes().count(b'<?xml') == 1, 'exactly one XML declaration'
    assert [(f.attrib['path'], f.attrib['type']) for f in ET.parse(physical_project).findall('.//File')] == selected

    lines = (SOURCE / 'build.tcl').read_text(encoding='utf8').splitlines()
    assert lines.count('open_project acg720_ano_port.gprj') == 1
    assert lines.count('set_option -place_option 3') == 1
    assert lines.count('set_option -route_option 0') == 1
    assert lines.count('set_option -timing_driven 1') == 1
    assert lines.count('set_option -global_freq 50') == 1
    assert lines.count('set_option -map_option 2') == 1
    assert lines.count('set_option -replicate_resources 0') == 1
    assert lines.count('set_option -user_code 0000B0B4') == 1
    assert lines.count('run all') == 1 and lines.count('exit') == 1
    replacements = {'open_project acg720_ano_port.gprj': 'open_project physical.gprj',
                    'set_option -place_option 3': 'set_option -place_option 1',
                    'set_option -route_option 0': 'set_option -route_option 2',
                    'run all': 'run pnr'}
    physical_lines = [replacements.get(line, line) for line in lines if line.strip() != 'exit']
    physical_lines += ['puts PHYSICAL_COMMAND_RETURNED_EOF', 'flush stdout']
    physical_tcl = ATTEMPT / 'physical.tcl'
    physical_tcl.write_text('\n'.join(physical_lines) + '\n', encoding='utf8')
    assert 'run syn' not in physical_tcl.read_text() and physical_lines.count('run pnr') == 1
    assert physical_lines.count('set_option -timing_driven 1') == 1
    assert physical_lines.count('set_option -place_option 1') == 1
    assert physical_lines.count('set_option -route_option 2') == 1

    common = dict(mode='physical-only exact-netlist PNR P1R2 timing_driven1; no synthesis rerun; strict20ns gates unchanged',
        started_utc=BUILD.utc(), canonical_source=str(BUILD.CANON), source_directory=str(SOURCE),
        source_sha256=expected, donor_directory=str(DONOR), donor_netlist_sha256=VG_SHA,
        donor_evidence_sha256=donor_evidence, helper_sha256=BUILD.sha(Path(__file__)),
        original_runner_sha256=ORIGINAL_RUNNER_SHA,
        reused_functions=['check_sources', 'run_phase', 'physical_audit'],
        mapped_audit_reused_without_rebuilding=True,
        tools={str(BUILD.GOWIN): BUILD.sha(BUILD.GOWIN)},
        physical_options=dict(place=1, route=2, map_option=2, replicate_resources=0, timing_driven=1, global_freq=50),
        usercode='0000B0B4', a591_feature='0000B0B4', period_ns=20.0,
        project_sha256=BUILD.sha(physical_project), tcl_sha256=BUILD.sha(physical_tcl))
    BUILD.write('build_input.json', common)
    BUILD.write('physical_input.json', common)
    BUILD.check_sources(expected)
    BUILD.run_phase('physical', [str(BUILD.GOWIN), str(physical_tcl)], SOURCE, expected)
    result = BUILD.physical_audit(VG_SHA, expected)
    BUILD.check_sources(expected)
    assert BUILD.sha(donor_vg) == VG_SHA
    assert {str(p.relative_to(DONOR)): BUILD.sha(p) for p in (donor_input, donor_audit, donor_exit, donor_summary, donor_syn_input, donor_syn_tcl, donor_vg)} == donor_evidence
    BUILD.write('build_result.json', dict(passed=True,
        scope='Exact-VG P1R2 physical qualification; functional and hardware acceptance remain separate',
        completed_utc=BUILD.utc(), source_inputs_unchanged=True, source_sha256=expected,
        physical_options=common['physical_options'], helper_sha256=BUILD.sha(Path(__file__)),
        original_runner_sha256=ORIGINAL_RUNNER_SHA, donor_evidence_unchanged=True,
        physical_audit_sha256=BUILD.sha(VERIFY / 'physical_audit.json'),
        netlist_sha256=VG_SHA, bitstream_sha256=BUILD.sha(SOURCE / 'impl/pnr/acg720_ano_port.fs'),
        checks=result['checks'], fmax_mhz=result['fmax_mhz']))
    print('B0B4 compact_aw_v3 exact-VG P1R2 timing-driven1 strict physical qualification PASS', flush=True)


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
