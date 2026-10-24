"""Independently verify completed PNR after Gowin rebuilds synthesis dependencies.

The original wrapper conservatively requires the old raw netlist hash. Gowin can
refresh comment metadata when run pnr invokes synthesis. Accept only the exact
qualified HDL body, matched current sources, clean diagnostics and strict PNR.
Never accesses the aircraft, receivers or programmer.
"""
from pathlib import Path
import datetime as dt
import hashlib
import importlib.util
import json
import re

ROOT = Path(__file__).resolve().parent
FIX = ROOT / 'fixture'
RUN = ROOT / 'hardware/pnr_retry_20261023T054556_750275Z/run.json'
LOGIC_SHA = '072e7755e35323dba14850d436ebe28c2eed1da84b2bfe11dad92de0dbe22862'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def logic(p):
    # Only the observed vendor metadata may be omitted, never directives.
    lines = p.read_text(encoding='utf-8').splitlines()
    metadata = re.compile(r'//(?:$|Written by GowinSynthesis$|Tool Version:.*$|Device:.*$|'
                          r'Device Version:.*$|Part Number:.*$|Device-Package:.*$|'
                          r'(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\s+\d{4}$|'
                          r'Source file index table:$|file\d+\s+".*"$)')
    for line in lines:
        if line.lstrip().startswith('//'):
            require(metadata.fullmatch(line.strip()) is not None,
                    'Unexpected netlist comment/directive must be reviewed: ' + line[:100])
    body = '\n'.join(s for s in lines if not s.lstrip().startswith('//'))
    return hashlib.sha256(body.encode()).hexdigest()


def main():
    run = load(RUN)
    require('finished_utc' in run, 'Wait for the owned PNR wrapper to finish')
    require(run['driver_sha256'] == sha(ROOT / 'run_pnr_only.py'), 'PNR runner changed')
    require(run['run_script_sha256'] == sha(FIX / 'pnr_only.tcl'), 'PNR script changed')
    spec = importlib.util.spec_from_file_location('post_pnr_builder', FIX / 'build_project.py')
    b = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(b)
    b.static_contract()
    q = load(ROOT / 'qualification.json')
    require(q['offline_tests_passed'] and q['sources_sha256'] == b.source_hashes() == run['qualified_sources'],
            'Current source qualification differs from executed PNR')
    for name, digest in q['evidence_sha256'].items():
        require(sha(ROOT / name) == digest, 'Offline proof changed: ' + name)
    evidence = load(ROOT / 'hardware/rebuilt_synthesis_connectivity.json')
    old_proof = load(ROOT / 'hardware/full_build_connectivity.json')
    require(evidence['verified'] and evidence['connectivity_excerpts_unchanged'] and
            evidence['prior_connectivity_evidence_sha256'] == sha(ROOT / 'hardware/full_build_connectivity.json'),
            'Missing connectivity proof')
    vg = FIX / 'impl/gwsynthesis/acg720_ano_port.vg'
    synlog = FIX / 'impl/gwsynthesis/acg720_ano_port.log'
    reference = Path(evidence['qualified_reference_netlist'])
    study = load(reference.parents[2] / 'study.json')
    require(study['passed'] and study['sources_sha256'] == q['sources_sha256'], 'Reference synthesis source mismatch')
    require(sha(reference) == evidence['qualified_reference_netlist_sha256'], 'Reference netlist changed')
    require(sha(vg) == evidence['netlist_sha256'] and
            sha(synlog) == evidence['log_sha256'] == run['synthesis_log_sha256'], 'Rebuilt synthesis changed again')
    require(logic(vg) == logic(reference) == evidence['logic_without_line_comments_sha256'] == LOGIC_SHA,
            'Synthesized HDL body differs from qualified reference')
    lines = vg.read_text(encoding='utf-8').splitlines()
    for item in old_proof['evidence']:
        require('\n'.join(lines[item['start_line']-1:item['end_line']]) == item['text'],
                'PWM/freshness connectivity changed')
    start = dt.datetime.fromisoformat(run['started_utc']).timestamp()
    for suffix in ['.tr', '.rpt.txt', '.fs']:
        p = FIX / 'impl/pnr' / ('acg720_ano_port' + suffix)
        require(p.is_file() and p.stat().st_mtime >= start, 'Missing or stale PNR output: ' + suffix)
    actual = b.verify(q['sources_sha256'])
    actual.update(pnr_only_requested=True, vendor_dependency_synthesis_reran=True,
                  accepted_after_dependency_synthesis_rebuild=True,
                  pnr_driver_sha256=run['driver_sha256'], pnr_script_sha256=run['run_script_sha256'],
                  post_pnr_verifier_sha256=sha(Path(__file__)),
                  synthesized_logic_sha256=LOGIC_SHA,
                  connectivity_evidence_sha256=sha(ROOT / 'hardware/rebuilt_synthesis_connectivity.json'))
    (FIX / 'build_manifest.json').write_text(json.dumps(actual, indent=2), encoding='utf-8')
    result = dict(verified=True, hardware_accessed=False, flash_changed=False, flight_ready=False,
                  fmax_mhz=actual['fmax_mhz'], slack=actual['slack'], unrouted_nets=actual['unrouted_nets'],
                  bitstream=actual['bitstream'], original_wrapper_passed=run.get('passed'),
                  original_wrapper_note='Raw netlist hash refreshed by vendor synthesis; exact HDL body independently verified.',
                  manifest_sha256=sha(FIX / 'build_manifest.json'), verifier_sha256=sha(Path(__file__)))
    (RUN.parent / 'independent_verification.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
