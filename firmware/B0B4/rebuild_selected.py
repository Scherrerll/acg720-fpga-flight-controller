"""Rebuild a qualified archived netlist in a new directory; never program hardware."""
from pathlib import Path
import argparse
import gzip
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
HELPER_SHA = 'abb5246c203b73c111f80bc91f8db6c8220463f7d4c5cf48dbfe2167ef49db84'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path,
                        help='A new directory beneath this repository out/; never reused')
    parser.add_argument('--verify-only', action='store_true',
                        help='Verify saved inputs without creating a directory or starting Gowin')
    args = parser.parse_args()
    saved_qualification = json.loads((ROOT / 'qualification.json').read_text(encoding='utf8'))
    if saved_qualification.get('workflow') == 'native_RTL_project_SYN_audit_PNR_one_vendor_process':
        command = [sys.executable, '-B', str(ROOT / 'rebuild_native.py'), '--output', str(args.output)]
        if args.verify_only:
            command.append('--verify-only')
        subprocess.run(command, cwd=REPO, check=True)
        return
    subprocess.run([sys.executable, '-B', str(ROOT / 'verify_release.py')],
                   cwd=REPO, check=True)
    qualification = json.loads((ROOT / 'qualification.json').read_text(encoding='utf8'))
    assert qualification['passed'] and qualification['physical']['passed']
    expected = qualification['source_sha256']
    assert len(expected) == 55
    actual_names = {p.relative_to(ROOT / 'source').as_posix()
                    for p in (ROOT / 'source').rglob('*') if p.is_file()}
    assert actual_names == expected.keys()
    for name, digest in expected.items():
        path = ROOT / 'source' / name
        assert path.resolve().is_relative_to((ROOT / 'source').resolve())
        assert not path.is_symlink() and not path.name.lower().startswith('.env') and not path.name.lower().endswith('.env')
        assert '.env' not in [s.lower() for s in path.suffixes]
        assert sha(path) == digest
    helper_path = ROOT / 'build_candidate.py'
    assert sha(helper_path) == HELPER_SHA
    evidence = ROOT / 'evidence/selected'
    terminal = json.loads((evidence / 'TERMINAL_MANIFEST.json').read_text(encoding='utf8'))
    review = json.loads((evidence / 'INDEPENDENT_RAW_REVIEW.json').read_text(encoding='utf8'))
    assert terminal['passed'] and review['passed'] and all(review['checks'].values())
    assert terminal['vendor_actual_p_wait'] == terminal['runner_actual_p_wait'] == 0
    assert terminal['source55'] == expected
    # Match the preserved local copies to their original sealed bytes.
    preserved = {}
    for original, item in terminal['artifacts'].items():
        basename = Path(original).name
        if basename in {'physical.tcl', 'physical.gprj'}:
            assert sha(evidence / basename) == item['sha256']
            preserved[basename] = item['sha256']
    assert set(preserved) == {'physical.tcl', 'physical.gprj'}
    with gzip.open(evidence / 'acg720_ano_port.vg.gz', 'rb') as stream:
        netlist = stream.read()
    assert hashlib.sha256(netlist).hexdigest() == qualification['netlist_sha256'] == terminal['vg_sha256']
    extra_cst = evidence / 'physical_constraints.cst'
    if extra_cst.exists():
        # Additional physical constraints must be bound by the selected input receipt.
        binding_files = [evidence / n for n in
                         ['placement_constraint_binding.json', 'data_routing_binding.json', 'clock_route_binding.json']
                         if (evidence / n).is_file()]
        assert binding_files, 'Additional CST has no selected binding receipt'
        assert qualification['physical']['period_ns'] == 20
    # Incremental seeds need a separate documented reconstruction. Current non-incremental
    # v11/v12 recipes do not consume any external seed files.
    tcl = (evidence / 'physical.tcl').read_text(encoding='utf8')
    assert 'inc_pnr' not in tcl and 'inc_place' not in tcl
    assert 'open_project physical.gprj' in tcl and 'run pnr' in tcl
    assert 'run all' not in tcl and 'run syn' not in tcl
    destination = args.output.resolve()
    assert destination.is_relative_to((REPO / 'out').resolve())
    assert destination != (REPO / 'out').resolve() and not destination.exists()
    if args.verify_only:
        print(json.dumps({'verified': True, 'source_files': 55, 'netlist_sha256': qualification['netlist_sha256'],
                          'output_created': False, 'vendor_started': False, 'hardware_operation': False}))
        return

    destination.mkdir(parents=True)
    source = destination / 'source'
    shutil.copytree(ROOT / 'source', source)
    verification = destination / 'verification'
    verification.mkdir()
    shutil.copy2(Path(__file__), verification / 'executed_rebuild_selected.py')
    netlist_path = source / 'impl/gwsynthesis/acg720_ano_port.vg'
    netlist_path.parent.mkdir(parents=True)
    netlist_path.write_bytes(netlist)
    shutil.copy2(evidence / 'physical.gprj', source / 'physical.gprj')
    if extra_cst.exists():
        shutil.copy2(extra_cst, source / extra_cst.name)
    execution = destination / 'physical.tcl'
    shutil.copy2(evidence / 'physical.tcl', execution)
    tmp = verification / 'tmp'
    tmp.mkdir()
    os.environ.update(TMP=str(tmp), TEMP=str(tmp), TMPDIR=str(tmp))
    (verification / 'selected_input.json').write_text(json.dumps({
        'qualification_sha256': sha(ROOT / 'qualification.json'),
        'source55': expected, 'vg_sha256': qualification['netlist_sha256'],
        'selected_terminal_manifest_sha256': sha(evidence / 'TERMINAL_MANIFEST.json'),
        'selected_independent_review_sha256': sha(evidence / 'INDEPENDENT_RAW_REVIEW.json'),
        'helper_sha256': HELPER_SHA, 'execution_tcl_sha256': sha(execution),
        'scope': 'New physical implementation of the archived qualified netlist. Its result needs its own gates; the selected release remains unchanged.'
    }, indent=2) + '\n', encoding='utf8')
    spec = importlib.util.spec_from_file_location('selected_original_physical_gates', helper_path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    helper.CANON = ROOT / 'source'
    helper.ATTEMPT = destination
    helper.SOURCE = source
    helper.VERIFY = verification
    helper.run_phase('physical', [str(helper.GOWIN), str(execution)], source, expected)
    result = helper.physical_audit(qualification['netlist_sha256'], expected)
    helper.check_sources(expected)
    (verification / 'rebuild_result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print(json.dumps({'physical_gate_passed': result['passed'], 'fmax_mhz': result['fmax_mhz'],
                      'new_output': str(destination), 'hardware_operation': False}))


if __name__ == '__main__':
    main()
